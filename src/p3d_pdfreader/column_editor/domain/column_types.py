"""Type system and detection result models (decision D9). Pure Python, no Qt."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ColumnType(str, Enum):
    TEXT = "text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    PERCENTAGE = "percentage"    # Power-Query-like types, only ever reached through an explicit convert node
    TIME = "time"
    DURATION = "duration"
    NULL = "null"          # part of the type system, not classified in Sprint 1 (O1: empty column -> UNKNOWN)
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DetectionOrigin(str, Enum):
    APP_SCHEMA = "app_schema"      # priority 1, authoritative
    EXCEL_NATIVE = "excel_native"  # priority 2
    SAMPLE = "sample"              # priority 3
    NONE = "none"                  # nothing detectable -> unknown


class OnInvalid(str, Enum):
    FLAG = "flag"                  # keep the original value, mark it invalid
    EMPTY = "empty"                # set empty
    EMPTY_FLAG = "empty_flag"      # set empty and mark (default)
    ABORT = "abort"                # cancel the operation


@dataclass(frozen=True, slots=True)
class TypeDetectionConfig:
    preview_rows: int = 500
    max_values_per_column: int = 200
    threshold: float = 0.95
    suggestion_min_share: float = 0.50        # O4
    suggestion_min_samples: int = 10          # O4: with fewer non-empty samples there is no recommendation
    # one clearly configured format family per kind (D9); ambiguous strings such as 01/02/2025 are never interpreted
    date_formats: tuple[str, ...] = ("%Y-%m-%d", "%d.%m.%Y")
    datetime_formats: tuple[str, ...] = ("%Y-%m-%d %H:%M:%S",)
    text_name_hints: tuple[str, ...] = ("tag", "line", "p&id", "pid", "number", "no.", "id",
                                        "code", "spec", "class", "size", "nps")


@dataclass(frozen=True, slots=True)
class SchemaColumn:
    """One column as reported by read_schema() of an app table (priority 1)."""
    name: str
    declared_type: str            # raw, e.g. "INTEGER", "REAL", "TEXT", "BOOLEAN", "datetime"
    column_type: ColumnType       # mapped through SCHEMA_TYPE_MAP


@dataclass(frozen=True, slots=True)
class TypeDetection:
    origin: DetectionOrigin
    confidence: float             # 1.0 for authoritative origins
    sample_non_empty: int = 0     # non-empty values examined (max 200)
    matching_values: int = 0
    invalid_values: int = 0       # non-empty values not matching suggested_type
    suggested_type: ColumnType | None = None   # MIXED only, and only with >= 10 non-empty samples (O4)
    override: bool = False        # True while a convert node sets output_type != source_type

    @property
    def authoritative(self) -> bool:
        return self.origin == DetectionOrigin.APP_SCHEMA

    def to_dict(self) -> dict:
        d: dict = {"origin": self.origin.value, "confidence": round(self.confidence, 4)}
        if self.origin == DetectionOrigin.SAMPLE:
            d.update(sample_non_empty=self.sample_non_empty, matching_values=self.matching_values)
            if self.invalid_values:
                d["invalid_values"] = self.invalid_values
            if self.suggested_type is not None:
                d["suggested_type"] = self.suggested_type.value
        d["override"] = self.override
        return d

    @staticmethod
    def from_dict(d: dict) -> "TypeDetection":
        try:
            origin = DetectionOrigin(str(d.get("origin") or "none"))
        except ValueError:
            origin = DetectionOrigin.NONE
        sug = d.get("suggested_type")
        try:
            suggested = ColumnType(str(sug)) if sug else None
        except ValueError:
            suggested = None
        return TypeDetection(origin=origin, confidence=float(d.get("confidence") or 0.0),
                             sample_non_empty=int(d.get("sample_non_empty") or 0),
                             matching_values=int(d.get("matching_values") or 0),
                             invalid_values=int(d.get("invalid_values") or 0),
                             suggested_type=suggested, override=bool(d.get("override", False)))

    def describe(self, detected: ColumnType) -> tuple[str, str, str]:
        """(type, source, confidence) texts for the inspector."""
        kind = detected.value.capitalize()
        if self.origin == DetectionOrigin.APP_SCHEMA:
            return kind, "Programm-Schema", "verbindlich"
        if self.origin == DetectionOrigin.EXCEL_NATIVE:
            return kind, "Excel-Zelltyp", f"{round(self.confidence * 100)} %"
        if self.origin == DetectionOrigin.SAMPLE:
            return (kind, f"Stichprobe, {self.matching_values} von {self.sample_non_empty} Werten",
                    f"{round(self.confidence * 100)} %")
        return kind, "nicht erkennbar", "keine"


# D9 mapping of declared app / database types
SCHEMA_TYPE_MAP: dict[str, ColumnType] = {
    "INTEGER": ColumnType.INTEGER, "INT": ColumnType.INTEGER, "BIGINT": ColumnType.INTEGER,
    "SMALLINT": ColumnType.INTEGER,
    "REAL": ColumnType.DECIMAL, "FLOAT": ColumnType.DECIMAL, "DOUBLE": ColumnType.DECIMAL,
    "NUMERIC": ColumnType.DECIMAL, "DECIMAL": ColumnType.DECIMAL,
    "TEXT": ColumnType.TEXT, "VARCHAR": ColumnType.TEXT, "CHAR": ColumnType.TEXT, "STRING": ColumnType.TEXT,
    "BOOLEAN": ColumnType.BOOLEAN, "BOOL": ColumnType.BOOLEAN,
    "DATE": ColumnType.DATE,
    "DATETIME": ColumnType.DATETIME, "TIMESTAMP": ColumnType.DATETIME,
    "TIME": ColumnType.TIME, "INTERVAL": ColumnType.DURATION,
}


def schema_column(name: str, declared_type: str) -> SchemaColumn:
    """Map a declared type to the D9 type system; an unknown declaration stays UNKNOWN (never guessed)."""
    base = str(declared_type or "").strip().upper().split("(")[0].strip()
    return SchemaColumn(name=name, declared_type=str(declared_type), column_type=SCHEMA_TYPE_MAP.get(base, ColumnType.UNKNOWN))
