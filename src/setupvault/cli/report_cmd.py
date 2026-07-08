from __future__ import annotations

import argparse
import sys
from pathlib import Path

from setupvault.services.report_service import generate_report


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "report",
        help="Generate a report from a snapshot",
    )
    parser.add_argument(
        "snapshot",
        type=str,
        help="Path to the snapshot file",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Write output to file instead of stdout",
    )
    return parser


def run_report(args: argparse.Namespace) -> int:
    path = Path(args.snapshot)
    if not path.exists():
        print(f"Error: snapshot not found: {path}", file=sys.stderr)
        return 1

    try:
        report = generate_report(path, fmt=args.format)
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        return 1

    if args.output:
        out_path = Path(args.output)
        try:
            out_path.write_text(report)
            print(f"Report written to {out_path}")
        except OSError as e:
            print(f"Error writing to {out_path}: {e}", file=sys.stderr)
            return 1
    else:
        print(report)

    return 0
