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
        # 1.0.40: Tabellenstandard - Filterfeld je Spalte, Wertauswahl, Blattfilter, Zeilenzahl, Kopf-Menue
        header = win.view.horizontalHeader()
        assert len(header.editors) == len(HEAD)
        win.proxy.set_filter_values(HEAD.index("P&ID No."), ["SGOPS-P-DL1-PID-00-EQPM-124"])
        win._count()
        assert win.proxy.rowCount() == 3 and win.count.text() == "3 / 4 Zeilen"
        win.filter.setText("exakt")
        assert win.proxy.rowCount() == 1
        win.clear_filters()
        assert win.proxy.rowCount() == 4 and not win.proxy.value_filters
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        win._header_hook(menu, HEAD.index("Service"))
        assert any("Als Datenlink 2 setzen" in a.text() for a in menu.actions())
        assert [win.proxy.index(r, 0).data() for r in range(4)] == [r[0] for r in ROWS]   # Listenreihenfolge
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
    # 1.0.44: Dateiliste zeigt keine Importspalten, Datenlink 1 bleibt aktiv (Abgleich)
    assert w.page.files.headers == main_window.FILE_COLS
    assert w.links.active(1) and w.links.link.columns
    assert len(w.links.link.file_rows("SGOPS-P-DL1-PID-00-EQPM-124")) == 3
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


def test_file_link_by_pdf_name(tmp_path):
    """1.0.40: Datenlink-Feld „PDF“ (Dateiname mit .pdf, ggf. Kopie „ (2)“) findet die Zeichnung der Importliste,
    damit auch die Tags dieser PDF (Beispiel PIT-107 in UTLY-002)."""
    from p3d_pdfreader.core.data_link import file_variants
    assert file_variants("A-PID-1 (2).PDF") == ["A-PID-1 (2).PDF", "A-PID-1 (2)", "A-PID-1"]
    link = DataLink(_table(tmp_path), {"files": "PDF", "tags": "Tag"})
    assert link.file_rows("SGOPS-P-DL1-PID-00-EQPM-124.pdf") == [1, 2, 3]
    assert link.file_rows("SGOPS-P-DL1-PID-00-EQPM-124 (3).pdf") == [1, 2, 3]
    assert link.tag_rows("XV-332", "SGOPS-P-DL1-PID-00-EQPM-124.pdf") == [1]
    assert link.match_count(1, ["SGOPS-P-DL1-PID-00-EQPM-122.pdf", "X.pdf"]) == (1, 2)


def test_tag_join_modes(tmp_path):
    """1.0.38: PDF -> Liste, Liste -> PDF, beide; Importzeilen nur der eigenen Zeichnung; fehlend = n.a."""
    from p3d_pdfreader.core.data_link import JOIN_BOTH, JOIN_LIST, JOIN_PDF, NA
    link = DataLink(_table(tmp_path), {"files": "Zeichnungsnr.", "tags": "Tag"})
    dwg = "SGOPS-P-DL1-PID-00-EQPM-124"
    values = ["XV-332", "XV-777"]                         # XV-332 -> Zeile 1, XV-777 nicht in der Liste
    assert link.tag_join(values, dwg, JOIN_PDF) == [(0, [1]), (1, [])]
    assert link.tag_join(values, dwg, JOIN_LIST) == [(0, [1]), (None, [2]), (None, [3])]
    assert link.tag_join(values, dwg, JOIN_BOTH) == [(0, [1]), (1, []), (None, [2]), (None, [3])]
    assert link.values_or_na([]) == [NA] * len(link.columns)
    no_dwg = DataLink(_table(tmp_path), {"tags": "Tag"})  # ohne Datenlink 1: alle Importzeilen
    assert [i for i, _h in no_dwg.tag_join(["PV-330A"], None, JOIN_BOTH)] == [0, None, None, None]


