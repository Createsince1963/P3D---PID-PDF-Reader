"""Neutral transformation nodes (planning basis, section 12). Pure Python, no Qt.

Every user action that changes data becomes one node; the same node feeds preview, export and the JSON profile.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OutputDefinition:
    column_id: str
    name: str
    data_type: str
    display_index: int | None = None

    def to_dict(self) -> dict:
        d = {"id": self.column_id, "name": self.name, "type": self.data_type}
        if self.display_index is not None:
            d["display_index"] = self.display_index
        return d

    @staticmethod
    def from_dict(d: dict) -> "OutputDefinition":
        di = d.get("display_index")
        return OutputDefinition(str(d["id"]), str(d.get("name") or ""), str(d.get("type") or "text"),
                                int(di) if di is not None else None)


@dataclass(frozen=True, slots=True)
class TransformationNode:
    node_id: str
    operation: str
    input_ids: tuple[str, ...]
    parameters: dict[str, object]
    output: OutputDefinition
    keep_inputs: bool = True
    enabled: bool = True
    error_policy: str = "mark"

    def to_dict(self) -> dict:
        d = {"id": self.node_id, "operation": self.operation, "inputs": list(self.input_ids),
             "parameters": dict(self.parameters), "output": self.output.to_dict(),
             "keep_inputs": self.keep_inputs, "enabled": self.enabled}
        if self.error_policy != "mark":
            d["error_policy"] = self.error_policy
        return d

    @staticmethod
    def from_dict(d: dict) -> "TransformationNode":
        return TransformationNode(node_id=str(d["id"]), operation=str(d["operation"]),
                                  input_ids=tuple(str(x) for x in d.get("inputs") or ()),
                                  parameters=dict(d.get("parameters") or {}),
                                  output=OutputDefinition.from_dict(d["output"]),
                                  keep_inputs=bool(d.get("keep_inputs", True)), enabled=bool(d.get("enabled", True)),
                                  error_policy=str(d.get("error_policy") or "mark"))
