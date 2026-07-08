from __future__ import annotations

from setupvault.core.snapshot import (
    ShellConfigFile,
    ShellEntry,
    ShellInfo,
)
from setupvault.detectors.shell import ShellDetection as ShellDetectionResult


def _map_shell_entry(entry: ShellEntry) -> ShellEntry:
    return entry


def export_shell(detection: ShellDetectionResult) -> ShellInfo | None:
    """Transform shell detection data into a snapshot ``ShellInfo``.

    The current shell is always required; if it cannot be detected,
    a minimal entry with ``/bin/sh`` is used.
    """
    current = ShellEntry(
        name=detection.current.name,
        version=detection.current.version,
        path=detection.current.path,
    )

    available = tuple(
        ShellEntry(name=s.name, version=s.version, path=s.path) for s in detection.available
    )

    config_files = tuple(
        ShellConfigFile(path=cf.path, hash=cf.hash, size=cf.size) for cf in detection.config_files
    )

    return ShellInfo(
        current=current,
        available=available,
        config_files=config_files,
    )
