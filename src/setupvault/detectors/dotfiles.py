from __future__ import annotations

import glob as glob_module
from dataclasses import dataclass
from pathlib import Path

from setupvault.utils.hashing import hash_file


@dataclass(frozen=True)
class DotfileEntry:
    """Metadata for a discovered dotfile."""

    path: str
    hash: str | None = None
    size: int | None = None
    permissions: str | None = None


def detect_dotfiles(globs: list[str]) -> tuple[DotfileEntry, ...]:
    """Discover dotfiles matching the given glob patterns.

    Each pattern is relative to the user's home directory.
    Only regular files are included. Symlinks are not followed.

    Args:
        globs: List of Unix glob patterns relative to ``$HOME``.

    Returns:
        A tuple of ``DotfileEntry`` with metadata.
    """
    home = Path.home()
    entries: list[DotfileEntry] = []

    for pattern in globs:
        full_pattern = str(home / pattern)
        for matched_path in glob_module.glob(full_pattern, recursive=True):
            p = Path(matched_path)
            if not p.is_file() or p.is_symlink():
                continue
            try:
                rel_path = str(p.relative_to(home))
                file_hash = hash_file(p)
                stat = p.stat()
                size = stat.st_size
                permissions = oct(stat.st_mode & 0o777)[2:]
                entries.append(
                    DotfileEntry(
                        path=rel_path,
                        hash=file_hash,
                        size=size,
                        permissions=permissions,
                    )
                )
            except (OSError, ValueError):
                continue

    return tuple(entries)
