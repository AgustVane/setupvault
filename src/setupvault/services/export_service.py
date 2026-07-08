from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from setupvault import __version__
from setupvault.core.config import SetupVaultConfig
from setupvault.core.exceptions import ExportError
from setupvault.core.profile import BUILTIN_PROFILES, Profile, load_profile
from setupvault.core.snapshot import Snapshot, SnapshotBuilder
from setupvault.core.versions import CURRENT_SNAPSHOT_VERSION
from setupvault.detectors.distro import detect_distro
from setupvault.detectors.dotfiles import detect_dotfiles
from setupvault.detectors.environment import detect_environment
from setupvault.detectors.fonts import detect_fonts
from setupvault.detectors.packages import (
    PackageDetection,
    detect_aur_packages,
    detect_flatpak_packages,
    detect_official_packages,
    detect_snap_packages,
    detect_third_party_packages,
)
from setupvault.detectors.shell import (
    ShellDetection,
    detect_available_shells,
    detect_current_shell,
    detect_shell_config_files,
)
from setupvault.detectors.system import detect_system
from setupvault.detectors.themes import detect_themes
from setupvault.distro_adapters.base import DistroAdapter
from setupvault.exporters.dotfiles_exporter import export_dotfiles
from setupvault.exporters.environment_exporter import export_environment
from setupvault.exporters.fonts_exporter import export_fonts
from setupvault.exporters.packages_exporter import export_packages
from setupvault.exporters.shell_exporter import export_shell
from setupvault.exporters.system_exporter import export_system
from setupvault.exporters.themes_exporter import export_themes
from setupvault.storage.local import write_snapshot


@dataclass(frozen=True)
class ExportReport:
    """Result of an export operation, suitable for CLI output."""

    path: Path
    snapshot: Snapshot
    duration_seconds: float


class ExportService:
    """Orchestrates the full export pipeline.

    Usage::

        service = ExportService()
        report = service.execute(profile_name="full", output_path="snapshot.json")
    """

    def __init__(self, config: SetupVaultConfig | None = None) -> None:
        self._config = config or SetupVaultConfig()

    def execute(
        self,
        profile_name: str | None = None,
        output_path: str | Path | None = None,
        *,
        compress: bool = False,
        exclude_sections: list[str] | None = None,
    ) -> ExportReport:
        start = time.monotonic()

        profile = self._resolve_profile(profile_name)
        exclude = set(exclude_sections or [])
        sections = profile.sections() - exclude

        try:
            distro_detection = detect_distro()
        except Exception as exc:
            raise ExportError(f"Distribution detection failed: {exc}") from exc

        adapter: DistroAdapter = distro_detection.adapter

        system_detection = detect_system() if "system" in sections else None
        env_detection = detect_environment() if "environment" in sections else None
        shell_detection = self._detect_shell() if "shell" in sections else None
        theme_detection = detect_themes() if "themes" in sections else None
        font_detection = detect_fonts() if "fonts" in sections else None

        packages_detection = self._detect_packages(adapter) if "packages" in sections else None

        dotfile_entries = (
            detect_dotfiles(self._config.dotfile_globs) if "dotfiles" in sections else ()
        )

        builder = SnapshotBuilder()
        builder.with_snapshot_version(CURRENT_SNAPSHOT_VERSION)
        builder.with_tool_version(__version__)
        builder.with_created_at(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        builder.with_profile(profile.name)

        if system_detection is not None:
            distro_info = distro_detection.adapter.get_distro_info()
            builder.with_system(
                export_system(
                    detection=system_detection,
                    distro_id=distro_info.id,
                    distro_name=distro_info.name,
                    distro_version=distro_info.version,
                    distro_version_id=distro_info.version_id,
                    distro_id_like=distro_info.id_like,
                )
            )

        if env_detection is not None:
            env_info = export_environment(env_detection)
            if env_info is not None:
                builder.with_environment(env_info)

        if shell_detection is not None:
            shell_info = export_shell(shell_detection)
            if shell_info is not None:
                builder.with_shell(shell_info)

        if packages_detection is not None:
            builder.with_packages(export_packages(packages_detection))

        if theme_detection is not None:
            theme_info = export_themes(theme_detection)
            if theme_info is not None:
                builder.with_themes(theme_info)

        if font_detection is not None:
            font_info = export_fonts(font_detection)
            if font_info is not None:
                builder.with_fonts(font_info)

        if dotfile_entries:
            builder.with_dotfiles(list(export_dotfiles(dotfile_entries)))

        snapshot = builder.build()
        out_path = self._resolve_output_path(output_path)
        written = write_snapshot(snapshot, out_path, compress=compress)

        elapsed = time.monotonic() - start
        return ExportReport(path=written, snapshot=snapshot, duration_seconds=elapsed)

    def _resolve_profile(self, name: str | None) -> Profile:
        name = name or self._config.default_profile
        profile = BUILTIN_PROFILES.get(name)
        if profile is not None:
            return profile
        custom = load_profile(name)
        if custom is not None:
            return custom
        builtin_list = list(BUILTIN_PROFILES)
        raise ExportError(
            f"Unknown profile: {name!r}. Available: {builtin_list} (plus custom TOML profiles)",
        )

    def _resolve_output_path(self, hint: str | Path | None) -> Path:
        if hint:
            return Path(hint)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
        filename = f"setupvault-snapshot-{timestamp}.json"
        export_dir = Path(self._config.export_dir).expanduser()
        return export_dir / filename

    def _detect_shell(self) -> ShellDetection:
        current = detect_current_shell()
        available = detect_available_shells()
        config_files = detect_shell_config_files(current.name)
        return ShellDetection(current=current, available=available, config_files=config_files)

    def _detect_packages(self, adapter: DistroAdapter) -> PackageDetection:
        return PackageDetection(
            official=detect_official_packages(adapter),
            aur=detect_aur_packages(adapter),
            third_party=detect_third_party_packages(adapter),
            flatpak=detect_flatpak_packages(),
            snap=detect_snap_packages(),
        )
