from __future__ import annotations

import json
from pathlib import Path

from setupvault.services.validate_service import validate_snapshot


class TestValidateService:
    def test_valid_snapshot(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "snapshot.json"
        snap_path.write_text(
            json.dumps(
                {
                    "snapshot_version": 1,
                    "tool_version": "1.0.0",
                    "created_at": "2025-01-01T00:00:00",
                    "system": {
                        "distribution": {"id": "arch", "name": "Arch Linux", "version": "rolling"},
                        "kernel": {"release": "6.0", "version": "#1"},
                        "architecture": "x86_64",
                        "hostname": "box",
                    },
                    "packages": {"count": {}, "official": [], "aur": [], "third_party": []},
                }
            )
        )
        report = validate_snapshot(snap_path)
        assert report.valid is True

    def test_missing_required_field(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "bad.json"
        snap_path.write_text(json.dumps({"snapshot_version": 1}))
        report = validate_snapshot(snap_path)
        assert report.valid is False
        assert len(report.schema_errors) > 0

    def test_semantic_error(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "bad_counts.json"
        snap_path.write_text(
            json.dumps(
                {
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
                        "count": {
                            "official": 5,
                            "aur": 0,
                            "third_party": 0,
                            "flatpak": 0,
                            "snap": 0,
                            "total": 3,
                        },
                        "official": [],
                        "aur": [],
                        "third_party": [],
                    },
                }
            )
        )
        report = validate_snapshot(snap_path)
        assert report.valid is False
        assert len(report.semantic_errors) > 0

    def test_warnings_included(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "warn.json"
        snap_path.write_text(
            json.dumps(
                {
                    "snapshot_version": 1,
                    "tool_version": "1.0.0",
                    "created_at": "2025-01-01T00:00:00",
                    "system": {
                        "distribution": {"id": "unknownos", "name": "Unknown", "version": "1"},
                        "kernel": {"release": "6.0", "version": "#1"},
                        "architecture": "x86_64",
                        "hostname": "box",
                    },
                    "packages": {
                        "count": {"total": 0},
                        "official": [],
                        "aur": [],
                        "third_party": [],
                    },
                }
            )
        )
        report = validate_snapshot(snap_path)
        assert len(report.warnings) > 0
