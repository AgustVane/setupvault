from __future__ import annotations

from pathlib import Path

from setupvault.reports.html_report import render_html
from setupvault.reports.json_report import render_json
from setupvault.reports.markdown import render_markdown
from setupvault.storage.local import read_snapshot


def generate_report(path: Path, fmt: str = "markdown") -> str:
    """Generate a report from a snapshot file.

    Args:
        path: Path to the snapshot JSON file.
        fmt: Output format — "markdown", "json", or "html".

    Returns:
        The rendered report string.
    """
    snapshot = read_snapshot(path)

    if fmt == "json":
        return render_json(snapshot)
    if fmt == "html":
        return render_html(snapshot)
    return render_markdown(snapshot)
