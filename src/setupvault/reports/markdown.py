from __future__ import annotations

from setupvault.core.snapshot import Snapshot


def render_markdown(snapshot: Snapshot) -> str:
    """Render a snapshot as a human-readable Markdown report.

    Args:
        snapshot: The snapshot to render.

    Returns:
        A Markdown string.
    """
    lines: list[str] = []
    lines.append("# SetupVault Snapshot Report")
    lines.append("")
    lines.append(f"**Created:** {snapshot.created_at}")
    lines.append(f"**Tool version:** {snapshot.tool_version}")
    lines.append(f"**Profile:** {snapshot.profile or 'default'}")
    lines.append(f"**Notes:** {snapshot.notes or '—'}")
    lines.append("")

    _render_system(lines, snapshot)
    _render_packages(lines, snapshot)
    _render_themes(lines, snapshot)
    _render_fonts(lines, snapshot)
    _render_dotfiles(lines, snapshot)

    return "\n".join(lines)


def _render_system(lines: list[str], snapshot: Snapshot) -> None:
    sys_info = snapshot.system
    lines.append("## System")
    lines.append("")
    dist_str = f"{sys_info.distribution.name} {sys_info.distribution.version}"
    lines.append(f"- **Distribution:** {dist_str}")
    lines.append(f"- **Kernel:** {sys_info.kernel.release}")
    lines.append(f"- **Architecture:** {sys_info.architecture}")
    lines.append(f"- **Hostname:** {sys_info.hostname}")
    if sys_info.uptime_seconds is not None:
        hours = sys_info.uptime_seconds // 3600
        minutes = (sys_info.uptime_seconds % 3600) // 60
        lines.append(f"- **Uptime:** {hours}h {minutes}m")
    lines.append("")


def _render_packages(lines: list[str], snapshot: Snapshot) -> None:
    pkg = snapshot.packages
    lines.append("## Packages")
    lines.append("")
    c = pkg.counts
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    if c.official:
        lines.append(f"| Official | {c.official} |")
    if c.aur:
        lines.append(f"| AUR | {c.aur} |")
    if c.third_party:
        lines.append(f"| Third-party | {c.third_party} |")
    if c.flatpak:
        lines.append(f"| Flatpak | {c.flatpak} |")
    if c.snap:
        lines.append(f"| Snap | {c.snap} |")
    lines.append(f"| **Total** | **{c.total}** |")
    lines.append("")

    for section_name, section_list in [
        ("Official", pkg.official),
        ("AUR", pkg.aur),
        ("Third-party", pkg.third_party),
    ]:
        if section_list:
            lines.append(f"### {section_name}")
            lines.append("")
            for p in section_list:
                lines.append(f"- `{p.name}` {p.version}")
            lines.append("")


def _render_themes(lines: list[str], snapshot: Snapshot) -> None:
    theme = snapshot.themes
    if not theme:
        return
    lines.append("## Themes")
    lines.append("")
    if theme.gtk:
        g = theme.gtk
        if g.theme:
            lines.append(f"- **GTK Theme:** `{g.theme}`")
        if g.icon_theme:
            lines.append(f"- **GTK Icons:** `{g.icon_theme}`")
        if g.font_name:
            lines.append(f"- **GTK Font:** `{g.font_name}`")
        if g.color_scheme:
            lines.append(f"- **Color Scheme:** `{g.color_scheme}`")
    if theme.qt:
        q = theme.qt
        if q.theme:
            lines.append(f"- **Qt Theme:** `{q.theme}`")
        if q.icon_theme:
            lines.append(f"- **Qt Icons:** `{q.icon_theme}`")
        if q.font_name:
            lines.append(f"- **Qt Font:** `{q.font_name}`")
    lines.append("")


def _render_fonts(lines: list[str], snapshot: Snapshot) -> None:
    font_info = snapshot.fonts
    if not font_info:
        return
    lines.append("## Fonts")
    lines.append("")

    if font_info.user_fonts:
        lines.append(f"**User fonts ({len(font_info.user_fonts)}):**")
        for f in font_info.user_fonts:
            style_str = f" ({f.style})" if f.style else ""
            lines.append(f"- {f.family}{style_str}")

    if font_info.system_fonts:
        lines.append(f"\n**System fonts ({len(font_info.system_fonts)}):**")

    if font_info.config:
        cfg = font_info.config
        parts: list[str] = []
        if cfg.hinting is not None:
            parts.append(f"hinting={cfg.hinting}")
        if cfg.antialiasing is not None:
            parts.append(f"antialiasing={cfg.antialiasing}")
        if cfg.freetype_preset is not None:
            parts.append(f"freetype_preset={cfg.freetype_preset}")
        if parts:
            lines.append(f"\n**Rendering:** {', '.join(parts)}")

    lines.append("")


def _render_dotfiles(lines: list[str], snapshot: Snapshot) -> None:
    if not snapshot.dotfiles:
        return
    lines.append("## Dotfiles")
    lines.append("")
    lines.append("| Path | Hash |")
    lines.append("|------|------|")
    for df in snapshot.dotfiles:
        lines.append(f"| `{df.path}` | `{df.hash[:16]}…` |")
    lines.append("")
