"""Column definitions and the configuration of one table (planning basis, sections 11, 11.5, 16). Pure Python, no Qt.

`ColumnConfig` is the only place that changes `output_type`: through an explicit convert node. There is no setter that
changes a type without a node (D9), and the source type is never overwritten.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .column_types import ColumnType, OnInvalid, TypeDetection
from .convert import ConvertError, ConvertParameters, build_convert_node
from .transformation_node import TransformationNode


@dataclass(slots=True)
class ColumnDefinition:
    column_id: str
    source_name: str
    output_name: str
    source_type: ColumnType = ColumnType.TEXT          # as delivered by the source, never overwritten
    detected_type: ColumnType = ColumnType.TEXT        # engine result (== source_type for authoritative origins)
    output_type: ColumnType = ColumnType.TEXT          # differs from source_type only through a convert node
    type_detection: TypeDetection | None = None
    display_index: int = 0
    visible_in_editor: bool = True
    include_in_export: bool = True
    calculated: bool = False
    sample_value: object | None = None
    short_name: str = ""                               # tile label chosen by the user ("" = automatic)

    def to_dict(self) -> dict:
        d = {"id": self.column_id, "source_name": self.source_name, "output_name": self.output_name,
             "source_type": self.source_type.value, "detected_type": self.detected_type.value,
             "output_type": self.output_type.value, "display_index": self.display_index,
             "visible_in_editor": self.visible_in_editor, "include_in_export": self.include_in_export,
             "calculated": self.calculated}
        if self.short_name:
            d["short_name"] = self.short_name
        if self.type_detection is not None:
            d["type_detection"] = self.type_detection.to_dict()
        return d

    @staticmethod
    def from_dict(d: dict) -> "ColumnDefinition":
        def ctype(key: str) -> ColumnType:
            try:
                return ColumnType(str(d.get(key) or "text"))
            except ValueError:
                return ColumnType.UNKNOWN
        td = d.get("type_detection")
        return ColumnDefinition(column_id=str(d["id"]), source_name=str(d.get("source_name") or ""),
                                output_name=str(d.get("output_name") or d.get("source_name") or ""),
                                source_type=ctype("source_type"), detected_type=ctype("detected_type"),
                                output_type=ctype("output_type"),
                                type_detection=TypeDetection.from_dict(td) if isinstance(td, dict) else None,
                                display_index=int(d.get("display_index") or 0),
                                visible_in_editor=bool(d.get("visible_in_editor", True)),
                                include_in_export=bool(d.get("include_in_export", True)),
                                calculated=bool(d.get("calculated", False)),
                                short_name=str(d.get("short_name") or ""))


@dataclass
class ColumnConfig:
    columns: list[ColumnDefinition] = field(default_factory=list)
    nodes: list[TransformationNode] = field(default_factory=list)
    bands: list[dict] = field(default_factory=list)       # group header bands: {"name", "keys": [source keys], "color": palette index}

    def column(self, column_id: str) -> ColumnDefinition:
        for c in self.columns:
            if c.column_id == column_id:
                return c
        raise KeyError(column_id)

    def convert_node(self, column_id: str) -> TransformationNode | None:
        return next((n for n in self.nodes if n.operation == "convert" and n.input_ids == (column_id,)), None)

    def _next_id(self, prefix: str) -> str:
        used = {n.node_id for n in self.nodes} | {n.output.column_id for n in self.nodes} | {c.column_id for c in self.columns}
        i = 1
        while f"{prefix}{i:02d}" in used:
            i += 1
        return f"{prefix}{i:02d}"

    def set_output_type(self, column_id: str, to_type: ColumnType, *, text_values=None,
                        on_invalid: OnInvalid = OnInvalid.EMPTY_FLAG, date_format: str | None = None,
                        decimal_separator: str = ".", thousands_separator: str = ",") -> TransformationNode | None:
        """Change the OUTPUT type through an explicit convert node. Setting it back to the source type removes the node.
        Returns the node (or None). Raises ConvertError; on an error nothing is changed."""
        col = self.column(column_id)
        old = self.convert_node(column_id)
        if to_type == col.source_type:                                  # back to the source: no node, no override
            if old is not None:
                self.nodes.remove(old)
            col.output_type = col.source_type
            self._set_override(col, False)
            return None
        node = build_convert_node(node_id=old.node_id if old else self._next_id("n"), column_id=column_id,
                                  column_name=col.output_name, from_type=col.source_type, to_type=to_type,
                                  out_id=old.output.column_id if old else self._next_id("x"), on_invalid=on_invalid,
                                  decimal_separator=decimal_separator, thousands_separator=thousands_separator,
                                  date_format=date_format, text_values=text_values, display_index=col.display_index)
        assert node is not None
        if old is not None:
            self.nodes[self.nodes.index(old)] = node
        else:
            self.nodes.append(node)
        col.output_type = to_type
        self._set_override(col, True)
        return node

    @staticmethod
    def _set_override(col: ColumnDefinition, on: bool) -> None:
        td = col.type_detection
        if td is not None:
            from dataclasses import replace
            col.type_detection = replace(td, override=on)

    def to_dict(self) -> dict:
        return {"columns": [c.to_dict() for c in self.columns], "nodes": [n.to_dict() for n in self.nodes],
                "bands": [{"name": b["name"], "keys": list(b["keys"]), "color": b.get("color", 0), "band": bool(b.get("band", False))}
                          for b in self.bands]}

    @staticmethod
    def from_dict(d: dict) -> "ColumnConfig":
        return ColumnConfig([ColumnDefinition.from_dict(c) for c in d.get("columns") or ()],
                            [TransformationNode.from_dict(n) for n in d.get("nodes") or ()],
                            [dict(b) for b in d.get("bands") or () if isinstance(b, dict)])

    def convert_params(self, column_id: str) -> ConvertParameters | None:
        n = self.convert_node(column_id)
        return ConvertParameters.from_dict(n.parameters) if n else None


__all__ = ["ColumnConfig", "ColumnDefinition", "ConvertError"]
