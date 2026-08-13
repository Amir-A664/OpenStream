from __future__ import annotations

import subprocess
from pathlib import Path
from string import Template

from .config import SERVICE_NAMES, SYSTEMD_DIR, OpenStreamConfig

TEMPLATE_ROOT = Path(__file__).with_name("templates")

SCRIPT_TEMPLATES = {
    "opst-netns.sh.tpl": "opst-netns.sh",
    "opst-start-socks.sh.tpl": "opst-start-socks.sh",
    "opst-start-localproxy.sh.tpl": "opst-start-localproxy.sh",
    "opst-wait-socks-ready.sh.tpl": "opst-wait-socks-ready.sh",
}

SERVICE_TEMPLATES = {
    "opst-setup.service.tpl": "opst-setup.service",
    "opst-openvpn.service.tpl": "opst-openvpn.service",
    "opst-socks.service.tpl": "opst-socks.service",
    "opst-localproxy.service.tpl": "opst-localproxy.service",
}


def render_template(path: Path, values: dict[str, str]) -> str:
    return Template(path.read_text(encoding="utf-8")).safe_substitute(values)


def install_runtime_templates(cfg: OpenStreamConfig) -> None:
    values = cfg.template_values()
    cfg.libexec_dir.mkdir(parents=True, exist_ok=True)
    for template_name, output_name in SCRIPT_TEMPLATES.items():
        src = TEMPLATE_ROOT / template_name
        dst = cfg.libexec_dir / output_name
        dst.write_text(render_template(src, values), encoding="utf-8")
        dst.chmod(0o755)

    SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    systemd_root = TEMPLATE_ROOT / "systemd"
    for template_name, output_name in SERVICE_TEMPLATES.items():
        src = systemd_root / template_name
        dst = SYSTEMD_DIR / output_name
        dst.write_text(render_template(src, values), encoding="utf-8")
        dst.chmod(0o644)


def daemon_reload() -> None:
    subprocess.run(["systemctl", "daemon-reload"], check=True)


def systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["systemctl", *args], check=check, text=True)


def service_state(name: str) -> str:
    result = subprocess.run(["systemctl", "is-active", name], text=True, capture_output=True)
    return result.stdout.strip() or "inactive"


def start_all() -> None:
    systemctl("start", *SERVICE_NAMES)


def stop_all() -> None:
    systemctl("stop", "opst-localproxy.service", "opst-socks.service", "opst-openvpn.service", "opst-setup.service", check=False)


def disable_all() -> None:
    systemctl("disable", *SERVICE_NAMES, check=False)
