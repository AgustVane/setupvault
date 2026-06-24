from unittest.mock import patch

from setupvault.detectors.distro import detect_distro
from setupvault.distro_adapters.arch import ArchAdapter


class TestDetectDistro:
    @patch("setupvault.detectors.distro.adapter_registry.get_adapter")
    def test_detect_distro_arch(self, mock_get_adapter) -> None:
        adapter = ArchAdapter()
        with patch.object(
            adapter,
            "get_os_release_content",
            return_value={
                "ID": "arch",
                "NAME": "Arch Linux",
                "VERSION": "rolling",
            },
        ):
            mock_get_adapter.return_value = adapter
            result = detect_distro()
            assert result.distro_id == "arch"
            assert isinstance(result.adapter, ArchAdapter)
