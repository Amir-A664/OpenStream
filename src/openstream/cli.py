from __future__ import annotations

import argparse
import os
import subprocess
import sys

from .config import (
    BIN_PATH,
    CONFIG_PATH,
    LAN_LISTEN_IP,
    LOCAL_LISTEN_IP,
    VERSION,
    clear_latch,
    load_config,
    read_latch,
    read_listen_ip,
    validate_port,
    with_port,
    write_config,
    write_latch,
    write_listen_ip,
)
from .installer import prompt_port
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
from .systemd import (
    daemon_reload,
    install_runtime_templates,
    service_state,
    start_all,
    stop_all,
    systemctl,
)
from .ui import (
    header,
    key_value,
    print_command_reference,
    section,
    step,
    success,
    warning,
)

SERVICE_UNITS = (
    "opst-setup.service",
    "opst-openvpn.service",
    "opst-socks.service",
    "opst-localproxy.service",
)


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


def _is_any_service_active() -> bool:
    return any(service_state(unit) == "active" for unit in SERVICE_UNITS)


def _print_endpoint(cfg, listen_ip: str) -> None:
    key_value("SOCKS5 endpoint", f"socks5h://{listen_ip}:{cfg.port}")


def start_flow(lan: bool, latch: bool = False) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    header(f"Starting OpenStream v{VERSION}", "Scanning profiles, selecting the active VPN profile, then starting the service chain.")
    write_listen_ip(cfg, lan=lan)
    listen_ip = LAN_LISTEN_IP if lan else LOCAL_LISTEN_IP
    if latch:
        write_latch(cfg)
        step("Latch mode enabled: daemon will forcefully reconnect on VPN drop.")
    else:
        clear_latch(cfg)
    section("Profile scan")
    profiles = refresh_profiles(cfg)
    profile = select_profile_interactive(cfg, profiles)
    set_current_profile(cfg, profile, latch=latch)
    success(f"Active profile: {profile.name}")

    section("Starting services")
    step("Starting namespace, OpenVPN, SOCKS5, and local forwarding services...")
    start_all()
    success("OpenStream service chain started.")
    _print_endpoint(cfg, listen_ip)
    if lan:
        warning(f"LAN mode exposes SOCKS5 on 0.0.0.0:{cfg.port}")
        print("  Only use this on trusted networks.")
    return 0


def off_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    header(f"Stopping OpenStream v{VERSION}")
    clear_latch(cfg)
    stop_all()
    success("OpenStream stopped.")
    return 0


