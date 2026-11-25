"""Projektmodus: Projekt-Datenbank (Schema wie P3D Tag Compliance), Uebernahme, Pruefung, Excel, GUI-Umschaltung."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from p3d_pdfreader.core.project_defs import (CODE_MISSING, DUPLICATE, FAULT, INCOMPLETE, OK, RULES,  # noqa: E402
                                             SEGMENTS, STRUCTURES, ProjectDB)


def _tc_db(path: Path) -> Path:
    """Kleine Datenbank im Schema von P3D Tag Compliance (pidtag_project.db) mit Lizenz-/Fremdtabellen."""
    con = sqlite3.connect(path)
    con.executescript("""
        create table settings(key text primary key, value text not null);
        create table meta(key text primary key, value text);
        create table def_meta(key text primary key, value text);
        create table def_function_codes(code text, description text);
        create table def_fitting_types(code text primary key, description text);
        create table def_building_codes(code text primary key, description text);
        create table def_system_codes(code text primary key, description text);
        create table def_pipeclass(code text primary key, description text);
        create table def_tag_structures(tag_type text primary key, example text, structure text, note text);
        create table def_lists(name text primary key, title text not null, columns text not null,
            builtin integer not null default 0, source text default '', pos integer not null default 0);
        create table def_list_rows(list_name text not null, pos integer not null, data text not null);
    """)
    con.executemany("insert into settings values(?,?)", [("from_char", "-"), ("to_char", "_"), ("safe_regex", "x")])
    con.execute("insert into meta values('lic_sig','secret')")
    con.execute("insert into def_meta values('project','Testprojekt')")
    con.executemany("insert into def_function_codes values(?,?)", [("PMP", "Pump"), ("REA", "Reactor")])
    con.executemany("insert into def_fitting_types values(?,?)", [("VH", "Hand valve"), ("CKV", "Check valve")])
    con.executemany("insert into def_building_codes values(?,?)", [("203", "B203")])
    con.executemany("insert into def_system_codes values(?,?)", [("17", "S17")])
    con.executemany("insert into def_pipeclass values(?,?)", [("ST10", "Steel")])
    con.execute("insert into def_tag_structures values('EQUIPMENT','SG20_201_18_310TCU01','x','legend')")
    con.execute("insert into def_lists values('media','Media list','[\"Sr.No\", \"Medium Code (Fluid)\"]',1,'',1)")
    con.executemany("insert into def_list_rows values('media',?,?)",
                    [(0, json.dumps(["001", "PFC"])), (1, json.dumps(["002", "TFHR"]))])
    con.commit()
    con.close()
    return path


@pytest.fixture()
def project(tmp_path):
    db = ProjectDB.create(tmp_path / "Projekt.db", "Projekt")
    db.import_tag_compliance(_tc_db(tmp_path / "pidtag_project.db"))
    yield db
    db.close()


def test_create_has_default_rules_and_designs(tmp_path):
    with ProjectDB.create(tmp_path / "Neu.db", "Neu") as db:
        assert db.name == "Neu"
        assert db.rules()["Equipment"] == ["PDF_EQUIPMENT"]
        assert "PDF_PIPE_LINE" in db.designs() and db.count(RULES) == 6
    with pytest.raises(FileExistsError):
        ProjectDB.create(tmp_path / "Neu.db", "Neu")


def test_import_from_tag_compliance_reads_only(project, tmp_path):
    source = tmp_path / "pidtag_project.db"
    before = source.read_bytes()
    assert project.count("def_function_codes") == 2
    assert project.count("list:media") == 2
    assert project.read("def_meta")[1] == [["project", "Testprojekt"]]
    assert project.meta("source") == str(source.resolve())
    assert "meta" not in {r[0] for r in project.con.execute("select name from sqlite_master")}   # Lizenzdaten nicht
    assert source.read_bytes() == before                                       # Quelle unveraendert
    assert project.rules() and "PDF_EQUIPMENT" in project.designs()            # eigene Regeln/Strukturen bleiben


def test_checker_ok_fault_and_hints(project):
    ch = project.checker()
    assert ch.check("Equipment", "111PMP01").status == OK
    r = ch.check("Equipment", "111XYZ01")
    assert r.status == CODE_MISSING and "Function code „XYZ“" in r.hint
    assert ch.check("Armatur", "VH340").status == OK
    assert ch.check("Armatur", "BDI-102").status == FAULT
    r = ch.check("Volltag", "203-17-111-TZIT-011")
    assert r.status == FAULT == "Regelfehler Projektdefinition" and "Trennzeichen" in r.hint   # "-" statt "_"
    assert ch.check("Volltag", "203_17_111_TZIT-011").status == OK
    assert ch.check("Rohrleitung", '203_17_112PFC_ST10_013_1"').status == OK
    assert ch.check("Rohrleitung", 'TFHR_ST10_001_1 1/2"').status == OK
    assert ch.check("Rohrleitung", '151_HOS_206_1"').status == OK
    assert "Fluid code" in ch.check("Rohrleitung", 'XYZ_ST10_001_1"').hint
    r = ch.check("Rohrleitung", '203_17_152_PFC_ST10_001_1"')                  # ueberzaehliges "_": kein fehlender Code
    assert r.status == FAULT
    assert ch.check("Zeichnungsverweis", "ABC-PID-001").status == ""            # keine Regel = nicht geprueft


def test_checker_incomplete_missing_and_duplicate_together(project):
    """Platzhalter X/? = Code unvollstaendig; fehlender Code; Trennzeichen; mehrfach - alles zusammen gemeldet."""
    ch = project.checker()
    assert ch.check("Rohrleitung", 'TFHR_ST10_XXX_2"').status == INCOMPLETE
    assert ch.check("Armatur", "VHXXX").status == INCOMPLETE
    assert ch.check("Equipment", "111PMP0?").status == INCOMPLETE
    assert ch.check("Equipment", "111XXX01").status == INCOMPLETE                 # Code nur aus X = Platzhalter
    r = ch.check("Rohrleitung", 'TFHR_ST10_XXX_2"', count=3)
    assert r.status == f"{INCOMPLETE} + {DUPLICATE}" and "3×" in r.hint
    r = ch.check("Volltag", "203-17-1XX-TZIT-011", count=2)
    assert r.status == f"{INCOMPLETE} + {FAULT} + {DUPLICATE}"
    r = ch.check("Rohrleitung", 'LTCHW_ST1X_001_1"')                              # beides: fehlt + unvollstaendig
    assert r.status == f"{INCOMPLETE} + {CODE_MISSING}"
    assert ch.check("Equipment", "111REX01").status == CODE_MISSING               # X in Buchstaben-Code: fehlt
    assert ch.check("Equipment", "111PMP01", count=2).status == OK                # doppelt allein: kein Projekt-Befund
    assert ch.is_fault("Armatur", "VHXXX") and not ch.is_fault("Armatur", "VH340")


def test_placeholder_tags_only_in_project_mode(tmp_path):
    from test_extract import _pipe_pdf

    from p3d_pdfreader.core.extract import read_pdf
    pdf = _pipe_pdf(tmp_path / "pipes.pdf")
    plain = {t.tag for t in read_pdf(pdf, pipes=True).tags}
    assert 'AV_TL02_XXX_2"' not in plain                                           # Standard wie bisher
    tags = {t.tag for t in read_pdf(pdf, pipes=True, placeholders=True).tags}
    assert 'AV_TL02_XXX_2"' in tags and plain <= tags


def test_edit_tables_lists_and_rules(project):
    project.save("def_function_codes", [["XYZ", "Neu"], ["PMP", "Pump"], ["", ""]])
    assert project.read("def_function_codes")[1] == [["PMP", "Pump"], ["XYZ", "Neu"]]     # sortiert, Leerzeile weg
    assert project.checker().check("Equipment", "111XYZ01").status == OK
    with pytest.raises(ValueError):
        project.save("def_fitting_types", [["VH", "a"], ["VH", "b"]])                     # doppelter Schluessel
    assert project.count("def_fitting_types") == 2                                         # nichts veraendert
    key = project.create_list("suffix", "Suffixe", ["Code", "Label"])
    project.save(key, [["A", "a"]])
    project.set_list_columns(key, ["Code", "Label", "Extra"])
    assert project.read(key) == (["Code", "Label", "Extra"], [["A", "a", ""]])
    project.delete_list(key)
    assert key not in [t for t, _x, _c in project.tables()]
    with pytest.raises(ValueError):
        project.create_list("settings", "x", ["a"])
    rows = [r for r in project.read(RULES)[1] if r[0] != "Equipment"]
    project.save(RULES, rows)
    assert project.checker().check("Equipment", "111XYZ01").status == ""


def test_reimport_keeps_own_designs(project, tmp_path):
    segs = [r for r in project.read(SEGMENTS)[1] if r[0] == "PDF_VALVE"]
    segs[1][3] = "seq:4"                                          # eigene Aenderung an einer PDF-Struktur
    other = [r for r in project.read(SEGMENTS)[1] if r[0] != "PDF_VALVE"]
    project.save(SEGMENTS, other + segs)
    project.import_tag_compliance(tmp_path / "pidtag_project.db")
    assert project.checker().check("Armatur", "VH3400").status == OK


def test_excel_roundtrip(project, tmp_path):
    out = project.export_xlsx(tmp_path / "defs.xlsx")
    project.save("def_function_codes", [])
    counts = project.import_xlsx(out)
    assert counts["def_function_codes"] == 2 and project.count("list:media") == 2


def test_status_hits_project_faults(project):
    from types import SimpleNamespace

    from p3d_pdfreader.core.review_store import status_hits
    tags = [SimpleNamespace(type="Equipment", tag="111PMP01", hits=[(0, (1, 1, 2, 2))]),
            SimpleNamespace(type="Equipment", tag="111XYZ01", hits=[(0, (3, 3, 4, 4))]),
            SimpleNamespace(type="Equipment", tag="111ABC01", hits=[(0, (5, 5, 6, 6))])]
    store = SimpleNamespace(entries={"Equipment|111ABC01": {"Review": "Nicht relevant"}})
    ok, faulty = status_hits(tags, store, project.checker())
    assert faulty == [[(0, (3, 3, 4, 4))]] and len(ok) == 2                   # angenommene Abweichung = gruen
    ok, faulty = status_hits(tags, store)                                       # Standardmodus wie bisher
    assert not faulty


def _equipment_pdf(path: Path) -> Path:
    import pymupdf
    with pymupdf.open() as doc:
        page = doc.new_page(width=800, height=600)
        for i, text in enumerate(("111PMP01", "111XYZ01", "VH340", "VHXXX")):
            page.insert_text((50, 100 + 50 * i), text, fontsize=9)
        doc.save(path)
    return path


def _icon_green(button) -> bool:
    """Hat das Symbol des Knopfs ueberwiegend gruene Pixel (Projektmodus an)?"""
    image = button.icon().pixmap(32, 32).toImage()
    green = other = 0
    for x in range(image.width()):
        for y in range(image.height()):
            c = image.pixelColor(x, y)
            if c.alpha() > 128:
                if c.green() > c.red() + 40 and c.green() > c.blue() + 20:
                    green += 1
                else:
                    other += 1
    return green > other


def test_gui_project_mode_toggle(tmp_path, monkeypatch):
    """Menueband: Projektmodus an -> Pruefspalten sichtbar, Abweichung rot; aus -> Standard wie bisher; gemerkt."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path / "home"))
    from p3d_pdfreader import paths
    from p3d_pdfreader.gui.main_window import CHECK_COL, MainWindow
    from p3d_pdfreader.gui.project_dialog import ProjectDefinitionsDialog
    db_path = paths.projects_dir() / "P1.db"
    with ProjectDB.create(db_path, "P1") as db:
        db.import_tag_compliance(_tc_db(tmp_path / "pidtag_project.db"))
    pdf = _equipment_pdf(tmp_path / "eq.pdf")

    def wait():
        start = time.time()
        while w._thread is not None and time.time() - start < 30:
            app.processEvents()
        w.page.files.table.selectRow(0)
        app.processEvents()

    w = MainWindow(app, "test")
    assert w.checker is None and not w.ribbon.buttons["project_mode"].isChecked()
    w.scan([pdf])
    wait()
    assert w.page.tags.table.isColumnHidden(CHECK_COL)                          # Standardmodus: keine Pruefspalten
    assert all(r[CHECK_COL] == "" for r in w.page.tags.rows())
    assert "VHXXX" not in {r[1] for r in w.page.tags.rows()}                    # Platzhalter nur im Projektmodus
    assert w.activate_project(db_path)
    wait()                                                                       # neu eingelesen (Platzhalter)
    rows = {r[1]: r for r in w.page.tags.rows()}
    assert rows["111PMP01"][CHECK_COL] == OK and rows["111XYZ01"][CHECK_COL] == CODE_MISSING
    assert rows["VHXXX"][CHECK_COL] == INCOMPLETE
    assert not w.page.tags.table.isColumnHidden(CHECK_COL)
    assert w.project_label() == "P1"
    _ok, faulty = w.page.preview._status_groups
    assert len(faulty) == 2                                                      # 111XYZ01 und VHXXX rot umrandet
    w.page.fault_button.setChecked(True)
    w.page._only_duplicates()
    assert [r[1] for r in w.page.tags.rows()] == ["VHXXX", "111XYZ01"]
    dlg = ProjectDefinitionsDialog(w.project, w)                                 # Verwaltung: Code ergaenzen
    dlg.list.setCurrentRow([dlg.list.item(i).data(0x0100) for i in range(dlg.list.count())]
                           .index("def_function_codes"))
    dlg._add_row()
    dlg.grid.item(dlg.grid.rowCount() - 1, 0).setText("XYZ")
    assert dlg.save_table() and dlg.changed
    dlg.test_type.setCurrentText("Equipment")
    dlg.test_tag.setText("111XYZ01")
    assert dlg.test_result.text().startswith(OK)
    dlg.close()
    w._set_mode(True, quiet=True)
    w.page.fault_button.setChecked(False)
    w.page._only_duplicates()
    assert {r[1]: r[CHECK_COL] for r in w.page.tags.rows()}["111XYZ01"] == OK
    assert _icon_green(w.ribbon.buttons["project_mode"])                         # Symbol gruen, solange an
    w.ribbon.buttons["project_mode"].click()                                     # aus
    wait()
    assert w.checker is None and w.page.tags.table.isColumnHidden(CHECK_COL)
    assert "VHXXX" not in {r[1] for r in w.page.tags.rows()}
    assert not _icon_green(w.ribbon.buttons["project_mode"])
    w.ribbon.buttons["project_mode"].click()                                     # wieder an (Projekt ist gemerkt)
    wait()
    assert w.checker is not None and _icon_green(w.ribbon.buttons["project_mode"])
    w.close()
    w2 = MainWindow(app, "test")
    assert w2.checker is not None and w2.project.name == "P1"                    # Modus und Projekt gemerkt
    w2.close()


