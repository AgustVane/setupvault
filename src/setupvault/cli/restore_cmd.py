from __future__ import annotations

import argparse
import sys

from setupvault.core.exceptions import SetupVaultError
from setupvault.services.restore_service import RestoreService


def build_restore_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Add the ``restore`` subcommand parser."""
    parser = subparsers.add_parser(
        "restore",
        help="Restore system configuration from a snapshot file",
        description=(
            "Read a snapshot file, build a restoration plan, and optionally "
            "apply it. Dry-run is the default — use --apply to execute."
        ),
    )
    parser.add_argument(
        "snapshot",
        type=str,
        help="Path to the snapshot JSON file",
    )
    parser.add_argument(
        "--profile",
        "-p",
        default=None,
        choices=("full", "minimal", "packages-only"),
        help="Profile to restore (default: full)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        dest="dry_run",
        help="Show what would be done without making changes (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_false",
        dest="dry_run",
        help="Actually execute the restoration",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        default=False,
        dest="assume_yes",
        help="Skip confirmation prompts",
    )


def run_restore(args: argparse.Namespace) -> int:
    """Execute the ``restore`` subcommand.

    Returns:
        Exit code (0 on success, 1 on failure).
    """
    service = RestoreService()

    if args.dry_run:
        try:
            plan = service.plan(snapshot_path=args.snapshot, profile_name=args.profile)
        except SetupVaultError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        print(f"Snapshot: {args.snapshot}")
        print(f"Profile:  {args.profile or 'full'}")
        print()

        if not plan.has_changes:
            print("No changes needed — system already matches snapshot.")
            return 0

        for line in plan.summary_lines:
            print(f"  {line}")
        print()

        if plan.warnings:
            for w in plan.warnings:
                print(f"  ⚠ {w}")
            print()

        print("Run with --apply to execute this plan.")
        return 0

    try:
        plan = service.plan(snapshot_path=args.snapshot, profile_name=args.profile)
    except SetupVaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not plan.has_changes:
        print("No changes needed — system already matches snapshot.")
        return 0

    print("The following changes will be made:")
    for line in plan.summary_lines:
        print(f"  {line}")
    print()

    if plan.warnings:
        for w in plan.warnings:
            print(f"  ⚠ {w}")
        print()

    if not args.assume_yes:
        try:
            response = input("Proceed with restore? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 1
        if response not in ("y", "yes"):
            print("Cancelled.")
            return 1

    try:
        result = service.apply(plan, dry_run=False, assume_yes=args.assume_yes)
    except SetupVaultError as exc:
        print(f"Error during restore: {exc}", file=sys.stderr)
        return 1

    if result.success:
        print("Restore completed successfully.")
        return 0

    print("Restore completed with errors:", file=sys.stderr)
    for err in result.errors:
        print(f"  ✗ {err}", file=sys.stderr)
    return 1
