"""Leiste mit Tab-Buttons direkt ueber Tabelle und PDF-Viewer (schnell erreichbare Funktionen des Bereichs).

Symbole wie im Menueband (``icons.ribbon_icon``; PNG hat Vorrang, sonst Glyph). Die Glyphen fuer die zusaetzlichen
Schluessel dieses Tools werden hier ergaenzt - ``icons.py`` (Kopie aus P3D XCHANGE) bleibt unveraendert.
Farben nur aus der Kit-Palette (``LIGHT``) und dem Akzent (``appearance``)."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton

from main_gui_kit.theme import LIGHT

from . import appearance, icons

icons.GLYPHS.update({
    "zoom_in": "⊕", "zoom_out": "⊖", "fit": "⤢", "prev": "◀", "next": "▶", "monitor": "⧉", "dock": "⊟",
    "pdf_open": "⎘", "redline": "✎", "duplicates": "⚑", "filter_reset": "⊘", "review": "➤", "folder": "▤",
    "files": "⇧", "scan": "⟳", "excel_out": "⇩", "csv_out": "⇩", "info": "ⓘ", "help": "?", "pipe": "═", "mono": "◐",
    "project_mode": "◉", "defs": "☷", "deviations": "✗",
    # 1.0.43: Importspalten ein/aus, Abgleich, Dateiliste ein-/ausklappen
    "link_cols": "⇄", "match": "⇅", "fold": "⏶", "unfold": "⏷",
})


def _qss() -> str:
    accent = appearance.accent()
    return (f"#ToolStrip {{ background: {LIGHT.hdr}; border: 1px solid {LIGHT.border}; border-radius: 3px; }}"
            f"#ToolStrip QLabel {{ background: transparent; color: {LIGHT.txt_muted}; padding: 0 4px; }}"
            f"#ToolStrip QToolButton {{ background: {LIGHT.card}; border: 1px solid {LIGHT.border}; border-radius: 3px;"
            f" padding: 2px 8px; color: {LIGHT.txt}; }}"
            f"#ToolStrip QToolButton:hover {{ background: {appearance.selection_color()}; }}"
            f"#ToolStrip QToolButton:checked {{ background: {accent}; border-color: {accent}; color: white; }}"
            f"#ToolStrip QToolButton:disabled {{ color: #A9B4C6; }}")


class ToolStrip(QFrame):
    def __init__(self, caption: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("ToolStrip")
        self.setStyleSheet(_qss())
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 3, 4, 3)
        self._layout.setSpacing(4)
        if caption:
            self._layout.addWidget(QLabel(caption))
        self.buttons: dict[str, QToolButton] = {}

    def add(self, key: str, text: str, icon_key: str, slot: Callable, tip: str = "", *, checkable: bool = False,
            icon=None) -> QToolButton:
        button = QToolButton()
        button.setIcon(icon if icon is not None else icons.ribbon_icon(icon_key, 16))
        button.setIconSize(QSize(16, 16))
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon if text else Qt.ToolButtonIconOnly)
        button.setToolTip(tip or text)
        button.setCursor(Qt.PointingHandCursor)
        button.setCheckable(checkable)
        if checkable:
            button.toggled.connect(slot)
        else:
            button.clicked.connect(lambda _c=False: slot())
        self._layout.addWidget(button)
        self.buttons[key] = button
        return button

    def separator(self) -> None:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet(f"color: {LIGHT.border};")
        self._layout.addWidget(line)

    def stretch(self) -> None:
        self._layout.addStretch(1)
