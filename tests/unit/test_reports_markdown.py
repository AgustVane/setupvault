from __future__ import annotations

from setupvault.core.snapshot import (
    DistributionInfo,
    DotfileEntry,
    FontConfig,
    FontEntry,
    FontInfo,
    GtkThemeInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    Snapshot,
    SystemInfo,
    ThemeInfo,
)
from setupvault.reports.markdown import render_markdown


def _make_snapshot(**kwargs: object) -> Snapshot:
    return Snapshot(
        snapshot_version=1,
        tool_version="1.0.0",
        created_at="2025-01-01T00:00:00",
        profile=None,
        notes=None,
        system=SystemInfo(
            distribution=DistributionInfo(
                id="arch",
                name="Arch Linux",
                version="rolling",
                version_id="",
                id_like=(),
            ),
            kernel=KernelInfo(release="6.0.0", version="#1"),
            architecture="x86_64",
            hostname="box",
            uptime_seconds=3600,
        ),
        packages=PackageCollection(
            counts=PackageCounts(official=2, aur=1, third_party=0, flatpak=0, snap=0),
            official=(PackageEntry(name="vim", version="9.0"),),
            aur=(PackageEntry(name="yay", version="12.0"),),
            third_party=(),
        ),
        **kwargs,
    )


class TestRenderMarkdown:
    def test_basic_structure(self) -> None:
        snap = _make_snapshot()
        md = render_markdown(snap)
        assert "# SetupVault Snapshot Report" in md
        assert "Arch Linux" in md
        assert "vim" in md
        assert "yay" in md

    def test_includes_system_section(self) -> None:
        snap = _make_snapshot()
        md = render_markdown(snap)
        assert "## System" in md
        assert "x86_64" in md
        assert "box" in md

    def test_includes_packages_section(self) -> None:
        snap = _make_snapshot()
        md = render_markdown(snap)
        assert "## Packages" in md
        assert "| Official | 2 |" in md
        assert "| AUR | 1 |" in md
        assert "| **Total** | **3** |" in md

    def test_includes_themes_when_present(self) -> None:
        snap = _make_snapshot(themes=ThemeInfo(gtk=GtkThemeInfo(theme="Adwaita")))
        md = render_markdown(snap)
        assert "## Themes" in md
        assert "Adwaita" in md

    def test_includes_dotfiles_table(self) -> None:
        snap = _make_snapshot(dotfiles=(DotfileEntry(path=".bashrc", hash="a" * 64),))
        md = render_markdown(snap)
        assert "## Dotfiles" in md
        assert ".bashrc" in md

    def test_empty_fonts_omitted(self) -> None:
        snap = _make_snapshot()
        md = render_markdown(snap)
        assert "## Fonts" not in md

    def test_fonts_section(self) -> None:
        snap = _make_snapshot(
            fonts=FontInfo(
                user_fonts=(FontEntry(family="Fira Code", style="Regular"),),
                config=FontConfig(hinting="full", antialiasing=True),
            )
        )
        md = render_markdown(snap)
        assert "## Fonts" in md
        assert "Fira Code" in md
        assert "hinting=full" in md
