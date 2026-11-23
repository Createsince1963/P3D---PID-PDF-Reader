"""Kachel-Editor als eigenes Vollfenster (Nutzervorgabe 2026-11-22, Vorbild P3D Tag Compliance).

Die eingelesene Excel-Liste wird hier zu einer fuer den P3D PDF Reader kompatiblen Importliste angepasst. Drei Bereiche wie
in Tag Compliance:

1. **Kachel-Editor** (oben): Menueband Start / Umwandeln / Spalte hinzufuegen und die Kacheln (Modul ``column_editor``):
   Spalten verschieben, umbenennen, ausblenden, nicht exportieren, gruppieren, teilen, ersetzen, Wenn-dann-Spalten,
   Spalten aus einer anderen Liste usw. – jeder Schritt ist rueckgaengig zu machen und wird gespeichert.
2. **Seitenleiste** (rechts, Dock ueber die volle Hoehe): aktive Kachel, Gruppe, Verlauf der Schritte.
3. **Datentabelle** (unten): die Liste so, wie sie uebergeben wird; Rechtsklick auf den Spaltenkopf setzt Datenlink 1/2.

Beim Oeffnen deckt ein Ladebildschirm (Zahnrad, Schritt, Prozent) das Fenster ab, bis alles aufgebaut ist.
Ergebnis nach „Uebernehmen und verlinken“: ``self.result`` (``ImportTable`` mit Originalliste, Anpassung und Ergebnis)."""
from __future__ import annotations

import json
import time

from PySide6.QtCore import QEventLoop, Qt, QThread, Signal
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QMenu, QMessageBox, QSplitter, QTableView, QVBoxLayout, QWidget)

from main_gui_kit.buttons import ButtonKind, action_button
from main_gui_kit.tables import MultiColumnFilterProxy, configure_table_view, table_zoom_slider

from ...core.data_link import ImportTable, write_excel
from .. import last_paths
from ..controls import tip_button
from ..design import NOTE_QSS, SECTION_QSS, TITLE_QSS
from . import german
from .deck import SideDeck
from .loading import LoadingOverlay
from .source import ImportSource, SourceTableModel

TITLE = "Datenlink – Importliste anpassen (Kachel-Editor)"
LOADING = "Kachel-Editor wird geladen …"
TABLE_NAMES = {1: "Tabelle 1 – Dateien", 2: "Tabelle 2 – Tags"}
PROFILE_DIR = "last_tile_profile_dir"          # config/state.json: Ordner gespeicherter Anpassungen
READY_TIMEOUT = 15.0                           # s, laengstens auf die QML-Kacheln warten


def marker(n: int) -> str:
    return f"Datenlink {n}"


