from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from setupvault.storage.local import read_snapshot, snapshot_to_dict


@dataclass
class DiffResult:
    same: bool
    sections_changed: list[str] = field(default_factory=list)
    details: dict[str, list[str]] = field(default_factory=dict)


def diff_snapshots(left: Path, right: Path) -> DiffResult:
    """Compare two snapshot files.

    Args:
        left: Path to the first snapshot.
        right: Path to the second snapshot.

    Returns:
        A DiffResult describing what changed.
    """
    left_snap = read_snapshot(left)
    right_snap = read_snapshot(right)

    left_data = snapshot_to_dict(left_snap)
    right_data = snapshot_to_dict(right_snap)

    result = DiffResult(same=True)
    _diff_section(result, "system", left_data.get("system"), right_data.get("system"))
    _diff_section(result, "shell", left_data.get("shell"), right_data.get("shell"))
    _diff_packages(result, left_data, right_data)
    _diff_section(result, "themes", left_data.get("themes"), right_data.get("themes"))
    _diff_section(result, "fonts", left_data.get("fonts"), right_data.get("fonts"))
    _diff_dotfiles(result, left_data, right_data)

    result.same = len(result.sections_changed) == 0
    return result


def _diff_section(
    result: DiffResult,
    name: str,
    left: Any,
    right: Any,
) -> None:
    if left is None and right is None:
        return
    if left == right:
        return
    result.sections_changed.append(name)
    details: list[str] = []

    if left is None:
        details.append(f"{name}: added (was None)")
    elif right is None:
        details.append(f"{name}: removed (now None)")
    else:
        if isinstance(left, dict) and isinstance(right, dict):
            added = set(right.keys()) - set(left.keys())
            removed = set(left.keys()) - set(right.keys())
            if added:
                details.append(f"{name}: added keys {sorted(added)}")
            if removed:
                details.append(f"{name}: removed keys {sorted(removed)}")
            common = set(left.keys()) & set(right.keys())
            for k in sorted(common):
                if left[k] != right[k]:
                    details.append(f"{name}.{k}: changed")
        else:
            details.append(f"{name}: changed ({type(left).__name__} → {type(right).__name__})")

    if details:
        result.details[name] = details


def _diff_packages(
    result: DiffResult, left_data: dict[str, Any], right_data: dict[str, Any]
) -> None:
    lp = left_data.get("packages", {})
    rp = right_data.get("packages", {})

    lc = lp.get("count", {})
    rc = rp.get("count", {})
    count_changes: list[str] = []

    for attr in ("official", "aur", "third_party", "flatpak", "snap", "total"):
        lv = lc.get(attr)
        rv = rc.get(attr)
        if lv != rv:
            count_changes.append(f"count.{attr}: {lv} → {rv}")

    left_names = (
        _package_names(lp, "official")
        | _package_names(lp, "aur")
        | _package_names(lp, "third_party")
    )
    right_names = (
        _package_names(rp, "official")
        | _package_names(rp, "aur")
        | _package_names(rp, "third_party")
    )

    added_pkgs = right_names - left_names
    removed_pkgs = left_names - right_names

    all_details: list[str] = count_changes
    if added_pkgs:
        all_details.append(f"packages added: {len(added_pkgs)}")
    if removed_pkgs:
        all_details.append(f"packages removed: {len(removed_pkgs)}")

    if all_details:
        result.sections_changed.append("packages")
        result.details["packages"] = all_details


def _package_names(pkg_dict: dict[str, Any], section: str) -> set[str]:
    entries = pkg_dict.get(section, [])
    if not isinstance(entries, list):
        return set()
    return {e.get("name", "") for e in entries if isinstance(e, dict)}


def _diff_dotfiles(
    result: DiffResult, left_data: dict[str, Any], right_data: dict[str, Any]
) -> None:
    left_dots = left_data.get("dotfiles", [])
    right_dots = right_data.get("dotfiles", [])
    if not isinstance(left_dots, list):
        left_dots = []
    if not isinstance(right_dots, list):
        right_dots = []

    left_paths = {d.get("path") for d in left_dots if isinstance(d, dict)}
    right_paths = {d.get("path") for d in right_dots if isinstance(d, dict)}

    added = right_paths - left_paths
    removed = left_paths - right_paths

    if added or removed:
        result.sections_changed.append("dotfiles")
        details: list[str] = []
        if added:
            details.append(f"dotfiles added: {len(added)}")
        if removed:
            details.append(f"dotfiles removed: {len(removed)}")
        result.details["dotfiles"] = details
