from __future__ import annotations

from pathlib import Path

from setupvault.distro_adapters.base import DistroAdapter, DistroInfo, InstallResult, Package
from setupvault.utils.shell import SafeCommandRunner

_OFFICIAL_REPOS = frozenset(
    {
        "@fedora",
        "@updates",
        "@fedora-cisco-openh264",
        "fedora",
        "updates",
        "fedora-cisco-openh264",
    }
)


class FedoraAdapter(DistroAdapter):
    """Distribution adapter for Fedora."""

    distro_id = "fedora"
    distro_names = ["Fedora Linux", "Fedora"]
    id_like = ["fedora"]

    def __init__(self) -> None:
        self._runner = SafeCommandRunner(timeout=30.0)
        self._os_release: dict[str, str] = {}
        self._all_packages: list[Package] | None = None

    def detect(self) -> bool:
        data = self.get_os_release_content()
        if data.get("ID") == "fedora":
            return True
        if "fedora" in data.get("ID_LIKE", "").lower():
            return True
        return Path("/etc/fedora-release").exists()

    def get_package_manager(self) -> str:
        return "dnf"

    def _load_all_packages(self) -> list[Package]:
        if self._all_packages is not None:
            return self._all_packages

        result = self._runner.run(
            ["dnf", "list", "installed"],
            check=False,
            timeout=60.0,
        )
        if result.returncode != 0:
            result = self._runner.run(
                ["rpm", "-qa", "--queryformat", "%{NAME} %{VERSION} %{REPO} %{SIZE} %{SUMMARY}\n"],
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
                packages.append(
                    Package(
                        name=parts[0],
                        version=parts[1] if len(parts) > 1 else None,
                        repository=parts[2] if len(parts) > 2 else None,
                        size=int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None,
                        description=parts[4] if len(parts) > 4 else None,
                    )
                )
            self._all_packages = packages
            return packages

        packages = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("Installed") or line.startswith("Upgraded"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name_part = parts[0]
            name = name_part.rsplit(".", 1)[0] if "." in name_part else name_part
            version = parts[1]
            repo = parts[2].lstrip("@") if len(parts) > 2 else None
            packages.append(Package(name=name, version=version, repository=repo))

        self._all_packages = packages
        return packages

    def list_official_packages(self) -> list[Package]:
        return [p for p in self._load_all_packages() if p.repository in _OFFICIAL_REPOS]

    def list_third_party_packages(self) -> list[Package]:
        return [
            p
            for p in self._load_all_packages()
            if p.repository is not None and p.repository not in _OFFICIAL_REPOS
        ]

    def install_packages(
        self,
        packages: list[str],
        *,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> InstallResult:
        if not packages:
            return InstallResult(success=True, installed=[], failed=[], errors=[])

        args = ["sudo", "dnf", "install"]
        if dry_run:
            args.append("--setopt=tsflags=test")
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
            id=data.get("ID", "fedora"),
            name=data.get("NAME", "Fedora Linux"),
            version=data.get("VERSION", ""),
            version_id=data.get("VERSION_ID"),
            id_like=tuple(v.strip() for v in data.get("ID_LIKE", "").split() if v.strip()),
        )
