"""Projektdefinitionen (Projektmodus): Codelisten, Tag-Strukturen und Pruefregeln eines Projekts. Ohne Qt.

Eine Projekt-Datenbank ist eine SQLite-Datei im **Schema von P3D Tag Compliance** (``pidtag_project.db``): dieselben
Tabellen ``def_*`` (Codelisten, Nummernkreise, Tag-Strukturen, Tag-Segmente, Notizen), ``def_lists``/``def_list_rows``
(freie Listen, z. B. Media list) und ``settings`` (Trennzeichen-Regel). Die Definitionen lassen sich deshalb 1:1 aus
Tag Compliance uebernehmen (``import_tag_compliance``, die Quelle wird nur gelesen) und als Excel im selben Blattformat
aus- und einlesen.

Dazu kommen zwei Tabellen nur dieses Tools:

* ``pdf_tag_rules`` - welcher Tag-Typ des PDF Readers (Instrument, Equipment, Armatur, Volltag, Rohrleitung) gegen
  welche Tag-Struktur (``def_tag_segments``, Segment Tag Designer von Tag Compliance) geprueft wird.
* ``pdf_meta`` - Projektname, Quelle der Uebernahme, Zeitpunkte.

Pruefung (``Checker``): Eine Tag-Struktur ist eine Folge von Segmenten (Quelle = Codeliste, Konstante, laufende Nummer
oder freier Text, mit Trennzeichen davor/danach). Daraus entsteht ein regulaerer Ausdruck wie in Tag Compliance
(``pidtag_segments.tag_regex``). Passt ein Tag zu keiner Struktur seines Typs, nennt der Hinweis das erste Segment,
das nicht passt, oder die Trennzeichen-Regel (z. B. ``-`` statt ``_``)."""
from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_SUFFIX = ".db"
LIST_PREFIX = "list:"
RULES = "pdf_tag_rules"
SETTINGS = "settings"
SEGMENTS = "def_tag_segments"
STRUCTURES = "def_tag_structures"

OK, FAULT = "OK", "Regelfehler Projektdefinition"   # Status der Spalte "Projekt-Pruefung"
CHECK_HEADERS = ["Projekt-Prüfung", "Projekt-Hinweis"]

SCHEMA = """
create table if not exists settings(key text primary key, value text not null);
create table if not exists def_meta(key text primary key, value text);
create table if not exists def_general_codes(code text, description text);
create table if not exists def_building_codes(code text primary key, description text);
create table if not exists def_system_codes(code text primary key, description text);
create table if not exists def_fitting_types(code text primary key, description text);
create table if not exists def_function_codes(code text, description text);
create table if not exists def_pipeclass(code text primary key, description text);
create table if not exists def_number_ranges(scope text, range text, description text);
create table if not exists def_tag_structures(tag_type text primary key, example text, structure text, note text,
    color text not null default '');
create table if not exists def_tag_segments(tag_type text not null, pos integer not null, name text not null,
    source text not null default 'free', sample text not null default '', prefix text not null default '',
    suffix text not null default '', required text not null default 'yes', visible text not null default 'yes',
    color text not null default '', description text not null default '', primary key(tag_type, pos));
create table if not exists def_notes(topic text, note text);
create table if not exists def_lists(name text primary key, title text not null, columns text not null,
    builtin integer not null default 0, source text default '', pos integer not null default 0,
    rev integer not null default 1);
create table if not exists def_list_rows(list_name text not null, pos integer not null, data text not null);
create index if not exists ix_def_list_rows on def_list_rows(list_name, pos);
create table if not exists pdf_tag_rules(pdf_type text not null, tag_type text not null, enabled text not null
    default 'ja', note text not null default '', primary key(pdf_type, tag_type));
create table if not exists pdf_meta(key text primary key, value text);
"""

#: Feste Tabellen: (Schluessel, Titel, Spalten). Schluessel und Spalten wie in Tag Compliance (``DEF_TABLES``).
DEF_TABLES = [
    ("def_meta", "Quelle und Projekt", ("key", "value")),
    ("def_general_codes", "General codes", ("code", "description")),
    ("def_building_codes", "Building codes", ("code", "description")),
    ("def_system_codes", "System codes", ("code", "description")),
    ("def_fitting_types", "Fitting type codes (valves)", ("code", "description")),
    ("def_function_codes", "Function codes (equipment)", ("code", "description")),
    ("def_pipeclass", "Pipeclass codes", ("code", "description")),
    ("def_number_ranges", "Sequential number ranges", ("scope", "range", "description")),
    (STRUCTURES, "Tag structures", ("tag_type", "example", "structure", "note", "color")),
    (SEGMENTS, "Tag segments", ("tag_type", "pos", "name", "source", "sample", "prefix", "suffix", "required",
                                "visible", "color", "description")),
    ("def_notes", "Notes", ("topic", "note")),
]
#: Tabellen nur dieses Tools (im Verwaltungsdialog unter den Definitionen)
TOOL_TABLES = [
    (RULES, "PDF-Prüfregeln", ("pdf_type", "tag_type", "enabled", "note")),
    (SETTINGS, "Einstellungen (Trennzeichen)", ("key", "value")),
]
DEFAULT_SETTINGS = {"from_char": "-", "to_char": "_"}
SETTING_NOTES = {"from_char": "falsches Trennzeichen", "to_char": "richtiges Trennzeichen"}
LIST_NAME = re.compile(r"^[a-z][a-z0-9_]{0,29}$")
RESERVED = {t.replace("def_", "") for t, _, _ in DEF_TABLES} | {t for t, _, _ in TOOL_TABLES}
TRUE = {"1", "yes", "ja", "true", "x", "y", "j", "wahr", "on"}

