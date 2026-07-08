from __future__ import annotations

from unittest.mock import MagicMock, patch

from setupvault.core.snapshot import FontConfig, FontEntry, FontInfo
from setupvault.restorers.fonts_restorer import apply_fonts, plan_fonts


class TestPlanFonts:
    def test_none_returns_empty(self) -> None:
        plan = plan_fonts(None)
        assert plan.copies == ()
        assert plan.warnings == ()

    def test_user_fonts_generate_copies(self) -> None:
        fonts = FontInfo(
            user_fonts=(
                FontEntry(family="MyFont", path="~/fonts/MyFont.otf"),
                FontEntry(family="MyFont2", path="~/fonts/MyFont2.ttf"),
            ),
        )
        plan = plan_fonts(fonts)
        assert len(plan.copies) == 2
        assert "MyFont.otf" in plan.copies[0].dest or "MyFont.otf" in plan.copies[1].dest

    def test_system_fonts_skipped_with_warning(self) -> None:
        fonts = FontInfo(
            system_fonts=(
                FontEntry(family="DejaVu Sans", path="/usr/share/fonts/dejavu/DejaVuSans.ttf"),
            ),
        )
        plan = plan_fonts(fonts)
        assert plan.copies == ()
        assert any("System font" in w for w in plan.warnings)

    def test_font_config_skipped_with_warning(self) -> None:
        fonts = FontInfo(
            config=FontConfig(hinting="full"),
        )
        plan = plan_fonts(fonts)
        assert any("Font config" in w for w in plan.warnings)

    def test_user_font_without_path_skipped(self) -> None:
        fonts = FontInfo(
            user_fonts=(FontEntry(family="NoPath"),),
        )
        plan = plan_fonts(fonts)
        assert plan.copies == ()

    def test_mixed_fonts(self) -> None:
        fonts = FontInfo(
            system_fonts=(FontEntry(family="Sys", path="/sys/Sys.ttf"),),
            user_fonts=(FontEntry(family="User", path="~/User.ttf"),),
        )
        plan = plan_fonts(fonts)
        assert len(plan.copies) == 1
        assert len(plan.warnings) == 1

    def test_empty_font_info_returns_empty_plan(self) -> None:
        plan = plan_fonts(FontInfo())
        assert plan.copies == ()
        assert plan.warnings == ()

    def test_empty_tuples(self) -> None:
        plan = plan_fonts(FontInfo(system_fonts=(), user_fonts=()))
        assert plan.copies == ()
        assert plan.warnings == ()


class TestApplyFonts:
    @patch("shutil.copy2")
    @patch("subprocess.run")
    def test_copies_fonts(self, mock_run: MagicMock, mock_copy: MagicMock) -> None:
        fonts = FontInfo(
            user_fonts=(FontEntry(family="F", path="/tmp/F.ttf"),),
        )
        plan = plan_fonts(fonts)
        errors = apply_fonts(plan)
        assert errors == []
        mock_copy.assert_called_once()
        mock_run.assert_called_once()

    @patch("shutil.copy2")
    def test_source_not_found(self, mock_copy: MagicMock) -> None:
        mock_copy.side_effect = FileNotFoundError("No such file")
        fonts = FontInfo(
            user_fonts=(FontEntry(family="F", path="/tmp/F.ttf"),),
        )
        plan = plan_fonts(fonts)
        errors = apply_fonts(plan)
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_empty_plan_does_nothing(self) -> None:
        plan = plan_fonts(None)
        errors = apply_fonts(plan)
        assert errors == []
