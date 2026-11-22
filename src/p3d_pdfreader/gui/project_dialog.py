"""Projektmodus: Projekt anlegen / oeffnen / aus P3D Tag Compliance uebernehmen und der Verwaltungsdialog
"Projektdefinitionen" (bearbeitbare Datenbank, Aufbau wie in Tag Compliance: links die Tabellen und Listen mit
Zeilenzahl, rechts die Tabelle; Listen anlegen, Spalten, Liste aus Excel, Excel-Export/-Import, Uebernahme aus Tag
Compliance, Tag testen). Daten und Pruefung: ``core.project_defs`` (ohne Qt). Farben nur aus design/appearance/Kit."""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QDialog, QFileDialog, QFormLayout, QGroupBox,
                               QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidgetItem, QMessageBox,
                               QSplitter, QTableWidget, QVBoxLayout, QWidget)

from main_gui_kit.buttons import ButtonKind, action_button

from .. import paths
from ..core.patterns import TAG_TYPES
from ..core.project_defs import (DEFAULT_DESIGNS, RULES, SEGMENTS, SETTING_NOTES, SETTINGS, ProjectDB, is_list)
from . import last_paths
from .design import ERROR_QSS, NOTE_QSS, SECTION_QSS
from .paths_dialog import open_in_explorer
from .project_tiles import ColumnTiles, GridEditing, TileList, load_json_meta
from .sheet import table_header_qss
from .table_export import export_table_view
from .controls import tip_button

TILES_ON = "defs_tile_editor_on"          # config/state.json: Kachel-Editor zuletzt ein/aus
TILE_ORDER, TILE_NAMES = "tile_order", "tile_names"   # Projekt-Datenbank (meta): Kachelreihenfolge und -namen links
TC_KIND = "last_tag_compliance_dir"     # config/state.json: zuletzt gewaehlter Ordner der Tag-Compliance-Datenbank
DB_FILTER = "Projekt-Datenbank (*.db);;Alle Dateien (*.*)"

HINTS = {
    SEGMENTS: "Quelle: Tabelle (z. B. def_function_codes), Liste mit Spalte (list:media|Medium Code (Fluid)), "
              "const:TEXT (feste Zeichen), seq:3 (laufende Nummer, 3 Stellen), free (freier Text). prefix/suffix = "
              "Trennzeichen davor/danach, required/visible = yes/no. Eine Tag-Struktur = alle Zeilen mit gleichem "
              "tag_type, Reihenfolge nach pos.",
    RULES: "pdf_type = Tag-Typ des PDF Readers (" + ", ".join(TAG_TYPES) + "); tag_type = Tag-Struktur mit Segmenten "
           "(Tabelle „Tag segments“). Mehrere Strukturen je Typ möglich – ein Tag ist OK, wenn er zu einer passt. "
           "enabled = ja/nein. Typen ohne Regel werden nicht geprüft.",
    SETTINGS: "from_char = falsches Trennzeichen, to_char = richtiges (Projektregel aus Tag Compliance). Passt ein "
              "Tag erst nach dem Ersetzen, nennt die Prüfung die Trennzeichen-Regel.",
}


# ----------------------------------------------------------------------------------------------------------------
# Projekt anlegen / oeffnen / uebernehmen
# ----------------------------------------------------------------------------------------------------------------
def _ask_name(parent, title: str, default: str = "") -> str:
    name, ok = QInputDialog.getText(parent, title, "Projektname:", text=default)
    name = name.strip() if ok else ""
    return "".join(c if c.isalnum() or c in " -_.()" else "_" for c in name).strip()


def _target(parent, name: str) -> Path | None:
    path = paths.projects_dir() / f"{name}.db"
    if path.exists():
        QMessageBox.warning(parent, "Projekt", f"Ein Projekt „{name}“ gibt es schon:\n{path}\n\n"
                                               "Bitte „Projekt öffnen“ nutzen oder einen anderen Namen wählen.")
        return None
    return path


