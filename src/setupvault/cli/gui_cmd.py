from __future__ import annotations

import argparse


def build_gui_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Add the ``gui`` subcommand to the CLI parser."""
    parser = sub.add_parser(
        "gui",
        help="Launch the SetupVault graphical user interface.",
    )
    parser.add_argument(
        "--style",
        choices=["light", "dark", "system"],
        default="system",
        help="Initial UI theme (default: system).",
    )


def run_gui(args: argparse.Namespace) -> int:
    """Launch the GUI. Returns a process exit code."""
    from setupvault.gui.app import launch

    try:
        return launch(style=args.style)  # type: ignore[no-any-return]
    except ImportError as exc:  # pragma: no cover - environment dependent
        print("GUI dependencies are missing. Install with: pip install 'setupvault[gui]'")
        print(f"Details: {exc}")
        return 1
