from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from setupvault.core.snapshot import Snapshot


def render_json(snapshot: Snapshot, pretty: bool = True) -> str:
    """Render a snapshot as a JSON report.

    Args:
        snapshot: The snapshot to render.
        pretty: Whether to pretty-print the output.

    Returns:
        A JSON string.
    """
    data = _snapshot_to_report(snapshot)
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, default=str)


def _snapshot_to_report(snapshot: Snapshot) -> dict[str, Any]:
    result: dict[str, Any] = {
        "report_generated": datetime.now(timezone.utc).isoformat(),
        "snapshot_version": snapshot.snapshot_version,
        "tool_version": snapshot.tool_version,
        "created_at": snapshot.created_at,
        "profile": snapshot.profile,
        "notes": snapshot.notes,
        "system": {
            "distribution": {
                "id": snapshot.system.distribution.id,
                "name": snapshot.system.distribution.name,
                "version": snapshot.system.distribution.version,
                "version_id": snapshot.system.distribution.version_id,
                "id_like": list(snapshot.system.distribution.id_like),
            },
            "kernel": {
                "release": snapshot.system.kernel.release,
                "version": snapshot.system.kernel.version,
            },
            "architecture": snapshot.system.architecture,
            "hostname": snapshot.system.hostname,
            "uptime_seconds": snapshot.system.uptime_seconds,
        },
        "packages": {
            "count": {
                "official": snapshot.packages.counts.official,
                "aur": snapshot.packages.counts.aur,
                "third_party": snapshot.packages.counts.third_party,
                "flatpak": snapshot.packages.counts.flatpak,
                "snap": snapshot.packages.counts.snap,
                "total": snapshot.packages.counts.total,
            },
            "official": [
                {"name": p.name, "version": p.version} for p in snapshot.packages.official
            ],
            "aur": [{"name": p.name, "version": p.version} for p in snapshot.packages.aur],
            "third_party": [
                {"name": p.name, "version": p.version} for p in snapshot.packages.third_party
            ],
        },
        "dotfiles": [{"path": df.path, "hash": df.hash} for df in snapshot.dotfiles],
    }

    if snapshot.themes:
        t = snapshot.themes
        themes_dict: dict[str, Any] = {}
        if t.gtk:
            themes_dict["gtk"] = {
                "theme": t.gtk.theme,
                "icon_theme": t.gtk.icon_theme,
                "cursor_theme": t.gtk.cursor_theme,
                "font_name": t.gtk.font_name,
                "color_scheme": t.gtk.color_scheme,
            }
        if t.qt:
            themes_dict["qt"] = {
                "theme": t.qt.theme,
                "icon_theme": t.qt.icon_theme,
                "font_name": t.qt.font_name,
            }
        result["themes"] = themes_dict
    else:
        result["themes"] = None

    if snapshot.fonts:
        f = snapshot.fonts
        fonts_dict: dict[str, Any] = {
            "system_fonts": [
                {"family": fe.family, "style": fe.style, "path": fe.path} for fe in f.system_fonts
            ],
            "user_fonts": [
                {"family": fe.family, "style": fe.style, "path": fe.path} for fe in f.user_fonts
            ],
        }
        if f.config:
            fonts_dict["config"] = {
                "freetype_preset": f.config.freetype_preset,
                "hinting": f.config.hinting,
                "antialiasing": f.config.antialiasing,
            }
        result["fonts"] = fonts_dict
    else:
        result["fonts"] = None

    return result
