from __future__ import annotations

import json
from pathlib import Path

from setupvault.mappings.package_mapper import PackageMapper, get_mapper


class TestPackageMapper:
    def test_known_mappings(self) -> None:
        mapper = PackageMapper()
        assert mapper.map("vim", target="arch") == "vim"
        assert mapper.map("vim", target="debian") == "vim"
        assert mapper.map("vim", target="fedora") == "vim"

    def test_base_devel_mapping(self) -> None:
        mapper = PackageMapper()
        assert mapper.map("base-devel", target="debian") == "build-essential"
        assert mapper.map("build-essential", target="arch") == "base-devel"
        assert mapper.map("build-essential", target="fedora") == "@development-tools"

    def test_unknown_package_returns_none(self) -> None:
        mapper = PackageMapper()
        assert mapper.map("nonexistent-package-xyz", target="arch") is None

    def test_unknown_target_returns_none(self) -> None:
        mapper = PackageMapper()
        assert mapper.map("vim", target="solaris") is None

    def test_resolve_known(self) -> None:
        mapper = PackageMapper()
        result = mapper.resolve("vim")
        assert result is not None
        assert result["arch"] == "vim"
        assert result["debian"] == "vim"
        assert result["fedora"] == "vim"

    def test_resolve_unknown(self) -> None:
        mapper = PackageMapper()
        assert mapper.resolve("does-not-exist") is None

    def test_all_names(self) -> None:
        mapper = PackageMapper()
        names = mapper.all_names("arch")
        assert "vim" in names
        assert "python" in names
        assert "base-devel" in names

    def test_known_count(self) -> None:
        mapper = PackageMapper()
        assert mapper.known_count() > 150

    def test_load_from_custom_path(self, tmp_path: Path) -> None:
        custom_map = tmp_path / "custom.json"
        custom_map.write_text(
            json.dumps(
                {
                    "my-pkg": {"arch": "my-pkg", "debian": "my-pkg-debian"},
                }
            )
        )
        mapper = PackageMapper(mapping_path=custom_map)
        assert mapper.map("my-pkg", target="debian") == "my-pkg-debian"
        assert mapper.map("my-pkg-debian", target="arch") == "my-pkg"

    def test_empty_file(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.json"
        empty.write_text("{}")
        mapper = PackageMapper(mapping_path=empty)
        assert mapper.known_count() == 0
        assert mapper.map("anything", target="arch") is None

    def test_get_mapper_singleton(self) -> None:
        mapper1 = get_mapper()
        mapper2 = get_mapper()
        assert mapper1 is mapper2
