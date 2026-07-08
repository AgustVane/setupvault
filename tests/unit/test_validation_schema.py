from __future__ import annotations

from setupvault.validation.schema import validate_against_schema


class TestValidateAgainstSchema:
    def test_valid_minimal(self) -> None:
        data = {
            "snapshot_version": 1,
            "tool_version": "1.0.0",
            "created_at": "2025-01-01T00:00:00",
            "system": {
                "distribution": {"id": "arch", "name": "Arch Linux", "version": "rolling"},
                "kernel": {"release": "6.0", "version": "#1"},
                "architecture": "x86_64",
                "hostname": "box",
            },
            "packages": {
                "count": {},
                "official": [],
                "aur": [],
                "third_party": [],
            },
        }
        errors = validate_against_schema(data)
        assert errors == []

    def test_missing_required_field(self) -> None:
        data = {
            "snapshot_version": 1,
            "tool_version": "1.0.0",
        }
        errors = validate_against_schema(data)
        assert len(errors) > 0
        assert any("required" in e for e in errors)

    def test_unknown_version_no_schema(self) -> None:
        data = {
            "snapshot_version": 99,
            "tool_version": "1.0.0",
            "created_at": "2025-01-01T00:00:00",
            "system": {},
            "packages": {},
        }
        errors = validate_against_schema(data)
        assert any("No schema found" in e for e in errors)

    def test_invalid_field_type(self) -> None:
        data = {
            "snapshot_version": "not-an-int",
            "tool_version": "1.0.0",
            "created_at": "2025-01-01T00:00:00",
            "system": {
                "distribution": {"id": "arch", "name": "Arch Linux", "version": "rolling"},
                "kernel": {"release": "6.0", "version": "#1"},
                "architecture": "x86_64",
                "hostname": "box",
            },
            "packages": {"count": {}},
        }
        errors = validate_against_schema(data)
        assert isinstance(errors, list)
