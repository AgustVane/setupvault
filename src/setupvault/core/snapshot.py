from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DistributionInfo:
    """Information about the Linux distribution."""

    id: str
    name: str
    version: str
    version_id: str | None = None
    id_like: tuple[str, ...] = ()

    def family(self) -> str:
        """Return the distribution family identifier.

        Returns self.id if id_like is empty, otherwise the first entry in id_like.
        This is useful for cross-distro package mapping.
        """
        return self.id_like[0] if self.id_like else self.id


@dataclass(frozen=True)
class KernelInfo:
    """Kernel release and version strings."""

    release: str
    version: str


@dataclass(frozen=True)
class SystemInfo:
    """System identification and hardware/OS metadata."""

    distribution: DistributionInfo
    kernel: KernelInfo
    architecture: str
    hostname: str
    uptime_seconds: int | None = None
    os: str = "Linux"


@dataclass(frozen=True)
class DesktopEnvironment:
    """Detected desktop environment."""

    name: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class WindowManager:
    """Detected window manager."""

    name: str | None = None
    version: str | None = None


@dataclass(frozen=True)
class EnvironmentInfo:
    """Desktop environment, window manager, and display server."""

    desktop_environment: DesktopEnvironment | None = None
    window_manager: WindowManager | None = None
    display_server: str | None = None
    session_type: str | None = None


@dataclass(frozen=True)
class ShellEntry:
    """A single shell installation."""

    name: str
    version: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class ShellConfigFile:
    """Metadata for a shell configuration file."""

    path: str
    hash: str | None = None
    size: int | None = None


@dataclass(frozen=True)
class ShellInfo:
    """Shell and shell configuration."""

    current: ShellEntry
    available: tuple[ShellEntry, ...] = ()
    config_files: tuple[ShellConfigFile, ...] = ()


@dataclass(frozen=True)
class PackageEntry:
    """A single installed package."""

    name: str
    version: str | None = None
    repository: str | None = None
    size: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class FlatpakEntry:
    """A single installed Flatpak application."""

    name: str
    app_id: str
    version: str | None = None
    origin: str | None = None


@dataclass(frozen=True)
class SnapEntry:
    """A single installed Snap package."""

    name: str
    version: str | None = None
    channel: str | None = None


@dataclass(frozen=True)
class PackageCounts:
    """Aggregated package counts by source."""

    official: int = 0
    aur: int = 0
    third_party: int = 0
    flatpak: int = 0
    snap: int = 0

    @property
    def total(self) -> int:
        return self.official + self.aur + self.third_party + self.flatpak + self.snap


@dataclass(frozen=True)
class PackageCollection:
    """All installed packages organized by source."""

    counts: PackageCounts
    official: tuple[PackageEntry, ...] = ()
    aur: tuple[PackageEntry, ...] = ()
    third_party: tuple[PackageEntry, ...] = ()
    flatpak: tuple[FlatpakEntry, ...] = ()
    snap: tuple[SnapEntry, ...] = ()


@dataclass(frozen=True)
class GtkThemeInfo:
    """GTK theme, icon, cursor, and font settings."""

    theme: str | None = None
    icon_theme: str | None = None
    cursor_theme: str | None = None
    font_name: str | None = None
    color_scheme: str | None = None


@dataclass(frozen=True)
class QtThemeInfo:
    """Qt theme, icon, and font settings."""

    theme: str | None = None
    icon_theme: str | None = None
    font_name: str | None = None


@dataclass(frozen=True)
class ThemeInfo:
    """Desktop theming state covering GTK and Qt."""

    gtk: GtkThemeInfo | None = None
    qt: QtThemeInfo | None = None


@dataclass(frozen=True)
class FontEntry:
    """A single installed font."""

    family: str
    style: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class FontConfig:
    """Font rendering configuration."""

    freetype_preset: str | None = None
    hinting: str | None = None
    antialiasing: bool | None = None


@dataclass(frozen=True)
class FontInfo:
    """Font configuration including system and user fonts."""

    system_fonts: tuple[FontEntry, ...] = ()
    user_fonts: tuple[FontEntry, ...] = ()
    config: FontConfig | None = None


@dataclass(frozen=True)
class DotfileEntry:
    """Metadata for a tracked dotfile."""

    path: str
    hash: str | None = None
    size: int | None = None
    permissions: str | None = None
    backed_up: bool = False


_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_PACKAGE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9@._+\-]*$")
_PATH_SAFE_RE = re.compile(r"^[a-zA-Z0-9_./\-]+$")


