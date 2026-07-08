from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from setupvault.core.config import get_config_paths
from setupvault.detectors.distro import detect_distro
from setupvault.detectors.shell import detect_current_shell
from setupvault.utils.shell import SafeCommandRunner

CheckResult = tuple[str, bool, str]


@dataclass
class DoctorCheck:
    name: str
    description: str
    run: Callable[[], CheckResult]


def python_version() -> CheckResult:
    import sys

    v = sys.version_info
    ok = v.major >= 3 and v.minor >= 10
    return (
        "python_version",
        ok,
        f"{v.major}.{v.minor}.{v.micro} (≥3.10 required)"
        if ok
        else f"{v.major}.{v.minor}.{v.micro} (need ≥3.10)",
    )


def distro_detected() -> CheckResult:
    result = detect_distro()
    ok = result.distro_id != "unknown"
    return (
        "distro_detected",
        ok,
        f"{result.distro_id}/{result.distro_name}" if ok else "Could not detect distribution",
    )


def shell_detected() -> CheckResult:
    shell = detect_current_shell()
    ok = bool(shell.name)
    return (
        "shell_detected",
        ok,
        f"{shell.name} ({shell.path})" if ok else "Could not detect shell",
    )


def config_dir_exists() -> CheckResult:
    paths = get_config_paths()
    ok = paths.config_dir.exists()
    return (
        "config_dir_exists",
        ok,
        str(paths.config_dir) if ok else f"Config dir does not exist: {paths.config_dir}",
    )


def snapshots_dir_exists() -> CheckResult:
    paths = get_config_paths()
    ok = paths.snapshots_dir.exists()
    return (
        "snapshots_dir_exists",
        ok,
        str(paths.snapshots_dir) if ok else f"Snapshots dir does not exist: {paths.snapshots_dir}",
    )


def sudo_available() -> CheckResult:
    runner = SafeCommandRunner()
    result = runner.run(["which", "sudo"])
    ok = result.returncode == 0
    return (
        "sudo_available",
        ok,
        "sudo found" if ok else "sudo not found (package restore may need it)",
    )


def pacman_available() -> CheckResult:
    runner = SafeCommandRunner()
    result = runner.run(["which", "pacman"])
    ok = result.returncode == 0
    return (
        "pacman_available",
        ok,
        "pacman found" if ok else "pacman not found (Arch Linux?)",
    )


def gsettings_available() -> CheckResult:
    runner = SafeCommandRunner()
    result = runner.run(["which", "gsettings"])
    ok = result.returncode == 0
    return (
        "gsettings_available",
        ok,
        "gsettings found" if ok else "gsettings not found (themes restore may fail)",
    )


def fc_cache_available() -> CheckResult:
    runner = SafeCommandRunner()
    result = runner.run(["which", "fc-cache"])
    ok = result.returncode == 0
    return (
        "fc_cache_available",
        ok,
        "fc-cache found" if ok else "fc-cache not found (fonts restore may fail)",
    )


_ALL_CHECKS: list[DoctorCheck] = [
    DoctorCheck("python_version", "Python version check", python_version),
    DoctorCheck("distro_detected", "Distro detection check", distro_detected),
    DoctorCheck("shell_detected", "Shell detection check", shell_detected),
    DoctorCheck("config_dir_exists", "Config directory check", config_dir_exists),
    DoctorCheck("snapshots_dir_exists", "Snapshots directory check", snapshots_dir_exists),
    DoctorCheck("sudo_available", "sudo availability check", sudo_available),
    DoctorCheck("pacman_available", "pacman availability check", pacman_available),
    DoctorCheck("gsettings_available", "gsettings availability check", gsettings_available),
    DoctorCheck("fc_cache_available", "fc-cache availability check", fc_cache_available),
]


def get_all_checks() -> list[DoctorCheck]:
    return list(_ALL_CHECKS)
