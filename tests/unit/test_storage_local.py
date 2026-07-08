from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from setupvault.core.exceptions import StorageError
from setupvault.core.snapshot import (
    DesktopEnvironment,
    DistributionInfo,
    DotfileEntry,
    EnvironmentInfo,
    FlatpakEntry,
    FontConfig,
    FontEntry,
    FontInfo,
    GtkThemeInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    QtThemeInfo,
    ShellConfigFile,
    ShellEntry,
    ShellInfo,
    SnapEntry,
    Snapshot,
    SnapshotBuilder,
    SystemInfo,
    ThemeInfo,
    WindowManager,
)
from setupvault.storage.local import (
    dict_to_snapshot,
    read_snapshot,
    snapshot_to_dict,
    write_snapshot,
)


class TestSnapshotToDict:
    def test_minimal_snapshot(self, sample_snapshot: Snapshot) -> None:
        d = snapshot_to_dict(sample_snapshot)
        assert d["snapshot_version"] == 1
        assert d["tool_version"] == "1.0.0"
        assert d["created_at"] == "2026-06-24T14:30:00Z"
        assert d["system"]["distribution"]["id"] == "arch"
        assert d["packages"]["count"]["official"] == 1500
        assert d["packages"]["count"]["total"] == 1550

    def test_optional_fields_omitted_when_none(self) -> None:
        """Fields that are None should not appear in the dict."""
        sys_info = SystemInfo(
            distribution=DistributionInfo(id="test", name="Test", version="1"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="test",
            os="Linux",
        )
        pkgs = PackageCollection(
            counts=PackageCounts(),
        )
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .build()
        )
        d = snapshot_to_dict(snap)
        assert "environment" not in d
        assert "shell" not in d
        assert "themes" not in d
        assert "fonts" not in d
        assert "dotfiles" not in d
        assert "extensions" not in d
        assert "profile" not in d
        assert "notes" not in d

    def test_full_snapshot(self) -> None:
        snap = _full_snapshot()
        d = snapshot_to_dict(snap)
        assert "profile" in d
        assert "environment" in d
        assert "shell" in d
        assert "themes" in d
        assert "fonts" in d
        assert "dotfiles" in d
        assert "extensions" in d
        assert d["profile"] == "full"
        assert d["environment"]["display_server"] == "wayland"
        assert d["shell"]["current"]["name"] == "zsh"
        assert d["themes"]["gtk"]["theme"] == "Catppuccin-Mocha"
        assert len(d["fonts"]["system_fonts"]) == 2
        assert len(d["dotfiles"]) == 2
        assert d["extensions"] == {"notes": "test"}

    def test_empty_environment_not_included(self) -> None:
        """Empty env dicts should be omitted."""
        sys_info = SystemInfo(
            distribution=DistributionInfo(id="t", name="T", version="1"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="t",
            os="Linux",
        )
        pkgs = PackageCollection(counts=PackageCounts())
        env = EnvironmentInfo(
            desktop_environment=DesktopEnvironment(name=None),
            window_manager=None,
        )
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .with_environment(env)
            .build()
        )
        d = snapshot_to_dict(snap)
        assert "environment" not in d


class TestDictToSnapshot:
    def test_minimal(self, sample_snapshot: Snapshot) -> None:
        d = snapshot_to_dict(sample_snapshot)
        restored = dict_to_snapshot(d)
        assert restored.snapshot_version == 1
        assert restored.system.distribution.id == "arch"
        assert restored.packages.counts.official == 1500

    def test_full_roundtrip(self) -> None:
        original = _full_snapshot()
        d = snapshot_to_dict(original)
        restored = dict_to_snapshot(d)
        assert restored.snapshot_version == original.snapshot_version
        assert restored.tool_version == original.tool_version
        assert restored.created_at == original.created_at
        assert restored.profile == original.profile
        assert restored.system == original.system
        assert restored.packages == original.packages
        assert restored.environment is not None
        assert restored.environment == original.environment
        assert restored.shell is not None
        assert restored.shell == original.shell
        assert restored.themes is not None
        assert restored.themes == original.themes
        assert restored.fonts is not None
        assert restored.fonts == original.fonts
        assert restored.dotfiles == original.dotfiles
        assert restored.extensions == original.extensions

    def test_unsupported_version_raises(self) -> None:
        with pytest.raises(StorageError, match="Unsupported snapshot version"):
            dict_to_snapshot({"snapshot_version": 999, "system": {}, "packages": {}})

    def test_missing_system_raises(self) -> None:
        with pytest.raises(StorageError, match="missing required field"):
            dict_to_snapshot({"snapshot_version": 1, "packages": {}})

    def test_missing_packages_raises(self) -> None:
        with pytest.raises(StorageError, match="missing required field"):
            dict_to_snapshot({"snapshot_version": 1, "system": {}})


