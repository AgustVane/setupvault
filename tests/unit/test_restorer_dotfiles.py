from __future__ import annotations

from unittest.mock import patch

from setupvault.core.snapshot import DotfileEntry
from setupvault.restorers.dotfiles_restorer import apply_dotfiles, plan_dotfiles


class TestPlanDotfiles:
    def test_absolute_path_rejected(self) -> None:
        entries = (DotfileEntry(path="/etc/passwd"),)
        plan = plan_dotfiles(entries)
        assert "/etc/passwd" in plan.rejected
        assert plan.actions == ()

    def test_path_traversal_rejected(self) -> None:
        entries = (DotfileEntry(path="../etc/passwd"),)
        plan = plan_dotfiles(entries)
        assert "../etc/passwd" in plan.rejected

    def test_double_dot_component_rejected(self) -> None:
        entries = (DotfileEntry(path="foo/../../bar"),)
        plan = plan_dotfiles(entries)
        assert "foo/../../bar" in plan.rejected

    def test_valid_new_file(self) -> None:
        entries = (DotfileEntry(path=".config/test.conf"),)
        plan = plan_dotfiles(entries)
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "copy"
        assert plan.actions[0].dest_exists is False

    def test_existing_unchanged_file_skipped(self, tmp_path, monkeypatch) -> None:
        from setupvault.utils.hashing import hash_file

        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        target = tmp_path / ".zshrc"
        target.write_text("content")
        actual_hash = hash_file(str(target))
        entries = (
            DotfileEntry(
                path=".zshrc",
                hash=actual_hash,
                size=7,
            ),
        )
        plan = plan_dotfiles(entries)
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "skip_unchanged"

    def test_multiple_entries(self) -> None:
        entries = (
            DotfileEntry(path=".zshrc"),
            DotfileEntry(path=".config/nvim/init.lua"),
            DotfileEntry(path="/absolute/path"),
        )
        plan = plan_dotfiles(entries)
        assert len(plan.actions) == 2
        assert len(plan.rejected) == 1

    def test_empty_entries(self) -> None:
        plan = plan_dotfiles(())
        assert plan.actions == ()
        assert plan.rejected == ()


class TestApplyDotfiles:
    def test_empty_plan_does_nothing(self) -> None:
        errors = apply_dotfiles(plan_dotfiles(()))
        assert errors == []

    def test_backup_and_create(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        target = tmp_path / ".existing"
        target.write_text("old content")

        entries = (DotfileEntry(path=".existing"),)
        plan = plan_dotfiles(entries)
        errors = apply_dotfiles(plan)
        assert errors == []

    def test_path_with_special_chars(self) -> None:
        entries = (DotfileEntry(path=".config/wezterm/wezterm.lua"),)
        plan = plan_dotfiles(entries)
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "copy"

    def test_rollback_dir_created(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        target = tmp_path / ".testfile"
        target.write_text("content")
        entries = (DotfileEntry(path=".testfile"),)
        plan = plan_dotfiles(entries)
        with patch("setupvault.restorers.dotfiles_restorer._create_rollback_dir") as mock_rollback:
            mock_rollback.return_value = tmp_path / "rollbacks" / "test"
            errors = apply_dotfiles(plan)
            assert errors == []
