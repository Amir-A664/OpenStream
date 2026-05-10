from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

APP_NAME = "opst"
PROJECT_NAME = "OpenStream"
REPOSITORY_URL = "https://github.com/Amir-A664/OpenStream/"
VERSION = "1.0.0"

NS_NAME = "opstns"
HOST_IF = "veth-opst-host"
NS_IF = "veth-opst-ns"
HOST_IP_CIDR = "10.200.1.1/30"
NS_IP_CIDR = "10.200.1.2/30"
NS_HOST_IP = "10.200.1.1"
NS_BIND_IP = "10.200.1.2"
TUN_DEV = "tun-opst"
LOCAL_LISTEN_IP = "127.0.0.1"
LAN_LISTEN_IP = "0.0.0.0"
DEFAULT_SOCKS_PORT = 2086
DATA_CIPHERS = "AES-128-CBC:AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305"
DATA_CIPHERS_FALLBACK = "AES-128-CBC"

CONFIG_DIR = Path("/etc/opst")
CONFIG_PATH = CONFIG_DIR / "config.toml"
LISTEN_IP_PATH = CONFIG_DIR / "listen_ip"
PROFILE_REGISTRY_PATH = CONFIG_DIR / "profiles.json"

OPENVPN_DIR = Path("/etc/openvpn/opst")
AUTH_DIR = OPENVPN_DIR / "auth"
CURRENT_OVPN = OPENVPN_DIR / "current.ovpn"

NETNS_DIR = Path("/etc/netns") / NS_NAME
NETNS_RESOLV_CONF = NETNS_DIR / "resolv.conf"

STATE_ROOT = Path("/var/lib/opst")
PROFILES_DIR = STATE_ROOT / "profiles"
STATE_DIR = STATE_ROOT / "state"
RUNTIME_DIR = STATE_ROOT / "runtime"
CACHE_DIR = Path("/var/cache/opst")
RUN_DIR = Path("/run/opst")

BIN_PATH = Path("/usr/local/bin/opst")
LIBEXEC_DIR = Path("/usr/local/lib/opst")
PYTHON_LIB_DIR = LIBEXEC_DIR / "python"
TEMPLATE_DIR = LIBEXEC_DIR / "templates"
SYSTEMD_DIR = Path("/etc/systemd/system")

SERVICE_NAMES = [
    "opst-setup.service",
    "opst-openvpn.service",
    "opst-socks.service",
    "opst-localproxy.service",
]

AUTH_LABELS = {
    "userpass": "username/password saved",
    "cert": "certificate-based",
    "hybrid": "hybrid username/password + certificate",
    "static_key": "static key / tls-auth / tls-crypt",
    "unknown": "unknown",
}


@dataclass(frozen=True)
class OpenStreamConfig:
    project_name: str = PROJECT_NAME
    cli: str = APP_NAME
    version: str = VERSION
    namespace: str = NS_NAME
    host_if: str = HOST_IF
    ns_if: str = NS_IF
    host_ip_cidr: str = HOST_IP_CIDR
    ns_ip_cidr: str = NS_IP_CIDR
    ns_host_ip: str = NS_HOST_IP
    ns_bind_ip: str = NS_BIND_IP
    tun_dev: str = TUN_DEV
    port: int = DEFAULT_SOCKS_PORT
    local_listen_ip: str = LOCAL_LISTEN_IP
    lan_listen_ip: str = LAN_LISTEN_IP
    drop_dir: Path = Path("/tmp/opst-drop")
    profiles_dir: Path = PROFILES_DIR
    auth_dir: Path = AUTH_DIR
    current_ovpn: Path = CURRENT_OVPN
    listen_ip_path: Path = LISTEN_IP_PATH
    registry_path: Path = PROFILE_REGISTRY_PATH
    state_dir: Path = STATE_DIR
    runtime_dir: Path = RUNTIME_DIR
    libexec_dir: Path = LIBEXEC_DIR

    @property
    def local_endpoint(self) -> str:
        return f"socks5h://127.0.0.1:{self.port}"

    @property
    def lan_endpoint(self) -> str:
        return f"socks5h://0.0.0.0:{self.port}"

    def template_values(self) -> dict[str, str]:
        return {
            "APP_NAME": APP_NAME,
            "PROJECT_NAME": PROJECT_NAME,
            "NS_NAME": self.namespace,
            "HOST_IF": self.host_if,
            "NS_IF": self.ns_if,
            "HOST_IP_CIDR": self.host_ip_cidr,
            "NS_IP_CIDR": self.ns_ip_cidr,
            "NS_HOST_IP": self.ns_host_ip,
            "NS_BIND_IP": self.ns_bind_ip,
            "TUN_DEV": self.tun_dev,
            "PROXY_PORT": str(self.port),
            "LOCAL_LISTEN_IP": self.local_listen_ip,
            "LAN_LISTEN_IP": self.lan_listen_ip,
            "CONFIG_PATH": str(CONFIG_PATH),
            "LISTEN_IP_PATH": str(self.listen_ip_path),
            "CURRENT_OVPN": str(self.current_ovpn),
            "STATE_DIR": str(self.state_dir),
            "RUNTIME_DIR": str(self.runtime_dir),
            "LIBEXEC_DIR": str(self.libexec_dir),
        }


