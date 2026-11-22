"""Conservative, multi-stage column type detection (decision D9). Pure Python, no Qt.

Order of authority:
  1. app / database schema          -> detect_from_schema()
  2. native Excel cell type         -> detect_from_native()
  3. value sample (strings)         -> detect_from_sample()
detect_column() applies them in that order. Nothing in here converts data: detection only classifies.
"""
from __future__ import annotations

import datetime as _dt
import functools
import re
from typing import Iterable, Sequence

from .column_types import (ColumnType, DetectionOrigin, SchemaColumn, TypeDetection, TypeDetectionConfig)

DEFAULT_CONFIG = TypeDetectionConfig()

_INT_RE = re.compile(r"^[+-]?(0|[1-9]\d*)$")                    # leading zeros are NOT an integer (tag / code protection)
_DEC_RE = re.compile(r"^[+-]?(0|[1-9]\d*)\.\d+$")                # one decimal point only; "1.2.3" is a code, not a number
_BOOL_VALUES = {"true": True, "false": False}


# --------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------
def is_empty(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _share_ok(matching: int, total: int, threshold: float) -> bool:
    """matching / total >= threshold, computed in integers so that 190 of 200 is exactly 95 %."""
    return total > 0 and matching * 10000 >= round(threshold * 10000) * total


def has_text_name_hint(name: str, cfg: TypeDetectionConfig = DEFAULT_CONFIG) -> bool:
    """True if a column name indicates an identifier (Tag, Line number, P&ID, NPS ...). A hint only ever keeps a column
    at text; it never produces another type."""
    tokens = re.findall(r"[a-z0-9&]+", str(name or "").lower())
    hints = {re.sub(r"[^a-z0-9&]", "", h.lower()) for h in cfg.text_name_hints}
    return any(tok in hints or (tok.endswith("s") and tok[:-1] in hints) for tok in tokens)


def sample_values(values: Iterable[object], cfg: TypeDetectionConfig = DEFAULT_CONFIG) -> list[str]:
    """Deterministic sample: the first `preview_rows` rows, non-empty values only, at most `max_values_per_column` of them,
    spread evenly over the preview (not only the first values)."""
    rows = list(values)[: cfg.preview_rows]
    non_empty = [str(v).strip() for v in rows if not is_empty(v)]
    n, m = len(non_empty), cfg.max_values_per_column
    if n <= m:
        return non_empty
    return [non_empty[i * n // m] for i in range(m)]


@functools.lru_cache(maxsize=65536)                    # the same value is tried against every format, several times per column
def _parses(value: str, fmt: str) -> bool:
    if not any(c.isdigit() for c in value) and ("%d" in fmt or "%Y" in fmt or "%m" in fmt):
        return False                                                           # a numeric date format never matches text without digits
    try:
        return _dt.datetime.strptime(value, fmt).strftime(fmt) == value        # strict: "1.2.2026" is not "%d.%m.%Y"
    except ValueError:
        return False


def _is_int(v: str) -> bool:
    return bool(_INT_RE.match(v))


def _is_dec(v: str) -> bool:
    return bool(_INT_RE.match(v) or _DEC_RE.match(v))


# --------------------------------------------------------------------------------------------
# 1. app schema
# --------------------------------------------------------------------------------------------
def detect_from_schema(col: SchemaColumn) -> tuple[ColumnType, TypeDetection]:
    """Priority 1: the declared type is binding. A text column is never turned into a number."""
    if col.column_type == ColumnType.UNKNOWN:
        return ColumnType.UNKNOWN, TypeDetection(DetectionOrigin.NONE, 0.0)
    return col.column_type, TypeDetection(DetectionOrigin.APP_SCHEMA, 1.0)


# --------------------------------------------------------------------------------------------
# 2. native Excel types
# --------------------------------------------------------------------------------------------
def _native_type(v: object) -> ColumnType:
    if isinstance(v, bool):                                   # before int: bool is an int subclass
        return ColumnType.BOOLEAN
    if isinstance(v, int):
        return ColumnType.INTEGER
    if isinstance(v, float):
        return ColumnType.DECIMAL
    if isinstance(v, _dt.datetime):
        return ColumnType.DATE if v.time() == _dt.time(0) else ColumnType.DATETIME
    if isinstance(v, _dt.date):
        return ColumnType.DATE
    return ColumnType.TEXT                                    # Excel text (also "123" typed as text)


def detect_from_native(values: Iterable[object], cfg: TypeDetectionConfig = DEFAULT_CONFIG
                       ) -> tuple[ColumnType, TypeDetection]:
    """Priority 2: native cell types of the Excel reader (python objects). Number formats are not looked at."""
    kinds = [_native_type(v) for v in list(values)[: cfg.preview_rows] if not is_empty(v)]
    if len(kinds) > cfg.max_values_per_column:
        n, m = len(kinds), cfg.max_values_per_column
        kinds = [kinds[i * n // m] for i in range(m)]
    n = len(kinds)
    if n == 0:
        return ColumnType.UNKNOWN, TypeDetection(DetectionOrigin.NONE, 0.0)
    count = {k: kinds.count(k) for k in set(kinds)}
    numeric = count.get(ColumnType.INTEGER, 0) + count.get(ColumnType.DECIMAL, 0)
    if _share_ok(numeric, n, cfg.threshold):                  # integers and decimals count together; decimals win (lossless)
        chosen = ColumnType.DECIMAL if count.get(ColumnType.DECIMAL, 0) else ColumnType.INTEGER
        match = numeric
    else:
        chosen, match = max(((k, c) for k, c in count.items() if k not in (ColumnType.INTEGER, ColumnType.DECIMAL)),
                            key=lambda kc: kc[1], default=(ColumnType.MIXED, 0))
        if not _share_ok(match, n, cfg.threshold):
            chosen, match = ColumnType.MIXED, max(count.values())
    return chosen, TypeDetection(DetectionOrigin.EXCEL_NATIVE, match / n, sample_non_empty=n, matching_values=match,
                                 invalid_values=0)


# --------------------------------------------------------------------------------------------
# 3. value sample
# --------------------------------------------------------------------------------------------
def _date_family(sample: Sequence[str], formats: tuple[str, ...]) -> tuple[str | None, int]:
    best_fmt, best = None, 0
    for f in formats:
        c = sum(1 for v in sample if _parses(v, f))
        if c > best:
            best_fmt, best = f, c
    return best_fmt, best


def detect_from_sample(name: str, values: Iterable[object], cfg: TypeDetectionConfig = DEFAULT_CONFIG
                       ) -> tuple[ColumnType, TypeDetection]:
    """Priority 3: classify string values. Typed only if at least `cfg.threshold` of the non-empty sample matches one type,
    otherwise `mixed`. Identifier columns (name hint) and identifier-like values stay `text`."""
    sample = sample_values(values, cfg)
    n = len(sample)
    if n == 0:
        return ColumnType.UNKNOWN, TypeDetection(DetectionOrigin.NONE, 0.0)           # O1: completely empty column
    if has_text_name_hint(name, cfg):
        return ColumnType.TEXT, TypeDetection(DetectionOrigin.SAMPLE, 1.0, n, n)
    c_int = sum(1 for v in sample if _is_int(v))
    c_dec = sum(1 for v in sample if _is_dec(v))
    c_bool = sum(1 for v in sample if v.lower() in _BOOL_VALUES)
    _, c_date = _date_family(sample, cfg.date_formats)
    _, c_dt = _date_family(sample, cfg.datetime_formats)
    typed_any = sum(1 for v in sample if _is_dec(v) or v.lower() in _BOOL_VALUES
                    or any(_parses(v, f) for f in cfg.date_formats + cfg.datetime_formats))
    text_share = n - typed_any                                                       # values no typed candidate accepts
    if _share_ok(text_share, n, cfg.threshold):
        return ColumnType.TEXT, TypeDetection(DetectionOrigin.SAMPLE, text_share / n, n, text_share)
    candidates = [(ColumnType.INTEGER, c_int), (ColumnType.DECIMAL, c_dec), (ColumnType.BOOLEAN, c_bool),
                  (ColumnType.DATE, c_date), (ColumnType.DATETIME, c_dt)]
    if _share_ok(c_dec, n, cfg.threshold):                                           # integers count as decimal-compatible
        ctype = ColumnType.INTEGER if c_int == c_dec else ColumnType.DECIMAL        # any real decimal makes it decimal (lossless)
        return ctype, TypeDetection(DetectionOrigin.SAMPLE, c_dec / n, n, c_dec)
    for ctype, c in candidates[2:]:
        if _share_ok(c, n, cfg.threshold):
            return ctype, TypeDetection(DetectionOrigin.SAMPLE, c / n, n, c)
    best_type, best = ColumnType.UNKNOWN, 0
    for ctype, c in candidates:
        if c > best:                                                                 # first wins a tie (integer < decimal)
            best_type, best = ctype, c
    suggested = (best_type if n >= cfg.suggestion_min_samples and best_type != ColumnType.UNKNOWN
                 and best * 10000 >= round(cfg.suggestion_min_share * 10000) * n else None)
    return ColumnType.MIXED, TypeDetection(DetectionOrigin.SAMPLE, best / n, n, best, invalid_values=n - best if best else 0,
                                           suggested_type=suggested)


# --------------------------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------------------------
def detect_column(name: str, *, schema: SchemaColumn | None = None, native_values: Iterable[object] | None = None,
                  text_values: Iterable[object] | None = None, cfg: TypeDetectionConfig = DEFAULT_CONFIG
                  ) -> tuple[ColumnType, TypeDetection]:
    """Detect the type of one column; the first available source wins (schema, native Excel types, value sample)."""
    if schema is not None and schema.column_type != ColumnType.UNKNOWN:
        return detect_from_schema(schema)
    if native_values is not None:
        return detect_from_native(native_values, cfg)
    return detect_from_sample(name, text_values or (), cfg)
