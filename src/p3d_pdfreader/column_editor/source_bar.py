"""Collapsible source bar for the tile editor: more room for the tiles and the table.

Collapsed (default in tile mode): name, source type, app area, rows, columns, fingerprint and lock status in one line.
Expanded: the owner's full source widgets (folders, checksums, notes). The expanded state is a view state only; it is
never written to a view profile.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QWidget

from .source_summary import SourceSummary


class SourceBar(QFrame):
    expandedChanged = Signal(bool)
    collapsedChanged = Signal(bool)       # is_collapsed changed (also when tile mode switches on / off): owners fold more of their header

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._details: list[QWidget] = []
        self._active = False
        self._expanded = False
        self._was_collapsed = False
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 3, 6, 3)
        self.label = QLabel("")
        self.label.setTextFormat(Qt.PlainText)
        self.label.setProperty("role", "muted")
        self.label.setWordWrap(False)
        self.btn = QToolButton()
        self.btn.setAutoRaise(True)
        self.btn.setCheckable(True)
        self.btn.setToolTip("Show or hide the full source details")
        self.btn.toggled.connect(self.set_expanded)
        lay.addWidget(self.label, 1)
        lay.addWidget(self.btn)
        self._sync()

    def attach(self, *widgets: QWidget) -> None:
        """Widgets that show the full source details while the bar is expanded (or tile mode is off)."""
        self._details = list(widgets)
        self._sync()

    def set_summary(self, s: SourceSummary) -> None:
        text = "   ·   ".join(s.parts())
        self.label.setText(text)
        self.label.setToolTip(text)
        self.label.setStyleSheet("" if s.fingerprint_ok else "color:#b03a2e;")

    def set_active(self, on: bool) -> None:
        """Tile mode on: show the bar, collapsed. Tile mode off: bar hidden, details back as before."""
        if on and not self._active:
            self._expanded = False
        self._active = on
        self._sync()

    def set_expanded(self, on: bool) -> None:
        if on != self._expanded:
            self._expanded = on
            self._sync()
            self.expandedChanged.emit(on)

    @property
    def is_collapsed(self) -> bool:
        return self._active and not self._expanded

    def _sync(self) -> None:
        self.setVisible(self._active)
        self.btn.blockSignals(True)
        self.btn.setChecked(self._expanded)
        self.btn.blockSignals(False)
        self.btn.setText("Collapse ▲" if self._expanded else "Expand ▼")
        show = (not self._active) or self._expanded
        for w in self._details:
            w.setVisible(show)
        if self.is_collapsed != self._was_collapsed:
            self._was_collapsed = self.is_collapsed
            self.collapsedChanged.emit(self._was_collapsed)
