"""One place that knows every node type that creates a calculated column (join, text_op, conditional, lookup, check_list, index, yes_no).
Pure Python, no Qt. The controller, the profile replay (`PreviewWidget._sync_derived`) and the steps panel all use it."""
from __future__ import annotations

from . import checks, conditional, indexcol, lookup, text_ops, yesno
from .join import JoinParameters, join_columns
from .transformation_node import TransformationNode

DERIVED_OPERATIONS = ("join", "text_op", "conditional", "lookup", "check_list", "index", "yes_no")


def is_derived(node: TransformationNode) -> bool:
    return node.operation in DERIVED_OPERATIONS and node.enabled


def params_of(node: TransformationNode):
    d = node.parameters
    return {"join": JoinParameters.from_dict, "text_op": text_ops.TextOpParameters.from_dict,
            "conditional": conditional.ConditionalParameters.from_dict, "lookup": lookup.LookupParameters.from_dict,
            "check_list": checks.CheckParameters.from_dict, "index": indexcol.IndexParameters.from_dict,
            "yes_no": yesno.YesNoParameters.from_dict}[node.operation](d)


def output_key(node: TransformationNode) -> str:
    return str(node.parameters.get("output_key") or "")


def input_keys(node: TransformationNode) -> list[str]:
    """Keys of the columns the node reads (not ids)."""
    if node.operation in ("index", "yes_no"):
        return []                                  # no input column
    p = params_of(node)
    if node.operation == "join":
        return list(p.input_names)
    if node.operation == "conditional":
        return p.keys_used()
    return [p.source_key] if p.source_key else []


def compute(node: TransformationNode, get) -> list[str]:
    """Values of the calculated column; `get(key)` returns the value list of an input column."""
    p = params_of(node)
    if node.operation == "index":
        return indexcol.compute(p, len(get("")))   # get("") = any column: only the row count is needed
    if node.operation == "yes_no":
        return yesno.compute(p, len(get("")))
    if node.operation == "join":
        return join_columns([get(k) for k in p.input_names], p)[0]
    if node.operation == "text_op":
        return text_ops.apply_column(get(p.source_key), p)
    if node.operation == "conditional":
        return conditional.compute(p, get)
    if node.operation == "lookup":
        return lookup.compute(p, get)
    return checks.compute(p, get)


def describe(node: TransformationNode, label_of=lambda k: k) -> str:
    p = params_of(node)
    if node.operation == "index":
        return indexcol.describe(p)
    if node.operation == "yes_no":
        return yesno.describe(p)
    if node.operation == "join":
        return "Gruppe " + " + ".join(label_of(k) for k in p.input_names)
    if node.operation == "text_op":
        return f"{text_ops.describe(p)} auf '{label_of(p.source_key)}'"
    if node.operation == "conditional":
        return conditional.describe(p, label_of)
    if node.operation == "lookup":
        return lookup.describe(p, label_of)
    return checks.describe(p, label_of)


def editable(node: TransformationNode) -> bool:
    """Steps whose settings can be changed afterwards in a dialog."""
    return node.operation in ("text_op", "conditional", "check_list")
