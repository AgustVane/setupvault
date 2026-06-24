from __future__ import annotations

from setupvault.distro_adapters.base import DistroInfo
from setupvault.distro_adapters.debian import DebianAdapter


class UbuntuAdapter(DebianAdapter):
    """Distribution adapter for Ubuntu.

    Inherits most logic from DebianAdapter; only overrides detection
    and distribution identity.
    """

    distro_id = "ubuntu"
    distro_names = ["Ubuntu"]
    id_like = ["debian", "ubuntu"]

    def detect(self) -> bool:
        data = self.get_os_release_content()
        return data.get("ID") == "ubuntu"

    def get_distro_info(self) -> DistroInfo:
        if not self._os_release:
            self._os_release = self.get_os_release_content()
        data = self._os_release
        return DistroInfo(
            id=data.get("ID", "ubuntu"),
            name=data.get("NAME", "Ubuntu"),
            version=data.get("VERSION", ""),
            version_id=data.get("VERSION_ID"),
            id_like=tuple(v.strip() for v in data.get("ID_LIKE", "").split() if v.strip()),
        )
