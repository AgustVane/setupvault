from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from setupvault.core.exceptions import RestoreError, UnsupportedDistributionError
from setupvault.core.profile import BUILTIN_PROFILES, Profile, load_profile
from setupvault.detectors.distro import detect_distro
from setupvault.distro_adapters.base import DistroAdapter
from setupvault.restorers.dotfiles_restorer import DotfilesPlan, apply_dotfiles, plan_dotfiles
from setupvault.restorers.fonts_restorer import FontsPlan, apply_fonts, plan_fonts
from setupvault.restorers.packages_restorer import PackagesPlan, apply_packages, plan_packages
from setupvault.restorers.themes_restorer import ThemesPlan, apply_themes, plan_themes
from setupvault.storage.local import read_snapshot


@dataclass(frozen=True)
class RestorePlan:
    """Complete restoration plan assembled from a snapshot.

    Each sub-plan corresponds to an optional snapshot section.
    """

    packages: PackagesPlan = field(default_factory=PackagesPlan)
    themes: ThemesPlan = field(default_factory=ThemesPlan)
    fonts: FontsPlan = field(default_factory=FontsPlan)
    dotfiles: DotfilesPlan = field(default_factory=DotfilesPlan)

    warnings: tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        """Whether any section has work to do."""
        return bool(
            self.packages.to_install
            or self.themes.actions
            or self.fonts.copies
            or any(a.action == "copy" for a in self.dotfiles.actions)
        )

    @property
    def summary_lines(self) -> list[str]:
        """Human-readable summary of the plan."""
        lines: list[str] = []
        if self.packages.to_install:
            lines.append(
                f"Packages: install {len(self.packages.to_install)} "
                f"({self.packages.already_present} already present)"
            )
        if self.packages.unknown_names:
            lines.append(f"  ⚠ {len(self.packages.unknown_names)} package names look suspicious")
        if self.themes.actions:
            lines.append(f"Themes: {len(self.themes.actions)} gsettings changes")
        if self.fonts.copies:
            lines.append(f"Fonts: copy {len(self.fonts.copies)} font files")
        dotfile_copies = sum(1 for a in self.dotfiles.actions if a.action == "copy")
        if dotfile_copies:
            lines.append(f"Dotfiles: update {dotfile_copies} files")
        if self.dotfiles.rejected:
            lines.append(f"  ⚠ {len(self.dotfiles.rejected)} dotfiles rejected (unsafe paths)")
        return lines


@dataclass(frozen=True)
class RestoreResult:
    """Outcome of a restore operation."""

    success: bool
    plan: RestorePlan
    errors: tuple[str, ...] = ()


class RestoreService:
    """Orchestrates snapshot restoration.

    Usage::

        service = RestoreService()
        plan = service.plan(snapshot_path)
        result = service.apply(plan, assume_yes=True)
    """

    def plan(
        self,
        snapshot_path: str | Path,
        profile_name: str | None = None,
    ) -> RestorePlan:
        """Read a snapshot and build a restoration plan (no system changes).

        Args:
            snapshot_path: Path to the snapshot JSON file.
            profile_name: Profile to use (default ``"full"``).

        Returns:
            A ``RestorePlan`` describing what would be done.
        """
        snapshot = read_snapshot(snapshot_path)
        adapter = self._detect_adapter()
        profile = self._resolve_profile(profile_name)
        sections = profile.sections()

        warnings: list[str] = []

        packages = (
            plan_packages(snapshot.packages, adapter) if "packages" in sections else PackagesPlan()
        )

        themes = plan_themes(snapshot.themes) if "themes" in sections else ThemesPlan()

        fonts = plan_fonts(snapshot.fonts) if "fonts" in sections else FontsPlan()

        dotfiles = plan_dotfiles(snapshot.dotfiles) if "dotfiles" in sections else DotfilesPlan()

        for pkg_warning in packages.warnings:
            warnings.append(pkg_warning)
        for theme_warning in themes.warnings:
            warnings.append(theme_warning)
        for font_warning in fonts.warnings:
            warnings.append(font_warning)
        for dotfile_warning in dotfiles.warnings:
            warnings.append(dotfile_warning)

        return RestorePlan(
            packages=packages,
            themes=themes,
            fonts=fonts,
            dotfiles=dotfiles,
            warnings=tuple(warnings),
        )

    def apply(
        self,
        plan: RestorePlan,
        *,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> RestoreResult:
        """Execute a restoration plan.

        Args:
            plan: The plan to execute.
            dry_run: If ``True``, simulate without making changes.
            assume_yes: If ``True``, skip confirmation prompts.

        Returns:
            A ``RestoreResult`` summarising the outcome.
        """
        errors: list[str] = []

        adapter = self._detect_adapter()

        if plan.packages.to_install:
            result = apply_packages(
                plan.packages,
                adapter,
                dry_run=dry_run,
                assume_yes=assume_yes,
            )
            if not result.success:
                errors.extend(result.errors)

        if plan.themes.actions:
            theme_errors = apply_themes(plan.themes)
            errors.extend(theme_errors)

        if plan.fonts.copies:
            font_errors = apply_fonts(plan.fonts)
            errors.extend(font_errors)

        if any(a.action == "copy" for a in plan.dotfiles.actions):
            dotfile_errors = apply_dotfiles(plan.dotfiles, rollback=True)
            errors.extend(dotfile_errors)

        return RestoreResult(
            success=not errors,
            plan=plan,
            errors=tuple(errors),
        )

    def _detect_adapter(self) -> DistroAdapter:
        try:
            detection = detect_distro()
        except UnsupportedDistributionError:
            raise
        except Exception as exc:
            raise UnsupportedDistributionError(f"Could not detect distribution: {exc}") from exc
        return detection.adapter

    def _resolve_profile(self, name: str | None) -> Profile:
        name = name or "full"
        profile = BUILTIN_PROFILES.get(name)
        if profile is not None:
            return profile
        custom = load_profile(name)
        if custom is not None:
            return custom
        builtin_list = list(BUILTIN_PROFILES)
        raise RestoreError(
            f"Unknown profile: {name!r}. Available: {builtin_list} (plus custom TOML profiles)",
        )
