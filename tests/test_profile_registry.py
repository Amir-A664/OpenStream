from pathlib import Path

from openstream.config import OpenStreamConfig
from openstream.profiles import (
    current_profile_id,
    load_registry,
    profile_id_for,
    refresh_profiles,
    remove_profile,
    set_current_profile,
    sha256_file,
)

FIXTURES = Path(__file__).parent / "fixtures"


def temp_config(tmp_path: Path) -> OpenStreamConfig:
    return OpenStreamConfig(
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


def test_refresh_imports_profile_and_writes_registry(tmp_path: Path, monkeypatch) -> None:
    cfg = temp_config(tmp_path)
    cfg.drop_dir.mkdir(parents=True)
    source = cfg.drop_dir / "basic-auth.ovpn"
    source.write_text((FIXTURES / "basic-auth.ovpn").read_text(encoding="utf-8"), encoding="utf-8")

    def fake_auth_file(cfg_arg: OpenStreamConfig, profile_id: str) -> Path:
        path = cfg_arg.auth_dir / f"{profile_id}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("user\npass\n", encoding="utf-8")
        return path

    monkeypatch.setattr("openstream.profiles.ensure_auth_file", fake_auth_file)

    profiles = refresh_profiles(cfg)

    assert len(profiles) == 1
    profile = profiles[0]
    assert profile.name == "basic-auth.ovpn"
    assert profile.auth_method == "userpass"
    assert Path(profile.original_ovpn).exists()
    assert Path(profile.patched_ovpn).exists()
    assert cfg.registry_path.exists()
    assert load_registry(cfg)[0].id == profile.id
    assert "auth-user-pass" in Path(profile.patched_ovpn).read_text(encoding="utf-8")


def test_set_current_profile_uses_symlink_and_can_resolve_current(tmp_path: Path, monkeypatch) -> None:
    cfg = temp_config(tmp_path)
    cfg.drop_dir.mkdir(parents=True)
    source = cfg.drop_dir / "cert-inline.ovpn"
    source.write_text((FIXTURES / "cert-inline.ovpn").read_text(encoding="utf-8"), encoding="utf-8")

    profiles = refresh_profiles(cfg)
    profile = profiles[0]
    set_current_profile(cfg, profile)

    assert cfg.current_ovpn.is_symlink()
    assert current_profile_id(cfg, profiles) == profile.id


def test_remove_profile_deletes_cache_but_not_original_drop_file(tmp_path: Path, monkeypatch) -> None:
    cfg = temp_config(tmp_path)
    cfg.drop_dir.mkdir(parents=True)
    source = cfg.drop_dir / "cert-inline.ovpn"
    source.write_text((FIXTURES / "cert-inline.ovpn").read_text(encoding="utf-8"), encoding="utf-8")

    profile = refresh_profiles(cfg)[0]
    set_current_profile(cfg, profile)
    remove_profile(cfg, profile)

    assert source.exists()
    assert not Path(profile.patched_ovpn).exists()
    assert not cfg.current_ovpn.exists()
    assert load_registry(cfg) == []


def test_profile_id_uses_sanitized_filename_and_digest(tmp_path: Path) -> None:
    source = tmp_path / "NL Amsterdam!.ovpn"
    source.write_text("client\nremote vpn.example.com 1194\n", encoding="utf-8")
    digest = sha256_file(source)

    pid = profile_id_for(source, digest)

    assert pid.startswith("NL-Amsterdam-")
    assert pid.endswith(digest[:8])
