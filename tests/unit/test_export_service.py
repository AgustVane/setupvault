from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from setupvault.core.exceptions import ExportError
from setupvault.core.snapshot import DistributionInfo, Snapshot
from setupvault.services.export_service import ExportService


class TestExportService:
    """Tests for ``ExportService``.

    Uses patching to avoid real system calls. The goal is to verify
    orchestration logic, not individual detector accuracy.
    """

    @patch("setupvault.services.export_service.detect_distro")
    @patch("setupvault.services.export_service.detect_system")
    @patch("setupvault.services.export_service.detect_environment")
    @patch("setupvault.services.export_service.detect_available_shells")
    @patch("setupvault.services.export_service.detect_current_shell")
    @patch("setupvault.services.export_service.detect_shell_config_files")
    @patch("setupvault.services.export_service.detect_themes")
    @patch("setupvault.services.export_service.detect_fonts")
    @patch("setupvault.services.export_service.detect_official_packages")
    @patch("setupvault.services.export_service.detect_aur_packages")
    @patch("setupvault.services.export_service.detect_third_party_packages")
    @patch("setupvault.services.export_service.detect_flatpak_packages")
    @patch("setupvault.services.export_service.detect_snap_packages")
    @patch("setupvault.services.export_service.detect_dotfiles")
    @patch("setupvault.services.export_service.write_snapshot")
    def test_full_export(
        self,
        mock_write: MagicMock,
        mock_dotfiles: MagicMock,
        mock_snap: MagicMock,
        mock_flatpak: MagicMock,
        mock_third_party: MagicMock,
        mock_aur: MagicMock,
        mock_official: MagicMock,
        mock_fonts: MagicMock,
        mock_themes: MagicMock,
        mock_shell_cf: MagicMock,
        mock_shell_cur: MagicMock,
        mock_shell_avail: MagicMock,
        mock_env: MagicMock,
        mock_sys: MagicMock,
        mock_distro: MagicMock,
        tmp_path: Path,
    ) -> None:
        # Arrange — set up mock return values to produce a valid snapshot
        distro_adapter = MagicMock()
        distro_adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_distro.return_value = MagicMock(adapter=distro_adapter)

        mock_sys.return_value = MagicMock(
            kernel_release="6.6.32-arch1-1",
            kernel_version="#1",
            architecture="x86_64",
            hostname="rig",
            uptime_seconds=3600,
            os_name="Linux",
        )

        mock_env.return_value = MagicMock(
            desktop_environment="Hyprland",
            window_manager="Hyprland",
            display_server="wayland",
        )

        mock_shell_cur.return_value = MagicMock(name="zsh", version="5.9", path="/usr/bin/zsh")
        mock_shell_avail.return_value = ()
        mock_shell_cf.return_value = ()

        mock_official.return_value = (MagicMock(name="linux", version="6.6.32", repository="core"),)
        mock_aur.return_value = ()
        mock_third_party.return_value = ()
        mock_flatpak.return_value = ()
        mock_snap.return_value = ()

        mock_themes.return_value = MagicMock(gtk=None, qt=None)

        mock_fonts.return_value = MagicMock(system_fonts=())

        mock_dotfiles.return_value = ()

        mock_write.return_value = tmp_path / "snapshot.json"

        service = ExportService()

        # Act
        report = service.execute(
            profile_name="full",
            output_path=tmp_path / "snapshot.json",
        )

        # Assert
        assert report.path == tmp_path / "snapshot.json"
        assert isinstance(report.snapshot, Snapshot)
        assert report.snapshot.snapshot_version == 1
        assert report.snapshot.system.distribution.id == "arch"
        assert report.duration_seconds >= 0

        mock_distro.assert_called_once()
        mock_sys.assert_called_once()
        mock_env.assert_called_once()
        mock_official.assert_called_once()
        mock_write.assert_called_once()

    @patch("setupvault.services.export_service.detect_distro")
    def test_unknown_profile_raises(self, mock_distro: MagicMock) -> None:
        service = ExportService()
        with pytest.raises(ExportError, match="Unknown profile"):
            service.execute(profile_name="nonexistent")

    @patch("setupvault.services.export_service.detect_distro")
    def test_distro_failure_propagates(self, mock_distro: MagicMock) -> None:
        mock_distro.side_effect = RuntimeError("no /etc/os-release")
        service = ExportService()
        with pytest.raises(ExportError, match="Distribution detection failed"):
            service.execute()

    @patch("setupvault.services.export_service.detect_distro")
    @patch("setupvault.services.export_service.detect_system")
    @patch("setupvault.services.export_service.detect_official_packages")
    @patch("setupvault.services.export_service.detect_aur_packages")
    @patch("setupvault.services.export_service.detect_third_party_packages")
    @patch("setupvault.services.export_service.detect_flatpak_packages")
    @patch("setupvault.services.export_service.detect_snap_packages")
    @patch("setupvault.services.export_service.write_snapshot")
    def test_minimal_profile_skips_optional_sections(
        self,
        mock_write: MagicMock,
        mock_snap: MagicMock,
        mock_flatpak: MagicMock,
        mock_third_party: MagicMock,
        mock_aur: MagicMock,
        mock_official: MagicMock,
        mock_sys: MagicMock,
        mock_distro: MagicMock,
    ) -> None:
        distro_adapter = MagicMock()
        distro_adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_distro.return_value = MagicMock(adapter=distro_adapter)

        mock_sys.return_value = MagicMock(
            kernel_release="6.6.32-arch1-1",
            kernel_version="#1",
            architecture="x86_64",
            hostname="rig",
            uptime_seconds=3600,
            os_name="Linux",
        )
        mock_official.return_value = ()
        mock_aur.return_value = ()
        mock_third_party.return_value = ()
        mock_flatpak.return_value = ()
        mock_snap.return_value = ()

        # No need to mock optional detectors — they shouldn't be called

        # Mock write_snapshot to return a path
        mock_write.return_value = MagicMock()

        service = ExportService()
        report = service.execute(profile_name="minimal")

        assert report.snapshot.environment is None
        assert report.snapshot.shell is None
        assert report.snapshot.themes is None
        assert report.snapshot.fonts is None
        assert report.snapshot.dotfiles == ()

    @patch("setupvault.services.export_service.detect_distro")
    @patch("setupvault.services.export_service.detect_system")
    @patch("setupvault.services.export_service.detect_environment")
    @patch("setupvault.services.export_service.detect_available_shells")
    @patch("setupvault.services.export_service.detect_current_shell")
    @patch("setupvault.services.export_service.detect_shell_config_files")
    @patch("setupvault.services.export_service.detect_themes")
    @patch("setupvault.services.export_service.detect_fonts")
    @patch("setupvault.services.export_service.detect_official_packages")
    @patch("setupvault.services.export_service.detect_aur_packages")
    @patch("setupvault.services.export_service.detect_third_party_packages")
    @patch("setupvault.services.export_service.detect_flatpak_packages")
    @patch("setupvault.services.export_service.detect_snap_packages")
    @patch("setupvault.services.export_service.detect_dotfiles")
    @patch("setupvault.services.export_service.write_snapshot")
    def test_exclude_sections_skips_those_detectors(
        self,
        mock_write: MagicMock,
        mock_dotfiles: MagicMock,
        mock_snap: MagicMock,
        mock_flatpak: MagicMock,
        mock_third_party: MagicMock,
        mock_aur: MagicMock,
        mock_official: MagicMock,
        mock_fonts: MagicMock,
        mock_themes: MagicMock,
        mock_shell_cf: MagicMock,
        mock_shell_cur: MagicMock,
        mock_shell_avail: MagicMock,
        mock_env: MagicMock,
        mock_sys: MagicMock,
        mock_distro: MagicMock,
    ) -> None:
        distro_adapter = MagicMock()
        distro_adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_distro.return_value = MagicMock(adapter=distro_adapter)

        mock_sys.return_value = MagicMock(
            kernel_release="6.6.32-arch1-1",
            kernel_version="#1",
            architecture="x86_64",
            hostname="rig",
            uptime_seconds=3600,
            os_name="Linux",
        )
        mock_env.return_value = MagicMock()
        mock_shell_cur.return_value = MagicMock(name="bash")
        mock_shell_avail.return_value = ()
        mock_shell_cf.return_value = ()
        mock_official.return_value = ()
        mock_aur.return_value = ()
        mock_third_party.return_value = ()
        mock_flatpak.return_value = ()
        mock_snap.return_value = ()
        mock_themes.return_value = MagicMock()
        mock_fonts.return_value = MagicMock()
        mock_dotfiles.return_value = ()
        mock_write.return_value = MagicMock()

        service = ExportService()
        report = service.execute(
            exclude_sections=["themes", "fonts", "dotfiles", "shell", "environment"]
        )

        assert report.snapshot.environment is None
        assert report.snapshot.shell is None
        assert report.snapshot.themes is None
        assert report.snapshot.fonts is None
        assert report.snapshot.dotfiles == ()
        # But these should still be present
        assert report.snapshot.system is not None
        assert report.snapshot.packages is not None
