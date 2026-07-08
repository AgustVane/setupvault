from __future__ import annotations

from setupvault.doctor.checks import (
    fc_cache_available,
    get_all_checks,
    gsettings_available,
    python_version,
)


class TestDoctorChecks:
    def test_python_version_passes(self) -> None:
        name, ok, msg = python_version()
        assert name == "python_version"
        assert ok is True
        assert "3." in msg

    def test_get_all_checks_returns_list(self) -> None:
        checks = get_all_checks()
        assert len(checks) > 0
        names = [c.name for c in checks]
        assert "python_version" in names
        assert "distro_detected" in names

    def test_gsettings_check_runs(self) -> None:
        name, ok, msg = gsettings_available()
        assert name == "gsettings_available"
        assert isinstance(ok, bool)
        assert isinstance(msg, str)

    def test_fc_cache_check_runs(self) -> None:
        name, ok, msg = fc_cache_available()
        assert name == "fc_cache_available"
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