def test_tag_table_join_and_filter_reset(app, tmp_path, monkeypatch):
    """Tag-Tabelle: Abgleich „beide“ zeigt Importzeilen ohne PDF-Tag mit n.a. (nicht bearbeitbar); PDF-Wechsel setzt
    die Filter der Tag-Tabelle zurueck."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.core.data_link import JOIN_BOTH, JOIN_LIST, NA
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import main_window
    _table(tmp_path).save(paths.config_dir())
    w = main_window.MainWindow(app, "test")
    a = PdfResult(path=tmp_path / "a.pdf", drawing_no="SGOPS-P-DL1-PID-00-EQPM-124",
                  tags=[Tag(tag="XV-332", type="Instrument"), Tag(tag="XV-777", type="Instrument")])
    b = PdfResult(path=tmp_path / "b.pdf", drawing_no="SGOPS-P-DL1-PID-00-EQPM-122",
                  tags=[Tag(tag="XV-332", type="Instrument")])
    w.results = [a, b]
    w._refresh()
    w.links.set_field("files", "Zeichnungsnr.")
    w.links.set_field("tags", "Tag")
    page = w.page
    page.files.table.setCurrentIndex(page.files.proxy.index(0, 0))
    page.set_join_mode(JOIN_BOTH)
    headers, rows = page.tags.headers, page.tags.rows()
    service = headers.index("Service")
    assert [r[1] for r in rows] == ["XV-332", "XV-777", NA, NA]
    assert rows[1][service] == NA and rows[2][service] == "Inlet A4" and rows[2][2] == 0
    page.edit_button.setChecked(True)
    model = page.tags.proxy.sourceModel()
    assert not (model.flags(model.index(2, main_window.FIRST_FIELD)) & Qt.ItemIsEditable)
    assert model.flags(model.index(0, main_window.FIRST_FIELD)) & Qt.ItemIsEditable
    page.edit_button.setChecked(False)
    page.set_join_mode(JOIN_LIST)
    assert [r[1] for r in page.tags.rows()] == ["XV-332", NA, NA]
    # Filter setzen, PDF wechseln -> Standard
    page.tags.filter.setText("XV")
    page.dup_button.setChecked(True)
    page.files.table.setCurrentIndex(page.files.proxy.index(1, 0))
    assert page._store_result is b
    assert page.tags.filter.text() == "" and not page.dup_button.isChecked()
    assert page.tags.proxy.rowCount() == page.tags.proxy.sourceModel().rowCount()
    w.links.set_join_mode("pdf")
    w.close()


def test_link_columns_toggle_menu_and_fold(app, tmp_path, monkeypatch):
    """1.0.43: Importspalten ein/aus mit getrennten Layout-Schluesseln, Menue Importliste (Link aufheben),
    Dateiliste ein-/ausklappen (gemerkt)."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import last_paths, main_window
    _table(tmp_path).save(paths.config_dir())
    w = main_window.MainWindow(app, "test")
    a = PdfResult(path=tmp_path / "a.pdf", drawing_no="SGOPS-P-DL1-PID-00-EQPM-124",
                  tags=[Tag(tag="XV-332", type="Instrument")])
    w.results = [a]
    w._refresh()
    page, view = w.page, w.page.tags.table
    page.files.table.setCurrentIndex(page.files.proxy.index(0, 0))
    assert not page.link_cols_button.isEnabled() and view.layout_key == "tags"
    w.links.set_field("files", "Zeichnungsnr.")
    w.links.set_field("tags", "Tag")
    assert page.link_cols_button.isEnabled() and page.link_cols_button.isChecked()
    assert len(page.tags.headers) > len(main_window.TAG_COLS) and view.layout_key == "tags_link"
    assert view._shared_layout_store[1] == "auto|tags_link"
    page.link_cols_button.setChecked(False)                   # Importspalten aus -> eigenes Layout, nur Tool-Spalten
    assert page.tags.headers == main_window.TAG_COLS and view.layout_key == "tags"
    assert view._shared_layout_store[1] == "auto|tags" and not page.join_button.isEnabled()
    assert last_paths.get_value("data_link_tags_shown") is False and w.links.fields.get("tags") == "Tag"
    page.link_cols_button.setChecked(True)
    assert view.layout_key == "tags_link"
    page._fill_link_menu()
    texts = [a.text() for a in page.link_menu.actions() if a.text()]
    assert any(t.startswith("Link aufheben") for t in texts) and "Liste neu einlesen …" in texts
    next(a for a in page.link_menu.actions() if a.text().startswith("Link aufheben")).trigger()
    assert "tags" not in w.links.fields and page.tags.headers == main_window.TAG_COLS
    assert not page.link_cols_button.isEnabled()
    # Dateiliste einklappen / aufklappen
    page.fold_button.setChecked(True)
    assert page.files.table.isHidden() and page.fold_button.text() == "Aufklappen"
    assert last_paths.get_value("files_collapsed") is True
    page.fold_button.setChecked(False)
    assert not page.files.table.isHidden() and page.fold_button.text() == "Einklappen"
    w.close()


def test_match_count_and_samples(tmp_path):
    link = DataLink(_table(tmp_path), {"files": "Zeichnungsnr.", "tags": "Tag"})
    assert link.match_count(1, ["SGOPS-P-DL1-PID-00-EQPM-124", "GIBT-ES-NICHT", "", None]) == (1, 2)
    assert link.match_count(2, ["NIX-1", "NIX-2"]) == (0, 2)
    assert link.samples(1) == ["SGOPS-P-DL1-PID-00-EQPM-122", "SGOPS-P-DL1-PID-00-EQPM-124"]