FREE, CONST, SEQ = "free", "const", "seq"

#: Mitgelieferte Tag-Strukturen fuer die Tag-Typen des PDF Readers (Schreibweise auf dem Plot). Nur angelegt, wenn
#: die Struktur im Projekt fehlt; danach frei aenderbar. Segment: (Name, Quelle, Beispiel, davor, danach, Pflicht).
DEFAULT_DESIGNS = {
    "PDF_EQUIPMENT": ("Equipment auf dem Plot, z. B. 111PMP01 (Unit + Function code + laufende Nummer)", [
        ("Unit", "seq:3", "111", "", "", True),
        ("Function code", "def_function_codes", "PMP", "", "", True),
        ("Running number", "seq:2", "01", "", "", True)]),
    "PDF_VALVE": ("Armatur auf dem Plot, z. B. VH340 (Fitting type + laufende Nummer)", [
        ("Fitting type", "def_fitting_types", "VH", "", "", True),
        ("Running number", "seq:3", "340", "", "", True)]),
    "PDF_PIPE_LINE": ("Rohrleitung auf dem Plot, z. B. 203_17_112PFC_ST10_013_1\" oder TFHR_SS01_001_1\"", [
        ("Building", "def_building_codes", "203", "", "_", False),
        ("System", "def_system_codes", "17", "", "_", False),
        ("Unit", "seq:3", "112", "", "", False),
        ("Fluid code", "list:media|Medium Code (Fluid)", "PFC", "", "_", True),
        ("Pipeclass", "def_pipeclass", "ST10", "", "_", True),
        ("Line number", "seq:3", "013", "", "_", True),
        ("Size", "free", "1\"", "", "", True)]),
    "PDF_HOSE": ("Schlauch auf dem Plot, z. B. 151_HOS_206_1\"", [
        ("Unit", "seq:3", "151", "", "_", True),
        ("Hose code", "const:HOS", "HOS", "", "_", True),
        ("Line number", "seq:3", "206", "", "_", True),
        ("Size", "free", "1\"", "", "", True)]),
    "PDF_FULL_TAG": ("Volltag, z. B. 203_17_111_TZIT-011 (Building_System_Unit_Tag)", [
        ("Building", "def_building_codes", "203", "", "_", True),
        ("System", "def_system_codes", "17", "", "_", True),
        ("Unit", "seq:3", "111", "", "_", True),
        ("Tag", "free", "TZIT-011", "", "", True)]),
    "PDF_INSTRUMENT": ("Instrument (Blase), z. B. TIT-130 (Kuerzel + Nummer, vom PDF Reader mit - verbunden)", [
        ("Function", "free", "TIT", "", "-", True),
        ("Number", "seq:3", "130", "", "", True)]),
}
DEFAULT_RULES = [("Equipment", "PDF_EQUIPMENT"), ("Armatur", "PDF_VALVE"), ("Rohrleitung", "PDF_PIPE_LINE"),
                 ("Rohrleitung", "PDF_HOSE"), ("Volltag", "PDF_FULL_TAG"), ("Instrument", "PDF_INSTRUMENT")]


def truthy(value) -> bool:
    return str(value or "").strip().lower() in TRUE


def _clean(v) -> str:
    return "" if v is None else str(v).strip()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_list(table: str) -> bool:
    return str(table).startswith(LIST_PREFIX)


def list_name(table: str) -> str:
    return str(table)[len(LIST_PREFIX):]


def sheet_name(table: str) -> str:
    """Excel-Blattname wie in Tag Compliance (``def_`` entfaellt, Listen mit ihrem Namen)."""
    return (list_name(table) if is_list(table) else table.replace("def_", ""))[:31]


def code_col(cols) -> int:
    return next((i for i, c in enumerate(cols) if str(c).strip().lower() == "code"), -1)


def _natural(v) -> list:
    return [(0, int(t), "") if t.isdigit() else (1, 0, t.lower()) for t in re.split(r"(\d+)", str(v)) if t != ""]


def sort_code_rows(cols, rows: list) -> None:
    """Zeilen nach der Spalte ``code`` sortieren (A-Z, Zahlen numerisch, leere zuletzt) - wie in Tag Compliance."""
    ci = code_col(cols)
    if ci >= 0:
        rows.sort(key=lambda r: (not _clean(r[ci]), _natural(_clean(r[ci]))))


