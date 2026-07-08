from __future__ import annotations

from setupvault.validation.rules import validate_semantic


class TestValidateSemantic:
    def test_valid_full_snapshot(self) -> None:
        data = {
            "snapshot_version": 1,
            "tool_version": "1.0.0",
            "created_at": "2025-01-01T00:00:00",
            "system": {
                "distribution": {"id": "arch", "name": "Arch Linux", "version": "rolling"},
            },
            "packages": {
                "count": {
                    "official": 2,
                    "aur": 1,
                    "third_party": 0,
                    "flatpak": 0,
                    "snap": 0,
                    "total": 3,
                },
            },
        }
        assert validate_semantic(data) == []

    def test_unsupported_version(self) -> None:
        data = {"snapshot_version": 999, "system": {}, "packages": {}}
        errors = validate_semantic(data)
        assert any("not supported" in e for e in errors)

    def test_invalid_created_at(self) -> None:
        data = {
            "snapshot_version": 1,
            "created_at": "not-a-date",
            "system": {},
            "packages": {},
        }
        errors = validate_semantic(data)
        assert any("ISO 8601" in e for e in errors)

    def test_package_count_mismatch(self) -> None:
        data = {
            "snapshot_version": 1,
            "system": {},
            "packages": {
                "count": {
                    "official": 5,
                    "aur": 0,
                    "third_party": 0,
                    "flatpak": 0,
                    "snap": 0,
                    "total": 3,
                },
            },
        }
        errors = validate_semantic(data)
        assert any("does not match sum" in e for e in errors)

    def test_suspicious_package_name(self) -> None:
        data = {
            "snapshot_version": 1,
            "system": {},
            "packages": {
                "count": {"total": 1},
                "official": [{"name": "../../etc/passwd", "version": "1.0"}],
                "aur": [],
                "third_party": [],
            },
        }
        errors = validate_semantic(data)
        assert any("suspicious" in e for e in errors)

    def test_absolute_dotfile_path(self) -> None:
        data = {
            "snapshot_version": 1,
            "system": {},
            "packages": {"count": {}},
            "dotfiles": [{"path": "/etc/shadow", "hash": "a" * 64}],
        }
        errors = validate_semantic(data)
        assert any("absolute" in e for e in errors)

    def test_invalid_dotfile_hash(self) -> None:
        data = {
            "snapshot_version": 1,
            "system": {},
            "packages": {"count": {}},
            "dotfiles": [{"path": ".bashrc", "hash": "too-short"}],
        }
        errors = validate_semantic(data)
        assert any("SHA-256" in e for e in errors)
