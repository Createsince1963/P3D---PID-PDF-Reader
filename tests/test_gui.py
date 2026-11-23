"""GUI-Rauchtest (offscreen): Fenster bauen, eine PDF scannen, Tabellen gefuellt."""
from __future__ import annotations

import os
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

from test_extract import SAMPLE, needs_sample  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@needs_sample
def test_scan_fills_tables(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui.main_window import MainWindow
    w = MainWindow(app, "test")
    w.scan([SAMPLE])
    start = time.time()
    while w._thread is not None and time.time() - start < 30:
        app.processEvents()
    assert w.page.files.proxy.rowCount() == 1
    assert w.page.tags.proxy.rowCount() > 100
    assert w.all_page.tags.proxy.rowCount() == w.page.tags.proxy.rowCount()
    w.close()


@needs_sample
def test_occurrence_navigation_and_review(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.No)
    from p3d_pdfreader.gui.main_window import MainWindow
    from p3d_pdfreader.gui.review_dialog import ReviewOptions
    w = MainWindow(app, "test")
    w.scan([SAMPLE])
    start = time.time()
    while w._thread is not None and time.time() - start < 30:
        app.processEvents()
    page = w.page
    rows = page.tags.rows()
    dup = next(i for i, r in enumerate(rows) if r[2] > 1)
    page.tags.table.selectRow(page.tags.proxy.mapFromSource(page.tags.proxy.sourceModel().index(dup, 0)).row())
    assert page._focus is None                          # erst Uebersicht
    page.next_occurrence()
    assert page._focus == 0
    for _ in range(rows[dup][2]):
        page.next_occurrence()
    assert page._focus is None                          # nach der letzten wieder Uebersicht
    folder = w.run_review(w.results, ReviewOptions(False, True, True, True, True, str(tmp_path)))
    names = sorted(p.suffix for p in folder.iterdir())
    assert names == [".pdf", ".xlsx", ".xlsx"]                 # Redline, Review je PDF, Review gesamt
    w.close()


@needs_sample
def test_edit_mode_save_and_excel_table(app, tmp_path, monkeypatch):
    """Bearbeiten: Feld setzen -> Datum/User automatisch; Speichern -> beim erneuten Laden da; Export als Datentabelle."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from PySide6.QtCore import Qt
    import openpyxl
    from p3d_pdfreader.core import review
    from p3d_pdfreader.core.review_store import ReviewStore
    from p3d_pdfreader.gui.main_window import MainWindow
    from p3d_pdfreader.gui.table_export import visible_table, write_view
    w = MainWindow(app, "test")
    w.scan([SAMPLE])
    start = time.time()
    while w._thread is not None and time.time() - start < 30:
        app.processEvents()
    page = w.page
    proxy = page.tags.proxy
    from p3d_pdfreader.gui.main_window import FIRST_FIELD
    f = FIRST_FIELD                                          # Spalte "Review" (nach Typ, Tag, Anzahl, Seiten, Projekt-Spalten)
    index = proxy.index(0, f)
    assert not proxy.setData(index, "OK")                    # ohne Bearbeiten-Modus nicht editierbar
    page.edit_button.setChecked(True)
    assert proxy.setData(index, "OK")
    assert proxy.setData(proxy.index(0, f + 4), "WPO-4711")      # Spalte "WPO"
    row = [proxy.index(0, c).data() for c in range(proxy.columnCount())]
    assert row[f] == "OK" and row[f + 4] == "WPO-4711" and row[f + 5] and row[f + 6]    # Datum, User automatisch
    assert page.save_button.isEnabled()
    assert page.save_review()
    stored = ReviewStore(SAMPLE).values(row[0], row[1])
    assert stored[0] == "OK" and stored[4] == "WPO-4711"
    headers, rows = visible_table(page.tags.table)
    assert headers[-2:] == ["Datum", "User"]
    out = tmp_path / "tags.xlsx"
    write_view(str(out), "Tags", headers, rows)
    ws = openpyxl.load_workbook(out).active
    assert ws.tables and ws.column_dimensions["A"].width > 6
    review.write_review_xlsx(tmp_path / "rev.xlsx", w.results)
    ws = openpyxl.load_workbook(tmp_path / "rev.xlsx")["Review"]
    head = [c.value for c in ws[1]]
    assert head[-2:] == ["Datum", "User"] and "WPO" in head and ws.tables
    page.edit_button.setChecked(False)
    w.close()


def test_no_filters_at_start_and_after_new_data(app, tmp_path, monkeypatch):
    """1.0.39: gemerkte Filter (Wertauswahl „Checked“, Textfilter) kommen weder beim Start noch nach neuen Daten zurueck;
    Spaltenbreiten und Co. bleiben gemerkt."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from PySide6.QtCore import QCoreApplication
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import table_views
    from p3d_pdfreader.gui.main_window import MainWindow
    layout = {"column_filters": {"PDF": "zzz"}, "value_filters": {"Checked": []}, "column_widths": {"PDF": 321}}
    plain = table_views.store()
    for key in ("auto|files", "named|files"):
        plain.save(key, "Default", dict(layout))
    assert table_views.layout_store().load("auto|files") == {"column_widths": {"PDF": 321}}
    w = MainWindow(app, "test")
    w.results = [PdfResult(path=tmp_path / "a.pdf", drawing_no="A", tags=[Tag(tag="XV-1", type="Instrument")]),
                 PdfResult(path=tmp_path / "b.pdf", drawing_no="B", tags=[])]
    w._refresh()
    for _ in range(5):
        QCoreApplication.processEvents()
    proxy = w.page.files.proxy
    assert not proxy.column_filters and not proxy.value_filters
    assert proxy.rowCount() == 2
    w.close()


def test_table_preview_uses_tag_table_columns(app, tmp_path, monkeypatch):
    """1.0.40: Tabellen-Vorschau = Tags aller PDFs mit den Spalten der Tag-Tabelle (Reihenfolge, Ausblendung wie
    eingestellt), ohne X/Y; ungespeicherte Review-Eintraege der gewaehlten PDF sind enthalten."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui.main_window import FIRST_FIELD, TAG_COLS, MainWindow
    w = MainWindow(app, "test")
    a = PdfResult(path=tmp_path / "a.pdf", drawing_no="DWG-A", tags=[Tag(tag="XV-1", type="Instrument")])
    b = PdfResult(path=tmp_path / "b.pdf", drawing_no="DWG-B",
                  tags=[Tag(tag="PI-2", type="Instrument"), Tag(tag="VH1", type="Armatur")])
    w.results = [a, b]
    w._refresh()
    page = w.page
    page.files.table.setCurrentIndex(page.files.proxy.index(0, 0))
    page.edit_button.setChecked(True)
    assert page.tags.proxy.setData(page.tags.proxy.index(0, FIRST_FIELD), "OK")
    page.edit_button.setChecked(False)
    view = page.tags.table
    view.setColumnHidden(TAG_COLS.index("Seiten"), True)
    header = view.horizontalHeader()
    header.moveSection(header.visualIndex(TAG_COLS.index("Review")), 0)       # Review ganz nach vorn
    w.show_table_preview()
    t = w.preview_page.tags
    assert w.tabs.currentWidget() is w.preview_page
    assert t.headers[:4] == ["PDF", "Zeichnungsnr.", "Review", "Typ"]
    assert "Seiten" not in t.headers and "X" not in t.headers and "Y" not in t.headers
    rows = {(r[0], r[t.headers.index("Tag")]): r for r in t.rows()}
    assert len(rows) == 3 and rows[(page._store_result.name, page.tags.rows()[0][1])][2] == "OK"
    assert page.save_review()                                # sonst fragt close() modal nach
    w.close()


def test_msgbox_clicked_survives_translation(app):
    """Uebersetzter Dialog (Englisch): der gemerkte Button wird trotz neuem Python-Wrapper erkannt (Bug 1.0.37:
    "Discard" wirkte wie "Cancel", Fenster liess sich mit ungespeicherten Review-Eintraegen nicht schliessen)."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QMessageBox
    from p3d_pdfreader import i18n
    from p3d_pdfreader.gui import msgbox
    previous = i18n._state.get("lang")
    i18n.install(app, "en")
    try:
        for label in ("Discard", "Save", "Cancel"):
            box = QMessageBox(QMessageBox.Question, "Review-Einträge", "x")
            save = box.addButton("Speichern", QMessageBox.AcceptRole)
            discard = box.addButton("Verwerfen", QMessageBox.DestructiveRole)
            box.addButton("Abbrechen", QMessageBox.RejectRole)
            QTimer.singleShot(50, lambda b=box, t=label: next(x for x in b.buttons() if x.text() == t).click())
            box.exec()
            expected = {"Discard": discard, "Save": save, "Cancel": None}[label]
            assert msgbox.clicked(box, save, discard) is expected
    finally:
        i18n._state["lang"] = previous


@needs_sample
def test_choose_tags_when_filter_active(app, tmp_path, monkeypatch):
    """Ohne Filter alle Tags; mit "Nur doppelte" Rueckfrage (hier: "Alle Tags" gewaehlt -> alle)."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from PySide6.QtWidgets import QMessageBox
    from p3d_pdfreader.gui.main_window import MainWindow
    w = MainWindow(app, "test")
    w.scan([SAMPLE])
    start = time.time()
    while w._thread is not None and time.time() - start < 30:
        app.processEvents()
    result = w.page.current_result()
    assert len(w._choose_tags(result, "t")) == len(result.tags)
    w.page.dup_button.setChecked(True)

    def pick_all(box):
        box.setProperty("picked", next(b for b in box.buttons() if b.text().startswith("Alle")))
        box.clickedButton = lambda: box.property("picked")
        return 0
    monkeypatch.setattr(QMessageBox, "exec", pick_all)
    assert len(w._choose_tags(result, "t")) == len(result.tags)
    w.page.dup_button.setChecked(False)
    w.close()


def test_pipe_option_rescans_and_is_remembered(app, tmp_path, monkeypatch):
    """Menueband „Rohrleitungen“: Option an -> PDFs werden neu eingelesen, Rohrleitungsnummern in der Tag-Liste."""
    from test_extract import _pipe_pdf
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui.main_window import MainWindow
    pdf = _pipe_pdf(tmp_path / "pipes.pdf")

    def wait(w):
        start = time.time()
        while w._thread is not None and time.time() - start < 30:
            app.processEvents()

    w = MainWindow(app, "test")
    assert not w.pipes_enabled()
    w.scan([pdf])
    wait(w)
    w.page.files.table.selectRow(0)
    assert "Rohrleitung" not in {r[0] for r in w.page.tags.rows()}
    assert w.ribbon.buttons["pipes"].text().endswith("aus")
    w.ribbon.buttons["pipes"].click()                  # an -> neu einlesen
    assert w.ribbon.buttons["pipes"].text().endswith("an")
    wait(w)
    w.page.files.table.selectRow(0)
    assert sum(r[0] == "Rohrleitung" for r in w.page.tags.rows()) == 4
    w.close()
    w2 = MainWindow(app, "test")
    assert w2.pipes_enabled()                          # gemerkt in config/state.json
    w2.close()


def test_viewer_second_monitor_full_width_and_back(app, tmp_path, monkeypatch):
    """2. Monitor: Tag-Tabelle ueber die ganze Breite, Zurueckholen-Knopf ueber der Tabelle; zurueck = Standardteilung.
    Dazu die neuen Knoepfe "Aus PDF-Scan übernehmen" und "Autofill OK" vor "Bearbeiten"."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui.main_window import SCAN_COL, TAG_COLS, VIEWER_SPLIT, MainWindow
    w = MainWindow(app, "test")
    w.resize(1600, 900)
    w.show()
    app.processEvents()
    page = w.page
    keys = list(page.tags.layout().itemAt(1).widget().buttons)
    assert keys.index("scan_fields") < keys.index("autofill") < keys.index("edit")
    assert TAG_COLS[SCAN_COL:] == ["Ersteller", "Checked", "Rev", "Rev-Datum", "Rev-Text"]
    page.viewer.monitor_button.setChecked(True)
    app.processEvents()
    assert page._viewer_host.isHidden() and not page.viewer_away.isHidden()
    page.viewer.monitor_button.setChecked(False)
    app.processEvents()
    assert not page._viewer_host.isHidden() and page.viewer_away.isHidden()
    left, right = page._hsplit.sizes()
    # Standardteilung, ausser die Mindestbreite der Tag-Tabelle (Knopfleiste) laesst weniger nicht zu
    expected = VIEWER_SPLIT[0] / sum(VIEWER_SPLIT)
    assert right > 0
    assert abs(left / (left + right) - expected) < 0.05 or left <= page.tags.minimumSizeHint().width() + 2
    w.close()
