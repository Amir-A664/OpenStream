from __future__ import annotations

import os
import shutil
import sys
import textwrap
from dataclasses import dataclass


def supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("OPENSTREAM_COLOR") == "always":
        return True
    if os.environ.get("OPENSTREAM_COLOR") == "never":
        return False
    return sys.stdout.isatty()


@dataclass(frozen=True)
class Palette:
    reset: str = "\033[0m"
    bold: str = "\033[1m"
    dim: str = "\033[2m"
    cyan: str = "\033[36m"
    green: str = "\033[32m"
    yellow: str = "\033[33m"
    red: str = "\033[31m"
    blue: str = "\033[34m"


P = Palette()


def color(text: str, code: str) -> str:
    if not supports_color():
        return text
    return f"{code}{text}{P.reset}"


def bold(text: str) -> str:
    return color(text, P.bold)


def dim(text: str) -> str:
    return color(text, P.dim)


def ok(text: str) -> str:
    return color(text, P.green)


def warn(text: str) -> str:
    return color(text, P.yellow)


def err(text: str) -> str:
    return color(text, P.red)


def info(text: str) -> str:
    return color(text, P.cyan)


def terminal_width(default: int = 78) -> int:
    return max(60, min(shutil.get_terminal_size((default, 20)).columns, 100))


def rule(title: str | None = None) -> None:
    width = terminal_width()
    if not title:
        print(dim("─" * width))
        return
    label = f" {title} "
    side = max(0, width - len(label))
    print(dim("─" * (side // 2)) + bold(label) + dim("─" * (side - side // 2)))


def header(title: str, subtitle: str | None = None) -> None:
    width = terminal_width()
    print()
    print(color("╭" + "─" * (width - 2) + "╮", P.cyan))
    inner = f" {title} ".center(width - 2)
    print(color("│", P.cyan) + bold(inner) + color("│", P.cyan))
    if subtitle:
        for line in textwrap.wrap(subtitle, width=max(40, width - 8)):
            print(color("│", P.cyan) + dim(line.center(width - 2)) + color("│", P.cyan))
    print(color("╰" + "─" * (width - 2) + "╯", P.cyan))
    print()


def section(title: str) -> None:
    print()
    print(info(f"▸ {title}"))


def success(text: str) -> None:
    print(ok(f"✓ {text}"))


def warning(text: str) -> None:
    print(warn(f"! {text}"))


def error(text: str) -> None:
    print(err(f"✗ {text}"))


def step(text: str) -> None:
    print(f"  {info('•')} {text}")


def key_value(key: str, value: str) -> None:
    print(f"  {dim(key + ':')} {value}")


def progress(label: str, current: int, total: int) -> None:
    width = 24
    total = max(1, total)
    current = max(0, min(current, total))
    filled = round(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    print(f"  {label:<28} {color(bar, P.green)} {current}/{total}")


def clear_screen() -> None:
    if sys.stdout.isatty() and os.environ.get("OPENSTREAM_NO_CLEAR") != "1":
        os.system("clear")


def command_reference() -> str:
    return """OpenStream command reference

Service control:
  opst on                 start OpenStream in local mode
  opst on --lan           start OpenStream in LAN mode
  opst on --latch         start with forceful VPN reconnect (server mode)
  opst on --lan --latch   start in LAN mode with forceful VPN reconnect
  opst off                stop OpenStream
  opst restart            restart OpenStream in local mode
  opst restart --lan      restart OpenStream in LAN mode
  opst restart --latch    restart with forceful VPN reconnect (server mode)

Profile management:
  opst current            show the active profile
  opst profiles           list cached profiles
  opst add                scan the drop folder for new .ovpn files
  opst use                switch the active profile interactively
  opst remove             remove a cached profile interactively

Testing and logs:
  opst status             show service status and endpoint details
  opst test               test the local SOCKS5 endpoint
  opst logs               follow OpenStream logs
  opst logs openvpn       follow only OpenVPN logs

Configuration:
  opst changeport         change the SOCKS5 port interactively
  opst changeport PORT    change the SOCKS5 port directly
  opst --version          show the installed version
  sudo opst uninstall     uninstall OpenStream
"""


def print_command_reference() -> None:
    rule("Commands")
    print(command_reference().rstrip())


def wrap(text: str, *, indent: str = "") -> str:
    width = terminal_width() - len(indent)
    return "\n".join(indent + line for line in textwrap.wrap(text, width=max(40, width)))
