"""Projektdaten in der Projekt-Datenbank (1.0.53): Reviews mit Verlauf und JSON-Uebernahme, gelesene PDF-Daten,
automatisches Speichern der Einstellungen beim Arbeiten und beim Projektwechsel."""
from __future__ import annotations

import os
import sqlite3
import time

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

from p3d_pdfreader.core import project_settings, project_store  # noqa: E402
from p3d_pdfreader.core.project_defs import ProjectDB  # noqa: E402
from p3d_pdfreader.core.review_store import ReviewStore  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    return tmp_path


def _project(home, name):
    path = home / "projects" / f"{name}.db"
    ProjectDB.create(path, name).close()
    return path


def _pdf(path, text="111PMP01"):
    import pymupdf
    with pymupdf.open() as doc:
        doc.new_page(width=600, height=400).insert_text((100, 100), text, fontsize=10)
        doc.save(path)
    return path


def _rows(db, table):
    con = sqlite3.connect(db)
    try:
        return con.execute(f"select count(*) from {table}").fetchone()[0]
    finally:
        con.close()


def test_reviews_per_project_with_history_and_json_import(home):
    pdf = home / "a.pdf"
    project_store.activate(None)                              # ohne Projekt: JSON wie bisher
    old = ReviewStore(pdf)
    old.set("Instrument", "XV-1", "Bemerkung", "alt")
    assert old.save().suffix == ".json"
    a, b = _project(home, "A"), _project(home, "B")
    project_store.activate(a)
    store = ReviewStore(pdf)
    assert store.entries["Instrument|XV-1"]["Bemerkung"] == "alt"             # JSON-Stand uebernommen
    store.set("Instrument", "XV-1", "Bemerkung", "neu in A")
    store.set_removed([("Instrument", "XV-2")])
    assert store.save() == a.resolve()
    assert _rows(a, "review_versions") == 2 and len(old.versions()) == 1      # Verlauf; JSON bleibt wie er war
    again = ReviewStore(pdf)
    assert again.entries["Instrument|XV-1"]["Bemerkung"] == "neu in A" and again.is_removed("Instrument", "XV-2")
    project_store.activate(b)                                                  # anderes Projekt: eigener Stand
    assert ReviewStore(pdf).entries["Instrument|XV-1"]["Bemerkung"] == "alt"
    again.set("Instrument", "XV-1", "Review", "OK")                            # geladen aus A -> bleibt in A
    assert again.save() == a.resolve()
    assert ReviewStore(pdf).values("Instrument", "XV-1")[0] == ""


def test_scan_cache_reuses_only_unchanged_files(home):
    from p3d_pdfreader.core.extract import read_pdf
    db = _project(home, "A")
    pdf = _pdf(home / "eq.pdf")
    cache = project_store.ScanCache(db, "1", "muster", False, False)
    assert cache.get(pdf) is None
    result = read_pdf(pdf)
    cache.put(result)
    cached = cache.get(pdf)
    assert cached == result and cached is not result
    assert project_store.ScanCache(db, "2", "muster", False, False).get(pdf) is None        # neue Tool-Version
    assert project_store.ScanCache(db, "1", "anders", False, False).get(pdf) is None        # andere Tag-Muster
    assert project_store.ScanCache(db, "1", "muster", True, False).get(pdf) is None         # andere Leseoption
    st = pdf.stat()
    os.utime(pdf, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))                      # Datei geaendert
    assert cache.get(pdf) is None
    broken = home / "kaputt.pdf"
    broken.write_bytes(b"keine pdf")
    cache.put(read_pdf(broken))
    assert cache.get(broken) is None                                                        # Fehler nie merken


def test_autosave_writes_only_changes_and_keeps_backup(home):
    from p3d_pdfreader import paths
    from p3d_pdfreader.gui import last_paths
    with ProjectDB(_project(home, "A")) as db:
        last_paths.set_value("tag_edit", {"find": "_", "to": "-"})
        assert project_settings.autosave(db, paths.config_dir(), "1")
        assert not project_settings.autosave(db, paths.config_dir(), "1")
        last_paths.set_value("tag_edit", {"find": "", "to": ""})
        assert project_settings.autosave(db, paths.config_dir(), "1")
        assert project_settings.load_from_project(db)["state"]["tag_edit"] == {"find": "", "to": ""}
        saved = db.con.execute("select bundle from settings_backups").fetchall()
        assert len(saved) == 1 and '"_"' in saved[0][0]


def test_window_saves_and_restores_per_project_and_reuses_scan(app, home):
    from p3d_pdfreader import paths
    from p3d_pdfreader.gui import last_paths
    from p3d_pdfreader.gui.main_window import MainWindow
    a, b = _project(home, "A"), _project(home, "B")
    pdf = _pdf(home / "eq.pdf")
    w = MainWindow(app, "test")

    def wait():
        start = time.time()
        while w._thread is not None and time.time() - start < 30:
            app.processEvents()

    assert w.activate_project(a)
    w.scan([pdf])
    wait()
    assert _rows(a, "pdf_scans") == 1 and "aus dem Projekt" not in w.statusBar().currentMessage()
    w.scan([pdf])
    wait()
    assert "1 unverändert aus dem Projekt übernommen" in w.statusBar().currentMessage()
    last_paths.set_value("redline_review_layer", False)
    assert w.activate_project(b)                       # A wird beim Wechsel gespeichert, B uebernimmt den Stand
    wait()
    assert w.page.store is None or w.page.store.db == b.resolve()
    last_paths.set_value("redline_review_layer", True)
    assert w.activate_project(a)                       # zurueck: Einstellungen von A ohne Rueckfrage
    wait()
    assert last_paths.get_value("redline_review_layer") is False
    last_paths.set_value("redline_review_layer", True)
    w.close()                                          # beim Beenden gespeichert
    with ProjectDB(a) as db:
        assert project_settings.load_from_project(db)["state"]["redline_review_layer"] is True
    assert paths.config_dir().is_dir()
