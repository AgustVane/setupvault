from __future__ import annotations

from dataclasses import dataclass, field

from setupvault.core.exceptions import ProfileError

KNOWN_SECTIONS: frozenset[str] = frozenset({
    "system",
    "environment",
    "shell",
    "packages",
    "themes",
    "fonts",
    "dotfiles",
})


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
                f"Sections {overlap} are both included and excluded "
                f"in profile {self.name!r}."
            )

    def sections(self) -> set[str]:
        """Resolve the effective set of sections for this profile."""
        if self.included_sections:
            base = set(self.included_sections)
        else:
            base = set(KNOWN_SECTIONS)
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
