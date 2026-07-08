from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Run a blocking callable off the UI thread.

    Emits :attr:`finished` with the return value on success, or
    :attr:`errored` with the exception on failure. Use :meth:`run_fn`
    to schedule work and connect to the signals.
    """

    finished = Signal(object)
    errored = Signal(object)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.finished.connect(lambda _: self.deleteLater())
        self.errored.connect(lambda _: self.deleteLater())

    def run(self) -> None:  # type: ignore[override]
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - surface to UI
            self.errored.emit(exc)
