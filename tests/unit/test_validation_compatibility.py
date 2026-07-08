from __future__ import annotations

from setupvault.validation.compatibility import check_compatibility


class TestCheckCompatibility:
    def test_known_distro(self) -> None:
        data = {
            "system": {"distribution": {"id": "arch"}},
            "packages": {"count": {"total": 10}},
        }
        assert check_compatibility(data) == []

    def test_unknown_distro_warning(self) -> None:
        data = {
            "system": {"distribution": {"id": "solaris"}},
            "packages": {"count": {"total": 10}},
        }
        warnings = check_compatibility(data)
        assert any("solaris" in w for w in warnings)

    def test_older_version_warning(self) -> None:
        data = {
            "snapshot_version": 0,
            "system": {"distribution": {"id": "arch"}},
            "packages": {"count": {"total": 10}},
        }
        warnings = check_compatibility(data)
        assert any("version 0" in w for w in warnings)

    def test_empty_packages_warning(self) -> None:
        data = {
            "system": {"distribution": {"id": "arch"}},
            "packages": {"count": {"total": 0}},
        }
        warnings = check_compatibility(data)
        assert any("empty" in w for w in warnings)

    def test_clean_snapshot_no_warnings(self) -> None:
        data = {
            "snapshot_version": 1,
            "system": {"distribution": {"id": "arch", "name": "Arch Linux"}},
            "packages": {"count": {"total": 50}},
        }
        assert check_compatibility(data) == []
