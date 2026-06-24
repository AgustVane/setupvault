from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from setupvault.core.exceptions import SnapshotVersionError

CURRENT_SNAPSHOT_VERSION: Final[int] = 1
"""Current snapshot format version. Incremented when breaking changes are made."""

MINIMUM_SNAPSHOT_VERSION: Final[int] = 1
"""Oldest snapshot version still supported."""


@dataclass(frozen=True)
class VersionInfo:
    """Represents a snapshot format version."""

    major: int

    def __post_init__(self) -> None:
        if self.major < 1:
            raise ValueError(f"Version must be >= 1, got {self.major}")

    def __str__(self) -> str:
        return str(self.major)


def supported_versions() -> list[VersionInfo]:
    """Return all currently supported snapshot format versions."""
    return [VersionInfo(major=v) for v in range(MINIMUM_SNAPSHOT_VERSION, CURRENT_SNAPSHOT_VERSION + 1)]


def is_supported(version: int) -> bool:
    """Check whether a given snapshot version is supported."""
    return MINIMUM_SNAPSHOT_VERSION <= version <= CURRENT_SNAPSHOT_VERSION


def validate_version(version: int) -> None:
    """Validate that *version* is supported; raise SnapshotVersionError if not."""
    if not is_supported(version):
        raise SnapshotVersionError(
            f"Snapshot version {version} is not supported. "
            f"Supported range: v{MINIMUM_SNAPSHOT_VERSION} – v{CURRENT_SNAPSHOT_VERSION}."
        )


def schema_resource_path(version: int) -> str:
    """Return the resource path to the JSON Schema file for *version*.

    The schema file is expected at: setupvault/validation/schemas/snapshot-v{version}.json
    """
    return f"setupvault/validation/schemas/snapshot-v{version}.json"
