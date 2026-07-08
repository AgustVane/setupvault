from __future__ import annotations

import json
from pathlib import Path

from setupvault.services.diff_service import diff_snapshots

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
        "count": {"official": 2, "aur": 1, "third_party": 0, "flatpak": 0, "snap": 0, "total": 3},
        "official": [{"name": "vim", "version": "9.0"}, {"name": "bash", "version": "5.1"}],
        "aur": [{"name": "yay", "version": "12.0"}],
        "third_party": [],
    },
    "themes": {},
    "fonts": {},
    "dotfiles": [],
}


class TestDiffService:
    def test_identical_snapshots(self, tmp_path: Path) -> None:
        left = tmp_path / "left.json"
        right = tmp_path / "right.json"
        left.write_text(json.dumps(_BASE))
        right.write_text(json.dumps(_BASE))
        result = diff_snapshots(left, right)
        assert result.same is True
        assert len(result.sections_changed) == 0

    def test_different_system(self, tmp_path: Path) -> None:
        left = tmp_path / "left.json"
        right = tmp_path / "right.json"
        left_data = {**_BASE}
        right_data = {**_BASE, "system": {**_BASE["system"], "hostname": "other"}}
        left.write_text(json.dumps(left_data))
        right.write_text(json.dumps(right_data))
        result = diff_snapshots(left, right)
        assert result.same is False
        assert "system" in result.sections_changed

    def test_different_packages(self, tmp_path: Path) -> None:
        left = tmp_path / "left.json"
        right = tmp_path / "right.json"
        left_data = {**_BASE}
        right_data = {**_BASE}
        right_data["packages"] = {
            **_BASE["packages"],
            "count": {**_BASE["packages"]["count"], "official": 3, "total": 4},
            "official": [
                {"name": "vim", "version": "9.0"},
                {"name": "bash", "version": "5.1"},
                {"name": "zsh", "version": "5.8"},
            ],
        }
        left.write_text(json.dumps(left_data))
        right.write_text(json.dumps(right_data))
        result = diff_snapshots(left, right)
        assert result.same is False
        assert "packages" in result.sections_changed

    def test_different_dotfiles(self, tmp_path: Path) -> None:
        left = tmp_path / "left.json"
        right = tmp_path / "right.json"
        left_data = {**_BASE}
        right_data = {**_BASE, "dotfiles": [{"path": ".bashrc", "hash": "a" * 64}]}
        left.write_text(json.dumps(left_data))
        right.write_text(json.dumps(right_data))
        result = diff_snapshots(left, right)
        assert result.same is False
        assert "dotfiles" in result.sections_changed
