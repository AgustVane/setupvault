from unittest.mock import patch

from setupvault.detectors.themes import detect_themes


class TestDetectThemes:
    @patch("setupvault.detectors.themes._RUNNER.check_tool")
    @patch("setupvault.detectors.themes._RUNNER.run")
    def test_detect_via_gsettings(self, mock_run, mock_check_tool) -> None:
        mock_check_tool.return_value = True

        def mock_run_side_effect(args, **kwargs):
            values = {
                "gtk_theme": "'Adwaita-dark'",
                "icon_theme": "'Papirus-Dark'",
                "cursor_theme": "'Nordzy-cursors'",
                "font_name": "'Cantarell 11'",
                "color_scheme": "'prefer-dark'",
            }
            key = args[3] if len(args) > 3 else ""
            return _subprocess_result(values.get(key, "''"))

        mock_run.side_effect = mock_run_side_effect

        result = detect_themes()
        assert result.gtk is not None
        assert result.gtk.theme == "Adwaita-dark"
        assert result.gtk.icon_theme == "Papirus-Dark"
        assert result.gtk.cursor_theme == "Nordzy-cursors"
        assert result.qt is None

    @patch("setupvault.detectors.themes._detect_gtk_themes")
    @patch("setupvault.detectors.themes._detect_qt_themes")
    def test_no_themes(self, mock_qt, mock_gtk) -> None:
        mock_gtk.return_value = None
        mock_qt.return_value = None
        result = detect_themes()
        assert result.gtk is None
        assert result.qt is None


def _subprocess_result(stdout: str) -> object:
    import subprocess

    return subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=stdout,
        stderr="",
    )
