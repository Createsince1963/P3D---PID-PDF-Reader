"""Review-Positionen: jede Tag-Fundstelle bekommt eine Positionsnummer (Pos.-Nr.), einen automatischen Review-Kommentar
und Felder fuer Pruefstatus und Bemerkung. Dieselbe Nummerierung steht in den Redline-Kommentaren (``redline``), so dass
Excel-Zeile und Markierung in der PDF eindeutig zusammengehoeren.

Reihenfolge der Nummern: Typ, Tag (wie in der Tag-Tabelle), dann Fundstelle 1..n."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .extract import PdfResult, Tag

from .project_defs import CHECK_HEADERS, is_fault_status
from .review_store import CHANGE_VALUES, FIELDS, REVIEW_VALUES, ReviewStore

STATUS_VALUES = tuple(v for v in REVIEW_VALUES if v)
REVIEW_HEADERS = ["Pos.-Nr.", "PDF", "Zeichnungsnr.", "Rev", "Typ", "Tag", "Seite", "Fundstelle", "Anzahl auf Seite",
                  "Doppelt",
                  "Review-Kommentar", "X", "Y", *FIELDS]   # FIELDS: Review, Änderung, Neuer Wert, Bemerkung, WPO, Datum, User


@dataclass
class ReviewPosition:
    pos: int
    tag: Tag
    occurrence: int          # 1..n auf dieser Seite
    total: int               # Anzahl auf dieser Seite (> 1 = doppelt)
    rect: tuple
    page: int = 0            # 0-basiert

    @property
    def comment(self) -> str:
        if self.total > 1:
            return f"Doppelter Tag – Fundstelle {self.occurrence}/{self.total} prüfen"
        return "Tag erkannt"

    @property
    def default_status(self) -> str:
        return "Offen" if self.total > 1 else ""


def positions(tags: list[Tag]) -> list[ReviewPosition]:
    """Alle Fundstellen aller Seiten; Doppelt-Bewertung je Seite (mehrseitige Plots = oft dieselbe Zeichnung)."""
    out: list[ReviewPosition] = []
    for tag in sorted(tags, key=lambda t: (t.type, t.tag)):
        hits = tag.hits or ([(0, tag.rect)] if tag.rect else [])
        for page in sorted({p for p, _r in hits}):
            rects = sorted((r for p, r in hits if p == page), key=lambda r: (round(r[1]), r[0]))
            for n, rect in enumerate(rects, start=1):
                out.append(ReviewPosition(len(out) + 1, tag, n, len(rects), rect, page))
    return out


def review_headers(checker=None) -> list[str]:
    """Spalten der Review-Excel; im Projektmodus nach "Doppelt" die Projekt-Pruefung."""
    if checker is None:
        return list(REVIEW_HEADERS)
    i = REVIEW_HEADERS.index("Doppelt") + 1
    return REVIEW_HEADERS[:i] + CHECK_HEADERS + REVIEW_HEADERS[i:]


def review_rows(result: PdfResult, tags: list[Tag] | None = None, checker=None) -> list[list]:
    """Eine Zeile je Fundstelle; Review-Spalten aus dem gespeicherten Review der PDF (Bearbeiten-Modus).
    Ohne gespeicherten Review-Wert bekommen doppelte Tags "Offen". ``checker``: Projekt-Pruefung (Projektmodus)."""
    store = ReviewStore(result.path)
    rows = []
    for p in positions(result.tags if tags is None else tags):
        values = store.values(p.tag.type, p.tag.tag)
        if not values[0] and p.total > 1:
            values[0] = "Offen"
        rows.append([p.pos, result.name, result.drawing_no, result.revision, p.tag.type, p.tag.tag, p.page + 1,
                     f"{p.occurrence}/{p.total}", p.total, "Ja" if p.total > 1 else "",
                     *(checker.columns(p.tag.type, p.tag.tag, p.tag.count) if checker is not None else []),
                     p.comment,
                     round(p.rect[0], 1), round(p.rect[1], 1), *values])
    return rows


def write_review_xlsx(path: str | Path, results: list[PdfResult], tags_by_pdf: dict | None = None,
                      checker=None) -> Path:
    """Review-Excel: Blatt "Review" (eine Zeile je Fundstelle: Pos.-Nr., Review-Kommentar, Review als Auswahlliste,
    Aenderung, Neuer Wert, Bemerkung, WPO, zuletzt Datum und User), Blatt "Dateien", Blatt "Info".
    Alle Blaetter als Excel-Datentabelle mit autofit; doppelte Tags gelb."""
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    from .export import FILE_HEADERS, file_rows
    from .xlsx import write_table

    wb, used = Workbook(), set()
    ws = wb.active
    ws.title = "Review"
    rows = []
    for result in results:
        rows.extend(review_rows(result, (tags_by_pdf or {}).get(result.path), checker))
    if len(results) > 1:                                      # Pos.-Nr. je PDF eindeutig: "<PDF-Nr>.<Pos>"
        pdf_no = {r.name: i for i, r in enumerate(results, start=1)}
        for row in rows:
            row[0] = f"{pdf_no[row[1]]}.{row[0]}"
    headers = review_headers(checker)
    write_table(ws, headers, rows, "Review", used)
    col = {h: i + 1 for i, h in enumerate(headers)}
    dup_fill = PatternFill("solid", fgColor="FFF2CC")
    for r in range(2, len(rows) + 2):
        if ws.cell(r, col["Doppelt"]).value == "Ja":
            for c in range(1, len(headers) + 1):
                ws.cell(r, c).fill = dup_fill
    if rows:
        for header, values in (("Review", REVIEW_VALUES), ("Änderung", CHANGE_VALUES)):
            letter = get_column_letter(col[header])
            dv = DataValidation(type="list", formula1='"' + ",".join(v for v in values if v) + '"', allow_blank=True)
            dv.add(f"{letter}2:{letter}{len(rows) + 1}")
            ws.add_data_validation(dv)

    write_table(wb.create_sheet("Dateien"), FILE_HEADERS, file_rows(results), "Dateien", used)
    info_rows = [["Erstellt", datetime.now().strftime("%Y-%m-%d %H:%M")], ["Werkzeug", "P3D PDF Reader"],
                 ["PDFs", len(results)], ["Positionen", len(rows)],
                 ["Doppelte Fundstellen", sum(1 for r in rows if r[col["Doppelt"] - 1] == "Ja")],
                 ["Pos.-Nr.", "gleiche Nummer wie im Redline-PDF (Kommentar 'Pos. n')"],
                 ["Review", ", ".join(v for v in REVIEW_VALUES if v)],
                 ["Änderung", ", ".join(v for v in CHANGE_VALUES if v)]]
    if checker is not None:
        info_rows += [["Projekt", checker.project],
                      ["Projekt-Befunde (Fundstellen)",
                       sum(1 for r in rows if is_fault_status(r[col[CHECK_HEADERS[0]] - 1]))]]
    write_table(wb.create_sheet("Info"), ["Eintrag", "Wert"], info_rows, "Info", used)
    path = Path(path)
    wb.save(path)
    return path
