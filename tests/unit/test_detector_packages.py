import subprocess
from unittest.mock import patch

from setupvault.detectors.packages import (
    Package,
    detect_aur_packages,
    detect_flatpak_packages,
    detect_official_packages,
    detect_snap_packages,
)


class MockAdapter:
    """A minimal mock adapter for testing package detectors."""

    def __init__(self, official=None, aur=None):
        self._official = official or []
        self._aur = aur or []

    def list_official_packages(self):
        return self._official

    def list_aur_packages(self):
        return self._aur


class TestDetectOfficial:
    def test_with_real_adapter(self) -> None:
        packages = [Package(name="linux"), Package(name="firefox")]
        adapter = MockAdapter(official=packages)
        result = detect_official_packages(adapter)
        assert len(result) == 2
        assert result[0].name == "linux"

    def test_with_failing_adapter(self) -> None:
        class FailingAdapter:
            def list_official_packages(self):
                raise RuntimeError("package manager not found")

        result = detect_official_packages(FailingAdapter())
        assert result == ()


class TestDetectAUR:
    def test_with_aur_packages(self) -> None:
        adapter = MockAdapter(aur=[Package(name="yay")])
        result = detect_aur_packages(adapter)
        assert len(result) == 1
        assert result[0].name == "yay"

    def test_without_aur(self) -> None:
        adapter = MockAdapter()
        result = detect_aur_packages(adapter)
        assert result == ()


class TestDetectFlatpak:
    @patch("setupvault.detectors.packages._RUNNER")
    def test_detect_flatpak(self, mock_runner) -> None:
        mock_runner.check_tool.return_value = True
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["flatpak", "list", "--app", "--columns=application,version,origin"],
            returncode=0,
            stdout="org.mozilla.firefox\t127.0\tflathub\norg.gimp.GIMP\t3.0\tflathub\n",
            stderr="",
        )
        packages = detect_flatpak_packages()
        assert len(packages) == 2
        assert packages[0].name == "firefox"
        assert packages[0].repository == "flathub"

    @patch("setupvault.detectors.packages._RUNNER")
    def test_detect_flatpak_not_installed(self, mock_runner) -> None:
        mock_runner.check_tool.return_value = False
        packages = detect_flatpak_packages()
        assert packages == ()


class TestDetectSnap:
    @patch("setupvault.detectors.packages._RUNNER")
    def test_detect_snap(self, mock_runner) -> None:
        mock_runner.check_tool.return_value = True
        mock_runner.run.return_value = subprocess.CompletedProcess(
            args=["snap", "list"],
            returncode=0,
            stdout="Name    Version     Rev   Tracking  Publisher\n"
            "core22  20240101   1234  latest    canonical\n"
            "firefox 127.0-1   5678  latest    mozilla\n",
            stderr="",
        )
        packages = detect_snap_packages()
        assert len(packages) == 2
        assert packages[0].name == "core22"
        assert packages[1].name == "firefox"
