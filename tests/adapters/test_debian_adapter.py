from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from setupvault.distro_adapters.debian import DebianAdapter


class TestDebianAdapterDetect:
    @patch.object(DebianAdapter, "get_os_release_content")
    def test_detect_via_os_release(self, mock_os_release) -> None:
        mock_os_release.return_value = {"ID": "debian"}
        adapter = DebianAdapter()
        assert adapter.detect() is True

    @patch.object(DebianAdapter, "get_os_release_content")
    def test_detect_via_id_like(self, mock_os_release) -> None:
        mock_os_release.return_value = {"ID_LIKE": "debian"}
        adapter = DebianAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.debian.Path.exists")
    @patch.object(DebianAdapter, "get_os_release_content")
    def test_detect_via_debian_version(self, mock_os_release, mock_exists) -> None:
        mock_os_release.return_value = {}
        mock_exists.return_value = True
        adapter = DebianAdapter()
        assert adapter.detect() is True


class TestDebianAdapterListOfficial:
    def test_list_official_packages(self) -> None:
        adapter = DebianAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["apt", "list", "--installed"],
            returncode=0,
            stdout=(
                "Listing...\n"
                "apt/stable,now 2.9.8 amd64 [installed]\n"
                "bash/stable,now 5.2.21-2 amd64 [installed]\n"
                "firefox-esr/stable,now 115.12.0esr-1 amd64 [installed]\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert len(packages) == 3
        assert packages[0].name == "apt"
        assert packages[0].version == "2.9.8"
        assert packages[1].name == "bash"
        assert packages[2].name == "firefox-esr"


class TestDebianAdapterMap:
    def test_map_package_to_arch(self) -> None:
        adapter = DebianAdapter()
        mapped = adapter.map_package("build-essential", "arch")
        assert mapped == "base-devel"

    def test_map_unknown_package(self) -> None:
        adapter = DebianAdapter()
        mapped = adapter.map_package("nonexistent-pkg", "arch")
        assert mapped is None
