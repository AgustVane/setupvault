from __future__ import annotations

import json
from pathlib import Path

from setupvault.services.report_service import generate_report

_MINIMAL_SNAPSHOT = {
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
    "themes": {},
    "fonts": {},
    "dotfiles": [],
}


class TestReportService:
    def test_markdown_report(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "snap.json"
        snap_path.write_text(json.dumps(_MINIMAL_SNAPSHOT))
        report = generate_report(snap_path, fmt="markdown")
        assert "# SetupVault Snapshot Report" in report
        assert "Arch Linux" in report

    def test_json_report(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "snap.json"
        snap_path.write_text(json.dumps(_MINIMAL_SNAPSHOT))
        report = generate_report(snap_path, fmt="json")
        data = json.loads(report)
        assert data["snapshot_version"] == 1

    def test_default_format_is_markdown(self, tmp_path: Path) -> None:
        snap_path = tmp_path / "snap.json"
        snap_path.write_text(json.dumps(_MINIMAL_SNAPSHOT))
        report = generate_report(snap_path)
        assert report.startswith("#")
