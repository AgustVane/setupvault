from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from setupvault.cli.diff_cmd import run_diff

_BASE = {
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
        "count": {"official": 1, "aur": 0, "third_party": 0, "flatpak": 0, "snap": 0, "total": 1},
        "official": [{"name": "vim", "version": "9.0"}],
        "aur": [],
        "third_party": [],
    },
    "dotfiles": [],
}


def _make_args(left: str, right: str) -> Any:
    return type("Args", (), {"left": left, "right": right})()


class TestCliDiff:
    def test_identical(self, tmp_path: Path, capsys: Any) -> None:
        left = tmp_path / "a.json"
        right = tmp_path / "b.json"
        left.write_text(json.dumps(_BASE))
        right.write_text(json.dumps(_BASE))
        rc = run_diff(_make_args(str(left), str(right)))
        assert rc == 0
        captured = capsys.readouterr()
        assert "identical" in captured.out

    def test_different(self, tmp_path: Path, capsys: Any) -> None:
        left = tmp_path / "a.json"
        right = tmp_path / "b.json"
        left.write_text(json.dumps(_BASE))
        right_data = {**_BASE}
        right_data["system"] = {**_BASE["system"], "hostname": "other"}
        right.write_text(json.dumps(right_data))
        rc = run_diff(_make_args(str(left), str(right)))
        assert rc == 0
        captured = capsys.readouterr()
        assert "Sections changed" in captured.out

    def test_missing_file(self, capsys: Any) -> None:
        rc = run_diff(_make_args("/nonexistent/a.json", "/nonexistent/b.json"))
        assert rc == 1
