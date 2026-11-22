"""The neutral `join` node: several columns -> one calculated column (planning basis, section 12). Pure Python, no Qt.

The same function feeds the live info text in the inspector, the preview column and the export.
"""
from __future__ import annotations

from dataclasses import dataclass

from .column_types import ColumnType, OnInvalid
from .convert import ConvertParameters, convert_value, display_value
from .transformation_node import OutputDefinition, TransformationNode
from .type_detection import is_empty

SEPARATOR_PRESETS: tuple[tuple[str, str], ...] = (
    ("_", "Unterstrich  _"), ("-", "Bindestrich  -"), ("/", "Schrägstrich  /"), (" ", "Leerzeichen"), ("", "Kein Trennzeichen"))


class JoinError(Exception):
    """Readable reason why a group cannot be applied."""


@dataclass(frozen=True, slots=True)
class JoinParameters:
    separator: str = "_"
    trim: bool = True
    skip_empty: bool = True
    output_type: ColumnType = ColumnType.TEXT
    on_invalid: OnInvalid = OnInvalid.EMPTY_FLAG
    include_originals_in_export: bool = True
    input_names: tuple[str, ...] = ()           # source keys of the inputs, in result order (rebuild on another data set)
    output_key: str = ""                        # key of the calculated column in the table

    def to_dict(self) -> dict:
        return {"separator": self.separator, "trim": self.trim, "skip_empty": self.skip_empty,
                "output_type": self.output_type.value, "on_invalid": self.on_invalid.value,
                "include_originals_in_export": self.include_originals_in_export,
                "input_names": list(self.input_names), "output_key": self.output_key}

    @staticmethod
    def from_dict(d: dict) -> "JoinParameters":
        try:
            typ = ColumnType(str(d.get("output_type") or "text"))
        except ValueError:
            typ = ColumnType.TEXT
        try:
            inv = OnInvalid(str(d.get("on_invalid") or "empty_flag"))
        except ValueError:
            inv = OnInvalid.EMPTY_FLAG
        return JoinParameters(separator=str(d.get("separator", "_")), trim=bool(d.get("trim", True)),
                              skip_empty=bool(d.get("skip_empty", True)), output_type=typ, on_invalid=inv,
                              include_originals_in_export=bool(d.get("include_originals_in_export", True)),
                              input_names=tuple(str(x) for x in d.get("input_names") or ()),
                              output_key=str(d.get("output_key") or ""))


def join_values(values, p: JoinParameters) -> str:
    """Join the values of ONE row in the given order."""
    parts = []
    for v in values:
        text = "" if v is None else str(v)
        if p.trim:
            text = text.strip()
        if p.skip_empty and is_empty(text):
            continue
        parts.append(text)
    return p.separator.join(parts)


def join_row(values, p: JoinParameters) -> tuple[str, bool]:
    """(display text, valid) of one row including the optional output-type conversion."""
    joined = join_values(values, p)
    if p.output_type in (ColumnType.TEXT, ColumnType.MIXED, ColumnType.UNKNOWN):
        return joined, True
    conv = ConvertParameters(ColumnType.TEXT, p.output_type, on_invalid=p.on_invalid)
    res, ok = convert_value(joined, conv)
    return display_value(res, p.output_type), ok


def join_columns(columns: list[list], p: JoinParameters) -> tuple[list[str], int]:
    """Result column over all rows. `columns` = one value list per input. Returns (values, invalid count)."""
    n = max((len(c) for c in columns), default=0)
    out, bad = [], 0
    for r in range(n):
        text, ok = join_row([c[r] if r < len(c) else "" for c in columns], p)
        out.append(text)
        bad += 0 if ok else 1
    return out, bad


def example_row(columns: list[list], limit: int = 500) -> list:
    """The row used for 'Example result': the first row in which every input has a value, else the first row with any."""
    n = min(max((len(c) for c in columns), default=0), limit)
    best = None
    for r in range(n):
        row = [c[r] if r < len(c) else "" for c in columns]
        if all(not is_empty(v) for v in row):
            return row
        if best is None and any(not is_empty(v) for v in row):
            best = row
    return best or [""] * len(columns)


def build_join_node(*, node_id: str, input_ids: tuple[str, ...], out_id: str, out_name: str, params: JoinParameters,
                    keep_inputs: bool = True, display_index: int | None = None) -> TransformationNode:
    if len(input_ids) < 2:
        raise JoinError("Mindestens zwei Spalten zum Gruppieren wählen.")
    if len(set(input_ids)) != len(input_ids):
        raise JoinError("Eine Spalte kann nur einmal in einer Gruppe stehen.")
    if not out_name.strip():
        raise JoinError("Der Name der Zielspalte ist leer.")
    return TransformationNode(node_id=node_id, operation="join", input_ids=tuple(input_ids), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip(), params.output_type.value, display_index),
                              keep_inputs=keep_inputs)
