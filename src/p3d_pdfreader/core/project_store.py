"""Daten je Projekt in der Projekt-Datenbank (Nutzervorgabe 2026-11-26): Review-Eintraege (mit Verlauf) und die aus den
PDFs gelesenen Daten. Die Einstellungen samt Importtabelle speichert ``project_settings`` in derselben Datei.

* ``review_versions``: je Speichern ein neuer Stand (nichts wird ueberschrieben); geladen wird der neueste je PDF.
* ``pdf_scans``: Ergebnis von ``read_pdf`` je PDF und Leseoption. Es wird nur wiederverwendet, wenn Dateigroesse,
  Aenderungszeit, Tool-Version und Tag-Muster unveraendert sind. Die PDF-Datei selbst wird nicht gespeichert.

"Aktives Projekt" setzt die Oberflaeche mit ``activate``; ohne diesen Aufruf (Web-Server) gilt ``project_db`` aus
``config/state.json``. Jede Funktion oeffnet eine eigene kurze Verbindung (Scan-Thread, Web-Server). Ohne Qt."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from ..paths import config_dir, home_dir
from .extract import PdfResult, Tag

SCHEMA = (
    "create table if not exists review_versions(id integer primary key autoincrement, path_key text not null, "
    "pdf text not null, saved text not null, user text not null default '', payload text not null)",
    "create index if not exists review_versions_key on review_versions(path_key, id)",
    "create table if not exists pdf_scans(path_key text not null, variant text not null, pdf text not null, "
    "stamp text not null, scanned text not null, data text not null, primary key(path_key, variant))",
)

_active: tuple[str, Path | None] | None = None      # (Datenordner, Projekt) - gilt nur fuer diesen Datenordner
_reviews: dict[Path, tuple] = {}                    # Datenbank -> (Dateistand, {path_key: neuester Stand als JSON})


def activate(db_path: str | Path | None) -> None:
    """Aktives Projekt dieses Prozesses setzen (``None`` = keines)."""
    global _active
    _active = (str(home_dir()), Path(db_path).resolve() if db_path else None)


def active() -> Path | None:
    """Projekt-Datenbank, in die Reviews gehoeren; ``None`` = ohne Projekt (Ablage als JSON wie bisher)."""
    if _active is not None and _active[0] == str(home_dir()):
        path = _active[1]
    else:
        try:
            state = json.loads((config_dir() / "state.json").read_text(encoding="utf-8"))
            path = Path(state["project_db"]).resolve() if state.get("project_db") else None
        except (OSError, ValueError, KeyError, AttributeError, TypeError):
            path = None
    return path if path is not None and path.is_file() else None


def path_key(pdf: str | Path) -> str:
    return str(Path(pdf).resolve()).casefold()


@contextmanager
def _connect(db: Path):
    """Verbindung mit Tabellen; Fehler kommen als ``OSError`` (wie beim Schreiben einer Datei)."""
    try:
        con = sqlite3.connect(str(db), timeout=10)
        try:
            with con:
                for statement in SCHEMA:
                    con.execute(statement)
                yield con
        finally:
            con.close()
    except sqlite3.Error as exc:
        raise OSError(f"Projekt-Datenbank {Path(db).name}: {exc}") from exc


# --- Reviews ------------------------------------------------------------------------------------------------------
def _stamp(db: Path) -> tuple:
    st = db.stat()
    return st.st_mtime_ns, st.st_size


def load_review(db: Path, key: str) -> dict | None:
    """Neuester Stand der PDF; ``None`` = die Datenbank hat noch keinen. Alle neuesten Staende werden zusammen gelesen
    und gemerkt, bis sich die Datei aendert (Dateiliste und Export fragen je PDF)."""
    stamp = _stamp(db)
    hit = _reviews.get(db)
    if hit is None or hit[0] != stamp:
        with _connect(db) as con:
            rows = dict(con.execute("select path_key, payload from review_versions where id in "
                                    "(select max(id) from review_versions group by path_key)"))
        hit = _reviews[db] = (_stamp(db), rows)
    text = hit[1].get(key)
    return json.loads(text) if text is not None else None


def save_review(db: Path, key: str, payload: dict) -> None:
    with _connect(db) as con:
        con.execute("insert into review_versions(path_key, pdf, saved, user, payload) values(?,?,?,?,?)",
                    (key, str(payload.get("pdf", "")), str(payload.get("saved", "")), str(payload.get("user", "")),
                     json.dumps(payload, ensure_ascii=False)))
    _reviews.pop(db, None)


# --- Gelesene PDF-Daten -------------------------------------------------------------------------------------------
def to_data(result: PdfResult) -> dict:
    data = asdict(result)
    data["path"] = str(result.path)
    for name in ("created", "modified"):
        data[name] = data[name].isoformat() if data[name] else None
    return data


def from_data(data: dict, path: Path) -> PdfResult:
    data = dict(data, path=Path(path))
    for name in ("created", "modified"):
        data[name] = datetime.fromisoformat(data[name]) if data[name] else None
    tags = []
    for t in data["tags"]:
        tags.append(Tag(**dict(t, rect=tuple(t["rect"]), hits=[(p, tuple(r)) for p, r in t["hits"]])))
    data["tags"] = tags
    return PdfResult(**data)


class ScanCache:
    """Gelesene PDF-Daten eines Projekts. Ein Fehler der Datenbank bricht den Scan nie ab (dann wird neu gelesen)."""

    def __init__(self, db: Path, version: str, patterns_text: str, pipes: bool, placeholders: bool):
        self.db = db
        self.variant = f"pipes={int(pipes)} placeholders={int(placeholders)}"
        self.rules = f"{version}|{hashlib.sha1(patterns_text.encode('utf-8')).hexdigest()[:12]}"

    def _file_stamp(self, path: Path) -> str:
        st = Path(path).stat()
        return f"{self.rules}|{st.st_size}|{st.st_mtime_ns}"

    def get(self, path: Path) -> PdfResult | None:
        try:
            stamp = self._file_stamp(path)
            with _connect(self.db) as con:
                row = con.execute("select data from pdf_scans where path_key=? and variant=? and stamp=?",
                                  (path_key(path), self.variant, stamp)).fetchone()
            return from_data(json.loads(row[0]), path) if row else None
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def put(self, result: PdfResult) -> None:
        if result.error:                                    # defekt oder gesperrt: beim naechsten Mal neu versuchen
            return
        try:
            stamp = self._file_stamp(result.path)
            with _connect(self.db) as con:
                con.execute("insert or replace into pdf_scans(path_key, variant, pdf, stamp, scanned, data) "
                            "values(?,?,?,?,?,?)",
                            (path_key(result.path), self.variant, str(result.path), stamp,
                             datetime.now().isoformat(timespec="seconds"),
                             json.dumps(to_data(result), ensure_ascii=False, separators=(",", ":"))))
        except (OSError, ValueError, TypeError):
            pass
