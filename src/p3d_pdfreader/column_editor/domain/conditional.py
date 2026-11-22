"""Conditional column ("If ... then ..."): the first rule whose condition is true decides the value. Pure Python, no Qt.

Each rule looks at ONE column; the result is a fixed text or the value of another column. No scripts, no free formulas.
"""
from __future__ import annotations

from dataclasses import dataclass

from .transformation_node import OutputDefinition, TransformationNode
from .type_detection import is_empty

OPERATORS: tuple[tuple[str, str], ...] = (
    ("equals", "ist gleich"), ("not_equals", "ist nicht gleich"), ("contains", "enthält"), ("not_contains", "enthält nicht"),
    ("starts", "beginnt mit"), ("ends", "endet mit"), ("empty", "ist leer"), ("not_empty", "ist nicht leer"),
    ("gt", "ist größer als"), ("lt", "ist kleiner als"), ("in_list", "ist einer von (getrennt durch ;)"))
NO_VALUE_OPERATORS = ("empty", "not_empty")


class ConditionalError(Exception):
    """Readable reason why the rules cannot be used."""


@dataclass(frozen=True, slots=True)
class Rule:
    column: str                 # key of the column that is looked at
    operator: str
    value: str = ""
    result: str = ""            # fixed text ...
    result_column: str = ""     # ... or the value of this column (key); '' = use the text

    def to_dict(self) -> dict:
        return {"column": self.column, "operator": self.operator, "value": self.value, "result": self.result,
                "result_column": self.result_column}

    @staticmethod
    def from_dict(d: dict) -> "Rule":
        return Rule(str(d.get("column") or ""), str(d.get("operator") or "equals"), str(d.get("value") or ""),
                    str(d.get("result") or ""), str(d.get("result_column") or ""))


@dataclass(frozen=True, slots=True)
class ConditionalParameters:
    rules: tuple[Rule, ...] = ()
    else_value: str = ""
    else_column: str = ""
    ignore_case: bool = True
    output_key: str = ""

    def keys_used(self) -> list[str]:
        out: list[str] = []
        for r in self.rules:
            for k in (r.column, r.result_column):
                if k and k not in out:
                    out.append(k)
        if self.else_column and self.else_column not in out:
            out.append(self.else_column)
        return out

    def to_dict(self) -> dict:
        return {"rules": [r.to_dict() for r in self.rules], "else_value": self.else_value, "else_column": self.else_column,
                "ignore_case": self.ignore_case, "output_key": self.output_key}

    @staticmethod
    def from_dict(d: dict) -> "ConditionalParameters":
        return ConditionalParameters(tuple(Rule.from_dict(r) for r in d.get("rules") or () if isinstance(r, dict)),
                                     str(d.get("else_value") or ""), str(d.get("else_column") or ""),
                                     bool(d.get("ignore_case", True)), str(d.get("output_key") or ""))


def validate(p: ConditionalParameters) -> str:
    if not p.rules:
        return "Mindestens eine Regel hinzufügen."
    valid = {k for k, _ in OPERATORS}
    for i, r in enumerate(p.rules, 1):
        if not r.column:
            return f"Regel {i}: zu prüfende Spalte wählen."
        if r.operator not in valid:
            return f"Regel {i}: unbekannte Bedingung '{r.operator}'."
        if r.operator not in NO_VALUE_OPERATORS and r.value == "":
            return f"Regel {i}: Vergleichswert eingeben."
    return ""


def _num(text: str) -> float | None:
    try:
        return float(text.strip().replace(",", "."))
    except ValueError:
        return None


def test_value(cell: str, operator: str, value: str, ignore_case: bool = True) -> bool:
    c, v = cell.strip(), value.strip()
    if operator == "empty":
        return is_empty(cell)
    if operator == "not_empty":
        return not is_empty(cell)
    if operator in ("gt", "lt"):
        a, b = _num(c), _num(v)
        if a is not None and b is not None:
            return a > b if operator == "gt" else a < b
        a_t, b_t = (c.casefold(), v.casefold()) if ignore_case else (c, v)
        return a_t > b_t if operator == "gt" else a_t < b_t
    if ignore_case:
        c, v = c.casefold(), v.casefold()
    if operator == "equals":
        return c == v
    if operator == "not_equals":
        return c != v
    if operator == "contains":
        return v in c
    if operator == "not_contains":
        return v not in c
    if operator == "starts":
        return c.startswith(v)
    if operator == "ends":
        return c.endswith(v)
    if operator == "in_list":
        return c in [x.strip() for x in v.split(";")]
    return False


def compute(p: ConditionalParameters, get) -> list[str]:
    """`get(key)` returns the value list of a column. Result column over all rows."""
    cols = {k: [("" if v is None else str(v)) for v in get(k)] for k in p.keys_used()}
    n = max((len(v) for v in cols.values()), default=0)

    def cell(key: str, r: int) -> str:
        c = cols.get(key, [])
        return c[r] if r < len(c) else ""
    out = []
    for r in range(n):
        for rule in p.rules:
            if test_value(cell(rule.column, r), rule.operator, rule.value, p.ignore_case):
                out.append(cell(rule.result_column, r) if rule.result_column else rule.result)
                break
        else:
            out.append(cell(p.else_column, r) if p.else_column else p.else_value)
    return out


def describe(p: ConditionalParameters, label_of=lambda k: k) -> str:
    ops = dict(OPERATORS)
    parts = []
    for r in p.rules[:3]:
        cond = f"{label_of(r.column)} {ops.get(r.operator, r.operator)}" + ("" if r.operator in NO_VALUE_OPERATORS else f" '{r.value}'")
        parts.append(f"wenn {cond} dann " + (label_of(r.result_column) if r.result_column else f"'{r.result}'"))
    more = f" (+{len(p.rules) - 3} weitere)" if len(p.rules) > 3 else ""
    other = label_of(p.else_column) if p.else_column else f"'{p.else_value}'"
    return "Wenn-dann-Spalte: " + "; ".join(parts) + more + f"; sonst {other}"


def build_node(*, node_id: str, input_ids: tuple[str, ...], out_id: str, out_name: str, params: ConditionalParameters) -> TransformationNode:
    err = validate(params)
    if err:
        raise ConditionalError(err)
    if not out_name.strip():
        raise ConditionalError("Der Name der Zielspalte ist leer.")
    return TransformationNode(node_id=node_id, operation="conditional", input_ids=tuple(input_ids), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip(), "text"), keep_inputs=True)
