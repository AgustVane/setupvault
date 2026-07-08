from __future__ import annotations

from setupvault.core.snapshot import (
    DistributionInfo,
    DotfileEntry,
    GtkThemeInfo,
    KernelInfo,
    PackageCollection,
    PackageCounts,
    PackageEntry,
    Snapshot,
    SystemInfo,
    ThemeInfo,
)
from setupvault.reports.html_report import render_html


def _make_snapshot(**kwargs: object) -> Snapshot:
    return Snapshot(
        snapshot_version=1,
        tool_version="1.0.0",
        created_at="2025-01-01T00:00:00",
        system=SystemInfo(
            distribution=DistributionInfo(
                id="arch",
                name="Arch Linux",
                version="rolling",
            ),
            kernel=KernelInfo(release="6.0.0", version="#1"),
            architecture="x86_64",
            hostname="box",
        ),
        packages=PackageCollection(
            counts=PackageCounts(official=2, aur=1, third_party=0, flatpak=0, snap=0),
            official=(PackageEntry(name="vim", version="9.0"),),
            aur=(PackageEntry(name="yay", version="12.0"),),
            third_party=(),
        ),
        **kwargs,
    )


class TestRenderHtml:
    def test_basic_structure(self) -> None:
        snap = _make_snapshot()
        html = render_html(snap)
        assert "<!DOCTYPE html>" in html
        assert "SetupVault Profile" in html
        assert "Arch Linux" in html
        assert "vim" in html
        assert "box" in html

    def test_includes_theme_section(self) -> None:
        snap = _make_snapshot(themes=ThemeInfo(gtk=GtkThemeInfo(theme="Adwaita")))
        html = render_html(snap)
        assert "Themes" in html
        assert "Adwaita" in html

    def test_includes_dotfiles_section(self) -> None:
        snap = _make_snapshot(dotfiles=(DotfileEntry(path=".bashrc", hash="a" * 64),))
        html = render_html(snap)
        assert "Dotfiles" in html
        assert ".bashrc" in html

    def test_no_theme_section_when_not_present(self) -> None:
        snap = _make_snapshot()
        html = render_html(snap)
        assert "Themes" not in html

    def test_counts_rendered(self) -> None:
        snap = _make_snapshot()
        html = render_html(snap)
        assert "2" in html
        assert "1" in html