def new_project(parent) -> Path | None:
    """Leeres Projekt (nur die mitgelieferten Tag-Strukturen und Pruefregeln) in ``<Datenordner>/projects``."""
    name = _ask_name(parent, "Neues Projekt")
    if not name:
        return None
    path = _target(parent, name)
    if path is None:
        return None
    ProjectDB.create(path, name).close()
    return path


def open_project(parent) -> Path | None:
    file, _ = QFileDialog.getOpenFileName(parent, "Projekt öffnen", str(paths.projects_dir()), DB_FILTER)
    if not file:
        return None
    try:
        ProjectDB(file).close()
    except Exception as exc:  # noqa: BLE001 - keine gueltige Datenbank
        QMessageBox.warning(parent, "Projekt öffnen", f"Keine gültige Projekt-Datenbank:\n{exc}")
        return None
    return Path(file).resolve()


def pick_tag_compliance_db(parent) -> str:
    """Datenbank von P3D Tag Compliance waehlen (``pidtag_project.db``); der Ordner wird gemerkt."""
    file, _ = QFileDialog.getOpenFileName(parent, "Projektdatenbank von P3D Tag Compliance wählen (pidtag_project.db)",
                                          last_paths.get(TC_KIND), DB_FILTER)
    if file:
        last_paths.remember(TC_KIND, file)
    return file


def import_project(parent) -> Path | None:
    """Neues Projekt mit den Definitionen aus P3D Tag Compliance (Quelle wird nur gelesen)."""
    source = pick_tag_compliance_db(parent)
    if not source:
        return None
    name = _ask_name(parent, "Projekt aus Tag Compliance übernehmen", Path(source).parent.parent.name)
    if not name:
        return None
    path = _target(parent, name)
    if path is None:
        return None
    try:
        with ProjectDB.create(path, name) as db:
            counts = db.import_tag_compliance(source)
    except Exception as exc:  # noqa: BLE001
        if path.exists():
            path.unlink()
        QMessageBox.warning(parent, "Übernahme", f"Übernahme fehlgeschlagen:\n{exc}")
        return None
    QMessageBox.information(parent, "Übernahme", _counts_text(counts))
    return path


def _counts_text(counts: dict[str, int]) -> str:
    rows = sum(counts.values())
    return (f"Aus P3D Tag Compliance übernommen: {len(counts)} Tabellen/Listen, {rows} Zeilen.\n"
            "Die Quelle wurde nur gelesen. Die Prüfregeln des PDF Readers bleiben erhalten.")


