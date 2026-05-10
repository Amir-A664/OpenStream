from __future__ import annotations

import argparse
import os
import pwd
import shutil
import subprocess
import sys
from pathlib import Path

from .config import (
    AUTH_DIR,
    BIN_PATH,
    CACHE_DIR,
    CONFIG_DIR,
    CURRENT_OVPN,
    DEFAULT_SOCKS_PORT,
    LAN_LISTEN_IP,
    LIBEXEC_DIR,
    LISTEN_IP_PATH,
    LOCAL_LISTEN_IP,
    NETNS_DIR,
    NETNS_RESOLV_CONF,
    OPENVPN_DIR,
    PROFILE_REGISTRY_PATH,
    PROFILES_DIR,
    PYTHON_LIB_DIR,
    RUN_DIR,
    SERVICE_NAMES,
    STATE_DIR,
    STATE_ROOT,
    SYSTEMD_DIR,
    OpenStreamConfig,
    VERSION,
    validate_port,
    write_config,
)
from .dependencies import ensure_dependencies_interactive
from .systemd import daemon_reload, install_runtime_templates


class InstallerError(RuntimeError):
    pass


def require_root() -> None:
    if os.geteuid() != 0:
        raise InstallerError("OpenStream installer must run as root. Use: sudo ./install.sh")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True)


def detect_target_user(explicit: str | None = None) -> tuple[str, Path]:
    candidates = [explicit, os.environ.get("SUDO_USER")]
    try:
        candidates.append(os.getlogin())
    except OSError:
        pass
    try:
        candidates.append(subprocess.check_output(["logname"], text=True).strip())
    except Exception:
        pass

    for user in candidates:
        if not user or user == "root":
            continue
        try:
            entry = pwd.getpwnam(user)
        except KeyError:
            continue
        return user, Path(entry.pw_dir)

    raise InstallerError("Could not detect the non-root desktop user. Pass --target-user USER.")


def prompt_port(default: int = DEFAULT_SOCKS_PORT) -> int:
    print("Choose the SOCKS5 port OpenStream should expose on this machine.")
    print(f"Default: {default}")
    while True:
        raw = input("Port: ").strip()
        if not raw:
            return default
        try:
            port = validate_port(raw)
        except ValueError as exc:
            print(f"Invalid port: {exc}")
            continue
        if port < 1024:
            print("WARNING: ports below 1024 may require extra privileges and can be annoying.")
            confirm = input("Use this port anyway? [y/N]: ").strip().lower()
            if confirm != "y":
                continue
        return port


def get_nameservers() -> list[str]:
    nameservers: list[str] = []
    try:
        data = Path("/etc/resolv.conf").read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        data = ""
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "nameserver":
            ns = parts[1]
            if ns in {"127.0.0.1", "127.0.0.53", "::1"}:
                continue
            if ns not in nameservers:
                nameservers.append(ns)
    for fallback in ("1.1.1.1", "9.9.9.9"):
        if fallback not in nameservers:
            nameservers.append(fallback)
    return nameservers[:3]


def write_netns_resolv_conf() -> None:
    NETNS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"nameserver {ns}" for ns in get_nameservers()]
    lines.append("options timeout:2 attempts:2")
    NETNS_RESOLV_CONF.write_text("\n".join(lines) + "\n", encoding="utf-8")
    NETNS_RESOLV_CONF.chmod(0o644)


def copy_python_package(source_root: Path) -> None:
    source_package = source_root / "src" / "openstream"
    if not source_package.exists():
        raise InstallerError(f"OpenStream source package not found: {source_package}")
    target_package = PYTHON_LIB_DIR / "openstream"
    if target_package.exists():
        shutil.rmtree(target_package)
    PYTHON_LIB_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_package, target_package)


def write_cli_wrapper() -> None:
    BIN_PATH.parent.mkdir(parents=True, exist_ok=True)
    BIN_PATH.write_text(
        f"""#!/usr/bin/env sh
set -eu
export PYTHONPATH="{PYTHON_LIB_DIR}${{PYTHONPATH:+:$PYTHONPATH}}"
exec python3 -m openstream.cli "$@"
""",
        encoding="utf-8",
    )
    BIN_PATH.chmod(0o755)


