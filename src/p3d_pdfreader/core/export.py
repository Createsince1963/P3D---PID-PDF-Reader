"""Export der Scan-Ergebnisse: Excel (Blaetter "Dateien" und "Tags") und CSV (``;``, UTF-8 mit BOM fuer Excel)."""
from __future__ import annotations

import csv
from pathlib import Path

from .extract import PdfResult
from .review_store import FIELDS, ReviewStore

FILE_HEADERS = ["PDF", "Zeichnungsnr.", "Erstellt (PDF)", "Ersteller", "Drawn", "Checked", "Datum Schriftfeld", "Rev",
                "Rev-Datum", "Rev-Text", "Rev-Kuerzel", "Plot-Benutzer", "Creator", "Seiten", "Groesse KB",
                "Anzahl Tags", "Ordner", "Fehler"]
TAG_HEADERS = ["PDF", "Zeichnungsnr.", "Typ", "Tag", "Anzahl", "Seiten", "X", "Y"]


def file_rows(results: list[PdfResult]) -> list[list]:
    return [[r.name, r.drawing_no, r.created.strftime("%Y-%m-%d %H:%M") if r.created else "", r.author_display,
             r.drawn, r.checked, r.title_date, r.revision, r.revision_date, r.revision_text, r.revision_by,
             r.plot_user, r.creator, r.pages, r.size_kb, len(r.tags), str(r.path.parent), r.error] for r in results]


def tag_rows(results: list[PdfResult], review: bool = False) -> list[list]:
    """Eine Zeile je Tag; mit ``review`` zusaetzlich die gespeicherten Review-Spalten (``review_store.FIELDS``)."""
    rows = []
    for r in results:
        store = ReviewStore(r.path) if review else None
        for t in r.tags:
            row = [r.name, r.drawing_no, t.type, t.tag, t.count, t.pages_text, t.x, t.y]
            rows.append(row + store.values(t.type, t.tag) if store else row)
    return rows


def write_xlsx(path: str | Path, results: list[PdfResult]) -> Path:
    """Blaetter "Dateien" und "Tags" (mit gespeicherten Review-Spalten) als Excel-Datentabellen, Spaltenbreite autofit."""
    from openpyxl import Workbook

    from .xlsx import write_table

    wb, used = Workbook(), set()
    for i, (title, headers, rows) in enumerate((("Dateien", FILE_HEADERS, file_rows(results)),
                                               ("Tags", TAG_HEADERS + FIELDS, tag_rows(results, review=True)))):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = title
        write_table(ws, headers, rows, title, used)
    path = Path(path)
    wb.save(path)
    return path


def write_csv(path: str | Path, headers: list[str], rows: list[list]) -> Path:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(headers)
        writer.writerows(rows)
    return path
