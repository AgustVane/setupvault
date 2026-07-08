from __future__ import annotations

from pathlib import Path

from setupvault.services.list_service import list_snapshots


class TestListService:
    def test_no_directory_returns_error(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "does_not_exist"
        result = list_snapshots(custom_dir=nonexistent)
        assert result.error is not None
        assert result.snapshots == []

    def test_empty_directory(self, tmp_path: Path) -> None:
        result = list_snapshots(custom_dir=tmp_path)
        assert result.error is None
        assert result.snapshots == []

    def test_lists_json_files(self, tmp_path: Path) -> None:
        (tmp_path / "snap1.json").write_text("{}")
        (tmp_path / "snap2.json").write_text("{}")
        result = list_snapshots(custom_dir=tmp_path)
        assert len(result.snapshots) == 2
        names = [e.filename for e in result.snapshots]
        assert "snap1.json" in names
        assert "snap2.json" in names

    def test_ignores_non_snapshot_files(self, tmp_path: Path) -> None:
        (tmp_path / "snap.json").write_text("{}")
        (tmp_path / "readme.txt").write_text("hello")
        result = list_snapshots(custom_dir=tmp_path)
        assert len(result.snapshots) == 1

    def test_includes_size_and_modified(self, tmp_path: Path) -> None:
        (tmp_path / "snap.json").write_text("{}")
        result = list_snapshots(custom_dir=tmp_path)
        entry = result.snapshots[0]
        assert entry.size_bytes > 0
        assert entry.modified is not None
