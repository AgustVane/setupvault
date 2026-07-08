from __future__ import annotations

from pathlib import Path

from setupvault.distro_adapters.base import DistroAdapter, DistroInfo, InstallResult, Package
from setupvault.utils.shell import SafeCommandRunner


class OpenSUSEAdapter(DistroAdapter):
    """Distribution adapter for openSUSE (Leap and Tumbleweed)."""

    distro_id = "opensuse"
    distro_names = ["openSUSE Tumbleweed", "openSUSE Leap", "openSUSE"]
    id_like = ["suse", "opensuse"]

    def __init__(self) -> None:
        self._runner = SafeCommandRunner(timeout=30.0)
        self._os_release: dict[str, str] = {}
        self._all_packages: list[Package] | None = None

    def detect(self) -> bool:
        data = self.get_os_release_content()
        _id = data.get("ID", "")
        if _id in ("opensuse-tumbleweed", "opensuse-leap", "opensuse"):
            return True
        if "suse" in data.get("ID_LIKE", "").lower():
            return True
        if _id.startswith("opensuse"):
            return True
        return Path("/etc/SuSE-release").exists()

    def get_package_manager(self) -> str:
        return "zypper"

    def _load_all_packages(self) -> list[Package]:
        if self._all_packages is not None:
            return self._all_packages

        result = self._runner.run(
            ["rpm", "-qa", "--queryformat", "%{NAME} %{VERSION} %{VENDOR} %{SIZE} %{SUMMARY}\n"],
            check=False,
            timeout=60.0,
        )
        if result.returncode != 0:
            self._all_packages = []
            return self._all_packages

        packages: list[Package] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 4)
            if not parts:
                continue
            vendor = parts[2] if len(parts) > 2 else None
            packages.append(
                Package(
                    name=parts[0],
                    version=parts[1] if len(parts) > 1 else None,
                    repository=vendor,
                    size=int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None,
                    description=parts[4] if len(parts) > 4 else None,
                )
            )

        self._all_packages = packages
        return packages

    def list_official_packages(self) -> list[Package]:
        return self._load_all_packages()

    def install_packages(
        self,
        packages: list[str],
        *,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> InstallResult:
        if not packages:
            return InstallResult(success=True, installed=[], failed=[], errors=[])

        args = ["sudo", "zypper", "install"]
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
            id=data.get("ID", "opensuse"),
            name=data.get("NAME", "openSUSE"),
            version=data.get("VERSION", ""),
            version_id=data.get("VERSION_ID"),
            id_like=tuple(v.strip() for v in data.get("ID_LIKE", "").split() if v.strip()),
        )
