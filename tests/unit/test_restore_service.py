from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from setupvault.core.exceptions import RestoreError
from setupvault.core.snapshot import (
    DistributionInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    Snapshot,
    SnapshotBuilder,
    SystemInfo,
)
from setupvault.services.restore_service import RestoreService


class TestRestoreService:
    @patch("setupvault.services.restore_service.detect_distro")
    @patch("setupvault.services.restore_service.read_snapshot")
    def test_plan_returns_plan(self, mock_read: MagicMock, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.list_official_packages.return_value = []
        adapter.list_aur_packages.return_value = []
        adapter.list_third_party_packages.return_value = []
        adapter.map_package.return_value = None
        adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_detect.return_value = MagicMock(adapter=adapter)
        mock_read.return_value = _minimal_snapshot()

        service = RestoreService()
        plan = service.plan("/fake/snapshot.json")

        assert plan.packages is not None
        assert plan.has_changes is False

    @patch("setupvault.services.restore_service.detect_distro")
    @patch("setupvault.services.restore_service.read_snapshot")
    def test_plan_with_missing_packages(self, mock_read: MagicMock, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.list_official_packages.return_value = []
        adapter.list_aur_packages.return_value = []
        adapter.list_third_party_packages.return_value = []
        adapter.map_package.return_value = None
        adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_detect.return_value = MagicMock(adapter=adapter)

        sys_info = SystemInfo(
            distribution=DistributionInfo(id="arch", name="Arch", version="r"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="test",
            os="Linux",
        )
        pkgs = PackageCollection(
            counts=PackageCounts(official=1),
            official=(PackageEntry(name="firefox", version="1.0"),),
        )
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .build()
        )
        mock_read.return_value = snap

        service = RestoreService()
        plan = service.plan("/fake/snapshot.json")

        assert plan.has_changes is True
        assert "firefox" in plan.packages.to_install

    @patch("setupvault.services.restore_service.detect_distro")
    @patch("setupvault.services.restore_service.read_snapshot")
    def test_plan_unknown_profile_raises(
        self, mock_read: MagicMock, mock_detect: MagicMock
    ) -> None:
        service = RestoreService()
        with pytest.raises(RestoreError, match="Unknown profile"):
            service.plan("/fake/snapshot.json", profile_name="nonexistent")

    @patch("setupvault.services.restore_service.detect_distro")
    @patch("setupvault.services.restore_service.read_snapshot")
    def test_plan_minimal_profile(self, mock_read: MagicMock, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.list_official_packages.return_value = []
        mock_detect.return_value = MagicMock(adapter=adapter)
        mock_read.return_value = _minimal_snapshot()

        service = RestoreService()
        plan = service.plan("/fake/snapshot.json", profile_name="minimal")
        assert plan.themes.actions == ()
        assert plan.fonts.copies == ()
        assert plan.dotfiles.actions == ()
        assert plan.packages is not None

    @patch("setupvault.services.restore_service.detect_distro")
    @patch("setupvault.services.restore_service.read_snapshot")
    def test_apply_empty_plan(self, mock_read: MagicMock, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.list_official_packages.return_value = []
        adapter.list_aur_packages.return_value = []
        adapter.list_third_party_packages.return_value = []
        adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_detect.return_value = MagicMock(adapter=adapter)
        mock_read.return_value = _minimal_snapshot()

        service = RestoreService()
        plan = service.plan("/fake/snapshot.json")
        result = service.apply(plan, dry_run=True)
        assert result.success

    @patch("setupvault.services.restore_service.detect_distro")
    @patch("setupvault.services.restore_service.read_snapshot")
    def test_apply_with_install(self, mock_read: MagicMock, mock_detect: MagicMock) -> None:
        adapter = MagicMock()
        adapter.list_official_packages.return_value = []
        adapter.list_aur_packages.return_value = []
        adapter.list_third_party_packages.return_value = []
        adapter.map_package.return_value = None
        adapter.get_distro_info.return_value = DistributionInfo(
            id="arch", name="Arch Linux", version="rolling"
        )
        mock_detect.return_value = MagicMock(adapter=adapter)

        sys_info = SystemInfo(
            distribution=DistributionInfo(id="arch", name="Arch", version="r"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="test",
            os="Linux",
        )
        pkgs = PackageCollection(
            counts=PackageCounts(official=1),
            official=(PackageEntry(name="vim", version="1.0"),),
        )
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .build()
        )
        mock_read.return_value = snap

        # Set up the adapter's install to succeed
        adapter.install_packages = MagicMock(
            return_value=MagicMock(success=True, installed=["vim"], failed=[], errors=[])
        )

        service = RestoreService()
        plan = service.plan("/fake/snapshot.json")
        result = service.apply(plan, dry_run=False)
        assert result.success


def _minimal_snapshot() -> Snapshot:
    sys_info = SystemInfo(
        distribution=DistributionInfo(id="arch", name="Arch", version="r"),
        kernel=KernelInfo(release="1", version="1"),
        architecture="x86_64",
        hostname="test",
        os="Linux",
    )
    pkgs = PackageCollection(counts=PackageCounts())
    return (
        SnapshotBuilder()
        .with_snapshot_version(1)
        .with_tool_version("1")
        .with_created_at("now")
        .with_system(sys_info)
        .with_packages(pkgs)
        .build()
    )
