from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomllib

from setupvault.core.exceptions import ConfigError

DEFAULT_CONFIG_DIR: str = "~/.config/setupvault"
DEFAULT_CONFIG_FILE: str = "config.toml"
DEFAULT_EXPORT_DIR: str = "."
DEFAULT_PROFILE: str = "full"

DEFAULT_DOTFILE_GLOBS: list[str] = [
    ".bashrc",
    ".zshrc",
    ".config/fish/config.fish",
    ".config/hypr/*",
    ".config/waybar/*",
    ".config/gtk-3.0/settings.ini",
    ".config/gtk-4.0/settings.ini",
    ".config/qt5ct/*",
    ".config/qt6ct/*",
    ".config/kitty/*",
    ".config/alacritty/*",
    ".config/neofetch/*",
    ".config/fastfetch/*",
    ".tmux.conf",
    ".config/nvim/*",
    ".config/Code - OSS/User/settings.json",
    ".xinitrc",
    ".xprofile",
]


@dataclass
class SetupVaultConfig:
    """User-facing configuration for SetupVault behaviour.

    Loaded from ``~/.config/setupvault/config.toml``. All fields have
    sensible defaults so the config file is entirely optional.
    """

    export_dir: str = DEFAULT_EXPORT_DIR
    default_profile: str = DEFAULT_PROFILE
    compress_by_default: bool = False
    always_backup: bool = True
    max_rollback_age_days: int = 30

    excluded_sections: list[str] = field(default_factory=list)
    included_sections: list[str] = field(default_factory=list)

    dotfile_globs: list[str] = field(default_factory=lambda: DEFAULT_DOTFILE_GLOBS.copy())

    @classmethod
    def load(cls, path: str | Path | None = None) -> SetupVaultConfig:
        """Load config from a TOML file, falling back to defaults.

        Args:
            path: Explicit path to a TOML config file. If ``None``, the
                  default location ``~/.config/setupvault/config.toml``
                  is tried. If that file does not exist, an empty config
                  (all defaults) is returned.

        Returns:
            A populated ``SetupVaultConfig`` instance.
        """
        if path is None:
            path = Path(os.path.expanduser(DEFAULT_CONFIG_DIR)) / DEFAULT_CONFIG_FILE

        path = Path(path)

        if not path.exists():
            return cls()

        try:
            raw = path.read_bytes()
            data: dict[str, Any] = tomllib.loads(raw.decode("utf-8"))
        except (tomllib.TOMLDecodeError, OSError) as exc:
            raise ConfigError(f"Failed to parse config file {path}: {exc}") from exc

        return cls._from_dict(data, path)

    @classmethod
    def _from_dict(cls, data: dict[str, Any], source: Path) -> SetupVaultConfig:
        """Build a config from a parsed TOML dictionary."""
        _ = source  # reserved for future error reporting
        core = data.get("core", {})

        return cls(
            export_dir=core.get("export_dir", DEFAULT_EXPORT_DIR),
            default_profile=core.get("default_profile", DEFAULT_PROFILE),
            compress_by_default=core.get("compress_by_default", False),
            always_backup=core.get("always_backup", True),
            max_rollback_age_days=core.get("max_rollback_age_days", 30),
            excluded_sections=core.get("excluded_sections", []),
            included_sections=core.get("included_sections", []),
            dotfile_globs=data.get("dotfiles", {}).get("globs", DEFAULT_DOTFILE_GLOBS),
        )

    def dict(self) -> dict[str, Any]:
        """Return config as a plain dict (useful for serialization)."""
        return {
            "export_dir": self.export_dir,
            "default_profile": self.default_profile,
            "compress_by_default": self.compress_by_default,
            "always_backup": self.always_backup,
            "max_rollback_age_days": self.max_rollback_age_days,
            "excluded_sections": list(self.excluded_sections),
            "included_sections": list(self.included_sections),
            "dotfile_globs": list(self.dotfile_globs),
        }
