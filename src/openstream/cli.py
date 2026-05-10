from __future__ import annotations

import argparse
import os
import subprocess
import sys

from .config import BIN_PATH, LAN_LISTEN_IP, LOCAL_LISTEN_IP, VERSION, load_config, read_listen_ip, write_listen_ip
from .installer import uninstall as uninstall_command
from .profiles import (
    choose_cached_profile,
    current_profile_id,
    load_registry,
    print_profiles,
    refresh_profiles,
    remove_profile,
    select_profile_interactive,
    set_current_profile,
)
from .systemd import service_state, start_all, stop_all, systemctl


def require_root_or_reexec(argv: list[str]) -> None:
    if os.geteuid() == 0:
        return

    # After installation, always re-enter through the public wrapper. The wrapper
    # sets PYTHONPATH to /usr/local/lib/opst/python before executing the module.
    # Calling sys.argv[0] directly is fragile because `python -m openstream.cli`
    # exposes the module file path, not the wrapper command.
    if BIN_PATH.exists():
        os.execvp("sudo", ["sudo", str(BIN_PATH), *argv])

    # Development fallback for running from a checkout before install. Keep the
    # current PYTHONPATH visible across sudo by passing it through env explicitly.
    env_args = ["env"]
    pythonpath = os.environ.get("PYTHONPATH")
    if pythonpath:
        env_args.append(f"PYTHONPATH={pythonpath}")
    os.execvp("sudo", ["sudo", *env_args, sys.executable, "-m", "openstream.cli", *argv])


def start_flow(lan: bool) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    write_listen_ip(cfg, lan=lan)
    profiles = refresh_profiles(cfg)
    profile = select_profile_interactive(cfg, profiles)
    set_current_profile(cfg, profile)
    start_all()
    listen_ip = LAN_LISTEN_IP if lan else LOCAL_LISTEN_IP
    print(f"OpenStream started with profile: {profile.name}")
    print(f"SOCKS5 endpoint: socks5h://{listen_ip}:{cfg.port}")
    if lan:
        print(f"WARNING: LAN mode exposes SOCKS5 on 0.0.0.0:{cfg.port}")
        print("Only use this on trusted networks.")
    return 0


def off_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    stop_all()
    print("OpenStream stopped.")
    return 0


def restart_flow(args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    stop_all()
    return start_flow(lan=args.lan)


def status_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    profiles = load_registry(cfg)
    current_id = current_profile_id(cfg, profiles)
    current = next((p for p in profiles if p.id == current_id), None)
    listen_ip = read_listen_ip(cfg)
    print("OpenStream status")
    print(f"Version: v{VERSION}")
    print(f"Profile: {current.name if current else 'none'}")
    print(f"Auth: {current.label if current else 'none'}")
    print(f"Namespace: {cfg.namespace}")
    print(f"Listen: {listen_ip}:{cfg.port}")
    for unit in ("opst-setup.service", "opst-openvpn.service", "opst-socks.service", "opst-localproxy.service"):
        print(f"{unit.replace('opst-', '').replace('.service', '')}: {service_state(unit)}")
    return 0


def current_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    profiles = load_registry(cfg)
    current_id = current_profile_id(cfg, profiles)
    current = next((p for p in profiles if p.id == current_id), None)
    listen_ip = read_listen_ip(cfg)
    if not current:
        print("Current profile: none")
        print(f"Endpoint: socks5h://{listen_ip}:{cfg.port}")
        return 1
    print(f"Current profile: {current.name}")
    print(f"Endpoint: socks5h://{listen_ip}:{cfg.port}")
    return 0


def profiles_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    print_profiles(cfg)
    return 0


def add_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    profiles = refresh_profiles(cfg)
    print_profiles(cfg, profiles)
    return 0


def use_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    profile = choose_cached_profile(cfg)
    set_current_profile(cfg, profile)
    print(f"Active profile set to: {profile.name}")
    if service_state("opst-openvpn.service") == "active":
        systemctl("restart", "opst-openvpn.service", "opst-socks.service", "opst-localproxy.service")
        print("Running services restarted.")
    return 0


def remove_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    profile = choose_cached_profile(cfg)
    confirm = input(f"Remove cached profile '{profile.name}'? This will not delete the original drop-folder file. [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return 1
    remove_profile(cfg, profile)
    print(f"Removed cached profile: {profile.name}")
    return 0


def test_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    return subprocess.call(["curl", "--proxy", f"socks5h://127.0.0.1:{cfg.port}", "https://ifconfig.me"])


def logs_flow(args: argparse.Namespace) -> int:
    unit_map = {
        "setup": ["opst-setup.service"],
        "openvpn": ["opst-openvpn.service"],
        "socks": ["opst-socks.service"],
        "localproxy": ["opst-localproxy.service"],
        "all": ["opst-setup.service", "opst-openvpn.service", "opst-socks.service", "opst-localproxy.service"],
    }
    units = unit_map.get(args.scope, ["opst-openvpn.service", "opst-socks.service", "opst-localproxy.service"])
    cmd = ["journalctl"]
    for unit in units:
        cmd.extend(["-u", unit])
    cmd.append("-f")
    os.execvp(cmd[0], cmd)
    return 0


def uninstall_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    return uninstall_command(None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="opst", description="OpenStream control CLI")
    parser.add_argument("--version", action="version", version=f"OpenStream v{VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    on = sub.add_parser("on", help="start OpenStream")
    on.add_argument("--lan", action="store_true", help="bind SOCKS listener to 0.0.0.0")
    on.set_defaults(func=lambda args: start_flow(args.lan))

    off = sub.add_parser("off", help="stop OpenStream")
    off.set_defaults(func=off_flow)

    restart = sub.add_parser("restart", help="restart OpenStream")
    restart.add_argument("--lan", action="store_true", help="restart in LAN mode")
    restart.set_defaults(func=restart_flow)

    sub.add_parser("status", help="show service status").set_defaults(func=status_flow)
    sub.add_parser("current", help="show current profile").set_defaults(func=current_flow)
    sub.add_parser("profiles", help="list profiles").set_defaults(func=profiles_flow)
    sub.add_parser("add", help="scan drop folder for new .ovpn files").set_defaults(func=add_flow)
    sub.add_parser("use", help="switch current profile interactively").set_defaults(func=use_flow)
    sub.add_parser("remove", help="remove a cached profile interactively").set_defaults(func=remove_flow)
    sub.add_parser("test", help="test local SOCKS endpoint").set_defaults(func=test_flow)

    logs = sub.add_parser("logs", help="follow OpenStream logs")
    logs.add_argument("scope", nargs="?", default="default", choices=["default", "setup", "openvpn", "socks", "localproxy", "all"])
    logs.set_defaults(func=logs_flow)

    sub.add_parser("uninstall", help="uninstall OpenStream").set_defaults(func=uninstall_flow)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