def test_relink_warns_without_common_values(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import main_window
    _table(tmp_path).save(paths.config_dir())
    w = main_window.MainWindow(app, "test")
    shown = []
    monkeypatch.setattr(main_window.QMessageBox, "warning", lambda *a, **k: shown.append(a[2]))
    w.results = [PdfResult(path=tmp_path / "a.pdf", drawing_no="ANDERE-ZEICHNUNG",
                           tags=[Tag(tag="XX-1", type="Instrument")])]
    w.links.set_field("files", "Zeichnungsnr.")
    assert len(shown) == 1 and "Datenlink 1" in shown[0] and "ANDERE-ZEICHNUNG" in shown[0]
    w.links.set_field("tags", "Tag")
    assert "Datenlink 2" in shown[-1]
    w.results[0].drawing_no = "SGOPS-P-DL1-PID-00-EQPM-124"
    w.results[0].tags[0].tag = "XV-332"
    shown.clear()
    w._relink()
    assert shown == []
    w.close()


def test_table_profile_roundtrip(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui import table_profiles as tp
    stored = tp.stored_layouts({"auto|a": {"profiles": {"Default": {"column_order": ["x"]}}, "last_profile": "Default"},
                                "named|a": {"profiles": {"P": {"column_order": ["y"]}}}})
    assert stored == {"auto|a": {"column_order": ["x"]}}
    profile = tp.build_profile(stored, {"auto|b": {"column_order": ["z"]}}, "1.0.34")
    assert set(profile["tables"]) == {"auto|a", "auto|b"}
    path = tmp_path / "profil.json"
    import json
    path.write_text(json.dumps(profile), encoding="utf-8")
    assert tp.load_profile(path) == (2, 0)
    assert tp.table_views.store().load("auto|b", "Default") == {"column_order": ["z"]}
    assert tp.save_profile(tmp_path / "neu.json") >= 2       # plus offene Tabellen anderer Tests
    with pytest.raises(ValueError):
        tp.parse_profile({"format": "fremd"})


def test_review_rows_status(tmp_path):
    from p3d_pdfreader.core import data_link as dl
    table = _table(tmp_path)
    link = DataLink(table, {"files": "Zeichnungsnr.", "tags": "Tag"})
    pdfs = [("b.pdf", "SGOPS-P-DL1-PID-00-EQPM-124",
             [("Instrument", "XV-332", 1, "1", "203-17-339-XV-332"), ("Instrument", "XX-9", 1, "1", "XX-9")])]
    headers, rows = dl.review_rows(link, pdfs)
    assert headers[:len(dl.REVIEW_HEAD)] == dl.REVIEW_HEAD and "Service" in headers
    status = {(r[0], r[4] or r[7]) for r in rows}
    assert (dl.STATUS_OK, "XV-332") in status and (dl.STATUS_NOT_IN_LIST, "XX-9") in status
    counts = dl.review_summary(rows)
    assert counts[dl.STATUS_NOT_IN_PDF] == 2            # zwei weitere Zeilen der gescannten Zeichnung ...124
    assert counts[dl.STATUS_NO_PDF] == 1                # Zeichnung ...122 nicht gescannt
    assert dl.review_rows(DataLink(table, {"files": "Zeichnungsnr."}), pdfs)[1] == []   # ohne Datenlink 2


def test_main_window_link_review_sheet(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.core import data_link as dl
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import main_window
    _table(tmp_path).save(paths.config_dir())
    w = main_window.MainWindow(app, "test")
    assert "link_review" in w.ribbon.buttons
    w.results = [PdfResult(path=tmp_path / "a.pdf", drawing_no="SGOPS-P-DL1-PID-00-EQPM-124",
                           tags=[Tag(tag="XV-332", type="Instrument")])]
    w.links.set_field("files", "Zeichnungsnr.")
    w.links.set_field("tags", "Tag")
    w.show_link_review()
    assert w.tabs.currentWidget() is w.review_page
    rows = w.review_page.tags.rows()
    assert rows[0][0] == dl.STATUS_OK and len(rows) == 4
    w.close()


def test_main_window_project_save_and_load(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.gui import main_window
    _table(tmp_path).save(paths.config_dir())
    w = main_window.MainWindow(app, "test")
    monkeypatch.setattr(main_window.QMessageBox, "question", lambda *a, **k: main_window.QMessageBox.Yes)
    path = paths.projects_dir() / "Test.db"
    from p3d_pdfreader.core.project_defs import ProjectDB
    ProjectDB.create(path, "Test").close()
    w.activate_project(path)
    w.links.set_field("tags", "Tag")
    assert w.save_project()
    w.links.set_field("tags", "")
    w.links.remove()
    assert w.links.table is None
    assert w.load_project_settings(ask=False)
    assert w.links.table is not None and w.links.fields == {"tags": "Tag"}
    w.close()
