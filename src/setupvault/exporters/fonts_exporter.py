from __future__ import annotations

from setupvault.core.snapshot import FontConfig, FontEntry, FontInfo
from setupvault.detectors.fonts import FontDetection


def export_fonts(detection: FontDetection) -> FontInfo | None:
    """Transform font detection data into a snapshot ``FontInfo``.

    Returns ``None`` if no font data was detected.
    """
    system = tuple(
        FontEntry(family=f.family, style=f.style, path=f.path) for f in detection.system_fonts
    )

    user = tuple(FontEntry(family=f.family, path=f.path) for f in detection.user_fonts)

    config: FontConfig | None = None
    if detection.config is not None:
        config = FontConfig(
            freetype_preset=detection.config.freetype_preset,
            hinting=detection.config.hinting,
            antialiasing=detection.config.antialiasing,
        )

    if not system and not user and config is None:
        return None

    return FontInfo(system_fonts=system, user_fonts=user, config=config)
