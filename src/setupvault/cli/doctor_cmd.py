from __future__ import annotations

import argparse

from setupvault.services.doctor_service import diagnose


def build_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "doctor",
        help="Run system diagnostics",
    )
    parser.add_argument(
        "checks",
        type=str,
        nargs="*",
        help="Specific checks to run (default: all)",
    )


def run_doctor(args: argparse.Namespace) -> int:
    check_names = args.checks if args.checks else None
    report = diagnose(check_names)

    print(f"Doctor Report ({report.timestamp})")
    print(f"All passed: {'yes' if report.all_passed else 'no'}")
    print()

    if report.passed:
        print("PASSED:")
        for name, _, msg in report.passed:
            print(f"  ✓ {name}: {msg}")

    if report.failed:
        print("\nFAILED:")
        for name, _, msg in report.failed:
            print(f"  ✗ {name}: {msg}")

    return 0 if report.all_passed else 1
