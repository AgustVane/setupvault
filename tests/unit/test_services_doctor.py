from __future__ import annotations

from setupvault.services.doctor_service import diagnose


class TestDoctorService:
    def test_diagnose_all(self) -> None:
        report = diagnose()
        assert len(report.checks) > 0

    def test_diagnose_subset(self) -> None:
        report = diagnose(names=["python_version"])
        assert len(report.checks) == 1

    def test_report_has_timestamp(self) -> None:
        report = diagnose()
        assert report.timestamp is not None
