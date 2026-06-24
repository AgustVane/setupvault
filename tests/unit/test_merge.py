from setupvault.core.merge import MergeStrategy, ThreeWayMerger


class TestThreeWayMerger:
    def test_unchanged_returns_applied(self) -> None:
        merger = ThreeWayMerger(MergeStrategy.KEEP_NEWER)
        result = merger.merge("file1.txt", "a", "a", "a")
        assert result.applied is True
        assert "Unchanged" in result.detail

    def test_source_applied_when_destination_unchanged(self) -> None:
        merger = ThreeWayMerger(MergeStrategy.KEEP_NEWER)
        result = merger.merge("file1.txt", "a", "b", "a")
        assert result.applied is True
        assert "source" in result.detail

    def test_destination_kept_when_source_unchanged(self) -> None:
        merger = ThreeWayMerger(MergeStrategy.KEEP_NEWER)
        result = merger.merge("file1.txt", "a", "a", "b")
        assert result.applied is True
        assert "Kept destination" in result.detail

    def test_keep_source_strategy(self) -> None:
        merger = ThreeWayMerger(MergeStrategy.KEEP_SOURCE)
        result = merger.merge("file1.txt", "a", "b", "c")
        assert result.applied is True
        assert "Applied source" in result.detail

    def test_keep_dest_strategy(self) -> None:
        merger = ThreeWayMerger(MergeStrategy.KEEP_DEST)
        result = merger.merge("file1.txt", "a", "b", "c")
        assert result.applied is True
        assert "Kept destination" in result.detail

    def test_interactive_returns_not_applied(self) -> None:
        merger = ThreeWayMerger(MergeStrategy.INTERACTIVE)
        result = merger.merge("file1.txt", "a", "b", "c")
        assert result.applied is False
        assert "Awaiting user" in result.detail

    def test_item_id_preserved(self) -> None:
        merger = ThreeWayMerger()
        result = merger.merge("my-config.json", "a", "b", "a")
        assert result.item == "my-config.json"
