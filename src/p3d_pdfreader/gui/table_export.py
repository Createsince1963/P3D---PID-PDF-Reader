"""Export-Symbol in der linken oberen Tabellenecke und Export der sichtbaren Ansicht
(Muster: P3D XCHANGE 0.5.0 ``gui/table_export.py``). Exportiert werden sichtbare Spalten in angezeigter Reihenfolge und
die Zeilen, die die Filter passieren."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QMessageBox, QTableView, QToolButton

from ..core.export import write_csv
from ..paths import display_path, exports_dir, file_timestamp
from . import last_paths
from .icons import excel_icon


def visible_table(table: QTableView) -> tuple[list[str], list[list]]:
    model, header = table.model(), table.horizontalHeader()
    cols = [header.logicalIndex(v) for v in range(header.count()) if not header.isSectionHidden(header.logicalIndex(v))]
    headers = [str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "") for c in cols]
    rows = [[model.index(r, c).data(Qt.DisplayRole) for c in cols] for r in range(model.rowCount())]
    return headers, rows


def write_view(path: str, title: str, headers: list[str], rows: list[list]) -> None:
    if path.lower().endswith(".csv"):
        write_csv(path, headers, rows)
        return
    from openpyxl import Workbook

    from ..core.xlsx import write_table
    wb = Workbook()
    ws = wb.active
    ws.title = "".join(ch for ch in (title or "Tabelle") if ch not in "[]:*?/\\")[:31] or "Tabelle"
    write_table(ws, headers, rows, title or "Tabelle")       # Excel-Datentabelle, Spaltenbreite autofit
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
    write_view(path, title, headers, rows)
    QMessageBox.information(table, "Export", f"Gespeichert:\n{display_path(path)}\n\n{len(rows)} Zeile(n).")


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
    button.setToolTip("Tabelle als Excel sichern (sichtbare Spalten und gefilterte Zeilen)\n"
                      "Dateiname: PDF-Name bzw. Tabellenname + Zeitstempel")
    button.clicked.connect(lambda _c=False: export_table_view(table, title))
    _CornerPlacer(table, button)
    return button
