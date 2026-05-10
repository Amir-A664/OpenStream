from __future__ import annotations

import getpass
import os
import re
from pathlib import Path

from .config import AUTH_LABELS, OpenStreamConfig

INLINE_BLOCKS = {"ca", "cert", "key", "tls-auth", "tls-crypt", "tls-crypt-v2", "secret"}
CERT_DIRECTIVES = {"ca", "cert", "key", "pkcs12"}
STATIC_DIRECTIVES = {"tls-auth", "tls-crypt", "tls-crypt-v2", "secret", "key-direction"}


def iter_directive_lines(text: str) -> list[str]:
    lines: list[str] = []
    in_block: str | None = None
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        stripped = raw.strip()
        low = stripped.lower()
        if in_block:
            if low == f"</{in_block}>":
                in_block = None
            continue
        if low.startswith("<") and low.endswith(">") and not low.startswith("</"):
            name = low[1:-1].strip()
            if name in INLINE_BLOCKS:
                in_block = name
                continue
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue
        lines.append(stripped)
    return lines


def directive_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for line in iter_directive_lines(text):
        keys.add(line.split()[0].lower())
    return keys


def has_inline_block(text: str, names: set[str]) -> bool:
    low = text.lower()
    return any(re.search(rf"^\s*<{re.escape(name)}>\s*$", low, re.M) for name in names)


def detect_auth_method(text: str) -> str:
    keys = directive_keys(text)
    has_userpass = "auth-user-pass" in keys
    has_cert = bool(keys & CERT_DIRECTIVES) or has_inline_block(text, {"ca", "cert", "key"})
    has_static = bool(keys & STATIC_DIRECTIVES) or has_inline_block(
        text, {"tls-auth", "tls-crypt", "tls-crypt-v2", "secret"}
    )

    if has_userpass and (has_cert or has_static):
        return "hybrid"
    if has_userpass:
        return "userpass"
    if has_cert:
        return "cert"
    if has_static:
        return "static_key"
    return "unknown"


def choose_auth_method(text: str, filename: str) -> str:
    guessed = detect_auth_method(text)
    if guessed != "unknown":
        return guessed

    print(f"Could not confidently detect authentication method for: {filename}")
    print()
    print("Select authentication method for this .ovpn profile:")
    print("[1] Username / Password basic auth")
    print("[2] Certificate-based auth / TLS mutual auth")
    print("[3] Username/Password + Certificate hybrid auth")
    print("[4] Static Key / pre-shared key / tls-auth / tls-crypt")
    print()
    print("Not supported in this build yet:")
    print("- PAM / LDAP / RADIUS backends")
    print("- Token / OTP flows")
    selection = input("Selection: ").strip()
    mapping = {"1": "userpass", "2": "cert", "3": "hybrid", "4": "static_key"}
    if selection not in mapping:
        raise RuntimeError("Invalid authentication method selection.")
    return mapping[selection]


def auth_requires_credentials(method: str) -> bool:
    return method in {"userpass", "hybrid"}


def auth_label(method: str) -> str:
    return AUTH_LABELS.get(method, AUTH_LABELS["unknown"])


def write_auth_file(cfg: OpenStreamConfig, profile_id: str, username: str, password: str) -> Path:
    cfg.auth_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.auth_dir / f"{profile_id}.txt"
    path.write_text(f"{username}\n{password}\n", encoding="utf-8")
    os.chown(path, 0, 0)
    path.chmod(0o600)
    return path


def ensure_auth_file(cfg: OpenStreamConfig, profile_id: str) -> Path:
    path = cfg.auth_dir / f"{profile_id}.txt"
    if path.exists():
        path.chmod(0o600)
        return path
    print(f"Credentials required for profile: {profile_id}")
    username = input("VPN username: ").strip()
    if not username:
        raise RuntimeError("VPN username cannot be empty.")
    password = getpass.getpass("VPN password: ")
    if not password:
        raise RuntimeError("VPN password cannot be empty.")
    return write_auth_file(cfg, profile_id, username, password)
