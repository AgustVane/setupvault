from __future__ import annotations

from typing import Any


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return *singular* or *plural* form based on *count*."""
    if count == 1:
        return singular
    return plural if plural else f"{singular}s"


def human_size(bytes_: int) -> str:
    """Format a byte count as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(bytes_) < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} PB"


def human_duration(seconds: int) -> str:
    """Format a duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m {seconds % 60}s"
    hours = minutes // 60
    return f"{hours}h {minutes % 60}m {seconds % 60}s"


def key_value_table(items: list[tuple[str, str]], title: str | None = None) -> str:
    """Format a list of key-value pairs as a simple aligned table.

    This is a plain-text fallback. The CLI uses Rich tables when available.
    """
    if not items:
        return ""
    key_width = max(len(k) for k, _ in items)
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))
    for key, value in items:
        lines.append(f"  {key:<{key_width}}  {value}")
    return "\n".join(lines)


def truncate(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate *text* to *max_length* characters."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
