from __future__ import annotations

from pathlib import Path

from setupvault.distro_adapters.base import DistroAdapter, DistroInfo, InstallResult, Package
from setupvault.utils.shell import SafeCommandRunner


class ArchAdapter(DistroAdapter):
    """Distribution adapter for Arch Linux and derivatives."""

    distro_id = "arch"
    distro_names = ["Arch Linux", "Arch Linux (BTW)"]
    id_like = ["arch"]

    def __init__(self) -> None:
        self._runner = SafeCommandRunner(timeout=30.0)
        self._os_release: dict[str, str] = {}

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

    def list_official_packages(self) -> list[Package]:
        result = self._runner.run(["pacman", "-Qqe"], check=False)
        if result.returncode != 0:
            return []

        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not names:
            return []

        # Get detailed info: pacman -Qi for each package
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
            # Fallback: just use names from -Qqe
            packages = [Package(name=n) for n in names]

        return packages

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

        # Fallback: use pacman -Qqm
        result = self._runner.run(["pacman", "-Qqm"], check=False)
        if result.returncode != 0:
            return []
        return [Package(name=line.strip()) for line in result.stdout.splitlines() if line.strip()]

    def list_third_party_packages(self) -> list[Package]:
        # Arch doesn't cleanly separate third-party from official repos
        # in a simple way. This is a best-effort: we can check which
        # pacman repositories are listed in /etc/pacman.conf that are
        # not in the well-known official set.
        return []

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
