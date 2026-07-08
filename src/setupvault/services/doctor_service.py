from __future__ import annotations

from setupvault.doctor.runner import DoctorReport, run_doctor


def diagnose(names: list[str] | None = None) -> DoctorReport:
    """Run system diagnostics.

    Args:
        names: Optional subset of check names.

    Returns:
        A DoctorReport with outcomes.
    """
    return run_doctor(names)
