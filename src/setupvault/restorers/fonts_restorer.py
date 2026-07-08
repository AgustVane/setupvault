from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from setupvault.core.snapshot import FontInfo


@dataclass(frozen=True)
class FontCopyAction:
    """A single font file to copy from source to destination."""

    source: str
    dest: str


@dataclass(frozen=True)
class FontsPlan:
    """Restoration plan for the fonts section."""

    copies: tuple[FontCopyAction, ...] = ()
    warnings: tuple[str, ...] = ()


def plan_fonts(snapshot_fonts: FontInfo | None) -> FontsPlan:
    """Build a plan to restore user fonts from snapshot data.

    In v1, font restoration only handles ``user_fonts`` (files under
    ``~/.local/share/fonts``). System fonts are assumed to come via
    packages and are skipped.

    Args:
        snapshot_fonts: The ``FontInfo`` from the snapshot (may be ``None``).

    Returns:
        A ``FontsPlan`` describing fonts to copy.
    """
    if snapshot_fonts is None:
        return FontsPlan()

    copies: list[FontCopyAction] = []
    warnings: list[str] = []

    if snapshot_fonts.system_fonts:
        warnings.append(
            "System font restore not supported in v1 — "
            f"{len(snapshot_fonts.system_fonts)} fonts skipped"
        )

    if snapshot_fonts.config:
        warnings.append("Font config restore not supported in v1")

    for uf in snapshot_fonts.user_fonts:
        if not uf.path:
            continue
        user_font_dir = Path.home() / ".local" / "share" / "fonts"
        dest = user_font_dir / Path(uf.path).name
        copies.append(FontCopyAction(source=uf.path, dest=str(dest)))

    return FontsPlan(
        copies=tuple(copies),
        warnings=tuple(warnings),
    )


def apply_fonts(plan: FontsPlan) -> list[str]:
    """Execute the font restoration plan.

    Copies font files to ``~/.local/share/fonts/`` and runs ``fc-cache``.

    Args:
        plan: The ``FontsPlan`` returned by ``plan_fonts``.

    Returns:
        A list of error messages (empty on full success).
    """
    import subprocess

    errors: list[str] = []
    for copy_action in plan.copies:
        src = Path(copy_action.source)
        dst = Path(copy_action.dest)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
        except FileNotFoundError:
            errors.append(f"Font source not found: {copy_action.source}")
        except OSError as exc:
            errors.append(f"Failed to copy {copy_action.source}: {exc}")

    if plan.copies and not errors:
        try:
            subprocess.run(
                ["fc-cache", "-f"],
                capture_output=True,
                timeout=30.0,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"fc-cache failed: {exc}")

    return errors
