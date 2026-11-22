"""Datenlink (1.0.30): Excel-Liste importieren, Datenlink 1/2, Abgleich mit Dateiliste und Tag-Tabelle."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from p3d_pdfreader.core.data_link import DataLink, ImportTable, read_sheet, suffixes  # noqa: E402

HEAD = ["P&ID No.", "Tag", "Service", "Leer", "Location"]
ROWS = [["SGOPS-P-DL1-PID-00-EQPM-122", "203-17-336-XV-332", "Process Nitrogen Inlet", None, "203-3-11B"],
        ["SGOPS-P-DL1-PID-00-EQPM-124", "203-17-339-XV-332", "Inlet A2", None, "203-2-13C"],
        ["SGOPS-P-DL1-PID-00-EQPM-124", "203-17-339-XV-330", "Inlet A4", None, None],
        ["SGOPS-P-DL1-PID-00-EQPM-124", "PV-330A", "Exakt", None, "X"]]


def _xlsx(path: Path) -> Path:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Blattuebersicht"
    ws.append(["nur", "info"])
    ws2 = wb.create_sheet("Gesamtliste")
    ws2.append(["Titelzeile"])            # nur ein Eintrag: keine Kopfzeile
    ws2.append(HEAD)
    for r in ROWS:
        ws2.append(r)
    ws2.append([None] * 5)
    wb.save(path)
    return path


def _table(tmp_path) -> ImportTable:
    headers, rows = read_sheet(_xlsx(tmp_path / "liste.xlsx"), "Gesamtliste")
    return ImportTable(source="liste.xlsx", sheet="Gesamtliste", headers=headers, rows=rows,
                       link1="P&ID No.", link2="Tag")


def test_read_sheet_finds_header_and_drops_empty(tmp_path):
    headers, rows = read_sheet(_xlsx(tmp_path / "liste.xlsx"), "Gesamtliste")
    assert headers == HEAD
    assert "Leer" in headers                   # Kopf vorhanden -> Spalte bleibt (Werte leer)
    assert len(rows) == 4 and rows[0][1] == "203-17-336-XV-332"


def test_suffix_and_matching(tmp_path):
    assert suffixes("301-30-149-ti-300") == ["30-149-ti-300", "149-ti-300", "ti-300", "300"]
    t = _table(tmp_path)
    link = DataLink(t, {"files": "Zeichnungsnr.", "tags": "Tag"})
    assert link.active(1) and link.active(2)
    assert link.file_rows("sgops-p-dl1-pid-00-eqpm-124 ") == [1, 2, 3]
    # Endung ab Bindestrich, nur Zeilen derselben Zeichnung
    assert link.tag_rows("XV-332", "SGOPS-P-DL1-PID-00-EQPM-122") == [0]
    assert link.tag_rows("XV-332", "SGOPS-P-DL1-PID-00-EQPM-124") == [1]
    assert sorted(link.tag_rows("XV-332")) == [0, 1]
    assert link.tag_rows("XV-999", "SGOPS-P-DL1-PID-00-EQPM-124") == []
    # exakter Treffer geht vor
    assert link.tag_rows("pv-330a") == [3]
    t.hidden = ["Leer", "P&ID No."]
    link = DataLink(t, {"tags": "Tag"})
    assert not link.active(1) and link.columns == ["Tag", "Service", "Location"]
    assert link.values([0, 1]) == ["203-17-336-XV-332 | 203-17-339-XV-332", "Process Nitrogen Inlet | Inlet A2",
                                   "203-3-11B | 203-2-13C"]


def test_save_and_load(tmp_path):
    t = _table(tmp_path)
    t.hidden = ["Leer"]
    t.save(tmp_path)
    back = ImportTable.load(tmp_path)
    assert back == t
    ImportTable.remove(tmp_path)
    assert ImportTable.load(tmp_path) is None


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_tile_editor_window_full(app, tmp_path):
    """Kachel-Editor als Vollfenster: Ladebildschirm, drei Bereiche, Datenlinks, Export ja/nein, Anpassung bleibt."""
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    from p3d_pdfreader.core.data_link import write_excel
    from p3d_pdfreader.gui.tile_editor import TileEditorWindow
    t = _table(tmp_path)
    t.link1 = ""
    win = TileEditorWindow(t, maximized=False)
    seen = []
    step = win.overlay.step
    win.overlay.step = lambda f, text="": (seen.append((f, text)), step(f, text))
    win.open()
    try:
        assert win.overlay.title == "Kachel-Editor wird geladen …" and not win.overlay.isVisible()
        assert seen[0][1] == "Kachel-Editor wird erstellt …" and seen[-1][0] == 1.0
        assert win.panel is not None and win.panel.state == "ready", win.notes
        assert win.panel.ribbon.tabs.tabText(0) == "Start"                     # Bereich 1, deutsch
        assert win.deck.side_for(win.panel) is not None and win.deck.isVisible()   # Bereich 2: Seitenleiste im Dock
        assert win.model.columnCount() == len(HEAD) and win.model.rowCount() == len(ROWS)   # Bereich 3
        assert win.links == {1: "", 2: "Tag"} and "Datenlink 2" in win.model.headerData(1, Qt.Horizontal)
        win.link_boxes[1].setCurrentIndex(win.link_boxes[1].findData("P&ID No."))
        assert win.links[1] == "P&ID No." and win._link_columns() == {0, 1}
        ctl, keys = win.panel.controller, win.panel.model.keys()
        assert ctl.setExport(keys.index("Leer"), False)                        # Leer nicht uebergeben
        ctl.moveColumn(keys.index("Service"), 0)
        app.processEvents()
        win.source.flush()
        assert win.model.keys()[0] == "Service"
        assert ctl.renameOutput(win.panel.model.keys().index("Location"), "Ort") == ""
        win.source.flush()
        res = win.build_result()
        assert res.headers[0] == "Service" and "Ort" in res.headers and res.hidden == ["Leer"]
        assert res.link1 == "P&ID No." and res.link2 == "Tag" and res.raw_headers == HEAD and res.tile_config
        headers, rows = res.export_view()
        assert "Leer" not in headers and rows[0][0] == "Process Nitrogen Inlet"
        path = write_excel(tmp_path / "out.xlsx", headers, rows)
        assert read_sheet(path)[0] == headers                                  # kompatibel zu "Liste importieren"
        win.grab()
        win.accept()
        assert win.result is not None and not win.isVisible() and win.panel is None
    finally:
        win.close()
    # erneut oeffnen: Anpassung wird auf die Originalliste angewendet
    again = TileEditorWindow(win.result, maximized=False)
    again.open()
    try:
        assert again.build_result().headers == win.result.headers
        assert again.build_result().hidden == ["Leer"] and again.links[1] == "P&ID No."
        assert not again.dirty
    finally:
        again.close()


def test_main_window_link_fields_and_columns(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import main_window
    from p3d_pdfreader.gui.data_link_ui import HITS
    _table(tmp_path).save(paths.config_dir())
    w = main_window.MainWindow(app, "test")
    assert "data_link" in w.ribbon.buttons
    result = PdfResult(path=tmp_path / "a.pdf", drawing_no="SGOPS-P-DL1-PID-00-EQPM-124",
                       tags=[Tag(tag="XV-332", type="Instrument"), Tag(tag="XV-777", type="Instrument")])
    w.results = [result]
    w._refresh()
    assert w.page.files.headers == main_window.FILE_COLS          # ohne Datenlink-Feld keine Zusatzspalten
    # Rechtsklick-Menue des Spaltenkopfs: Eintrag "als Datenlink-Feld setzen"
    from PySide6.QtWidgets import QMenu
    menu = QMenu()
    w.page.files.table._shared_header_menu_hook(menu, main_window.FILE_COLS.index("Zeichnungsnr."))
    act = next(a for a in menu.actions() if "Datenlink-Feld setzen" in a.text())
    act.trigger()
    assert w.links.fields == {"files": "Zeichnungsnr."}
    assert w.page.files.headers[-1] == HITS and w.page.files.rows()[0][-1] == 3
    w.links.set_field("tags", "Tag")
    w.page._store_result, w.page.store = result, None
    w.page._only_duplicates()
    headers = w.page.tags.headers
    assert headers[len(main_window.TAG_COLS)] == HITS and "Tag (Liste)" in headers and "Service" in headers
    rows = {r[1]: r for r in w.page.tags.rows()}
    service = headers.index("Service")
    assert rows["XV-332"][service] == "Inlet A2" and rows["XV-332"][headers.index(HITS)] == 1
    assert rows["XV-777"][headers.index(HITS)] == 0
    # gruener Kopf: Datenlink-Feld wird erkannt, Zeichnen laeuft
    assert w.links._field_columns("tags", w.page.tags) == {main_window.TAG_COLS.index("Tag")}
    w.page.tags.table.horizontalHeader().grab()
    # Feld wieder entfernen -> Spalten weg
    w.links.set_field("tags", "")
    w.page._only_duplicates()
    assert w.page.tags.headers == main_window.TAG_COLS
    w.close()


def test_help_workflow_data():
    """Handbuch-Kapitel "Workflow Schritt fuer Schritt": workflow.js gueltig, alle Bilder vorhanden, Nummern im Bild."""
    import json
    help_dir = Path(__file__).resolve().parent.parent / "src" / "p3d_pdfreader" / "assets" / "help"
    html = (help_dir / "handbuch.html").read_text(encoding="utf-8")
    assert '<script src="workflow.js"></script>' in html and 'id="workflow"' in html
    js = (help_dir / "workflow.js").read_text(encoding="utf-8")
    steps = json.loads(js[js.index("["):js.rindex("]") + 1])
    assert [s["id"] for s in steps][:2] == ["overview", "project"] and len(steps) >= 7
    for step in steps:
        for fig in step["figs"]:
            assert (help_dir / fig["img"]).is_file() and fig["marks"]
            for m in fig["marks"]:
                assert 0 <= m["pin"][0] <= 100 and 0 <= m["pin"][1] <= 100 and m["title"] and m["text"]
