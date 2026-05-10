from pathlib import Path

from openstream import cli


def test_non_root_reexec_uses_installed_wrapper(monkeypatch, tmp_path: Path) -> None:
    wrapper = tmp_path / "opst"
    wrapper.write_text("#!/bin/sh\n", encoding="utf-8")

    captured: dict[str, object] = {}
    monkeypatch.setattr(cli.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(cli, "BIN_PATH", wrapper)

    def fake_execvp(program: str, args: list[str]) -> None:
        captured["program"] = program
        captured["args"] = args
        raise RuntimeError("stop exec")

    monkeypatch.setattr(cli.os, "execvp", fake_execvp)

    try:
        cli.require_root_or_reexec(["on", "--lan"])
    except RuntimeError as exc:
        assert str(exc) == "stop exec"

    assert captured == {
        "program": "sudo",
        "args": ["sudo", str(wrapper), "on", "--lan"],
    }


def test_non_root_reexec_has_development_fallback(monkeypatch, tmp_path: Path) -> None:
    missing_wrapper = tmp_path / "missing-opst"
    captured: dict[str, object] = {}
    monkeypatch.setattr(cli.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(cli, "BIN_PATH", missing_wrapper)
    monkeypatch.setenv("PYTHONPATH", "/tmp/openstream-src")

    def fake_execvp(program: str, args: list[str]) -> None:
        captured["program"] = program
        captured["args"] = args
        raise RuntimeError("stop exec")

    monkeypatch.setattr(cli.os, "execvp", fake_execvp)

    try:
        cli.require_root_or_reexec(["status"])
    except RuntimeError as exc:
        assert str(exc) == "stop exec"

    assert captured["program"] == "sudo"
    args = captured["args"]
    assert args[:3] == ["sudo", "env", "PYTHONPATH=/tmp/openstream-src"]
    assert args[-3:] == ["-m", "openstream.cli", "status"]


def test_status_displays_version(monkeypatch, tmp_path, capsys) -> None:
    from openstream.config import OpenStreamConfig

    cfg = OpenStreamConfig(
        port=2086,
        drop_dir=tmp_path / "drop",
        current_ovpn=tmp_path / "current.ovpn",
        listen_ip_path=tmp_path / "listen_ip",
        registry_path=tmp_path / "profiles.json",
    )
    monkeypatch.setattr(cli, "load_config", lambda: cfg)
    monkeypatch.setattr(cli, "load_registry", lambda cfg_arg: [])
    monkeypatch.setattr(cli, "current_profile_id", lambda cfg_arg, profiles: None)
    monkeypatch.setattr(cli, "read_listen_ip", lambda cfg_arg: "127.0.0.1")
    monkeypatch.setattr(cli, "service_state", lambda unit: "inactive")

    assert cli.status_flow(None) == 0

    out = capsys.readouterr().out
    assert "OpenStream status" in out
    assert "Version: v1.0.0" in out
    assert "Listen: 127.0.0.1:2086" in out


def test_parser_version_flag(capsys) -> None:
    parser = cli.build_parser()
    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0

    assert "OpenStream v1.0.0" in capsys.readouterr().out


def test_empty_opst_prints_command_reference(capsys) -> None:
    assert cli.main([]) == 2
    out = capsys.readouterr().out
    assert "A command is required" in out
    assert "opst changeport" in out
    assert "opst on" in out


def test_changeport_updates_config_and_renders_runtime(monkeypatch, tmp_path: Path, capsys) -> None:
    from openstream.config import OpenStreamConfig, load_config

    cfg = OpenStreamConfig(
        port=2086,
        drop_dir=tmp_path / "drop",
        current_ovpn=tmp_path / "current.ovpn",
        listen_ip_path=tmp_path / "listen_ip",
        registry_path=tmp_path / "profiles.json",
        libexec_dir=tmp_path / "libexec",
    )
    config_path = tmp_path / "config.toml"
    calls: list[str] = []

    monkeypatch.setattr(cli.os, "geteuid", lambda: 0)
    monkeypatch.setattr(cli, "load_config", lambda: cfg)
    monkeypatch.setattr(cli, "CONFIG_PATH", config_path)
    monkeypatch.setattr(cli, "service_state", lambda unit: "inactive")
    monkeypatch.setattr(cli, "install_runtime_templates", lambda cfg_arg: calls.append(f"render:{cfg_arg.port}"))
    monkeypatch.setattr(cli, "daemon_reload", lambda: calls.append("daemon-reload"))

    assert cli.main(["changeport", "2099"]) == 0

    written = load_config(config_path)
    assert written.port == 2099
    assert calls == ["render:2099", "daemon-reload"]
    out = capsys.readouterr().out
    assert "Port changed successfully" in out
    assert "socks5h://127.0.0.1:2099" in out
