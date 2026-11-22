"""Gut sichtbare Auswahl-Indikatoren fuer Checkboxen und Optionsfelder (app-weit).

Das Kit-Theme zeigt bei Optionsfeldern die Auswahl nicht und bei Checkboxen nur einen Haken ohne Kaestchen - der
Nutzer erkennt nicht, was gewaehlt ist. Hier: Kaestchen/Kreis mit Rahmen; gewaehlt = Akzentflaeche mit weissem Haken
bzw. weissem Punkt; Hover und deaktiviert unterscheidbar. Farben nur aus Kit-Palette (``LIGHT``) und Akzent.
Das Haken-Bild wird einmal gezeichnet und im Konfigurationsordner abgelegt (QSS braucht eine Bilddatei)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap

from main_gui_kit.theme import LIGHT

from ..paths import config_dir
from . import appearance
from .design import DISABLED

SIZE = 16


def _check_image() -> Path:
    path = config_dir() / "ui" / "check_white.png"
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        scale = 4                                            # hochaufgeloest zeichnen, Qt skaliert sauber herunter
        pix = QPixmap(SIZE * scale, SIZE * scale)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("white"), 2.2 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        line = QPainterPath(QPointF(3.6 * scale, 8.4 * scale))
        line.lineTo(6.8 * scale, 11.4 * scale)
        line.lineTo(12.4 * scale, 4.8 * scale)
        p.drawPath(line)
        p.end()
        pix.save(str(path))
    return path


def indicator_qss() -> str:
    accent = appearance.accent()
    hover = appearance.selection_color()
    check = _check_image().as_posix()
    frame = QColor(LIGHT.txt_muted).name()
    return f"""
QCheckBox, QRadioButton {{ spacing: 8px; }}
QCheckBox::indicator, QRadioButton::indicator {{ width: {SIZE}px; height: {SIZE}px; background: {LIGHT.card};
    border: 1px solid {frame}; }}
QCheckBox::indicator {{ border-radius: 3px; }}
QRadioButton::indicator {{ border-radius: {SIZE // 2 + 1}px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {accent}; background: {hover}; }}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; image: url("{check}"); }}
QRadioButton::indicator:checked {{ border: 1px solid {accent};
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 white, stop:0.32 white, stop:0.40 {accent}, stop:1 {accent}); }}
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{ background: {LIGHT.hdr}; border-color: {LIGHT.border}; }}
QCheckBox::indicator:checked:disabled {{ background: {LIGHT.border}; }}
QCheckBox:disabled, QRadioButton:disabled {{ color: {DISABLED}; }}
"""


def tip_button(text: str, kind, tip: str):
    """Kit-Knopf mit Tooltip. ``main_gui_kit.buttons.action_button`` nimmt als dritten Parameter ein Symbol, das vor
    den Text gesetzt wird - ein dort uebergebener Erklaerungstext stand deshalb auf dem Knopf."""
    from main_gui_kit.buttons import action_button
    button = action_button(text, kind)
    button.setToolTip(tip)
    return button
