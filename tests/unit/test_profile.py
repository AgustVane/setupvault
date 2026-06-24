import pytest

from setupvault.core.profile import (
    Profile,
    KNOWN_SECTIONS,
    FULL_PROFILE,
    MINIMAL_PROFILE,
    PACKAGES_ONLY_PROFILE,
    BUILTIN_PROFILES,
)
from setupvault.core.exceptions import ProfileError


class TestProfile:
    def test_full_profile_includes_all_sections(self) -> None:
        sections = FULL_PROFILE.sections()
        assert sections == KNOWN_SECTIONS

    def test_minimal_profile_excludes_optional_sections(self) -> None:
        sections = MINIMAL_PROFILE.sections()
        assert "system" in sections
        assert "packages" in sections
        assert "environment" not in sections
        assert "themes" not in sections

    def test_packages_only_profile(self) -> None:
        sections = PACKAGES_ONLY_PROFILE.sections()
        assert sections == {"system", "packages"}

    def test_custom_included_sections(self) -> None:
        profile = Profile(
            name="themes-only",
            included_sections=("themes", "fonts"),
        )
        assert profile.sections() == {"themes", "fonts"}

    def test_unknown_section_raises(self) -> None:
        with pytest.raises(ProfileError, match="Unknown section"):
            Profile(name="bad", included_sections=("nonsense",))

    def test_overlapping_include_exclude_raises(self) -> None:
        with pytest.raises(ProfileError, match="both included and excluded"):
            Profile(
                name="bad",
                included_sections=("packages",),
                excluded_sections=("packages",),
            )

    def test_builtin_profiles_are_accessible(self) -> None:
        assert "full" in BUILTIN_PROFILES
        assert "minimal" in BUILTIN_PROFILES
        assert "packages-only" in BUILTIN_PROFILES
        assert BUILTIN_PROFILES["full"] is FULL_PROFILE
