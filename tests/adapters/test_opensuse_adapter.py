from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from setupvault.distro_adapters.opensuse import OpenSUSEAdapter


class TestOpenSUSEAdapterDetect:
    @patch("setupvault.distro_adapters.opensuse.Path.exists")
    @patch.object(OpenSUSEAdapter, "get_os_release_content")
    def test_detect_tumbleweed(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = False
        mock_os_release.return_value = {"ID": "opensuse-tumbleweed"}
        adapter = OpenSUSEAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.opensuse.Path.exists")
    @patch.object(OpenSUSEAdapter, "get_os_release_content")
    def test_detect_leap(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = False
        mock_os_release.return_value = {"ID": "opensuse-leap"}
        adapter = OpenSUSEAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.opensuse.Path.exists")
    @patch.object(OpenSUSEAdapter, "get_os_release_content")
    def test_detect_via_id_like(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = False
        mock_os_release.return_value = {"ID_LIKE": "suse"}
        adapter = OpenSUSEAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.opensuse.Path.exists")
    @patch.object(OpenSUSEAdapter, "get_os_release_content")
    def test_detect_via_suse_release(self, mock_os_release, mock_exists) -> None:
        mock_exists.return_value = True
        mock_os_release.return_value = {}
        adapter = OpenSUSEAdapter()
        assert adapter.detect() is True


class TestOpenSUSEAdapterListOfficial:
    def test_list_official_packages(self) -> None:
        adapter = OpenSUSEAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=[
                "rpm",
                "-qa",
                "--queryformat",
                "%{NAME} %{VERSION} %{VENDOR} %{SIZE} %{SUMMARY}\n",
            ],
            returncode=0,
            stdout=(
                "kernel 6.6.32-1 openSUSE 52428800 Linux kernel\n"
                "firefox 127.0-1 openSUSE 262144000 Firefox\n"
                "neovim 0.10.0-1 openSUSE 15728640 Neovim\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert len(packages) == 3
        assert packages[0].name == "kernel"
        assert packages[1].name == "firefox"
        assert packages[2].name == "neovim"

    def test_list_official_packages_command_fails(self) -> None:
        adapter = OpenSUSEAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=[
                "rpm",
                "-qa",
                "--queryformat",
                "%{NAME} %{VERSION} %{VENDOR} %{SIZE} %{SUMMARY}\n",
            ],
            returncode=1,
            stdout="",
            stderr="error",
        )
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert packages == []


class TestOpenSUSEAdapterInstall:
    def test_install_success(self) -> None:
        adapter = OpenSUSEAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["sudo", "zypper", "install", "-y", "firefox"],
            returncode=0,
            stdout="",
            stderr="",
        )
        adapter._runner = mock_runner
        result = adapter.install_packages(["firefox"], assume_yes=True)
        assert result.success is True
        assert result.installed == ["firefox"]

    def test_install_dry_run(self) -> None:
        adapter = OpenSUSEAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["sudo", "zypper", "install", "--dry-run", "firefox"],
            returncode=0,
            stdout="",
            stderr="",
        )
        adapter._runner = mock_runner
        result = adapter.install_packages(["firefox"], dry_run=True)
        assert result.success is True

    def test_install_failure(self) -> None:
        adapter = OpenSUSEAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["sudo", "zypper", "install", "nonexistent"],
            returncode=1,
            stdout="",
            stderr="Package not found",
        )
        adapter._runner = mock_runner
        result = adapter.install_packages(["nonexistent"])
        assert result.success is False

    def test_install_empty_list(self) -> None:
        adapter = OpenSUSEAdapter()
        result = adapter.install_packages([])
        assert result.success is True


class TestOpenSUSEAdapterGetDistroInfo:
    @patch.object(OpenSUSEAdapter, "get_os_release_content")
    def test_get_distro_info_tumbleweed(self, mock_os_release) -> None:
        mock_os_release.return_value = {
            "ID": "opensuse-tumbleweed",
            "NAME": "openSUSE Tumbleweed",
            "VERSION": "20250618",
        }
        adapter = OpenSUSEAdapter()
        info = adapter.get_distro_info()
        assert info.id == "opensuse-tumbleweed"
        assert info.name == "openSUSE Tumbleweed"
        assert info.version == "20250618"

    def test_get_package_manager(self) -> None:
        adapter = OpenSUSEAdapter()
        assert adapter.get_package_manager() == "zypper"

    def test_distro_names(self) -> None:
        adapter = OpenSUSEAdapter()
        assert adapter.distro_names == ["openSUSE Tumbleweed", "openSUSE Leap", "openSUSE"]
        assert adapter.id_like == ["suse", "opensuse"]
