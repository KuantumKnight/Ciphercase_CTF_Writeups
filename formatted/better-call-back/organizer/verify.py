#!/usr/bin/env python3
"""Socket-free organizer verification for Better Call Back."""

import ast
import importlib.util
import os
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit


ROOT = Path(__file__).resolve().parent
CHALLENGE = ROOT / "challenge"


def load(name, path, env):
    os.environ.update(env)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    app_paths = [CHALLENGE / service / "app.py" for service in ("portal", "idp", "collector", "bot")]
    for path in app_paths:
        ast.parse(path.read_text(), filename=str(path))

    idp = load("verify_idp", CHALLENGE / "idp/app.py", {
        "PORTAL_URL": "http://portal.example",
        "SECRET_KEY": "verify-idp-session",
        "CODE_SECRET": "verify-code-secret",
        "ADMIN_PASSWORD": "verify-admin-password",
    })
    collector = load("verify_collector", CHALLENGE / "collector/app.py", {})
    portal = load("verify_portal", CHALLENGE / "portal/app.py", {
        "IDP_PUBLIC_URL": "http://idp.example",
        "IDP_INTERNAL_URL": "http://idp.internal:5001",
        "PORTAL_URL": "http://portal.example",
        "COLLECTOR_URL": "http://collector.example",
        "BOT_URL": "http://bot.example",
        "BOT_SHARED_SECRET": "verify-bot-secret",
        "SECRET_KEY": "verify-portal-session",
        "REAL_FLAG": "CYS{C4LLB4CKS_D0NT_PR0V3_1D3NT1TY}",
    })
    bot = load("verify_bot", CHALLENGE / "bot/app.py", {
        "IDP_PUBLIC_URL": "http://idp.example",
        "IDP_INTERNAL_URL": "http://idp.internal:5001",
        "COLLECTOR_PUBLIC_URL": "http://collector.example",
        "COLLECTOR_INTERNAL_URL": "http://collector.internal:5002",
        "BOT_SHARED_SECRET": "verify-bot-secret",
        "ADMIN_PASSWORD": "verify-admin-password",
        "REQUIRE_HTTPS": "false",
    })

    idp_client = idp.app.test_client()
    collector_client = collector.app.test_client()
    portal_client = portal.app.test_client()

    assert portal.app.config["SESSION_COOKIE_NAME"] != idp.app.config["SESSION_COOKIE_NAME"]
    assert portal.IDP_PUBLIC_URL == "http://idp.example"
    assert portal.IDP_INTERNAL_URL == "http://idp.internal:5001"
    assert bot.rewrite_origin(
        "http://portal.example@collector.example/collect?box=test",
        bot.COLLECTOR_PUBLIC_URL,
        bot.COLLECTOR_INTERNAL_URL,
    ) == "http://collector.internal:5002/collect?box=test"

    with portal_client.session_transaction() as session:
        session["user"] = "employee"
        session["role"] = "user"
    portal_home = portal_client.get("/")
    assert "Sign out" in portal_home.text
    logout = portal_client.post("/logout")
    assert logout.status_code == 302
    assert logout.headers["Location"] == "http://idp.example/logout"

    with idp_client.session_transaction() as session:
        session["user"] = "employee"
    idp_home = idp_client.get("/")
    assert "Sign out of SSO" in idp_home.text
    idp_logout = idp_client.get("/logout")
    assert idp_logout.status_code == 302
    assert idp_logout.headers["Location"] == "http://portal.example/"

    assert idp_client.post("/login", data={
        "username": "regional.admin",
        "password": "verify-admin-password",
    }).status_code == 302
    state_location = portal_client.get("/login").headers["Location"]
    state = parse_qs(urlsplit(state_location).query)["state"][0]
    box = collector_client.get("/new").get_json()["box"]
    crafted = f"http://portal.example@collector.example/collect?box={box}"

    issued = idp_client.get("/authorize?" + urlencode({
        "client_id": "supplier-portal",
        "redirect_uri": crafted,
        "state": state,
    }))
    assert issued.status_code == 302
    location = urlsplit(issued.headers["Location"])
    assert location.hostname == "collector.example"
    assert collector_client.get(location.path + "?" + location.query).status_code == 200
    entry = collector_client.get(f"/mailbox/{box}").get_json()[0]
    assert entry["state"] == state and entry["code"]

    first_exchange = idp_client.post("/token", data={
        "client_id": "supplier-portal",
        "code": entry["code"],
        "redirect_uri": "http://portal.example/callback",
    })
    second_exchange = idp_client.post("/token", data={
        "client_id": "supplier-portal",
        "code": entry["code"],
        "redirect_uri": "http://portal.example/callback",
    })
    assert first_exchange.status_code == 200
    assert second_exchange.status_code == 400
    assert second_exchange.get_json()["error"] == "used_code"

    class TokenResponse:
        status_code = 200
        def json(self):
            return {"user": "regional.admin", "role": "admin"}

    original_post = portal.requests.post
    portal.requests.post = lambda *args, **kwargs: TokenResponse()
    try:
        assert portal_client.get("/callback?" + urlencode({
            "code": entry["code"],
            "state": state,
        })).status_code == 302
    finally:
        portal.requests.post = original_post

    manifest = portal_client.get("/admin/manifest")
    assert manifest.status_code == 200
    assert "CYS{C4LLB4CKS_D0NT_PR0V3_1D3NT1TY}" in manifest.text
    decoy = portal.app.test_client().post("/legacy-admin", data={
        "username": "legacy_ops",
        "password": "chickenfeed",
    })
    assert "CYS{L3G4CY_P4N3L_W4S_4_D3C0Y}" in decoy.text
    rejected = bot.app.test_client().post("/visit", json={
        "url": "http://not-the-idp.example/authorize",
    }, headers={"X-Bot-Secret": "verify-bot-secret"})
    assert rejected.status_code == 400

    print("PASS: syntax, cookie isolation, URL translation, OAuth redirect confusion, one-time code redemption, manifest, decoy, and reviewer allowlist")
    print("FLAG: CYS{C4LLB4CKS_D0NT_PR0V3_1D3NT1TY}")


if __name__ == "__main__":
    main()
