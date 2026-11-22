"""The `convert` node: the only way to change the type of a column (decisions D9, O3). Pure Python, no Qt.

There is no silent conversion anywhere: a changed output type exists only as an explicit convert node.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass

from .column_types import ColumnType, OnInvalid, TypeDetectionConfig
from .transformation_node import OutputDefinition, TransformationNode
from .type_detection import DEFAULT_CONFIG, _date_family, _parses, is_empty, sample_values


class ConvertError(Exception):
    """Readable reason why a conversion cannot be set up (shown to the user, no node is created)."""


@dataclass(frozen=True, slots=True)
class ConvertParameters:
    from_type: ColumnType
    to_type: ColumnType
    decimal_separator: str = "."
    thousands_separator: str = ","
    on_invalid: OnInvalid = OnInvalid.EMPTY_FLAG
    date_format: str | None = None            # O3: needed for text -> date/datetime unless the format family is unambiguous

    def to_dict(self) -> dict:
        d = {"from": self.from_type.value, "to": self.to_type.value, "decimal_separator": self.decimal_separator,
             "thousands_separator": self.thousands_separator, "on_invalid": self.on_invalid.value}
        if self.date_format:
            d["date_format"] = self.date_format
        return d

    @staticmethod
    def from_dict(d: dict) -> "ConvertParameters":
        return ConvertParameters(ColumnType(str(d["from"])), ColumnType(str(d["to"])),
                                 str(d.get("decimal_separator") or "."), str(d.get("thousands_separator") or ","),
                                 OnInvalid(str(d.get("on_invalid") or "empty_flag")), d.get("date_format") or None)


def resolve_date_format(values, kind: ColumnType, cfg: TypeDetectionConfig = DEFAULT_CONFIG) -> str:
    """The one configured format family that all parseable values of a text column belong to (O3).
    Raises ConvertError when the values are ambiguous (several families, or none)."""
    formats = cfg.datetime_formats if kind == ColumnType.DATETIME else cfg.date_formats
    sample = sample_values(values, cfg)
    fmt, best = _date_family(sample, formats)
    if fmt is None or best == 0:
        raise ConvertError("Aus den Werten ließ sich kein Datumsformat bestimmen. Datumsformat ausdrücklich angeben.")
    others = sum(1 for f in formats if f != fmt and any(_parses(v, f) for v in sample))
    if others or best * 10000 < round(cfg.threshold * 10000) * len(sample):
        raise ConvertError("Die Werte nutzen mehrere Datumsformate oder sind mehrdeutig. Datumsformat ausdrücklich angeben.")
    return fmt


def build_convert_node(*, node_id: str, column_id: str, column_name: str, from_type: ColumnType, to_type: ColumnType,
                       out_id: str, out_name: str | None = None, on_invalid: OnInvalid = OnInvalid.EMPTY_FLAG,
                       decimal_separator: str = ".", thousands_separator: str = ",", date_format: str | None = None,
                       text_values=None, cfg: TypeDetectionConfig = DEFAULT_CONFIG,
                       display_index: int | None = None) -> TransformationNode | None:
    """Create the convert node for an output-type override. Returns None when nothing changes (same type).
    Raises ConvertError for conversions that need a format and have none (O3)."""
    if from_type == to_type:
        return None
    if to_type in (ColumnType.UNKNOWN, ColumnType.NULL):
        raise ConvertError(f"Eine Spalte kann nicht in '{to_type.value}' umgewandelt werden.")
    if on_invalid == OnInvalid.ABORT:
        raise ConvertError("Umwandlung abgebrochen.")
    fmt = date_format
    if to_type == ColumnType.MIXED:
        fmt = None                                                 # Mixed keeps every value as it is
    if to_type in (ColumnType.DATE, ColumnType.DATETIME) and from_type == ColumnType.TEXT and not fmt:
        fmt = resolve_date_format(text_values or (), to_type, cfg)
    params = ConvertParameters(from_type, to_type, decimal_separator, thousands_separator, on_invalid, fmt)
    return TransformationNode(node_id=node_id, operation="convert", input_ids=(column_id,), parameters=params.to_dict(),
                              output=OutputDefinition(out_id, out_name or column_name, to_type.value, display_index))


# --------------------------------------------------------------------------------------------
# executing a conversion on one value (preview and export use the same function)
# --------------------------------------------------------------------------------------------
TIME_FORMATS = ("%H:%M:%S", "%H:%M")
_DURATION = re.compile(r"([+-]?)(\d+):([0-5]\d)(?::([0-5]\d))?")


def convert_value(value: object, p: ConvertParameters) -> tuple[object, bool]:
    """Convert one value. Returns (result, valid). Empty values stay empty and are valid.
    On an invalid value the result follows `on_invalid`: FLAG keeps the original, EMPTY / EMPTY_FLAG give ''."""
    if is_empty(value):
        return "", True
    text = str(value).strip()
    try:
        if p.to_type == ColumnType.MIXED:
            return value, True
        if p.to_type in (ColumnType.INTEGER, ColumnType.DECIMAL, ColumnType.PERCENTAGE):
            percent = p.to_type == ColumnType.PERCENTAGE
            if percent and text.endswith("%"):
                text = text[:-1].strip()
            if p.thousands_separator:
                text = text.replace(p.thousands_separator, "")
            if p.decimal_separator and p.decimal_separator != ".":
                text = text.replace(p.decimal_separator, ".")
            if not re.fullmatch(r"[+-]?\d+(\.\d+)?", text):
                raise ValueError(text)
            num = float(text)
            if percent:
                return num / 100.0, True                       # "12.5 %" and "12.5" both mean 12.5 percent = 0.125
            if p.to_type == ColumnType.INTEGER:
                if num != int(num):
                    raise ValueError(text)
                return int(num), True
            return num, True
        if p.to_type == ColumnType.BOOLEAN:
            low = text.lower()
            if low in ("true", "false"):
                return low == "true", True
            raise ValueError(text)
        if p.to_type in (ColumnType.DATE, ColumnType.DATETIME):
            if not p.date_format:
                raise ValueError("no date format")
            parsed = _dt.datetime.strptime(text, p.date_format)
            return (parsed.date() if p.to_type == ColumnType.DATE else parsed), True
        if p.to_type == ColumnType.TIME:
            for fmt in ((p.date_format,) if p.date_format else TIME_FORMATS):
                try:
                    return _dt.datetime.strptime(text, fmt).time(), True
                except ValueError:
                    continue
            raise ValueError(text)
        if p.to_type == ColumnType.DURATION:
            m = _DURATION.fullmatch(text)
            if not m:
                raise ValueError(text)
            td = _dt.timedelta(hours=int(m.group(2)), minutes=int(m.group(3)), seconds=int(m.group(4) or 0))
            return (-td if m.group(1) == "-" else td), True
        if p.to_type == ColumnType.TEXT:
            return text, True
    except ValueError:
        pass
    return ("" if p.on_invalid in (OnInvalid.EMPTY, OnInvalid.EMPTY_FLAG) else value), False


def display_value(value: object, to_type: ColumnType) -> str:
    """Readable text of a converted value (preview dialog, derived columns)."""
    if value is None or value == "":
        return ""
    if to_type == ColumnType.PERCENTAGE and isinstance(value, float):
        return f"{value * 100:g} %"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, _dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, _dt.date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, _dt.time):
        return value.strftime("%H:%M:%S")
    if isinstance(value, _dt.timedelta):
        secs = int(value.total_seconds())
        sign, secs = ("-", -secs) if secs < 0 else ("", secs)
        return f"{sign}{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}"
    return str(value)


def preview_convert(values, p: ConvertParameters, limit: int = 6) -> list[dict]:
    """First `limit` non-empty values with their result (for the 'Change column type' dialog)."""
    out: list[dict] = []
    for v in values:
        if is_empty(v):
            continue
        res, ok = convert_value(v, p)
        out.append({"source": str(v), "result": display_value(res, p.to_type), "valid": ok})
        if len(out) >= limit:
            break
    return out
