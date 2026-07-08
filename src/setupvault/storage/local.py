from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

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
from setupvault.core.versions import CURRENT_SNAPSHOT_VERSION, is_supported


def snapshot_to_dict(snapshot: Snapshot) -> dict[str, Any]:
    """Serialize a ``Snapshot`` to a plain dict suitable for JSON.

    This is a custom serializer rather than relying on ``dataclasses.asdict``
    to have precise control over the output format (e.g. tuples → lists,
    ``None`` fields omitted).
    """
    data: dict[str, Any] = {
        "snapshot_version": snapshot.snapshot_version,
        "tool_version": snapshot.tool_version,
        "created_at": snapshot.created_at,
        "system": _system_to_dict(snapshot.system),
        "packages": _packages_to_dict(snapshot.packages),
    }

    if snapshot.profile is not None:
        data["profile"] = snapshot.profile
    if snapshot.notes is not None:
        data["notes"] = snapshot.notes
    if snapshot.environment is not None:
        env_dict = _environment_to_dict(snapshot.environment)
        if env_dict:
            data["environment"] = env_dict
    if snapshot.shell is not None:
        shell_dict = _shell_to_dict(snapshot.shell)
        if shell_dict:
            data["shell"] = shell_dict
    if snapshot.themes is not None:
        themes_dict = _themes_to_dict(snapshot.themes)
        if themes_dict:
            data["themes"] = themes_dict
    if snapshot.fonts is not None:
        fonts_dict = _fonts_to_dict(snapshot.fonts)
        if fonts_dict:
            data["fonts"] = fonts_dict
    if snapshot.dotfiles:
        data["dotfiles"] = [_dotfile_to_dict(d) for d in snapshot.dotfiles]
    if snapshot.extensions:
        data["extensions"] = snapshot.extensions

    return data


def dict_to_snapshot(data: dict[str, Any]) -> Snapshot:
    """Deserialize a plain dict (from JSON) into a ``Snapshot``.

    Validates the snapshot version and required fields before
    constructing the domain object.
    """
    sv = data.get("snapshot_version")
    if not isinstance(sv, int) or not is_supported(sv):
        raise StorageError(
            f"Unsupported snapshot version {sv!r}. "
            f"Supported versions: {list(range(1, CURRENT_SNAPSHOT_VERSION + 1))}"
        )

    system_data = data.get("system")
    if not isinstance(system_data, dict):
        raise StorageError("Snapshot is missing required field: system")

    packages_data = data.get("packages")
    if not isinstance(packages_data, dict):
        raise StorageError("Snapshot is missing required field: packages")

    builder = SnapshotBuilder()
    builder.with_snapshot_version(sv)
    builder.with_tool_version(str(data.get("tool_version", "")))
    builder.with_created_at(str(data.get("created_at", "")))
    builder.with_system(_dict_to_system(system_data))
    builder.with_packages(_dict_to_packages(packages_data))

    if "profile" in data:
        builder.with_profile(str(data["profile"]))
    if "notes" in data:
        builder.with_notes(str(data["notes"]))
    if "environment" in data:
        builder.with_environment(_dict_to_environment(data["environment"]))
    if "shell" in data:
        builder.with_shell(_dict_to_shell(data["shell"]))
    if "themes" in data:
        builder.with_themes(_dict_to_themes(data["themes"]))
    if "fonts" in data:
        builder.with_fonts(_dict_to_fonts(data["fonts"]))
    if "dotfiles" in data:
        builder.with_dotfiles([_dict_to_dotfile(d) for d in data["dotfiles"]])
    if "extensions" in data and isinstance(data["extensions"], dict):
        builder.with_extensions(data["extensions"])

    return builder.build()


