from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from setupvault.cli.restore_cmd import build_restore_parser, run_restore
from setupvault.core.exceptions import SetupVaultError


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="setupvault")
    sub = p.add_subparsers(dest="command")
    build_restore_parser(sub)
    return p


class TestBuildRestoreParser:
    def test_restore_subcommand_added(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snapshot.json"])
        assert args.command == "restore"

    def test_snapshot_required(self, parser: argparse.ArgumentParser) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["restore"])

    def test_defaults(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json"])
        assert args.snapshot == "snap.json"
        assert args.profile is None
        assert args.dry_run is True
        assert args.assume_yes is False

    def test_profile_option(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json", "--profile", "minimal"])
        assert args.profile == "minimal"

    def test_profile_short(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json", "-p", "packages-only"])
        assert args.profile == "packages-only"

    def test_apply_flag_sets_dry_run_false(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json", "--apply"])
        assert args.dry_run is False

    def test_explicit_dry_run(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json", "--dry-run"])
        assert args.dry_run is True

    def test_yes_flag(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json", "--apply", "--yes"])
        assert args.assume_yes is True

    def test_yes_short(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["restore", "snap.json", "--apply", "-y"])
        assert args.assume_yes is True


class TestRunRestore:
    @patch("setupvault.cli.restore_cmd.RestoreService")
    def test_dry_run_no_changes(self, mock_service_cls: MagicMock) -> None:
        mock_plan = MagicMock()
        mock_plan.has_changes = False
        mock_service = MagicMock()
        mock_service.plan.return_value = mock_plan
        mock_service_cls.return_value = mock_service

        args = MagicMock(snapshot="/tmp/snap.json", profile=None, dry_run=True, assume_yes=False)
        exit_code = run_restore(args)
        assert exit_code == 0

    @patch("setupvault.cli.restore_cmd.RestoreService")
    def test_dry_run_with_changes(self, mock_service_cls: MagicMock) -> None:
        mock_plan = MagicMock()
        mock_plan.has_changes = True
        mock_plan.summary_lines = ["Packages: install 2"]
        mock_plan.warnings = ()
        mock_service = MagicMock()
        mock_service.plan.return_value = mock_plan
        mock_service_cls.return_value = mock_service

        args = MagicMock(snapshot="/tmp/snap.json", profile=None, dry_run=True, assume_yes=False)
        exit_code = run_restore(args)
        assert exit_code == 0

    @patch("setupvault.cli.restore_cmd.RestoreService")
    def test_apply_with_changes(self, mock_service_cls: MagicMock) -> None:
        mock_plan = MagicMock()
        mock_plan.has_changes = True
        mock_plan.summary_lines = ["Packages: install 1"]
        mock_plan.warnings = ()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.errors = ()

        mock_service = MagicMock()
        mock_service.plan.return_value = mock_plan
        mock_service.apply.return_value = mock_result
        mock_service_cls.return_value = mock_service

        args = MagicMock(
            snapshot="/tmp/snap.json",
            profile=None,
            dry_run=False,
            assume_yes=True,
        )
        exit_code = run_restore(args)
        assert exit_code == 0

    @patch("setupvault.cli.restore_cmd.RestoreService")
    def test_apply_with_errors(self, mock_service_cls: MagicMock) -> None:
        mock_plan = MagicMock()
        mock_plan.has_changes = True
        mock_plan.summary_lines = ["Packages: install 1"]
        mock_plan.warnings = ()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = ("Install failed",)

        mock_service = MagicMock()
        mock_service.plan.return_value = mock_plan
        mock_service.apply.return_value = mock_result
        mock_service_cls.return_value = mock_service

        args = MagicMock(
            snapshot="/tmp/snap.json",
            profile=None,
            dry_run=False,
            assume_yes=True,
        )
        exit_code = run_restore(args)
        assert exit_code == 1

    @patch("setupvault.cli.restore_cmd.RestoreService")
    def test_plan_error(self, mock_service_cls: MagicMock) -> None:
        mock_service = MagicMock()
        mock_service.plan.side_effect = SetupVaultError("snapshot not found")
        mock_service_cls.return_value = mock_service

        args = MagicMock(snapshot="/nonexistent.json", profile=None, dry_run=True, assume_yes=False)
        exit_code = run_restore(args)
        assert exit_code == 1
