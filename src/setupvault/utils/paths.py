from __future__ import annotations

import os
from pathlib import Path


def expand_path(path: str) -> Path:
    """Expand ``~`` and environment variables in *path* and return a Path."""
    return Path(os.path.expandvars(os.path.expanduser(path)))


def xdg_data_home() -> Path:
    """Return the XDG data home directory (default: ``~/.local/share``)."""
    raw = os.environ.get("XDG_DATA_HOME", "~/.local/share")
    return expand_path(raw)


def xdg_config_home() -> Path:
    """Return the XDG config home directory (default: ``~/.config``)."""
    raw = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    return expand_path(raw)


def setupvault_data_dir() -> Path:
    """Return the SetupVault data directory."""
    return xdg_data_home() / "setupvault"


def setupvault_config_dir() -> Path:
    """Return the SetupVault config directory."""
    return xdg_config_home() / "setupvault"


def setupvault_log_dir() -> Path:
    """Return the SetupVault log directory."""
    return setupvault_data_dir() / "logs"


def setupvault_rollback_dir() -> Path:
    """Return the SetupVault rollback directory."""
    return setupvault_data_dir() / "rollbacks"


def is_safe_relative_path(path: str) -> bool:
    """Check that *path* is a safe relative path (no traversal, no absolute).

    Returns:
        True if the path is relative, does not contain ``..``, and does
        not start with ``/``.
    """
    if not path:
        return False
    if path.startswith("/"):
        return False
    if ".." in path.split("/"):
        return False
    return True


def sanitize_path_component(name: str) -> str:
    """Sanitize a string for use as a single path component.

    Replaces characters that are unsafe in file names.
    """
    safe = []
    for ch in name:
        if ch.isalnum() or ch in ("-", "_", "."):
            safe.append(ch)
        else:
            safe.append("_")
    return "".join(safe).strip("_") or "unnamed"
