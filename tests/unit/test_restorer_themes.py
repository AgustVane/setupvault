from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from setupvault.core.snapshot import GtkThemeInfo, QtThemeInfo, ThemeInfo
from setupvault.restorers.themes_restorer import apply_themes, plan_themes


class TestPlanThemes:
    def test_none_returns_empty(self) -> None:
        plan = plan_themes(None)
        assert plan.actions == ()

    def test_gtk_actions_generated(self) -> None:
        themes = ThemeInfo(
            gtk=GtkThemeInfo(
                theme="Catppuccin-Mocha",
                icon_theme="Papirus-Dark",
                cursor_theme="Nordzy-cursors",
                font_name="Cantarell 11",
                color_scheme="prefer-dark",
            ),
        )
        plan = plan_themes(themes)
        assert len(plan.actions) == 5

        action_map = {a.args[0]: a.value for a in plan.actions}
        assert action_map["gtk-theme"] == "Catppuccin-Mocha"
        assert action_map["icon-theme"] == "Papirus-Dark"
        assert action_map["cursor-theme"] == "Nordzy-cursors"
        assert action_map["font-name"] == "Cantarell 11"
        assert action_map["color-scheme"] == "prefer-dark"

    def test_gtk_partial_fields(self) -> None:
        themes = ThemeInfo(
            gtk=GtkThemeInfo(theme="Adwaita"),
        )
        plan = plan_themes(themes)
        assert len(plan.actions) == 1
        assert plan.actions[0].value == "Adwaita"

    def test_qt_generates_warnings(self) -> None:
        themes = ThemeInfo(
            qt=QtThemeInfo(theme="Breeze", icon_theme="breeze-dark"),
        )
        plan = plan_themes(themes)
        assert plan.actions == ()
        assert len(plan.warnings) == 2
        assert any("Qt theme" in w for w in plan.warnings)
        assert any("Qt icon" in w for w in plan.warnings)

    def test_no_theme_info_returns_empty_plan(self) -> None:
        plan = plan_themes(ThemeInfo())
        assert plan.actions == ()
        assert plan.warnings == ()

    def test_qt_without_gtk(self) -> None:
        themes = ThemeInfo(
            gtk=None,
            qt=QtThemeInfo(theme="kvantum"),
        )
        plan = plan_themes(themes)
        assert plan.actions == ()
        assert len(plan.warnings) == 1


class TestApplyThemes:
    @patch("subprocess.run")
    def test_applies_actions(self, mock_run: MagicMock) -> None:
        themes = ThemeInfo(
            gtk=GtkThemeInfo(theme="Mocha"),
        )
        plan = plan_themes(themes)
        errors = apply_themes(plan)
        assert errors == []
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_gsettings_not_found(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError()
        themes = ThemeInfo(
            gtk=GtkThemeInfo(theme="Mocha"),
        )
        plan = plan_themes(themes)
        errors = apply_themes(plan)
        assert len(errors) == 1
        assert "gsettings not found" in errors[0]

    @patch("subprocess.run")
    def test_gsettings_fails(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["gsettings", "set"],
            stderr="No such schema",
        )
        themes = ThemeInfo(
            gtk=GtkThemeInfo(theme="Mocha"),
        )
        plan = plan_themes(themes)
        errors = apply_themes(plan)
        assert len(errors) == 1
        assert "No such schema" in errors[0]
