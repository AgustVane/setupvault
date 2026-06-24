from __future__ import annotations

import sys

from setupvault import __version__


def main() -> None:
    """Entry point for the SetupVault CLI.

    This is a stub that will be expanded with Typer/Click commands.
    """
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h"):
        _print_help()
        return

    if args[0] in ("--version", "-V", "version"):
        print(f"SetupVault {__version__}")
        return

    print(f"Unknown command: {args[0]}")
    print("Run 'setupvault --help' for usage.")
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
