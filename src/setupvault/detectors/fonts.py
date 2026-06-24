from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from setupvault.utils.shell import SafeCommandRunner


@dataclass(frozen=True)
class FontEntry:
    """A single detected font."""

    family: str
    style: str | None = None
    path: str | None = None


@dataclass(frozen=True)
class FontConfig:
    """Font rendering configuration."""

    freetype_preset: str | None = None
    hinting: str | None = None
    antialiasing: bool | None = None


@dataclass(frozen=True)
class FontDetection:
    """Result of font detection."""

    system_fonts: tuple[FontEntry, ...] = ()
    user_fonts: tuple[FontEntry, ...] = ()
    config: FontConfig | None = None


_RUNNER = SafeCommandRunner(timeout=5.0)


def detect_fonts() -> FontDetection:
    """Detect system and user fonts, plus font rendering configuration.

    Returns:
        A ``FontDetection`` with whatever could be determined.
    """
    system = _detect_system_fonts()
    user = _detect_user_fonts()
    config = _detect_font_config()

    return FontDetection(
        system_fonts=system,
        user_fonts=user,
        config=config,
    )


def _detect_system_fonts() -> tuple[FontEntry, ...]:
    """Detect system-installed fonts via ``fc-list``."""
    if not _RUNNER.check_tool("fc-list"):
        return ()

    result = _RUNNER.run(
        ["fc-list", "--format=%{family}\t%{style}\t%{file}\n"],
        check=False,
        timeout=5.0,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return ()

    entries: list[FontEntry] = []
    seen: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 1:
            continue
        family = parts[0].strip()
        if not family or family in seen:
            continue
        seen.add(family)
        style = parts[1].strip() if len(parts) > 1 else None
        path = parts[2].strip() if len(parts) > 2 else None
        entries.append(FontEntry(family=family, style=style, path=path))

    return tuple(entries)


def _detect_user_fonts() -> tuple[FontEntry, ...]:
    """Detect user-installed fonts in ``~/.local/share/fonts/`` and ``~/.fonts/``."""
    home = Path.home()
    font_dirs = [
        home / ".local" / "share" / "fonts",
        home / ".fonts",
    ]

    entries: list[FontEntry] = []
    for font_dir in font_dirs:
        if not font_dir.exists():
            continue
        for font_file in font_dir.rglob("*"):
            if not font_file.is_file():
                continue
            if font_file.suffix.lower() not in (".ttf", ".otf", ".woff", ".woff2"):
                continue
            family = font_file.stem
            rel_path = str(font_file.relative_to(home))
            entries.append(FontEntry(family=family, path=rel_path))

    return tuple(entries)


def _detect_font_config() -> FontConfig | None:
    """Detect font rendering configuration."""
    freetype_preset: str | None = None
    hinting: str | None = None
    antialiasing: bool | None = None

    # Check fontconfig config files
    fontconfig_paths = [
        Path("/etc/fonts/local.conf"),
        Path.home() / ".config" / "fontconfig" / "fonts.conf",
    ]

    for config_path in fontconfig_paths:
        if not config_path.exists():
            continue
        try:
            content = config_path.read_text()
            if "preset" in content and freetype_preset is None:
                if "lcd" in content:
                    freetype_preset = "lcd"
                elif "light" in content:
                    freetype_preset = "light"
            if "hinting" in content:
                if "hintfull" in content or "full" in content:
                    hinting = "full"
                elif "hintmedium" in content or "medium" in content:
                    hinting = "medium"
                elif "hintslight" in content or "slight" in content:
                    hinting = "slight"
                elif "hintnone" in content or "none" in content:
                    hinting = "none"
            if "antialias" in content:
                antialiasing = "true" in content or "yes" in content
        except (OSError, UnicodeDecodeError):
            continue

    if any((freetype_preset, hinting, antialiasing is not None)):
        return FontConfig(
            freetype_preset=freetype_preset,
            hinting=hinting,
            antialiasing=antialiasing,
        )
    return None
