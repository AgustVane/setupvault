from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tomllib

from setupvault.core.exceptions import ProfileError

USER_PROFILES_DIR: str = "~/.config/setupvault/profiles"

KNOWN_SECTIONS: frozenset[str] = frozenset(
    {
        "system",
        "environment",
        "shell",
        "packages",
        "themes",
        "fonts",
        "dotfiles",
    }
)


@dataclass(frozen=True)
class Profile:
    """A named profile defining which sections to export or restore.

    If *included_sections* is empty, all known sections are included
    (minus those in *excluded_sections*).
    """

    name: str
    description: str = ""
    included_sections: tuple[str, ...] = ()
    excluded_sections: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        for sec in self.included_sections:
            if sec not in KNOWN_SECTIONS:
                raise ProfileError(
                    f"Unknown section {sec!r} in profile {self.name!r}. "
                    f"Known sections: {sorted(KNOWN_SECTIONS)}"
                )
        for sec in self.excluded_sections:
            if sec not in KNOWN_SECTIONS:
                raise ProfileError(
                    f"Unknown section {sec!r} in profile {self.name!r}. "
                    f"Known sections: {sorted(KNOWN_SECTIONS)}"
                )
        overlap = set(self.included_sections) & set(self.excluded_sections)
        if overlap:
            raise ProfileError(
                f"Sections {overlap} are both included and excluded in profile {self.name!r}."
            )

    def sections(self) -> set[str]:
        """Resolve the effective set of sections for this profile."""
        base = set(self.included_sections) if self.included_sections else set(KNOWN_SECTIONS)
        return base - set(self.excluded_sections)


# Built-in profiles
FULL_PROFILE = Profile(
    name="full",
    description="All sections (default)",
)

MINIMAL_PROFILE = Profile(
    name="minimal",
    description="System info and packages only",
    excluded_sections=("environment", "shell", "themes", "fonts", "dotfiles"),
)

PACKAGES_ONLY_PROFILE = Profile(
    name="packages-only",
    description="Package lists only",
    included_sections=("system", "packages"),
)

BUILTIN_PROFILES: dict[str, Profile] = {
    "full": FULL_PROFILE,
    "minimal": MINIMAL_PROFILE,
    "packages-only": PACKAGES_ONLY_PROFILE,
}


def _profiles_dir() -> Path:
    return Path(USER_PROFILES_DIR).expanduser()


def load_profile(name: str) -> Profile | None:
    """Load a user-defined profile from a TOML file.

    Args:
        name: Profile name (file name without ``.toml`` suffix).

    Returns:
        A ``Profile`` instance, or ``None`` if no matching file exists.
    """
    path = _profiles_dir() / f"{name}.toml"
    if not path.exists():
        return None

    try:
        raw = path.read_bytes()
        data: dict[str, Any] = tomllib.loads(raw.decode("utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return None

    included = tuple(data.get("included_sections", []))
    excluded = tuple(data.get("excluded_sections", []))
    return Profile(
        name=name,
        description=data.get("description", ""),
        included_sections=included,
        excluded_sections=excluded,
    )


def load_all_custom_profiles() -> dict[str, Profile]:
    """Load all user-defined profiles from the profiles directory.

    Returns:
        A mapping of profile name to ``Profile``.
    """
    profiles: dict[str, Profile] = {}
    pdir = _profiles_dir()
    if not pdir.exists():
        return profiles

    for fpath in pdir.iterdir():
        if fpath.is_file() and fpath.suffix == ".toml":
            name = fpath.stem
            profile = load_profile(name)
            if profile is not None:
                profiles[name] = profile

    return profiles
