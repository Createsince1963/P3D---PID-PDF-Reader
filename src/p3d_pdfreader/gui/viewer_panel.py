"""PDF-Viewer-Bereich: Leiste mit Tab-Buttons + Vorschau; wahlweise im Hauptfenster oder als eigenes Fenster auf dem
zweiten Monitor (Umschalter "2. Monitor"). Schliessen des Viewer-Fensters holt den Viewer ins Hauptfenster zurueck.
Die Wahl wird gemerkt (``config/state.json``)."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from main_gui_kit.buttons import ButtonKind, action_button

from .. import i18n
from . import last_paths
from .design import NOTE_QSS
from .preview import PdfPreview
from .toolstrip import ToolStrip

STATE_KEY = "viewer_on_second_monitor"
MONO_KEY = "viewer_monochrome"


class ViewerWindow(QWidget):
    """Eigenes Fenster fuer den Viewer (zweiter Monitor)."""
    closing = Signal()

    def __init__(self, title: str):
        super().__init__(None, Qt.Window)
        self.setWindowTitle(title)
        QVBoxLayout(self).setContentsMargins(4, 4, 4, 4)

    def closeEvent(self, event) -> None:
        self.closing.emit()
        super().closeEvent(event)


class ViewerPanel(QWidget):
    """Leiste + Vorschau. ``sheet`` liefert Fundstellen-Navigation und Redline (TagsSheet).
    ``detached_changed(bool)``: Viewer ausgelagert (True) / zurueck im Hauptfenster (False) - das Blatt nutzt die Breite."""
    detached_changed = Signal(bool)

    def __init__(self, sheet, app_title: str):
        super().__init__()
        self.sheet, self.app_title = sheet, app_title
        self.preview = PdfPreview()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.strip = ToolStrip("PDF")
        s = self.strip
        s.add("fit", "Einpassen", "fit", self.preview.fit, "Ganze Seite zeigen (Doppelklick in die Vorschau)")
        s.add("zoom_in", "", "zoom_in", lambda: self.preview.zoom(1.25), "Vergrößern (Mausrad)")
        s.add("zoom_out", "", "zoom_out", lambda: self.preview.zoom(0.8), "Verkleinern (Mausrad)")
        s.add("rot_left", "", "undo", lambda: self.preview.rotate_view(-90), "Ansicht 90° nach links drehen")
        s.add("rot_right", "Drehen", "reload", lambda: self.preview.rotate_view(90), "Ansicht 90° nach rechts drehen")
        self.mono_button = s.add("mono", "Monochrom", "mono", self.set_monochrome,
                                 "PDF schwarz-weiß anzeigen (nur Ansicht, die PDF bleibt unverändert)", checkable=True)
        s.separator()
        self.page_prev = s.add("page_prev", "", "prev", lambda: self.preview.step_page(-1), "Vorherige Seite (Bild ↑)")
        self.page_label = QLabel("Seite –")
        s._layout.addWidget(self.page_label)
        self.page_next = s.add("page_next", "", "next", lambda: self.preview.step_page(1), "Nächste Seite (Bild ↓)")
        self.preview.page_changed.connect(self._page_changed)
        self._page_changed(0, 0)
        s.separator()
        s.add("prev", "", "prev", sheet.previous_occurrence, "Vorherige Fundstelle (Umschalt+F3)")
        s.add("next", "Fundstelle", "next", sheet.next_occurrence, "Nächste Fundstelle (F3, oder erneut auf den Tag klicken)")
        s.separator()
        s.add("redline", "Redline", "redline", sheet.win.redline_current, "Redline-PDF der gewählten PDF (sichtbare Tags)")
        # eigene zweite Zeile: die erste Leiste ist voll, sonst wuerde das Fenster noch breiter
        self.notes_strip = ToolStrip("Multi Tag")
        self.notes_button = self.notes_strip.add("notes", "Kommentare bearbeiten", "notes", sheet.toggle_notes,
                                  "Rote Multi-Tag-Einträge zeigen und mit der Maus verschieben. Die Positionen gelten für "
                                  "„Multi-Tag-PDF“; die PDF selbst bleibt unverändert.", checkable=True)
        self.preview.page_changed.connect(lambda *_a: sheet.refresh_notes())
        self.preview.note_moved.connect(sheet.note_moved)
        self.preview.note_reset.connect(sheet.note_reset)
        s.add("pdf_open", "Öffnen", "pdf_open", self.open_external, "PDF im Standardprogramm öffnen")
        s.stretch()
        self.monitor_button = s.add("monitor", "2. Monitor", "monitor", self.set_detached,
                                    "PDF-Viewer in eigenem Fenster auf dem zweiten Monitor zeigen", checkable=True)
        lay.addWidget(self.strip)
        self.notes_strip.stretch()
        lay.addWidget(self.notes_strip)
        lay.addWidget(self.preview, 1)

        # Platzhalter im Hauptfenster, solange der Viewer ausgelagert ist
        self.placeholder = QWidget()
        ph = QVBoxLayout(self.placeholder)
        ph.addStretch(1)
        note = QLabel("PDF-Viewer ist auf dem zweiten Monitor.")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet(NOTE_QSS)
        ph.addWidget(note)
        back = action_button("Viewer zurückholen", ButtonKind.SECONDARY)
        back.clicked.connect(lambda: self.monitor_button.setChecked(False))
        ph.addWidget(back, 0, Qt.AlignCenter)
        ph.addStretch(1)
        self.placeholder.hide()
        self._window: ViewerWindow | None = None
        self._host_layout = None                 # Layout im Hauptfenster, in dem der Viewer sitzt
        self.mono_button.setChecked(bool(last_paths.get_value(MONO_KEY, False)))

    def set_monochrome(self, on: bool) -> None:
        self.preview.set_monochrome(on)
        last_paths.set_value(MONO_KEY, bool(on))

    def _page_changed(self, page: int, count: int) -> None:
        self.page_label.setText(i18n.tr(f"Seite {page + 1} / {count}" if count else "Seite –"))
        self.page_label.setToolTip("Mehrseitige PDF: Seiten enthalten oft dieselbe Zeichnung (z. B. mit Markups); "
                                   "doppelte Tags werden je Seite gezählt." if count > 1 else "")
        self.page_prev.setEnabled(page > 0)
        self.page_next.setEnabled(page + 1 < count)

    def install(self, host_layout) -> None:
        """Im Hauptfenster einhaengen; gemerkte Wahl "2. Monitor" wiederherstellen."""
        self._host_layout = host_layout
        host_layout.addWidget(self, 1)
        host_layout.addWidget(self.placeholder, 1)
        if last_paths.get_value(STATE_KEY, False) and len(QGuiApplication.screens()) > 1:
            self.monitor_button.setChecked(True)

    def open_external(self) -> None:
        result = self.sheet.current_result()
        if result is not None:
            os.startfile(str(result.path))  # noqa: S606

    def set_detached(self, detached: bool) -> None:
        if detached and self._window is None:
            self._window = ViewerWindow(f"{self.app_title} – PDF-Viewer")
            self._window.closing.connect(lambda: self.monitor_button.setChecked(False))
            self._host_layout.removeWidget(self)
            self._window.layout().addWidget(self)
            self.placeholder.show()
            self._place_on_second_screen()
        elif not detached and self._window is not None:
            window, self._window = self._window, None
            window.layout().removeWidget(self)
            self.placeholder.hide()
            self._host_layout.insertWidget(0, self, 1)
            window.closing.disconnect()
            window.close()
            window.deleteLater()
        self.show()
        last_paths.set_value(STATE_KEY, bool(detached))
        self.detached_changed.emit(bool(detached))

    def _place_on_second_screen(self) -> None:
        own = self.sheet.window().screen()
        screens = QGuiApplication.screens()
        target = next((s for s in screens if s is not own), own)
        self._window.setGeometry(target.availableGeometry())
        self._window.showMaximized() if target is not own else self._window.show()
        self._window.raise_()

    def close_window(self) -> None:
        if self._window is not None:
            self._window.closing.disconnect()
            self._window.close()
