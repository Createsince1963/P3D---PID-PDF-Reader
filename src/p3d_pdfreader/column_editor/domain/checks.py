"""Check against a code list (Plant 3D): marks values that are not in the project's list (Building, System, Fluid, Pipe class ...).
Pure Python, no Qt. The list is stored with the step, so a saved view checks the same list when it is loaded again."""
from __future__ import annotations

from dataclasses import dataclass

from .transformation_node import OutputDefinition, TransformationNode
from .type_detection import is_empty


class CheckError(Exception):
    """Readable reason why the check cannot be set up."""


@dataclass(frozen=True, slots=True)
class CheckParameters:
    values: tuple[str, ...] = ()
    list_name: str = ""             # where the list came from, e.g. 'Building codes (project definitions)'
    ignore_case: bool = True
    empty_ok: bool = True           # an empty cell is not an error
    ok_text: str = "OK"
    bad_text: str = "NICHT IN LISTE"
    source_key: str = ""
    output_key: str = ""

    def to_dict(self) -> dict:
        return {"values": list(self.values), "list_name": self.list_name, "ignore_case": self.ignore_case,
                "empty_ok": self.empty_ok, "ok_text": self.ok_text, "bad_text": self.bad_text, "source_key": self.source_key,
                "output_key": self.output_key}

    @staticmethod
    def from_dict(d: dict) -> "CheckParameters":
        return CheckParameters(tuple(str(v) for v in d.get("values") or ()), str(d.get("list_name") or ""),
                               bool(d.get("ignore_case", True)), bool(d.get("empty_ok", True)), str(d.get("ok_text") or "OK"),
                               str(d.get("bad_text") or "NICHT IN LISTE"), str(d.get("source_key") or ""), str(d.get("output_key") or ""))


def validate(p: CheckParameters) -> str:
    if not p.values:
        return "Die Codeliste ist leer."
    if not p.source_key:
        return "Keine Spalte zum Prüfen."
    return ""


def compute(p: CheckParameters, get) -> list[str]:
    fold = (lambda s: s.strip().casefold()) if p.ignore_case else (lambda s: s.strip())
    allowed = {fold(v) for v in p.values}
    out = []
    for v in get(p.source_key):
        text = "" if v is None else str(v)
        if is_empty(text):
            out.append(p.ok_text if p.empty_ok else p.bad_text)
        else:
            out.append(p.ok_text if fold(text) in allowed else p.bad_text)
    return out


def count_bad(p: CheckParameters, values) -> int:
    return sum(1 for r in compute(p, lambda _k: values) if r == p.bad_text)


def describe(p: CheckParameters, label_of=lambda k: k) -> str:
    return f"'{label_of(p.source_key)}' gegen {p.list_name or 'Codeliste'} prüfen ({len(p.values):,} Codes)"


def build_node(*, node_id: str, input_id: str, out_id: str, out_name: str, params: CheckParameters) -> TransformationNode:
    err = validate(params)
    if err:
        raise CheckError(err)
    return TransformationNode(node_id=node_id, operation="check_list", input_ids=(input_id,), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip() or "Prüfung", "text"), keep_inputs=True)
