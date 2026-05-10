import subprocess

import pytest

from openstream import dependencies
from openstream.dependencies import Dependency, package_list


def test_missing_required_uses_command_presence(monkeypatch) -> None:
    installed = {"ip", "iptables", "socat", "curl", "systemctl"}
    monkeypatch.setattr(dependencies, "is_installed", lambda command: command in installed)

    missing = dependencies.missing_required()

    assert [dep.command for dep in missing] == ["openvpn", "microsocks"]
    assert package_list(missing) == ["openvpn", "microsocks"]


def test_package_list_deduplicates_in_order() -> None:
    deps = [
        Dependency("ip", "iproute2"),
        Dependency("ss", "iproute2"),
        Dependency("openvpn", "openvpn"),
    ]

    assert package_list(deps) == ["iproute2", "openvpn"]


def test_assume_no_prints_manual_install_command(monkeypatch) -> None:
    monkeypatch.setattr(dependencies, "missing_required", lambda: [Dependency("openvpn", "openvpn")])
    monkeypatch.setattr(dependencies, "print_dependency_summary", lambda: [Dependency("openvpn", "openvpn")])

    with pytest.raises(RuntimeError) as exc:
        dependencies.ensure_dependencies_interactive(assume_no=True)

    assert "sudo apt install openvpn" in str(exc.value)


def test_apt_install_missing_installs_only_missing_packages(monkeypatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(dependencies.shutil, "which", lambda command: "/usr/bin/apt" if command == "apt" else None)

    def fake_run(args, check):
        calls.append(args)
        assert check is True
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(dependencies.subprocess, "run", fake_run)

    dependencies.apt_install_missing([
        Dependency("openvpn", "openvpn"),
        Dependency("microsocks", "microsocks"),
    ])

    assert calls == [
        ["apt", "update"],
        ["apt", "install", "-y", "openvpn", "microsocks"],
    ]
