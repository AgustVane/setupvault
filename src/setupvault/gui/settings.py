from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from setupvault.core.config import DEFAULT_CONFIG_DIR


@dataclass
class GuiSettings:
    """Persistent GUI preferences.

    Stored as JSON in the SetupVault config directory so the CLI config
    (TOML) stays focused on behaviour, not presentation.
    """

    theme: str = "system"  # "light", "dark", or "system"
    accent: str = ""  # empty = theme default
    density: str = "comfortable"  # "comfortable" or "compact"
    default_profile: str = "full"
    default_report_format: str = "markdown"
    window_geometry: str = ""
    window_state: str = ""

    def save(self, path: Path | None = None) -> None:
        target = path or self._default_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | None = None) -> GuiSettings:
        target = path or cls._default_path()
        if not target.exists():
            return cls()
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**known)
        except (json.JSONDecodeError, OSError, TypeError):
            return cls()

    @staticmethod
    def _default_path() -> Path:
        return Path(DEFAULT_CONFIG_DIR).expanduser() / "gui_settings.json"
