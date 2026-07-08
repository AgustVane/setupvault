from __future__ import annotations

import argparse
import sys

from setupvault.core.exceptions import SetupVaultError
from setupvault.services.export_service import ExportService


def build_export_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add the ``export`` subcommand parser to an argparse subparsers group."""
    parser = subparsers.add_parser(
        "export",
        help="Export a snapshot of the current system configuration",
        description=(
            "Detect system, packages, themes, fonts, dotfiles and write a portable snapshot."
        ),
    )
    parser.add_argument(
        "--profile",
        "-p",
        default=None,
        choices=("full", "minimal", "packages-only"),
        help="Export profile (default: full)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        type=str,
        help="Output file path (auto-generated if omitted)",
    )
    parser.add_argument(
        "--compress",
        "-c",
        action="store_true",
        help="Gzip-compress the output snapshot",
    )
    parser.add_argument(
        "--exclude",
        "-x",
        action="append",
        default=[],
        dest="exclude_sections",
        help="Exclude a section (system, packages, themes, fonts, dotfiles, shell, environment). "
        "May be specified multiple times.",
    )


def run_export(args: argparse.Namespace) -> int:
    """Execute the ``export`` subcommand.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    service = ExportService()
    try:
        report = service.execute(
            profile_name=args.profile,
            output_path=args.output,
            compress=args.compress,
            exclude_sections=args.exclude_sections,
        )
    except SetupVaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Snapshot written to: {report.path}")
    print(f"Profile:            {report.snapshot.profile or 'default'}")
    print(
        f"System:             {report.snapshot.system.distribution.name} "
        f"{report.snapshot.system.distribution.version}"
    )
    print(f"Packages:           {report.snapshot.packages.counts.total} total")
    if report.snapshot.themes:
        print("Themes:             captured")
    if report.snapshot.fonts:
        print("Fonts:              captured")
    if report.snapshot.dotfiles:
        print(f"Dotfiles:           {len(report.snapshot.dotfiles)} files")
    print(f"Duration:           {report.duration_seconds:.2f}s")
    return 0
