"""Hauptfenster im Aufbau von P3D XCHANGE: Kopfband, Menueband (Ribbon) mit Gruppen, Blaetter als schliessbare Reiter,
je Blatt ein Blattkopf (Titel, Untertitel, Band mit Beschriftung/Wert, Akzentlinie) und ein Fortschrittsdialog beim Scan.

Blatt "PID-Tags": oben Dateien (eine Zeile je PDF), links unten Tags der gewaehlten PDF, rechts Seitenvorschau.
Blatt "Alle Tags": Tags aller gescannten PDFs. Jede Tabelle: Kit-Standard (Spaltenfilter, Sortierung, Zoom, gemerkte
Ansicht), dunkelblauer Tabellenkopf wie in XCHANGE, TableAdminBar fuer benannte Ansichten, Excel-Symbol in der Ecke."""
from __future__ import annotations

import os
from contextlib import nullcontext
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QThread, QTimer
from PySide6.QtGui import QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu,
                               QMessageBox, QSplitter, QStatusBar, QStyledItemDelegate, QTabBar, QTableView,
                               QTabWidget, QVBoxLayout, QWidget)

from main_gui_kit.branding import HeaderBanner
from main_gui_kit.buttons import ButtonKind, action_button
from main_gui_kit.preview import DataPreviewDialog
from main_gui_kit.tables import (MultiColumnFilterProxy, TableAdminBar, TableDataModel, configure_table_view,
                                 table_zoom_slider)
from main_gui_kit.theme import LIGHT, ThemeManager

from .. import i18n, paths
from ..constants import APP_NAME
from ..core import export, redline, review
from ..core.extract import PdfResult
from ..core.project_defs import CHECK_HEADERS, ProjectDB, is_fault_status
from ..core.review_store import CHANGE_VALUES, EDIT_FIELDS, FIELDS, REVIEW_VALUES, ReviewStore, status_hits
from . import appearance, icons, last_paths, table_views
from .design import NOTE_QSS
from .paths_dialog import PathsDialog, open_in_explorer
from . import project_dialog, web_control
from .controls import indicator_qss
from .data_link_ui import LinkController
from .icons import excel_icon
from .progress import ProgressDialog, progress_task
from .review_dialog import ReviewDialog
from .ribbon import Ribbon
from .ribbon_fold import RibbonFold
from .ribbon_heads import apply_group_heads
from .sheet import SheetHeader, configure_subtabs, mark_active_filters, table_header_qss
from .table_export import export_table_view, install_excel_corner
from .table_menu import install_table_menus
from .toolstrip import ToolStrip
from .viewer_panel import ViewerPanel
from .worker import ScanWorker

PIPES_KEY = "read_pipe_lines"       # config/state.json
LAYER_TIP = ("Redline-PDF: Rahmen, Pos.-Nr. und Kommentare auf eine eigene PDF-Ebene „Review_TT.MM.JJJJ“ (Datum der "
             "Erstellung) legen – in Acrobat, PDF-XChange oder Bluebeam unter „Ebenen“ ein- und ausblendbar. "
             "Gilt auch für Bulk, Web-Server und Offline-Bericht.")
PIPES_TIP = ("Rohrleitungsnummern (z. B. TFHR_SS01_001_1\") als Typ „Rohrleitung“ in die Tag-Liste übernehmen – "
             "waagerecht und senkrecht beschriftet. Umschalten liest die PDFs neu ein.")

FILE_COLS = ["PDF", "Zeichnungsnr.", "Erstellt (PDF)", "Ersteller", "Checked", "Rev", "Rev-Datum", "Rev-Text",
             "Plot-Benutzer", "Anzahl Tags", "Fehler"]
# FIELDS: Review, Änderung, Neuer Wert, Bemerkung, WPO, Datum, User; CHECK_HEADERS: Projekt-Prüfung, Projekt-Hinweis
# (nur im Projektmodus sichtbar)
# SCAN_COLS: Schriftfeld-Werte der PDF, hinten angefuegt; nur sichtbar mit "Aus PDF-Scan übernehmen"
SCAN_COLS = ["Ersteller", "Checked", "Rev", "Rev-Datum", "Rev-Text"]
TAG_COLS = ["Typ", "Tag", "Anzahl", "Seiten", *CHECK_HEADERS, *FIELDS, *SCAN_COLS]
FIRST_FIELD = TAG_COLS.index(FIELDS[0])
CHECK_COL = TAG_COLS.index(CHECK_HEADERS[0])
SCAN_COL = len(TAG_COLS) - len(SCAN_COLS)
SCAN_KEY = "tags_scan_fields"       # config/state.json
FOLD_KEY = "ribbon_collapsed"       # config/state.json: eingeklappte Menueband-Gruppen
SCAN_TIP = ("Aus PDF-Scan übernehmen: Ersteller, Checked, Rev, Rev-Datum und Rev-Text aus dem Schriftfeld der PDF als "
            "Spalten hinten an die Tag-Tabelle anfügen (bleibt eingeschaltet).")
AUTOFILL_TIP = ("Autofill OK: bei allen Tags mit Review „OK“ (oder leerem Review und Projekt-Prüfung „OK“) Review = OK, "
                "User und Datum (heute, ohne Uhrzeit) setzen; leeres WPO bekommt den Checked-Wert aus dem Schriftfeld. "
                "Danach Speichern.")
ALL_TAG_COLS = ["PDF", "Zeichnungsnr.", "Typ", "Tag", "Anzahl", *CHECK_HEADERS]
ALL_CHECK_COL = ALL_TAG_COLS.index(CHECK_HEADERS[0])
VIEWER_SPLIT = (500, 800)           # Standardteilung Tag-Tabelle : Viewer im Hauptfenster
DATA_LINK_TIP = ("Datenlink: Excel-Liste (z. B. Instrumenten-Gesamtliste) importieren, im Kachel-Editor prüfen und "
                 "bearbeiten, Datenlink 1 (Zeichnung) und 2 (Tag) setzen. In den Tabellen per Rechtsklick auf den "
                 "Spaltenkopf das Datenlink-Feld wählen (Kopf dunkelgrün) – dann erscheinen die Listenspalten.")
PROJECT_MODE_KEY, PROJECT_DB_KEY = "project_mode", "project_db"     # config/state.json
PROJECT_TIP = ("Projektmodus: Tags werden gegen die Projektdefinitionen geprüft (Codelisten und Tag-Strukturen wie in "
               "P3D Tag Compliance). Aus = Standardmodus ohne Projektdefinitionen.")


def file_row(r: list) -> list:
    """Zeile der Dateiliste (``FILE_COLS``) aus einer Zeile von ``export.file_rows``."""
    return [r[0], r[1], r[2], r[3], r[5], r[7], r[8], r[9], r[11], r[15], r[17]]


def scan_values(result: PdfResult) -> list[str]:
    """Schriftfeld-Werte der PDF in der Reihenfolge ``SCAN_COLS`` (wie in der Dateiliste)."""
    return [result.author_display, result.checked, result.revision, result.revision_date, result.revision_text]


