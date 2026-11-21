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
                                             SEGMENTS, ProjectDB)


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
    w.ribbon.buttons["project_mode"].click()                                     # aus
    wait()
    assert w.checker is None and w.page.tags.table.isColumnHidden(CHECK_COL)
    assert "VHXXX" not in {r[1] for r in w.page.tags.rows()}
    w.ribbon.buttons["project_mode"].click()                                     # wieder an (Projekt ist gemerkt)
    wait()
    assert w.checker is not None
    w.close()
    w2 = MainWindow(app, "test")
    assert w2.checker is not None and w2.project.name == "P1"                    # Modus und Projekt gemerkt
    w2.close()
