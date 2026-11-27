"""Export-Symbol in der linken oberen Tabellenecke und Export der sichtbaren Ansicht
(Muster: P3D XCHANGE 0.5.0 ``gui/table_export.py``). Exportiert wird, was die Tabelle gerade zeigt: sichtbare Spalten
(auch hinzugefuegte) in angezeigter Reihenfolge, ausgeblendete nicht, die Zeilen, die die Filter passieren, in der
angezeigten Sortierung - in Excel mit Kopffarbe, Spaltenbreiten, Zellfarben und Ausrichtung der Ansicht."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QMenu, QMessageBox, QTableView, QTableWidget,
                               QTableWidgetItem, QToolButton, QVBoxLayout)

from ..core.export import write_csv
from ..paths import display_path, exports_dir, file_timestamp
from . import appearance, last_paths
from .design import NOTE_QSS
from .icons import excel_icon


PREVIEW_ROWS = 500          # Vorschau zeigt hoechstens so viele Zeilen, exportiert werden alle
VIEW_TABLE_STYLE = "TableStyleLight1"                       # zurueckhaltend, damit die Farben der Ansicht wirken


def _visible(table: QTableView) -> tuple[list[int], list[int]]:
    """Sichtbare Spalten (angezeigte Reihenfolge) und Zeilen der Ansicht."""
    header = table.horizontalHeader()
    cols = [header.logicalIndex(v) for v in range(header.count()) if not header.isSectionHidden(header.logicalIndex(v))]
    rows = [r for r in range(table.model().rowCount())
            if not table.isRowHidden(r)]                         # ausgefilterte Zeilen (setRowHidden) gehoeren nicht dazu
    return cols, rows


def visible_table(table: QTableView) -> tuple[list[str], list[list]]:
    model = table.model()
    cols, shown = _visible(table)
    headers = [str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "") for c in cols]
    return headers, [[model.index(r, c).data(Qt.DisplayRole) for c in cols] for r in shown]


def _rgb(value) -> str | None:
    """Farbe einer Modellrolle (QBrush/QColor/Farbname) als ``RRGGBB``; ohne Farbe ``None``."""
    if value is None:
        return None
    if isinstance(value, QBrush):
        if value.style() == Qt.NoBrush:
            return None
        value = value.color()
    color = QColor(value)
    return color.name()[1:].upper() if color.isValid() else None


def view_style(table: QTableView) -> dict:
    """Aussehen der Ansicht: Kopffarben, Spaltenbreiten (Pixel) und je Zelle (Zeile, Spalte der Ausgabe) die
    abweichende Flaeche, Schriftfarbe und Ausrichtung."""
    model = table.model()
    cols, shown = _visible(table)
    cells = {}
    for out_row, r in enumerate(shown):
        for out_col, c in enumerate(cols):
            index = model.index(r, c)
            fill, font = _rgb(index.data(Qt.BackgroundRole)), _rgb(index.data(Qt.ForegroundRole))
            align, horizontal = index.data(Qt.TextAlignmentRole), ""
            if align is not None:
                bits = int(getattr(align, "value", align))
                if bits & Qt.AlignHCenter.value:
                    horizontal = "center"
                elif bits & Qt.AlignRight.value:
                    horizontal = "right"
            if fill or font or horizontal:
                cells[out_row, out_col] = (fill, font, horizontal)
    return {"header_fill": _rgb(appearance.header_color()), "header_font": _rgb("white"),
            "widths": [table.columnWidth(c) for c in cols], "cells": cells}


def apply_style(ws, style: dict) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    for name in ws.tables:
        ws.tables[name].tableStyleInfo.name = VIEW_TABLE_STYLE
    head_fill = PatternFill("solid", fgColor=style["header_fill"])
    head_font = Font(bold=True, color=style["header_font"])
    for cell in ws[1]:
        cell.fill, cell.font = head_fill, head_font
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for i, pixels in enumerate(style["widths"], start=1):       # Excel-Breite in Zeichen, ein Zeichen ca. 7 Pixel
        ws.column_dimensions[get_column_letter(i)].width = max(3.0, min(120.0, round(pixels / 7.0, 1)))
    fills, fonts, aligns = {}, {}, {}                           # Stilobjekte je Wert nur einmal anlegen
    for (r, c), (fill, font, horizontal) in style["cells"].items():
        cell = ws.cell(row=r + 2, column=c + 1)
        if fill:
            cell.fill = fills.get(fill) or fills.setdefault(fill, PatternFill("solid", fgColor=fill))
        if font:
            cell.font = fonts.get(font) or fonts.setdefault(font, Font(color=font))
        if horizontal:
            cell.alignment = aligns.get(horizontal) or aligns.setdefault(horizontal, Alignment(horizontal=horizontal))


def write_view(path: str, title: str, headers: list[str], rows: list[list], style: dict | None = None) -> None:
    if path.lower().endswith(".csv"):
        write_csv(path, headers, rows)
        return
    from openpyxl import Workbook

    from ..core.xlsx import write_table
    wb = Workbook()
    ws = wb.active
    ws.title = "".join(ch for ch in (title or "Tabelle") if ch not in "[]:*?/\\")[:31] or "Tabelle"
    write_table(ws, headers, rows, title or "Tabelle")       # Excel-Datentabelle, Spaltenbreite autofit
    if style is not None:
        apply_style(ws, style)                               # ... mit dem Aussehen der Ansicht
    wb.save(path)


def safe_name(text: str) -> str:
    return "".join(ch for ch in str(text) if ch not in '\\/:*?"<>|').strip() or "Tabelle"


def export_name(table: QTableView, title: str) -> str:
    """Dateiname ohne Endung: ``<Name>_<JJJJ-MM-TT_HH-MM>``. ``table.export_name`` (Funktion) liefert z. B. den PDF-Namen."""
    provider = getattr(table, "export_name", None)
    base = provider() if callable(provider) else ""
    return f"{safe_name(base or title)}_{file_timestamp()}"


def export_table_view(table: QTableView, title: str = "Tabelle") -> None:
    headers, rows = visible_table(table)
    if not headers:
        return
    path = last_paths.save_file(table, "Tabelle als Excel sichern", f"{export_name(table, title)}.xlsx",
                                "Excel (*.xlsx);;CSV (*.csv)", exports_dir())
    if not path:
        return
    write_view(path, title, headers, rows, None if path.lower().endswith(".csv") else view_style(table))
    QMessageBox.information(table, "Export", f"Gespeichert:\n{display_path(path)}\n\n{len(rows)} Zeile(n).")


class PreviewDialog(QDialog):
    """Vorschau des Excel-Exports: Spalten, Reihenfolge, Breiten und Farben wie in der Datei."""

    def __init__(self, table: QTableView, title: str, parent=None):
        super().__init__(parent or table.window())
        self.setWindowTitle(f"Vorschau – {title}")
        self.resize(1100, 640)
        headers, rows = visible_table(table)
        style = view_style(table)
        lay = QVBoxLayout(self)
        shown = rows[:PREVIEW_ROWS]
        note = QLabel(f"{len(rows)} Zeile(n), {len(headers)} Spalte(n)"
                      + (f" – Vorschau der ersten {PREVIEW_ROWS}" if len(rows) > PREVIEW_ROWS else ""))
        note.setStyleSheet(NOTE_QSS)
        lay.addWidget(note)
        view = self.view = QTableWidget(len(shown), len(headers))
        view.setHorizontalHeaderLabels(headers)
        view.setEditTriggers(QTableWidget.NoEditTriggers)
        view.horizontalHeader().setStyleSheet(appearance.plain_header_qss())
        for r, row in enumerate(shown):
            for c, value in enumerate(row):
                item = QTableWidgetItem("" if value is None else str(value))
                fill, font, _align = style["cells"].get((r, c), (None, None, ""))
                if fill:
                    item.setBackground(QColor(f"#{fill}"))
                if font:
                    item.setForeground(QColor(f"#{font}"))
                view.setItem(r, c, item)
        for c, width in enumerate(style["widths"]):
            view.setColumnWidth(c, max(40, width))
        lay.addWidget(view, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        buttons.button(QDialogButtonBox.Save).setText("Als Excel sichern …")
        buttons.button(QDialogButtonBox.Close).setText("Schließen")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)


def preview_table_view(table: QTableView, title: str = "Tabelle") -> None:
    """Vorschau zeigen; „Als Excel sichern“ fuehrt in den normalen Export."""
    if visible_table(table)[0] and PreviewDialog(table, title).exec() == QDialog.Accepted:
        export_table_view(table, title)


class _CornerPlacer(QObject):
    def __init__(self, table: QTableView, button: QToolButton):
        super().__init__(button)
        self.table, self.button = table, button
        for w in (table, table.verticalHeader(), table.horizontalHeader()):
            w.installEventFilter(self)
        self.place()

    def place(self) -> None:
        f = self.table.frameWidth()
        self.button.setGeometry(f, f, max(20, self.table.verticalHeader().width()),
                                max(20, self.table.horizontalHeader().height()))
        self.button.raise_()

    def eventFilter(self, obj, event) -> bool:
        if event.type() in (QEvent.Resize, QEvent.Show, QEvent.LayoutRequest, QEvent.Move):
            self.place()
        return False


def install_excel_corner(table: QTableView, title: str) -> QToolButton:
    button = QToolButton(table)
    button.setIcon(excel_icon())
    button.setAutoRaise(True)
    button.setCursor(Qt.PointingHandCursor)
    button.setToolTip("Tabelle als Excel sichern - wie angezeigt (sichtbare Spalten, Filter, Sortierung, Farben)\n"
                      "Dateiname: PDF-Name bzw. Tabellenname + Zeitstempel\nRechtsklick: Vorschau ansehen")
    button.setContextMenuPolicy(Qt.CustomContextMenu)

    def menu(pos) -> None:
        m = QMenu(button)
        m.addAction("Vorschau ansehen …", lambda: preview_table_view(table, title))
        m.addAction("Als Excel sichern …", lambda: export_table_view(table, title))
        m.exec(button.mapToGlobal(pos))

    button.customContextMenuRequested.connect(menu)
    button.clicked.connect(lambda _c=False: export_table_view(table, title))
    _CornerPlacer(table, button)
    return button
