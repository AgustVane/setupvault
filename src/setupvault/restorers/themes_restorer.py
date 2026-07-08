from __future__ import annotations

from dataclasses import dataclass

from setupvault.core.snapshot import ThemeInfo


@dataclass(frozen=True)
class ThemePlanAction:
    """A single gsettings or config command to apply a theme setting."""

    command: str
    args: tuple[str, ...] = ()
    value: str | None = None


@dataclass(frozen=True)
class ThemesPlan:
    """Restoration plan for the themes section."""

    actions: tuple[ThemePlanAction, ...] = ()
    warnings: tuple[str, ...] = ()


def plan_themes(snapshot_themes: ThemeInfo | None) -> ThemesPlan:
    """Build a plan to restore theme settings from snapshot data.

    Args:
        snapshot_themes: The ``ThemeInfo`` from the snapshot (may be ``None``).

    Returns:
        A ``ThemesPlan`` listing gsettings commands to execute.
    """
    if snapshot_themes is None:
        return ThemesPlan()

    actions: list[ThemePlanAction] = []
    warnings: list[str] = []

    gtk = snapshot_themes.gtk
    if gtk:
        _add_gsetting(actions, "org.gnome.desktop.interface", "gtk-theme", gtk.theme)
        _add_gsetting(actions, "org.gnome.desktop.interface", "icon-theme", gtk.icon_theme)
        _add_gsetting(actions, "org.gnome.desktop.interface", "cursor-theme", gtk.cursor_theme)
        _add_gsetting(actions, "org.gnome.desktop.interface", "font-name", gtk.font_name)
        _add_gsetting(
            actions,
            "org.gnome.desktop.interface",
            "color-scheme",
            gtk.color_scheme,
        )

    qt = snapshot_themes.qt
    if qt:
        if qt.theme:
            warnings.append(
                f"Qt theme '{qt.theme}' cannot be auto-applied in v1 — "
                "set QT_STYLE_OVERRIDE manually"
            )
        if qt.icon_theme:
            warnings.append(f"Qt icon theme '{qt.icon_theme}' cannot be auto-applied in v1")

    return ThemesPlan(
        actions=tuple(actions),
        warnings=tuple(warnings),
    )


def apply_themes(plan: ThemesPlan) -> list[str]:
    """Execute the theme restoration plan.

    Runs ``gsettings set`` for each action. Returns a list of error messages
    (empty on full success).

    Args:
        plan: The ``ThemesPlan`` returned by ``plan_themes``.
    """
    import subprocess

    errors: list[str] = []
    for action in plan.actions:
        if action.value is None:
            continue
        try:
            subprocess.run(
                ["gsettings", "set", action.command, action.args[0], action.value],
                capture_output=True,
                text=True,
                check=True,
                timeout=5.0,
            )
        except FileNotFoundError:
            errors.append("gsettings not found — cannot apply theme settings")
            break
        except subprocess.CalledProcessError as exc:
            errors.append(f"Failed to set {action.command} {action.args[0]}: {exc.stderr.strip()}")
        except OSError as exc:
            errors.append(str(exc))
    return errors


def _add_gsetting(
    actions: list[ThemePlanAction],
    schema: str,
    key: str,
    value: str | None,
) -> None:
    if value is not None:
        actions.append(ThemePlanAction(command=schema, args=(key,), value=value))