def ensure_directories(cfg: OpenStreamConfig, target_user: str | None = None) -> None:
    for path in [
        CONFIG_DIR,
        OPENVPN_DIR,
        AUTH_DIR,
        NETNS_DIR,
        STATE_ROOT,
        PROFILES_DIR,
        STATE_DIR,
        cfg.runtime_dir,
        CACHE_DIR,
        RUN_DIR,
        cfg.libexec_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)
    cfg.drop_dir.mkdir(parents=True, exist_ok=True)
    if target_user:
        try:
            entry = pwd.getpwnam(target_user)
            for root, dirs, files in os.walk(cfg.drop_dir):
                os.chown(root, entry.pw_uid, entry.pw_gid)
                for name in dirs:
                    os.chown(Path(root) / name, entry.pw_uid, entry.pw_gid)
                for name in files:
                    os.chown(Path(root) / name, entry.pw_uid, entry.pw_gid)
        except PermissionError:
            pass


def initialize_state_files(cfg: OpenStreamConfig) -> None:
    if not LISTEN_IP_PATH.exists():
        LISTEN_IP_PATH.write_text(LOCAL_LISTEN_IP + "\n", encoding="utf-8")
        LISTEN_IP_PATH.chmod(0o644)
    if not PROFILE_REGISTRY_PATH.exists():
        PROFILE_REGISTRY_PATH.write_text('{"profiles": []}\n', encoding="utf-8")
        PROFILE_REGISTRY_PATH.chmod(0o644)


def install(args: argparse.Namespace) -> int:
    require_root()
    source_root = Path(args.source_root).resolve()
    target_user, target_home = detect_target_user(args.target_user)
    drop_dir = Path(args.drop_dir).expanduser() if args.drop_dir else target_home / "Desktop" / "opst"
    port = validate_port(args.port) if args.port else prompt_port()

    if not args.skip_dependency_check:
        ensure_dependencies_interactive(auto_install=args.yes, assume_no=args.no)

    cfg = OpenStreamConfig(port=port, drop_dir=drop_dir)
    ensure_directories(cfg, target_user=target_user)
    write_config(cfg)
    initialize_state_files(cfg)
    write_netns_resolv_conf()
    copy_python_package(source_root)
    write_cli_wrapper()
    install_runtime_templates(cfg)
    daemon_reload()

    print()
    print(f"OpenStream v{VERSION} installed successfully.")
    print("Drop your .ovpn files into:")
    print(f"  {cfg.drop_dir}")
    print()
    print("Then run:")
    print("  opst on")
    print()
    print("Local SOCKS5 endpoint will be:")
    print(f"  {cfg.local_endpoint}")
    return 0


def _safe_rmtree(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        else:
            shutil.rmtree(path, ignore_errors=True)


def uninstall(_args: argparse.Namespace | None = None) -> int:
    require_root()
    run(["systemctl", "stop", "opst-localproxy.service", "opst-socks.service", "opst-openvpn.service", "opst-setup.service"], check=False)
    run(["systemctl", "disable", *SERVICE_NAMES], check=False)

    cleanup_script = LIBEXEC_DIR / "opst-netns.sh"
    if cleanup_script.exists():
        run([str(cleanup_script), "down"], check=False)

    for service in SERVICE_NAMES:
        (SYSTEMD_DIR / service).unlink(missing_ok=True)
    run(["systemctl", "daemon-reload"], check=False)

    if shutil.which("ip"):
        run(["sh", "-c", "ip netns pids opstns 2>/dev/null | xargs -r kill || true"], check=False)
        run(["ip", "netns", "del", "opstns"], check=False)
        run(["ip", "link", "del", "veth-opst-host"], check=False)

    _safe_rmtree(LIBEXEC_DIR)
    BIN_PATH.unlink(missing_ok=True)
    _safe_rmtree(CONFIG_DIR)
    _safe_rmtree(OPENVPN_DIR)
    _safe_rmtree(NETNS_DIR)
    _safe_rmtree(STATE_ROOT)
    _safe_rmtree(CACHE_DIR)
    _safe_rmtree(RUN_DIR)

    print("OpenStream uninstalled.")
    print("Your original .ovpn drop folder was not deleted.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install or uninstall OpenStream")
    sub = parser.add_subparsers(dest="command", required=True)

    install_parser = sub.add_parser("install", help="install OpenStream")
    install_parser.add_argument("--source-root", required=True)
    install_parser.add_argument("--target-user")
    install_parser.add_argument("--drop-dir")
    install_parser.add_argument("--port")
    install_parser.add_argument("--yes", action="store_true", help="install missing dependencies using apt without prompting")
    install_parser.add_argument("--no", action="store_true", help="abort instead of offering apt install when dependencies are missing")
    install_parser.add_argument("--skip-dependency-check", action="store_true", help="developer/testing only")
    install_parser.set_defaults(func=install)

    uninstall_parser = sub.add_parser("uninstall", help="uninstall OpenStream")
    uninstall_parser.set_defaults(func=uninstall)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (InstallerError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
