from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from setupvault.distro_adapters.arch import ArchAdapter, _parse_size


class TestParseSize:
    def test_bytes(self) -> None:
        assert _parse_size("500.00 B") == 500

    def test_kibibytes(self) -> None:
        assert _parse_size("1.50 KiB") == 1536

    def test_mebibytes(self) -> None:
        assert _parse_size("8.25 MiB") == 8650752

    def test_gibibytes(self) -> None:
        assert _parse_size("2.00 GiB") == 2147483648

    def test_empty_string(self) -> None:
        assert _parse_size("") is None

    def test_invalid_format(self) -> None:
        assert _parse_size("not-a-size") is None


class TestArchAdapterDetect:
    @patch("setupvault.distro_adapters.arch.Path.exists")
    def test_detect_via_arch_release(self, mock_exists) -> None:
        mock_exists.return_value = True
        adapter = ArchAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.arch.Path.exists")
    @patch.object(ArchAdapter, "get_os_release_content")
    def test_detect_via_os_release(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = False
        mock_os_release.return_value = {"ID": "arch"}
        adapter = ArchAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.arch.Path.exists")
    @patch.object(ArchAdapter, "get_os_release_content")
    def test_detect_via_id_like(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = False
        mock_os_release.return_value = {"ID_LIKE": "arch"}
        adapter = ArchAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.arch.Path.exists")
    @patch.object(ArchAdapter, "get_os_release_content")
    def test_detect_fails(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = False
        mock_os_release.return_value = {"ID": "ubuntu"}
        adapter = ArchAdapter()
        assert adapter.detect() is False


class TestArchAdapterListOfficial:
    def _make_runner_mock(self):
        """Create a mock SafeCommandRunner with a mock run method."""
        return MagicMock()

    def test_list_official_packages(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.side_effect = [
            subprocess.CompletedProcess(
                args=["pacman", "-Qqe"],
                returncode=0,
                stdout="linux\nfirefox\nneovim\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=["pacman", "-Qi", "linux", "firefox", "neovim"],
                returncode=0,
                stdout=(
                    "Name            : linux\n"
                    "Version         : 6.6.32.arch1-1\n"
                    "Repository      : core\n"
                    "Installed Size  : 102.40 MiB\n"
                    "Description     : The Linux kernel and modules\n"
                    "\n"
                    "Name            : firefox\n"
                    "Version         : 127.0-1\n"
                    "Repository      : extra\n"
                    "Installed Size  : 250.00 MiB\n"
                    "\n"
                    "Name            : neovim\n"
                    "Version         : 0.10.0-1\n"
                    "Repository      : extra\n"
                    "Installed Size  : 15.00 MiB\n"
                ),
                stderr="",
            ),
        ]
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert len(packages) == 3
        assert packages[0].name == "linux"
        assert packages[0].version == "6.6.32.arch1-1"
        assert packages[0].repository == "core"
        assert packages[0].size == 107374182
        assert packages[1].name == "firefox"
        assert packages[2].name == "neovim"

    def test_list_official_packages_fallback(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.side_effect = [
            subprocess.CompletedProcess(
                args=["pacman", "-Qqe"],
                returncode=0,
                stdout="linux\nfirefox\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=["pacman", "-Qi", "linux", "firefox"],
                returncode=1,
                stdout="",
                stderr="error",
            ),
        ]
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert len(packages) == 2
        assert packages[0].name == "linux"
        assert packages[0].version is None

    def test_list_official_packages_command_fails(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["pacman", "-Qqe"],
            returncode=1,
            stdout="",
            stderr="error",
        )
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert packages == []


class TestArchAdapterListAUR:
    def test_list_aur_via_pacman(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()

        def mock_run(args, **kwargs):
            if args[0] in ("yay", "paru", "which"):
                return subprocess.CompletedProcess(
                    args=args,
                    returncode=1,
                    stdout="",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout="yay\nparu-bin\n",
                stderr="",
            )

        mock_runner.run.side_effect = mock_run
        mock_runner.check_tool.return_value = False
        adapter._runner = mock_runner
        packages = adapter.list_aur_packages()
        assert len(packages) == 2
        assert packages[0].name == "yay"
        assert packages[1].name == "paru-bin"


class TestArchAdapterInstall:
    def test_install_success(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["sudo", "pacman", "-S", "--noconfirm", "firefox"],
            returncode=0,
            stdout="",
            stderr="",
        )
        adapter._runner = mock_runner
        result = adapter.install_packages(["firefox"], assume_yes=True)
        assert result.success is True
        assert result.installed == ["firefox"]
        assert result.failed == []

    def test_install_dry_run(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["sudo", "pacman", "-S", "--print-format", "%n", "firefox"],
            returncode=0,
            stdout="firefox\n",
            stderr="",
        )
        adapter._runner = mock_runner
        result = adapter.install_packages(["firefox"], dry_run=True)
        assert result.success is True
        assert result.installed == ["firefox"]

    def test_install_empty_list(self) -> None:
        adapter = ArchAdapter()
        result = adapter.install_packages([])
        assert result.success is True
        assert result.installed == []

    def test_install_failure(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["sudo", "pacman", "-S", "nonexistent"],
            returncode=1,
            stdout="",
            stderr="error: target not found: nonexistent",
        )
        adapter._runner = mock_runner
        result = adapter.install_packages(["nonexistent"])
        assert result.success is False
        assert result.failed == ["nonexistent"]