def read_snapshot(path: str | Path) -> Snapshot:
    """Read a snapshot from a JSON file (optionally gzip-compressed).

    Args:
        path: Path to a ``.json`` or ``.json.gz`` file.

    Returns:
        A validated ``Snapshot`` instance.

    Raises:
        StorageError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise StorageError(f"Snapshot file not found: {path}")

    try:
        if path.suffix == ".gz" or path.name.endswith(".json.gz"):
            raw = gzip.decompress(path.read_bytes())
        else:
            raw = path.read_bytes()
    except OSError as exc:
        raise StorageError(f"Failed to read snapshot file {path}: {exc}") from exc

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(f"Invalid JSON in snapshot file {path}: {exc}") from exc

    return dict_to_snapshot(data)


def write_snapshot(
    snapshot: Snapshot,
    path: str | Path,
    *,
    compress: bool = False,
    indent: int | None = 2,
) -> Path:
    """Write a snapshot to a JSON file.

    Args:
    snapshot: The ``Snapshot`` to write.
    path: Destination path. If *compress* is ``True``, ``.gz`` is appended.
    compress: If ``True``, write gzip-compressed JSON.
    indent: JSON indentation level (``None`` for compact output).

    Returns:
        The path to the written file.
    """
    path = Path(path)
    data = snapshot_to_dict(snapshot)
    json_bytes = json.dumps(data, indent=indent, ensure_ascii=False).encode("utf-8")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if compress:
            out_path = path.with_suffix(path.suffix + ".gz")
            with gzip.open(out_path, "wb") as f:
                f.write(json_bytes)
        else:
            out_path = path
            path.write_bytes(json_bytes)
    except OSError as exc:
        raise StorageError(f"Failed to write snapshot to {path}: {exc}") from exc

    return out_path


# ── Serialisation helpers ────────────────────────────────────────


def _opt(val: Any) -> Any:
    """Return the value or ``None`` — used for optional fields."""
    return val


def _system_to_dict(s: SystemInfo) -> dict[str, Any]:
    return {
        "distribution": {
            "id": s.distribution.id,
            "name": s.distribution.name,
            "version": s.distribution.version,
            **({"version_id": s.distribution.version_id} if s.distribution.version_id else {}),
            **({"id_like": list(s.distribution.id_like)} if s.distribution.id_like else {}),
        },
        "kernel": {
            "release": s.kernel.release,
            "version": s.kernel.version,
        },
        "architecture": s.architecture,
        "hostname": s.hostname,
        **({"uptime_seconds": s.uptime_seconds} if s.uptime_seconds is not None else {}),
        "os": s.os,
    }


def _environment_to_dict(e: EnvironmentInfo) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if e.desktop_environment:
        de: dict[str, Any] = {}
        if e.desktop_environment.name:
            de["name"] = e.desktop_environment.name
        if e.desktop_environment.version:
            de["version"] = e.desktop_environment.version
        if de:
            d["desktop_environment"] = de
    if e.window_manager:
        wm: dict[str, Any] = {}
        if e.window_manager.name:
            wm["name"] = e.window_manager.name
        if e.window_manager.version:
            wm["version"] = e.window_manager.version
        if wm:
            d["window_manager"] = wm
    if e.display_server:
        d["display_server"] = e.display_server
    if e.session_type:
        d["session_type"] = e.session_type
    return d


def _shell_to_dict(s: ShellInfo) -> dict[str, Any]:
    d: dict[str, Any] = {
        "current": {
            "name": s.current.name,
            **({"version": s.current.version} if s.current.version else {}),
            **({"path": s.current.path} if s.current.path else {}),
        },
    }
    if s.available:
        d["available"] = [
            {
                "name": a.name,
                **({"version": a.version} if a.version else {}),
                **({"path": a.path} if a.path else {}),
            }
            for a in s.available
        ]
    if s.config_files:
        d["config_files"] = [
            {
                "path": cf.path,
                **({"hash": cf.hash} if cf.hash else {}),
                **({"size": cf.size} if cf.size is not None else {}),
            }
            for cf in s.config_files
        ]
    return d


def _packages_to_dict(p: PackageCollection) -> dict[str, Any]:
    d: dict[str, Any] = {
        "count": {
            "official": p.counts.official,
            "aur": p.counts.aur,
            "third_party": p.counts.third_party,
            "flatpak": p.counts.flatpak,
            "snap": p.counts.snap,
            "total": p.counts.total,
        },
    }
    if p.official:
        d["official"] = [
            {
                "name": pkg.name,
                "version": pkg.version,
                **({"repository": pkg.repository} if pkg.repository else {}),
                **({"size": pkg.size} if pkg.size is not None else {}),
                **({"description": pkg.description} if pkg.description else {}),
            }
            for pkg in p.official
        ]
    if p.aur:
        d["aur"] = [{"name": pkg.name, "version": pkg.version} for pkg in p.aur if pkg.version]
    if p.third_party:
        d["third_party"] = [
            {
                "name": pkg.name,
                "version": pkg.version,
                **({"repository": pkg.repository} if pkg.repository else {}),
            }
            for pkg in p.third_party
        ]
    if p.flatpak:
        d["flatpak"] = [
            {
                "name": fp.name,
                "app_id": fp.app_id,
                **({"version": fp.version} if fp.version else {}),
                **({"origin": fp.origin} if fp.origin else {}),
            }
            for fp in p.flatpak
        ]
    if p.snap:
        d["snap"] = [
            {"name": s.name, **({"version": s.version} if s.version else {})} for s in p.snap
        ]
    return d


def _themes_to_dict(t: ThemeInfo) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if t.gtk:
        g: dict[str, Any] = {}
        if t.gtk.theme:
            g["theme"] = t.gtk.theme
        if t.gtk.icon_theme:
            g["icon_theme"] = t.gtk.icon_theme
        if t.gtk.cursor_theme:
            g["cursor_theme"] = t.gtk.cursor_theme
        if t.gtk.font_name:
            g["font_name"] = t.gtk.font_name
        if t.gtk.color_scheme:
            g["color_scheme"] = t.gtk.color_scheme
        if g:
            d["gtk"] = g
    if t.qt:
        q: dict[str, Any] = {}
        if t.qt.theme:
            q["theme"] = t.qt.theme
        if t.qt.icon_theme:
            q["icon_theme"] = t.qt.icon_theme
        if t.qt.font_name:
            q["font_name"] = t.qt.font_name
        if q:
            d["qt"] = q
    return d


def _fonts_to_dict(f: FontInfo) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if f.system_fonts:
        d["system_fonts"] = [
            {
                "family": sf.family,
                **({"style": sf.style} if sf.style else {}),
                **({"path": sf.path} if sf.path else {}),
            }
            for sf in f.system_fonts
        ]
    if f.user_fonts:
        d["user_fonts"] = [
            {
                "family": uf.family,
                **({"path": uf.path} if uf.path else {}),
            }
            for uf in f.user_fonts
        ]
    if f.config:
        c: dict[str, Any] = {}
        if f.config.freetype_preset:
            c["freetype_preset"] = f.config.freetype_preset
        if f.config.hinting:
            c["hinting"] = f.config.hinting
        if f.config.antialiasing is not None:
            c["antialiasing"] = f.config.antialiasing
        if c:
            d["config"] = c
    return d


def _dotfile_to_dict(d: DotfileEntry) -> dict[str, Any]:
    entry: dict[str, Any] = {"path": d.path}
    if d.hash:
        entry["hash"] = d.hash
    if d.size is not None:
        entry["size"] = d.size
    if d.permissions:
        entry["permissions"] = d.permissions
    if d.content:
        entry["content"] = d.content
    return entry


# ── Deserialisation helpers ──────────────────────────────────────


def _dict_to_system(d: dict[str, Any]) -> SystemInfo:
    dist = d.get("distribution", {})
    kernel = d.get("kernel", {})
    return SystemInfo(
        distribution=DistributionInfo(
            id=str(dist.get("id", "")),
            name=str(dist.get("name", "")),
            version=str(dist.get("version", "")),
            version_id=str(dist["version_id"])
            if "version_id" in dist and dist["version_id"] is not None
            else None,
            id_like=tuple(str(x) for x in dist.get("id_like", [])),
        ),
        kernel=KernelInfo(
            release=str(kernel.get("release", "")),
            version=str(kernel.get("version", "")),
        ),
        architecture=str(d.get("architecture", "")),
        hostname=str(d.get("hostname", "")),
        uptime_seconds=int(d["uptime_seconds"])
        if "uptime_seconds" in d and d["uptime_seconds"] is not None
        else None,
        os=str(d.get("os", "Linux")),
    )


def _dict_to_environment(d: dict[str, Any]) -> EnvironmentInfo | None:
    if not isinstance(d, dict):
        return None
    de_data = d.get("desktop_environment")
    de = (
        DesktopEnvironment(
            name=str(de_data["name"])
            if isinstance(de_data, dict) and de_data.get("name")
            else None,
            version=str(de_data["version"])
            if isinstance(de_data, dict) and de_data.get("version")
            else None,
        )
        if isinstance(de_data, dict)
        else None
    )

    wm_data = d.get("window_manager")
    wm = (
        WindowManager(
            name=str(wm_data["name"])
            if isinstance(wm_data, dict) and wm_data.get("name")
            else None,
            version=str(wm_data["version"])
            if isinstance(wm_data, dict) and wm_data.get("version")
            else None,
        )
        if isinstance(wm_data, dict)
        else None
    )

    return EnvironmentInfo(
        desktop_environment=de,
        window_manager=wm,
        display_server=str(d["display_server"]) if "display_server" in d else None,
        session_type=str(d["session_type"]) if "session_type" in d else None,
    )


def _dict_to_shell(d: dict[str, Any]) -> ShellInfo | None:
    if not isinstance(d, dict):
        return None
    cur = d.get("current", {})
    current = ShellEntry(
        name=str(cur.get("name", "")),
        version=str(cur["version"]) if "version" in cur and cur["version"] is not None else None,
        path=str(cur["path"]) if "path" in cur and cur["path"] is not None else None,
    )
    available = tuple(
        ShellEntry(
            name=str(a.get("name", "")),
            version=str(a["version"]) if "version" in a and a["version"] is not None else None,
            path=str(a["path"]) if "path" in a and a["path"] is not None else None,
        )
        for a in d.get("available", [])
    )
    config_files = tuple(
        ShellConfigFile(
            path=str(cf.get("path", "")),
            hash=str(cf["hash"]) if "hash" in cf and cf["hash"] is not None else None,
            size=int(cf["size"]) if "size" in cf and cf["size"] is not None else None,
        )
        for cf in d.get("config_files", [])
    )
    return ShellInfo(current=current, available=available, config_files=config_files)


def _dict_to_packages(d: dict[str, Any]) -> PackageCollection:
    cnt = d.get("count", {})
    counts = PackageCounts(
        official=int(cnt.get("official", 0)),
        aur=int(cnt.get("aur", 0)),
        third_party=int(cnt.get("third_party", 0)),
        flatpak=int(cnt.get("flatpak", 0)),
        snap=int(cnt.get("snap", 0)),
    )
    official = tuple(
        PackageEntry(
            name=str(p.get("name", "")),
            version=str(p["version"]) if "version" in p and p["version"] is not None else None,
            repository=str(p["repository"])
            if "repository" in p and p["repository"] is not None
            else None,
            size=int(p["size"]) if "size" in p and p["size"] is not None else None,
            description=str(p["description"])
            if "description" in p and p["description"] is not None
            else None,
        )
        for p in d.get("official", [])
    )
    aur = tuple(
        PackageEntry(name=str(p.get("name", "")), version=str(p.get("version", "")))
        for p in d.get("aur", [])
    )
    third_party = tuple(
        PackageEntry(
            name=str(p.get("name", "")),
            version=str(p.get("version", "")),
            repository=str(p["repository"])
            if "repository" in p and p["repository"] is not None
            else None,
        )
        for p in d.get("third_party", [])
    )
    flatpak = tuple(
        FlatpakEntry(
            name=str(p.get("name", "")),
            app_id=str(p.get("app_id", "")),
            version=str(p["version"]) if "version" in p and p["version"] is not None else None,
            origin=str(p["origin"]) if "origin" in p and p["origin"] is not None else None,
        )
        for p in d.get("flatpak", [])
    )
    snap_pkgs = tuple(
        SnapEntry(name=str(p.get("name", "")), version=str(p.get("version", "")))
        for p in d.get("snap", [])
    )
    return PackageCollection(
        counts=counts,
        official=official,
        aur=aur,
        third_party=third_party,
        flatpak=flatpak,
        snap=snap_pkgs,
    )


def _dict_to_themes(d: dict[str, Any]) -> ThemeInfo | None:
    if not isinstance(d, dict):
        return None
    gtk_data = d.get("gtk")
    gtk = (
        GtkThemeInfo(
            theme=str(gtk_data.get("theme"))
            if isinstance(gtk_data, dict) and gtk_data.get("theme")
            else None,
            icon_theme=str(gtk_data.get("icon_theme"))
            if isinstance(gtk_data, dict) and gtk_data.get("icon_theme")
            else None,
            cursor_theme=str(gtk_data.get("cursor_theme"))
            if isinstance(gtk_data, dict) and gtk_data.get("cursor_theme")
            else None,
            font_name=str(gtk_data.get("font_name"))
            if isinstance(gtk_data, dict) and gtk_data.get("font_name")
            else None,
            color_scheme=str(gtk_data.get("color_scheme"))
            if isinstance(gtk_data, dict) and gtk_data.get("color_scheme")
            else None,
        )
        if isinstance(gtk_data, dict)
        else None
    )

    qt_data = d.get("qt")
    qt = (
        QtThemeInfo(
            theme=str(qt_data.get("theme"))
            if isinstance(qt_data, dict) and qt_data.get("theme")
            else None,
            icon_theme=str(qt_data.get("icon_theme"))
            if isinstance(qt_data, dict) and qt_data.get("icon_theme")
            else None,
            font_name=str(qt_data.get("font_name"))
            if isinstance(qt_data, dict) and qt_data.get("font_name")
            else None,
        )
        if isinstance(qt_data, dict)
        else None
    )

    if gtk is None and qt is None:
        return None
    return ThemeInfo(gtk=gtk, qt=qt)


def _dict_to_fonts(d: dict[str, Any]) -> FontInfo | None:
    if not isinstance(d, dict):
        return None
    system = tuple(
        FontEntry(
            family=str(f.get("family", "")),
            style=str(f["style"]) if "style" in f and f["style"] is not None else None,
            path=str(f["path"]) if "path" in f and f["path"] is not None else None,
        )
        for f in d.get("system_fonts", [])
    )
    user = tuple(
        FontEntry(
            family=str(f.get("family", "")),
            path=str(f["path"]) if "path" in f and f["path"] is not None else None,
        )
        for f in d.get("user_fonts", [])
    )
    cfg = d.get("config")
    config = (
        FontConfig(
            freetype_preset=str(cfg.get("freetype_preset"))
            if isinstance(cfg, dict) and cfg.get("freetype_preset")
            else None,
            hinting=str(cfg.get("hinting"))
            if isinstance(cfg, dict) and cfg.get("hinting")
            else None,
            antialiasing=bool(cfg["antialiasing"])
            if isinstance(cfg, dict) and "antialiasing" in cfg
            else None,
        )
        if isinstance(cfg, dict)
        else None
    )
    return FontInfo(system_fonts=system, user_fonts=user, config=config)


def _dict_to_dotfile(d: dict[str, Any]) -> DotfileEntry:
    return DotfileEntry(
        path=str(d.get("path", "")),
        hash=str(d["hash"]) if "hash" in d and d["hash"] is not None else None,
        size=int(d["size"]) if "size" in d and d["size"] is not None else None,
        permissions=str(d["permissions"])
        if "permissions" in d and d["permissions"] is not None
        else None,
        content=str(d["content"]) if "content" in d and d["content"] is not None else None,
    )
