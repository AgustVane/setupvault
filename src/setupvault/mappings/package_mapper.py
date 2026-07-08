from __future__ import annotations

import json
from pathlib import Path

_MAPPINGS_DIR = Path(__file__).parent


class PackageMapper:
    """Cross-distribution package name mapping service.

    Loads a package mapping database and provides lookups to translate
    package names between distributions.

    Usage::

        mapper = PackageMapper()
        # Map "build-essential" from Debian to Arch:
        mapper.map("build-essential", target="arch")
        "base-devel"

        # Look up all names for a known package:
        mapper.resolve("vim")
        {"arch": "vim", "debian": "vim", "fedora": "vim", "ubuntu": "vim"}
    """

    def __init__(self, mapping_path: Path | None = None) -> None:
        self._path = mapping_path or _MAPPINGS_DIR / "package_map.json"
        self._entries: dict[str, dict[str, str]] = {}
        self._name_to_canonical: dict[str, str] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self._path.exists():
            self._loaded = True
            return
        try:
            raw = self._path.read_bytes()
            data: dict[str, dict[str, str]] = json.loads(raw)
        except (json.JSONDecodeError, OSError):
            self._loaded = True
            return

        self._entries = data
        for canonical, names in data.items():
            for _distro, pkg_name in names.items():
                self._name_to_canonical[pkg_name] = canonical
        self._loaded = True

    def map(self, name: str, target: str) -> str | None:
        """Map a package name from any distro to a target distro.

        Args:
            name: The package name to translate.
            target: Target distro identifier (e.g. ``"arch"``, ``"debian"``).

        Returns:
            The translated package name, or ``None`` if unknown.
        """
        self._ensure_loaded()
        canonical = self._name_to_canonical.get(name)
        if canonical is None:
            return None
        entry = self._entries.get(canonical)
        if entry is None:
            return None
        return entry.get(target)

    def resolve(self, name: str) -> dict[str, str] | None:
        """Resolve all known names for a package.

        Args:
            name: A package name on any supported distro.

        Returns:
            A dict mapping distro IDs to package names, or ``None``.
        """
        self._ensure_loaded()
        canonical = self._name_to_canonical.get(name)
        if canonical is None:
            return None
        return dict(self._entries.get(canonical) or {})

    def all_names(self, distro: str) -> set[str]:
        """Return all known package names for a given distro.

        Args:
            distro: Distro identifier (e.g. ``"arch"``).

        Returns:
            A set of package names.
        """
        self._ensure_loaded()
        return {entry[distro] for entry in self._entries.values() if distro in entry}

    def known_count(self) -> int:
        """Return the number of known package mappings."""
        self._ensure_loaded()
        return len(self._entries)


_GLOBAL_MAPPER = PackageMapper()


def get_mapper() -> PackageMapper:
    """Return the global PackageMapper singleton."""
    return _GLOBAL_MAPPER
