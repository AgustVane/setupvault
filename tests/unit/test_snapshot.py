import pytest

from setupvault.core.snapshot import (
    DistributionInfo,
    DotfileEntry,
    EnvironmentInfo,
    FontConfig,
    FontEntry,
    FontInfo,
    GtkThemeInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    ShellConfigFile,
    ShellEntry,
    ShellInfo,
    SnapshotBuilder,
    SystemInfo,
    ThemeInfo,
)


class TestDistributionInfo:
    def test_family_uses_id_like(self) -> None:
        info = DistributionInfo(id="ubuntu", name="Ubuntu", version="24.04", id_like=("debian",))
        assert info.family() == "debian"

    def test_family_falls_back_to_id(self) -> None:
        info = DistributionInfo(id="arch", name="Arch Linux", version="rolling")
        assert info.family() == "arch"

    def test_family_empty_id_like(self) -> None:
        info = DistributionInfo(id="fedora", name="Fedora", version="40", id_like=())
        assert info.family() == "fedora"


class TestPackageCounts:
    def test_total_matches_sum(self) -> None:
        counts = PackageCounts(official=100, aur=10, third_party=5, flatpak=3, snap=2)
        assert counts.total == 120

    def test_total_with_zeros(self) -> None:
        counts = PackageCounts(official=50)
        assert counts.total == 50


class TestSnapshotBuilder:
    def test_build_minimal_snapshot(self, sample_system_info, sample_package_collection) -> None:
        snapshot = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1.0.0")
            .with_created_at("2026-06-24T14:30:00Z")
            .with_system(sample_system_info)
            .with_packages(sample_package_collection)
            .build()
        )
        assert snapshot.snapshot_version == 1
        assert snapshot.tool_version == "1.0.0"
        assert snapshot.created_at == "2026-06-24T14:30:00Z"
        assert snapshot.system == sample_system_info
        assert snapshot.packages == sample_package_collection
        assert snapshot.profile is None
        assert snapshot.environment is None
        assert snapshot.dotfiles == ()

    def test_build_full_snapshot(self, sample_system_info, sample_package_collection) -> None:
        env = EnvironmentInfo(display_server="wayland")
        shell = ShellInfo(
            current=ShellEntry(name="zsh", version="5.9", path="/usr/bin/zsh"),
            available=(ShellEntry(name="bash", version="5.2", path="/usr/bin/bash"),),
            config_files=(ShellConfigFile(path=".zshrc", hash="abc123"),),
        )
        themes = ThemeInfo(gtk=GtkThemeInfo(theme="Adwaita-dark"))
        fonts = FontInfo(
            system_fonts=(FontEntry(family="Noto Sans"),),
            config=FontConfig(hinting="full"),
        )
        dotfiles = [DotfileEntry(path=".zshrc", hash="def456", size=2048)]

        snapshot = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1.0.0")
            .with_created_at("2026-06-24T14:30:00Z")
            .with_system(sample_system_info)
            .with_packages(sample_package_collection)
            .with_environment(env)
            .with_shell(shell)
            .with_themes(themes)
            .with_fonts(fonts)
            .with_dotfiles(dotfiles)
            .build()
        )

        assert snapshot.environment == env
        assert snapshot.shell == shell
        assert snapshot.themes == themes
        assert snapshot.fonts == fonts
        assert len(snapshot.dotfiles) == 1
        assert snapshot.dotfiles[0].path == ".zshrc"

    def test_build_missing_required_field(self) -> None:
        with pytest.raises(Exception):
            SnapshotBuilder().build()

    def test_build_missing_snapshot_version(self, sample_system_info, sample_package_collection) -> None:
        builder = (
            SnapshotBuilder()
            .with_tool_version("1.0.0")
            .with_created_at("2026-01-01T00:00:00Z")
            .with_system(sample_system_info)
            .with_packages(sample_package_collection)
        )
        with pytest.raises(Exception, match="snapshot_version is required"):
            builder.build()

    def test_build_missing_system(self, sample_package_collection) -> None:
        builder = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1.0.0")
            .with_created_at("2026-01-01T00:00:00Z")
            .with_packages(sample_package_collection)
        )
        with pytest.raises(Exception, match="system section is required"):
            builder.build()


class TestSystemInfo:
    def test_system_info_creation(self, sample_distro_info, sample_kernel_info) -> None:
        info = SystemInfo(
            distribution=sample_distro_info,
            kernel=sample_kernel_info,
            architecture="x86_64",
            hostname="test-pc",
        )
        assert info.hostname == "test-pc"
        assert info.os == "Linux"
