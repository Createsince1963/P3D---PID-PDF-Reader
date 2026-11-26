"""Scan im Hintergrund (QThread) mit Fortschritt und Abbruch."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from ..core.extract import find_pdfs, read_pdf
from ..core.patterns import load
from ..core.project_store import ScanCache
from ..paths import patterns_file


class ScanWorker(QObject):
    progress = Signal(int, int, str)
    result = Signal(object)
    finished = Signal(bool)

    def __init__(self, sources, pipes: bool = False, placeholders: bool = False, db=None, version: str = ""):
        super().__init__()
        self.sources = list(sources)
        self.pipes = pipes          # Rohrleitungsnummern mit einlesen
        self.placeholders = placeholders    # Projektmodus: Platzhalter-Tags (X/? statt Ziffern) mit einlesen
        self.db, self.version = db, version     # Projekt: unveraenderte PDFs aus der Datenbank uebernehmen
        self.reused = 0
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        pat = load(patterns_file())
        files = find_pdfs(self.sources)
        cache = None
        if self.db is not None:
            try:
                text = patterns_file().read_text(encoding="utf-8")
            except OSError:
                text = ""
            cache = ScanCache(self.db, self.version, text, self.pipes, self.placeholders)
        for i, path in enumerate(files, start=1):
            if self._cancel:
                break
            self.progress.emit(i, len(files), path.name)
            result = cache.get(path) if cache else None
            if result is None:
                result = read_pdf(path, pat, self.pipes, self.placeholders)
                if cache:
                    cache.put(result)
            else:
                self.reused += 1
            self.result.emit(result)
        self.finished.emit(self._cancel)
