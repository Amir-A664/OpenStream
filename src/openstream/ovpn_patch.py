from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .config import DATA_CIPHERS, DATA_CIPHERS_FALLBACK, TUN_DEV

INLINE_BLOCKS = {"ca", "cert", "key", "tls-auth", "tls-crypt", "tls-crypt-v2", "secret"}
DROP_DIRECTIVES = {
    "auth-user-pass",
    "auth-nocache",
    "data-ciphers",
    "data-ciphers-fallback",
    "compat-mode",
}
SINGLETON_RECONNECT_DIRECTIVES = {
    "resolv-retry": "resolv-retry infinite",
    "persist-key": "persist-key",
    "persist-tun": "persist-tun",
    "nobind": "nobind",
    "connect-retry": "connect-retry 5 300",
    "connect-timeout": "connect-timeout 10",
    "ping": "ping 10",
    "ping-restart": "ping-restart 60",
}
EXTERNAL_FILE_DIRECTIVES = {"ca", "cert", "key", "pkcs12", "tls-auth", "tls-crypt", "tls-crypt-v2", "secret"}


@dataclass
class PatchResult:
    text: str
    external_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _block_name_from_opening(line: str) -> str | None:
    stripped = line.strip().lower()
    if stripped.startswith("<") and stripped.endswith(">") and not stripped.startswith("</"):
        name = stripped[1:-1].strip()
        if name in INLINE_BLOCKS:
            return name
    return None


def _is_block_closing(line: str, block: str) -> bool:
    return line.strip().lower() == f"</{block}>"


def _copy_external_file(
    directive: str,
    line: str,
    profile_source_dir: Path,
    external_dir: Path,
) -> tuple[str, str | None]:
    try:
        parts = shlex.split(line, comments=False, posix=True)
    except ValueError:
        return line, None
    if len(parts) < 2:
        return line, None

    file_token = parts[1]
    if file_token.startswith("[") or file_token.startswith("<"):
        return line, None
    source = Path(file_token)
    if source.is_absolute():
        return line, None

    source_path = (profile_source_dir / source).resolve()
    if not source_path.exists():
        raise RuntimeError(f"Referenced file for directive '{directive}' was not found: {source}")

    external_dir.mkdir(parents=True, exist_ok=True)
    destination = external_dir / source.name
    if destination.exists() and destination.read_bytes() != source_path.read_bytes():
        stem = source.stem or "external"
        suffix = source.suffix
        destination = external_dir / f"{stem}-{hashlib.sha256(source_path.read_bytes()).hexdigest()[:8]}{suffix}"
    shutil.copy2(source_path, destination)
    os.chmod(destination, 0o600 if directive in {"key", "secret", "tls-auth", "tls-crypt", "tls-crypt-v2"} else 0o644)
    parts[1] = str(destination)
    return " ".join(shlex.quote(part) for part in parts), str(destination)


def patch_ovpn_config(
    raw: str,
    *,
    auth_method: str,
    auth_file: Path | None,
    profile_source_dir: Path,
    external_dir: Path,
    tun_dev: str = TUN_DEV,
    latch: bool = False,
) -> PatchResult:
    text = normalize_newlines(raw)
    output: list[str] = []
    seen_directives: set[str] = set()
    saw_dev = False
    block: str | None = None
    external_files: list[str] = []

    for raw_line in text.splitlines():
        if block:
            output.append(raw_line)
            if _is_block_closing(raw_line, block):
                block = None
            continue

        opening = _block_name_from_opening(raw_line)
        if opening:
            block = opening
            output.append(raw_line)
            continue

        stripped = raw_line.strip()
        if not stripped:
            output.append(raw_line)
            continue
        if stripped.startswith("#") or stripped.startswith(";"):
            output.append(raw_line)
            continue

        key = stripped.split()[0].lower()
        if key in DROP_DIRECTIVES:
            continue
        if key == "dev":
            if not saw_dev:
                output.append(f"dev {tun_dev}")
                saw_dev = True
            seen_directives.add("dev")
            continue

        if key in SINGLETON_RECONNECT_DIRECTIVES:
            # In latch mode, suppress persist-tun even if present in the
            # source config so OpenVPN exits on connection drop.
            if latch and key == "persist-tun":
                continue
            if key not in seen_directives:
                output.append(stripped)
                seen_directives.add(key)
            continue

        if key in EXTERNAL_FILE_DIRECTIVES:
            rewritten, copied = _copy_external_file(key, stripped, profile_source_dir, external_dir)
            output.append(rewritten)
            if copied:
                external_files.append(copied)
            seen_directives.add(key)
            continue

        output.append(stripped)
        seen_directives.add(key)

    if block:
        raise RuntimeError(f"Unclosed inline OpenVPN block: <{block}>")

    compact = [line for line in output]
    while compact and not compact[-1].strip():
        compact.pop()

    if not saw_dev and "dev" not in seen_directives:
        compact.insert(0, f"dev {tun_dev}")

    existing_keys = {
        line.strip().split()[0].lower()
        for line in compact
        if line.strip() and not line.strip().startswith(("#", ";", "<"))
    }
    for key, directive in SINGLETON_RECONNECT_DIRECTIVES.items():
        # In latch mode we omit persist-tun so that a connection drop tears down
        # the tun interface and causes OpenVPN to exit (rather than internally
        # reconnecting), allowing systemd's Restart=always to restart it cleanly.
        if latch and key == "persist-tun":
            continue
        if key not in existing_keys:
            compact.append(directive)

    # In latch mode, remap SIGUSR1 (which OpenVPN sends itself on reconnect
    # triggers such as ping-restart) to SIGTERM so the process exits and systemd
    # restarts it from scratch.
    if latch:
        compact.append("remap-usr1 SIGTERM")

    compact.append(f"data-ciphers {DATA_CIPHERS}")
    compact.append(f"data-ciphers-fallback {DATA_CIPHERS_FALLBACK}")

    if auth_method in {"userpass", "hybrid"}:
        if auth_file is None:
            raise RuntimeError("auth_file is required for username/password and hybrid profiles.")
        compact.append(f"auth-user-pass {auth_file}")
        compact.append("auth-nocache")

    patched = "\n".join(compact).rstrip() + "\n"
    if re.search(r"^\s*compat-mode\s+2\.4\s*$", patched, re.M):
        raise RuntimeError("Internal patcher error: compat-mode 2.4 survived patching.")
    return PatchResult(text=patched, external_files=external_files)
