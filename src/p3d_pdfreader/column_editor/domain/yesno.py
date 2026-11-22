"""Yes / No column (logical field): a new calculated column whose cells hold one of two words. Pure Python, no Qt.

The user picks the pair of words (Yes / No, Ja / Nein, True / False, 1 / 0, X / empty ...) and the value every row starts with
(the "yes" word, the "no" word, or empty). The node has no input column, so - like the index column - it is recreated with the
row count of whatever data the saved view is loaded on.
"""
from __future__ import annotations

from dataclasses import dataclass

from .transformation_node import OutputDefinition, TransformationNode

DEFAULT_NAME = "Ja / Nein"
DEFAULTS = ("yes", "no", "")          # value every row starts with: the yes word, the no word, empty
# ready-made word pairs for the dialog (yes word, no word)
PAIRS: tuple[tuple[str, str], ...] = (("Ja", "Nein"), ("Yes", "No"), ("True", "False"), ("1", "0"), ("X", ""), ("Y", "N"))


@dataclass(frozen=True, slots=True)
class YesNoParameters:
    yes_text: str = "Yes"
    no_text: str = "No"
    default: str = "no"               # one of DEFAULTS
    output_key: str = ""

    def to_dict(self) -> dict:
        return {"yes_text": self.yes_text, "no_text": self.no_text, "default": self.default, "output_key": self.output_key}

    @staticmethod
    def from_dict(d: dict) -> "YesNoParameters":
        default = str(d.get("default") if d.get("default") is not None else "no")
        return YesNoParameters(str(d.get("yes_text") if d.get("yes_text") is not None else "Yes"),
                               str(d.get("no_text") if d.get("no_text") is not None else "No"),
                               default if default in DEFAULTS else "no", str(d.get("output_key") or ""))

    @property
    def start_value(self) -> str:
        return self.yes_text if self.default == "yes" else self.no_text if self.default == "no" else ""


def validate(p: YesNoParameters) -> str:
    if p.yes_text.strip() == "":
        return "Wort für „ja“ eingeben."
    if p.yes_text.strip() == p.no_text.strip():
        return "Die Wörter für „ja“ und „nein“ müssen verschieden sein."
    if p.default not in DEFAULTS:
        return "Startwert der Zeilen wählen."
    return ""


def compute(p: YesNoParameters, rows: int) -> list[str]:
    return [p.start_value] * max(0, rows)


def describe(p: YesNoParameters) -> str:
    start = {"yes": f"'{p.yes_text}'", "no": f"'{p.no_text}'", "": "leer"}[p.default]
    return f"Ja/Nein-Spalte: '{p.yes_text}' / '{p.no_text}', jede Zeile beginnt mit {start}"


def build_node(*, node_id: str, out_id: str, out_name: str, params: YesNoParameters) -> TransformationNode:
    return TransformationNode(node_id=node_id, operation="yes_no", input_ids=(), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip() or DEFAULT_NAME, "text"), keep_inputs=True)
