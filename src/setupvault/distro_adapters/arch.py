from __future__ import annotations

from pathlib import Path

from setupvault.distro_adapters.base import DistroAdapter, DistroInfo, InstallResult, Package
from setupvault.utils.shell import SafeCommandRunner

_OFFICIAL_REPOS = frozenset(
    {
        "core",
        "extra",
        "community",
        "multilib",
        "testing",
        "core-testing",
        "extra-testing",
        "community-testing",
        "multilib-testing",
    }
)


class ArchAdapter(DistroAdapter):
    """Distribution adapter for Arch Linux and derivatives."""

    distro_id = "arch"
    distro_names = ["Arch Linux", "Arch Linux (BTW)"]
    id_like = ["arch"]

    def __init__(self) -> None:
        self._runner = SafeCommandRunner(timeout=30.0)
        self._os_release: dict[str, str] = {}
        self._all_packages: list[Package] | None = None

    def detect(self) -> bool:
        if Path("/etc/arch-release").exists():
            return True
        data = self.get_os_release_content()
        if data.get("ID") == "arch":
            return True
        return "arch" in data.get("ID_LIKE", "").lower()

    def get_package_manager(self) -> str:
        return "pacman"

    def _find_aur_helper(self) -> str | None:
        """Detect an installed AUR helper (yay, paru, or others)."""
        for helper in ("yay", "paru"):
            if self._runner.check_tool(helper):
                return helper
        return None

    def _load_all_packages(self) -> list[Package]:
        if self._all_packages is not None:
            return self._all_packages

        result = self._runner.run(["pacman", "-Qqe"], check=False)
        if result.returncode != 0:
            self._all_packages = []
            return self._all_packages

        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not names:
            self._all_packages = []
            return self._all_packages

        detail_result = self._runner.run(["pacman", "-Qi"] + names, check=False, timeout=60.0)
        packages: list[Package] = []
        current: dict[str, str] = {}

        if detail_result.returncode == 0:
            for line in detail_result.stdout.splitlines():
                if not line.strip():
                    if current.get("Name"):
                        packages.append(
                            Package(
                                name=current["Name"],
                                version=current.get("Version"),
                                repository=current.get("Repository"),
                                size=_parse_size(current.get("Installed Size", "0 B")),
                                description=current.get("Description"),
                            )
                        )
                    current = {}
                    continue
                if ":" in line:
                    key, _, value = line.partition(":")
                    current[key.strip()] = value.strip()
            if current.get("Name"):
                packages.append(
                    Package(
                        name=current["Name"],
                        version=current.get("Version"),
                        repository=current.get("Repository"),
                        size=_parse_size(current.get("Installed Size", "0 B")),
                        description=current.get("Description"),
                    )
                )
        else:
            packages = [Package(name=n) for n in names]

        self._all_packages = packages
        return packages

    def list_official_packages(self) -> list[Package]:
        return [
            p
            for p in self._load_all_packages()
            if p.repository is None or p.repository in _OFFICIAL_REPOS
        ]

    def list_third_party_packages(self) -> list[Package]:
        return [
            p
            for p in self._load_all_packages()
            if p.repository is not None and p.repository not in _OFFICIAL_REPOS
        ]

    def list_aur_packages(self) -> list[Package]:
        helper = self._find_aur_helper()
        if helper:
            result = self._runner.run([helper, "-Qqm"], check=False)
            if result.returncode == 0 and result.stdout.strip():
                return [
                    Package(name=line.strip())
                    for line in result.stdout.splitlines()
                    if line.strip()
                ]

        result = self._runner.run(["pacman", "-Qqm"], check=False)
        if result.returncode != 0:
            return []
        return [Package(name=line.strip()) for line in result.stdout.splitlines() if line.strip()]

    def install_packages(
        self,
        packages: list[str],
        *,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> InstallResult:
        if not packages:
            return InstallResult(success=True, installed=[], failed=[], errors=[])

        args = ["sudo", "pacman", "-S"]
        if dry_run:
            args.append("--print-format")
            args.append("%n")
        if assume_yes:
            args.append("--noconfirm")
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
            id=data.get("ID", "arch"),
            name=data.get("NAME", "Arch Linux"),
            version=data.get("VERSION", "rolling"),
            version_id=data.get("VERSION_ID"),
            id_like=tuple(v.strip() for v in data.get("ID_LIKE", "").split() if v.strip()),
        )


def _parse_size(size_str: str) -> int | None:
    """Parse pacman's ``Installed Size`` field into bytes.

    Handles formats like ``123.45 MiB``, ``67.00 KiB``, ``1.23 GiB``.
    """
    if not size_str:
        return None
    try:
        parts = size_str.split()
        if len(parts) < 2:
            return None
        value = float(parts[0])
        unit = parts[1].upper()
        multipliers = {
            "B": 1,
            "KIB": 1024,
            "MIB": 1024**2,
            "GIB": 1024**3,
            "TIB": 1024**4,
        }
        multiplier = multipliers.get(unit, 1)
        return int(value * multiplier)
    except (ValueError, IndexError):
        return None