class DuplicateModel(TableDataModel):
    """Kit-Tabellenmodell; Zeilen mit Anzahl > 1 (doppelte Tags) bekommen einen gelben Hintergrund."""

    def __init__(self, headers, rows, count_col: int | None, parent=None):
        super().__init__(headers, rows, parent)
        self.count_col = count_col
        self._brush = QBrush(QColor(appearance.DEFAULT_DIRTY))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Spaltenkoepfe in der Oberflaechensprache (intern bleiben die deutschen Namen)."""
        value = super().headerData(section, orientation, role)
        if orientation == Qt.Horizontal and role in (Qt.DisplayRole, Qt.ToolTipRole) and isinstance(value, str):
            return i18n.tr(value)
        return value

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundRole and self.count_col is not None and index.isValid():
            try:
                if int(self.rows[index.row()][self.count_col]) > 1:
                    return self._brush
            except (TypeError, ValueError):
                pass
            return None
        if role == Qt.ToolTipRole and self.count_col is not None and index.isValid():
            value = self.rows[index.row()][self.count_col]
            if isinstance(value, int) and value > 1:
                return f"Doppelter Tag: {value}× in der PDF"
        return super().data(index, role)


class ReviewModel(DuplicateModel):
    """Tag-Tabelle mit Review-Spalten. Im Bearbeiten-Modus sind die Spalten ``EDIT_FIELDS`` editierbar; jede Aenderung
    geht in den ``ReviewStore`` der PDF, der Datum und User (letzte zwei Spalten) automatisch setzt."""

    def __init__(self, headers, rows, count_col, parent=None, *, store=None, edit_mode=False, first_field=4):
        super().__init__(headers, rows, count_col, parent)
        self.store, self.edit_mode, self.first_field = store, edit_mode, first_field
        self._edit_cols = {first_field + i for i in range(len(EDIT_FIELDS))}
        self._edit_brush = QBrush(QColor(appearance.selection_color()))

    def flags(self, index):
        flags = super().flags(index)
        if self.edit_mode and self.store is not None and index.column() in self._edit_cols:
            flags |= Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.EditRole and index.isValid():
            return self.rows[index.row()][index.column()]
        if (role == Qt.BackgroundRole and self.edit_mode and index.isValid() and index.column() in self._edit_cols
                and not self._is_duplicate(index.row())):
            return self._edit_brush                      # editierbare Zellen im Bearbeiten-Modus hervorheben
        return super().data(index, role)

    def _is_duplicate(self, row: int) -> bool:
        try:
            return int(self.rows[row][self.count_col]) > 1
        except (TypeError, ValueError):
            return False

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not (self.flags(index) & Qt.ItemIsEditable):
            return False
        row = self.rows[index.row()]
        field = EDIT_FIELDS[index.column() - self.first_field]
        values = self.store.set(row[0], row[1], field, str(value or "").strip())
        row[self.first_field:self.first_field + len(FIELDS)] = values
        self.dataChanged.emit(self.index(index.row(), 0), self.index(index.row(), self.columnCount() - 1))
        return True


class ChoiceDelegate(QStyledItemDelegate):
    """Auswahlliste als Editor (Review: feste Werte; Aenderung: Vorschlaege, frei ergaenzbar)."""

    def __init__(self, values: list[str], editable: bool, parent=None):
        super().__init__(parent)
        self.values, self.editable = values, editable

    def createEditor(self, parent, option, index):
        box = QComboBox(parent)
        box.setEditable(self.editable)
        box.addItems(self.values)
        return box

    def setEditorData(self, editor, index):
        value = str(index.data(Qt.EditRole) or "")
        if editor.findText(value) < 0 and value:
            editor.addItem(value)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


def add_subtab_off_menu(table: QTableView) -> None:
    """Rechtsklick auf die Subtab-Leiste: "Subtabs aus" (zusaetzlich zum Eintrag im Spaltenkopf-Menue des Kits)."""
    bar = getattr(table, "_shared_subtab_bar", None)
    if bar is None:
        return

    def menu(widget, pos):
        m = QMenu(widget)
        off = m.addAction("Subtabs aus (zurück zur Gesamttabelle)")
        off.setEnabled(bool(bar.is_active))
        if m.exec(widget.mapToGlobal(pos)) is off:
            bar.deactivate()

    for widget in (bar, bar.tabbar, bar.all_button):
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(lambda pos, w=widget: menu(w, pos))
        widget.setToolTip("Rechtsklick: Subtabs aus")


class DataTable(QWidget):
    """Tabelle nach Kit-Standard mit Blattfilter, Tabellenverwaltung (Ansichten) und Zoom."""

    def __init__(self, key: str, title: str, headers: list[str], parent=None, count_col: int | None = None,
                 model_factory=None):
        super().__init__(parent)
        self.key, self.title, self.headers, self.count_col = key, title, headers, count_col
        self.model_factory = model_factory or (lambda h, rows, c, p: DuplicateModel(h, rows, c, p))
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        top = QHBoxLayout()
        caption = QLabel(title)
        caption.setStyleSheet("font-weight: 600;")
        top.addWidget(caption)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("In dieser Tabelle filtern …")
        self.filter.setClearButtonEnabled(True)
        top.addWidget(self.filter, 1)
        self.count = QLabel()
        self.count.setStyleSheet(NOTE_QSS)
        top.addWidget(self.count)
        lay.addLayout(top)
        self.proxy = MultiColumnFilterProxy(self)
        self.proxy.setSourceModel(self.model_factory(headers, [], count_col, self))
        self.table = QTableView()
        self.table.layout_key = key
        self.table.setModel(self.proxy)
        configure_table_view(self.table)
        self.table.horizontalHeader().setStyleSheet(table_header_qss())
        mark_active_filters(self.table.horizontalHeader())
        configure_subtabs(self.table)
        add_subtab_off_menu(self.table)
        excel = install_excel_corner(self.table, title)
        # Rechtsklick wie P3D XCHANGE: Zellenmenue (Kopieren, Filtern, Spalten …) und Excel-Symbol > Spalten …
        install_table_menus(self.table, excel, on_clear_all=self.clear_filters, on_filter=self._count,
                            on_export=lambda: export_table_view(self.table, title))
        lay.addWidget(self.table, 1)
        bottom = QHBoxLayout()
        self.admin = TableAdminBar(self.table, table_views.store(), "named|" + key)
        bottom.addWidget(self.admin, 1)
        bottom.addWidget(table_zoom_slider(self.table))
        lay.addLayout(bottom)
        self.filter.textChanged.connect(self._filter)
        self._count()

    def set_rows(self, rows: list[list]) -> None:
        self.proxy.setSourceModel(self.model_factory(self.headers, rows, self.count_col, self))
        header = self.table.horizontalHeader()
        if hasattr(header, "bind_model"):
            header.bind_model()
            mark_active_filters(header)
        self.proxy.set_global_filter(self.filter.text())
        self._count()

    def clear_filters(self) -> None:
        """Blattfilter, Spaltenfilter (Text) und Wertauswahl der Spalten zuruecksetzen."""
        self.filter.clear()
        for editor in getattr(self.table.horizontalHeader(), "editors", []) or []:
            editor.clear()
        self.proxy.column_filters.clear()
        self.proxy.value_filters.clear()
        self.proxy.set_global_filter("")
        self._count()

    def _filter(self, text: str) -> None:
        self.proxy.set_global_filter(text)
        self._count()

    def _count(self) -> None:
        total = self.proxy.sourceModel().rowCount() if self.proxy.sourceModel() else 0
        self.count.setText(i18n.tr(f"{self.proxy.rowCount()} / {total} Zeilen"))

    def source_row(self, index: QModelIndex) -> int:
        return self.proxy.mapToSource(index).row() if index.isValid() else -1

    def rows(self) -> list[list]:
        model = self.proxy.sourceModel()
        return [list(r) for r in model.rows] if model else []


class Sheet(QWidget):
    """Blatt mit Blattkopf wie in XCHANGE."""

    def __init__(self, title: str, subtitle: str, closable: bool):
        super().__init__()
        self.title, self.subtitle = title, subtitle
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.header = SheetHeader(closable=closable)
        lay.addWidget(self.header)
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(10, 8, 10, 6)
        lay.addWidget(self.body, 1)
        self.set_band("")

    def set_band(self, band: str) -> None:
        self.header.set_lines([i18n.tr(self.title), i18n.tr(self.subtitle)] + ([band] if band else []))


class TagsSheet(Sheet):
    def __init__(self, window: "MainWindow"):
        super().__init__("PID-Tags", "Plant-3D-PDF-Plots: Dateien, Tags je PDF und Seitenvorschau", closable=False)
        self.win = window
        self._switching = False
        vsplit = QSplitter(Qt.Vertical)
        self.files = DataTable("files", "Dateien", FILE_COLS)
        strip = ToolStrip("Dateien")
        strip.add("mark_all", "Alle markieren", "columns", self.files.table.selectAll, "Alle PDFs der Liste markieren")
        strip.add("review", "Review markierte …", "review", window.review,
                  "Markierte PDFs prüfen: Redline-PDF, Excel je PDF, Gesamt-Excel")
        strip.add("excel_files", "Excel", "excel", lambda: export_table_view(self.files.table, "PID_Dateien"),
                  "Dateiliste als Excel sichern", icon=excel_icon(16))
        strip.stretch()
        self.files.layout().insertWidget(1, strip)
        vsplit.addWidget(self.files)
        hsplit = QSplitter(Qt.Horizontal)
        self.store: ReviewStore | None = None          # Review-Eintraege der gewaehlten PDF
        self._store_result: PdfResult | None = None
        self.edit_mode = False
        self.tags = DataTable("tags", "Tags der gewählten PDF", TAG_COLS, count_col=2, model_factory=lambda h, rows, c, p:
                              ReviewModel(h, rows, c, p, store=self.store, edit_mode=self.edit_mode,
                                          first_field=FIRST_FIELD))
        self.tags.table.setItemDelegateForColumn(FIRST_FIELD, ChoiceDelegate(REVIEW_VALUES, False, self.tags.table))
        self.tags.table.setItemDelegateForColumn(FIRST_FIELD + 1, ChoiceDelegate(CHANGE_VALUES, True, self.tags.table))
        strip = ToolStrip("Tags")
        self.scan_button = strip.add("scan_fields", "Aus PDF-Scan übernehmen", "import", self._toggle_scan_fields,
                                     SCAN_TIP, checkable=True)
        self.scan_button.setChecked(bool(last_paths.get_value(SCAN_KEY, False)))
        self.autofill_button = strip.add("autofill", "Autofill OK", "syscheck", self.autofill_ok, AUTOFILL_TIP)
        self.edit_button = strip.add("edit", "Bearbeiten", "rename", self.set_edit_mode,
                                     "Bearbeiten-Modus: Review, Änderung, Neuer Wert, Bemerkung, WPO eintragen "
                                     "(Datum und User werden automatisch gesetzt)", checkable=True)
        self.save_button = strip.add("save", "Speichern", "write", self.save_review,
                                     "Review-Einträge dieser PDF speichern (Strg+S)")
        self.save_button.setEnabled(False)
        strip.separator()
        self.dup_button = strip.add("duplicates", "Nur doppelte", "duplicates", self._only_duplicates,
                                    "Nur Tags zeigen, die mehrfach in der PDF vorkommen (gelb)", checkable=True)
        self.fault_button = strip.add("deviations", "Nur Abweichungen", "deviations", self._only_duplicates,
                                      "Projektmodus: nur Tags mit Befund zeigen (Code unvollständig, Code fehlt, Regelfehler)",
                                      checkable=True)
        strip.add("filter_reset", "Filter zurücksetzen", "filter_reset", self.reset_tag_filters)
        strip.separator()
        strip.add("prev", "", "prev", self.previous_occurrence, "Vorherige Fundstelle (Umschalt+F3)")
        strip.add("next", "Fundstelle", "next", self.next_occurrence, "Nächste Fundstelle (F3)")
        strip.separator()
        strip.add("excel_tags", "Excel", "excel", lambda: export_table_view(self.tags.table, "Tags"),
                  "Tags der PDF als Excel sichern (Name: PDF + Zeitstempel)", icon=excel_icon(16))
        strip.add("redline", "Redline", "redline", window.redline_current, "Redline-PDF mit den sichtbaren Tags")
        strip.stretch()
        self.tags.layout().insertWidget(1, strip)
        hsplit.addWidget(self.tags)
        viewer_host = QWidget()
        host_layout = QVBoxLayout(viewer_host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer = ViewerPanel(self, APP_NAME)
        self.preview = self.viewer.preview
        hsplit.addWidget(viewer_host)
        self._viewer_host_layout = host_layout
        self._hsplit, self._viewer_host = hsplit, viewer_host
        hsplit.setStretchFactor(0, 2)
        hsplit.setStretchFactor(1, 3)
        hsplit.setSizes(list(VIEWER_SPLIT))
        # Viewer auf dem 2. Monitor: Hinweis + "Viewer zurückholen" oberhalb der Tag-Tabelle (rechts in der Kopfzeile)
        self.viewer_away = QWidget()
        away = QHBoxLayout(self.viewer_away)
        away.setContentsMargins(8, 0, 0, 0)
        note = QLabel("PDF-Viewer ist auf dem zweiten Monitor.")
        note.setStyleSheet(NOTE_QSS)
        away.addWidget(note)
        back = action_button("Viewer zurückholen", ButtonKind.SECONDARY)
        back.clicked.connect(lambda: self.viewer.monitor_button.setChecked(False))
        away.addWidget(back)
        self.viewer_away.hide()
        self.tags.layout().itemAt(0).layout().addWidget(self.viewer_away)
        vsplit.addWidget(hsplit)
        vsplit.setSizes([300, 520])
        self.body_layout.addWidget(vsplit, 1)

        self.files.table.export_name = lambda: "PID_Dateien"
        self.tags.table.export_name = self._tags_export_name
        self.files.table.selectionModel().currentRowChanged.connect(self._file_changed)
        # Tag-Navigation: neuer Tag (Klick, Pfeiltasten) -> markieren und zoomen; bei mehreren Fundstellen zuerst die
        # ganze Seite mit allen nummerierten Fundstellen, jeder weitere Klick auf denselben Tag (oder F3) -> naechste.
        self._hit = None            # aktuell gewaehlter Tag
        self._focus: int | None = None
        self._fresh_selection = False
        self.tags.table.selectionModel().currentRowChanged.connect(lambda cur, _prev: self._tag_selected(cur))
        self.tags.table.clicked.connect(self._tag_clicked)
        for keys, slot in (("F3", self.next_occurrence), ("Shift+F3", self.previous_occurrence)):
            QShortcut(QKeySequence(keys), self, activated=slot, context=Qt.ApplicationShortcut)  # auch im Viewer-Fenster
        self.viewer.detached_changed.connect(self._viewer_detached)
        self.viewer.install(self._viewer_host_layout)

    def _viewer_detached(self, detached: bool) -> None:
        """2. Monitor: Tag-Tabelle ueber die ganze Breite, Zurueckholen-Knopf ueber der Tabelle. Zurueck: Bereich wieder
        im Standardverhaeltnis (``VIEWER_SPLIT``) teilen."""
        self._viewer_host.setVisible(not detached)
        self.viewer_away.setVisible(detached)
        if not detached:
            total = max(sum(self._hsplit.sizes()), self._hsplit.width(), sum(VIEWER_SPLIT))
            left = round(total * VIEWER_SPLIT[0] / sum(VIEWER_SPLIT))
            self._hsplit.setSizes([left, total - left])

    # --- Tag-Tabelle ---------------------------------------------------------------------------------------------
    def _tag_rows(self) -> list[list]:
        result = self._store_result
        if result is None:
            return []
        checker = self.win.checker
        scan = scan_values(result) if self.scan_button.isChecked() else [""] * len(SCAN_COLS)
        rows = [[t.type, t.tag, t.count, t.pages_text,
                 *(checker.columns(t.type, t.tag, t.count) if checker else ["", ""]),
                 *(self.store.values(t.type, t.tag) if self.store else [""] * len(FIELDS)), *scan]
                for t in result.tags]
        # Datenlink 2: Zusatzspalten aus der Importtabelle (Feld per Rechtsklick auf den Spaltenkopf)
        links = self.win.links
        field = links.fields.get("tags", "")
        if links.active(2) and field in TAG_COLS:
            c, file_value = TAG_COLS.index(field), self.win.file_link_value(result)
            for row in rows:
                row.extend(links.tag_values(row[c], file_value))
        return rows

    def _toggle_scan_fields(self, on: bool) -> None:
        last_paths.set_value(SCAN_KEY, bool(on))
        self._only_duplicates()

    def apply_scan_columns(self) -> None:
        on = self.scan_button.isChecked()
        for c in range(SCAN_COL, len(TAG_COLS)):
            if self.tags.table.isColumnHidden(c) == on:
                self.tags.table.setColumnHidden(c, not on)

    def autofill_ok(self) -> None:
        """Alle OK-Werte der gewaehlten PDF: Review OK, User, Datum (ohne Uhrzeit), WPO = Checked (falls leer)."""
        result, store = self._store_result, self.store
        if result is None or store is None:
            self.win.statusBar().showMessage("Autofill OK: zuerst eine PDF wählen.", 6000)
            return
        checker = self.win.checker
        changed = sum(store.autofill_ok(t.type, t.tag, result.checked,
                                        checker.columns(t.type, t.tag, t.count)[0] if checker else "")
                      for t in result.tags)
        self._only_duplicates()
        self._store_changed()
        self.win.statusBar().showMessage(f"Autofill OK: {changed} Tag(s) ausgefüllt – zum Übernehmen Speichern."
                                         if changed else "Autofill OK: keine OK-Werte zum Ausfüllen.", 8000)

    def _only_duplicates(self, on: bool | None = None) -> None:
        """Tag-Tabelle neu fuellen; Filter "Nur doppelte" und (Projektmodus) "Nur Abweichungen"."""
        on = self.dup_button.isChecked() if on is None else on
        faults = self.fault_button.isChecked() and self.win.checker is not None
        rows = [r for r in self._tag_rows() if (not on or r[2] > 1) and (not faults or is_fault_status(r[CHECK_COL]))]
        field = self.win.links.fields.get("tags", "")
        self.tags.headers = TAG_COLS + (self.win.links.tag_extra(TAG_COLS) if field in TAG_COLS else [])
        self.tags.set_rows(rows)
        self.tags.proxy.sourceModel().dataChanged.connect(self._store_changed)   # neues Modell -> neu verbinden
        self.win.apply_project_columns()
        self._hit = None

    def show_status(self) -> None:
        """Rahmen im Viewer: gruen korrekt, rot Review "Korrektur erforderlich" oder (Projektmodus) Abweichung."""
        result = self._store_result
        self.preview.show_status(*status_hits(result.tags if result else [], self.store, self.win.checker))

    # --- Bearbeiten-Modus / Speichern -----------------------------------------------------------------------------
    def set_edit_mode(self, on: bool) -> None:
        self.edit_mode = on
        triggers = (QTableView.DoubleClicked | QTableView.EditKeyPressed | QTableView.AnyKeyPressed) if on \
            else QTableView.NoEditTriggers
        self.tags.table.setEditTriggers(triggers)
        model = self.tags.proxy.sourceModel()
        if isinstance(model, ReviewModel):
            model.edit_mode = on
            # nur Darstellung/Flags aendern sich -> dataChanged (layoutChanged ohne layoutAboutToBeChanged bringt den
            # Filter-Proxy durcheinander und fuehrte zum Absturz)
            if model.rowCount() and model.columnCount():
                model.dataChanged.emit(model.index(0, 0), model.index(model.rowCount() - 1, model.columnCount() - 1))
        self.win.statusBar().showMessage("Bearbeiten-Modus: Doppelklick oder Tippen in Review … WPO; Datum und User "
                                         "werden automatisch gesetzt." if on else "Bearbeiten-Modus aus", 6000)

    def _store_changed(self, *_args) -> None:
        dirty = bool(self.store and self.store.dirty)
        self.save_button.setEnabled(dirty)
        self.save_button.setText(i18n.tr("Speichern *" if dirty else "Speichern"))
        self.show_status()

    def save_review(self) -> bool:
        if not (self.store and self.store.dirty):
            return True
        try:
            path = self.store.save()
        except OSError as exc:
            QMessageBox.warning(self, "Speichern", f"Review konnte nicht gespeichert werden:\n{exc}")
            return False
        self._store_changed()
        self.win.statusBar().showMessage(f"Review gespeichert (neuer Stand, PDF unverändert): {path.name}", 8000)
        return True

    def confirm_unsaved(self) -> bool:
        """Ungespeicherte Review-Eintraege: Speichern / Verwerfen / Abbrechen. False = Aktion abbrechen."""
        if not (self.store and self.store.dirty):
            return True
        box = QMessageBox(QMessageBox.Question, "Review-Einträge",
                          f"Ungespeicherte Review-Einträge für „{self.store.pdf_path.name}“ speichern?\n\n"
                          "Gespeichert wird ein neuer Stand mit Zeitstempel im Review-Ordner des Tools. "
                          "Die PDF selbst wird nicht verändert (nur gelesen).", parent=self)
        save = box.addButton("Speichern", QMessageBox.AcceptRole)
        discard = box.addButton("Verwerfen", QMessageBox.DestructiveRole)
        box.addButton("Abbrechen", QMessageBox.RejectRole)
        box.setDefaultButton(save)
        box.exec()
        if box.clickedButton() is save:
            return self.save_review()
        if box.clickedButton() is discard:
            self.store.load()
            self._store_changed()
            self._only_duplicates()
            return True
        return False

    def reset_tag_filters(self) -> None:
        self.dup_button.setChecked(False)
        self.fault_button.setChecked(False)
        self.tags.clear_filters()

    def current_result(self) -> PdfResult | None:
        return self.win.result_at(self.files.source_row(self.files.table.currentIndex()))

    def _tags_export_name(self) -> str:
        result = self.current_result()
        return f"{result.path.stem}_Tags" if result else "Tags"

    def _file_changed(self, current: QModelIndex, _previous=None) -> None:
        if self._switching:
            return
        result = self.win.result_at(self.files.source_row(current))
        if result is self._store_result:
            return
        if not self.confirm_unsaved():                 # Abbrechen: bei der bisherigen PDF bleiben
            self._switching = True
            try:
                if _previous is not None and _previous.isValid():
                    self.files.table.setCurrentIndex(_previous)
            finally:
                self._switching = False
            return
        self._store_result = result
        if result is None:
            self.store = None
            self._only_duplicates()
            self._store_changed()
            self.preview.show_pdf(None)
        else:
            self._load_with_progress(result)
        dups = sum(1 for t in result.tags if t.duplicate) if result else 0
        self.tags.count.setToolTip(i18n.tr(f"{dups} doppelte Tag(s) gelb hinterlegt") if dups else "")

    def _load_with_progress(self, result: PdfResult) -> None:
        """Tag-Tabelle und PDF der gewaehlten Datei laden - mit Fortschrittsfenster wie in P3D XCHANGE (nach dem Scan
        im bereits offenen Ladedialog als Schritte 2 und 3)."""
        open_dlg = self.win._table_progress
        ctx = nullcontext(open_dlg) if open_dlg is not None else progress_task(self, "PDF wird geladen", steps=2)
        first = 2 if open_dlg is not None else 1
        with ctx as dlg:
            dlg.update_progress(10, f"Tag-Tabelle lesen: {result.name} ({len(result.tags)} Tags)", first)
            self.store = ReviewStore(result.path)
            self._only_duplicates()
            self._store_changed()
            dlg.update_progress(60, f"PDF öffnen und anzeigen: {result.name} ({result.pages} Seite(n))", first + 1)
            self.preview.show_pdf(result.path)
            self.show_status()
            self.preview.show_duplicates([t.hits for t in result.tags if t.duplicate])
            dlg.update_progress(100)

    # --- Tag-Navigation ------------------------------------------------------------------------------------------
    def _tag_at(self, index: QModelIndex):
        result = self.current_result()
        row = self.tags.source_row(index)
        if not result or row < 0:
            return None
        typ, tag = self.tags.rows()[row][:2]
        return next((t for t in result.tags if t.type == typ and t.tag == tag), None)

    def _tag_selected(self, index: QModelIndex) -> None:
        """Neuer Tag gewaehlt: eine Fundstelle -> darauf zoomen; mehrere -> Uebersicht der ganzen Seite."""
        self._hit = self._tag_at(index)
        # Auswahl per Maus: der folgende clicked() derselben Mausaktion blaettert nicht weiter (per Tastatur kein clicked)
        self._fresh_selection = QApplication.mouseButtons() != Qt.NoButton
        if self._hit is None:
            self.preview.clear_marks()
            return
        self._focus = None if len(self._hits()) > 1 else 0
        self._show_focus()

    def _tag_clicked(self, index: QModelIndex) -> None:
        if self._fresh_selection:
            self._fresh_selection = False
            return
        if self._hit is not None and self._tag_at(index) is self._hit:
            self.next_occurrence()

    def _hits(self) -> list[tuple]:
        """Fundstellen des gewaehlten Tags [(Seite, Rechteck)] in Leserichtung: Seite, dann oben -> unten, links -> rechts.
        Mehrfach-Tags beginnen auf der Seite, auf der sie doppelt sind (``Tag.page``)."""
        if not self._hit:
            return []
        first = self._hit.page
        return sorted(self._hit.hits, key=lambda h: (h[0] != first, h[0], round(h[1][1]), h[1][0]))

    def _step(self, delta: int) -> None:
        """Reihenfolge: Uebersicht -> 1 -> 2 -> ... -> n -> Uebersicht (rueckwaerts entsprechend)."""
        count = len(self._hits())
        if count <= 1:
            if self._hit is not None:
                self._show_focus()
            return
        states = [None, *range(count)]
        self._focus = states[(states.index(self._focus) + delta) % len(states)]
        self._show_focus()

    def next_occurrence(self) -> None:
        self._step(1)

    def previous_occurrence(self) -> None:
        self._step(-1)

    def _show_focus(self) -> None:
        self.preview.mark(self._hits(), self._focus, self._hit.tag, overview_page=self._hit.page)


class AllTagsSheet(Sheet):
    def __init__(self):
        super().__init__("Alle Tags", "Tags aller gescannten PDFs", closable=True)
        self.tags = DataTable("all_tags", "Tags aller PDFs", ALL_TAG_COLS, count_col=4)
        self.tags.table.export_name = lambda: "PID_Tags_alle"
        self.body_layout.addWidget(self.tags, 1)


class MainWindow(QMainWindow):
    def __init__(self, app, version: str):
        super().__init__()
        table_views.install()
        self.theme = ThemeManager(app, start="LIGHT")
        app.setStyleSheet(app.styleSheet() + appearance.app_qss() + indicator_qss())
        self.version = version
        self.setWindowTitle(APP_NAME)
        self.resize(1500, 920)
        self.results: list[PdfResult] = []
        self.sources: list[str] = []
        self._thread: QThread | None = None
        self._worker: ScanWorker | None = None
        self._progress: ProgressDialog | None = None
        self._table_progress: ProgressDialog | None = None    # offener Ladedialog (Tabellen nach dem Scan)
        self.project: ProjectDB | None = None          # Projektmodus: geoeffnete Projekt-Datenbank
        self.checker = None                            # Projektmodus: Pruefung (project_defs.Checker), sonst None
        self._scan_placeholders = False                # letzter Scan mit Platzhalter-Tags (nur Projektmodus)
        # Datenlink: importierte Excel-Liste, verknuepft ueber Datenlink 1 (Dateien) und 2 (Tags)
        self.links = LinkController(self._relink, self.edit_data_link)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(HeaderBanner(APP_NAME, version))
        self.setStatusBar(QStatusBar())
        self.page = TagsSheet(self)                 # vor dem Menueband: es ruft Funktionen der Blaetter auf
        self.links.install("files", self.page.files, FILE_COLS)
        self.links.install("tags", self.page.tags, TAG_COLS)
        self.all_page = AllTagsSheet()
        self.ribbon = self._build_ribbon()
        self._show_pipes(bool(last_paths.get_value(PIPES_KEY, False)))
        root.addWidget(self.ribbon)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_index)
        root.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        self.all_page.header.close_requested.connect(lambda: self._close_widget(self.all_page))
        self.tabs.addTab(self.page, "PID-Tags")
        for side in (QTabBar.RightSide, QTabBar.LeftSide):
            self.tabs.tabBar().setTabButton(0, side, None)
        QShortcut(QKeySequence("F5"), self, activated=lambda: self.scan(None))
        QShortcut(QKeySequence.Save, self, activated=self.page.save_review)
        self._restore_project()
        self._update_bands()
        self.statusBar().showMessage(f"Datenordner: {paths.home_dir()}", 8000)

    # --- Menueband -----------------------------------------------------------------------------------------------
    def _build_ribbon(self) -> Ribbon:
        """Menueband: Projekt (mit den Einstellungen Pfade/Tag-Muster), dann die Arbeitsschritte 1 Einlesen -> 2 Ansicht
        -> 3 Pruefen -> 4 Review/Redline -> 5 Export, zuletzt Hilfe (Nutzervorgabe 2026-11-21). Jede Gruppe hat eine
        dunkelblaue Ueberschrift. Jede Funktion als Symbol (Glyphen-Ergaenzung in ``toolstrip``)."""
        r = Ribbon("P&ID-PDF-Reader")
        # Projekt: Projekt waehlen, dann die Umschalter 1. Projektmodus 2. Rohrleitungen (Nutzervorgabe 2026-11-22),
        # Verwaltung der Definitionen
        g = r.group("Projekt")
        self.project_menu = QMenu(self)
        self.project_menu.aboutToShow.connect(self._fill_project_menu)
        g.large("project_pick", "Projekt\nwählen", "project", lambda: None, self.project_menu)
        r.buttons["project_pick"].setToolTip("Projekt anlegen, öffnen oder aus P3D Tag Compliance übernehmen")
        g.large("project_mode", "Projekt-\nmodus: aus", "project_mode", self.toggle_project_mode)
        r.buttons["project_mode"].setCheckable(True)
        r.buttons["project_mode"].setToolTip(PROJECT_TIP)
        # Rohrleitungsnummern (waagerecht und senkrecht) mit in die Tag-Liste uebernehmen: Umschalter wie der
        # Projektmodus (an = Symbol gruen), gemerkt je Benutzer
        g.large("pipes", "Rohr-\nleitungen: aus", "pipe", self._toggle_pipes)
        r.buttons["pipes"].setCheckable(True)
        r.buttons["pipes"].setToolTip(PIPES_TIP)
        g.large("project_defs", "Projekt-\ndefinitionen …", "defs", self.edit_project_definitions)
        r.buttons["project_defs"].setToolTip("Projektdefinitionen verwalten: Codelisten, Listen, Tag-Strukturen, "
                                             "Prüfregeln, Excel, Übernahme aus Tag Compliance")
        # Einstellungen gehoeren zur Gruppe Projekt (Nutzervorgabe 2026-11-21)
        g.large("paths", "Pfade", "settings", self.edit_paths)
        g.large("patterns", "Tag-\nMuster", "header", lambda: open_in_explorer(paths.patterns_file()))
        self.settings_menu = QMenu(self)
        self.layer_action = self.settings_menu.addAction("Layer für Review im PDF", self._toggle_review_layer)
        self.layer_action.setCheckable(True)
        self.layer_action.setChecked(redline.review_layer_enabled())
        self.layer_action.setToolTip(LAYER_TIP)
        self.settings_menu.setToolTipsVisible(True)
        g.large("settings_menu", "Einstel-\nlungen", "settings", lambda: None, self.settings_menu)
        r.buttons["settings_menu"].setToolTip("Einstellungen: Layer für Review im PDF")
        g = r.group("1  Einlesen")
        g.large("scan", "Quellordner\nscannen", "scan", lambda: self.scan(None))
        g.large("folder", "Ordner\nöffnen …", "folder", self._pick_folder)
        g.large("files", "Dateien\nöffnen …", "files", self._pick_files)
        # Datenlink: Excel-Liste (z. B. Instrumenten-Gesamtliste) importieren und mit den Tabellen verknuepfen
        self.link_menu = QMenu(self)
        self.link_menu.aboutToShow.connect(self._fill_link_menu)
        g.large("data_link", "Liste\nimportieren", "import", lambda: None, self.link_menu)
        r.buttons["data_link"].setToolTip(DATA_LINK_TIP)
        g = r.group("2  Ansicht")
        g.large("sheet_tags", "PID-Tags", "start", lambda: self.tabs.setCurrentWidget(self.page))
        g.large("sheet_all", "Alle Tags", "reports", self.show_all_tags)
        g.large("monitor", "Viewer\n2. Monitor", "monitor", self.page.viewer.monitor_button.toggle)
        g.large("preview", "Tabellen-\nVorschau …", "columns", self.show_table_preview)
        g = r.group("3  Prüfen")
        g.large("prev", "Fundstelle\nzurück", "prev", self.page.previous_occurrence)
        g.large("next", "Fundstelle\nweiter", "next", self.page.next_occurrence)
        g.large("dups", "Nur doppelte\nTags", "duplicates", self.page.dup_button.toggle)
        g.large("deviations", "Nur Projekt-\nabweichungen", "deviations", self.page.fault_button.toggle)
        g.large("filter_reset", "Filter\nzurücksetzen", "filter_reset", self._clear_filters)
        g.large("edit", "Tabelle\nbearbeiten", "rename", self.page.edit_button.toggle)
        g.large("save", "Review\nspeichern", "write", self.page.save_review)
        g = r.group("4  Review / Redline")
        g.large("review", "Review\nAuswahl/Bulk …", "review", self.review)
        g.large("redline", "Redline-PDF\ngewählte PDF", "redline", self.redline_current)
        g.large("review_xlsx", "Review-Excel\ngewählte PDF", "excel_out", self.review_excel_current)
        g = r.group("5  Export")
        g.large("xlsx", "Export\nExcel …", "excel_out", lambda: self.export("xlsx"))
        g.large("csv", "Export\nCSV …", "csv_out", lambda: self.export("csv"))
        g.large("open_exports", "Export-\nordner", "folder", lambda: open_in_explorer(paths.exports_dir()))
        # Web-Version fuer Kollegen im Firmennetz (Server als eigener Prozess, gui/web_control.py)
        g = r.group("Web")
        g.large("web_server", "Web-Server\naus", "connect", self.toggle_web_server)
        r.buttons["web_server"].setCheckable(True)
        r.buttons["web_server"].setToolTip(web_control.WEB_TIP)
        g.large("web_open", "Im Browser\nöffnen", "other", self.open_web_version)
        r.buttons["web_open"].setToolTip("Web-Version auf diesem PC im Browser öffnen (startet den Server bei Bedarf)")
        g.large("web_report", "Offline-\nBericht …", "report", self.create_offline_report)
        r.buttons["web_report"].setToolTip("Offline-HTML-Bericht (markierte oder alle PDFs): eine HTML-Datei mit Tabellen, "
                                           "Viewer, Audit-Spalten, Redline-PDF und Review-Excel – ohne Server, zum "
                                           "Weitergeben per Mail, Freigabe oder SharePoint")
        g = r.group("Hilfe")
        g.large("help", "Handbuch", "help", self.show_help)
        g.large("about", "Info", "info", self.show_about)
        # Sprache: Globus-Symbol mit Menue Deutsch / English / Français (wie P3D XCHANGE)
        self.lang_menu = QMenu(self)
        for code, name in i18n.LANGUAGES.items():
            action = self.lang_menu.addAction(name, lambda c=code: self.set_language(c))
            action.setCheckable(True)
            action.setData(code)
            action.setProperty("i18n_skip", True)          # Sprachnamen bleiben in ihrer eigenen Sprache
        self.lang_menu.aboutToShow.connect(self._mark_language)
        g.large("language", "Sprache", "language", lambda: None, self.lang_menu)
        r.buttons["language"].setToolTip("Sprache der Oberfläche: Deutsch, English, Français")
        apply_group_heads(r)                                # dunkelblaue Gruppenueberschriften oben
        # Klick auf eine Kopfleiste klappt die Gruppe ein; gestapelt (4 je Spalte) hinter den sichtbaren, gemerkt.
        # Beim Start stehen die eingeklappten Kopfleisten in einer Reihe (Nutzervorgabe 2026-11-22)
        self.ribbon_fold = RibbonFold(r, last_paths.get_value(FOLD_KEY),     # None = Standard: nur Projekt offen
                                      lambda keys: last_paths.set_value(FOLD_KEY, keys))
        return r

    # --- Blaetter ------------------------------------------------------------------------------------------------
    def show_all_tags(self) -> None:
        if self.tabs.indexOf(self.all_page) < 0:
            self.tabs.addTab(self.all_page, "Alle Tags")
        self.tabs.setCurrentWidget(self.all_page)

    def _close_index(self, index: int) -> None:
        if self.tabs.widget(index) is not self.page:
            self.tabs.removeTab(index)

    def _close_widget(self, widget: QWidget) -> None:
        index = self.tabs.indexOf(widget)
        if index >= 0:
            self._close_index(index)

    def _clear_filters(self) -> None:
        self.page.dup_button.setChecked(False)
        self.page.fault_button.setChecked(False)
        for table in (self.page.files, self.page.tags, self.all_page.tags):
            table.clear_filters()

    def _update_bands(self) -> None:
        source = "; ".join(self.sources) if self.sources else "–"
        tags = sum(len(r.tags) for r in self.results)
        errors = sum(1 for r in self.results if r.error)
        t = i18n.tr
        band = (f"{t('PROJEKT')}  {self.project_label()}   {t('QUELLE')}  {source}   {t('PDFS')}  "
                f"{len(self.results)}   {t('TAGS')}  {tags}   {t('FEHLER')}  {errors}")
        if self.checker is not None:
            faults = sum(1 for r in self.results for x in r.tags if self.checker.is_fault(x.type, x.tag))
            band += f"   {t('ABWEICHUNGEN')}  {faults}"
        self.page.set_band(band)
        self.all_page.set_band(band)

    # --- Daten ---------------------------------------------------------------------------------------------------
    def result_at(self, row: int) -> PdfResult | None:
        return self.results[row] if 0 <= row < len(self.results) else None

    def _refresh(self) -> None:
        rows = [file_row(r) for r in export.file_rows(self.results)]
        field = self.links.fields.get("files", "")
        extra = self.links.file_extra() if field in FILE_COLS else []
        if extra:
            c = FILE_COLS.index(field)
            for row in rows:
                row.extend(self.links.file_values(row[c]))
        self.page.files.headers = FILE_COLS + extra
        self.page.files.set_rows(rows)
        self._refresh_tags()

    def file_link_value(self, result: PdfResult):
        """Wert des Datenlink-Felds der Dateiliste fuer diese PDF (None ohne Feld)."""
        field = self.links.fields.get("files", "")
        if field not in FILE_COLS:
            return None
        return file_row(export.file_rows([result])[0])[FILE_COLS.index(field)]

    # --- Datenlink -----------------------------------------------------------------------------------------------
    def _fill_link_menu(self) -> None:
        m = self.link_menu
        m.clear()
        m.addAction("Excel-Liste importieren …", lambda: self.edit_data_link(new=True))
        edit = m.addAction("Importtabelle bearbeiten (Kachel-Editor) …", self.edit_data_link)
        edit.setEnabled(self.links.table is not None)
        m.addSeparator()
        m.addAction("Datenlinks anzeigen", lambda: QMessageBox.information(self, "Datenlink", self.links.summary()))
        remove = m.addAction("Importtabelle entfernen", self._remove_data_link)
        remove.setEnabled(self.links.table is not None)

    def edit_data_link(self, new: bool = False) -> None:
        if self.links.edit(self, new=new or self.links.table is None):
            self.statusBar().showMessage("Datenlink: " + self.links.summary().replace("\n", " · "), 12000)

    def _remove_data_link(self) -> None:
        answer = QMessageBox.question(self, "Datenlink", "Importtabelle entfernen? Die Datenlink-Spalten verschwinden "
                                                         "aus den Tabellen (die Excel-Datei bleibt unverändert).")
        if answer == QMessageBox.Yes:
            self.links.remove()

    def _relink(self) -> None:
        """Nach Import oder neuem Datenlink-Feld: Dateiliste und Tag-Tabelle neu fuellen, gewaehlte PDF bleibt."""
        page = self.page
        current = page._store_result
        page._switching = True                       # kein PDF-Wechsel waehrend die Dateiliste neu gefuellt wird
        try:
            self._refresh()
            if current is not None and current in self.results:
                src = page.files.proxy.sourceModel().index(self.results.index(current), 0)
                index = page.files.proxy.mapFromSource(src)
                if index.isValid():
                    page.files.table.setCurrentIndex(index)
        finally:
            page._switching = False
        page._only_duplicates()
        page.files.table.horizontalHeader().viewport().update()
        page.tags.table.horizontalHeader().viewport().update()

    def _refresh_tags(self) -> None:
        """Blatt "Alle Tags", Pruefspalten und Kopfband (Dateiliste und Auswahl bleiben)."""
        checker = self.checker
        self.all_page.tags.set_rows([r[:5] + (checker.columns(r[2], r[3], r[4]) if checker else ["", ""])
                                     for r in export.tag_rows(self.results)])
        self.apply_project_columns()
        self._update_bands()

    # --- Scan ----------------------------------------------------------------------------------------------------
    def _pick_folder(self) -> None:
        folder = last_paths.open_dir(self, "Ordner mit PDF-Plots wählen")
        if folder:
            self.scan([folder])

    def _pick_files(self) -> None:
        files = last_paths.open_files(self, "PDF-Plots wählen", "PDF (*.pdf)")
        if files:
            self.scan(files)

    def _toggle_review_layer(self) -> None:
        last_paths.set_value(redline.LAYER_KEY, self.layer_action.isChecked())
        on = (f"auf der Ebene „{redline.review_layer_name()}“" if self.layer_action.isChecked()
              else "ohne eigene Ebene")
        self.statusBar().showMessage(f"Redline-PDF: Review-Kommentare {on}.", 8000)

    def pipes_enabled(self) -> bool:
        return self.ribbon.buttons["pipes"].isChecked()

    def _show_pipes(self, on: bool) -> None:
        """Umschalter Rohrleitungen wie der Projektmodus: Text an/aus, Symbol gruen solange an (Kit-Farbe ``ok``)."""
        button = self.ribbon.buttons["pipes"]
        button.setChecked(on)
        self.ribbon.set_text("pipes", "Rohr-\nleitungen: an" if on else "Rohr-\nleitungen: aus")
        button.setIcon(icons.glyph_icon("pipe", LIGHT.ok, 32) if on else icons.ribbon_icon("pipe", 32))

    def _toggle_pipes(self) -> None:
        """Menueband: Rohrleitungen ein/aus. Option merken; eingelesene PDFs mit der neuen Einstellung neu einlesen."""
        self._show_pipes(self.pipes_enabled())
        last_paths.set_value(PIPES_KEY, self.pipes_enabled())
        on = "werden mit eingelesen" if self.pipes_enabled() else "werden nicht eingelesen"
        self.statusBar().showMessage(f"Rohrleitungsnummern {on}.", 8000)
        if self.results and self.sources:
            self.scan(list(self.sources))

    def scan(self, sources) -> None:
        if self._thread is not None:
            return
        if sources is None:
            sources = paths.PathSettings.load().existing_sources()
            if not sources:
                QMessageBox.information(self, "Scan", "Keine Quellordner hinterlegt. Bitte unter „Pfade“ einen Ordner "
                                        "hinzufügen oder „Ordner öffnen“ nutzen.")
                return
        if not self.page.confirm_unsaved():
            return
        self.sources = [str(Path(s)) for s in sources]
        self.results = []
        self.page._store_result = None
        self._refresh()
        self._progress = ProgressDialog("PDFs einlesen", self).open()
        cancel = action_button("Abbrechen", ButtonKind.DANGER)
        cancel.clicked.connect(self.cancel_scan)
        self._progress.layout().addWidget(cancel, 0, Qt.AlignRight)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self._thread = QThread(self)
        self._scan_placeholders = self.checker is not None
        self._worker = ScanWorker([Path(s) for s in sources], self.pipes_enabled(), self._scan_placeholders)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self.results.append)
        self._worker.result.connect(lambda r: paths.protect([r.path]))     # Originale: nur lesen, nie Ausgabeziel
        self._worker.finished.connect(self._on_finished)
        self._thread.start()

    def cancel_scan(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_progress(self, i: int, n: int, name: str) -> None:
        if self._progress:
            self._progress.update_progress(100 * i / max(1, n), f"„{name}“ lesen ({i} von {n})")

    def _on_finished(self, cancelled: bool) -> None:
        self._thread.quit()
        self._thread.wait()
        self._thread = self._worker = None
        QApplication.restoreOverrideCursor()
        if self._progress:
            self._progress.close()
            self._progress.deleteLater()
            self._progress = None
        errors = sum(1 for r in self.results if r.error)
        tags = sum(len(r.tags) for r in self.results)
        with progress_task(self, "Tabellen werden geladen", steps=3,
                           message=f"Dateiliste und „Alle Tags“ aufbauen ({len(self.results)} PDFs, {tags} Tags)") as dlg:
            self._table_progress = dlg
            try:
                dlg.update_progress(5)
                self._refresh()
                if self.results:
                    self.page.files.table.selectRow(0)     # laedt Tag-Tabelle und PDF (Schritte 2 und 3)
            finally:
                self._table_progress = None
        self.statusBar().showMessage(f"{'Abgebrochen: ' if cancelled else ''}{len(self.results)} PDF(s), {tags} Tags, "
                                     f"{errors} Fehler")

    # --- Export / Vorschau / Pfade / Info ------------------------------------------------------------------------
    def export(self, kind: str) -> None:
        if not self.results:
            QMessageBox.information(self, "Export", "Noch keine PDFs gescannt.")
            return
        name = f"PID_Tags_{paths.file_timestamp()}"
        if kind == "xlsx":
            path = last_paths.save_file(self, "Export Excel", f"{name}.xlsx", "Excel (*.xlsx)", paths.exports_dir())
            if path:
                export.write_xlsx(path, self.results, self.checker)
        else:
            path = last_paths.save_file(self, "Export CSV (Tags)", f"{name}.csv", "CSV (*.csv)", paths.exports_dir())
            if path:
                export.write_csv(path, export.tag_headers(False, self.checker),
                                 export.tag_rows(self.results, False, self.checker))
                export.write_csv(Path(path).with_name(Path(path).stem + "_Dateien.csv"), export.FILE_HEADERS,
                                 export.file_rows(self.results))
        if path:
            answer = QMessageBox.question(self, "Export", f"Gespeichert:\n{paths.display_path(path)}\n\n"
                                          "Ordner öffnen?", QMessageBox.Yes | QMessageBox.No)
            if answer == QMessageBox.Yes:
                open_in_explorer(path)

    # --- Redline ------------------------------------------------------------------------------------------------
    def redline_current(self) -> None:
        """Redline der gewaehlten PDF; bei aktivem Tabellenfilter wird gefragt: nur gefilterte oder alle Tags."""
        result = self.page.current_result()
        if result is None:
            QMessageBox.information(self, "Redline-PDF", "Bitte zuerst eine PDF in der Dateiliste wählen.")
            return
        tags = self._choose_tags(result, "Redline-PDF")
        if tags is None:
            return
        name = f"{result.path.stem}_Redline_{paths.file_timestamp()}.pdf"
        path = last_paths.save_file(self, "Redline-PDF speichern", name, "PDF (*.pdf)", paths.exports_dir())
        if not path:
            return
        try:
            store = self.page.store if self.page._store_result is result else None   # auch ungespeicherte Eintraege
            count = redline.write_redline(result, path, tags, store=store, checker=self.checker)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Redline-PDF", f"Redline-PDF konnte nicht geschrieben werden:\n{exc}")
            return
        filtered = "" if len(tags) == len(result.tags) else f"\n(Filter aktiv: {len(tags)} von {len(result.tags)} Tags)"
        answer = QMessageBox.question(self, "Redline-PDF", f"Gespeichert:\n{paths.display_path(path)}\n\n{count} "
                                      f"Kommentar(e){filtered}\n\nPDF öffnen?", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            os.startfile(path)  # noqa: S606

    def _visible_tags(self, result: PdfResult) -> list:
        proxy = self.page.tags.proxy
        visible = {(proxy.index(r, 0).data(), proxy.index(r, 1).data()) for r in range(proxy.rowCount())}
        return [t for t in result.tags if (t.type, t.tag) in visible]

    def _choose_tags(self, result: PdfResult, title: str) -> list | None:
        """Tags fuer Redline/Review-Excel. Ist ein Filter aktiv (z. B. "Nur doppelte"), fragen: nur gefilterte oder alle.
        ``None`` = abgebrochen."""
        visible = self._visible_tags(result)
        if len(visible) == len(result.tags):
            return visible
        box = QMessageBox(QMessageBox.Question, title,
                          f"In der Tag-Tabelle ist ein Filter aktiv: {len(visible)} von {len(result.tags)} Tags sichtbar"
                          + (" (Nur doppelte)" if self.page.dup_button.isChecked() else "")
                          + (" (Nur Abweichungen)" if self.page.fault_button.isChecked() else "")
                          + ".\n\nWelche Tags ausgeben?",
                          parent=self)
        only = box.addButton(f"Nur gefilterte ({len(visible)})", QMessageBox.AcceptRole)
        every = box.addButton(f"Alle Tags ({len(result.tags)})", QMessageBox.AcceptRole)
        box.addButton(QMessageBox.Cancel)
        box.setDefaultButton(every)
        box.exec()
        if box.clickedButton() is only:
            return visible
        if box.clickedButton() is every:
            return list(result.tags)
        return None

    def review_excel_current(self) -> None:
        """Review-Excel der gewaehlten PDF (sichtbare Tags): Pos.-Nr., Review-Kommentar, Pruefstatus, Bemerkung."""
        result = self.page.current_result()
        if result is None:
            QMessageBox.information(self, "Review-Excel", "Bitte zuerst eine PDF in der Dateiliste wählen.")
            return
        tags = self._choose_tags(result, "Review-Excel")
        if tags is None:
            return
        self.page.save_review()                         # gespeicherte Review-Eintraege kommen in die Excel
        name = f"{result.path.stem}_Review_{paths.file_timestamp()}.xlsx"
        path = last_paths.save_file(self, "Review-Excel speichern", name, "Excel (*.xlsx)", paths.exports_dir())
        if not path:
            return
        try:
            review.write_review_xlsx(path, [result], {result.path: tags}, checker=self.checker)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Review-Excel", f"Review-Excel konnte nicht geschrieben werden:\n{exc}")
            return
        answer = QMessageBox.question(self, "Review-Excel", f"Gespeichert:\n{paths.display_path(path)}\n\n"
                                      "Datei öffnen?", QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            os.startfile(path)  # noqa: S606

    def marked_results(self) -> list[PdfResult]:
        """In der Dateiliste markierte PDFs (Mehrfachauswahl), in Tabellenreihenfolge."""
        table = self.page.files
        rows = sorted({i.row() for i in table.table.selectionModel().selectedRows()})
        return [r for r in (self.result_at(table.source_row(table.proxy.index(row, 0))) for row in rows) if r]

    def review(self) -> None:
        """Review / Audit einzeln oder im Bulk: Redline-PDF, Excel je PDF, Gesamt-Excel."""
        if not self.results:
            QMessageBox.information(self, "Review", "Noch keine PDFs eingelesen (Quellordner scannen, Ordner oder "
                                    "Dateien öffnen).")
            return
        marked = self.marked_results()
        dlg = ReviewDialog(len(marked), len(self.results), self)
        if dlg.exec() != ReviewDialog.Accepted:
            return
        self.run_review(marked if dlg.options().only_marked else list(self.results), dlg.options())

    def run_review(self, results: list[PdfResult], opts) -> Path | None:
        todo = [r for r in results if not r.error]
        if not todo:
            return None
        stamp = paths.file_timestamp()
        folder = Path(opts.folder) / (f"Review_{stamp}" if opts.subfolder else "")
        folder.mkdir(parents=True, exist_ok=True)
        steps = len(todo) * (int(opts.redline) + int(opts.excel_each)) + int(opts.excel_total)
        done, failed, comments, files = 0, [], 0, 0
        dlg = ProgressDialog("Review / Audit", self).open()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        def tick(text: str) -> None:
            nonlocal done
            done += 1
            dlg.update_progress(100 * done / max(1, steps), text)

        try:
            for i, result in enumerate(todo, start=1):
                label = f"„{result.name}“ ({i} von {len(todo)})"
                for enabled, kind, write in (
                        (opts.redline, "Redline", lambda r=result: redline.write_redline(
                            r, folder / f"{r.path.stem}_Redline_{stamp}.pdf", checker=self.checker)),
                        (opts.excel_each, "Review-Excel", lambda r=result: review.write_review_xlsx(
                            folder / f"{r.path.stem}_Review_{stamp}.xlsx", [r], checker=self.checker))):
                    if not enabled:
                        continue
                    try:
                        value = write()
                        files += 1
                        comments += value if isinstance(value, int) else 0
                    except Exception as exc:  # noqa: BLE001 - eine Datei darf den Lauf nicht abbrechen
                        failed.append(f"{result.name} ({kind}): {exc}")
                    tick(f"{kind}: {label}")
            if opts.excel_total:
                try:
                    review.write_review_xlsx(folder / f"PID_Review_gesamt_{stamp}.xlsx", todo,
                                             checker=self.checker)
                    files += 1
                except Exception as exc:  # noqa: BLE001
                    failed.append(f"Gesamt-Excel: {exc}")
                tick("Gesamt-Excel")
        finally:
            QApplication.restoreOverrideCursor()
            dlg.close()
            dlg.deleteLater()
        dups = sum(1 for r in todo for t in r.tags if t.duplicate)
        text = (f"{len(todo)} PDF(s) geprüft, {files} Datei(en) erzeugt"
                + (f", {comments} Kommentare" if opts.redline else "") + f"\nDoppelte Tags: {dups}\nOrdner: {folder}")
        if failed:
            text += "\n\nFehler:\n" + "\n".join(failed[:10])
        self.statusBar().showMessage(f"Review: {len(todo)} PDF(s), {files} Datei(en) – {folder}")
        answer = QMessageBox.question(self, "Review / Audit", text + "\n\nOrdner öffnen?",
                                      QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            open_in_explorer(folder)
        return folder

    def show_table_preview(self) -> None:
        DataPreviewDialog("Tabellen-Vorschau: Tags aller PDFs", export.TAG_HEADERS, export.tag_rows(self.results),
                          self).exec()

    def edit_paths(self) -> None:
        PathsDialog(self).exec()

    # --- Projektmodus ---------------------------------------------------------------------------------------------
    def project_label(self) -> str:
        if self.checker is not None and self.project is not None:
            return self.project.name
        return i18n.tr("Standard (ohne Projektdefinitionen)")

    def _restore_project(self) -> None:
        """Projektmodus und Projekt vom letzten Mal (config/state.json); fehlt die Datei, startet der Standardmodus."""
        path = str(last_paths.get_value(PROJECT_DB_KEY, "") or "")
        if path and Path(path).is_file():
            try:
                self.project = ProjectDB(path)
            except Exception:  # noqa: BLE001 - defekte Datenbank: Standardmodus
                self.project = None
        self._set_mode(bool(last_paths.get_value(PROJECT_MODE_KEY, False)) and self.project is not None, quiet=True)

    def toggle_project_mode(self) -> None:
        """Menueband: Projektmodus ein/aus. Ohne Projekt wird zuerst eines gewaehlt (uebernehmen, oeffnen, anlegen)."""
        on = self.ribbon.buttons["project_mode"].isChecked()
        if on and self.project is None:
            if not self._choose_project():
                self._set_mode(False, quiet=True)
            return
        self._set_mode(on)

    def _choose_project(self) -> bool:
        """Projekt waehlen und Projektmodus einschalten. False = abgebrochen."""
        box = QMessageBox(QMessageBox.Question, "Projektmodus",
                          "Für den Projektmodus ist noch kein Projekt gewählt.\n\nProjektdefinitionen aus "
                          "P3D Tag Compliance übernehmen, ein vorhandenes Projekt öffnen oder ein neues anlegen?",
                          parent=self)
        take = box.addButton("Aus Tag Compliance …", QMessageBox.AcceptRole)
        open_ = box.addButton("Projekt öffnen …", QMessageBox.AcceptRole)
        new = box.addButton("Neues Projekt …", QMessageBox.AcceptRole)
        box.addButton("Abbrechen", QMessageBox.RejectRole)
        box.setDefaultButton(take)
        box.exec()
        action = {take: project_dialog.import_project, open_: project_dialog.open_project,
                  new: project_dialog.new_project}.get(box.clickedButton())
        path = action(self) if action else None
        return bool(path) and self.activate_project(path)

    def activate_project(self, path) -> bool:
        """Projekt-Datenbank oeffnen, merken und den Projektmodus einschalten."""
        try:
            db = ProjectDB(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Projekt", f"Projekt konnte nicht geöffnet werden:\n{exc}")
            return False
        if self.project is not None:
            self.project.close()
        self.project = db
        last_paths.set_value(PROJECT_DB_KEY, str(db.path))
        self._set_mode(True)
        return True

    def _set_mode(self, on: bool, quiet: bool = False) -> None:
        """Projektmodus setzen (an nur mit Projekt) und Tabellen, Viewer-Rahmen und Kopfband neu aufbauen."""
        on = bool(on and self.project is not None)
        self.checker = self.project.checker() if on else None
        self.ribbon.buttons["project_mode"].setChecked(on)
        self.ribbon.set_text("project_mode", "Projekt-\nmodus: an" if on else "Projekt-\nmodus: aus")
        # Symbol gruen, solange der Projektmodus an ist (Kit-Farbe ``ok``, Nutzervorgabe 2026-11-21)
        self.ribbon.buttons["project_mode"].setIcon(icons.glyph_icon("project_mode", LIGHT.ok, 32) if on
                                                    else icons.ribbon_icon("project_mode", 32))
        self.ribbon.set_enabled("deviations", on)
        self.page.fault_button.setEnabled(on)
        if not on:
            self.page.fault_button.setChecked(False)
        last_paths.set_value(PROJECT_MODE_KEY, on)
        if self.results and self.sources and on != self._scan_placeholders and self._thread is None:
            self.scan(list(self.sources))           # Platzhalter-Tags (X/?) gibt es nur im Projektmodus: neu einlesen
        else:
            self._refresh_tags()
            if self.page._store_result is not None:
                self.page._only_duplicates()
            self.page.show_status()
        if not quiet and self._thread is None:
            missing = f" – Tag-Strukturen fehlen: {', '.join(self.checker.missing)}" if on and self.checker.missing else ""
            self.statusBar().showMessage(f"Projektmodus an: {self.project.name}{missing}" if on else
                                         "Projektmodus aus: Standard ohne Projektdefinitionen", 10000)

    def apply_project_columns(self) -> None:
        """Pruefspalten nur im Projektmodus zeigen; im Standardmodus ausgeblendet (Tabellen wie bisher). Zusaetzlich
        verzoegert, weil das Kit die gemerkte Tabellenansicht nach jedem neuen Modell verzoegert wiederherstellt."""
        def apply() -> None:
            on = self.checker is not None
            for table, first in ((self.page.tags.table, CHECK_COL), (self.all_page.tags.table, ALL_CHECK_COL)):
                for c in (first, first + 1):
                    if table.isColumnHidden(c) == on:
                        table.setColumnHidden(c, not on)
            self.page.apply_scan_columns()           # Schriftfeld-Spalten ("Aus PDF-Scan übernehmen")
        apply()
        QTimer.singleShot(0, apply)

    def _fill_project_menu(self) -> None:
        m = self.project_menu
        m.clear()
        m.addAction("Aus Tag Compliance übernehmen …", lambda: self._pick(project_dialog.import_project))
        m.addAction("Projekt öffnen …", lambda: self._pick(project_dialog.open_project))
        m.addAction("Neues Projekt …", lambda: self._pick(project_dialog.new_project))
        m.addSeparator()
        current = self.project.path if self.project else None
        found = sorted(paths.projects_dir().glob("*.db"), key=lambda f: f.name.casefold())
        for f in found:
            action = m.addAction(f.stem, lambda f=f: self.activate_project(f))
            action.setCheckable(True)
            action.setChecked(current is not None and paths.same_path(f, current))
            action.setProperty("i18n_skip", True)
        if not found:
            m.addAction("(noch keine Projekte)").setEnabled(False)
        m.addSeparator()
        m.addAction("Projektordner öffnen", lambda: open_in_explorer(paths.projects_dir()))

    def _pick(self, action) -> None:
        path = action(self)
        if path:
            self.activate_project(path)

    def edit_project_definitions(self) -> None:
        """Verwaltung der Projektdefinitionen; nach Aenderungen wird die Pruefung neu aufgebaut."""
        if self.project is None and not self._choose_project():
            return
        dlg = project_dialog.ProjectDefinitionsDialog(self.project, self)
        dlg.exec()
        if dlg.changed:
            self._set_mode(self.checker is not None, quiet=True)
            self.statusBar().showMessage("Projektdefinitionen gespeichert – Prüfung aktualisiert.", 8000)

    # --- Sprache --------------------------------------------------------------------------------------------------
    def _mark_language(self) -> None:
        current = i18n.language()
        for action in self.lang_menu.actions():
            action.setChecked(action.data() == current)

    def set_language(self, code: str) -> None:
        """Oberflaechensprache sofort fuer alle offenen Fenster wechseln (gemerkt je Benutzer in config/state.json).
        Tabellenkoepfe, Zaehler, Blattkopf und Seitenanzeige werden neu gesetzt, weil der Code sie dynamisch schreibt."""
        i18n.set_language(code)
        self._mark_language()
        for table in (self.page.files, self.page.tags, self.all_page.tags):
            model = table.proxy.sourceModel()
            if model is not None and model.columnCount():
                model.headerDataChanged.emit(Qt.Horizontal, 0, model.columnCount() - 1)
            header = table.table.horizontalHeader()
            if hasattr(header, "bind_model"):
                header.bind_model()
                mark_active_filters(header)                 # deutsche Filter-Tooltips neu setzen ...
            i18n.translate_widget(table, code)              # ... und in die gewaehlte Sprache uebersetzen
            table._count()
        self.page._store_changed()
        self._update_bands()
        self.page.viewer._page_changed(self.page.preview.page, self.page.preview.page_count())

    # --- Web-Version ---------------------------------------------------------------------------------------------
    def _web_button(self, on: bool) -> None:
        button = self.ribbon.buttons["web_server"]
        button.setChecked(on)
        button.setText("Web-Server\nan" if on else "Web-Server\naus")
        button.setIcon(icons.glyph_icon("connect", LIGHT.ok, 32) if on else icons.ribbon_icon("connect", 32))

    def toggle_web_server(self) -> None:
        if not hasattr(self, "_web"):
            self._web = web_control.WebServerControl()
        if self._web.own_running:
            self._web.stop()
            self._web_button(False)
            self.statusBar().showMessage("Web-Server beendet.", 6000)
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            result = self._web.start()
        finally:
            QApplication.restoreOverrideCursor()
        if result not in ("started", "external"):
            self._web_button(False)
            QMessageBox.warning(self, "Web-Server", result)
            return
        self._web_button(result == "started")
        urls = "\n".join(web_control.addresses(self._web.port))
        intro = ("Der Web-Server läuft." if result == "started" else
                 f"Auf Port {self._web.port} läuft bereits ein Web-Server (z. B. aus dem Launcher oder "
                 "start_web_server.bat) – er wird genutzt.")
        QMessageBox.information(self, "Web-Server", f"{intro}\n\nAdressen für Kollegen im Firmennetz:\n{urls}\n\n"
                                "Quellordner: Einstellungen › Pfade dieses PCs. Der Server läuft, bis du ihn hier "
                                "ausschaltest oder die App schließt.")

    def create_offline_report(self) -> None:
        """Variante 1: Offline-HTML-Bericht der markierten (sonst aller) PDFs (``web/report.py``)."""
        from PySide6.QtWidgets import QFileDialog, QProgressDialog

        from ..web import report
        results = [r for r in (self.marked_results() or self.results) if not r.error]
        if not results:
            QMessageBox.information(self, "Offline-Bericht", "Noch keine PDFs eingelesen.")
            return
        mb = report.estimate_mb(results)
        if mb > 150 and QMessageBox.question(
                self, "Offline-Bericht", f"{len(results)} PDFs ergeben etwa {mb:.0f} MB (ohne Redline). "
                "Trotzdem erstellen?\n\nTipp: nur die benötigten PDFs markieren.") != QMessageBox.Yes:
            return
        start = paths.exports_dir() / f"PDF_Reader_Bericht_{paths.file_timestamp()}.html"
        target, _ = QFileDialog.getSaveFileName(self, "Offline-Bericht speichern", str(start), "HTML (*.html)")
        if not target:
            return
        target = paths.ensure_timestamp(target)
        dlg = QProgressDialog("Offline-Bericht wird erstellt …", "Abbrechen", 0, len(results), self)
        dlg.setWindowTitle("Offline-Bericht")
        dlg.setMinimumDuration(0)

        def progress(i: int, n: int, name: str) -> bool:
            dlg.setValue(i - 1)
            dlg.setLabelText(f"{i} / {n}: {name}")
            QApplication.processEvents()
            return dlg.wasCanceled()

        try:
            out = report.write_report(results, target, progress=progress, title=Path(target).stem)
        except Exception as exc:  # noqa: BLE001
            dlg.close()
            QMessageBox.warning(self, "Offline-Bericht", f"Bericht konnte nicht erstellt werden:\n{exc}")
            return
        dlg.close()
        if QMessageBox.question(self, "Offline-Bericht", f"Gespeichert ({out.stat().st_size / 1e6:.1f} MB):\n{out}\n\n"
                                "Jetzt im Browser öffnen?") == QMessageBox.Yes:
            os.startfile(str(out))  # noqa: S606

    def open_web_version(self) -> None:
        if not hasattr(self, "_web"):
            self._web = web_control.WebServerControl()
        if not web_control.port_open(self._web.port):
            self.toggle_web_server()
        if web_control.port_open(self._web.port):
            self._web.open_browser()

    def show_about(self) -> None:
        QMessageBox.information(self, "Info", f"{APP_NAME} {self.version}\n\nDatenordner: {paths.home_dir()}\n"
                                f"Tool: {paths.tool_root()}\nPython: {os.sys.version.split()[0]}")

    def show_help(self) -> None:
        """Interaktives Handbuch (``assets/help/handbuch.html``, im Browser); ohne die Datei die README."""
        handbook = Path(__file__).resolve().parent.parent / "assets" / "help" / "handbuch.html"
        target = handbook if handbook.is_file() else paths.tool_root() / "README.md"
        if target.is_file():
            os.startfile(str(target))  # noqa: S606

    def closeEvent(self, event) -> None:
        if not self.page.confirm_unsaved():
            event.ignore()
            return
        self.page.viewer.close_window()
        if hasattr(self, "_web"):
            self._web.stop()                               # nur einen selbst gestarteten Server beenden
        if self.project is not None:
            self.project.close()
        if self._worker:
            self._worker.cancel()
        if self._thread:
            self._thread.quit()
            self._thread.wait(3000)
        super().closeEvent(event)
