from __future__ import annotations

import argparse
import sys
from pathlib import Path

from setupvault.services.diff_service import diff_snapshots


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "diff",
        help="Compare two snapshots",
    )
    parser.add_argument(
        "left",
        type=str,
        help="First snapshot file",
    )
    parser.add_argument(
        "right",
        type=str,
        help="Second snapshot file",
    )


def run_diff(args: argparse.Namespace) -> int:
    left = Path(args.left)
    right = Path(args.right)

    errors: list[str] = []
    if not left.exists():
        errors.append(f"Left snapshot not found: {left}")
    if not right.exists():
        errors.append(f"Right snapshot not found: {right}")
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        result = diff_snapshots(left, right)
    except Exception as e:
        print(f"Error comparing snapshots: {e}", file=sys.stderr)
        return 1

    if result.same:
        print("Snapshots are identical.")
        return 0

    print(f"Sections changed: {', '.join(result.sections_changed)}")
    for section, details in result.details.items():
        print(f"\n  {section}:")
        for d in details:
            print(f"    • {d}")

    return 0
