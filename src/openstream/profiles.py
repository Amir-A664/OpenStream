from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .auth import auth_label, auth_requires_credentials, choose_auth_method, ensure_auth_file
from .config import OpenStreamConfig
from .ovpn_patch import patch_ovpn_config
from .ui import key_value, section, success, warning


@dataclass
class Profile:
    id: str
    name: str
    source_path: str
    sha256: str
    auth_method: str
    original_ovpn: str
    patched_ovpn: str
    external_files: list[str]

    @property
    def label(self) -> str:
        return auth_label(self.auth_method)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            source_path=str(data["source_path"]),
            sha256=str(data["sha256"]),
            auth_method=str(data["auth_method"]),
            original_ovpn=str(data["original_ovpn"]),
            patched_ovpn=str(data["patched_ovpn"]),
            external_files=list(data.get("external_files", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "sha256": self.sha256,
            "auth_method": self.auth_method,
            "auth_label": self.label,
            "original_ovpn": self.original_ovpn,
            "patched_ovpn": self.patched_ovpn,
            "external_files": self.external_files,
        }


def sanitize_name(name: str) -> str:
    stem = Path(name).stem
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-_")
    return safe or "profile"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def profile_id_for(path: Path, digest: str) -> str:
    return f"{sanitize_name(path.name)}-{digest[:8]}"


def load_registry(cfg: OpenStreamConfig) -> list[Profile]:
    try:
        raw = json.loads(cfg.registry_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Profile registry is corrupted: {cfg.registry_path}") from exc
    return [Profile.from_dict(item) for item in raw.get("profiles", [])]


def save_registry(cfg: OpenStreamConfig, profiles: list[Profile]) -> None:
    cfg.registry_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"profiles": [profile.to_dict() for profile in profiles]}
    cfg.registry_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cfg.registry_path.chmod(0o644)


def current_profile_id(cfg: OpenStreamConfig, profiles: list[Profile] | None = None) -> str | None:
    if not cfg.current_ovpn.exists() and not cfg.current_ovpn.is_symlink():
        return None
    try:
        target = cfg.current_ovpn.resolve(strict=True)
    except FileNotFoundError:
        return None
    for profile in profiles or load_registry(cfg):
        if Path(profile.patched_ovpn).resolve() == target:
            return profile.id
    return None


def discover_drop_files(cfg: OpenStreamConfig) -> list[Path]:
    if not cfg.drop_dir.exists():
        return []
    return sorted(path for path in cfg.drop_dir.glob("*.ovpn") if path.is_file())


def _write_metadata(profile_dir: Path, profile: Profile) -> None:
    metadata = profile.to_dict()
    (profile_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def import_profile(cfg: OpenStreamConfig, source: Path, existing: dict[str, Profile]) -> Profile:
    digest = sha256_file(source)
    pid = profile_id_for(source, digest)
    if pid in existing:
        return existing[pid]

    raw = source.read_text(encoding="utf-8", errors="surrogateescape")
    method = choose_auth_method(raw, source.name)
    profile_dir = cfg.profiles_dir / pid
    external_dir = profile_dir / "external-files"
    profile_dir.mkdir(parents=True, exist_ok=True)
    original = profile_dir / "original.ovpn"
    patched = profile_dir / "patched.ovpn"
    shutil.copy2(source, original)
    os.chmod(original, 0o600)

    auth_file = ensure_auth_file(cfg, pid) if auth_requires_credentials(method) else None
    patch = patch_ovpn_config(
        raw,
        auth_method=method,
        auth_file=auth_file,
        profile_source_dir=source.parent,
        external_dir=external_dir,
        tun_dev=cfg.tun_dev,
    )
    patched.write_text(patch.text, encoding="utf-8")
    os.chmod(patched, 0o600)

    profile = Profile(
        id=pid,
        name=source.name,
        source_path=str(source),
        sha256=digest,
        auth_method=method,
        original_ovpn=str(original),
        patched_ovpn=str(patched),
        external_files=patch.external_files,
    )
    _write_metadata(profile_dir, profile)
    return profile


def refresh_profiles(cfg: OpenStreamConfig) -> list[Profile]:
    existing_profiles = load_registry(cfg)
    existing_by_id = {profile.id: profile for profile in existing_profiles}
    profiles = list(existing_profiles)
    changed = False

    for source in discover_drop_files(cfg):
        digest = sha256_file(source)
        pid = profile_id_for(source, digest)
        if pid in existing_by_id:
            continue
        profile = import_profile(cfg, source, existing_by_id)
        profiles.append(profile)
        existing_by_id[profile.id] = profile
        changed = True

    if changed or not cfg.registry_path.exists():
        save_registry(cfg, profiles)
    return profiles


def print_profiles(cfg: OpenStreamConfig, profiles: list[Profile] | None = None) -> None:
    profiles = profiles or load_registry(cfg)
    current = current_profile_id(cfg, profiles)
    if not profiles:
        warning("No OpenStream profiles are registered yet.")
        print("Put your .ovpn config files here:")
        print(f"  {cfg.drop_dir}")
        print("Then run:")
        print("  opst add")
        return
    print("Cached profiles:")
    for i, profile in enumerate(profiles, 1):
        marker = "current" if profile.id == current else "available"
        print(f"  [{i}] {profile.name}")
        key_value("auth", profile.label)
        key_value("state", marker)


def select_profile_interactive(cfg: OpenStreamConfig, profiles: list[Profile]) -> Profile:
    if not profiles:
        raise RuntimeError(
            "No .ovpn files were found.\n"
            f"Put your OpenVPN config files here:\n{cfg.drop_dir}\n\nThen run again:\nopst on"
        )
    if len(profiles) == 1:
        profile = profiles[0]
        success(f"Using the only available profile: {profile.name} ({profile.label})")
        return profile

    section("Select profile")
    for i, profile in enumerate(profiles, 1):
        print(f"  [{i}] {profile.name:<28} auth: {profile.label}")
    print(f"  [{len(profiles) + 1}] Add new .ovpn file")
    selection = input("Select profile: ").strip()
    if not selection.isdigit():
        raise RuntimeError("Invalid profile selection.")
    index = int(selection)
    if index == len(profiles) + 1:
        raise RuntimeError(
            f"Put your OpenVPN config files here:\n{cfg.drop_dir}\n\nThen run again:\nopst on"
        )
    if index < 1 or index > len(profiles):
        raise RuntimeError("Invalid profile selection.")
    return profiles[index - 1]


def set_current_profile(cfg: OpenStreamConfig, profile: Profile) -> None:
    cfg.current_ovpn.parent.mkdir(parents=True, exist_ok=True)
    if cfg.current_ovpn.exists() or cfg.current_ovpn.is_symlink():
        cfg.current_ovpn.unlink()
    os.symlink(profile.patched_ovpn, cfg.current_ovpn)


def remove_profile(cfg: OpenStreamConfig, profile: Profile) -> None:
    profiles = [item for item in load_registry(cfg) if item.id != profile.id]
    current = current_profile_id(cfg, [profile])
    if current == profile.id and (cfg.current_ovpn.exists() or cfg.current_ovpn.is_symlink()):
        cfg.current_ovpn.unlink()
    auth_file = cfg.auth_dir / f"{profile.id}.txt"
    if auth_file.exists():
        auth_file.unlink()
    profile_dir = cfg.profiles_dir / profile.id
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    save_registry(cfg, profiles)


def choose_cached_profile(cfg: OpenStreamConfig) -> Profile:
    profiles = load_registry(cfg)
    return select_profile_interactive(cfg, profiles)
