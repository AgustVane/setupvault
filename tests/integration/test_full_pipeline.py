from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from setupvault.core.snapshot import (
    DesktopEnvironment,
    DistributionInfo,
    DotfileEntry,
    EnvironmentInfo,
    FlatpakEntry,
    FontEntry,
    FontInfo,
    GtkThemeInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    ShellConfigFile,
    ShellInfo,
    SnapshotBuilder,
    SystemInfo,
    ThemeInfo,
)
from setupvault.core.snapshot import (
    ShellEntry as SnapShellEntry,
)
from setupvault.detectors.fonts import FontDetection
from setupvault.detectors.system import SystemDetection
from setupvault.services.diff_service import diff_snapshots
from setupvault.services.list_service import list_snapshots
from setupvault.services.report_service import generate_report
from setupvault.services.validate_service import validate_snapshot
from setupvault.storage.local import read_snapshot, write_snapshot


class TestFullPipelineExportStoreRead:
    def test_export_store_read_snapshot(self, tmp_path: Path) -> None:
        """Full pipeline: build -> write -> read -> validate -> report."""
        snapshot_path = tmp_path / "test_full.json"

        snapshot = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("2.0.0")
            .with_created_at("2025-01-01T00:00:00Z")
            .with_system(
                SystemInfo(
                    distribution=DistributionInfo(id="arch", name="Arch Linux", version="rolling"),
                    kernel=KernelInfo(release="6.6.32-arch1-1", version="#1 SMP PREEMPT_DYNAMIC"),
                    architecture="x86_64",
                    hostname="test-rig",
                )
            )
            .with_packages(
                PackageCollection(
                    counts=PackageCounts(official=2, aur=1, third_party=1, flatpak=1, snap=0),
                    official=(
                        PackageEntry(name="linux", version="6.6.32", repository="core"),
                        PackageEntry(name="firefox", version="127.0", repository="extra"),
                    ),
                    aur=(PackageEntry(name="yay-bin", version="12.0.0"),),
                    third_party=(
                        PackageEntry(name="spotify", version="1.2.0", repository="chaotic-aur"),
                    ),
                    flatpak=(
                        FlatpakEntry(
                            name="Froggy", app_id="io.github.froggy.Froggy", version="1.0"
                        ),
                    ),
                    snap=(),
                )
            )
            .with_themes(
                ThemeInfo(
                    gtk=GtkThemeInfo(
                        theme="Adwaita",
                        icon_theme="Adwaita",
                        cursor_theme="Adwaita",
                        font_name="Cantarell 11",
                    )
                )
            )
            .with_fonts(
                FontInfo(
                    system_fonts=(
                        FontEntry(family="FiraCode Nerd Font"),
                        FontEntry(family="Cantarell"),
                    ),
                )
            )
            .with_dotfiles(
                [
                    DotfileEntry(
                        path=".zshrc",
                        hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        size=2048,
                        permissions="644",
                        content="IyB6c2hyYwpleHBvcnQgRURJVD1uZXZpbQo=",
                    ),
                ]
            )
            .with_environment(
                EnvironmentInfo(
                    desktop_environment=DesktopEnvironment(name="zsh"),
                    session_type="wayland",
                )
            )
            .with_shell(
                ShellInfo(
                    current=SnapShellEntry(name="zsh", version="5.9", path="/bin/zsh"),
                    config_files=(
                        ShellConfigFile(path=".zshrc"),
                        ShellConfigFile(path=".zshenv"),
                    ),
                )
            )
            .build()
        )

        write_snapshot(snapshot, str(snapshot_path))
        assert snapshot_path.exists()

        restored = read_snapshot(str(snapshot_path))
        assert restored.snapshot_version == 1
        assert restored.tool_version == "2.0.0"
        assert restored.system.hostname == "test-rig"
        assert len(restored.packages.official) == 2
        assert len(restored.packages.aur) == 1
        assert len(restored.packages.third_party) == 1
        assert len(restored.packages.flatpak) == 1
        assert restored.packages.counts.total == 5
        assert restored.themes is not None
        assert restored.themes.gtk.theme == "Adwaita"
        assert len(restored.dotfiles) == 1
        assert restored.dotfiles[0].path == ".zshrc"
        assert restored.dotfiles[0].content == "IyB6c2hyYwpleHBvcnQgRURJVD1uZXZpbQo="
        assert restored.environment is not None
        assert restored.environment.desktop_environment is not None
        assert restored.environment.desktop_environment.name == "zsh"
        assert restored.shell is not None
        assert restored.shell.current is not None
        assert restored.shell.current.name == "zsh"

        result = validate_snapshot(snapshot_path)
        assert result.valid is True, f"Validation failed: {result.all_errors}"

        md = generate_report(snapshot_path, fmt="markdown")
        assert "Arch Linux" in md
        assert "linux" in md
        assert "spotify" in md

        json_report = generate_report(snapshot_path, fmt="json")
        parsed = json.loads(json_report)
        assert parsed["system"]["distribution"]["id"] == "arch"

        html = generate_report(snapshot_path, fmt="html")
        assert "<html" in html
        assert "Arch Linux" in html

    def test_diff_snapshots(self, tmp_path: Path) -> None:
        """Diff two snapshots and verify changes are detected."""
        left = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("2.0.0")
            .with_created_at("2025-01-01T00:00:00Z")
            .with_system(
                SystemInfo(
                    distribution=DistributionInfo(id="arch", name="Arch Linux", version="rolling"),
                    kernel=KernelInfo(release="6.6.0", version="#1"),
                    architecture="x86_64",
                    hostname="same-box",
                )
            )
            .with_packages(
                PackageCollection(
                    counts=PackageCounts(official=1),
                    official=(PackageEntry(name="linux", version="6.6.0"),),
                    aur=(),
                    third_party=(),
                    flatpak=(),
                    snap=(),
                )
            )
            .with_dotfiles([])
            .build()
        )

        right = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("2.0.0")
            .with_created_at("2025-06-01T00:00:00Z")
            .with_system(
                SystemInfo(
                    distribution=DistributionInfo(id="arch", name="Arch Linux", version="rolling"),
                    kernel=KernelInfo(release="6.6.1", version="#1"),
                    architecture="x86_64",
                    hostname="same-box",
                )
            )
            .with_packages(
                PackageCollection(
                    counts=PackageCounts(official=1),
                    official=(PackageEntry(name="linux", version="6.6.1"),),
                    aur=(),
                    third_party=(),
                    flatpak=(),
                    snap=(),
                )
            )
            .with_dotfiles([])
            .build()
        )

        left_path = tmp_path / "left.json"
        right_path = tmp_path / "right.json"
        write_snapshot(left, left_path)
        write_snapshot(right, right_path)

        diff = diff_snapshots(left_path, right_path)
        assert not diff.same
        assert "system" in diff.sections_changed

    def test_list_snapshots(self, tmp_path: Path) -> None:
        """List snapshots in a directory."""
        base = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("2.0.0")
            .with_created_at("2025-01-01T00:00:00Z")
            .with_system(
                SystemInfo(
                    distribution=DistributionInfo(id="arch", name="Arch", version="rolling"),
                    kernel=KernelInfo(release="6.6.0", version="#1"),
                    architecture="x86_64",
                    hostname="test",
                )
            )
            .with_packages(
                PackageCollection(
                    counts=PackageCounts(),
                    official=(),
                    aur=(),
                    third_party=(),
                    flatpak=(),
                    snap=(),
                )
            )
            .with_dotfiles([])
            .build()
        )

        for name in ("alpha.json", "beta.json", "gamma.snapshot"):
            write_snapshot(base, tmp_path / name)

        result = list_snapshots(tmp_path)
        names = sorted(e.filename for e in result.snapshots)
        assert names == ["alpha.json", "beta.json", "gamma.snapshot"]

    def test_validate_reports_errors(self, tmp_path: Path) -> None:
        """Validate an invalid snapshot yields proper errors."""
        bad_path = tmp_path / "bad.json"
        bad_path.write_text('{"snapshot_version": 999}')

        result = validate_snapshot(bad_path)
        assert result.valid is False
        assert len(result.all_errors) > 0

    def test_export_via_service(self, tmp_path: Path) -> None:
        """Test export service orchestrates all detectors correctly."""
        from setupvault.services.export_service import ExportReport, ExportService

        snapshots_dir = tmp_path

        from setupvault.detectors.shell import ShellConfigFile as DetectedConfigFile
        from setupvault.detectors.shell import ShellEntry as DetectedShellEntry

        current_shell_mock = DetectedShellEntry(name="bash", version="5.2", path="/bin/bash")
        config_mock = DetectedConfigFile(path=".bashrc")

        with (
            patch("setupvault.services.export_service.detect_distro") as mock_dd,
            patch("setupvault.services.export_service.detect_system") as mock_sys,
            patch("setupvault.services.export_service.detect_environment") as mock_env,
            patch(
                "setupvault.services.export_service.detect_available_shells",
                return_value=[current_shell_mock],
            ),
            patch(
                "setupvault.services.export_service.detect_current_shell",
                return_value=current_shell_mock,
            ),
            patch(
                "setupvault.services.export_service.detect_shell_config_files",
                return_value=(config_mock,),
            ),
            patch("setupvault.services.export_service.detect_themes", return_value=None),
            patch("setupvault.services.export_service.detect_fonts") as mock_fonts,
            patch("setupvault.services.export_service.detect_official_packages") as mock_official,
            patch("setupvault.services.export_service.detect_aur_packages", return_value=()),
            patch(
                "setupvault.services.export_service.detect_third_party_packages", return_value=()
            ),
            patch("setupvault.services.export_service.detect_flatpak_packages", return_value=()),
            patch("setupvault.services.export_service.detect_snap_packages", return_value=()),
            patch("setupvault.services.export_service.detect_dotfiles") as mock_df,
            patch("setupvault.services.export_service.write_snapshot"),
        ):
            mock_sys.return_value = SystemDetection(
                os_name="Debian GNU/Linux",
                kernel_release="6.1.0",
                kernel_version="#1",
                architecture="amd64",
                hostname="deb-box",
            )
            mock_env.return_value = MagicMock(shell="/bin/bash", desktop="", session_type="tty")
            mock_fonts.return_value = FontDetection()
            mock_official.return_value = (MagicMock(name="bash", version="5.2"),)
            mock_df.return_value = (
                MagicMock(path=".bashrc", hash="abc", size=100, permissions="644"),
            )

            mock_adapter = MagicMock()
            mock_adapter.distro_id = "debian"
            mock_dd.return_value.adapter = mock_adapter
            mock_dd.return_value.distro_id = "debian"

            service = ExportService()
            report: ExportReport = service.execute(output_path=str(snapshots_dir / "exported.json"))

        assert report.snapshot.system.hostname == "deb-box"
        assert len(report.snapshot.packages.official) == 1

    def test_dotfile_content_in_snapshot(self, tmp_path: Path) -> None:
        """Dotfile content is stored in and restored from the snapshot."""
        snapshot_path = tmp_path / "dotfiles_content.json"

        snapshot = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("2.0.0")
            .with_created_at("2025-01-01T00:00:00Z")
            .with_system(
                SystemInfo(
                    distribution=DistributionInfo(id="arch", name="Arch", version="rolling"),
                    kernel=KernelInfo(release="6.6.0", version="#1"),
                    architecture="x86_64",
                    hostname="test",
                )
            )
            .with_packages(
                PackageCollection(
                    counts=PackageCounts(),
                    official=(),
                    aur=(),
                    third_party=(),
                    flatpak=(),
                    snap=(),
                )
            )
            .with_dotfiles(
                [
                    DotfileEntry(
                        path=".config/wezterm/wezterm.lua",
                        hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        size=42,
                        permissions="644",
                        content="bG9jYWwgdiA9IDQyCg==",
                    ),
                ]
            )
            .build()
        )

        write_snapshot(snapshot, str(snapshot_path))
        restored = read_snapshot(str(snapshot_path))
        assert len(restored.dotfiles) == 1
        df = restored.dotfiles[0]
        assert df.path == ".config/wezterm/wezterm.lua"
        assert df.content == "bG9jYWwgdiA9IDQyCg=="
        assert df.hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert df.size == 42
