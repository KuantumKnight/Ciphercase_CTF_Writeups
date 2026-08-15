# Better Call Back — Organizer Package

**Author:** KuantumKnight

This directory contains the deployable challenge under `challenge/`, the
organizer solution under `solution/`, staged hints, requirements, and a local
verifier.

## Verify

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements/requirements.txt
python3 verify.py
```

The verifier uses Flask request clients, so it does not need Docker or open
TCP sockets. It checks the OAuth redirect confusion, authorization-code
replay, real manifest flag, decoy flag, and reviewer URL allowlist.

## Deploy

Use `challenge/docker-compose.yml` for local deployment or
`challenge/render.yaml` for Render. The player-facing package contains only
the challenge description; do not publish this organizer directory.

`IDP_PUBLIC_URL` and `COLLECTOR_PUBLIC_URL` are the browser-visible service
origins. Their `*_INTERNAL_URL` counterparts are the addresses used for
server-to-server traffic. They may be identical outside a container network.