def test_save_list_with_new_columns(project):
    """Kachel-Editor: neue Spaltenfolge einer Liste in einer Transaktion; feste Tabellen behalten ihre Spalten."""
    project.save("list:media", [["PFC", "001", "x"]], columns=["Medium Code (Fluid)", "Sr.No", "Hinweis"])
    assert project.read("list:media") == (["Medium Code (Fluid)", "Sr.No", "Hinweis"], [["PFC", "001", "x"]])
    with pytest.raises(ValueError):
        project.save("list:media", [["a", "b"]], columns=["A", "a"])
    with pytest.raises(ValueError):
        project.save("def_function_codes", [["X", "y"]], columns=["description", "code"])
    assert project.read("list:media")[0] == ["Medium Code (Fluid)", "Sr.No", "Hinweis"]


def test_definitions_dialog_menus_tiles_and_undo(project, tmp_path, monkeypatch):
    """Projektdefinitionen wie Tag Compliance: Rechtsklick-Menues (Zelle, Zeilennummer, Spaltenkopf), Undo/Redo,
    Kachel-Editor (Spalten verschieben/ausblenden/einfuegen), Kacheln links umsortieren, Ansicht nach Excel."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path / "home"))
    from p3d_pdfreader.gui import project_dialog
    from p3d_pdfreader.gui.project_dialog import ProjectDefinitionsDialog
    dlg = ProjectDefinitionsDialog(project)
    keys = [dlg.list.item(i).data(Qt.UserRole) for i in range(dlg.list.count())]
    dlg.list.setCurrentRow(keys.index("def_function_codes"))
    assert dlg.grid_data()[1] == [["PMP", "Pump"], ["REA", "Reactor"]]

    # Zeilen: Menue der Zeilennummern, duplizieren, Rueckgaengig/Wiederholen
    dlg._select_rows([0])
    texts = [a.text() for a in dlg.row_header_menu().actions() if a.text()]
    assert "Zeile oberhalb einfügen" in texts and "Zeile duplizieren" in texts and "Rückgängig" in texts
    dlg.duplicate_rows()
    assert dlg.grid.rowCount() == 3 and dlg.dirty
    dlg.undo()
    assert dlg.grid.rowCount() == 2
    dlg.redo()
    assert dlg.grid.rowCount() == 3
    dlg.undo()
    # Zellenmenue und Spaltenmenue einer festen Tabelle (Spalten fest)
    cell = [a.text() for a in dlg.cell_menu(dlg.grid.model().index(0, 0)).actions() if a.text()]
    assert "Zeile hinzufügen" in cell and "Ansicht nach Excel …" in cell and "Nach Code A–Z sortieren" in cell
    col = {a.text(): a.isEnabled() for a in dlg.column_menu(0).actions() if a.text()}
    assert col["Spalte links einfügen"] is False and col["Zeilen absteigend sortieren"] is True
    # feste Tabelle: Spalten nur in der Ansicht verschieben, gespeichert wird in der Tabellenfolge
    dlg.move_columns([1, 0])
    assert dlg.grid_data()[0] == ["description", "code"]
    dlg.grid.item(0, dlg.grid.horizontalHeader().logicalIndex(1)).setText("ABC")
    assert dlg.rows()[0][0] == "ABC" and dlg.save_table()
    assert ["ABC", "Pump"] in project.read("def_function_codes")[1]

    # Liste: Kachel-Editor, Spalte einfuegen, umsortieren, ausblenden, speichern
    dlg.tiles_button.setChecked(True)
    assert dlg.column_tiles.isVisibleTo(dlg) and dlg.column_tiles.tiles.count() == 2
    dlg.list.setCurrentRow([dlg.list.item(i).data(Qt.UserRole) for i in range(dlg.list.count())].index("list:media"))
    dlg.insert_columns(2, 1, ["Hinweis"])
    dlg.move_columns([1, 0, 2])
    dlg.set_column_hidden(2, True)
    assert dlg.column_tiles.tiles.count() == 3
    assert dlg.column_tiles.tiles.item(2).checkState() == Qt.Unchecked
    assert dlg.save_table()
    assert project.read("list:media")[0] == ["Medium Code (Fluid)", "Sr.No", "Hinweis"]
    # Kacheln links: Reihenfolge und Name gemerkt (Projekt-Datenbank)
    dlg._tiles_reordered()
    assert json.loads(project.meta(project_dialog.TILE_ORDER))[0] == keys[0]
    # Ansicht nach Excel: nur sichtbare Spalten und gefilterte Zeilen
    from p3d_pdfreader.gui.table_export import visible_table
    dlg.filter.setText("TFHR")
    assert visible_table(dlg.grid) == (["Medium Code (Fluid)", "Sr.No"], [["TFHR", "002"]])
    dlg.close()
    app.processEvents()


def test_project_settings_roundtrip(tmp_path):
    import json
    from p3d_pdfreader.core import project_settings as ps
    from p3d_pdfreader.core.project_defs import ProjectDB
    cfg = tmp_path / "cfg"
    cfg.mkdir()
    (cfg / "paths.json").write_text(json.dumps({"sources": ["X:/pdf"]}), encoding="utf-8")
    (cfg / "data_link.json").write_text(json.dumps({"rows": [[1]]}), encoding="utf-8")
    (cfg / "state.json").write_text(json.dumps({"data_link_fields": {"tags": "Tag"}, "fremd": 1}), encoding="utf-8")
    db = ProjectDB.create(tmp_path / "p.db", "P")
    assert ps.load_from_project(db) is None
    ps.save_to_project(db, cfg, "1.0.37")
    # anderer Stand im Tool: Importtabelle weg, anderes Feld, eigene Tabellenansicht
    (cfg / "data_link.json").unlink()
    (cfg / "table_views.json").write_text("{}", encoding="utf-8")
    (cfg / "state.json").write_text(json.dumps({"data_link_fields": {}, "fremd": 2}), encoding="utf-8")
    written = ps.apply(cfg, ps.load_from_project(db))
    assert set(written) == {"paths.json", "data_link.json"}
    assert not (cfg / "table_views.json").exists()
    state = json.loads((cfg / "state.json").read_text(encoding="utf-8"))
    assert state == {"fremd": 2, "data_link_fields": {"tags": "Tag"}}
    db.close()


def test_instrument_tag_with_dash(tmp_path):
    """Projektregel: Instrument = Kuerzel-Nummer (TIT-130); der Stand ohne Trennzeichen (1.0.46) wird zurueckgestellt."""
    db = ProjectDB.create(tmp_path / "P.db", "P")
    chk = db.checker()
    assert chk.check("Instrument", "TIT-130").status == OK
    assert chk.check("Instrument", "TIT130").status == FAULT
    db.con.execute(f"update {SEGMENTS} set source='alnum', suffix='' where tag_type='PDF_INSTRUMENT' and pos=1")
    db.con.execute(f"update {STRUCTURES} set example='TIT130', structure='FunctionNumber', note=? "
                   "where tag_type='PDF_INSTRUMENT'",
                   ("Instrument (Blase), z. B. TIT130 (Kuerzel + Nummer ohne Trennzeichen; TIT-130 ist falsch)",))
    db.con.commit()
    db.close()
    db = ProjectDB(tmp_path / "P.db")                 # Oeffnen stellt zurueck
    try:
        assert db.checker().check("Instrument", "TIT-130").status == OK
        assert db.checker().check("Instrument", "TIT130").status == FAULT
        row = db.con.execute(f"select example,structure from {STRUCTURES} where tag_type='PDF_INSTRUMENT'").fetchone()
        assert tuple(row) == ("TIT-130", "Function-Number")
    finally:
        db.close()


def test_tile_click_acts_on_release_not_on_press():
    """Kachel-Editor: Anfassen/Ziehen loest keine Kachel-Funktion aus; ein Klick wirkt erst beim Loslassen ohne Ziehen."""
    from p3d_pdfreader.column_editor import qml_resources  # noqa: F401  (registriert die QML-Ressourcen)
    from PySide6.QtCore import QFile
    f = QFile(":/column_editor/ColumnCard.qml")
    assert f.open(QFile.ReadOnly)
    text = bytes(f.readAll()).decode("utf-8")
    press = text.split("onPressed:")[1].split("onReleased:")[0]
    assert "card.clicked()" not in press
    assert "pendingSingle = true" in press
    assert "!drag.active" in text.split("onReleased:")[1].split("onCanceled")[0]


def test_tag_edit_replace_char(tmp_path):
    """Zeichen ersetzen: XV_130 -> XV-130 wirkt auf Pruefung und Ansicht; ungueltige Regeln werden abgelehnt."""
    from p3d_pdfreader.core import tag_edit
    from p3d_pdfreader.core.export import tag_rows
    from p3d_pdfreader.core.extract import PdfResult, Tag
    db = ProjectDB.create(tmp_path / "P.db", "P")
    chk = db.checker()
    try:
        assert chk.check("Instrument", "XV_130").status == FAULT
        tag_edit.RULE.set("_", "-")
        assert tag_edit.apply("XV_130") == "XV-130" and tag_edit.RULE.active
        assert chk.check("Instrument", "XV_130").status == OK            # Cache beruecksichtigt die Regel
        r = PdfResult(path=tmp_path / "a.pdf", drawing_no="D", tags=[Tag(tag="XV_130", type="Instrument")])
        assert tag_rows([r])[0][3] == "XV-130"
        with pytest.raises(ValueError):
            tag_edit.RULE.set("-", "--")
        tag_edit.RULE.clear()
        assert chk.check("Instrument", "XV_130").status == FAULT and tag_edit.apply("XV_130") == "XV_130"
    finally:
        tag_edit.RULE.clear()
        db.close()


def test_review_model_marks_rule_fault_and_shows_replacement():
    """Tag-Tabelle: Tag-Wert eines Regelverstosses hellgelb; mit Ersetzungsregel zeigt die Zelle den ersetzten Tag."""
    from PySide6.QtCore import Qt
    from p3d_pdfreader.core import tag_edit
    from p3d_pdfreader.gui.main_window import CHECK_COL, TAG_COLS, ReviewModel
    bad, ok = [""] * len(TAG_COLS), [""] * len(TAG_COLS)
    bad[:3], bad[CHECK_COL] = ["Instrument", "XV-130", 1], FAULT
    ok[:3], ok[CHECK_COL] = ["Instrument", "XV130", 1], OK
    m = ReviewModel(TAG_COLS, [bad, ok], 2)
    try:
        assert m.data(m.index(0, 1), Qt.BackgroundRole) is not None
        assert m.data(m.index(1, 1), Qt.BackgroundRole) is None
        assert m.data(m.index(0, 0), Qt.BackgroundRole) is None
        tag_edit.RULE.set("-", "")
        assert m.data(m.index(0, 1), Qt.DisplayRole) == "XV130" and m.rows[0][1] == "XV-130"
    finally:
        tag_edit.RULE.clear()


def test_fast_sort_proxy_matches_kit_order():
    """Performance: FastSortProxy sortiert wie der Kit-Proxy (auf-/absteigend, Zahlen vor Text), ueberspringt eine schon
    aufsteigende Quelle und sortiert das naechste, unsortierte Modell wieder nach dem gemerkten Wunsch."""
    import random
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    from main_gui_kit.tables import MultiColumnFilterProxy, TableDataModel
    from p3d_pdfreader.gui.fast_proxy import FastSortProxy
    QApplication.instance() or QApplication([])
    rnd = random.Random(3)
    rows = [[rnd.choice(["b", "A", "10", "9", "", "c-1"]), str(i)] for i in range(300)]

    def order(proxy_cls, data, col, direction, presorted_first=False):
        proxy = proxy_cls()
        if presorted_first:
            proxy.sort(col, direction)
            proxy.setSourceModel(TableDataModel(["a", "b"], sorted(data, key=lambda r: TableDataModel._sort_key(r[0]))))
        else:
            proxy.sort(col, direction)
        proxy.setSourceModel(TableDataModel(["a", "b"], [list(r) for r in data]))
        return [proxy.index(i, 1).data() for i in range(proxy.rowCount())], proxy

    for col, direction in ((0, Qt.AscendingOrder), (0, Qt.DescendingOrder), (1, Qt.AscendingOrder)):
        kit, _ = order(MultiColumnFilterProxy, rows, col, direction)
        fast, _ = order(FastSortProxy, rows, col, direction)
        assert fast == kit
    already = sorted(rows, key=lambda r: TableDataModel._sort_key(r[0]))
    kit, _ = order(MultiColumnFilterProxy, already, 0, Qt.AscendingOrder)
    fast, proxy = order(FastSortProxy, already, 0, Qt.AscendingOrder)
    assert fast == kit
    kit, _ = order(MultiColumnFilterProxy, rows, 0, Qt.AscendingOrder)
    fast, _ = order(FastSortProxy, rows, 0, Qt.AscendingOrder, presorted_first=True)
    assert fast == kit                                   # nach uebersprungener Sortierung wieder sortiert
