from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from setupvault.cli.report_cmd import run_report


def _make_args(snapshot: str, fmt: str = "markdown", output: str | None = None) -> Any:
    return type("Args", (), {"snapshot": snapshot, "format": fmt, "output": output})()


@pytest.fixture
def valid_snapshot(tmp_path: Path) -> Path:
    snap = tmp_path / "snap.json"
    snap.write_text(
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
    return snap


class TestCliReport:
    def test_markdown_output(self, valid_snapshot: Path, capsys: Any) -> None:
        rc = run_report(_make_args(str(valid_snapshot), fmt="markdown"))
        assert rc == 0
        captured = capsys.readouterr()
        assert "SetupVault Snapshot Report" in captured.out

    def test_json_output(self, valid_snapshot: Path, capsys: Any) -> None:
        rc = run_report(_make_args(str(valid_snapshot), fmt="json"))
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["snapshot_version"] == 1

    def test_output_to_file(self, valid_snapshot: Path, tmp_path: Path) -> None:
        out_path = tmp_path / "report.md"
        rc = run_report(_make_args(str(valid_snapshot), fmt="markdown", output=str(out_path)))
        assert rc == 0
        assert out_path.exists()
        assert "# SetupVault Snapshot Report" in out_path.read_text()

    def test_missing_snapshot(self, capsys: Any) -> None:
        rc = run_report(_make_args("/nonexistent.json"))
        assert rc == 1
