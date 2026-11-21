"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). Erscheinungsbild (Einstellungen › Erscheinungsbild): Akzentfarbe, Farbe geänderter Zellen - gilt für alle Blätter."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor

DEFAULT_ACCENT = "#0F5EA8"
DEFAULT_DIRTY = "#FFF2CC"
ACCENT_CHOICES = ["#0F5EA8", "#1B6B5A", "#2E7D32", "#6A1B9A", "#AD1457", "#C62828", "#E65100", "#37474F", "#00838F", "#5D4037"]

_state = {"accent": DEFAULT_ACCENT}


def configure(settings: dict | None) -> None:
    """Aus ``config.extra['Erscheinungsbild']`` uebernehmen."""
    settings = settings or {}
    accent = str(settings.get("Akzent") or DEFAULT_ACCENT)
    _state["accent"] = accent if QColor(accent).isValid() else DEFAULT_ACCENT


def accent() -> str:
    return _state["accent"]


def accent_dark() -> str:
    color = QColor(_state["accent"]).darker(135)
    return color.name().upper()


ORIGINAL_HEADER = "#1F4E79"          # Tabellenkopf der Excel-Vorlage (Standard-Akzent)
ORIGINAL_HEADER_LINE = "#2F6AA3"


def header_color() -> str:
    return ORIGINAL_HEADER if _state["accent"].upper() == DEFAULT_ACCENT else accent_dark()


def header_line() -> str:
    return ORIGINAL_HEADER_LINE if _state["accent"].upper() == DEFAULT_ACCENT else accent()


def header_qss() -> str:
    """Tabellenkopf in der Akzentfarbe (Standard: Farbe der Vorlage); Kit-Tabellen mit Filterzeile behalten den Text im oberen Teil."""
    from .sheet import _filter_height
    return (f"QHeaderView::section {{ background: {header_color()}; color: white; border: none; border-right: 1px solid {header_line()}; "
            f"padding-left: 6px; padding-bottom: {_filter_height()}px; }}")


def plain_header_qss() -> str:
    return (f"QHeaderView::section {{ background: {header_color()}; color: white; border: none; border-right: 1px solid {header_line()}; padding: 5px 6px; }}")


def selection_color() -> str:
    """Helle Auswahlfarbe (Akzent stark aufgehellt), damit dunkle Schrift in markierten Zellen lesbar bleibt."""
    base = QColor(_state["accent"])
    mix = 0.78
    return QColor(round(base.red() * (1 - mix) + 255 * mix), round(base.green() * (1 - mix) + 255 * mix),
                  round(base.blue() * (1 - mix) + 255 * mix)).name().upper()


def selection_qss() -> str:
    from .design import TEXT
    return (f"QTableView, QTreeView, QListView, QTableWidget, QTreeWidget, QListWidget "
            f"{{ selection-background-color: {selection_color()}; selection-color: {TEXT}; }}")


def tab_button_qss() -> str:
    """Aktiver Reiter (Blattregister) sieht aus wie ein gedrueckter Button: Akzentflaeche, weisse Schrift."""
    return (f"QTabBar::tab:selected {{ background: {accent()}; color: white; font-weight: 600; border-radius: 3px; }}")


def app_qss() -> str:
    """Zusatz-Stylesheet fuer das Hauptfenster: Akzentfarbe fuer Kit-Buttons und deutlich graue deaktivierte Buttons.

    Das Kit faerbt ``QPushButton[kind=...]`` mit hoeherer Spezifitaet als ``:disabled``; ohne diese Regel sehen deaktivierte
    Buttons aktiv aus."""
    from .design import BORDER, DISABLED
    qss = [f'QPushButton[kind]:disabled {{ background: {BORDER}; color: {DISABLED}; border: 1px solid {BORDER}; }}',
           selection_qss(), tab_button_qss()]
    if _state["accent"].upper() != DEFAULT_ACCENT:
        dark = accent_dark()
        for kind in ("primary", "secondary", "process", "success", "warning", "danger"):
            qss.append(f'QPushButton[kind="{kind}"]:enabled {{ background: {accent()}; color: white; }} '
                       f'QPushButton[kind="{kind}"]:enabled:hover {{ background: {dark}; }}')
    return " ".join(qss)