def _ro_connect(path: Path) -> sqlite3.Connection:
    """Fremde Datenbank nur lesend oeffnen (Tag Compliance wird nie veraendert)."""
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


# ------------------------------------------------------------------------------------------------------------------
# Projekt-Datenbank
# ------------------------------------------------------------------------------------------------------------------
class ProjectDB:
    """Eine Projekt-Datenbank. ``create`` legt eine neue an, ``ProjectDB(path)`` oeffnet eine vorhandene."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"Projekt-Datenbank nicht gefunden: {self.path}")
        self.con = sqlite3.connect(str(self.path))
        self.con.executescript(SCHEMA)
        self._migrate()

    @classmethod
    def create(cls, path: str | Path, name: str) -> "ProjectDB":
        path = Path(path)
        if path.exists():
            raise FileExistsError(f"Datei existiert bereits: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        sqlite3.connect(str(path)).close()
        db = cls(path)
        db.set_meta("name", name.strip() or path.stem)
        db.set_meta("created", _now())
        db.ensure_defaults()
        return db

    def close(self) -> None:
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def _migrate(self) -> None:
        if "rev" not in [r[1] for r in self.con.execute("pragma table_info(def_lists)")]:
            self.con.execute("alter table def_lists add column rev integer not null default 1")
        for k, v in DEFAULT_SETTINGS.items():
            self.con.execute("insert or ignore into settings(key,value) values(?,?)", (k, v))
        self.con.commit()

    # --- Meta ---------------------------------------------------------------------------------------------------
    def meta(self, key: str, default: str = "") -> str:
        r = self.con.execute("select value from pdf_meta where key=?", (key,)).fetchone()
        return r[0] if r and r[0] is not None else default

    def set_meta(self, key: str, value: str) -> None:
        self.con.execute("insert or replace into pdf_meta(key,value) values(?,?)", (key, str(value)))
        self.con.commit()

    @property
    def name(self) -> str:
        return self.meta("name", self.path.stem)

    def setting(self, key: str) -> str:
        r = self.con.execute("select value from settings where key=?", (key,)).fetchone()
        return r[0] if r else DEFAULT_SETTINGS.get(key, "")

    # --- Tabellen ----------------------------------------------------------------------------------------------
    def lists(self) -> list[tuple[str, str, tuple]]:
        return [(LIST_PREFIX + r[0], r[1], tuple(json.loads(r[2])))
                for r in self.con.execute("select name,title,columns from def_lists order by pos, name")]

    def tables(self) -> list[tuple[str, str, tuple]]:
        """Alle Tabellen in Anzeigereihenfolge: Definitionen, Listen, Tabellen dieses Tools."""
        return list(DEF_TABLES) + self.lists() + list(TOOL_TABLES)

    def info(self, table: str) -> tuple[str, tuple]:
        for t, title, cols in self.tables():
            if t == table:
                return title, cols
        raise KeyError(f"Unbekannte Tabelle: {table}")

    def count(self, table: str) -> int:
        if is_list(table):
            return self.con.execute("select count(*) from def_list_rows where list_name=?",
                                    (list_name(table),)).fetchone()[0]
        self.info(table)
        return self.con.execute(f"select count(*) from {table}").fetchone()[0]

    def read(self, table: str) -> tuple[list[str], list[list[str]]]:
        _title, cols = self.info(table)
        cols = list(cols)
        if is_list(table):
            rows = []
            for (data,) in self.con.execute("select data from def_list_rows where list_name=? order by pos",
                                            (list_name(table),)):
                v = [_clean(x) for x in json.loads(data)]
                rows.append((v + [""] * len(cols))[:len(cols)])
        else:
            order = " order by tag_type, pos" if table == SEGMENTS else ""
            rows = [[_clean(x) for x in r] for r in self.con.execute(f"select {','.join(cols)} from {table}{order}")]
        sort_code_rows(cols, rows)
        return cols, rows

    def save(self, table: str, rows: list) -> int:
        """Inhalt einer Tabelle ersetzen (eine Transaktion). Leere Zeilen entfallen; doppelte Schluessel -> ValueError."""
        _title, cols = self.info(table)
        clean = []
        for r in rows:
            r = [_clean(x) for x in list(r)[:len(cols)]]
            r += [""] * (len(cols) - len(r))
            if any(r):
                clean.append(r)
        sort_code_rows(cols, clean)
        try:
            self.con.execute("begin")
            if is_list(table):
                n = list_name(table)
                self.con.execute("delete from def_list_rows where list_name=?", (n,))
                self.con.executemany("insert into def_list_rows(list_name,pos,data) values(?,?,?)",
                                     [(n, i, json.dumps(r, ensure_ascii=False)) for i, r in enumerate(clean)])
            else:
                if table == SEGMENTS:
                    for r in clean:
                        if not r[1].isdigit():
                            raise ValueError(f"Tag segments: Spalte pos muss eine Zahl sein ({r[0]!r}, {r[1]!r})")
                self.con.execute(f"delete from {table}")
                self.con.executemany(f"insert into {table}({','.join(cols)}) values({','.join('?' * len(cols))})",
                                     clean)
            self.con.commit()
        except sqlite3.Error as exc:
            self.con.rollback()
            raise ValueError(f"{table}: {exc} (Schlüssel doppelt?)") from exc
        except ValueError:
            self.con.rollback()
            raise
        if table == SETTINGS:
            self._migrate()
        return len(clean)

    def create_list(self, name: str, title: str, columns) -> str:
        name = _clean(name).lower()
        if not LIST_NAME.match(name):
            raise ValueError("Listenname: Kleinbuchstaben, Ziffern und _ , mit einem Buchstaben beginnend (max. 30).")
        if name in RESERVED:
            raise ValueError(f"„{name}“ ist der Name einer festen Tabelle – bitte anderen Namen wählen.")
        cols = [c for c in (_clean(c) for c in columns) if c]
        if not cols:
            raise ValueError("Eine Liste braucht mindestens eine Spalte.")
        if len({c.lower() for c in cols}) != len(cols):
            raise ValueError("Spaltennamen doppelt.")
        if self.con.execute("select 1 from def_lists where name=?", (name,)).fetchone():
            raise ValueError(f"Eine Liste „{name}“ gibt es schon.")
        pos = (self.con.execute("select coalesce(max(pos),0) from def_lists").fetchone()[0] or 0) + 1
        self.con.execute("insert into def_lists(name,title,columns,builtin,source,pos) values(?,?,?,?,?,?)",
                         (name, _clean(title) or name, json.dumps(cols, ensure_ascii=False), 0, "", pos))
        self.con.commit()
        return LIST_PREFIX + name

    def delete_list(self, table: str) -> None:
        if not is_list(table):
            raise ValueError("Nur Listen lassen sich löschen, feste Tabellen nicht.")
        n = list_name(table)
        self.con.execute("delete from def_list_rows where list_name=?", (n,))
        self.con.execute("delete from def_lists where name=?", (n,))
        self.con.commit()

    def set_list_columns(self, table: str, columns, title: str | None = None) -> list[str]:
        """Spalten umbenennen/ergaenzen; die Zellen behalten ihre Position (neue Spalten leer)."""
        cols = [c for c in (_clean(c) for c in columns) if c]
        if not cols:
            raise ValueError("Eine Liste braucht mindestens eine Spalte.")
        n = list_name(table)
        self.con.execute("update def_lists set columns=? where name=?", (json.dumps(cols, ensure_ascii=False), n))
        if title is not None and _clean(title):
            self.con.execute("update def_lists set title=? where name=?", (_clean(title), n))
        self.con.commit()
        return cols

    # --- Standardregeln ----------------------------------------------------------------------------------------
    def ensure_defaults(self, force: bool = False) -> int:
        """Mitgelieferte Tag-Strukturen (``DEFAULT_DESIGNS``) anlegen, wenn sie fehlen, und die Pruefregeln setzen,
        wenn noch keine da sind (``force``: Regeln und mitgelieferte Strukturen auf den Standard zuruecksetzen)."""
        n = 0
        have = {r[0] for r in self.con.execute(f"select distinct tag_type from {SEGMENTS}")}
        for tag_type, (note, segs) in DEFAULT_DESIGNS.items():
            if tag_type in have and not force:
                continue
            self.con.execute(f"delete from {SEGMENTS} where tag_type=?", (tag_type,))
            self.con.executemany(
                f"insert into {SEGMENTS}(tag_type,pos,name,source,sample,prefix,suffix,required,visible,color,"
                "description) values(?,?,?,?,?,?,?,?,?,?,?)",
                [(tag_type, i + 1, name, src, sample, pre, suf, "yes" if req else "no", "yes", "", "")
                 for i, (name, src, sample, pre, suf, req) in enumerate(segs)])
            example = "".join(f"{pre}{sample}{suf}" for _n, _s, sample, pre, suf, _r in segs)
            structure = "".join(f"{pre}{name if req else '[' + name + ']'}{suf}" for name, _s, _x, pre, suf, req in segs)
            self.con.execute(f"insert or replace into {STRUCTURES}(tag_type,example,structure,note,color) "
                             "values(?,?,?,?,'')", (tag_type, example, structure, note))
            n += 1
        if force:
            self.con.execute(f"delete from {RULES}")
        if force or not self.con.execute(f"select count(*) from {RULES}").fetchone()[0]:
            self.con.executemany(f"insert or ignore into {RULES}(pdf_type,tag_type,enabled,note) values(?,?,'ja','')",
                                 DEFAULT_RULES)
        self.con.commit()
        return n

    # --- Uebernahme aus P3D Tag Compliance --------------------------------------------------------------------
    def import_tag_compliance(self, source: str | Path) -> dict[str, int]:
        """Definitionen aus einer Tag-Compliance-Datenbank (``pidtag_project.db``) uebernehmen. Die Quelle wird nur
        gelesen. Ersetzt werden alle ``def_*``-Tabellen, die Listen und die Trennzeichen-Regel; die Pruefregeln dieses
        Tools bleiben, ebenso eigene Tag-Strukturen, die in der Quelle nicht vorkommen. Rueckgabe: Zeilen je Tabelle."""
        source = Path(source).resolve()
        if source == self.path:
            raise ValueError("Quelle und Projekt sind dieselbe Datei.")
        src = _ro_connect(source)
        try:
            src_tables = {r[0] for r in src.execute("select name from sqlite_master where type='table'")}
            if not any(t.startswith("def_") for t in src_tables):
                raise ValueError(f"Keine Projektdefinitionen (Tabellen def_*) in {source.name}.")
            keep = self._own_designs()
            counts: dict[str, int] = {}
            self.con.execute("begin")
            for table, _title, cols in DEF_TABLES:
                if table not in src_tables:
                    continue
                have = [r[1] for r in src.execute(f"pragma table_info({table})")]
                use = [c for c in cols if c in have]
                rows = src.execute(f"select {','.join(use)} from {table}").fetchall()
                self.con.execute(f"delete from {table}")
                self.con.executemany(f"insert or replace into {table}({','.join(use)}) "
                                     f"values({','.join('?' * len(use))})", rows)
                counts[table] = len(rows)
            if "def_lists" in src_tables:
                have = [r[1] for r in src.execute("pragma table_info(def_lists)")]
                rev = "rev" if "rev" in have else "1"
                lists = src.execute(f"select name,title,columns,builtin,coalesce(source,''),pos,{rev} "
                                    "from def_lists").fetchall()
                self.con.execute("delete from def_lists")
                self.con.execute("delete from def_list_rows")
                self.con.executemany("insert into def_lists(name,title,columns,builtin,source,pos,rev) "
                                     "values(?,?,?,?,?,?,?)", lists)
                if "def_list_rows" in src_tables:
                    rows = src.execute("select list_name,pos,data from def_list_rows").fetchall()
                    self.con.executemany("insert into def_list_rows(list_name,pos,data) values(?,?,?)", rows)
                    for name, *_rest in lists:
                        counts[LIST_PREFIX + name] = sum(1 for r in rows if r[0] == name)
            if SETTINGS in src_tables:
                for k in DEFAULT_SETTINGS:
                    r = src.execute("select value from settings where key=?", (k,)).fetchone()
                    if r is not None:
                        self.con.execute("insert or replace into settings(key,value) values(?,?)", (k, r[0]))
            src_types = {r[0] for r in self.con.execute(f"select distinct tag_type from {SEGMENTS}")}
            for tag_type, (structure, segments) in keep.items():
                if tag_type in src_types:
                    continue
                self.con.executemany(f"insert into {SEGMENTS} values({','.join('?' * 11)})", segments)
                if structure:
                    self.con.execute(f"insert or replace into {STRUCTURES} values(?,?,?,?,?)", structure)
            self.con.commit()
        except Exception:
            if self.con.in_transaction:
                self.con.rollback()
            raise
        finally:
            src.close()
        self.ensure_defaults()
        self.set_meta("source", str(source))
        self.set_meta("imported", _now())
        return counts

    def _own_designs(self) -> dict[str, tuple]:
        """Tag-Strukturen, auf die eine Pruefregel zeigt: {Typ: (Zeile der Struktur, [Segmentzeilen])}."""
        out = {}
        for (tag_type,) in self.con.execute(f"select distinct tag_type from {RULES}").fetchall():
            segs = self.con.execute(f"select * from {SEGMENTS} where tag_type=? order by pos", (tag_type,)).fetchall()
            if segs:
                struct = self.con.execute(f"select * from {STRUCTURES} where tag_type=?", (tag_type,)).fetchone()
                out[tag_type] = (struct, segs)
        return out

    # --- Excel ------------------------------------------------------------------------------------------------
    def export_xlsx(self, path: str | Path, tables: list[str] | None = None) -> Path:
        """Ein Blatt je Tabelle (Blattnamen wie in Tag Compliance), als Excel-Datentabelle."""
        from openpyxl import Workbook

        from .xlsx import write_table
        wb, used = Workbook(), set()
        wb.remove(wb.active)
        for table in tables or [t for t, _x, _c in self.tables()]:
            cols, rows = self.read(table)
            ws = wb.create_sheet(sheet_name(table))
            write_table(ws, cols, [[("'" + x if x.startswith("=") else x) for x in r] for r in rows],
                        "t_" + sheet_name(table), used)
        path = Path(path)
        wb.save(path)
        return path

    def import_xlsx(self, path: str | Path, only: str | None = None) -> dict[str, int]:
        """Excel einlesen: jedes bekannte Blatt ersetzt seine Tabelle (Spalten nach Kopfzeile, sonst nach Position);
        unbekannte Blaetter werden neue Listen. ``only``: nur diese Tabelle (erstes Blatt, wenn kein passendes)."""
        from openpyxl import load_workbook
        wb = load_workbook(str(path), read_only=True, data_only=True)
        try:
            sheets = {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}
        finally:
            wb.close()
        by_sheet = {sheet_name(t): t for t, _x, _c in self.tables()}
        out: dict[str, int] = {}
        if only is not None:
            want = sheet_name(only)
            data = sheets.get(want) or (next(iter(sheets.values())) if sheets else [])
            out[only] = self.save(only, self._match_rows(only, data))
            return out
        for title, data in sheets.items():
            if not data:
                continue
            table = by_sheet.get(title)
            if table is None:
                cols = [_clean(c) for c in data[0] if _clean(c)]
                key = re.sub(r"[^a-z0-9_]", "_", title.lower()).strip("_")[:30] or "liste"
                if not key[0].isalpha():
                    key = "l_" + key[:28]
                table = self.create_list(key, title, cols)
            out[table] = self.save(table, self._match_rows(table, data))
        return out

    def _match_rows(self, table: str, data: list[list]) -> list[list[str]]:
        if not data:
            return []
        _title, cols = self.info(table)
        head = [_clean(h).lower() for h in data[0]]
        if all(c.lower() in head for c in cols):
            idx = [head.index(c.lower()) for c in cols]
            return [[_clean(r[i]) if i < len(r) else "" for i in idx] for r in data[1:]]
        return [[_clean(x) for x in r[:len(cols)]] for r in data[1:]]

    # --- Pruefung ---------------------------------------------------------------------------------------------
    def checker(self) -> "Checker":
        return Checker(self)

    def designs(self) -> list[str]:
        return [r[0] for r in self.con.execute(f"select distinct tag_type from {SEGMENTS} order by tag_type")]

    def rules(self) -> dict[str, list[str]]:
        """{PDF-Typ: [Tag-Strukturen]} der aktiven Pruefregeln."""
        out: dict[str, list[str]] = {}
        for pdf_type, tag_type, enabled in self.con.execute(
                f"select pdf_type,tag_type,enabled from {RULES} order by pdf_type, tag_type"):
            if truthy(enabled) and _clean(pdf_type) and _clean(tag_type):
                out.setdefault(_clean(pdf_type), []).append(_clean(tag_type))
        return out

    def source_values(self, source: str) -> list[str]:
        """Erlaubte Werte einer Segment-Quelle (Tabelle bzw. ``Tabelle|Spalte``), eindeutig, in Tabellenreihenfolge."""
        table, _sep, col = str(source).partition("|")
        try:
            cols, rows = self.read(table)
        except (KeyError, sqlite3.Error, ValueError):
            return []
        ci = cols.index(col) if col and col in cols else max(0, code_col(cols))
        seen, out = set(), []
        for r in rows:
            v = r[ci] if ci < len(r) else ""
            if v and v not in seen:
                seen.add(v)
                out.append(v)
        return out

    def source_title(self, source: str) -> str:
        kind, ref = _split(source)
        if kind == FREE:
            return "freier Text"
        if kind == CONST:
            return f"Konstante „{ref}“"
        if kind == SEQ:
            return f"laufende Nummer ({_seq_width(ref)} Stellen)"
        table, _s, col = ref.partition("|")
        try:
            title = self.info(table)[0]
        except KeyError:
            title = table
        return f"{title} – {col}" if col else title


def _split(source: str) -> tuple[str, str]:
    s = str(source or "")
    if not s or s == FREE:
        return FREE, ""
    for kind in (CONST, SEQ):
        if s.startswith(kind + ":"):
            return kind, s[len(kind) + 1:]
    return "table", s


def _seq_width(ref: str) -> int:
    try:
        return max(1, min(9, int(ref)))
    except ValueError:
        return 3


#: Befunde der Projekt-Pruefung (Spalte "Projekt-Pruefung"; mehrere werden mit " + " verbunden, z. B.
#: "Code unvollständig + mehrfach vorhanden"). Fehlerhaft ist jeder Status ausser OK und leer.
INCOMPLETE = "Code unvollständig"
CODE_MISSING = "Code fehlt in Projektdefinition"
DUPLICATE = "mehrfach vorhanden"
FINDING_ORDER = (INCOMPLETE, CODE_MISSING, FAULT, DUPLICATE)
_PLACEHOLDER_SEQ = re.compile(r"[X?]")


def is_fault_status(status: str) -> bool:
    return bool(status) and status != OK


def is_placeholder(value: str, digits: bool = False, known=()) -> bool:
    """Platzhalter statt eines Codes: ``?`` irgendwo; bei Nummern (``digits``) jedes ``X`` an Stelle einer Ziffer; bei
    Codes ein Code nur aus ``X``, mit ``XX`` oder einer, bei dem X fuer eine Ziffer eines bekannten Codes steht
    (``ST1X`` -> ST10). Ein X in einem Buchstaben-Code (HEX, XV, CHX) ist kein Platzhalter; ein unbekannter Code "fehlt"."""
    v = str(value or "")
    if "?" in v:
        return True
    if digits:
        return bool(_PLACEHOLDER_SEQ.search(v))
    if not v or "X" not in v.upper():
        return False
    if set(v.upper()) <= {"X"} or "XX" in v.upper():
        return True
    joker = re.compile("".join(r"\d" if c in "Xx" else re.escape(c) for c in v))     # X steht fuer eine Ziffer
    return any(joker.fullmatch(k) for k in known)


@dataclass
class Segment:
    name: str
    source: str
    prefix: str
    suffix: str
    required: bool
    pattern: str = ""
    title: str = ""
    kind: str = FREE
    values: frozenset = frozenset()     # erlaubte Codes (leer = nicht gegen eine Liste pruefbar)


@dataclass
class Design:
    tag_type: str
    segments: list[Segment]
    regex: re.Pattern | None = None
    partial: list[re.Pattern] | None = None
    # Varianten mit jedem Segment als Gruppe: Platzhalter (X/?) ueberall zugelassen, ein unbekannter Code hoechstens
    # an EINER Stelle (sonst passt fast alles irgendwie und der Hinweis waere irrefuehrend)
    relaxed: list[re.Pattern] | None = None


@dataclass
class CheckResult:
    status: str          # OK | Befund(e) mit " + " | "" (Typ ohne Pruefregel)
    hint: str = ""

    def with_count(self, count: int) -> "CheckResult":
        """Mehrfach vorhanden (Anzahl auf einer Seite > 1) bei jedem Befund zusaetzlich melden."""
        if count > 1 and is_fault_status(self.status):
            return CheckResult(f"{self.status} + {DUPLICATE}", f"{self.hint}; {count}× auf einer Seite")
        return self


class Checker:
    """Prueft Tags gegen die Tag-Strukturen des Projekts (Ergebnis je Typ und Tag gemerkt). Geprueft wird immer alles:
    Platzhalter (Code unvollstaendig), Codes, die in der Liste fehlen, Trennzeichen-Regel und Aufbau - die Befunde
    stehen zusammen im Status; "mehrfach vorhanden" kommt ueber ``count`` dazu."""

    MAX_VALUES = 400        # wie Tag Compliance: groessere Listen gelten als freier Text

    def __init__(self, db: ProjectDB):
        self.project = db.name
        self.from_char, self.to_char = db.setting("from_char"), db.setting("to_char")
        self.designs: dict[str, Design] = {}
        self.rules: dict[str, list[Design]] = {}
        self.missing: list[str] = []
        for pdf_type, names in db.rules().items():
            for name in names:
                design = self.designs.get(name) or self._load(db, name)
                if design is None:
                    self.missing.append(name)
                    continue
                self.designs[name] = design
                self.rules.setdefault(pdf_type, []).append(design)
        self._cache: dict[tuple[str, str], CheckResult] = {}

    @staticmethod
    def _load(db: ProjectDB, tag_type: str) -> Design | None:
        rows = db.con.execute(f"select name,source,prefix,suffix,required,visible from {SEGMENTS} where tag_type=? "
                              "order by pos", (tag_type,)).fetchall()
        segs, parts = [], []           # parts je Segment: (davor, danach, streng/Platzhalter, mit unbekanntem Code)
        for name, source, prefix, suffix, required, visible in rows:
            if visible not in (None, "") and not truthy(visible):
                continue
            kind, ref = _split(source)
            values: list[str] = []
            if kind == CONST:
                core = loose = re.escape(ref)
                unknown = None
            elif kind == SEQ:
                core, loose = r"\d{%d}" % _seq_width(ref), r"[0-9X?]{%d}" % _seq_width(ref)
                unknown = None
            elif kind == "table":
                vals = db.source_values(ref)
                if vals and len(vals) < Checker.MAX_VALUES:
                    values = vals
                    known = "(?:" + "|".join(re.escape(v) for v in sorted(vals, key=len, reverse=True)) + ")"
                    # Zeichen wie in der Liste, aber ohne die Trennzeichen des Segments und nicht mit einem
                    # Sonderzeichen am Anfang/Ende (sonst gaelte z. B. "_PFC" als Code)
                    seps = set(prefix or "") | set(suffix or "")
                    extra = "".join(sorted({re.escape(c) for v in vals for c in v if not c.isalnum() and c not in seps}))
                    token = f"[A-Za-z0-9?](?:[A-Za-z0-9?{extra}]*?[A-Za-z0-9?])?"
                    ph = f"(?=[A-Za-z0-9{extra}]*[X?]){token}"              # Platzhalter: enthaelt X oder ?
                    core, loose, unknown = known, f"(?:{known}|{ph})", f"(?:{known}|{token})"
                else:
                    core = loose = r".+?"
                    unknown = None
            else:
                core = loose = r".+?"
                unknown = None
            req = required in (None, "") or truthy(required)
            pre, suf = re.escape(prefix or ""), re.escape(suffix or "")
            pat = pre + core + suf
            segs.append(Segment(_clean(name), _clean(source), prefix or "", suffix or "", req,
                                pat if req else f"(?:{pat})?", db.source_title(source), kind, frozenset(values)))
            parts.append((pre, suf, loose, unknown, req))
        if not segs:
            return None

        def variant(open_at: int | None) -> re.Pattern:
            out = ""
            for i, (pre, suf, loose, unknown, req) in enumerate(parts):
                group = f"{pre}(?P<g{i}>{unknown if i == open_at else loose}){suf}"
                out += group if req else f"(?:{group})?"
            return re.compile(out)

        relaxed = [variant(None)] + [variant(i) for i, x in enumerate(parts) if x[3] is not None]
        partial = [re.compile("".join(s.pattern for s in segs[:k])) for k in range(1, len(segs) + 1)]
        return Design(tag_type, segs, re.compile("".join(s.pattern for s in segs)), partial, relaxed)

    def has_rule(self, pdf_type: str) -> bool:
        return pdf_type in self.rules

    def check(self, pdf_type: str, tag: str, count: int = 1) -> CheckResult:
        key = (pdf_type, tag)
        if key not in self._cache:
            self._cache[key] = self._check(pdf_type, tag)
        return self._cache[key].with_count(count)

    def columns(self, pdf_type: str, tag: str, count: int = 1) -> list[str]:
        r = self.check(pdf_type, tag, count)
        return [r.status, r.hint]

    def is_fault(self, pdf_type: str, tag: str) -> bool:
        return is_fault_status(self.check(pdf_type, tag).status)

    @staticmethod
    def _result(findings: list[tuple[str, str]]) -> CheckResult:
        labels = [f for f in FINDING_ORDER if any(k == f for k, _h in findings)]
        return CheckResult(" + ".join(labels), "; ".join(h for _k, h in findings))

    def _findings(self, design: Design, text: str) -> list[tuple[str, str]] | None:
        """Befunde eines Tags, der zum gelockerten Aufbau einer Struktur passt (None = passt nicht)."""
        m = next((m for rx in design.relaxed if (m := rx.fullmatch(text))), None)
        if m is None:
            return None
        out: list[tuple[str, str]] = []
        for i, seg in enumerate(design.segments):
            v = m.group(f"g{i}")
            if v is None:
                continue
            if seg.kind == SEQ and is_placeholder(v, digits=True):
                out.append((INCOMPLETE, f"{seg.name} „{v}“ ist ein Platzhalter"))
            elif seg.kind == "table" and seg.values and v not in seg.values:
                if is_placeholder(v, known=seg.values):
                    out.append((INCOMPLETE, f"{seg.name} „{v}“ ist ein Platzhalter"))
                else:
                    out.append((CODE_MISSING, f"{seg.name} „{v}“ nicht in {seg.title}"))
            elif seg.kind == FREE and "?" in v:
                out.append((INCOMPLETE, f"{seg.name} „{v}“ enthält „?“"))
        return out

    def _check(self, pdf_type: str, tag: str) -> CheckResult:
        designs = self.rules.get(pdf_type)
        if not designs:
            return CheckResult("", "")
        for d in designs:
            if d.regex.fullmatch(tag):
                return CheckResult(OK, d.tag_type)
        candidates = [(tag, [])]
        if self.from_char and self.to_char and self.from_char in tag:
            fixed = tag.replace(self.from_char, self.to_char)
            candidates.append((fixed, [(FAULT, f"Trennzeichen „{self.from_char}“ statt „{self.to_char}“ "
                                               f"({fixed})")]))
        best: list[tuple[str, str]] | None = None
        for text, base in candidates:                   # beides immer pruefen: Codes/Platzhalter und Trennzeichen
            for d in designs:
                found = self._findings(d, text)
                if found is None:
                    continue
                found = base + found
                if best is None or len(found) < len(best):
                    best = [(k, f"{d.tag_type}: {h}" if k != FAULT else h) for k, h in found]
            if best is not None:
                break
        if best:
            return self._result(best)
        best_d, best_k = designs[0], -1                 # passt zu keinem Aufbau: erstes Segment, das nicht passt
        for d in designs:
            k = 0
            while k < len(d.partial) and d.partial[k].match(tag):
                k += 1
            if k > best_k:
                best_d, best_k = d, k
        if best_k >= len(best_d.segments):
            hint = f"{best_d.tag_type}: zusätzliche Zeichen am Ende"
        else:
            seg = best_d.segments[best_k]
            sep = f" bzw. Trennzeichen „{seg.prefix or seg.suffix}“" if (seg.prefix or seg.suffix) else ""
            hint = f"{best_d.tag_type}: Segment „{seg.name}“ passt nicht ({seg.title}{sep})"
        findings = [(FAULT, hint)]
        if "?" in tag:
            findings.insert(0, (INCOMPLETE, "Tag enthält „?“"))
        return self._result(findings)


def default_project_name(path: str | Path) -> str:
    return Path(path).stem
