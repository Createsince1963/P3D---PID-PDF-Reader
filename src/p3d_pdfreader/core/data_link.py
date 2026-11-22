"""Datenlink: eine Excel-Tabelle (z. B. die Instrumenten-Gesamtliste aus P3D InstrumentationList) importieren und
ueber zwei Schluesselspalten mit den Tabellen des Tools verknuepfen (Nutzervorgabe 2026-11-22). Ohne Qt.

* **Datenlink 1** - Spalte der Importtabelle, die zum Datenlink-Feld der Tabelle 1 (Dateien, z. B. „Zeichnungsnr.“)
  passt, z. B. „P&ID No.“.
* **Datenlink 2** - Spalte der Importtabelle, die zum Datenlink-Feld der Tabelle 2 (Tags der gewaehlten PDF, z. B.
  „Tag“) passt, z. B. „Tag“.

Abgleich: Gross-/Kleinschreibung und Leerzeichen egal. Zuerst exakt; gibt es keinen exakten Treffer, zaehlt die
**Endung ab einem Bindestrich** (Importwert „301-30-149-TI-300“ passt zum Tag „TI-300“). Sind beide Datenlinks aktiv,
zaehlen fuer eine Tag-Zeile nur Importzeilen derselben Zeichnung (Datenlink 1).

Die bearbeitete Importtabelle liegt in ``config/data_link.json``; die Datenlink-Felder der Tool-Tabellen in
``config/state.json`` (Schluessel ``data_link_fields``).

Seit 1.0.32 wird die Liste im Kachel-Editor (Modul ``column_editor`` aus P3D Tag Compliance) angepasst: gespeichert
werden die eingelesene Originalliste (``raw_headers``/``raw_rows``), die Anpassung (``tile_config``, Schritte, Reihenfolge,
Namen, Export ja/nein) und das Ergebnis (``headers``/``rows``, ``hidden`` = nicht exportierte Spalten)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

FILE_NAME = "data_link.json"
MAX_JOINED = 5          # hoechstens so viele verschiedene Werte je Zelle, wenn mehrere Importzeilen passen
JOIN = " | "


def cell_text(value) -> str:
    """Excel-Zellwert als Text (ganze Zahlen ohne „.0“, Datum als JJJJ-MM-TT)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d") if value.time() == datetime.min.time() else value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def norm(value) -> str:
    return "".join(str(value or "").split()).casefold()


def suffixes(value: str) -> list[str]:
    """Alle Endungen ab einem Bindestrich (ohne den Wert selbst): „a-b-c“ -> „b-c“, „c“."""
    parts = value.split("-")
    return ["-".join(parts[i:]) for i in range(1, len(parts)) if "-".join(parts[i:])]


def sheet_names(path) -> list[str]:
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def read_sheet(path, sheet: str | None = None) -> tuple[list[str], list[list[str]]]:
    """Ein Blatt lesen: Kopfzeile = erste Zeile mit mindestens zwei Eintraegen. Ganz leere Spalten und Zeilen fallen
    weg; doppelte oder leere Spaltennamen werden eindeutig gemacht."""
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[sheet] if sheet else wb.worksheets[0]
        data = [[cell_text(v) for v in r] for r in ws.iter_rows(values_only=True)]
    finally:
        wb.close()
    start = next((i for i, r in enumerate(data) if sum(1 for v in r if v) >= 2), None)
    if start is None:
        raise ValueError("Keine Kopfzeile gefunden (Blatt leer?).")
    head, body = data[start], [r for r in data[start + 1:] if any(r)]
    width = max([len(head)] + [len(r) for r in body])
    keep = [c for c in range(width)
            if (c < len(head) and head[c]) or any(c < len(r) and r[c] for r in body)]
    headers: list[str] = []
    for n, c in enumerate(keep, start=1):
        name = (head[c] if c < len(head) else "") or f"Spalte {n}"
        base, k = name, 2
        while name in headers:
            name, k = f"{base} ({k})", k + 1
        headers.append(name)
    rows = [[r[c] if c < len(r) else "" for c in keep] for r in body]
    return headers, rows