def validate_port(value: str | int) -> int:
    text = str(value).strip()
    if not text.isdigit():
        raise ValueError("Port must be numeric.")
    port = int(text)
    if port < 1 or port > 65535:
        raise ValueError("Port must be between 1 and 65535.")
    return port


def config_to_toml(cfg: OpenStreamConfig) -> str:
    return f"""[project]
name = "{cfg.project_name}"
cli = "{cfg.cli}"
version = "{cfg.version}"
repository = "{REPOSITORY_URL}"

[network]
namespace = "{cfg.namespace}"
host_if = "{cfg.host_if}"
ns_if = "{cfg.ns_if}"
host_ip_cidr = "{cfg.host_ip_cidr}"
ns_ip_cidr = "{cfg.ns_ip_cidr}"
ns_host_ip = "{cfg.ns_host_ip}"
ns_bind_ip = "{cfg.ns_bind_ip}"
tun_dev = "{cfg.tun_dev}"

[proxy]
port = {cfg.port}
local_listen_ip = "{cfg.local_listen_ip}"
lan_listen_ip = "{cfg.lan_listen_ip}"

[paths]
drop_dir = "{cfg.drop_dir}"
profiles_dir = "{cfg.profiles_dir}"
auth_dir = "{cfg.auth_dir}"
current_ovpn = "{cfg.current_ovpn}"
listen_ip = "{cfg.listen_ip_path}"
registry = "{cfg.registry_path}"
state_dir = "{cfg.state_dir}"
runtime_dir = "{cfg.runtime_dir}"
libexec_dir = "{cfg.libexec_dir}"
"""


def write_config(cfg: OpenStreamConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config_to_toml(cfg), encoding="utf-8")
    path.chmod(0o644)


def with_port(cfg: OpenStreamConfig, port: int) -> OpenStreamConfig:
    return replace(cfg, port=validate_port(port))


def _parse_simple_toml(text: str) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            data.setdefault(section, {})
            continue
        if "=" not in line or not section:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            parsed: Any = value[1:-1]
        else:
            try:
                parsed = int(value)
            except ValueError:
                parsed = value
        data.setdefault(section, {})[key] = parsed
    return data


def _load_toml(path: Path) -> dict[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:
        return _parse_simple_toml(text)
    return tomllib.loads(text)


def load_config(path: Path = CONFIG_PATH) -> OpenStreamConfig:
    data = _load_toml(path)
    network = data.get("network", {})
    proxy = data.get("proxy", {})
    paths = data.get("paths", {})
    project = data.get("project", {})
    return OpenStreamConfig(
        project_name=str(project.get("name", PROJECT_NAME)),
        cli=str(project.get("cli", APP_NAME)),
        version=str(project.get("version", VERSION)),
        namespace=str(network.get("namespace", NS_NAME)),
        host_if=str(network.get("host_if", HOST_IF)),
        ns_if=str(network.get("ns_if", NS_IF)),
        host_ip_cidr=str(network.get("host_ip_cidr", HOST_IP_CIDR)),
        ns_ip_cidr=str(network.get("ns_ip_cidr", NS_IP_CIDR)),
        ns_host_ip=str(network.get("ns_host_ip", NS_HOST_IP)),
        ns_bind_ip=str(network.get("ns_bind_ip", NS_BIND_IP)),
        tun_dev=str(network.get("tun_dev", TUN_DEV)),
        port=validate_port(proxy.get("port", DEFAULT_SOCKS_PORT)),
        local_listen_ip=str(proxy.get("local_listen_ip", LOCAL_LISTEN_IP)),
        lan_listen_ip=str(proxy.get("lan_listen_ip", LAN_LISTEN_IP)),
        drop_dir=Path(str(paths.get("drop_dir", "/tmp/opst-drop"))),
        profiles_dir=Path(str(paths.get("profiles_dir", PROFILES_DIR))),
        auth_dir=Path(str(paths.get("auth_dir", AUTH_DIR))),
        current_ovpn=Path(str(paths.get("current_ovpn", CURRENT_OVPN))),
        listen_ip_path=Path(str(paths.get("listen_ip", LISTEN_IP_PATH))),
        registry_path=Path(str(paths.get("registry", PROFILE_REGISTRY_PATH))),
        state_dir=Path(str(paths.get("state_dir", STATE_DIR))),
        runtime_dir=Path(str(paths.get("runtime_dir", RUNTIME_DIR))),
        libexec_dir=Path(str(paths.get("libexec_dir", LIBEXEC_DIR))),
    )


def read_listen_ip(cfg: OpenStreamConfig) -> str:
    try:
        value = cfg.listen_ip_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return cfg.local_listen_ip
    if value not in {cfg.local_listen_ip, cfg.lan_listen_ip}:
        return cfg.local_listen_ip
    return value


def write_listen_ip(cfg: OpenStreamConfig, lan: bool = False) -> str:
    value = cfg.lan_listen_ip if lan else cfg.local_listen_ip
    cfg.listen_ip_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.listen_ip_path.write_text(value + "\n", encoding="utf-8")
    cfg.listen_ip_path.chmod(0o644)
    return value
