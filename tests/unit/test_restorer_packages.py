from __future__ import annotations

from unittest.mock import MagicMock

from setupvault.core.snapshot import (
    FlatpakEntry,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    SnapEntry,
)
from setupvault.distro_adapters.base import DistroAdapter, InstallResult, Package
from setupvault.restorers.packages_restorer import apply_packages, plan_packages


class TestPlanPackages:
    def test_all_present(self) -> None:
        adapter = _adapter_with_installed({"firefox", "vim"})
        pkgs = PackageCollection(
            counts=PackageCounts(official=2),
            official=(
                PackageEntry(name="firefox", version="1.0"),
                PackageEntry(name="vim", version="2.0"),
            ),
        )
        plan = plan_packages(pkgs, adapter)
        assert plan.to_install == ()
        assert plan.already_present == 2

    def test_some_missing(self) -> None:
        adapter = _adapter_with_installed({"firefox"})
        pkgs = PackageCollection(
            counts=PackageCounts(official=2),
            official=(
                PackageEntry(name="firefox", version="1.0"),
                PackageEntry(name="vim", version="2.0"),
            ),
        )
        plan = plan_packages(pkgs, adapter)
        assert "vim" in plan.to_install
        assert plan.already_present == 1

    def test_unsafe_name_rejected(self) -> None:
        adapter = _adapter_with_installed(set())
        pkgs = PackageCollection(
            counts=PackageCounts(official=1),
            official=(PackageEntry(name="; rm -rf /", version="1.0"),),
        )
        plan = plan_packages(pkgs, adapter)
        assert "; rm -rf /" in plan.unknown_names
        assert plan.to_install == ()

    def test_flatpak_skipped_with_warning(self) -> None:
        adapter = _adapter_with_installed(set())
        pkgs = PackageCollection(
            counts=PackageCounts(flatpak=1),
            flatpak=(FlatpakEntry(name="Brave", app_id="com.brave.Browser"),),
        )
        plan = plan_packages(pkgs, adapter)
        assert any("Flatpak" in w for w in plan.warnings)

    def test_snap_skipped_with_warning(self) -> None:
        adapter = _adapter_with_installed(set())
        pkgs = PackageCollection(
            counts=PackageCounts(snap=1),
            snap=(SnapEntry(name="lxd"),),
        )
        plan = plan_packages(pkgs, adapter)
        assert any("Snap" in w for w in plan.warnings)

    def test_mapped_name(self) -> None:
        adapter = _adapter_with_installed(set())
        adapter.map_package = MagicMock(return_value="vim-extra")  # type: ignore[method-assign]
        pkgs = PackageCollection(
            counts=PackageCounts(official=1),
            official=(PackageEntry(name="vim", version="1.0"),),
        )
        plan = plan_packages(pkgs, adapter)
        assert "vim-extra" in plan.to_install

    def test_mapped_name_already_installed(self) -> None:
        adapter = _adapter_with_installed({"vim-extra"})
        adapter.map_package = MagicMock(return_value="vim-extra")  # type: ignore[method-assign]
        pkgs = PackageCollection(
            counts=PackageCounts(official=1),
            official=(PackageEntry(name="vim", version="1.0"),),
        )
        plan = plan_packages(pkgs, adapter)
        assert plan.to_install == ()

    def test_aur_packages_included(self) -> None:
        adapter = _adapter_with_installed(set())
        pkgs = PackageCollection(
            counts=PackageCounts(official=0, aur=2),
            aur=(
                PackageEntry(name="yay", version="12.0"),
                PackageEntry(name="paru", version="2.0"),
            ),
        )
        plan = plan_packages(pkgs, adapter)
        assert "yay" in plan.to_install
        assert "paru" in plan.to_install

    def test_third_party_included(self) -> None:
        adapter = _adapter_with_installed(set())
        pkgs = PackageCollection(
            counts=PackageCounts(official=0, third_party=1),
            third_party=(PackageEntry(name="chaotic-pkg", version="1.0"),),
        )
        plan = plan_packages(pkgs, adapter)
        assert "chaotic-pkg" in plan.to_install


class TestApplyPackages:
    def test_empty_plan_returns_immediately(self) -> None:
        adapter = MagicMock(spec=DistroAdapter)
        plan = plan_packages(
            PackageCollection(counts=PackageCounts()),
            adapter,
        )
        result = apply_packages(plan, adapter)
        assert result.success
        assert result.installed == []
        adapter.install_packages.assert_not_called()

    def test_delegates_to_adapter(self) -> None:
        adapter = _adapter_with_installed(set())
        adapter.install_packages = MagicMock(
            return_value=InstallResult(success=True, installed=["vim"], failed=[], errors=[])
        )
        pkgs = PackageCollection(
            counts=PackageCounts(official=1),
            official=(PackageEntry(name="vim", version="1.0"),),
        )
        plan = plan_packages(pkgs, adapter)
        result = apply_packages(plan, adapter, dry_run=False, assume_yes=False)
        assert result.success
        adapter.install_packages.assert_called_once_with(["vim"], dry_run=False, assume_yes=False)


def _adapter_with_installed(names: set[str]) -> MagicMock:
    adapter = MagicMock(spec=DistroAdapter)
    adapter.list_official_packages.return_value = [Package(name=n) for n in names]
    adapter.list_aur_packages.return_value = []
    adapter.list_third_party_packages.return_value = []
    adapter.map_package.return_value = None
    return adapter
