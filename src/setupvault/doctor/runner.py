from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from setupvault.doctor.checks import CheckResult, get_all_checks


@dataclass
class DoctorReport:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checks: dict[str, CheckResult] = field(default_factory=dict)
    all_passed: bool = True

    @property
    def passed(self) -> list[CheckResult]:
        return [c for c in self.checks.values() if c[1]]

    @property
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks.values() if not c[1]]


def run_doctor(names: list[str] | None = None) -> DoctorReport:
    """Run diagnostic checks.

    Args:
        names: Optional list of check names to run. If None, all checks run.

    Returns:
        A DoctorReport with results.
    """
    all_checks = get_all_checks()
    report = DoctorReport()

    if names:
        check_map = {c.name: c for c in all_checks}
        selected = []
        for name in names:
            if name in check_map:
                selected.append(check_map[name])
        checks_to_run = selected
    else:
        checks_to_run = all_checks

    for check in checks_to_run:
        try:
            result = check.run()
        except Exception as exc:
            result = (check.name, False, f"Check raised exception: {exc}")
        report.checks[check.name] = result
        if not result[1]:
            report.all_passed = False

    return report