class TestWriteAndReadSnapshot:
    def test_write_and_read(self, tmp_path: Path, sample_snapshot: Snapshot) -> None:
        p = tmp_path / "snapshot.json"
        written = write_snapshot(sample_snapshot, p)
        assert written == p
        assert p.exists()

        restored = read_snapshot(p)
        assert restored == sample_snapshot

    def test_write_compressed(self, tmp_path: Path, sample_snapshot: Snapshot) -> None:
        p = tmp_path / "snapshot.json"
        written = write_snapshot(sample_snapshot, p, compress=True)
        assert written.suffix == ".gz"
        assert written.exists()

        restored = read_snapshot(written)
        assert restored == sample_snapshot

    def test_read_uncompressed_with_compressed_file(
        self, tmp_path: Path, sample_snapshot: Snapshot
    ) -> None:
        """Reading a .json.gz file should work with read_snapshot."""
        p = tmp_path / "snapshot.json.gz"
        d = snapshot_to_dict(sample_snapshot)
        raw = json.dumps(d).encode("utf-8")
        with gzip.open(p, "wb") as f:
            f.write(raw)

        restored = read_snapshot(p)
        assert restored == sample_snapshot

    def test_file_not_found(self, tmp_path: Path) -> None:
        p = tmp_path / "nonexistent.json"
        with pytest.raises(StorageError, match="not found"):
            read_snapshot(p)

    def test_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{invalid")
        with pytest.raises(StorageError, match="Invalid JSON"):
            read_snapshot(p)

    def test_unsupported_version_on_read(self, tmp_path: Path) -> None:
        p = tmp_path / "bad_version.json"
        p.write_text(json.dumps({"snapshot_version": 999, "system": {}, "packages": {}}))
        with pytest.raises(StorageError, match="Unsupported snapshot version"):
            read_snapshot(p)


class TestSnapshotFileStorageFullRoundTrip:
    """Integration-style tests using a full snapshot with all optional fields."""

    def test_full_snapshot_roundtrip(self, tmp_path: Path) -> None:
        original = _full_snapshot()
        p = tmp_path / "full.json"
        write_snapshot(original, p)
        restored = read_snapshot(p)
        assert restored == original

    def test_full_snapshot_compressed_roundtrip(self, tmp_path: Path) -> None:
        original = _full_snapshot()
        p = tmp_path / "full.json"
        written = write_snapshot(original, p, compress=True)
        assert written.suffix == ".gz"
        restored = read_snapshot(written)
        assert restored == original

    def test_creates_parent_dirs(self, tmp_path: Path, sample_snapshot: Snapshot) -> None:
        p = tmp_path / "sub" / "dir" / "snap.json"
        written = write_snapshot(sample_snapshot, p)
        assert written.exists()

    def test_indent_controlled(self, tmp_path: Path) -> None:
        sys_info = SystemInfo(
            distribution=DistributionInfo(id="x", name="X", version="1"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="x",
            os="Linux",
        )
        pkgs = PackageCollection(counts=PackageCounts())
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .build()
        )

        p = tmp_path / "compact.json"
        write_snapshot(snap, p, indent=None)
        raw = p.read_text()
        assert "\n" not in raw

    def test_empty_counts_list(self, tmp_path: Path) -> None:
        sys_info = SystemInfo(
            distribution=DistributionInfo(id="x", name="X", version="1"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="x",
            os="Linux",
        )
        pkgs = PackageCollection(
            counts=PackageCounts(official=2, aur=0),
            official=(
                PackageEntry(name="a", version="1", repository="r"),
                PackageEntry(name="b", version="2"),
            ),
        )
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .build()
        )

        p = tmp_path / "empty_lists.json"
        write_snapshot(snap, p)
        restored = read_snapshot(p)
        assert restored.packages.counts.aur == 0
        assert len(restored.packages.aur) == 0

    def test_dotfiles_with_minimal_fields(self, tmp_path: Path) -> None:
        sys_info = SystemInfo(
            distribution=DistributionInfo(id="x", name="X", version="1"),
            kernel=KernelInfo(release="1", version="1"),
            architecture="x86_64",
            hostname="x",
            os="Linux",
        )
        pkgs = PackageCollection(counts=PackageCounts())
        snap = (
            SnapshotBuilder()
            .with_snapshot_version(1)
            .with_tool_version("1")
            .with_created_at("now")
            .with_system(sys_info)
            .with_packages(pkgs)
            .with_dotfiles([DotfileEntry(path="/tmp/test")])
            .build()
        )
        p = tmp_path / "dotfiles_min.json"
        write_snapshot(snap, p)
        restored = read_snapshot(p)
        assert len(restored.dotfiles) == 1
        assert restored.dotfiles[0].path == "/tmp/test"
        assert restored.dotfiles[0].hash is None
        assert restored.dotfiles[0].size is None
        assert restored.dotfiles[0].permissions is None


# ── Helpers ──────────────────────────────────────────────────────


def _full_snapshot() -> Snapshot:
    return (
        SnapshotBuilder()
        .with_snapshot_version(1)
        .with_tool_version("2.0.0")
        .with_created_at("2026-06-24T15:00:00Z")
        .with_profile("full")
        .with_system(
            SystemInfo(
                distribution=DistributionInfo(
                    id="arch",
                    name="Arch Linux",
                    version="rolling",
                    version_id="20260601",
                    id_like=("arch",),
                ),
                kernel=KernelInfo(
                    release="6.6.32-arch1-1",
                    version="#1 SMP PREEMPT_DYNAMIC Thu, 01 Jun 2026 00:00:00 +0000",
                ),
                architecture="x86_64",
                hostname="rig",
                uptime_seconds=3600,
                os="Linux",
            )
        )
        .with_environment(
            EnvironmentInfo(
                desktop_environment=DesktopEnvironment(name="Hyprland", version="0.44.1"),
                window_manager=WindowManager(name="Hyprland", version="0.44.1"),
                display_server="wayland",
                session_type="wayland",
            )
        )
        .with_shell(
            ShellInfo(
                current=ShellEntry(name="zsh", version="5.9", path="/usr/bin/zsh"),
                available=(
                    ShellEntry(name="bash", version="5.2.26", path="/usr/bin/bash"),
                    ShellEntry(name="zsh", version="5.9", path="/usr/bin/zsh"),
                ),
                config_files=(
                    ShellConfigFile(
                        path=".zshrc",
                        hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        size=2048,
                    ),
                ),
            )
        )
        .with_packages(
            PackageCollection(
                counts=PackageCounts(official=1500, aur=50, third_party=3, flatpak=5, snap=2),
                official=(
                    PackageEntry(
                        name="linux",
                        version="6.6.32.arch1-1",
                        repository="core",
                        size=102400000,
                        description="The Linux kernel",
                    ),
                ),
                aur=(PackageEntry(name="yay", version="12.3.5-1"),),
                third_party=(PackageEntry(name="cargo-bin", version="1.0.0", repository="cargo"),),
                flatpak=(
                    FlatpakEntry(
                        name="Brave", app_id="com.brave.Browser", version="1.0.0", origin="flathub"
                    ),
                ),
                snap=(SnapEntry(name="lxd", version="5.0"),),
            )
        )
        .with_themes(
            ThemeInfo(
                gtk=GtkThemeInfo(
                    theme="Catppuccin-Mocha",
                    icon_theme="Papirus-Dark",
                    cursor_theme="Nordzy-cursors",
                    font_name="Cantarell 11",
                    color_scheme="prefer-dark",
                ),
                qt=QtThemeInfo(
                    theme="Breeze",
                    icon_theme="breeze-dark",
                    font_name="Noto Sans 10",
                ),
            )
        )
        .with_fonts(
            FontInfo(
                system_fonts=(
                    FontEntry(
                        family="Noto Sans",
                        style="Regular",
                        path="/usr/share/fonts/noto/NotoSans-Regular.ttf",
                    ),
                    FontEntry(
                        family="Noto Sans Mono",
                        style="Regular",
                        path="/usr/share/fonts/noto/NotoSansMono-Regular.ttf",
                    ),
                ),
                config=FontConfig(hinting="full", antialiasing=True),
            )
        )
        .with_dotfiles(
            [
                DotfileEntry(
                    path=".zshrc",
                    hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    size=2048,
                    permissions="644",
                ),
                DotfileEntry(
                    path=".config/hypr/hyprland.conf",
                    hash="a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a",
                    size=12500,
                    permissions="644",
                ),
            ]
        )
        .with_extensions({"notes": "test"})
        .build()
    )