# ----------------------------------------------------------------------------------------------------------------
# Verwaltungsdialog
# ----------------------------------------------------------------------------------------------------------------
class ProjectDefinitionsDialog(GridEditing, QDialog):
    """Bearbeitbare Projektdefinitionen. ``changed`` ist True, sobald etwas gespeichert wurde (Pruefung neu bauen)."""

    def __init__(self, db: ProjectDB, parent=None):
        super().__init__(parent)
        self.db = db
        self.changed = False
        self.dirty = False
        self.table_key: str | None = None
        self.db_cols: list[str] = []
        self.db_key: str | None = None                   # Tabelle, die gerade im Raster steht
        self.column_tiles = None
        self._loading = False
        self.setWindowTitle("Projektdefinitionen (bearbeitbare Datenbank)")
        self.resize(1320, 820)
        root = QVBoxLayout(self)

        head = QGroupBox("Projekt")
        form = QFormLayout(head)
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit(db.name)
        name_row.addWidget(self.name_edit, 1)
        self._button(name_row, "Name speichern", ButtonKind.NEUTRAL, self._save_name)
        form.addRow("Projektname", name_row)
        file_row = QHBoxLayout()
        self.file_label = QLabel(str(db.path))
        self.file_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        file_row.addWidget(self.file_label, 1)
        self._button(file_row, "Ordner öffnen", ButtonKind.NEUTRAL, lambda: open_in_explorer(db.path))
        form.addRow("Projekt-Datenbank", file_row)
        source_row = QHBoxLayout()
        self.source_label = QLabel()
        self.source_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        source_row.addWidget(self.source_label, 1)
        self._button(source_row, "Aus Tag Compliance übernehmen …", ButtonKind.PRIMARY, self._import_tc)
        form.addRow("Quelle Tag Compliance", source_row)
        root.addWidget(head)

        actions = QHBoxLayout()
        self._button(actions, "Excel-Export …", ButtonKind.PRIMARY, self._export_xlsx)
        self._button(actions, "Excel-Import …", ButtonKind.PRIMARY, self._import_xlsx)
        self._button(actions, "Standard-Prüfregeln …", ButtonKind.NEUTRAL, self._reset_rules)
        actions.addStretch(1)
        self._button(actions, "Schließen", ButtonKind.NEUTRAL, self.close)
        root.addLayout(actions)

        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        caption = QLabel("Tabellen und Listen")
        caption.setStyleSheet(SECTION_QSS)
        left_lay.addWidget(caption)
        self.list = TileList()
        self.list.currentItemChanged.connect(self._table_changed)
        self.list.reordered.connect(self._tiles_reordered)
        self.list.renameRequested.connect(self._rename_tile)
        left_lay.addWidget(self.list, 1)
        for text, kind, slot in (("+ Neue Liste …", ButtonKind.SECONDARY, self._new_list),
                                 ("Liste aus Excel …", ButtonKind.SECONDARY, self._list_from_excel),
                                 ("Spalten …", ButtonKind.NEUTRAL, self._columns),
                                 ("Liste löschen", ButtonKind.DANGER, self._delete_list)):
            b = action_button(text, kind)
            b.clicked.connect(slot)
            left_lay.addWidget(b)
        split.addWidget(left)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setStyleSheet(SECTION_QSS)
        top.addWidget(self.title_label)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("In dieser Tabelle filtern …")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply_filter)
        top.addWidget(self.filter, 1)
        self.tiles_button = tip_button("Kachel-Editor", ButtonKind.PRIMARY,
                                       "Spalten als Kacheln: verschieben, ein-/ausblenden, umbenennen, einfügen, "
                                       "löschen (Rechtsklick auf eine Kachel)")
        self.tiles_button.setCheckable(True)
        self.tiles_button.toggled.connect(self._tiles_toggled)
        top.addWidget(self.tiles_button)
        self._button(top, "Ansicht nach Excel …", ButtonKind.PROCESS, self.export_view)
        right_lay.addLayout(top)
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(NOTE_QSS)
        right_lay.addWidget(self.hint)
        self.grid = QTableWidget()
        # bearbeitbares Raster: Kit-Kopf und Zeilenhoehe, aber ohne Sortierung/Spaltenfilter (Zeilenfolge bleibt)
        self.grid.setAlternatingRowColors(True)
        self.grid.verticalHeader().setDefaultSectionSize(22)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.horizontalHeader().setStyleSheet(table_header_qss())
        self.grid.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.grid.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
                                  | QAbstractItemView.AnyKeyPressed)
        self.grid.itemChanged.connect(self._edited)
        self.grid.setToolTip("Rechtsklick: Zeilen, Zellen und Spalten bearbeiten (auch auf Zeilennummern und "
                             "Spaltenköpfe); Strg+Z/Strg+Y rückgängig/wiederholen, Strg+C/Strg+V wie Excel")
        self.install_grid_functions()
        self.column_tiles = ColumnTiles(self)
        self.column_tiles.hide()
        right_lay.addWidget(self.column_tiles)
        right_lay.addWidget(self.grid, 1)
        edit_row = QHBoxLayout()
        self._button(edit_row, "+ Zeile", ButtonKind.SECONDARY, self._add_row)
        self._button(edit_row, "Zeile löschen", ButtonKind.DANGER, self._delete_rows)
        edit_row.addStretch(1)
        self.status = QLabel()
        self.status.setStyleSheet(NOTE_QSS)
        edit_row.addWidget(self.status)
        self.discard_button = self._button(edit_row, "Verwerfen", ButtonKind.NEUTRAL, self._discard)
        self.save_button = self._button(edit_row, "Speichern", ButtonKind.SUCCESS, self.save_table)
        right_lay.addLayout(edit_row)
        split.addWidget(right)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 4)
        split.setSizes([260, 1040])
        root.addWidget(split, 1)

        test = QGroupBox("Tag testen (gegen die gespeicherten Definitionen)")
        test_lay = QHBoxLayout(test)
        self.test_type = QComboBox()
        self.test_type.addItems(list(TAG_TYPES))
        self.test_tag = QLineEdit()
        self.test_tag.setPlaceholderText("Tag eingeben, z. B. 111PMP01")
        self.test_result = QLabel()
        self.test_result.setWordWrap(True)
        test_lay.addWidget(self.test_type)
        test_lay.addWidget(self.test_tag, 1)
        test_lay.addWidget(self.test_result, 2)
        self.test_type.currentIndexChanged.connect(self._test)
        self.test_tag.textChanged.connect(self._test)
        root.addWidget(test)

        self._checker = None
        self._fill_list()
        self._update_source()
        self._set_dirty(False)
        self.tiles_button.setChecked(bool(last_paths.get_value(TILES_ON, False)))

    # --- Hilfen ------------------------------------------------------------------------------------------------
    @staticmethod
    def _button(layout, text: str, kind: ButtonKind, slot):
        b = action_button(text, kind)
        b.clicked.connect(slot)
        layout.addWidget(b)
        return b

    def _update_source(self) -> None:
        source, when = self.db.meta("source"), self.db.meta("imported")
        self.source_label.setText(f"{source}   (übernommen {when})" if source else "– (noch nichts übernommen)")

    def _fill_list(self, select: str | None = None) -> None:
        select = select or self.table_key
        self._loading = True
        self.list.clear()
        names = load_json_meta(self.db, TILE_NAMES, {})
        for key, title, _cols in self._ordered_tables():
            item = QListWidgetItem(f"{names.get(key) or title}  ({self.db.count(key)})")
            item.setData(Qt.UserRole, key)
            tip = "Liste" if is_list(key) else ("Tabelle des PDF Readers" if key in (RULES, SETTINGS)
                                                else "Definitionstabelle (wie Tag Compliance)")
            item.setToolTip(f"{tip}: {key}")
            self.list.addItem(item)
        self._loading = False
        keys = [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]
        self.list.setCurrentRow(keys.index(select) if select in keys else 0)

    def _ordered_tables(self) -> list:
        """Tabellen in der Kachelreihenfolge des Nutzers; unbekannte bleiben in ihrer ueblichen Reihenfolge am Ende."""
        rank = {k: i for i, k in enumerate(load_json_meta(self.db, TILE_ORDER, []))}
        return sorted(self.db.tables(), key=lambda t: rank.get(t[0], len(rank)))

    def _tiles_reordered(self) -> None:
        order = [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]
        self.db.set_meta(TILE_ORDER, json.dumps(order))

    def _rename_tile(self, row: int) -> None:
        """Kachel umbenennen (nur Anzeige, die Tabelle behaelt ihren Namen); leer = urspruenglicher Titel."""
        item = self.list.item(row)
        if item is None:
            return
        key = item.data(Qt.UserRole)
        title, _cols = self.db.info(key)
        names = load_json_meta(self.db, TILE_NAMES, {})
        name, ok = QInputDialog.getText(self, "Kachel umbenennen", f"Name der Kachel (Original: {title}).\n"
                                        "Leer = Originalname.", text=names.get(key, title))
        if not ok:
            return
        name = name.strip()
        if name and name != title:
            names[key] = name
        else:
            names.pop(key, None)
        self.db.set_meta(TILE_NAMES, json.dumps(names, ensure_ascii=False))
        self._fill_list(self.table_key)

    def columns_editable(self) -> bool:
        return bool(self.table_key) and is_list(self.table_key)

    def _tiles_toggled(self, on: bool) -> None:
        last_paths.set_value(TILES_ON, bool(on))
        self.column_tiles.setVisible(on)
        if on:
            self.column_tiles.refresh()

    def toggle_tiles(self) -> None:
        self.tiles_button.setChecked(not self.tiles_button.isChecked())

    def export_view(self) -> None:
        """Sichtbare Spalten in angezeigter Reihenfolge und die gefilterten Zeilen nach Excel/CSV."""
        export_table_view(self.grid, self.title_label.text() or "Projektdefinitionen")

    def _set_dirty(self, dirty: bool) -> None:
        self.dirty = dirty
        self.save_button.setEnabled(dirty)
        self.discard_button.setEnabled(dirty)
        self.status.setText("ungespeicherte Änderungen" if dirty else "")

    def confirm_unsaved(self) -> bool:
        if not self.dirty:
            return True
        box = QMessageBox(QMessageBox.Question, "Projektdefinitionen",
                          f"Änderungen in „{self.title_label.text()}“ speichern?", parent=self)
        save = box.addButton("Speichern", QMessageBox.AcceptRole)
        discard = box.addButton("Verwerfen", QMessageBox.DestructiveRole)
        box.addButton("Abbrechen", QMessageBox.RejectRole)
        box.setDefaultButton(save)
        box.exec()
        if box.clickedButton() is save:
            return self.save_table()
        if box.clickedButton() is discard:
            self._set_dirty(False)
            return True
        return False

    # --- Tabelle ----------------------------------------------------------------------------------------------
    def _table_changed(self, current, previous) -> None:
        if self._loading or current is None:
            return
        key = current.data(Qt.UserRole)
        if key == self.table_key:
            return
        if not self.confirm_unsaved():
            self._loading = True
            self.list.setCurrentItem(previous)
            self._loading = False
            return
        self.load_table(key)

    def load_table(self, key: str) -> None:
        self.table_key = key
        title, _cols = self.db.info(key)
        same = key == self.db_key                        # nach Speichern/Verwerfen: Ansicht (ausgeblendet, Breiten) bleibt
        hidden = self._hidden_labels() if same else set()
        cols, rows = self.db.read(key)
        self.db_cols, self.db_key = list(cols), key
        self.set_grid(list(cols), rows, hidden)
        if not same:
            self.grid.resizeColumnsToContents()
            for c in range(len(cols)):
                self.grid.setColumnWidth(c, min(420, max(80, self.grid.columnWidth(c))))
        self.reset_undo()
        self.title_label.setText(title)
        hint = HINTS.get(key, "")
        if key == SETTINGS:
            hint += "  " + ", ".join(f"{k}: {v}" for k, v in SETTING_NOTES.items())
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self._apply_filter(self.filter.text())
        self._set_dirty(False)

    def rows(self) -> list[list[str]]:
        """Zeilen zum Speichern: Listen in Anzeigereihenfolge der Spalten, feste Tabellen in ihrer Spaltenfolge."""
        labels, rows = self.grid_data()
        if self.columns_editable():
            return rows
        pos = [labels.index(c) for c in self.db_cols]
        return [[r[p] for p in pos] for r in rows]

    def _edited(self, _item) -> None:
        if not self._loading:
            self.cell_edited()
            self._set_dirty(True)

    def _apply_filter(self, text: str) -> None:
        text = text.strip().casefold()
        for r in range(self.grid.rowCount()):
            cells = [self.grid.item(r, c).text() if self.grid.item(r, c) else "" for c in range(self.grid.columnCount())]
            self.grid.setRowHidden(r, bool(text) and not any(text in c.casefold() for c in cells))

    def _add_row(self) -> None:
        if self.table_key is None:
            return
        r = self.grid.rowCount()
        self.insert_rows(r)
        first = self.grid.horizontalHeader().logicalIndex(0)
        self.grid.scrollToBottom()
        self.grid.setCurrentCell(r, first)
        self.grid.editItem(self.grid.item(r, first))

    def _delete_rows(self) -> None:
        self.delete_rows()

    def _discard(self) -> None:
        if self.table_key:
            self.load_table(self.table_key)

    def save_table(self) -> bool:
        if self.table_key is None:
            return True
        labels = self.grid_data()[0]
        columns = labels if self.columns_editable() and labels != self.db_cols else None
        try:
            n = self.db.save(self.table_key, self.rows(), columns)
        except ValueError as exc:
            QMessageBox.warning(self, "Speichern", str(exc))
            return False
        self.changed = True
        self._checker = None
        self._set_dirty(False)
        self._fill_list(self.table_key)
        self.load_table(self.table_key)
        self.status.setText(f"Gespeichert: {n} Zeilen")
        self._test()
        return True

    # --- Listen ------------------------------------------------------------------------------------------------
    def _new_list(self) -> None:
        if not self.confirm_unsaved():
            return
        name, ok = QInputDialog.getText(self, "Neue Liste", "Kurzname (a-z, 0-9, _):")
        if not ok or not name.strip():
            return
        title, ok = QInputDialog.getText(self, "Neue Liste", "Titel:", text=name.strip())
        if not ok:
            return
        cols, ok = QInputDialog.getMultiLineText(self, "Neue Liste", "Spalten (eine je Zeile):", "Code\nLabel")
        if not ok:
            return
        try:
            key = self.db.create_list(name, title, cols.splitlines())
        except ValueError as exc:
            QMessageBox.warning(self, "Neue Liste", str(exc))
            return
        self.changed = True
        self._fill_list(key)

    def _list_from_excel(self) -> None:
        if not self.confirm_unsaved():
            return
        files = last_paths.open_files(self, "Liste aus Excel importieren", "Excel (*.xlsx)")
        if not files:
            return
        from openpyxl import load_workbook
        try:
            wb = load_workbook(files[0], read_only=True, data_only=True)
            try:
                names = wb.sheetnames
                sheet = names[0]
                if len(names) > 1:
                    sheet, ok = QInputDialog.getItem(self, "Liste aus Excel", "Blatt:", names, 0, False)
                    if not ok:
                        return
                data = [list(r) for r in wb[sheet].iter_rows(values_only=True)]
            finally:
                wb.close()
            if not data:
                raise ValueError("Das Blatt ist leer.")
            cols = [str(c).strip() for c in data[0] if c is not None and str(c).strip()]
            default = "".join(c if c.isalnum() else "_" for c in sheet.lower()).strip("_")[:30]
            name, ok = QInputDialog.getText(self, "Liste aus Excel", "Kurzname der Liste (a-z, 0-9, _):",
                                            text=default if default[:1].isalpha() else "liste_" + default)
            if not ok:
                return
            key = self.db.create_list(name, sheet, cols)
            n = self.db.save(key, [[("" if v is None else v) for v in r[:len(cols)]] for r in data[1:]])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Liste aus Excel", str(exc))
            return
        self.changed = True
        self._fill_list(key)
        self.status.setText(f"Liste angelegt: {n} Zeilen")

    def _columns(self) -> None:
        key = self.table_key
        if not key or not is_list(key):
            QMessageBox.information(self, "Spalten", "Spalten lassen sich nur bei Listen ändern.")
            return
        if not self.confirm_unsaved():
            return
        title, cols = self.db.info(key)
        text, ok = QInputDialog.getMultiLineText(self, "Spalten", "Spalten (eine je Zeile; Zellen behalten ihre "
                                                                  "Position, neue Spalten sind leer):", "\n".join(cols))
        if not ok:
            return
        try:
            self.db.set_list_columns(key, text.splitlines())
        except ValueError as exc:
            QMessageBox.warning(self, "Spalten", str(exc))
            return
        self.changed = True
        self.table_key = None
        self._fill_list(key)

    def _delete_list(self) -> None:
        key = self.table_key
        if not key or not is_list(key):
            QMessageBox.information(self, "Liste löschen", "Nur Listen lassen sich löschen, feste Tabellen nicht.")
            return
        title, _cols = self.db.info(key)
        if QMessageBox.question(self, "Liste löschen", f"Liste „{title}“ mit {self.db.count(key)} Zeilen löschen?\n"
                                "Das lässt sich nicht rückgängig machen (vorher Excel-Export möglich).",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.db.delete_list(key)
        self.changed = True
        self._set_dirty(False)
        self.table_key = None
        self._fill_list()

    # --- Projekt -----------------------------------------------------------------------------------------------
    def _save_name(self) -> None:
        name = self.name_edit.text().strip()
        if name:
            self.db.set_meta("name", name)
            self.changed = True

    def _import_tc(self) -> None:
        if not self.confirm_unsaved():
            return
        source = pick_tag_compliance_db(self)
        if not source:
            return
        answer = QMessageBox.question(self, "Aus Tag Compliance übernehmen",
                                      "Alle Definitionstabellen und Listen dieses Projekts werden durch die aus Tag "
                                      f"Compliance ersetzt:\n{source}\n\nDie Prüfregeln des PDF Readers bleiben "
                                      "erhalten. Vorher einen Excel-Export als Sicherung anlegen?",
                                      QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if answer == QMessageBox.Cancel:
            return
        if answer == QMessageBox.Yes:
            self._export_xlsx()
        try:
            counts = self.db.import_tag_compliance(source)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Übernahme", f"Übernahme fehlgeschlagen (nichts geändert):\n{exc}")
            return
        self.changed = True
        self._checker = None
        self._update_source()
        self.table_key = None
        self._fill_list()
        QMessageBox.information(self, "Übernahme", _counts_text(counts))

    def _export_xlsx(self) -> None:
        if not self.confirm_unsaved():
            return
        path = last_paths.save_file(self, "Projektdefinitionen als Excel", f"{self.db.name}_Definitionen.xlsx",
                                    "Excel (*.xlsx)", paths.exports_dir())
        if not path:
            return
        try:
            self.db.export_xlsx(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Excel-Export", str(exc))
            return
        if QMessageBox.question(self, "Excel-Export", f"Gespeichert:\n{path}\n\nOrdner öffnen?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            open_in_explorer(path)

    def _import_xlsx(self) -> None:
        if not self.confirm_unsaved():
            return
        files = last_paths.open_files(self, "Projektdefinitionen aus Excel", "Excel (*.xlsx)")
        if not files:
            return
        if QMessageBox.question(self, "Excel-Import", "Jedes Blatt mit dem Namen einer Tabelle ersetzt deren Inhalt "
                                "(Format wie Excel-Export, auch Exporte von Tag Compliance). Unbekannte Blätter "
                                "werden neue Listen.\n\nFortfahren?",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        try:
            counts = self.db.import_xlsx(files[0])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Excel-Import", str(exc))
            return
        self.changed = True
        self._checker = None
        self.table_key = None
        self._fill_list()
        QMessageBox.information(self, "Excel-Import", f"{len(counts)} Tabellen/Listen, {sum(counts.values())} Zeilen "
                                                      "eingelesen.")

    def _reset_rules(self) -> None:
        if not self.confirm_unsaved():
            return
        names = ", ".join(DEFAULT_DESIGNS)
        if QMessageBox.question(self, "Standard-Prüfregeln", "Prüfregeln und die mitgelieferten Tag-Strukturen "
                                f"({names}) auf den Standard zurücksetzen?\nAndere Tabellen bleiben unverändert.",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.db.ensure_defaults(force=True)
        self.changed = True
        self._checker = None
        self.table_key = None
        self._fill_list()

    # --- Tag testen --------------------------------------------------------------------------------------------
    def _test(self) -> None:
        tag = self.test_tag.text().strip()
        if not tag:
            self.test_result.setText("")
            return
        if self._checker is None:
            self._checker = self.db.checker()
        result = self._checker.check(self.test_type.currentText(), tag)
        if not result.status:
            text, qss = "keine Prüfregel für diesen Typ", NOTE_QSS
        else:
            text, qss = f"{result.status}: {result.hint}", ("" if result.status == "OK" else ERROR_QSS)
        self.test_result.setText(text)
        self.test_result.setStyleSheet(qss)

    def closeEvent(self, event) -> None:
        if self.confirm_unsaved():
            event.accept()
        else:
            event.ignore()
