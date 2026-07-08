from __future__ import annotations

from setupvault.doctor.runner import run_doctor


class TestDoctorRunner:
    def test_run_all_checks(self) -> None:
        report = run_doctor()
        assert len(report.checks) > 0
        assert isinstance(report.all_passed, bool)
        assert report.timestamp is not None

    def test_run_specific_checks(self) -> None:
        report = run_doctor(names=["python_version"])
        assert len(report.checks) == 1
        assert "python_version" in report.checks

    def test_passed_and_failed_lists(self) -> None:
        report = run_doctor()
        for _, ok, _ in report.passed:
            assert ok is True
        for _, ok, _ in report.failed:
            assert ok is False

    def test_unknown_check_name_omitted(self) -> None:
        report = run_doctor(names=["nonexistent_check"])
        assert len(report.checks) == 0
