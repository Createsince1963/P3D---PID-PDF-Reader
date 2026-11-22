"""Text operations on ONE column (Power Query: Transform / Replace values / Format / Fill). Pure Python, no Qt.

Every operation turns one input column into one calculated column (node `text_op`); the source is never changed.
The same functions feed the live preview in the dialog, the calculated column and the export.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from .transformation_node import OutputDefinition, TransformationNode
from .type_detection import is_empty


class TextOpError(Exception):
    """Readable reason why an operation cannot be set up."""


# op id -> (label for CAD users, one-line help, suffix of the new column, needs a dialog)
OPS: dict[str, tuple[str, str, str, bool]] = {
    "trim": ("Überzählige Leerzeichen entfernen", "Entfernt Leerzeichen am Anfang und Ende sowie doppelte Leerzeichen im Text.", "trimmed", False),
    "clean": ("Versteckte Zeichen entfernen", "Entfernt Zeilenumbrüche, Tabulatoren und andere unsichtbare Zeichen.", "cleaned", False),
    "upper": ("GROSSBUCHSTABEN", "Macht jeden Buchstaben groß.", "upper", False),
    "lower": ("kleinbuchstaben", "Macht jeden Buchstaben klein.", "lower", False),
    "capitalise": ("Jedes Wort Groß", "Erster Buchstabe jedes Worts groß, der Rest klein.", "capitalised", False),
    "normalise_size": ("Rohrgröße vereinheitlichen", "Schreibt Größen wie 1 1/2, 1.5\", DN40 einheitlich, z. B. 1 1/2\".", "size", True),
    "replace": ("Werte ersetzen", "Ersetzt einen Text durch einen anderen (ganze Zelle oder Teil).", "replaced", True),
    "format": ("Text ergänzen / mit Nullen auffüllen", "Fügt Text vor / nach dem Wert an oder füllt mit Nullen auf, z. B. 4 -> 0004.", "formatted", True),
    "duplicate": ("Spalte duplizieren", "Legt eine genaue Kopie der Spalte an (die Kopie ändern, das Original behalten).", "copy", False),
    "fill_down": ("Wert nach unten in leere Zellen kopieren", "Leere Zellen erhalten den Wert der Zelle darüber.", "filled", False),
    "fill_up": ("Wert nach oben in leere Zellen kopieren", "Leere Zellen erhalten den Wert der Zelle darunter.", "filled", False),
    "fill_from": ("Diesen Wert ab hier nach unten kopieren", "Leere Zellen unter dieser Zeile erhalten diesen Wert, bis zur nächsten gefüllten Zelle.", "filled", False),
    "fill_value": ("Leere Zellen mit einem Wert füllen", "Jede leere Zelle erhält den eingegebenen Wert; gefüllte bleiben.", "filled", True),
    "split_part": ("In mehrere Spalten teilen", "Teilt einen Text wie 203-04-715 an einem Trennzeichen und behält einen Teil.", "part", True),
    "split_fixed": ("An festen Positionen teilen", "Teilt einen Text nach einer festen Anzahl Zeichen und behält ein Stück.", "part", True),
    "split_transition": ("Beim Wechsel der Zeichenart teilen", "Teilt einen Text, wo klein zu groß, Buchstabe zu Ziffer usw. wechselt, und behält ein Stück.", "part", False),
    "extract_first": ("Erste Zeichen", "Behält die ersten N Zeichen.", "first", True),
    "extract_last": ("Letzte Zeichen", "Behält die letzten N Zeichen.", "last", True),
    "extract_before": ("Text vor Trennzeichen", "Behält den Text vor dem ersten Trennzeichen.", "before", True),
    "extract_after": ("Text nach Trennzeichen", "Behält den Text nach dem ersten Trennzeichen.", "after", True),
    "extract_between": ("Text zwischen Trennzeichen", "Behält den Text zwischen zwei Trennzeichen.", "between", True),
}
# split at a change of character type (Power Query: "By lowercase to uppercase" ...): mode -> (label, cut between previous and next char)
TRANSITIONS: dict[str, tuple[str, object]] = {
    "lower_upper": ("klein zu GROSS", lambda a, b: a.islower() and b.isupper()),
    "upper_lower": ("GROSS zu klein", lambda a, b: a.isupper() and b.islower()),
    "digit_nondigit": ("Ziffer zu Nicht-Ziffer", lambda a, b: a.isdigit() and not b.isdigit()),
    "nondigit_digit": ("Nicht-Ziffer zu Ziffer", lambda a, b: not a.isdigit() and b.isdigit()),
}
EXTRACT_OPS = ("extract_first", "extract_last", "extract_before", "extract_after", "extract_between")
FILL_OPS = ("fill_down", "fill_up", "fill_from", "fill_value")

# nominal pipe size DN -> inch (as written in the project: whole inches or a fraction, inch mark kept)
DN_TO_INCH: dict[int, str] = {6: "1/4", 8: "1/4", 10: "3/8", 15: "1/2", 20: "3/4", 25: "1", 32: "1 1/4", 40: "1 1/2", 50: "2", 65: "2 1/2",
                              80: "3", 90: "3 1/2", 100: "4", 125: "5", 150: "6", 200: "8", 250: "10", 300: "12", 350: "14", 400: "16",
                              450: "18", 500: "20", 600: "24"}

_HIDDEN = re.compile(r"[\x00-\x1f\x7f ​‌‍﻿]")


@dataclass(frozen=True, slots=True)
class TextOpParameters:
    op: str
    find: str = ""
    replace_with: str = ""            # replace: the new text - fill_value: the value for every empty cell
    whole_cell: bool = False          # replace: the cell must equal `find` (else: every occurrence inside the text)
    match_case: bool = False
    prefix: str = ""
    suffix: str = ""
    pad_width: int = 0                # 0 = no zero fill
    pad_char: str = "0"
    bare_numbers: str = "inch"        # normalise_size: a plain number is "inch" or "dn"
    output_key: str = ""              # key of the calculated column
    source_key: str = ""              # key of the input column (rebuild on another data set)
    replaced_original: bool = False   # the original was hidden / left out of the export when the node was applied
    number: int = 0                   # split_part: part number (1-based) - split_fixed: length - extract_first / last: N
    start: int = 0                    # split_fixed: first character (1-based)
    find2: str = ""                   # extract_between: closing separator
    start_row: int = 0                # fill_from: index of the row whose value is copied down (0-based, source order)
    part_label: str = ""              # split: suffix of the new column name, e.g. 'part 2'

    def to_dict(self) -> dict:
        return {"op": self.op, "find": self.find, "replace_with": self.replace_with, "whole_cell": self.whole_cell,
                "match_case": self.match_case, "prefix": self.prefix, "suffix": self.suffix, "pad_width": self.pad_width,
                "pad_char": self.pad_char, "bare_numbers": self.bare_numbers, "output_key": self.output_key,
                "source_key": self.source_key, "replaced_original": self.replaced_original, "number": self.number,
                "start": self.start, "find2": self.find2, "start_row": self.start_row, "part_label": self.part_label}

    @staticmethod
    def from_dict(d: dict) -> "TextOpParameters":
        def num(k: str) -> int:
            try:
                return max(0, int(d.get(k) or 0))
            except (TypeError, ValueError):
                return 0
        return TextOpParameters(op=str(d.get("op") or ""), find=str(d.get("find") or ""), replace_with=str(d.get("replace_with") or ""),
                                whole_cell=bool(d.get("whole_cell", False)), match_case=bool(d.get("match_case", False)),
                                prefix=str(d.get("prefix") or ""), suffix=str(d.get("suffix") or ""), pad_width=num("pad_width"),
                                pad_char=(str(d.get("pad_char") or "0"))[:1] or "0",
                                bare_numbers="dn" if str(d.get("bare_numbers")) == "dn" else "inch",
                                output_key=str(d.get("output_key") or ""), source_key=str(d.get("source_key") or ""),
                                replaced_original=bool(d.get("replaced_original", False)), number=num("number"),
                                start=num("start"), find2=str(d.get("find2") or ""), start_row=num("start_row"),
                                part_label=str(d.get("part_label") or ""))


def validate(p: TextOpParameters) -> str:
    """'' when the parameters are usable, else a readable message."""
    if p.op not in OPS:
        return f"Unbekannte Funktion '{p.op}'."
    if p.op == "replace" and p.find == "":
        return "Gesuchten Text eingeben."
    if p.op == "fill_value" and p.replace_with.strip() == "":
        return "Wert für die leeren Zellen eingeben."
    if p.op == "format" and not (p.prefix or p.suffix or p.pad_width):
        return "Text für vorne oder hinten oder eine Stellenzahl zum Auffüllen mit Nullen eingeben."
    if p.op == "split_part" and (p.find == "" or p.number < 1):
        return "Trennzeichen und Teilnummer eingeben (1 = erster Teil)."
    if p.op == "split_fixed" and (p.start < 1 or p.number < 1):
        return "Erstes Zeichen (1 = erstes) und Anzahl Zeichen eingeben."
    if p.op == "split_transition" and (p.find not in TRANSITIONS or p.number < 1):
        return "Wechsel der Zeichenart und Teilnummer wählen (1 = erster Teil)."
    if p.op in ("extract_first", "extract_last") and p.number < 1:
        return "Anzahl der zu behaltenden Zeichen eingeben."
    if p.op in ("extract_before", "extract_after", "extract_between") and p.find == "":
        return "Trennzeichen eingeben."
    if p.op == "extract_between" and p.find2 == "":
        return "Schließendes Trennzeichen eingeben."
    return ""


# --------------------------------------------------------------------------------------------
# pipe size
# --------------------------------------------------------------------------------------------
def _fraction_text(value: Fraction) -> str | None:
    """1.5 -> '1 1/2', 0.5 -> '1/2', 4 -> '4'. Only fractions with a denominator up to 16 are accepted."""
    if value <= 0:
        return None
    if value.denominator > 16:
        return None
    whole, rest = divmod(value.numerator, value.denominator)
    if rest == 0:
        return str(whole)
    frac = f"{rest}/{value.denominator}"
    return f"{whole} {frac}" if whole else frac


def normalise_size(text: str, bare_numbers: str = "inch") -> str | None:
    """'1 1/2', '1.5"', '1-1/2"', 'DN40', 'DN 40', 'NPS 2', '40' -> '1 1/2"'. None = not recognised."""
    t = text.strip().replace("''", '"').replace("”", '"').replace("″", '"')
    if not t:
        return None
    m = re.fullmatch(r"(?:DN|NB)\s*[-]?\s*(\d+)", t, re.I)
    if m:
        inch = DN_TO_INCH.get(int(m.group(1)))
        return f'{inch}"' if inch else None
    m = re.fullmatch(r"(?:NPS|IPS)\s*(.+)", t, re.I)
    if m:
        t = m.group(1).strip()
        bare_numbers = "inch"
    t = re.sub(r'\s*("|in\.?|inch(es)?)$', "", t, flags=re.I).strip()
    explicit_inch = t != text.strip().rstrip()
    t = t.replace(",", ".")
    try:
        m = re.fullmatch(r"(\d+)[\s-]+(\d+)/(\d+)", t)
        if m:
            value = Fraction(int(m.group(1))) + Fraction(int(m.group(2)), int(m.group(3)))
        elif re.fullmatch(r"\d+/\d+", t):
            a, b = t.split("/")
            value = Fraction(int(a), int(b))
        elif re.fullmatch(r"\d+(\.\d+)?", t):
            if bare_numbers == "dn" and "." not in t and not explicit_inch:
                inch = DN_TO_INCH.get(int(t))
                return f'{inch}"' if inch else None
            value = Fraction(t)
        else:
            return None
    except ZeroDivisionError:
        return None
    out = _fraction_text(value)
    return f'{out}"' if out else None


# --------------------------------------------------------------------------------------------
# one value / one column
# --------------------------------------------------------------------------------------------
def _cell(value: object) -> str:
    return "" if value is None else str(value)


def apply_value(value: object, p: TextOpParameters) -> str:
    """Result for ONE cell (fill operations need the neighbours, see apply_column)."""
    text = _cell(value)
    op = p.op
    if op == "trim":
        return re.sub(r"\s{2,}", " ", text.strip())
    if op == "clean":
        return _HIDDEN.sub("", text).strip()
    if op == "upper":
        return text.upper()
    if op == "lower":
        return text.lower()
    if op == "capitalise":
        return re.sub(r"[^\W_]+", lambda m: m.group(0)[:1].upper() + m.group(0)[1:].lower(), text)
    if op == "normalise_size":
        res = normalise_size(text, p.bare_numbers) if text.strip() else None
        return res if res is not None else text
    if op == "replace":
        if not p.find:
            return text
        if p.whole_cell:
            same = text.strip() == p.find if p.match_case else text.strip().lower() == p.find.lower()
            return p.replace_with if same else text
        return re.sub(re.escape(p.find), lambda _m: p.replace_with, text, flags=0 if p.match_case else re.I)
    if op == "split_part":
        parts = text.split(p.find)
        return parts[p.number - 1].strip() if p.number <= len(parts) else ""
    if op == "split_fixed":
        return text[p.start - 1:p.start - 1 + p.number].strip()
    if op == "split_transition":
        parts = split_at_transitions(text, p.find)
        return parts[p.number - 1].strip() if p.number <= len(parts) else ""
    if op == "extract_first":
        return text[:p.number]
    if op == "extract_last":
        return text[-p.number:] if text else ""
    if op == "extract_before":
        return text.split(p.find, 1)[0].strip() if p.find in text else ""
    if op == "extract_after":
        return text.split(p.find, 1)[1].strip() if p.find in text else ""
    if op == "extract_between":
        if p.find not in text:
            return ""
        rest = text.split(p.find, 1)[1]
        return rest.split(p.find2, 1)[0].strip() if p.find2 in rest else ""
    if op == "fill_value":
        return p.replace_with if is_empty(text) else text
    if op == "format":
        if text == "":
            return text                                     # empty cells stay empty (no stray prefix / suffix)
        core = text.rjust(p.pad_width, p.pad_char) if p.pad_width else text
        return f"{p.prefix}{core}{p.suffix}"
    return text


def apply_column(values, p: TextOpParameters) -> list[str]:
    """Result column over all rows."""
    if p.op == "fill_from":
        src = [_cell(v) for v in values]
        out = list(src)
        if not 0 <= p.start_row < len(src) or is_empty(src[p.start_row]):
            return out
        for i in range(p.start_row + 1, len(src)):
            if not is_empty(src[i]):
                break
            out[i] = src[p.start_row]
        return out
    if p.op in ("fill_down", "fill_up"):
        src = [_cell(v) for v in values]
        order = range(len(src)) if p.op == "fill_down" else range(len(src) - 1, -1, -1)
        out, last = list(src), ""
        for i in order:
            if is_empty(src[i]):
                out[i] = last
            else:
                last = src[i]
        return out
    return [apply_value(v, p) for v in values]


def changed_count(before, after) -> int:
    return sum(1 for a, b in zip(before, after) if _cell(a) != b)


def unrecognised_count(values, p: TextOpParameters) -> int:
    """normalise_size: filled cells that are not a size (they stay as they are)."""
    if p.op != "normalise_size":
        return 0
    return sum(1 for v in values if not is_empty(v) and normalise_size(_cell(v), p.bare_numbers) is None)


def preview(values, p: TextOpParameters, limit: int = 5) -> dict:
    """What the dialog shows: first `limit` cells that change (before -> after), counts, hint."""
    err = validate(p)
    if err:
        return {"ok": False, "error": err, "rows": [], "changed": 0, "total": 0, "unrecognised": 0}
    values = list(values)
    after = apply_column(values, p)
    rows = []
    for b, a in zip(values, after):
        if _cell(b) != a:
            rows.append({"before": _cell(b), "after": a})
            if len(rows) >= limit:
                break
    return {"ok": True, "error": "", "rows": rows, "changed": changed_count(values, after), "total": len(values),
            "unrecognised": unrecognised_count(values, p)}


def describe(p: TextOpParameters) -> str:
    """One line for the steps panel."""
    label = OPS.get(p.op, (p.op,))[0]
    if p.op == "replace":
        return f"{label}: '{p.find}' -> '{p.replace_with}'" + (" (ganze Zelle)" if p.whole_cell else "")
    if p.op == "split_part":
        return f"{label}: Teil {p.number} an '{p.find}'"
    if p.op == "split_fixed":
        return f"{label}: {p.number} Zeichen ab {p.start}"
    if p.op == "split_transition":
        return f"{label}: Teil {p.number}, {TRANSITIONS.get(p.find, (p.find,))[0]}"
    if p.op in ("extract_first", "extract_last"):
        return f"{label}: {p.number}"
    if p.op in ("extract_before", "extract_after"):
        return f"{label} '{p.find}'"
    if p.op == "extract_between":
        return f"{label} '{p.find}' ... '{p.find2}'"
    if p.op == "fill_from":
        return f"{label} (Zeile {p.start_row + 1})"
    if p.op == "fill_value":
        return f"{label}: '{p.replace_with}'"
    if p.op == "format":
        bits = [f"vorne '{p.prefix}'" if p.prefix else "", f"hinten '{p.suffix}'" if p.suffix else "",
                f"{p.pad_width} Stellen" if p.pad_width else ""]
        return f"{label}: " + ", ".join(b for b in bits if b)
    if p.op == "normalise_size":
        return f"{label} (reine Zahlen = {'DN' if p.bare_numbers == 'dn' else 'Zoll'})"
    return label


def new_column_name(source_label: str, p: TextOpParameters) -> str:
    return f"{source_label} ({p.part_label or OPS[p.op][2]})"


def split_parts(values, delimiter: str, limit: int = 12) -> int:
    """How many parts the biggest of the (sampled) values has when cut at `delimiter` (at least 1, at most `limit`)."""
    n = max((len(_cell(v).split(delimiter)) for v in values if not is_empty(v)), default=1) if delimiter else 1
    return max(1, min(limit, n))


def split_at_transitions(text: str, mode: str) -> list[str]:
    """'AB12cd' by 'digit_nondigit' -> ['AB12', 'cd']. Unknown mode or empty text: the whole text as one piece."""
    cut = TRANSITIONS.get(mode, (None, None))[1]
    if cut is None or not text:
        return [text]
    out, start = [], 0
    for i in range(1, len(text)):
        if cut(text[i - 1], text[i]):
            out.append(text[start:i])
            start = i
    out.append(text[start:])
    return out


def transition_parts(values, mode: str, limit: int = 24) -> int:
    """How many pieces the biggest of the (sampled) values has when cut at `mode` (at least 1, at most `limit`)."""
    n = max((len(split_at_transitions(_cell(v), mode)) for v in values if not is_empty(v)), default=1)
    return max(1, min(limit, n))


def build_text_node(*, node_id: str, input_id: str, out_id: str, out_name: str, params: TextOpParameters,
                    display_index: int | None = None) -> TransformationNode:
    err = validate(params)
    if err:
        raise TextOpError(err)
    if not out_name.strip():
        raise TextOpError("Der Name der Zielspalte ist leer.")
    return TransformationNode(node_id=node_id, operation="text_op", input_ids=(input_id,), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name.strip(), "text", display_index), keep_inputs=True)
