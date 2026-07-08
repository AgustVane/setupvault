from __future__ import annotations

from typing import Any

from setupvault.cli.doctor_cmd import run_doctor


def _make_args(checks: list[str] | None = None) -> Any:
    return type("Args", (), {"checks": checks or []})()


class TestCliDoctor:
    def test_run_all(self, capsys: Any) -> None:
        rc = run_doctor(_make_args())
        assert rc in (0, 1)
        captured = capsys.readouterr()
        assert "Doctor Report" in captured.out

    def test_run_specific(self, capsys: Any) -> None:
        run_doctor(_make_args(checks=["python_version"]))
        captured = capsys.readouterr()
        assert "python_version" in captured.out
