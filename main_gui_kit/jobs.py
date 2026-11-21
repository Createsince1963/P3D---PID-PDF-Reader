"""Reusable QThread job pattern extracted from AZ v0.62 workers."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread, Signal


ProgressCallback = Callable[[int, str], None]
JobFunction = Callable[[ProgressCallback], Any]


class BackgroundJob(QThread):
    """Run one callable off the GUI thread and report progress/result safely."""

    progress = Signal(int, str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, work: JobFunction, parent=None):
        super().__init__(parent)
        self._work = work

    def run(self) -> None:
        try:
            self.succeeded.emit(self._work(self.progress.emit))
        except Exception as exc:  # Worker exceptions must cross the Qt boundary as text.
            self.failed.emit(str(exc))
