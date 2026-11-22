"""Index column: a running number as a calculated column (first column of the table). Pure Python, no Qt.

start / step are chosen by the user (default 1 / 1; e.g. start 10, step 10 -> 10, 20, 30 ...). The node has no input column, so it
is recreated with the row count of whatever data the saved view is loaded on.
"""
from __future__ import annotations

from dataclasses import dataclass

from .transformation_node import OutputDefinition, TransformationNode

DEFAULT_NAME = "Pos."


@dataclass(frozen=True, slots=True)
class IndexParameters:
    start: int = 1
    step: int = 1
    output_key: str = ""
    digits: int = 1                   # minimum number of digits, filled with leading zeros (4 -> 0001); 0 = automatic (as many as the last number needs)

    def to_dict(self) -> dict:
        return {"start": self.start, "step": self.step, "output_key": self.output_key, "digits": self.digits}

    @staticmethod
    def from_dict(d: dict) -> "IndexParameters":
        return IndexParameters(int(d.get("start", 1)), int(d.get("step", 1)), str(d.get("output_key") or ""), max(0, int(d.get("digits", 1))))


def validate(p: IndexParameters) -> str:
    if p.step == 0:
        return "Die Schrittweite darf nicht 0 sein."
    return ""


def compute(p: IndexParameters, rows: int) -> list[str]:
    if rows <= 0:
        return []
    width = p.digits
    if width == 0:                                  # automatic: 1000 rows -> 0001 ... 1000, 10 rows -> 01 ... 10
        width = max(len(str(p.start)), len(str(p.start + (rows - 1) * p.step)))
    return [f"{p.start + i * p.step:0{width}d}" if width > 1 else str(p.start + i * p.step) for i in range(rows)]


def describe(p: IndexParameters) -> str:
    return f"Indexspalte: Start {p.start}, Schritt {p.step}, " + ("Stellen automatisch" if p.digits == 0 else f"{p.digits} Stellen")


def build_node(*, node_id: str, out_id: str, out_name: str, params: IndexParameters) -> TransformationNode:
    return TransformationNode(node_id=node_id, operation="index", input_ids=(), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip() or DEFAULT_NAME, "text"), keep_inputs=True)
