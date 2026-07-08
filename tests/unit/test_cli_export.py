from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from setupvault.cli.export_cmd import build_export_parser, run_export
from setupvault.core.exceptions import SetupVaultError


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="setupvault")
    sub = p.add_subparsers(dest="command")
    build_export_parser(sub)
    return p


class TestBuildExportParser:
    def test_export_subcommand_added(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export"])
        assert args.command == "export"

    def test_defaults(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export"])
        assert args.profile is None
        assert args.output is None
        assert args.compress is False
        assert args.exclude_sections == []

    def test_profile_option(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "--profile", "minimal"])
        assert args.profile == "minimal"

    def test_profile_short(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "-p", "packages-only"])
        assert args.profile == "packages-only"

    def test_invalid_profile_rejected(self, parser: argparse.ArgumentParser) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["export", "--profile", "invalid"])

    def test_output_option(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "--output", "/tmp/snap.json"])
        assert args.output == "/tmp/snap.json"

    def test_output_short(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "-o", "snap.json"])
        assert args.output == "snap.json"

    def test_compress_flag(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "--compress"])
        assert args.compress is True

    def test_compress_short(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "-c"])
        assert args.compress is True

    def test_single_exclude(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "--exclude", "themes"])
        assert args.exclude_sections == ["themes"]

    def test_multi_exclude(self, parser: argparse.ArgumentParser) -> None:
        args = parser.parse_args(["export", "-x", "themes", "-x", "fonts"])
        assert args.exclude_sections == ["themes", "fonts"]


class TestRunExport:
    @patch("setupvault.cli.export_cmd.ExportService")
    def test_successful_export(self, mock_service_cls: MagicMock) -> None:
        mock_report = MagicMock()
        mock_report.path = "/tmp/snap.json"
        mock_report.snapshot.profile = "full"
        mock_report.snapshot.system.distribution.name = "Arch Linux"
        mock_report.snapshot.system.distribution.version = "rolling"
        mock_report.snapshot.packages.counts.total = 1550
        mock_report.snapshot.themes = MagicMock()
        mock_report.snapshot.fonts = MagicMock()
        mock_report.snapshot.dotfiles = (MagicMock(), MagicMock())
        mock_report.duration_seconds = 1.23

        mock_service = MagicMock()
        mock_service.execute.return_value = mock_report
        mock_service_cls.return_value = mock_service

        args = argparse.Namespace(
            profile="full",
            output="/tmp/snap.json",
            compress=False,
            exclude_sections=[],
        )
        exit_code = run_export(args)
        assert exit_code == 0

    @patch("setupvault.cli.export_cmd.ExportService")
    def test_export_with_setupvault_error(self, mock_service_cls: MagicMock) -> None:
        mock_service = MagicMock()
        mock_service.execute.side_effect = SetupVaultError("something went wrong")
        mock_service_cls.return_value = mock_service

        args = argparse.Namespace(
            profile="full",
            output=None,
            compress=False,
            exclude_sections=[],
        )
        exit_code = run_export(args)
        assert exit_code == 1

    @patch("setupvault.cli.export_cmd.ExportService")
    def test_exclude_sections_passed_through(self, mock_service_cls: MagicMock) -> None:
        mock_report = MagicMock()
        mock_report.path = "/tmp/snap.json"
        mock_report.snapshot.profile = "full"
        mock_report.snapshot.system.distribution.name = "X"
        mock_report.snapshot.system.distribution.version = "1"
        mock_report.snapshot.packages.counts.total = 0
        mock_report.snapshot.themes = None
        mock_report.snapshot.fonts = None
        mock_report.snapshot.dotfiles = ()
        mock_report.duration_seconds = 0.5

        mock_service = MagicMock()
        mock_service.execute.return_value = mock_report
        mock_service_cls.return_value = mock_service

        args = argparse.Namespace(
            profile=None,
            output=None,
            compress=False,
            exclude_sections=["themes", "fonts"],
        )
        exit_code = run_export(args)
        assert exit_code == 0

        mock_service.execute.assert_called_once_with(
            profile_name=None,
            output_path=None,
            compress=False,
            exclude_sections=["themes", "fonts"],
        )
