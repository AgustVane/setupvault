from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from setupvault.core.versions import is_supported

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")


def validate_semantic(data: dict[str, Any]) -> list[str]:
    """Run semantic validation rules beyond schema compliance.

    Args:
        data: Parsed snapshot dictionary.

    Returns:
        A list of semantic violation messages (empty if valid).
    """
    errors: list[str] = []

    sv = data.get("snapshot_version")
    if isinstance(sv, int) and not is_supported(sv):
        errors.append(f"snapshot_version {sv} is not supported")

    tv = data.get("tool_version")
    if isinstance(tv, str) and not _SEMVER_RE.match(tv):
        errors.append(f"tool_version '{tv}' is not valid semver")

    ca = data.get("created_at")
    if isinstance(ca, str):
        try:
            datetime.fromisoformat(ca)
        except (ValueError, TypeError):
            errors.append(f"created_at '{ca}' is not valid ISO 8601")

    system = data.get("system", {})
    dist = system.get("distribution", {})
    if isinstance(dist, dict):
        _check_present(errors, "system.distribution.id", dist.get("id"))
        _check_present(errors, "system.distribution.name", dist.get("name"))

    pkgs = data.get("packages", {})
    counts = pkgs.get("count", {})
    if isinstance(counts, dict):
        sub_counts = sum(
            counts.get(k, 0) or 0 for k in ("official", "aur", "third_party", "flatpak", "snap")
        )
        declared_total = counts.get("total")
        if isinstance(declared_total, int) and sub_counts != declared_total:
            errors.append(
                f"packages.count.total ({declared_total}) does not match sum "
                f"of sub-counts ({sub_counts})"
            )

    for section, entries_key in [
        ("official", pkgs.get("official", [])),
        ("aur", pkgs.get("aur", [])),
        ("third_party", pkgs.get("third_party", [])),
    ]:
        if isinstance(entries_key, list):
            for i, entry in enumerate(entries_key):
                if isinstance(entry, dict):
                    name = entry.get("name", "")
                    if isinstance(name, str) and not _SAFE_NAME_RE.match(name):
                        errors.append(f"packages.{section}[{i}].name '{name}' looks suspicious")

    dotfiles = data.get("dotfiles", [])
    if isinstance(dotfiles, list):
        for i, entry in enumerate(dotfiles):
            if isinstance(entry, dict):
                path = entry.get("path", "")
                if isinstance(path, str):
                    if path.startswith("/"):
                        errors.append(f"dotfiles[{i}].path '{path}' is absolute")
                    if ".." in path.split("/"):
                        errors.append(f"dotfiles[{i}].path '{path}' contains traversal")

                h = entry.get("hash")
                if h is not None and isinstance(h, str) and not _SHA256_RE.match(h):
                    errors.append(f"dotfiles[{i}].hash is not valid SHA-256")

    return errors


def _check_present(errors: list[str], field: str, value: Any) -> None:
    if not value or not isinstance(value, str):
        errors.append(f"{field} is missing or empty")


_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9@._+\-]*$")
