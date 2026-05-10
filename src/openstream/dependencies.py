from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from .ui import progress, section, step, success, warning


@dataclass(frozen=True)
class Dependency:
    command: str
    package: str
    required: bool = True


REQUIRED_DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("openvpn", "openvpn"),
    Dependency("ip", "iproute2"),
    Dependency("iptables", "iptables"),
    Dependency("socat", "socat"),
    Dependency("microsocks", "microsocks"),
    Dependency("curl", "curl"),
    Dependency("systemctl", "systemd"),
)

OPTIONAL_DEPENDENCIES: tuple[Dependency, ...] = (
    Dependency("ss", "iproute2", required=False),
    Dependency("awk", "mawk", required=False),
    Dependency("sed", "sed", required=False),
    Dependency("grep", "grep", required=False),
)


def is_installed(command: str) -> bool:
    return shutil.which(command) is not None


def missing_required() -> list[Dependency]:
    return [dep for dep in REQUIRED_DEPENDENCIES if not is_installed(dep.command)]


def package_list(deps: list[Dependency]) -> list[str]:
    seen: set[str] = set()
    packages: list[str] = []
    for dep in deps:
        if dep.package not in seen:
            packages.append(dep.package)
            seen.add(dep.package)
    return packages


def print_dependency_summary() -> list[Dependency]:
    section("Checking runtime dependencies")
    missing = missing_required()
    installed = len(REQUIRED_DEPENDENCIES) - len(missing)
    progress("Required commands found", installed, len(REQUIRED_DEPENDENCIES))
    print(f"  Required dependencies: {len(REQUIRED_DEPENDENCIES)}")
    print(f"  Installed: {installed}/{len(REQUIRED_DEPENDENCIES)}")
    if missing:
        warning("Some required dependencies are missing:")
        for dep in missing:
            print(f"    - {dep.command:<10} package: {dep.package}")
    else:
        success("All required dependencies are already installed.")
    return missing


def apt_install_missing(deps: list[Dependency]) -> None:
    packages = package_list(deps)
    if not packages:
        return
    if shutil.which("apt") is None:
        raise RuntimeError("apt was not found. Install missing packages manually.")
    section("Installing missing packages with apt")
    step("Updating package metadata...")
    subprocess.run(["apt", "update"], check=True)
    step("Installing: " + " ".join(packages))
    subprocess.run(["apt", "install", "-y", *packages], check=True)
    success("Missing packages installed successfully.")


def ensure_dependencies_interactive(auto_install: bool = False, assume_no: bool = False) -> None:
    missing = print_dependency_summary()
    if not missing:
        return

    packages = package_list(missing)
    manual = "sudo apt install " + " ".join(packages)

    if assume_no:
        raise RuntimeError(
            "Missing required dependencies. Install them manually, then rerun:\n\n" + manual
        )

    if auto_install:
        apt_install_missing(missing)
        return

    print()
    print("Choose what to do:")
    print("  [1] Install missing dependencies now using apt")
    print("  [2] Abort installation so you can install them manually")
    selection = input("Selection: ").strip()
    if selection == "1":
        apt_install_missing(missing)
        return
    if selection == "2":
        raise RuntimeError(
            "Installation aborted.\nInstall missing dependencies manually, then rerun:\n\n" + manual
        )
    raise RuntimeError("Invalid dependency selection. Installation aborted.")
