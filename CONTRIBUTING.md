# Contributing to OpenStream

OpenStream is intentionally small: network namespace, OpenVPN, SOCKS5, systemd, clean profile management. Keep changes aligned with that shape.

## Development setup

```sh
git clone https://github.com/Amir-A664/OpenStream.git
cd OpenStream
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Run basic checks:

```sh
./scripts/lint.sh
./scripts/smoke-test.sh
```

## Design rules

Use the public identity everywhere:

```text
OpenStream / opst / opstns
```

Do not reintroduce old prototype names, personal paths, or hardcoded server names.

Keep Bash small. Bash should bootstrap and run system helpers. Python should handle profile parsing, registry state, config rendering, and `.ovpn` patching.

## Secrets policy

Do not commit real VPN configs, auth files, private keys, provider hostnames, or screenshots containing credentials. Use placeholders only.

Good placeholders:

```text
vpn.example.com
YOUR_USERNAME
YOUR_PASSWORD
REDACTED_CERTIFICATE
REDACTED_PRIVATE_KEY
```

## Pull request checklist

Before opening a PR:

- run `./scripts/lint.sh`,
- run `./scripts/smoke-test.sh`,
- confirm generated systemd units still use `opstns`,
- confirm the selected SOCKS port is not hardcoded in user-facing code,
- confirm `.ovpn` inline blocks are not modified by the patcher,
- confirm no real secrets are included.

## Coding style

Prefer clear boring code. This project touches networking, service management, firewall rules, and credentials. Clever code here is how you summon goblins.

Python should be compatible with Python 3.10+.