@dataclass
class ImportTable:
    """Bearbeitete Importtabelle. ``headers``/``rows`` in Anzeigereihenfolge; ``hidden`` = Spalten, die nicht an das
    Tool uebergeben werden; ``link1``/``link2`` = Spaltennamen der Datenlinks (oder "")."""
    source: str = ""
    sheet: str = ""
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)
    link1: str = ""
    link2: str = ""
    raw_headers: list[str] = field(default_factory=list)   # eingelesene Originalliste (Grundlage der Anpassung)
    raw_rows: list[list[str]] = field(default_factory=list)
    tile_config: dict = field(default_factory=dict)        # Anpassung aus dem Kachel-Editor (column_editor, schema 3)

    # --- Speichern -------------------------------------------------------------------------------------------------
    @staticmethod
    def file(folder) -> Path:
        return Path(folder) / FILE_NAME

    def save(self, folder) -> Path:
        path = self.file(folder)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def load(cls, folder) -> "ImportTable | None":
        try:
            data = json.loads(cls.file(folder).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or not isinstance(data.get("headers"), list):
            return None
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        table = cls(**known)
        table.headers = [str(h) for h in table.headers]
        table.rows = [[str(v) for v in r] for r in table.rows if isinstance(r, list)]
        table.hidden = [h for h in table.hidden if h in table.headers]
        table.link1 = table.link1 if table.link1 in table.headers else ""
        table.link2 = table.link2 if table.link2 in table.headers else ""
        table.raw_headers = [str(h) for h in (table.raw_headers or [])]
        table.raw_rows = [[str(v) for v in r] for r in (table.raw_rows or []) if isinstance(r, list)]
        table.tile_config = table.tile_config if isinstance(table.tile_config, dict) else {}
        return table

    @staticmethod
    def remove(folder) -> None:
        try:
            ImportTable.file(folder).unlink()
        except OSError:
            pass

    # --- Abfragen --------------------------------------------------------------------------------------------------
    def transfer_columns(self) -> list[str]:
        """Spalten, die an die Tag-Tabelle uebergeben werden (sichtbare, in Anzeigereihenfolge)."""
        hidden = set(self.hidden)
        return [h for h in self.headers if h not in hidden]

    def link(self, n: int) -> str:
        return self.link1 if n == 1 else self.link2

    def base(self) -> tuple[list[str], list[list[str]]]:
        """Grundlage fuer den Kachel-Editor: die eingelesene Originalliste, bei aelteren Dateien das gespeicherte Ergebnis."""
        if self.raw_headers:
            return list(self.raw_headers), [list(r) for r in self.raw_rows]
        return list(self.headers), [list(r) for r in self.rows]

    def export_view(self) -> tuple[list[str], list[list[str]]]:
        """Die kompatible Importliste: nur uebergebene Spalten, in Anzeigereihenfolge."""
        pos = [self.headers.index(h) for h in self.transfer_columns()]
        return [self.headers[c] for c in pos], [[r[c] if c < len(r) else "" for c in pos] for r in self.rows]


def unique_names(names: list[str]) -> list[str]:
    """Spaltennamen eindeutig machen (leere -> „Spalte n“, doppelte -> „Name (2)“)."""
    out: list[str] = []
    for n, name in enumerate(names, start=1):
        name = str(name or "").strip() or f"Spalte {n}"
        base, k = name, 2
        while name in out:
            name, k = f"{base} ({k})", k + 1
        out.append(name)
    return out


def write_excel(path, headers: list[str], rows: list[list], sheet: str = "Importliste") -> Path:
    """Liste als Excel-Datentabelle schreiben (kompatibel zu „Liste importieren“: Kopf in Zeile 1)."""
    from openpyxl import Workbook

    from .xlsx import write_table
    wb = Workbook()
    ws = wb.active
    ws.title = sheet[:31]
    write_table(ws, headers, rows, sheet)
    path = Path(path)
    wb.save(path)
    return path


class _KeyIndex:
    """Index einer Spalte: normalisierter Wert -> Zeilen, Endung -> Zeilen."""

    def __init__(self, values: list[str]):
        self.exact: dict[str, list[int]] = {}
        self.tail: dict[str, list[int]] = {}
        for i, v in enumerate(values):
            key = norm(v)
            if not key:
                continue
            self.exact.setdefault(key, []).append(i)
            for s in suffixes(key):
                self.tail.setdefault(s, []).append(i)

    def find(self, value) -> list[int]:
        key = norm(value)
        if not key:
            return []
        return self.exact.get(key) or self.tail.get(key, [])


class DataLink:
    """Verknuepfung der Importtabelle mit den Tool-Tabellen. ``fields`` = Datenlink-Feld je Tool-Tabelle
    (``{"files": "Zeichnungsnr.", "tags": "Tag"}``)."""

    def __init__(self, table: ImportTable, fields: dict[str, str]):
        self.table = table
        self.fields = dict(fields or {})
        cols = table.headers
        self._idx: dict[int, _KeyIndex] = {}
        for n in (1, 2):
            name = table.link(n)
            if name in cols:
                c = cols.index(name)
                self._idx[n] = _KeyIndex([r[c] if c < len(r) else "" for r in table.rows])
        self.columns = table.transfer_columns()
        self._pos = [cols.index(h) for h in self.columns]

    def active(self, n: int) -> bool:
        """Datenlink n aktiv: Spalte in der Importtabelle gesetzt und Feld in der Tool-Tabelle gesetzt."""
        return n in self._idx and bool(self.fields.get("files" if n == 1 else "tags"))

    def file_rows(self, value) -> list[int]:
        return self._idx[1].find(value) if self.active(1) else []

    def tag_rows(self, value, file_value=None) -> list[int]:
        """Importzeilen zu einem Wert der Tag-Tabelle; mit aktivem Datenlink 1 nur Zeilen derselben Zeichnung."""
        if not self.active(2):
            return []
        hits = self._idx[2].find(value)
        if hits and self.active(1) and file_value is not None:
            same = set(self.file_rows(file_value))
            hits = [i for i in hits if i in same]
        return hits

    def match_count(self, n: int, values) -> tuple[int, int]:
        """(Werte mit mindestens einem Treffer, nicht leere Werte) fuer Datenlink n – Pruefung nach dem Verknuepfen."""
        if n not in self._idx:
            return 0, 0
        idx, hits, total = self._idx[n], 0, 0
        for v in values:
            if not norm(v):
                continue
            total += 1
            hits += bool(idx.find(v))
        return hits, total

    def samples(self, n: int, limit: int = 3) -> list[str]:
        """Einige nicht leere Werte der Datenlink-Spalte n der Importtabelle (fuer Fehlermeldungen)."""
        name = self.table.link(n)
        if name not in self.table.headers:
            return []
        c, out = self.table.headers.index(name), []
        for r in self.table.rows:
            v = r[c] if c < len(r) else ""
            if v and v not in out:
                out.append(v)
                if len(out) >= limit:
                    break
        return out

    def values(self, rows: list[int]) -> list[str]:
        """Werte der uebergebenen Spalten; bei mehreren Treffern verschiedene Werte mit „ | “ verbunden."""
        out = []
        for c in self._pos:
            seen: list[str] = []
            for i in rows:
                v = self.table.rows[i][c] if c < len(self.table.rows[i]) else ""
                if v and v not in seen:
                    seen.append(v)
            text = JOIN.join(seen[:MAX_JOINED]) + (JOIN + "…" if len(seen) > MAX_JOINED else "")
            out.append(text)
        return out


# ----------------------------------------------------------------------------------------------------------------
# Review-Tabelle: Abgleich der PDF-Tags mit der Importtabelle (1.0.36)
# ----------------------------------------------------------------------------------------------------------------
STATUS_OK = "OK"
STATUS_NOT_IN_LIST = "Nicht in Liste"            # Tag im PDF, keine passende Zeile der Importtabelle
STATUS_NOT_IN_PDF = "Fehlt im PDF"               # Zeile der Importtabelle zu einer gescannten Zeichnung, Tag nicht im PDF
STATUS_NO_PDF = "Zeichnung nicht gescannt"       # Zeile der Importtabelle, deren Zeichnung (Datenlink 1) kein PDF hat
REVIEW_STATUS = (STATUS_OK, STATUS_NOT_IN_LIST, STATUS_NOT_IN_PDF, STATUS_NO_PDF)
REVIEW_HEAD = ["Prüfergebnis", "PDF", "Zeichnung (Tool)", "Typ", "Tag (PDF)", "Anzahl", "Seiten", "Importzeilen"]


def review_rows(link: DataLink, pdfs: list[tuple[str, object, list[tuple]]]) -> tuple[list[str], list[list]]:
    """Review-Tabelle aus Datenlink und PDF-Tags. ``pdfs`` = je PDF ``(PDF-Name, Wert des Datenlink-Felds der
    Dateiliste oder None, [(Typ, Tag, Anzahl, Seiten, Wert des Datenlink-Felds der Tag-Tabelle), …])``.

    Zeilen: jedes PDF-Tag mit „OK“ (passende Importzeile, mit Datenlink 1 nur derselben Zeichnung) oder „Nicht in
    Liste“; danach jede nicht getroffene Importzeile mit „Fehlt im PDF“ (ihre Zeichnung ist gescannt) bzw.
    „Zeichnung nicht gescannt“ (nur mit Datenlink 1). Rechts die exportierten Spalten der Importtabelle.
    Ohne aktiven Datenlink 2 gibt es keine Review-Tabelle (leere Liste)."""
    headers = REVIEW_HEAD + unique_names([h if h not in REVIEW_HEAD else h + " (Liste)" for h in link.columns])
    if not link.active(2):
        return headers, []
    empty = [""] * len(link.columns)
    rows: list[list] = []
    hit: set[int] = set()
    scanned: dict[int, str] = {}                   # Importzeile -> PDF-Name (Zeichnung gescannt)
    use_files = link.active(1)
    for name, file_value, tags in pdfs:
        if use_files:
            for i in link.file_rows(file_value):
                scanned.setdefault(i, name)
        for typ, tag, count, pages, value in tags:
            found = link.tag_rows(value, file_value if use_files else None)
            hit.update(found)
            rows.append([STATUS_OK if found else STATUS_NOT_IN_LIST, name, cell_text(file_value), typ, tag, count,
                         pages, ", ".join(str(i + 1) for i in found[:MAX_JOINED]),
                         *(link.values(found) if found else empty)])
    key = link.table.headers.index(link.table.link(2))      # aktiv(2) -> Spalte vorhanden
    for i, row in enumerate(link.table.rows):
        if i in hit or not cell_text(row[key] if key < len(row) else ""):
            continue                                         # getroffen oder ohne Tag
        if use_files and i not in scanned:
            status, pdf = STATUS_NO_PDF, ""
        else:
            status, pdf = STATUS_NOT_IN_PDF, scanned.get(i, "")
        rows.append([status, pdf, "", "", "", "", "", str(i + 1), *link.values([i])])
    return headers, rows


def review_summary(rows: list[list]) -> dict[str, int]:
    out = {s: 0 for s in REVIEW_STATUS}
    for r in rows:
        out[r[0]] = out.get(r[0], 0) + 1
    return out
