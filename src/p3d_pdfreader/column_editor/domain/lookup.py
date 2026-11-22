"""Add columns from another list (Power Query: Merge queries, left join): look a value up by a key column. Pure Python, no Qt
(openpyxl is imported only when an Excel file is read).

The other list is an Excel file (sheet by name). It is only read, never written. The values are looked up when the column is
created and again when a saved view is loaded; a missing file is reported and the column is not created.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .transformation_node import OutputDefinition, TransformationNode


class LookupError_(Exception):  # noqa: N801 - plain name would hide the built-in LookupError
    """Readable reason why the other list cannot be used."""


@dataclass(frozen=True, slots=True)
class LookupParameters:
    file: str = ""
    sheet: str = ""
    source_key: str = ""          # key of the column of THIS table that is looked up
    match_label: str = ""         # header of the key column in the other list
    take_label: str = ""          # header of the column that is brought over
    match_case: bool = False
    missing_text: str = ""        # shown when the key is not found
    output_key: str = ""

    def to_dict(self) -> dict:
        return {"file": self.file, "sheet": self.sheet, "source_key": self.source_key, "match_label": self.match_label,
                "take_label": self.take_label, "match_case": self.match_case, "missing_text": self.missing_text,
                "output_key": self.output_key}

    @staticmethod
    def from_dict(d: dict) -> "LookupParameters":
        return LookupParameters(str(d.get("file") or ""), str(d.get("sheet") or ""), str(d.get("source_key") or ""),
                                str(d.get("match_label") or ""), str(d.get("take_label") or ""), bool(d.get("match_case", False)),
                                str(d.get("missing_text") or ""), str(d.get("output_key") or ""))


_CACHE: dict[tuple, tuple[list[str], list[list[str]]]] = {}

# How one worksheet (openpyxl, read-only) becomes (headers, rows). The module is reusable in other applications: a host can plug
# in its own reader with `set_sheet_reader`. Without one, the reader of P3D - Tag Compliance (`linetag_sources`) is used when it is
# importable, else the small built-in reader below.
SheetReader = Callable[[object], "tuple[list[str], list[list[str]]]"]
_sheet_reader: SheetReader | None = None


def set_sheet_reader(reader: SheetReader | None) -> None:
    """Install the worksheet reader of the host application (None = back to the default). Clears the read cache."""
    global _sheet_reader
    _sheet_reader = reader
    _CACHE.clear()


def _cell_text(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def default_sheet_reader(ws) -> tuple[list[str], list[list[str]]]:
    """Built-in reader: header = first non-empty row (duplicates get ' (2)', ' (3)' ...), empty rows are skipped."""
    it = ws.iter_rows(values_only=True)
    headers: list[str] = []
    for row in it:
        if any(c is not None and str(c).strip() != "" for c in row):
            last = max(i for i, c in enumerate(row) if c is not None and str(c).strip() != "")
            seen: dict[str, int] = {}
            for i, c in enumerate(row[:last + 1]):
                name = _cell_text(c).strip() or f"Column {i + 1}"
                seen[name] = seen.get(name, 0) + 1
                headers.append(name if seen[name] == 1 else f"{name} ({seen[name]})")
            break
    if not headers:
        return [], []
    n = len(headers)
    rows: list[list[str]] = []
    for row in it:
        vals = [_cell_text(c) for c in row[:n]]
        vals += [""] * (n - len(vals))
        if any(v.strip() for v in vals):
            rows.append(vals)
    return headers, rows


def sheet_reader() -> SheetReader:
    if _sheet_reader is not None:
        return _sheet_reader
    try:
        import linetag_sources as SRC            # P3D - Tag Compliance host: same reading rules as the rest of the program
        return SRC._read_sheet
    except ImportError:
        return default_sheet_reader


def read_list(path: str | Path, sheet: str = "") -> tuple[list[str], list[list[str]]]:
    """(headers, rows) of one sheet of the other list, read from a byte copy (the file itself is not opened for reading twice
    and never for writing). Cached until the file changes."""
    path = Path(path)
    try:
        key = (str(path), path.stat().st_mtime_ns, sheet)
    except OSError as e:
        raise LookupError_(f"Die andere Liste ließ sich nicht lesen: {e}") from e
    if key in _CACHE:
        return _CACHE[key]
    from openpyxl import load_workbook
    with tempfile.TemporaryDirectory(prefix="p3d_lookup_") as tmp:
        copy = Path(tmp) / path.name
        try:
            shutil.copyfile(path, copy)
            wb = load_workbook(copy, read_only=True, data_only=True)
        except Exception as e:  # noqa: BLE001
            raise LookupError_(f"'{path.name}' lässt sich nicht als Excel-Mappe öffnen: {e}") from e
        try:
            names = [ws.title for ws in wb.worksheets]
            name = sheet or (names[0] if names else "")
            if name not in names:
                raise LookupError_(f"Blatt '{sheet}' fehlt in '{path.name}'. Vorhanden: {', '.join(names)}")
            headers, rows = sheet_reader()(wb[name])
        finally:
            wb.close()
    if len(_CACHE) > 8:
        _CACHE.clear()
    _CACHE[key] = (headers, rows)
    return headers, rows


def sheet_names(path: str | Path) -> list[str]:
    from openpyxl import load_workbook
    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001
        raise LookupError_(f"'{Path(path).name}' lässt sich nicht als Excel-Mappe öffnen: {e}") from e
    try:
        return [ws.title for ws in wb.worksheets]
    finally:
        wb.close()


def validate(p: LookupParameters) -> str:
    if not p.file:
        return "Andere Liste (Excel-Datei) wählen."
    if not p.source_key or not p.match_label or not p.take_label:
        return "Schlüsselspalte dieser Tabelle, Schlüsselspalte der anderen Liste und zu übernehmende Spalte wählen."
    return ""


def compute(p: LookupParameters, get, headers: list[str] | None = None, rows: list[list[str]] | None = None) -> list[str]:
    """Look the values up. `headers` / `rows` may be given (tests, dialog preview); else the file is read."""
    if headers is None or rows is None:
        headers, rows = read_list(p.file, p.sheet)
    for label in (p.match_label, p.take_label):
        if label not in headers:
            raise LookupError_(f"Die andere Liste hat keine Spalte '{label}'.")
    ki, ti = headers.index(p.match_label), headers.index(p.take_label)

    def norm(v: str) -> str:
        v = v.strip()
        return v if p.match_case else v.casefold()
    index: dict[str, str] = {}
    for r in rows:
        k = norm(r[ki]) if ki < len(r) else ""
        if k and k not in index:                                        # the first match wins
            index[k] = r[ti] if ti < len(r) else ""
    return [index.get(norm("" if v is None else str(v)), p.missing_text) if str(v or "").strip() else "" for v in get(p.source_key)]


def describe(p: LookupParameters, label_of=lambda k: k) -> str:
    return f"'{p.take_label}' hinzufügen aus {Path(p.file).name}" + (f" / {p.sheet}" if p.sheet else "") + \
        f" (Abgleich {label_of(p.source_key)} = {p.match_label})"


def build_node(*, node_id: str, input_id: str, out_id: str, out_name: str, params: LookupParameters) -> TransformationNode:
    err = validate(params)
    if err:
        raise LookupError_(err)
    return TransformationNode(node_id=node_id, operation="lookup", input_ids=(input_id,), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip() or params.take_label, "text"), keep_inputs=True)
