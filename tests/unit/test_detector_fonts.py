from unittest.mock import patch

from setupvault.detectors.fonts import detect_fonts


class TestDetectFonts:
    @patch("setupvault.detectors.fonts._RUNNER.check_tool")
    @patch("setupvault.detectors.fonts._RUNNER.run")
    def test_detect_system_fonts(self, mock_run, mock_check_tool) -> None:
        mock_check_tool.return_value = True
        mock_run.return_value = __import__("subprocess").CompletedProcess(
            args=["fc-list"],
            returncode=0,
            stdout=(
                "Noto Sans\tRegular\t/usr/share/fonts/noto/NotoSans-Regular.ttf\n"
                "Noto Sans Mono\tRegular\t/usr/share/fonts/noto/NotoSansMono-Regular.ttf\n"
                "DejaVu Sans\tBook\t/usr/share/fonts/dejavu/DejaVuSans.ttf\n"
            ),
            stderr="",
        )

        result = detect_fonts()
        assert len(result.system_fonts) == 3
        assert result.system_fonts[0].family == "Noto Sans"
        assert result.system_fonts[1].family == "Noto Sans Mono"
        assert result.system_fonts[2].family == "DejaVu Sans"

    @patch("setupvault.detectors.fonts._RUNNER.check_tool")
    def test_fc_list_not_installed(self, mock_check_tool) -> None:
        mock_check_tool.return_value = False
        result = detect_fonts()
        assert result.system_fonts == ()
