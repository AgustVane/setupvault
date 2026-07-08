from __future__ import annotations

import json

from setupvault.core.snapshot import (
    DistributionInfo,
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
from setupvault.reports.json_report import _snapshot_to_report, render_json


def _make_snapshot(**kwargs: object) -> Snapshot:
    return Snapshot(
        snapshot_version=1,
        tool_version="1.0.0",
        created_at="2025-01-01T00:00:00",
        profile="minimal",
        notes="test snapshot",
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
            uptime_seconds=None,
        ),
        packages=PackageCollection(
            counts=PackageCounts(official=1, aur=0, third_party=0, flatpak=0, snap=0),
            official=(PackageEntry(name="vim", version="9.0"),),
            aur=(),
            third_party=(),
        ),
        themes=ThemeInfo(gtk=GtkThemeInfo(theme="Adwaita", icon_theme="Papirus")),
        **kwargs,
    )


class TestRenderJson:
    def test_returns_valid_json(self) -> None:
        snap = _make_snapshot()
        raw = render_json(snap)
        data = json.loads(raw)
        assert data["snapshot_version"] == 1
        assert data["tool_version"] == "1.0.0"

    def test_includes_report_generated(self) -> None:
        snap = _make_snapshot()
        data = json.loads(render_json(snap))
        assert "report_generated" in data

    def test_includes_packages(self) -> None:
        snap = _make_snapshot()
        data = json.loads(render_json(snap))
        assert data["packages"]["official"][0]["name"] == "vim"

    def test_snapshot_to_report_structure(self) -> None:
        snap = _make_snapshot()
        data = _snapshot_to_report(snap)
        assert "system" in data
        assert "distribution" in data["system"]
        assert data["system"]["architecture"] == "x86_64"

    def test_notes_included(self) -> None:
        snap = _make_snapshot()
        data = json.loads(render_json(snap))
        assert data["notes"] == "test snapshot"

    def test_profile_included(self) -> None:
        snap = _make_snapshot()
        data = json.loads(render_json(snap))
        assert data["profile"] == "minimal"

    def test_themes_included(self) -> None:
        snap = _make_snapshot()
        data = json.loads(render_json(snap))
        assert data["themes"]["gtk"]["theme"] == "Adwaita"

    def test_fonts_none_by_default(self) -> None:
        snap = _make_snapshot()
        data = json.loads(render_json(snap))
        assert data["fonts"] is None

    def test_fonts_included(self) -> None:
        snap = _make_snapshot(
            fonts=FontInfo(
                user_fonts=(FontEntry(family="Fira Code", style="Regular"),),
            )
        )
        data = json.loads(render_json(snap))
        assert data["fonts"] is not None
        assert data["fonts"]["user_fonts"][0]["family"] == "Fira Code"
