from __future__ import annotations

import argparse
import sys
from pathlib import Path

from setupvault.services.list_service import list_snapshots


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List available snapshots",
    )
    parser.add_argument(
        "--dir",
        "-d",
        type=str,
        default=None,
        help="Custom snapshot directory (default: XDG snapshots dir)",
    )


def run_list(args: argparse.Namespace) -> int:
    custom_dir = Path(args.dir) if args.dir else None

    result = list_snapshots(custom_dir)

    if result.error:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    if not result.snapshots:
        print(f"No snapshots found in {result.snapshot_dir}")
        return 0

    print(f"Snapshots in {result.snapshot_dir}:")
    print()
    print(f"  {'Name':40s} {'Size':10s} {'Modified':20s}")
    print(f"  {'-' * 40} {'-' * 10} {'-' * 20}")
    for entry in result.snapshots:
        size_str = _format_size(entry.size_bytes)
        mod_str = entry.modified.strftime("%Y-%m-%d %H:%M")
        print(f"  {entry.filename:40s} {size_str:10s} {mod_str:20s}")

    return 0


def _format_size(bytes_: int) -> str:
    if bytes_ < 1024:
        return f"{bytes_}B"
    if bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:.1f}K"
    return f"{bytes_ / (1024 * 1024):.1f}M"
