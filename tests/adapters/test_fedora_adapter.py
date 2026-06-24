from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from setupvault.distro_adapters.fedora import FedoraAdapter


class TestFedoraAdapterDetect:
    @patch.object(FedoraAdapter, "get_os_release_content")
    def test_detect_via_os_release(self, mock_os_release) -> None:
        mock_os_release.return_value = {"ID": "fedora"}
        adapter = FedoraAdapter()
        assert adapter.detect() is True

    @patch.object(FedoraAdapter, "get_os_release_content")
    def test_detect_via_id_like(self, mock_os_release) -> None:
        mock_os_release.return_value = {"ID_LIKE": "fedora"}
        adapter = FedoraAdapter()
        assert adapter.detect() is True

    @patch("setupvault.distro_adapters.fedora.Path.exists")
    @patch.object(FedoraAdapter, "get_os_release_content")
    def test_detect_negative(self, mock_os_release, mock_exists) -> None:
        mock_os_release.return_value = {"ID": "ubuntu"}
        mock_exists.return_value = False
        adapter = FedoraAdapter()
        assert adapter.detect() is False


class TestFedoraAdapterListOfficial:
    def test_list_official_packages_dnf(self) -> None:
        adapter = FedoraAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["dnf", "list", "installed"],
            returncode=0,
            stdout=(
                "Installed packages\n"
                "glibc.x86_64 2.39-8.fc40 @fedora\n"
                "kernel.x86_64 6.8.5-301.fc40 @fedora\n"
                "bash.x86_64 5.2.26-4.fc40 @fedora\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert len(packages) == 3
        assert packages[0].name == "glibc"
        assert packages[0].version == "2.39-8.fc40"
        assert packages[0].repository == "fedora"
        assert packages[1].name == "kernel"
        assert packages[2].name == "bash"

    def test_list_official_packages_rpm_fallback(self) -> None:
        adapter = FedoraAdapter()
        mock_runner = MagicMock()
        mock_runner.run.side_effect = [
            subprocess.CompletedProcess(
                args=["dnf", "list", "installed"],
                returncode=1,
                stdout="",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=[
                    "rpm",
                    "-qa",
                    "--queryformat",
                    "%{NAME} %{VERSION} %{REPO} %{SIZE} %{SUMMARY}\n",
                ],
                returncode=0,
                stdout="glibc 2.39-8.fc40 fedora 12000000 GNU C Library\n",
                stderr="",
            ),
        ]
        adapter._runner = mock_runner
        packages = adapter.list_official_packages()
        assert len(packages) == 1
        assert packages[0].name == "glibc"
        assert packages[0].description == "GNU C Library"
