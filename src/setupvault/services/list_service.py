from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from setupvault.core.config import get_config_paths


@dataclass
class SnapshotEntry:
    path: Path
    filename: str
    name: str
    size_bytes: int
    modified: datetime


@dataclass
class ListResult:
    snapshots: list[SnapshotEntry] = field(default_factory=list)
    snapshot_dir: Path | None = None
    error: str | None = None


def list_snapshots(custom_dir: Path | None = None) -> ListResult:
    """List available snapshots in the snapshots directory.

    Args:
        custom_dir: Optional custom search directory.

    Returns:
        A ListResult with snapshot entries.
    """
    paths = get_config_paths()
    snap_dir = custom_dir or paths.snapshots_dir

    if not snap_dir.exists():
        return ListResult(
            snapshot_dir=snap_dir,
            error=f"Snapshots directory does not exist: {snap_dir}",
        )

    entries: list[SnapshotEntry] = []
    for fpath in sorted(snap_dir.iterdir()):
        if fpath.is_file() and fpath.suffix in (".json", ".json.gz", ".snapshot"):
            try:
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
            except OSError:
                mtime = datetime.now()
            entries.append(
                SnapshotEntry(
                    path=fpath,
                    filename=fpath.name,
                    name=fpath.stem,
                    size_bytes=fpath.stat().st_size,
                    modified=mtime,
                )
            )

    return ListResult(snapshots=entries, snapshot_dir=snap_dir)
