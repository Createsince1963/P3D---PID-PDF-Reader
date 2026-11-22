"""Public, Qt-free API of the column editor module (interface definition: md/XLS_EDITOR_INTERFACES.md).

* `config_to_document / config_from_document`  the saved configuration as one JSON-able dict with a schema number
* `replay_derived / apply_layout`              put a saved configuration onto a `ColumnSource` (calculated columns, order, labels, export flags)
* `apply_to`                                   run a saved configuration over plain rows, without any window
* `Providers`                                  data the module must not know itself (tag colours, code lists, sheet reader)

Nothing in this module imports Qt or the host application.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from .domain import derive as D
from .domain.column_config import ColumnConfig
from .domain.convert import ConvertParameters, convert_value
from .domain.transformation_node import TransformationNode
from .models.column_source import ColumnSource

MODULE_VERSION = "0.1.0"
CONFIG_SCHEMA = 3


class ConfigError(Exception):
    """The saved configuration cannot be used; the text is readable for the user."""


# ---------------------------------------------------------------------------------------------------------------------
# configuration document
# ---------------------------------------------------------------------------------------------------------------------
def config_to_document(config: ColumnConfig) -> dict:
    """The configuration as a plain dict (JSON-able): {"schema", "module_version", "columns", "nodes"}."""
    doc = config.to_dict()
    return {"schema": CONFIG_SCHEMA, "module_version": MODULE_VERSION, "columns": doc["columns"], "nodes": doc["nodes"]}


def config_from_document(doc: dict) -> tuple[ColumnConfig, list[str]]:
    """(config, notes). Raises ConfigError for a document that is not usable; nothing is applied then.
    Steps that cannot be read are skipped and named in `notes`."""
    if not isinstance(doc, dict):
        raise ConfigError("The saved configuration is not a valid document.")
    schema = doc.get("schema")
    if not isinstance(schema, int) or isinstance(schema, bool):
        raise ConfigError("The saved configuration has no schema number.")
    if schema > CONFIG_SCHEMA:
        raise ConfigError(f"The saved configuration was made by a newer version (schema {schema}, this module reads up to {CONFIG_SCHEMA}).")
    if schema < 1:
        raise ConfigError(f"Unknown schema number {schema}.")
    notes: list[str] = []
    try:
        config = ColumnConfig.from_dict({"columns": doc.get("columns") or (), "nodes": []})
    except (KeyError, TypeError, ValueError) as e:
        raise ConfigError(f"The saved column list cannot be read: {e}") from e
    for i, nd in enumerate(doc.get("nodes") or ()):
        try:
            config.nodes.append(TransformationNode.from_dict(nd))
        except (KeyError, TypeError, ValueError) as e:
            notes.append(f"Step {i + 1} was skipped: it cannot be read ({type(e).__name__}).")
    return config, notes


# ---------------------------------------------------------------------------------------------------------------------
# put a configuration onto a ColumnSource
# ---------------------------------------------------------------------------------------------------------------------
def replay_derived(source: ColumnSource, config: ColumnConfig) -> list[str]:
    """Create the calculated columns of `config` in `source`, in the order the steps were made (a step on a calculated column works).
    Existing columns are left alone. A step whose input is missing or that fails is reported in the notes, never raised."""
    notes: list[str] = []
    for node in config.nodes:
        if not D.is_derived(node) or not D.output_key(node):
            continue
        key, name = D.output_key(node), node.output.name or D.output_key(node)
        have = set(source.keys())
        if key in have:
            continue
        missing = [k for k in D.input_keys(node) if k not in have]
        if missing:
            notes.append(f"Calculated column '{name}' was not created: input column(s) {', '.join(missing)} are not in this data.")
            continue
        try:
            values = D.compute(node, lambda k: source.column_values(k or source.keys()[0]))
        except Exception as e:  # noqa: BLE001 - e.g. the other list of a lookup is gone
            notes.append(f"Calculated column '{name}' was not created: {e}")
            continue
        if not source.add_derived(key, name, values):
            notes.append(f"Calculated column '{name}' could not be added.")
    return notes


def apply_layout(source: ColumnSource, config: ColumnConfig) -> list[str]:
    """Order (display_index), output names and export flags of `config` onto `source`. Columns the source does not have are ignored."""
    notes: list[str] = []
    cols = [c for c in config.columns if c.source_name in set(source.keys())]
    for pos, c in enumerate(sorted(cols, key=lambda c: c.display_index)):
        try:
            source.move(c.source_name, pos)
            if c.output_name and c.output_name != source.label(c.source_name):
                source.set_label(c.source_name, c.output_name)
            source.set_export_excluded(c.source_name, not c.include_in_export)
        except Exception as e:  # noqa: BLE001
            notes.append(f"Column '{c.output_name or c.source_name}': layout could not be applied ({e}).")
    return notes


# ---------------------------------------------------------------------------------------------------------------------
# headless run
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(slots=True)
class ApplyResult:
    headers: list[str]
    rows: list[list[object]]
    notes: list[str] = field(default_factory=list)


def apply_to(headers: Sequence[str], rows: Sequence[Sequence[object]], document: dict, *, keys: Sequence[str] | None = None) -> ApplyResult:
    """Run a saved configuration over plain rows (no Qt, no window).

    `keys` are the column keys the configuration refers to (default: the headers). Steps run in stored order; a step whose input
    is missing is skipped and named in `notes`. Result: only columns with `include_in_export`, ordered by `display_index`,
    named by `output_name`; columns with a convert step hold typed values (int, float, date, ...), all others text / the original value.
    Columns the configuration does not know are appended at the end in source order."""
    config, notes = config_from_document(document)
    keys = list(keys) if keys is not None else list(headers)
    if len(keys) != len(headers):
        raise ConfigError("`keys` and `headers` must have the same length.")
    values: dict[str, list] = {k: [(r[i] if i < len(r) else "") for r in rows] for i, k in enumerate(keys)}
    names: dict[str, str] = dict(zip(keys, headers))
    for node in config.nodes:
        if not D.is_derived(node) or not D.output_key(node):
            continue
        key, name = D.output_key(node), node.output.name or D.output_key(node)
        missing = [k for k in D.input_keys(node) if k not in values]
        if missing:
            notes.append(f"Calculated column '{name}' was skipped: input column(s) {', '.join(missing)} are not in this data.")
            continue
        try:
            values[key] = D.compute(node, lambda k: values[k or keys[0]])
            names[key] = name
        except Exception as e:  # noqa: BLE001
            notes.append(f"Calculated column '{name}' was skipped: {e}")
    known = {c.source_name: c for c in config.columns}
    ordered = [c for c in sorted(config.columns, key=lambda c: c.display_index) if c.source_name in values]
    out = [(c.source_name, c.output_name or names[c.source_name], c) for c in ordered if c.include_in_export]
    out += [(k, names[k], None) for k in values if k not in known]
    result_cols: list[list] = []
    for key, _, c in out:
        col = list(values[key])
        node = config.convert_node(c.column_id) if c is not None else None
        if node is not None:
            try:
                p = ConvertParameters.from_dict(node.parameters)
            except (KeyError, ValueError) as e:
                notes.append(f"Column '{names[key]}': type change skipped ({e}).")
            else:
                conv = [convert_value(v, p) for v in col]
                bad = sum(1 for _, ok in conv if not ok)
                if bad:
                    notes.append(f"Column '{names[key]}': {bad} value(s) do not fit type '{p.to_type.value}'.")
                col = [v for v, _ in conv]
        result_cols.append(col)
    n = len(rows)
    return ApplyResult([name for _, name, _ in out], [[col[r] for col in result_cols] for r in range(n)], notes)


# ---------------------------------------------------------------------------------------------------------------------
# providers
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(slots=True)
class Providers:
    """Data the module must not know itself. All optional; a provider that raises counts as 'no data'.

    tag_colors   () -> {tag type: "#RRGGBB" or "#RRGGBB@NN"}      colour categories of the tiles
    code_lists   () -> {list name: [values]}                      lists offered by 'Check against code list'
    sheet_reader (worksheet) -> (headers, rows)                   reading of the other Excel list in 'Add columns from another list'
    """
    tag_colors: Callable[[], dict] | None = None
    code_lists: Callable[[], dict] | None = None
    sheet_reader: Callable[[object], tuple[list[str], list[list[str]]]] | None = None

    def install(self, controller=None) -> None:
        """Hand the providers over: tag colours / code lists to the editor controller (when given), the sheet reader to the lookup module."""
        from .domain import lookup
        if self.sheet_reader is not None:
            lookup.set_sheet_reader(self.sheet_reader)
        if controller is not None:
            if self.tag_colors is not None:
                controller.set_tag_color_provider(self.tag_colors)
            if self.code_lists is not None:
                controller.set_code_list_provider(self.code_lists)


__all__ = ["MODULE_VERSION", "CONFIG_SCHEMA", "ConfigError", "ApplyResult", "Providers", "config_to_document", "config_from_document",
           "replay_derived", "apply_layout", "apply_to"]
