from __future__ import annotations

import argparse
import sys
from pathlib import Path

from setupvault.reports.markdown import render_markdown
from setupvault.storage.local import read_snapshot


def build_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "info",
        help="Display snapshot information",
    )
    parser.add_argument(
        "snapshot",
        type=str,
        help="Path to the snapshot file",
    )
    return parser


def run_info(args: argparse.Namespace) -> int:
    path = Path(args.snapshot)
    if not path.exists():
        print(f"Error: snapshot not found: {path}", file=sys.stderr)
        return 1

    try:
        snapshot = read_snapshot(path)
        print(render_markdown(snapshot))
    except Exception as e:
        print(f"Error reading snapshot: {e}", file=sys.stderr)
        return 1

    return 0
