from __future__ import annotations

from setupvault.core.snapshot import (
    DesktopEnvironment,
    EnvironmentInfo,
    WindowManager,
)
from setupvault.detectors.environment import EnvironmentDetection


def export_environment(detection: EnvironmentDetection) -> EnvironmentInfo | None:
    """Transform environment detection data into a snapshot ``EnvironmentInfo``.

    Returns ``None`` when nothing meaningful was detected (sections with
    ``None`` values are omitted from the snapshot to keep it clean).
    """
    de = (
        DesktopEnvironment(
            name=detection.desktop_environment,
            version=detection.desktop_environment_version,
        )
        if detection.desktop_environment
        else None
    )

    wm = WindowManager(name=detection.window_manager) if detection.window_manager else None

    if de is None and wm is None and detection.display_server is None:
        return None

    return EnvironmentInfo(
        desktop_environment=de,
        window_manager=wm,
        display_server=detection.display_server,
        session_type=detection.session_type,
    )
