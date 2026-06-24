from __future__ import annotations

from pathlib import Path

from setupvault.distro_adapters.base import DistroAdapter, DistroInfo, InstallResult, Package
from setupvault.utils.shell import SafeCommandRunner


class DebianAdapter(DistroAdapter):
    """Distribution adapter for Debian and derivatives."""

    distro_id = "debian"
    distro_names = ["Debian GNU/Linux", "Debian"]
    id_like = ["debian"]

    def __init__(self) -> None:
        self._runner = SafeCommandRunner(timeout=30.0)
        self._os_release: dict[str, str] = {}

    def detect(self) -> bool:
        data = self.get_os_release_content()
        if data.get("ID") == "debian":
            return True
        if "debian" in data.get("ID_LIKE", "").lower():
            return True
        return Path("/etc/debian_version").exists()

    def get_package_manager(self) -> str:
        return "apt"

    def list_official_packages(self) -> list[Package]:
        result = self._runner.run(
            ["apt", "list", "--installed"],
            check=False,
            timeout=60.0,
        )
        if result.returncode != 0:
            return []

        packages: list[Package] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or "..." in line:
                continue
            # Format: "package_name/stable,now 1.2.3 amd64 [installed]"
            parts = line.split()
            if len(parts) < 2:
                continue
            name_part = parts[0]
            version_part = parts[1] if len(parts) > 1 else ""

            name = name_part.split("/")[0] if "/" in name_part else name_part
            version = version_part.rstrip(",") if version_part else None

            packages.append(Package(name=name, version=version))

        return packages

    def install_packages(
        self,
        packages: list[str],
        *,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> InstallResult:
        if not packages:
            return InstallResult(success=True, installed=[], failed=[], errors=[])

        args = ["sudo", "apt", "install"]
        if dry_run:
            args.append("--dry-run")
        if assume_yes:
            args.append("-y")
        args.extend(packages)

        result = self._runner.run(args, check=False, timeout=300.0)

        if result.returncode == 0:
            return InstallResult(
                success=True,
                installed=list(packages),
                failed=[],
                errors=[],
            )
        return InstallResult(
            success=False,
            installed=[],
            failed=list(packages),
            errors=[result.stderr.strip()] if result.stderr else ["Unknown error"],
        )

    def get_distro_info(self) -> DistroInfo:
        if not self._os_release:
            self._os_release = self.get_os_release_content()
        data = self._os_release
        return DistroInfo(
            id=data.get("ID", "debian"),
            name=data.get("NAME", "Debian GNU/Linux"),
            version=data.get("VERSION", ""),
            version_id=data.get("VERSION_ID"),
            id_like=tuple(v.strip() for v in data.get("ID_LIKE", "").split() if v.strip()),
        )

    def map_package(self, package_name: str, target_distro_id: str) -> str | None:
        _mappings: dict[str, dict[str, str]] = {
            "arch": {
                "build-essential": "base-devel",
            },
        }
        return _mappings.get(target_distro_id, {}).get(package_name)
