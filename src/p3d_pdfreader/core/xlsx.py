"""Gemeinsame Excel-Ausgabe: jedes Blatt als echte Excel-Datentabelle (Einfuegen > Tabelle: Formatvorlage,
Filterknoepfe, gebaenderte Zeilen) mit fixierter Kopfzeile und automatisch angepasster Spaltenbreite."""
from __future__ import annotations

import re
from datetime import date, datetime

MIN_WIDTH, MAX_WIDTH = 6, 60
TABLE_STYLE = "TableStyleMedium2"


def _text_len(value) -> int:
    if value is None:
        return 0
    if isinstance(value, (datetime, date)):
        return 16
    return max((len(line) for line in str(value).splitlines()), default=0)


def autofit(ws, headers: list[str], rows: list[list], extra: int = 2) -> None:
    """Spaltenbreite nach dem laengsten Inhalt, begrenzt auf ``MAX_WIDTH``. Der Kopf ist fett und hat in der
    Datentabelle einen Filterknopf (ca. 3 Zeichen) - daher etwas breiter gerechnet als die Zellwerte."""
    from openpyxl.utils import get_column_letter
    for c, header in enumerate(headers, start=1):
        head = round(_text_len(header) * 1.15) + 5
        cells = max([_text_len(r[c - 1]) for r in rows if c - 1 < len(r)], default=0) + extra
        ws.column_dimensions[get_column_letter(c)].width = max(MIN_WIDTH, min(MAX_WIDTH, max(head, cells)))


def table_name(text: str, used: set[str]) -> str:
    """Gueltiger, eindeutiger Name der Excel-Tabelle (Buchstabe am Anfang, keine Leer-/Sonderzeichen)."""
    base = re.sub(r"\W", "_", text) or "Tabelle"
    if not base[0].isalpha():
        base = "T_" + base
    name, n = base[:240], 2
    while name.casefold() in used:
        name, n = f"{base[:236]}_{n}", n + 1
    used.add(name.casefold())
    return name


def unique_headers(headers: list[str]) -> list[str]:
    """Spaltennamen einer Excel-Datentabelle muessen gefuellt und eindeutig sein (ohne Gross-/Kleinschreibung), sonst
    meldet Excel die Datei als beschaedigt - z. B. wenn eine hinzugefuegte Importspalte wie eine PDF-Spalte heisst."""
    out, used = [], set()
    for i, header in enumerate(headers, start=1):
        base = str(header) or f"Spalte {i}"
        name, n = base, 2
        while name.casefold() in used:
            name, n = f"{base} ({n})", n + 1
        used.add(name.casefold())
        out.append(name)
    return out


def write_table(ws, headers: list[str], rows: list[list], name: str, used: set[str] | None = None) -> None:
    """Kopf + Zeilen schreiben und als Excel-Datentabelle formatieren (bei 0 Zeilen nur Kopf, keine Tabelle)."""
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table, TableStyleInfo
    headers = unique_headers(headers)
    ws.append(headers)
    for row in rows:
        ws.append(list(row))
    ws.freeze_panes = "A2"
    if rows and headers:
        ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"
        table = Table(displayName=table_name(name, used if used is not None else set()), ref=ref)
        table.tableStyleInfo = TableStyleInfo(name=TABLE_STYLE, showRowStripes=True, showColumnStripes=False)
        ws.add_table(table)
    autofit(ws, headers, rows)
