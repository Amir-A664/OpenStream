from argparse import Namespace
from pathlib import Path

from openstream import installer
from openstream.config import OpenStreamConfig


def test_installer_completion_summary_reaches_config_path(monkeypatch, tmp_path: Path, capsys) -> None:
    cfg_holder: dict[str, OpenStreamConfig] = {}

    monkeypatch.setattr(installer, "require_root", lambda: None)
    monkeypatch.setattr(installer, "detect_target_user", lambda explicit=None: ("tester", tmp_path / "home" / "tester"))
    monkeypatch.setattr(installer, "ensure_dependencies_interactive", lambda **kwargs: None)
    monkeypatch.setattr(installer, "ensure_directories", lambda cfg, target_user=None: None)
    monkeypatch.setattr(installer, "write_config", lambda cfg: cfg_holder.setdefault("cfg", cfg))
    monkeypatch.setattr(installer, "initialize_state_files", lambda cfg: None)
    monkeypatch.setattr(installer, "write_netns_resolv_conf", lambda: None)
    monkeypatch.setattr(installer, "copy_python_package", lambda source_root: None)
    monkeypatch.setattr(installer, "write_cli_wrapper", lambda: None)
    monkeypatch.setattr(installer, "install_runtime_templates", lambda cfg: None)
    monkeypatch.setattr(installer, "daemon_reload", lambda: None)
    monkeypatch.setattr(installer, "clear_screen", lambda: None)

    args = Namespace(
        source_root=str(tmp_path),
        target_user="tester",
        drop_dir=str(tmp_path / "drop"),
        port="2092",
        skip_dependency_check=True,
        yes=False,
        no=False,
    )

    assert installer.install(args) == 0

    out = capsys.readouterr().out
    assert "OpenStream v1.0.0 installed successfully" in out
    assert "SOCKS5 endpoint" in out
    assert "socks5h://127.0.0.1:2092" in out
    assert "Config:" in out
    assert str(installer.CONFIG_PATH) in out
    assert cfg_holder["cfg"].port == 2092


def test_ensure_directories_does_not_create_config_file_as_directory(monkeypatch, tmp_path: Path) -> None:
    cfg = OpenStreamConfig(
        port=2086,
        drop_dir=tmp_path / "drop",
        profiles_dir=tmp_path / "var" / "profiles",
        auth_dir=tmp_path / "etc" / "openvpn" / "opst" / "auth",
        current_ovpn=tmp_path / "etc" / "openvpn" / "opst" / "current.ovpn",
        listen_ip_path=tmp_path / "etc" / "opst" / "listen_ip",
        registry_path=tmp_path / "etc" / "opst" / "profiles.json",
        state_dir=tmp_path / "var" / "state",
        runtime_dir=tmp_path / "var" / "runtime",
        libexec_dir=tmp_path / "usr" / "local" / "lib" / "opst",
    )
    monkeypatch.setattr(installer, "CONFIG_DIR", tmp_path / "etc" / "opst")
    monkeypatch.setattr(installer, "OPENVPN_DIR", tmp_path / "etc" / "openvpn" / "opst")
    monkeypatch.setattr(installer, "AUTH_DIR", cfg.auth_dir)
    monkeypatch.setattr(installer, "NETNS_DIR", tmp_path / "etc" / "netns" / "opstns")
    monkeypatch.setattr(installer, "STATE_ROOT", tmp_path / "var" / "lib" / "opst")
    monkeypatch.setattr(installer, "PROFILES_DIR", cfg.profiles_dir)
    monkeypatch.setattr(installer, "STATE_DIR", cfg.state_dir)
    monkeypatch.setattr(installer, "CACHE_DIR", tmp_path / "var" / "cache" / "opst")
    monkeypatch.setattr(installer, "RUN_DIR", tmp_path / "run" / "opst")

    installer.ensure_directories(cfg)

    assert (tmp_path / "etc" / "opst").is_dir()
    assert not (tmp_path / "etc" / "opst" / "config.toml").exists()
    assert cfg.drop_dir.is_dir()
