from __future__ import annotations

from pathlib import Path
from typing import Any

from setupvault.cli.list_cmd import _format_size, run_list


def _make_args(dir: str | None = None) -> Any:
    return type("Args", (), {"dir": dir})()


class TestCliList:
    def test_empty_directory(self, tmp_path: Path, capsys: Any) -> None:
        rc = run_list(_make_args(dir=str(tmp_path)))
        assert rc == 0
        captured = capsys.readouterr()
        assert "No snapshots" in captured.out

    def test_with_snapshots(self, tmp_path: Path, capsys: Any) -> None:
        (tmp_path / "snap.json").write_text("{}")
        rc = run_list(_make_args(dir=str(tmp_path)))
        assert rc == 0
        captured = capsys.readouterr()
        assert "snap.json" in captured.out

    def test_nonexistent_directory(self, capsys: Any) -> None:
        rc = run_list(_make_args(dir="/nonexistent/snapshots"))
        assert rc == 1

    def test_format_size(self) -> None:
        assert _format_size(500) == "500B"
        assert _format_size(2048) == "2.0K"
        assert _format_size(2 * 1024 * 1024) == "2.0M"
