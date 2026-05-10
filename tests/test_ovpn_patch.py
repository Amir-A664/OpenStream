from pathlib import Path

import pytest

from openstream.config import DATA_CIPHERS, DATA_CIPHERS_FALLBACK, TUN_DEV
from openstream.ovpn_patch import patch_ovpn_config

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_patches_legacy_username_password_profile(tmp_path: Path) -> None:
    auth_file = tmp_path / "auth.txt"
    auth_file.write_text("user\npass\n", encoding="utf-8")

    result = patch_ovpn_config(
        read_fixture("legacy-openvpn24.ovpn"),
        auth_method="hybrid",
        auth_file=auth_file,
        profile_source_dir=FIXTURES,
        external_dir=tmp_path / "external-files",
    )

    assert f"dev {TUN_DEV}" in result.text
    assert "compat-mode 2.4" not in result.text
    assert "/home/example/legacy/auth.txt" not in result.text
    assert f"data-ciphers {DATA_CIPHERS}" in result.text
    assert f"data-ciphers-fallback {DATA_CIPHERS_FALLBACK}" in result.text
    assert f"auth-user-pass {auth_file}" in result.text
    assert "auth-nocache" in result.text


def test_does_not_add_auth_user_pass_to_certificate_only_profile(tmp_path: Path) -> None:
    result = patch_ovpn_config(
        read_fixture("cert-inline.ovpn"),
        auth_method="cert",
        auth_file=None,
        profile_source_dir=FIXTURES,
        external_dir=tmp_path / "external-files",
    )

    assert "auth-user-pass" not in result.text
    assert "auth-nocache" not in result.text
    assert "<key>\n-----BEGIN PRIVATE KEY-----\nREDACTED_PRIVATE_KEY" in result.text
    assert f"dev {TUN_DEV}" in result.text


def test_preserves_inline_static_key_block(tmp_path: Path) -> None:
    result = patch_ovpn_config(
        read_fixture("static-key.ovpn"),
        auth_method="static_key",
        auth_file=None,
        profile_source_dir=FIXTURES,
        external_dir=tmp_path / "external-files",
    )

    assert "<tls-auth>\n-----BEGIN OpenVPN Static key V1-----\nREDACTED_STATIC_KEY" in result.text
    assert "auth-user-pass" not in result.text
    assert "key-direction 1" in result.text


def test_copies_and_rewrites_relative_external_files(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for name in ["ca.crt", "client.crt", "client.key", "ta.key"]:
        (source_dir / name).write_text(f"fake {name}\n", encoding="utf-8")

    raw = """
client
dev tun
remote external.example.com 1194
ca ca.crt
cert client.crt
key client.key
tls-auth ta.key 1
"""
    external_dir = tmp_path / "cache" / "external-files"
    result = patch_ovpn_config(
        raw,
        auth_method="cert",
        auth_file=None,
        profile_source_dir=source_dir,
        external_dir=external_dir,
    )

    assert len(result.external_files) == 4
    assert str(external_dir / "ca.crt") in result.text
    assert str(external_dir / "client.crt") in result.text
    assert str(external_dir / "client.key") in result.text
    assert str(external_dir / "ta.key") in result.text
    assert (external_dir / "client.key").exists()


def test_missing_relative_external_file_fails_clearly(tmp_path: Path) -> None:
    raw = """
client
dev tun
remote missing.example.com 1194
ca missing-ca.crt
"""
    with pytest.raises(RuntimeError, match="Referenced file.*missing-ca.crt"):
        patch_ovpn_config(
            raw,
            auth_method="cert",
            auth_file=None,
            profile_source_dir=tmp_path,
            external_dir=tmp_path / "external-files",
        )


def test_userpass_requires_auth_file(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="auth_file is required"):
        patch_ovpn_config(
            read_fixture("basic-auth.ovpn"),
            auth_method="userpass",
            auth_file=None,
            profile_source_dir=FIXTURES,
            external_dir=tmp_path / "external-files",
        )


def test_external_file_name_collision_uses_deterministic_suffix(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    nested = source_dir / "nested"
    nested.mkdir(parents=True)
    (source_dir / "client.key").write_text("first key\n", encoding="utf-8")
    (nested / "client.key").write_text("second key\n", encoding="utf-8")

    raw = """
client
dev tun
remote collision.example.com 1194
key client.key
tls-auth nested/client.key 1
"""
    external_dir = tmp_path / "external-files"
    result = patch_ovpn_config(
        raw,
        auth_method="cert",
        auth_file=None,
        profile_source_dir=source_dir,
        external_dir=external_dir,
    )

    assert str(external_dir / "client.key") in result.text
    assert "client-" in result.text
    assert result.text == patch_ovpn_config(
        raw,
        auth_method="cert",
        auth_file=None,
        profile_source_dir=source_dir,
        external_dir=external_dir,
    ).text
