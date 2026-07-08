from __future__ import annotations

import base64
from pathlib import Path

from setupvault.core.snapshot import DotfileEntry
from setupvault.detectors.dotfiles import DotfileEntry as DetectedDotfile


def export_dotfiles(detected: tuple[DetectedDotfile, ...]) -> tuple[DotfileEntry, ...]:
    """Transform detected dotfiles into snapshot ``DotfileEntry`` objects.

    Reads file content and stores it as base64 so snapshots are fully
    self-contained. Deduplicates by path.
    """
    seen: set[str] = set()
    entries: list[DotfileEntry] = []

    for d in detected:
        if d.path in seen:
            continue
        seen.add(d.path)

        content: str | None = None
        try:
            fpath = Path(d.path).expanduser()
            if fpath.is_file():
                raw = fpath.read_bytes()
                content = base64.b64encode(raw).decode("ascii")
        except (OSError, ValueError):
            pass

        entries.append(
            DotfileEntry(
                path=d.path,
                hash=d.hash,
                size=d.size,
                permissions=d.permissions,
                content=content,
            )
        )

    return tuple(entries)
