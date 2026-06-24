from __future__ import annotations

import pytest

from setupvault.core.exceptions import UnsupportedDistributionError
from setupvault.distro_adapters.arch import ArchAdapter
from setupvault.distro_adapters.registry import (
    get_adapter_for,
    list_supported_distros,
    register,
)


class TestRegistry:
    def test_get_adapter_for_known_distro(self) -> None:
        adapter = get_adapter_for("arch")
        assert isinstance(adapter, ArchAdapter)

    def test_get_adapter_for_unknown_distro(self) -> None:
        with pytest.raises(UnsupportedDistributionError):
            get_adapter_for("nonexistent-distro")

    def test_list_supported_distros(self) -> None:
        distros = list_supported_distros()
        assert "arch" in distros
        assert "debian" in distros
        assert "fedora" in distros
        assert "ubuntu" in distros

    def test_register_custom_adapter(self) -> None:
        class FakeAdapter(ArchAdapter):
            distro_id = "fake-distro"

        register(FakeAdapter)
        assert "fake-distro" in list_supported_distros()