class TileEditorWindow(QMainWindow):
    finished = Signal(bool)                    # True = uebernommen

    def __init__(self, table: ImportTable, parent=None, *, maximized: bool = True):
        super().__init__(parent, Qt.Window)
        self.table = table
        self.result: ImportTable | None = None
        self.dirty = False
        self.notes: list[str] = []
        self._building = False
        self._closing = False
        self._maximized = maximized
        self.links: dict[int, str] = {1: "", 2: ""}          # Datenlink n -> Spaltenschluessel
        self.source: ImportSource | None = None
        self.panel = None
        self.setWindowTitle(TITLE)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(1500, 950)
        self.overlay = LoadingOverlay(self)
        self.deck = SideDeck(self)

        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)
        lay.addWidget(self._head())
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        self.tiles_box = QWidget()                            # Bereich 1: Kachel-Editor
        self.tiles_lay = QVBoxLayout(self.tiles_box)
        self.tiles_lay.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.tiles_box)
        self.splitter.addWidget(self._table_area())           # Bereich 3: Datentabelle
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 6)
        lay.addWidget(self.splitter, 1)
        self.setCentralWidget(root)
        self.status = QLabel()
        self.status.setStyleSheet(NOTE_QSS)
        self.statusBar().addWidget(self.status, 1)

    # --- Aufbau der Oberflaeche ------------------------------------------------------------------------------------
    def _head(self) -> QWidget:
        box = QFrame()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        row = QHBoxLayout()
        title = QLabel("Importliste anpassen")
        title.setStyleSheet(TITLE_QSS)
        row.addWidget(title)
        row.addSpacing(12)
        self.source_label = QLabel()
        self.source_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.source_label.setStyleSheet(NOTE_QSS)
        row.addWidget(self.source_label, 1)
        self.b_other = tip_button("Andere Excel-Liste …", ButtonKind.SECONDARY,
                                  "Eine andere Excel-Datei bzw. ein anderes Blatt einlesen; die Anpassung (Schritte, "
                                  "Reihenfolge, Namen) wird darauf angewendet")
        self.b_other.clicked.connect(self.reload_other)
        self.b_save_cfg = tip_button("Anpassung speichern …", ButtonKind.SECONDARY,
                                     "Alle Schritte, Reihenfolge, Namen und Export-Einstellungen als Datei speichern – "
                                     "für die nächste Version der Liste")
        self.b_save_cfg.clicked.connect(self.save_adjustment)
        self.b_load_cfg = tip_button("Anpassung laden …", ButtonKind.SECONDARY,
                                     "Gespeicherte Anpassung auf diese Liste anwenden")
        self.b_load_cfg.clicked.connect(self.load_adjustment)
        self.b_excel = tip_button("Als Excel speichern …", ButtonKind.SECONDARY,
                                  "Die angepasste Liste (nur exportierte Spalten) als Excel speichern – kompatibel zu "
                                  "„Liste importieren“")
        self.b_excel.clicked.connect(self.save_excel)
        for b in (self.b_other, self.b_load_cfg, self.b_save_cfg, self.b_excel):
            row.addWidget(b)
        row.addSpacing(16)
        cancel = action_button("Abbrechen", ButtonKind.NEUTRAL)
        cancel.clicked.connect(self.close)
        row.addWidget(cancel)
        self.ok_button = tip_button("Übernehmen und verlinken", ButtonKind.SUCCESS,
                                    "Angepasste Liste speichern und – sobald Datenlinks gesetzt sind – an die Tabellen "
                                    "des Tools übergeben")
        self.ok_button.clicked.connect(self.accept)
        row.addWidget(self.ok_button)
        v.addLayout(row)

        links = QHBoxLayout()
        self.link_boxes: dict[int, QComboBox] = {}
        for n in (1, 2):
            cap = QLabel(f"{marker(n)} ({TABLE_NAMES[n]}):")
            cap.setStyleSheet(SECTION_QSS)
            box_ = QComboBox()
            box_.setMinimumWidth(260)
            box_.setToolTip(f"Spalte der Importliste, die zum Datenlink-Feld der {TABLE_NAMES[n]} passt "
                            f"(im Hauptfenster per Rechtsklick auf den Spaltenkopf setzen)")
            box_.currentIndexChanged.connect(lambda _i, n=n: self._box_changed(n))
            self.link_boxes[n] = box_
            links.addWidget(cap)
            links.addWidget(box_)
            links.addSpacing(16)
        note = QLabel("„Export ja/nein“ bzw. Bereich „Nicht exportiert“ = Spalte wird nicht übergeben · "
                      "Rechtsklick auf den Tabellenkopf = Datenlink setzen")
        note.setStyleSheet(NOTE_QSS)
        links.addWidget(note, 1)
        v.addLayout(links)
        return box

    def _table_area(self) -> QWidget:
        """Datentabelle nach dem Tabellenstandard des Tools (1.0.40, wie Dateiliste/Tag-Tabelle): Filterfeld je Spalte
        (Tippen = Textfilter, Doppelklick = Wertauswahl), Blattfilter, Zeilenzahl, Rechtsklick-Menue (Kopieren,
        Filtern, Spalten …), Excel-Symbol in der Ecke, Zoom. Reihenfolge und Ausblenden der Spalten bestimmt weiter
        der Kachel-Editor; gemerkt wird die Ansicht nicht (Spalten aendern sich mit jeder Anpassung)."""
        from ..data_link_ui import LinkHeaderPainter
        from ..sheet import _filter_height, mark_active_filters, table_header_qss
        from ..table_export import export_table_view, install_excel_corner
        from ..table_menu import install_table_menus
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        top = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("In dieser Tabelle filtern …")
        self.filter.setClearButtonEnabled(True)
        top.addWidget(self.filter, 1)
        self.count = QLabel()
        self.count.setStyleSheet(NOTE_QSS)
        top.addWidget(self.count)
        v.addLayout(top)
        self.view = QTableView()
        self.proxy = MultiColumnFilterProxy(self)
        self.view.setModel(self.proxy)               # noch ohne Daten -> keine gemerkte Ansicht (Kit-Provider)
        configure_table_view(self.view)
        self.view.sortByColumn(-1, Qt.AscendingOrder)    # Zeilen in Listenreihenfolge, Sortieren per Klick moeglich
        self.view.setSelectionBehavior(QAbstractItemView.SelectItems)   # Zellen bearbeiten
        h = self.view.horizontalHeader()
        h.setSectionsMovable(False)                  # Reihenfolge = Kacheln
        h.setStyleSheet(table_header_qss())
        h.setDefaultSectionSize(130)
        mark_active_filters(h)
        h.sectionClicked.connect(self._table_to_tile)
        self.view._shared_header_menu_hook = self._header_hook
        self.view.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
                                  | QAbstractItemView.AnyKeyPressed)
        self.painter = LinkHeaderPainter(h, self._link_columns, _filter_height)
        excel = install_excel_corner(self.view, "Importliste")
        install_table_menus(self.view, excel, on_clear_all=self.clear_filters, on_filter=self._count,
                            on_export=lambda: export_table_view(self.view, "Importliste"))
        self.view.export_name = lambda: "Importliste"
        v.addWidget(self.view, 1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(table_zoom_slider(self.view))
        v.addLayout(bottom)
        self.filter.textChanged.connect(lambda text: (self.proxy.set_global_filter(text), self._count()))
        if hasattr(h, "filterChanged"):
            h.filterChanged.connect(self._count)
        self._count()
        return w

    def _count(self) -> None:
        total = self.proxy.sourceModel().rowCount() if self.proxy.sourceModel() else 0
        self.count.setText(f"{self.proxy.rowCount()} / {total} Zeilen")

    def clear_filters(self) -> None:
        """Blattfilter, Spaltenfilter und Wertauswahl zuruecksetzen."""
        self.filter.clear()
        for editor in getattr(self.view.horizontalHeader(), "editors", []) or []:
            editor.clear()
        self.proxy.column_filters.clear()
        self.proxy.value_filters.clear()
        self.proxy.set_global_filter("")
        self._count()

    # --- Oeffnen / Ablauf --------------------------------------------------------------------------------------------
    def open(self) -> None:
        """Fenster zeigen (Vollbild) und mit Ladebildschirm aufbauen."""
        if self._maximized:
            self.showMaximized()
        else:
            self.show()
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
        self.build()

    def run(self) -> bool:
        """Oeffnen und warten, bis das Fenster geschlossen ist. True = uebernommen (Ergebnis in ``self.result``)."""
        loop = QEventLoop()
        self.finished.connect(loop.quit)
        self.open()
        if self.isVisible():
            loop.exec()
        return self.result is not None

    def build(self) -> None:
        ov = self.overlay
        self._building = True
        ov.begin(LOADING, "Kachel-Editor wird erstellt …")
        try:
            self._create(ov.step)
            ov.step(1.0, "Fertig")
        finally:
            ov.end()
            self._building = False
        self._status()

    def _create(self, step) -> None:
        from ...column_editor import api
        from ...column_editor import tile_editor_host as TH
        from ...column_editor.domain import lookup
        step(0.05, "Kachel-Editor wird erstellt …")
        headers, rows = self.table.base()
        german.prepare()
        TH.set_side_deck(self.deck)                         # Seitenleiste (Bereich 2) im Dock dieses Fensters
        self.source = ImportSource(headers, rows, self)
        self.source.structureChanged.connect(self._structure_changed)
        self.model = SourceTableModel(self.source, self)
        self.model.header_label = self._header_label
        self.model.on_edit = lambda: self._set_dirty(True)
        self.proxy.setSourceModel(self.model)
        self.panel = TH.TileEditorPanel(source=self.source, providers=api.Providers(
            sheet_reader=lookup.default_sheet_reader))
        step(0.25, "Kacheln mit der Tabelle verbinden …")
        german.translate(self.panel.ribbon)
        self.panel.exportRequested.connect(self.save_excel)
        self.panel.configChanged.connect(lambda: self._set_dirty(True))
        self.panel.controller.selectedChanged.connect(self._tile_to_table)
        self.panel.controller.message.connect(lambda m: self.statusBar().showMessage(str(m), 8000))
        self.panel.loadFailed.connect(lambda m: self.notes.append(str(m)))
        self.tiles_lay.addWidget(self.panel)
        step(0.35, "Gespeicherte Anpassung wird angewendet …")
        self._apply_saved()
        step(0.40, "Kachelansicht wird geladen …")
        t0 = time.monotonic()
        while self.panel.state == "loading" and time.monotonic() - t0 < READY_TIMEOUT:
            step(min(0.50, 0.40 + (time.monotonic() - t0) * 0.02), "Kachelansicht wird geladen …")
            QThread.msleep(20)
        step(0.55, "Tabelle wird aufgebaut …")
        self.source.flush()
        self._rebuild()
        step(0.75, "Spaltenbreiten werden angepasst …")
        self._fit_widths(lambda i, n: step(0.75 + 0.23 * i / max(n, 1), "Spaltenbreiten werden angepasst …"))
        self.source_label.setText(f"{self.table.source or '–'}" + (f"  ·  Blatt „{self.table.sheet}“"
                                                                   if self.table.sheet else ""))
        self.dirty = False

    def _apply_saved(self) -> None:
        """Gespeicherte Anpassung (oder bei aelteren Dateien die ausgeblendeten Spalten) anwenden, dann Datenlinks."""
        doc = self.table.tile_config
        if doc:
            from ...column_editor.api import ConfigError
            try:
                self.notes += self.panel.load_config(doc)
            except ConfigError as exc:
                self.notes.append(str(exc))
        elif self.table.hidden:
            keys = self.panel.model.keys()
            for name in self.table.hidden:
                if name in keys:
                    self.panel.controller.setExport(keys.index(name), False)
        self.source.flush()
        for n in (1, 2):
            self.links[n] = self.source.key_for_label(self.table.link(n)) or (
                self.table.link(n) if self.table.link(n) in self.source.keys() else "")

    def _teardown(self) -> None:
        if self.panel is not None:
            self.panel.shutdown()
            self.tiles_lay.removeWidget(self.panel)
            self.panel.hide()
            self.panel.deleteLater()
            self.panel = None

    # --- Tabelle (Bereich 3) -----------------------------------------------------------------------------------------
    def _header_label(self, key: str) -> str:
        marks = [marker(n) for n in (1, 2) if self.links.get(n) == key]
        return self.source.label(key) + ("  » " + " · ".join(marks) if marks else "")

    def _structure_changed(self) -> None:
        self._rebuild()
        if not self._building:
            self._set_dirty(True)

    def _rebuild(self) -> None:
        if self.source is None:
            return
        old_keys = getattr(self, "_keys", None)
        self.model.reset()
        keys = self.model.keys()
        header = self.view.horizontalHeader()
        if keys != old_keys:                         # Spalten geaendert: Filterfelder neu, Spaltenfilter passen nicht mehr
            self._keys = list(keys)
            self.proxy.column_filters.clear()
            self.proxy.value_filters.clear()
            self.proxy.invalidate()
            if hasattr(header, "bind_model"):
                header.bind_model()
                from ..sheet import mark_active_filters
                mark_active_filters(header)
        for c, key in enumerate(keys):
            self.view.setColumnHidden(c, self.source.is_hidden(key))
        self._count()
        for n in (1, 2):
            if self.links[n] and self.links[n] not in keys:
                self.links[n] = ""
        self._fill_boxes()
        self._status()

    def _fit_widths(self, progress=lambda i, n: None) -> None:
        fm = self.view.horizontalHeader().fontMetrics()
        keys = self.model.keys()
        for c, key in enumerate(keys):
            sample = [self.source.value(r, key) for r in range(min(self.source.n_rows, 50))]
            width = max([fm.horizontalAdvance(self._header_label(key)) + 28]
                        + [fm.horizontalAdvance(v) + 16 for v in sample])
            self.view.setColumnWidth(c, max(70, min(320, width)))
            if c % 25 == 0:
                progress(c, len(keys))

    def _link_columns(self) -> set[int]:
        keys = self.model.keys() if self.source is not None else []
        return {keys.index(self.links[n]) for n in (1, 2) if self.links[n] in keys}

    def _key_at(self, column: int) -> str:
        keys = self.model.keys()
        return keys[column] if 0 <= column < len(keys) else ""

    def _header_hook(self, menu: QMenu, column: int) -> None:
        """Eintraege im Spaltenkopf-Menue des Tabellenstandards: Datenlink setzen/entfernen, Kachel waehlen."""
        key = self._key_at(column)
        if not key:
            return
        menu.addSeparator()
        for n in (1, 2):
            if self.links[n] == key:
                menu.addAction(f"{marker(n)} entfernen", lambda n=n: self.set_link(n, ""))
            else:
                menu.addAction(f"Als {marker(n)} setzen ({TABLE_NAMES[n]})", lambda n=n: self.set_link(n, key))
        menu.addAction("Kachel dieser Spalte wählen", lambda: self._table_to_tile(column))

    def set_link(self, n: int, key: str) -> None:
        self.links[n] = key if key in self.source.keys() else ""
        self._set_dirty(True)
        self.view.horizontalHeader().viewport().update()
        self.model.headerDataChanged.emit(Qt.Horizontal, 0, max(0, self.model.columnCount() - 1))
        self._fill_boxes()
        self._status()

    def _fill_boxes(self) -> None:
        keys = self.source.keys() if self.source is not None else []
        for n, box in self.link_boxes.items():
            box.blockSignals(True)
            box.clear()
            box.addItem("(kein Datenlink)", "")
            for key in keys:
                box.addItem(self.source.label(key), key)
            box.setCurrentIndex(max(0, box.findData(self.links[n])))
            box.blockSignals(False)

    def _box_changed(self, n: int) -> None:
        self.set_link(n, self.link_boxes[n].currentData() or "")

    # --- Kachel <-> Tabelle ------------------------------------------------------------------------------------------
    def _tile_to_table(self) -> None:
        if self.panel is None:
            return
        row = self.panel.controller.selectedRow
        tiles = self.panel.model.keys()
        if not 0 <= row < len(tiles):
            return
        keys = self.model.keys()
        if tiles[row] in keys:
            col = keys.index(tiles[row])
            self.view.scrollTo(self.proxy.index(0, col), QAbstractItemView.PositionAtTop)
            self.view.horizontalHeader().setFocus()
            idx = self.proxy.index(max(0, self.view.currentIndex().row()), col)
            self.view.setCurrentIndex(idx)

    def _table_to_tile(self, column: int) -> None:
        key = self._key_at(column)
        if key and self.panel is not None:
            self.panel.controller.select_key(key)

    # --- Aktionen ----------------------------------------------------------------------------------------------------
    def build_result(self) -> ImportTable:
        headers, rows, excluded = self.source.result()
        names = dict(zip(self.source.keys(), headers))
        raw_h, raw_r = self.source.base_rows()
        return ImportTable(source=self.table.source, sheet=self.table.sheet, headers=headers, rows=rows,
                           hidden=excluded, link1=names.get(self.links[1], ""), link2=names.get(self.links[2], ""),
                           raw_headers=raw_h, raw_rows=raw_r,
                           tile_config=self.panel.export_config() if self.panel is not None else {})

    def accept(self) -> None:
        self.result = self.build_result()
        self.dirty = False
        self.close()

    def save_excel(self) -> None:
        t = self.build_result()
        headers, rows = t.export_view()
        if not headers:
            QMessageBox.information(self, "Als Excel speichern", "Es wird keine Spalte exportiert.")
            return
        path = last_paths.save_file(self, "Angepasste Importliste speichern", "Importliste.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            write_excel(path, headers, rows)
        except OSError as exc:
            QMessageBox.warning(self, "Als Excel speichern", f"Die Datei ließ sich nicht schreiben:\n{exc}")
            return
        self.statusBar().showMessage(f"Gespeichert: {path} ({len(rows)} Zeilen, {len(headers)} Spalten)", 12000)

    def save_adjustment(self) -> None:
        if self.panel is None:
            return
        path = last_paths.save_file(self, "Anpassung speichern", "Anpassung_Importliste.json",
                                    "Anpassung (*.json)", kind=PROFILE_DIR)
        if not path:
            return
        doc = {"tile_config": self.panel.export_config(),
               "links": {str(n): self.source.label(k) for n, k in self.links.items() if k}}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False, indent=1)
        except OSError as exc:
            QMessageBox.warning(self, "Anpassung speichern", f"Die Datei ließ sich nicht schreiben:\n{exc}")
            return
        self.statusBar().showMessage(f"Anpassung gespeichert: {path}", 12000)

    def load_adjustment(self, path: str = "") -> list[str]:
        if self.panel is None:
            return []
        if not path:
            files = last_paths.open_files(self, "Anpassung laden", "Anpassung (*.json)", kind=PROFILE_DIR)
            if not files:
                return []
            path = files[0]
        from ...column_editor.api import ConfigError
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
            notes = self.panel.load_config(doc.get("tile_config", doc))
        except (OSError, ValueError, AttributeError, ConfigError) as exc:
            QMessageBox.warning(self, "Anpassung laden", f"Die Anpassung ließ sich nicht anwenden:\n{exc}")
            return []
        self.source.flush()
        for n, name in (doc.get("links") or {}).items():
            key = self.source.key_for_label(str(name))
            if key and str(n) in ("1", "2"):
                self.links[int(n)] = key
        self._rebuild()
        self._set_dirty(True)
        if notes and self.isVisible():
            QMessageBox.information(self, "Anpassung laden", "Hinweise:\n" + "\n".join(notes[:20]))
        return notes

    def reload_other(self) -> None:
        from ..data_link_ui import choose_excel
        new = choose_excel(self)
        if new is None:
            return
        self.replace_list(new)

    def replace_list(self, new: ImportTable) -> None:
        """Andere Liste einlesen: Anpassung und Datenlinks bleiben und werden auf die neue Liste angewendet."""
        cur = self.build_result()
        new.tile_config = cur.tile_config
        new.link1 = new.link1 if not cur.link1 else cur.link1
        new.link2 = new.link2 if not cur.link2 else cur.link2
        self._teardown()
        self.table = new
        self.notes = []
        self.build()
        self._set_dirty(True)
        if self.notes and self.isVisible():
            QMessageBox.information(self, "Andere Excel-Liste", "Hinweise:\n" + "\n".join(self.notes[:20]))

    # --- Zustand ------------------------------------------------------------------------------------------------------
    def _set_dirty(self, dirty: bool) -> None:
        if self._building:
            return
        self.dirty = dirty
        self._status()

    def _status(self) -> None:
        if self.source is None:
            return
        keys = self.source.keys()
        sent = [k for k in keys if k not in self.source.export_excluded]
        links = ", ".join(f"{marker(n)} = „{self.source.label(self.links[n])}“" for n in (1, 2) if self.links[n])
        self.status.setText(f"{self.source.n_rows} Zeilen · {len(sent)} von {len(keys)} Spalten werden übergeben · "
                            f"{links or 'noch kein Datenlink'}" + (" · geändert" if self.dirty else ""))

    def closeEvent(self, e) -> None:  # noqa: N802
        if self.dirty and self.result is None and not self._closing:
            answer = QMessageBox.question(self, TITLE, "Änderungen verwerfen und den Kachel-Editor schließen?")
            if answer != QMessageBox.Yes:
                e.ignore()
                return
        self._closing = True
        self._teardown()
        from ...column_editor import tile_editor_host as TH
        TH.set_side_deck(None)
        super().closeEvent(e)
        self.finished.emit(self.result is not None)
