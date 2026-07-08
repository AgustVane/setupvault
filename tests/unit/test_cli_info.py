from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from setupvault.cli.info_cmd import run_info


def _make_args(snapshot: str) -> Any:
    return type("Args", (), {"snapshot": snapshot})()


class TestCliInfo:
    def test_existing_snapshot(self, tmp_path: Path, capsys: Any) -> None:
        snap_path = tmp_path / "snap.json"
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
        rc = run_info(_make_args(str(snap_path)))
        assert rc == 0
        captured = capsys.readouterr()
        assert "Arch Linux" in captured.out

    def test_missing_snapshot(self, capsys: Any) -> None:
        rc = run_info(_make_args("/nonexistent/snap.json"))
        assert rc == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err
