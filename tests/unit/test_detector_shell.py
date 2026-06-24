import os
from pathlib import Path
from unittest.mock import patch

from setupvault.detectors.shell import (
    ShellEntry,
    detect_available_shells,
    detect_current_shell,
    detect_shell_config_files,
)


class TestDetectShell:
    @patch("setupvault.detectors.shell.os.environ.get")
    @patch("setupvault.detectors.shell._get_shell_version")
    def test_detect_current_shell(self, mock_version, mock_environ) -> None:
        mock_environ.return_value = "/usr/bin/zsh"
        mock_version.return_value = "zsh 5.9 (x86_64-pc-linux-gnu)"

        result = detect_current_shell()
        assert result.name == "zsh"
        assert result.path == "/usr/bin/zsh"
        assert "5.9" in (result.version or "")

    @patch("setupvault.detectors.shell._RUNNER")
    def test_detect_current_shell_fallback(self, mock_runner) -> None:
        with patch.object(os.environ, "get", return_value="/bin/sh"):
            result = detect_current_shell()
            assert isinstance(result, ShellEntry)

    @patch("builtins.open")
    def test_detect_available_shells(self, mock_open) -> None:
        mock_open.return_value.__enter__.return_value = iter(
            [
                "# /etc/shells: valid login shells\n",
                "/bin/sh\n",
                "/bin/bash\n",
                "/usr/bin/zsh\n",
                "/usr/bin/fish\n",
            ]
        )

        shells = detect_available_shells()
        assert len(shells) >= 1
        assert any(s.name == "zsh" for s in shells)
        assert any(s.path == "/usr/bin/zsh" for s in shells)

    @patch("builtins.open")
    def test_detect_available_shells_empty_on_error(self, mock_open) -> None:
        mock_open.side_effect = FileNotFoundError
        shells = detect_available_shells()
        assert shells == ()

    @patch("setupvault.detectors.shell.hash_file")
    def test_detect_shell_config_files(self, mock_hash) -> None:
        mock_hash.return_value = "abc123"

        with patch.object(Path, "home", return_value=Path("/tmp/test_home")):
            config_dir = Path("/tmp/test_home/.config")
            config_dir.mkdir(parents=True, exist_ok=True)
            zshrc = Path("/tmp/test_home/.zshrc")
            zshrc.write_text("export ZSH=~/.oh-my-zsh\n")

            try:
                files = detect_shell_config_files("zsh")
                paths = [f.path for f in files]
                assert any(".zshrc" in p for p in paths)
            finally:
                import shutil

                shutil.rmtree(Path("/tmp/test_home"), ignore_errors=True)
