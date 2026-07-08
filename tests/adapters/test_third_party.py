from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

from setupvault.distro_adapters.arch import ArchAdapter
from setupvault.distro_adapters.debian import DebianAdapter
from setupvault.distro_adapters.fedora import FedoraAdapter


class TestArchThirdParty:
    def test_list_third_party_returns_non_official_repos(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.side_effect = [
            subprocess.CompletedProcess(
                args=["pacman", "-Qqe"],
                returncode=0,
                stdout="linux\nfirefox\nchaotic-pkg\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=["pacman", "-Qi", "linux", "firefox", "chaotic-pkg"],
                returncode=0,
                stdout=(
                    "Name            : linux\n"
                    "Version         : 6.6.32-1\n"
                    "Repository      : core\n"
                    "Installed Size  : 100.00 MiB\n"
                    "\n"
                    "Name            : firefox\n"
                    "Version         : 127.0-1\n"
                    "Repository      : extra\n"
                    "Installed Size  : 250.00 MiB\n"
                    "\n"
                    "Name            : chaotic-pkg\n"
                    "Version         : 1.0-1\n"
                    "Repository      : chaotic-aur\n"
                    "Installed Size  : 10.00 MiB\n"
                ),
                stderr="",
            ),
        ]
        adapter._runner = mock_runner
        third_party = adapter.list_third_party_packages()
        assert len(third_party) == 1
        assert third_party[0].name == "chaotic-pkg"
        assert third_party[0].repository == "chaotic-aur"

    def test_official_excludes_third_party(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.side_effect = [
            subprocess.CompletedProcess(
                args=["pacman", "-Qqe"],
                returncode=0,
                stdout="official-pkg\nthirdparty-pkg\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=["pacman", "-Qi", "official-pkg", "thirdparty-pkg"],
                returncode=0,
                stdout=(
                    "Name            : official-pkg\n"
                    "Repository      : core\n"
                    "\n"
                    "Name            : thirdparty-pkg\n"
                    "Repository      : some-other-repo\n"
                ),
                stderr="",
            ),
        ]
        adapter._runner = mock_runner
        official = adapter.list_official_packages()
        third_party = adapter.list_third_party_packages()
        assert len(official) == 1
        assert official[0].name == "official-pkg"
        assert len(third_party) == 1
        assert third_party[0].name == "thirdparty-pkg"

    def test_no_third_party_when_all_official(self) -> None:
        adapter = ArchAdapter()
        mock_runner = MagicMock()
        mock_runner.run.side_effect = [
            subprocess.CompletedProcess(
                args=["pacman", "-Qqe"],
                returncode=0,
                stdout="linux\n",
                stderr="",
            ),
            subprocess.CompletedProcess(
                args=["pacman", "-Qi", "linux"],
                returncode=0,
                stdout="Name            : linux\nRepository      : core\n",
                stderr="",
            ),
        ]
        adapter._runner = mock_runner
        assert adapter.list_third_party_packages() == []


class TestFedoraThirdParty:
    def test_list_third_party_returns_non_official_repos(self) -> None:
        adapter = FedoraAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["dnf", "list", "installed"],
            returncode=0,
            stdout=(
                "Installed Packages\n"
                "kernel.x86_64            6.6.32-1         @fedora\n"
                "firefox.x86_64           127.0-1          @updates\n"
                "rpmfusion-pkg.x86_64     1.0-1            @rpmfusion-nonfree\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        third_party = adapter.list_third_party_packages()
        assert len(third_party) == 1
        assert third_party[0].name == "rpmfusion-pkg"
        assert third_party[0].repository == "rpmfusion-nonfree"

    def test_official_excludes_third_party_fedora(self) -> None:
        adapter = FedoraAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["dnf", "list", "installed"],
            returncode=0,
            stdout=(
                "Installed Packages\n"
                "kernel.x86_64            6.6.32-1         @fedora\n"
                "nvidia-pkg.x86_64        560.0-1          @rpmfusion-nonfree\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        official = adapter.list_official_packages()
        third_party = adapter.list_third_party_packages()
        assert len(official) == 1
        assert official[0].name == "kernel"
        assert len(third_party) == 1
        assert third_party[0].name == "nvidia-pkg"

    def test_no_third_party_when_all_official_fedora(self) -> None:
        adapter = FedoraAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["dnf", "list", "installed"],
            returncode=0,
            stdout=("Installed Packages\nkernel.x86_64            6.6.32-1         @fedora\n"),
            stderr="",
        )
        adapter._runner = mock_runner
        assert adapter.list_third_party_packages() == []


class TestDebianThirdParty:
    def test_list_third_party_returns_non_official_suites(self) -> None:
        adapter = DebianAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["apt", "list", "--installed"],
            returncode=0,
            stdout=(
                "apt list --installed\n"
                "zsh/stable,now 5.9-5 amd64 [installed]\n"
                "firefox-esr/stable-updates,now 115.0-1 amd64 [installed]\n"
                "vscode/code,now 1.90.0 amd64 [installed]\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        third_party = adapter.list_third_party_packages()
        assert len(third_party) == 1
        assert third_party[0].name == "vscode"

    def test_official_excludes_third_party_debian(self) -> None:
        adapter = DebianAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["apt", "list", "--installed"],
            returncode=0,
            stdout=(
                "apt list --installed\n"
                "zsh/stable,now 5.9-5 amd64 [installed]\n"
                "spotify/stable,non-free,now 1.2.0 amd64 [installed]\n"
            ),
            stderr="",
        )
        adapter._runner = mock_runner
        third_party = adapter.list_third_party_packages()
        # spotify's suite "stable,non-free" — "stable" is in official suites
        assert len(third_party) == 0

    def test_no_third_party_when_all_official_debian(self) -> None:
        adapter = DebianAdapter()
        mock_runner = MagicMock()
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["apt", "list", "--installed"],
            returncode=0,
            stdout=("apt list --installed\nzsh/stable,now 5.9-5 amd64 [installed]\n"),
            stderr="",
        )
        adapter._runner = mock_runner
        assert adapter.list_third_party_packages() == []
