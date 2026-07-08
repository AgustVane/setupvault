from __future__ import annotations

from pathlib import Path

from setupvault.distro_adapters.base import DistroAdapter, DistroInfo, InstallResult, Package
from setupvault.utils.shell import SafeCommandRunner

_DEBIAN_OFFICIAL_SUITES = frozenset(
    {
        "stable",
        "stable-backports",
        "stable-security",
        "stable-updates",
        "testing",
        "testing-backports",
        "testing-security",
        "testing-updates",
        "unstable",
        "experimental",
        "bookworm",
        "bookworm-backports",
        "bookworm-security",
        "bookworm-updates",
        "bullseye",
        "bullseye-backports",
        "bullseye-security",
        "bullseye-updates",
        "trixie",
        "trixy-backports",
        "trixie-security",
        "trixie-updates",
        "sid",
    }
)
_UBUNTU_OFFICIAL_SUITES = frozenset(
    {
        "noble",
        "noble-updates",
        "noble-backports",
        "noble-security",
        "jammy",
        "jammy-updates",
        "jammy-backports",
        "jammy-security",
        "focal",
        "focal-updates",
        "focal-backports",
        "focal-security",
        "bionic",
        "bionic-updates",
        "bionic-backports",
        "bionic-security",
        "xenial",
        "xenial-updates",
        "xenial-backports",
        "xenial-security",
        "lunar",
        "lunar-updates",
        "lunar-backports",
        "lunar-security",
        "kinetic",
        "kinetic-updates",
        "kinetic-backports",
        "kinetic-security",
        "oracular",
        "oracular-updates",
        "oracular-backports",
        "oracular-security",
    }
)


class DebianAdapter(DistroAdapter):
    """Distribution adapter for Debian and derivatives."""

    distro_id = "debian"
    distro_names = ["Debian GNU/Linux", "Debian"]
    id_like = ["debian"]

    def __init__(self) -> None:
        self._runner = SafeCommandRunner(timeout=30.0)
        self._os_release: dict[str, str] = {}
        self._all_packages: list[Package] | None = None

    def detect(self) -> bool:
        data = self.get_os_release_content()
        if data.get("ID") == "debian":
            return True
        if "debian" in data.get("ID_LIKE", "").lower():
            return True
        return Path("/etc/debian_version").exists()

    def get_package_manager(self) -> str:
        return "apt"

    @property
    def _official_suites(self) -> frozenset[str]:
        return _DEBIAN_OFFICIAL_SUITES

    def _load_all_packages(self) -> list[Package]:
        if self._all_packages is not None:
            return self._all_packages

        result = self._runner.run(
            ["apt", "list", "--installed"],
            check=False,
            timeout=60.0,
        )
        if result.returncode != 0:
            self._all_packages = []
            return self._all_packages

        packages: list[Package] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or "..." in line:
                continue
            # Format: "package_name/suite,suite,now 1.2.3 amd64 [installed]"
            parts = line.split()
            if len(parts) < 2:
                continue
            name_part = parts[0]
            version_part = parts[1].rstrip(",") if len(parts) > 1 else ""

            name = name_part.split("/")[0]
            suites_str = name_part.split("/")[1] if "/" in name_part else ""
            version = version_part

            packages.append(
                Package(
                    name=name,
                    version=version,
                    repository=suites_str,
                )
            )

        self._all_packages = packages
        return packages

    def list_official_packages(self) -> list[Package]:
        official: list[Package] = []
        for p in self._load_all_packages():
            if not p.repository:
                official.append(p)
                continue
            suites = [s.strip() for s in p.repository.split(",")]
            if any(s in self._official_suites for s in suites):
                official.append(p)
        return official

    def list_third_party_packages(self) -> list[Package]:
        third_party: list[Package] = []
        for p in self._load_all_packages():
            if not p.repository:
                continue
            suites = [s.strip() for s in p.repository.split(",")]
            has_known = any(s in self._official_suites for s in suites)
            if not has_known:
                third_party.append(p)
        return third_party

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