@dataclass(frozen=True)
class Snapshot:
    """Root domain model for a SetupVault snapshot.

    A Snapshot is an immutable representation of a complete Linux environment
    export. It is constructed through SnapshotBuilder which enforces validation
    rules and ensures internal consistency.

    All fields beyond *snapshot_version*, *tool_version*, *created_at*,
    *system*, and *packages* are optional, providing forward compatibility.
    Consumers MUST ignore unknown keys at any nesting level.
    """

    snapshot_version: int
    tool_version: str
    created_at: str
    system: SystemInfo
    packages: PackageCollection

    profile: str | None = None
    notes: str | None = None

    environment: EnvironmentInfo | None = None
    shell: ShellInfo | None = None
    themes: ThemeInfo | None = None
    fonts: FontInfo | None = None
    dotfiles: tuple[DotfileEntry, ...] = ()

    extensions: dict[str, Any] | None = None


class SnapshotBuilder:
    """Builder for constructing validated Snapshot instances.

    Usage::

        builder = SnapshotBuilder()
        builder.with_system(system_info)
        builder.with_packages(package_collection)
        snapshot = builder.build()
    """

    def __init__(self) -> None:
        self._snapshot_version: int | None = None
        self._tool_version: str | None = None
        self._created_at: str | None = None
        self._system: SystemInfo | None = None
        self._packages: PackageCollection | None = None
        self._profile: str | None = None
        self._notes: str | None = None
        self._environment: EnvironmentInfo | None = None
        self._shell: ShellInfo | None = None
        self._themes: ThemeInfo | None = None
        self._fonts: FontInfo | None = None
        self._dotfiles: tuple[DotfileEntry, ...] = ()
        self._extensions: dict[str, Any] | None = None

    def with_snapshot_version(self, version: int) -> SnapshotBuilder:
        self._snapshot_version = version
        return self

    def with_tool_version(self, version: str) -> SnapshotBuilder:
        self._tool_version = version
        return self

    def with_created_at(self, timestamp: str) -> SnapshotBuilder:
        self._created_at = timestamp
        return self

    def with_system(self, info: SystemInfo) -> SnapshotBuilder:
        self._system = info
        return self

    def with_packages(self, packages: PackageCollection) -> SnapshotBuilder:
        self._packages = packages
        return self

    def with_profile(self, profile: str | None) -> SnapshotBuilder:
        self._profile = profile
        return self

    def with_notes(self, notes: str | None) -> SnapshotBuilder:
        self._notes = notes
        return self

    def with_environment(self, info: EnvironmentInfo | None) -> SnapshotBuilder:
        self._environment = info
        return self

    def with_shell(self, info: ShellInfo | None) -> SnapshotBuilder:
        self._shell = info
        return self

    def with_themes(self, info: ThemeInfo | None) -> SnapshotBuilder:
        self._themes = info
        return self

    def with_fonts(self, info: FontInfo | None) -> SnapshotBuilder:
        self._fonts = info
        return self

    def with_dotfiles(self, entries: list[DotfileEntry]) -> SnapshotBuilder:
        self._dotfiles = tuple(entries)
        return self

    def with_extensions(self, data: dict[str, Any] | None) -> SnapshotBuilder:
        self._extensions = data
        return self

    def build(self) -> Snapshot:
        """Validate and construct the Snapshot.

        Raises:
            InvalidSnapshotError: If any required fields are missing or invalid.
        """
        from setupvault.core.exceptions import InvalidSnapshotError

        errors: list[str] = []

        sv = self._snapshot_version
        if sv is None:
            errors.append("snapshot_version is required")
        elif not isinstance(sv, int) or sv < 1:
            errors.append(f"snapshot_version must be a positive integer, got {sv!r}")

        tv = self._tool_version
        if tv is None:
            errors.append("tool_version is required")
        elif not isinstance(tv, str) or not tv.strip():
            errors.append("tool_version must be a non-empty string")

        ca = self._created_at
        if ca is None:
            errors.append("created_at is required")
        elif not isinstance(ca, str) or not ca.strip():
            errors.append("created_at must be a non-empty string")

        if self._system is None:
            errors.append("system section is required")

        if self._packages is None:
            errors.append("packages section is required")

        if errors:
            raise InvalidSnapshotError(
                "Snapshot validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return Snapshot(
            snapshot_version=sv,
            tool_version=tv,
            created_at=ca,
            system=self._system,
            packages=self._packages,
            profile=self._profile,
            notes=self._notes,
            environment=self._environment,
            shell=self._shell,
            themes=self._themes,
            fonts=self._fonts,
            dotfiles=self._dotfiles,
            extensions=self._extensions,
        )
