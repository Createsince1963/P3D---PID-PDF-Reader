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
    w.pipe_action.trigger()                            # an -> neu einlesen
    wait(w)
    w.page.files.table.selectRow(0)
    assert sum(r[0] == "Rohrleitung" for r in w.page.tags.rows()) == 4
    w.close()
    w2 = MainWindow(app, "test")
    assert w2.pipes_enabled()                          # gemerkt in config/state.json
    w2.close()
