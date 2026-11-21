"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). Symbole der Buttonleiste.

Vorrang haben PNG-Dateien aus ``assets/icons/<Schluessel>.png`` (1:1 nach der Excel-Vorlage; optional ``<Schluessel>_disabled.png``,
sonst wird eine ausgegraute Fassung berechnet). Fehlt eine Datei, zeichnet ``glyph_icon`` uebergangsweise ein Unicode-Zeichen.
Benoetigte Schluessel und Masse: ``assets/icons/README.md``."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

#: Schluessel -> Glyph
GLYPHS = {
    "start": "⌂", "project": "▤", "reload": "⟳", "reload_all": "⟳", "write": "⇪",
    "sort": "⇅", "search": "⌕", "freeze": "❄", "delta": "Δ", "rename": "✎", "delete": "✖",
    "export": "⇩", "import": "⇧", "roles": "⚿", "settings": "⚙", "other": "⇲",
    "header": "☰", "manual": "?", "syscheck": "✔", "connect": "☁", "report": "⎙", "license": "©", "about": "ⓘ",
    "undo": "↶", "wizard": "➤", "admin_open": "⚿", "admin_close": "⏶", "columns": "▥", "reports": "▦",
    "dm_remove": "✖", "dm_workcopy": "⊞", "dm_back": "⇲",
}


def glyph_icon(key: str, color: str = "#2F80ED", size: int = 32, disabled_color: str = "#A9B4C6") -> QIcon:
    icon = QIcon()
    glyph = GLYPHS.get(key, "●")
    for mode, hex_color in ((QIcon.Normal, color), (QIcon.Disabled, disabled_color)):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        font = QFont("Segoe UI Symbol")
        font.setPixelSize(int(size * 0.8))
        painter.setFont(font)
        painter.setPen(QColor(hex_color))
        painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, glyph)
        painter.end()
        icon.addPixmap(pixmap, mode)
    return icon


def filter_icon(color: str = "#0F5EA8", size: int = 16) -> QIcon:
    """Kleiner Trichter fuer aktive Spaltenfilter (PNG ``filter.png`` hat Vorrang, siehe ``assets/icons/README.md``)."""
    png = png_icon("filter")
    if png is not None:
        return png
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QPolygonF
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))
    s = size / 16.0
    painter.drawPolygon(QPolygonF([QPointF(2 * s, 3 * s), QPointF(14 * s, 3 * s), QPointF(9.5 * s, 8.5 * s),
                                   QPointF(9.5 * s, 13 * s), QPointF(6.5 * s, 11.5 * s), QPointF(6.5 * s, 8.5 * s)]))
    painter.end()
    return QIcon(pixmap)


def excel_icon(size: int = 18) -> QIcon:
    """Excel-Symbol (PNG ``excel.png`` hat Vorrang, siehe ``assets/icons/README.md``); sonst gruenes Blatt mit „X“."""
    png = png_icon("excel")
    if png is not None:
        return png
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("#1D6F42"))
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 2, 2)
    font = QFont("Segoe UI")
    font.setBold(True)
    font.setPixelSize(int(size * 0.65))
    painter.setFont(font)
    painter.setPen(QColor("white"))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter, "X")
    painter.end()
    return QIcon(pixmap)


ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"


def png_icon(key: str) -> QIcon | None:
    normal = ICON_DIR / f"{key}.png"
    if not normal.is_file():
        return None
    pixmap = QPixmap(str(normal))
    if pixmap.isNull():
        return None
    icon = QIcon()
    icon.addPixmap(pixmap, QIcon.Normal)
    disabled = ICON_DIR / f"{key}_disabled.png"
    if disabled.is_file() and not QPixmap(str(disabled)).isNull():
        icon.addPixmap(QPixmap(str(disabled)), QIcon.Disabled)
    else:                                                  # Qt berechnet die ausgegraute Fassung selbst
        icon.addPixmap(pixmap, QIcon.Disabled)
    return icon


def globe_icon(color: str = "#2F80ED", size: int = 32, disabled_color: str = "#A9B4C6") -> QIcon:
    """Sprachsymbol (Globus mit Laengen- und Breitenkreisen); PNG ``language.png`` hat Vorrang."""
    from PySide6.QtCore import QLineF, QRectF
    from PySide6.QtGui import QPen
    icon = QIcon()
    for mode, hex_color in ((QIcon.Normal, color), (QIcon.Disabled, disabled_color)):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(hex_color))
        pen.setWidthF(max(1.2, size / 16.0))
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        m = pen.widthF() / 2 + size * 0.06
        r = QRectF(m, m, size - 2 * m, size - 2 * m)
        painter.drawEllipse(r)                                           # Umriss
        painter.drawEllipse(QRectF(r.center().x() - r.width() * 0.22, r.top(), r.width() * 0.44, r.height()))  # Meridian
        painter.drawLine(QLineF(r.center().x(), r.top(), r.center().x(), r.bottom()))
        painter.drawLine(QLineF(r.left(), r.center().y(), r.right(), r.center().y()))                                  # Aequator
        for f in (0.27, 0.73):                                           # Breitenkreise
            y = r.top() + r.height() * f
            half = (r.width() / 2) * (1 - ((f - 0.5) * 2) ** 2) ** 0.5
            painter.drawLine(QLineF(r.center().x() - half, y, r.center().x() + half, y))
        painter.end()
        icon.addPixmap(pixmap, mode)
    return icon


#: Gezeichnete Platzhalter (statt Glyphe), solange kein PNG geliefert ist
DRAWN = {"language": globe_icon}


def ribbon_icon(key: str, size: int) -> QIcon:
    """PNG der Vorlage, sonst gezeichnetes Symbol bzw. Glyph-Platzhalter."""
    png = png_icon(key)
    if png is not None:
        return png
    if key in DRAWN:
        return DRAWN[key](size=size)
    return glyph_icon(key, size=size)
