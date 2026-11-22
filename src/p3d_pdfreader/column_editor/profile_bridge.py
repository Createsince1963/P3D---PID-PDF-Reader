"""Column types and convert nodes <-> ViewProfile (schema 2, decision D8). Pure Python, no Qt.

The tile editor does not have a profile store of its own: it writes into / reads from the existing ViewProfile.
"""
from __future__ import annotations

from .domain.column_config import ColumnConfig, ColumnDefinition
from .domain.column_types import ColumnType, TypeDetection
from .domain.transformation_node import TransformationNode


def export_into(config: ColumnConfig, profile) -> None:
    """Write types and convert nodes of `config` into the column settings / nodes of `profile` (a ViewProfile)."""
    by_key = {c.source_name: c for c in config.columns}
    for cs in profile.columns:
        d = by_key.get(cs.key)
        if d is None:
            continue
        cs.source_type, cs.detected_type, cs.output_type = d.source_type.value, d.detected_type.value, d.output_type.value
        cs.type_detection = d.type_detection.to_dict() if d.type_detection else None
        cs.export, cs.short_name = d.include_in_export, d.short_name
    profile.nodes = [n.to_dict() for n in config.nodes]
    profile.bands = [dict(b) for b in config.bands]


def import_from(config: ColumnConfig, profile) -> list[str]:
    """Take saved types / nodes over into `config` (whose definitions were just detected from the current data).
    Returns readable mismatch messages; a changed source is never remapped silently."""
    notes: list[str] = []
    by_key = {c.source_name: c for c in config.columns}
    for cs in profile.columns:
        d: ColumnDefinition | None = by_key.get(cs.key)
        if d is None or not cs.detected_type:
            continue
        try:
            saved_detected, saved_output = ColumnType(cs.detected_type), ColumnType(cs.output_type or cs.detected_type)
        except ValueError:
            notes.append(f"Column '{cs.key}': unknown saved type '{cs.detected_type}' ignored.")
            continue
        if saved_detected != d.detected_type:
            notes.append(f"Column '{cs.key}': saved type is {saved_detected.value}, the data now looks like "
                         f"{d.detected_type.value}.")
        d.output_type = saved_output
        d.include_in_export, d.short_name = cs.export, cs.short_name
        if cs.type_detection:
            d.type_detection = TypeDetection.from_dict(cs.type_detection) if saved_detected == d.detected_type else d.type_detection
    config.nodes[:] = [TransformationNode.from_dict(n) for n in profile.nodes]
    config.bands[:] = [dict(b) for b in profile.bands]
    return notes
