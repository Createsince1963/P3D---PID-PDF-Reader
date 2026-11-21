"""Scan im Hintergrund (QThread) mit Fortschritt und Abbruch."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from ..core.extract import find_pdfs, read_pdf
from ..core.patterns import load
from ..paths import patterns_file


class ScanWorker(QObject):
    progress = Signal(int, int, str)
    result = Signal(object)
    finished = Signal(bool)

    def __init__(self, sources, pipes: bool = False):
        super().__init__()
        self.sources = list(sources)
        self.pipes = pipes          # Rohrleitungsnummern mit einlesen
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        pat = load(patterns_file())
        files = find_pdfs(self.sources)
        for i, path in enumerate(files, start=1):
            if self._cancel:
                break
            self.progress.emit(i, len(files), path.name)
            self.result.emit(read_pdf(path, pat, self.pipes))
        self.finished.emit(self._cancel)