def restart_flow(args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    header(f"Restarting OpenStream v{VERSION}")
    step("Stopping current services...")
    stop_all()
    success("Services stopped.")
    latch = getattr(args, "latch", False)
    if not latch:
        cfg = load_config()
        latch = read_latch(cfg)
    return start_flow(lan=args.lan, latch=latch)


def status_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    profiles = load_registry(cfg)
    current_id = current_profile_id(cfg, profiles)
    current = next((p for p in profiles if p.id == current_id), None)
    listen_ip = read_listen_ip(cfg)
    header("OpenStream status")
    key_value("Version", f"v{VERSION}")
    key_value("Profile", current.name if current else "none")
    key_value("Auth", current.label if current else "none")
    key_value("Namespace", cfg.namespace)
    key_value("Listen", f"{listen_ip}:{cfg.port}")
    _print_endpoint(cfg, listen_ip)
    print()
    print("Services:")
    for unit in SERVICE_UNITS:
        name = unit.replace("opst-", "").replace(".service", "")
        key_value(name, service_state(unit))
    return 0


def current_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    profiles = load_registry(cfg)
    current_id = current_profile_id(cfg, profiles)
    current = next((p for p in profiles if p.id == current_id), None)
    listen_ip = read_listen_ip(cfg)
    header("Current OpenStream profile")
    if not current:
        key_value("Profile", "none")
        _print_endpoint(cfg, listen_ip)
        warning("No active profile is selected yet. Run: opst on")
        return 1
    key_value("Profile", current.name)
    key_value("Auth", current.label)
    _print_endpoint(cfg, listen_ip)
    return 0


def profiles_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    header("OpenStream profiles")
    print_profiles(cfg)
    return 0


def add_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    header("Add OpenVPN profiles")
    step(f"Scanning drop folder: {cfg.drop_dir}")
    profiles = refresh_profiles(cfg)
    print_profiles(cfg, profiles)
    return 0


def use_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    header("Switch OpenStream profile")
    profile = choose_cached_profile(cfg)
    latch = read_latch(cfg)
    set_current_profile(cfg, profile, latch=latch)
    success(f"Active profile set to: {profile.name}")
    if service_state("opst-openvpn.service") == "active":
        step("OpenStream is running. Restarting VPN-facing services so the new profile is used...")
        systemctl("restart", "opst-openvpn.service", "opst-socks.service", "opst-localproxy.service")
        success("Running services restarted.")
    return 0


def remove_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    header("Remove cached OpenStream profile")
    profile = choose_cached_profile(cfg)
    print()
    warning("This removes the cached OpenStream copy and related auth file only.")
    print("  The original .ovpn file in the drop folder will not be deleted.")
    confirm = input(f"Remove cached profile '{profile.name}'? [y/N]: ").strip().lower()
    if confirm != "y":
        warning("Aborted.")
        return 1
    remove_profile(cfg, profile)
    success(f"Removed cached profile: {profile.name}")
    return 0


def test_flow(_args: argparse.Namespace) -> int:
    cfg = load_config()
    header("Testing OpenStream SOCKS5 endpoint")
    endpoint = f"socks5h://127.0.0.1:{cfg.port}"
    key_value("Endpoint", endpoint)
    step("Requesting https://ifconfig.me through the local SOCKS5 proxy...")
    result = subprocess.call(["curl", "--proxy", endpoint, "https://ifconfig.me"])
    print()
    if result == 0:
        success("SOCKS5 test completed.")
    else:
        warning("SOCKS5 test failed. Run 'opst status' and 'opst logs' for details.")
    return result


def logs_flow(args: argparse.Namespace) -> int:
    unit_map = {
        "setup": ["opst-setup.service"],
        "openvpn": ["opst-openvpn.service"],
        "socks": ["opst-socks.service"],
        "localproxy": ["opst-localproxy.service"],
        "all": list(SERVICE_UNITS),
    }
    units = unit_map.get(args.scope, ["opst-openvpn.service", "opst-socks.service", "opst-localproxy.service"])
    print(f"Following OpenStream logs for: {', '.join(units)}")
    cmd = ["journalctl"]
    for unit in units:
        cmd.extend(["-u", unit])
    cmd.append("-f")
    os.execvp(cmd[0], cmd)
    return 0


def changeport_flow(args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    cfg = load_config()
    header(f"Change OpenStream SOCKS5 port v{VERSION}")
    key_value("Current port", str(cfg.port))
    new_port = validate_port(args.port) if args.port else prompt_port(default=cfg.port)
    if new_port == cfg.port:
        success(f"SOCKS5 port is already set to {cfg.port}. Nothing changed.")
        return 0

    was_running = _is_any_service_active()
    if was_running:
        section("Stopping running services")
        step("OpenStream is currently active. Stopping services before changing the port...")
        stop_all()
        success("Services stopped.")

    new_cfg = with_port(cfg, new_port)
    section("Updating port across installed files")
    step(f"Writing new port to {CONFIG_PATH}...")
    write_config(new_cfg, CONFIG_PATH)
    success("Configuration updated.")
    step("Re-rendering helper scripts and systemd units with the new port...")
    install_runtime_templates(new_cfg)
    daemon_reload()
    success("Runtime scripts and systemd units updated.")

    if was_running:
        section("Restarting OpenStream")
        start_all()
        success("Services restarted with the new port.")

    listen_ip = read_listen_ip(new_cfg)
    header("Port changed successfully")
    key_value("New local endpoint", f"socks5h://127.0.0.1:{new_cfg.port}")
    key_value("Current listen", f"{listen_ip}:{new_cfg.port}")
    print("Use 'opst status' to verify the running services.")
    return 0


def uninstall_flow(_args: argparse.Namespace) -> int:
    require_root_or_reexec(sys.argv[1:])
    return uninstall_command(None)


def help_flow(_args: argparse.Namespace | None = None) -> int:
    header(f"OpenStream v{VERSION}", "A command is required after 'opst'. Choose one of the commands below.")
    print_command_reference()
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="opst", description="OpenStream control CLI", add_help=True)
    parser.add_argument("--version", action="version", version=f"OpenStream v{VERSION}")
    sub = parser.add_subparsers(dest="command", required=False)

    on = sub.add_parser("on", help="start OpenStream")
    on.add_argument("--lan", action="store_true", help="bind SOCKS listener to 0.0.0.0")
    on.add_argument("--latch", action="store_true", help="forcefully reconnect to VPN if the connection drops (server mode)")
    on.set_defaults(func=lambda args: start_flow(args.lan, latch=args.latch))

    off = sub.add_parser("off", help="stop OpenStream")
    off.set_defaults(func=off_flow)

    restart = sub.add_parser("restart", help="restart OpenStream")
    restart.add_argument("--lan", action="store_true", help="restart in LAN mode")
    restart.add_argument("--latch", action="store_true", help="forcefully reconnect to VPN if the connection drops (server mode)")
    restart.set_defaults(func=restart_flow)

    sub.add_parser("status", help="show service status").set_defaults(func=status_flow)
    sub.add_parser("current", help="show current profile").set_defaults(func=current_flow)
    sub.add_parser("profiles", help="list profiles").set_defaults(func=profiles_flow)
    sub.add_parser("add", help="scan drop folder for new .ovpn files").set_defaults(func=add_flow)
    sub.add_parser("use", help="switch current profile interactively").set_defaults(func=use_flow)
    sub.add_parser("remove", help="remove a cached profile interactively").set_defaults(func=remove_flow)
    sub.add_parser("test", help="test local SOCKS endpoint").set_defaults(func=test_flow)

    changeport = sub.add_parser("changeport", help="change the configured SOCKS5 port")
    changeport.add_argument("port", nargs="?", help="new SOCKS5 port, 1-65535")
    changeport.set_defaults(func=changeport_flow)

    logs = sub.add_parser("logs", help="follow OpenStream logs")
    logs.add_argument("scope", nargs="?", default="default", choices=["default", "setup", "openvpn", "socks", "localproxy", "all"])
    logs.set_defaults(func=logs_flow)

    sub.add_parser("uninstall", help="uninstall OpenStream").set_defaults(func=uninstall_flow)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        return help_flow(None)
    try:
        return int(args.func(args))
    except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
