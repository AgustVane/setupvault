from __future__ import annotations

import argparse
import sys

from setupvault import __version__
from setupvault.cli.diff_cmd import build_parser as build_diff_parser
from setupvault.cli.diff_cmd import run_diff
from setupvault.cli.doctor_cmd import build_parser as build_doctor_parser
from setupvault.cli.doctor_cmd import run_doctor
from setupvault.cli.export_cmd import build_export_parser, run_export
from setupvault.cli.gui_cmd import build_gui_parser, run_gui
from setupvault.cli.info_cmd import build_parser as build_info_parser
from setupvault.cli.info_cmd import run_info
from setupvault.cli.list_cmd import build_parser as build_list_parser
from setupvault.cli.list_cmd import run_list
from setupvault.cli.report_cmd import build_parser as build_report_parser
from setupvault.cli.report_cmd import run_report
from setupvault.cli.restore_cmd import build_restore_parser, run_restore
from setupvault.cli.validate_cmd import build_parser as build_validate_parser
from setupvault.cli.validate_cmd import run_validate

_ROUTER: dict[str, callable] = {
    "export": run_export,
    "restore": run_restore,
    "info": run_info,
    "validate": run_validate,
    "report": run_report,
    "doctor": run_doctor,
    "diff": run_diff,
    "list": run_list,
    "gui": run_gui,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setupvault",
        description="System configuration snapshot tool.",
    )
    parser.add_argument("--version", "-V", action="version", version=f"SetupVault {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    build_export_parser(sub)
    build_restore_parser(sub)
    build_info_parser(sub)
    build_validate_parser(sub)
    build_report_parser(sub)
    build_doctor_parser(sub)
    build_diff_parser(sub)
    build_list_parser(sub)
    build_gui_parser(sub)
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    runner = _ROUTER.get(args.command)
    if runner is not None:
        sys.exit(runner(args))

    parser.print_help()
    sys.exit(1)


def _print_help() -> None:
    print(f"SetupVault v{__version__}")
    print()
    print("Usage: setupvault <command> [options]")
    print()
    print("Commands:")
    print("  export     Export system configuration to a snapshot file")
    print("  restore    Restore system configuration from a snapshot file")
    print("  info       Display information about a snapshot")
    print("  validate   Validate a snapshot file")
    print("  report     Generate a report from a snapshot")
    print("  doctor     Run system diagnostics")
    print("  diff       Compare two snapshots")
    print("  list       List available snapshots")
    print("  version    Print version information")
    print()
    print("Run 'setupvault <command> --help' for more information on a command.")
