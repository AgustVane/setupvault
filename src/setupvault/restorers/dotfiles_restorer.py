from __future__ import annotations

import base64
import os
import re as _re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from setupvault.core.snapshot import DotfileEntry


@dataclass(frozen=True)
class DotfilePlanAction:
    """A single dotfile restoration action."""

    path: str
    action: str  # "copy" | "skip_unchanged" | "skip_conflict" | "rejected"
    dest_exists: bool = False
    hash_match: bool = False
    detail: str = ""
    content: str | None = None


@dataclass(frozen=True)
class DotfilesPlan:
    """Restoration plan for the dotfiles section."""

    actions: tuple[DotfilePlanAction, ...] = ()
    rejected: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


_ROLLBACK_BASE = Path.home() / ".local" / "share" / "setupvault" / "rollbacks"


def plan_dotfiles(
    snapshot_dotfiles: tuple[DotfileEntry, ...],
) -> DotfilesPlan:
    """Build a plan to restore dotfiles from snapshot metadata.

    Validates path safety and checks current state on disk.

    Args:
        snapshot_dotfiles: Dotfile entries from the snapshot.

    Returns:
        A ``DotfilesPlan`` describing actions for each dotfile.
    """
    actions: list[DotfilePlanAction] = []
    rejected: list[str] = []
    warnings: list[str] = []

    for entry in snapshot_dotfiles:
        if not _is_safe_path(entry.path):
            rejected.append(entry.path)
            continue

        home_path = Path.home() / entry.path
        dest_exists = home_path.exists()

        if dest_exists:
            from setupvault.utils.hashing import hash_file

            current_hash = hash_file(str(home_path)) if home_path.is_file() else None
            hash_match = (
                current_hash is not None and entry.hash is not None and current_hash == entry.hash
            )
            if hash_match:
                actions.append(
                    DotfilePlanAction(
                        path=entry.path,
                        action="skip_unchanged",
                        dest_exists=True,
                        hash_match=True,
                        detail="Content unchanged — skipping",
                        content=entry.content,
                    )
                )
                continue
            actions.append(
                DotfilePlanAction(
                    path=entry.path,
                    action="copy",
                    dest_exists=True,
                    hash_match=False,
                    detail="Will back up existing then overwrite",
                    content=entry.content,
                )
            )
        else:
            actions.append(
                DotfilePlanAction(
                    path=entry.path,
                    action="copy",
                    dest_exists=False,
                    detail="New file — will create",
                    content=entry.content,
                )
            )

    return DotfilesPlan(
        actions=tuple(actions),
        rejected=tuple(rejected),
        warnings=tuple(warnings),
    )


def apply_dotfiles(plan: DotfilesPlan, *, rollback: bool = True) -> list[str]:
    """Execute the dotfile restoration plan.

    For each ``copy`` action:
      1. Backs up the existing file (if any) to the rollback directory.
      2. Copies the source (if available) or creates a placeholder.

    Args:
        plan: The ``DotfilesPlan`` returned by ``plan_dotfiles``.
        rollback: If ``True``, create backups before overwriting.

    Returns:
        A list of error messages (empty on full success).
    """
    errors: list[str] = []

    rollback_dir = _create_rollback_dir() if rollback else None

    for action in plan.actions:
        if action.action != "copy":
            continue

        home_path = Path.home() / action.path

        if action.dest_exists and rollback_dir is not None:
            try:
                backup_target = rollback_dir / action.path
                backup_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(home_path), str(backup_target))
            except OSError as exc:
                errors.append(f"Rollback backup failed for {action.path}: {exc}")

        try:
            home_path.parent.mkdir(parents=True, exist_ok=True)
            if os.path.islink(str(home_path)):
                os.unlink(str(home_path))
            if action.content:
                raw = base64.b64decode(action.content)
                home_path.write_bytes(raw)
            else:
                home_path.touch(exist_ok=True)
        except OSError as exc:
            errors.append(f"Failed to create {action.path}: {exc}")
        except ValueError as exc:
            errors.append(f"Failed to decode content for {action.path}: {exc}")

    if rollback_dir is not None and plan.actions:
        for action in plan.actions:
            if action.action == "copy":
                pass

    return errors


def _is_safe_path(path: str) -> bool:
    """Reject paths with traversal or absolute paths."""
    if path.startswith("/"):
        return False
    if ".." in path.split("/"):
        return False
    return bool(_PATH_SAFE_RE.match(path))


def _create_rollback_dir() -> Path:
    """Create a timestamped rollback directory."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _ROLLBACK_BASE / ts
    path.mkdir(parents=True, exist_ok=True)
    return path


_PATH_SAFE_RE = _re.compile(r"^[a-zA-Z0-9_./\-]+$")
