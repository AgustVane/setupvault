from __future__ import annotations

import glob as glob_module
import os
from dataclasses import dataclass
from pathlib import Path

from setupvault.utils.hashing import hash_file
from setupvault.utils.shell import SafeCommandRunner


@dataclass(frozen=True)
class ShellEntry:
    """A single shell installation."""

    name: str
    version: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class ShellConfigFile:
    """Metadata for a tracked shell configuration file."""

    path: str
    hash: str | None = None
    size: int | None = None


@dataclass(frozen=True)
class ShellDetection:
    """Result of shell detection."""

    current: ShellEntry
    available: tuple[ShellEntry, ...] = ()
    config_files: tuple[ShellConfigFile, ...] = ()


_RUNNER = SafeCommandRunner(timeout=5.0)


def detect_current_shell() -> ShellEntry:
    """Detect the current user's shell.

    Uses ``$SHELL`` environment variable, resolving symlinks.
    Falls back to ``/bin/sh``.
    """
    shell_path = os.environ.get("SHELL", "/bin/sh")
    try:
        real_path = os.path.realpath(shell_path)
    except OSError:
        real_path = shell_path

    name = Path(real_path).name
    version = _get_shell_version(name, real_path)
    return ShellEntry(name=name, version=version, path=real_path)


def detect_available_shells() -> tuple[ShellEntry, ...]:
    """Read ``/etc/shells`` and return all available shells.

    Returns an empty tuple if the file cannot be read.
    """
    entries: list[ShellEntry] = []
    try:
        with open("/etc/shells") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                path = line
                name = Path(path).name
                version = _get_shell_version(name, path)
                entries.append(ShellEntry(name=name, version=version, path=path))
    except (FileNotFoundError, OSError):
        pass
    return tuple(entries)


def detect_shell_config_files(current_shell_name: str) -> tuple[ShellConfigFile, ...]:
    """Find shell configuration files for the current shell.

    Uses well-known paths for bash, zsh, and fish.
    """
    home = Path.home()
    config_patterns: list[str] = []

    shell_lower = current_shell_name.lower()

    if "bash" in shell_lower:
        config_patterns = [".bashrc", ".bash_profile", ".bash_logout"]
    elif "zsh" in shell_lower:
        config_patterns = [
            ".zshrc",
            ".zprofile",
            ".zshenv",
            ".zlogin",
            ".zlogout",
        ]
    elif "fish" in shell_lower:
        config_patterns = [
            ".config/fish/config.fish",
            ".config/fish/functions/*.fish",
        ]

    files: list[ShellConfigFile] = []
    for pattern in config_patterns:
        full_pattern = str(home / pattern)
        for matched_path in glob_module.glob(full_pattern):
            p = Path(matched_path)
            if not p.is_file():
                continue
            rel_path = str(p.relative_to(home))
            try:
                file_hash = hash_file(p)
                size = p.stat().st_size
            except (OSError, FileNotFoundError):
                file_hash = None
                size = None
            files.append(ShellConfigFile(path=rel_path, hash=file_hash, size=size))

    return tuple(files)


def _get_shell_version(name: str, path: str) -> str | None:
    """Try to get the version string for a shell by running ``<shell> --version``."""
    _ = path  # reserved for future use (e.g., running the exact binary)
    version_flags: dict[str, list[str]] = {
        "bash": ["bash", "--version"],
        "zsh": ["zsh", "--version"],
        "fish": ["fish", "--version"],
        "sh": ["sh", "--version"],
        "dash": ["dash", "--version"],
        "mksh": ["mksh", "--version"],
        "tcsh": ["tcsh", "--version"],
    }
    flags = version_flags.get(name)
    if not flags:
        flags = [name, "--version"]

    try:
        result = _RUNNER.run(flags, check=False, timeout=3.0)
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0] if result.stdout else ""
            return first_line.strip() if first_line else None
    except Exception:
        pass
    return None
