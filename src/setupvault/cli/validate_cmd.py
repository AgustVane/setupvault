from __future__ import annotations

import argparse
import sys
from pathlib import Path

from setupvault.services.validate_service import validate_snapshot


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "validate",
        help="Validate a snapshot file",
    )
    parser.add_argument(
        "snapshot",
        type=str,
        help="Path to the snapshot file",
    )


def run_validate(args: argparse.Namespace) -> int:
    path = Path(args.snapshot)
    if not path.exists():
        print(f"Error: snapshot not found: {path}", file=sys.stderr)
        return 1

    report = validate_snapshot(path)

    if report.valid:
        print(f"✓ {path.name} is valid")

    if report.schema_errors:
        print(f"\nSchema errors ({len(report.schema_errors)}):", file=sys.stderr)
        for err in report.schema_errors:
            print(f"  ✗ {err}", file=sys.stderr)

    if report.semantic_errors:
        print(f"\nSemantic errors ({len(report.semantic_errors)}):", file=sys.stderr)
        for err in report.semantic_errors:
            print(f"  ✗ {err}", file=sys.stderr)

    if report.warnings:
        print(f"\nWarnings ({len(report.warnings)}):")
        for w in report.warnings:
            print(f"  ⚠ {w}")

    return 0 if report.valid else 1
