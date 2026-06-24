from __future__ import annotations

from unittest.mock import patch

from setupvault.detectors.system import detect_system


class TestDetectSystem:
    @patch("setupvault.detectors.system.detect_os")
    @patch("setupvault.detectors.system.detect_kernel_release")
    @patch("setupvault.detectors.system.detect_kernel_version")
    @patch("setupvault.detectors.system.detect_architecture")
    @patch("setupvault.detectors.system.detect_hostname")
    @patch("setupvault.detectors.system.get_uptime_seconds")
    def test_detect_system(
        self,
        mock_uptime,
        mock_hostname,
        mock_arch,
        mock_kver,
        mock_krel,
        mock_os,
    ) -> None:
        mock_os.return_value = "Linux"
        mock_krel.return_value = "6.6.32-arch1-1"
        mock_kver.return_value = "#1 SMP PREEMPT_DYNAMIC"
        mock_arch.return_value = "x86_64"
        mock_hostname.return_value = "my-pc"
        mock_uptime.return_value = 3600

        result = detect_system()
        assert result.os_name == "Linux"
        assert result.kernel_release == "6.6.32-arch1-1"
        assert result.architecture == "x86_64"
        assert result.hostname == "my-pc"
        assert result.uptime_seconds == 3600
