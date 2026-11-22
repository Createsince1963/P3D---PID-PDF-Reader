"""ColumnConfigModel (QAbstractListModel) and ColumnEditorController for the QML tile grid (QtCore only).

Tiles are only a view: every action goes through ColumnEditorController -> UndoStack -> ColumnSource.
Types live in a ColumnConfig (domain); the output type changes only through explicit convert nodes, a group of columns
becomes a neutral join node. A group is a DRAFT until applyGroup(); cancelGroup() leaves no node and no data change.
"""
from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import (Property, QAbstractListModel, QModelIndex, QObject, Qt, Signal, Slot)

from ..domain.column_config import ColumnConfig, ColumnDefinition
from ..domain.column_types import ColumnType, OnInvalid
from ..domain.convert import ConvertError, ConvertParameters, preview_convert, resolve_date_format
from ..domain.join import JoinError, JoinParameters, build_join_node, example_row, join_columns, join_row
from ..domain import bands as BANDS
from ..domain import indexcol as IX
from ..domain import yesno as YN
from ..domain import protected as PROT
from ..domain import checks as CK
from ..domain import conditional as CO
from ..domain import derive as D
from ..domain import lookup as LK
from ..domain import tag_colors as TC
from ..domain import text_ops as TO
from ..domain.transformation_node import TransformationNode
from ..domain.type_detection import detect_column, is_empty
from .column_source import ColumnSource
from .undo_stack import Command, UndoStack

CHIP = {ColumnType.TEXT: "ABC", ColumnType.INTEGER: "123", ColumnType.DECIMAL: "1.5", ColumnType.BOOLEAN: "T/F",
        ColumnType.DATE: "date", ColumnType.DATETIME: "d+t", ColumnType.PERCENTAGE: "%", ColumnType.TIME: "time",
        ColumnType.DURATION: "dur", ColumnType.MIXED: "mix", ColumnType.NULL: "null", ColumnType.UNKNOWN: "?"}

# Power-Query-like names shown to the user
TYPE_NAMES = {ColumnType.TEXT: "Text", ColumnType.INTEGER: "Ganzzahl", ColumnType.DECIMAL: "Dezimalzahl",
              ColumnType.PERCENTAGE: "Prozent", ColumnType.BOOLEAN: "Wahr/Falsch", ColumnType.DATE: "Datum",
              ColumnType.TIME: "Zeit", ColumnType.DATETIME: "Datum/Zeit", ColumnType.DURATION: "Dauer",
              ColumnType.MIXED: "Gemischt", ColumnType.UNKNOWN: "Unbekannt", ColumnType.NULL: "Leer"}
DERIVED_OPERATIONS = D.DERIVED_OPERATIONS        # nodes that create a calculated column
PSEUDO_TYPES = ("auto", "source")                       # "Auto Detect", "Keep Source Type"


def short_name(label: str, limit: int = 12) -> str:
    return label if len(label) <= limit else label[: limit - 1] + "…"


class ColumnConfigModel(QAbstractListModel):
    (KeyRole, LabelRole, ShortRole, ChipRole, TypeRole, HiddenRole, PositionRole, CalculatedRole, TipRole,
     SelOrderRole, ExportRole, TagColorRole, MatchRole, RenamedRole, GroupColorRole, GroupNameRole, TemporaryRole, SplitRole, ProtectedRole, OriginalNameRole) = (Qt.UserRole + i for i in range(1, 21))
    countChanged = Signal()
    statsChanged = Signal()          # number of tiles in the 'not exported' area changed
    searchChanged = Signal()         # text of the tile / column search field changed

    def __init__(self, source: ColumnSource, config: ColumnConfig | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self.source = source
        self.config = config or ColumnConfig()
        self._keys: list[str] = []
        self._internal = False
        self._state: tuple = ()
        self._sel_order: dict[str, int] = {}
        self._tag_provider = None                  # callable -> {tag type: '#RRGGBB'} (project definitions > Tag structures); may be None
        self._tag_colors: dict[str, str] | None = None
        self._search = ""                          # search field: only tiles whose name contains this text are shown
        self._split_key = ""                       # column the Excel export splits by: its tile is light green (display only)
        self.reload()
        source.on_external_change(self._external)

    # --- model ---------------------------------------------------------------------------------------
    def roleNames(self):  # noqa: N802
        return {self.KeyRole: b"key", self.LabelRole: b"label", self.ShortRole: b"shortName", self.ChipRole: b"chip",
                self.TypeRole: b"typeName", self.HiddenRole: b"hidden", self.PositionRole: b"position",
                self.CalculatedRole: b"calculated", self.TipRole: b"tip", self.SelOrderRole: b"selOrder",
                self.ExportRole: b"inExport", self.TagColorRole: b"tagColor", self.MatchRole: b"match",
                self.RenamedRole: b"renamed", self.GroupColorRole: b"groupColor", self.GroupNameRole: b"groupName",
                self.TemporaryRole: b"temporary", self.SplitRole: b"isSplit", self.ProtectedRole: b"protectedColumn",
                self.OriginalNameRole: b"originalName"}

    def set_split_key(self, key: str | None) -> None:
        """Mark the tile of the export split column (light green); None / '' removes the mark."""
        key = key or ""
        if key == self._split_key:
            return
        self._split_key = key
        if self._keys:
            self.dataChanged.emit(self.index(0), self.index(len(self._keys) - 1), [self.SplitRole])

    def rowCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(self._keys)

    def _count(self) -> int:
        return len(self._keys)

    count = Property(int, _count, notify=countChanged)

    def _not_exported(self) -> int:
        """Columns shown in the 'Not exported' tile area: visible (not hidden) and excluded from export. A hidden column
        is shown in the 'Hidden' area instead, whatever its export flag - the two states are independent (kept, just not
        displayed in this area while hidden)."""
        return sum(1 for k in self._keys if not self.source.is_hidden(k)
                   and self.definition(k) is not None and not self.definition(k).include_in_export)

    notExportedCount = Property(int, _not_exported, notify=statsChanged)

    def _table_hidden_count(self) -> int:
        """Not-exported columns hidden in the table by the "Hide all in table" button (their tiles stay in 'Not exported')."""
        f = getattr(self.source, "is_table_hidden", None)
        return sum(1 for k in self._keys if f(k)) if f else 0

    tableHiddenCount = Property(int, _table_hidden_count, notify=statsChanged)

    def _hidden_count(self) -> int:
        return sum(1 for k in self._keys if self.source.is_hidden(k))

    hiddenCount = Property(int, _hidden_count, notify=statsChanged)

    def _renamed_count(self) -> int:
        """Columns whose output name differs from the original name (display only: the data and the source name are kept)."""
        return sum(1 for k in self._keys if self.source.label(k) != self.source.original_label(k))

    renamedCount = Property(int, _renamed_count, notify=statsChanged)

    # --- search field (tiles / columns) -----------------------------------------------------------------------------------
    def matches(self, key: str) -> bool:
        """Search text (case-insensitive) is part of the column name, the short tile name or the source name; empty = all.
        "a" finds every column with an a, "alt" every column with "alt" in its name."""
        s = self._search
        if not s:
            return True
        d = self.definition(key)
        names = (self.source.label(key), self.tile_name(key), d.source_name if d else "")
        return any(s in n.lower() for n in names if n)

    def set_search(self, text: str) -> None:
        text = (text or "").strip().lower()
        if text == self._search:
            return
        self._search = text
        if self._keys:
            self.dataChanged.emit(self.index(0), self.index(len(self._keys) - 1), [self.MatchRole])
        self.searchChanged.emit()

    def match_rows(self) -> list[int]:
        return [r for r, k in enumerate(self._keys) if self.matches(k)]

    searchText = Property(str, lambda self: self._search, notify=searchChanged)
    matchCount = Property(int, lambda self: len(self.match_rows()) if self._search else len(self._keys), notify=searchChanged)

    # --- colour categories (project definitions: colour per tag type) ---------------------------------------------------
    def set_tag_color_provider(self, provider) -> None:
        self._tag_provider = provider
        self.refresh_tag_colors()

    def refresh_tag_colors(self) -> None:
        """Read the colours of the project definitions again (the next lookup asks the provider) and repaint all tiles."""
        self._tag_colors = None
        if self._keys:
            self.dataChanged.emit(self.index(0), self.index(len(self._keys) - 1), [self.TagColorRole])

    def _colors(self) -> dict[str, str]:
        if self._tag_colors is None:
            try:
                self._tag_colors = dict(self._tag_provider() or {}) if self._tag_provider else {}
            except Exception:  # noqa: BLE001 - missing / damaged project definitions: tiles stay neutral
                self._tag_colors = {}
        return self._tag_colors

    def tag_info(self, key: str) -> tuple[str, str]:
        """(tag type, colour) of a column, ('', '') = neutral (no tag type matches, no colour defined, or the full line number)."""
        colors = self._colors()
        if not colors:
            return "", ""
        return TC.match_tag_type(self.source.label(key), colors)

    def header_marker(self, key: str) -> tuple[str, str] | None:
        """(tint, stripe) colours for the column header of the preview table: the same categories the tiles show.
        Not exported = orange tint; stripe = tag colour only (a calculated column has green cells already, no extra line). None = plain header."""
        d = self.definition(key)
        tint = "#F08C00" if d is not None and not d.include_in_export else ""
        stripe = self.tag_info(key)[1]
        return (tint, stripe) if (tint or stripe) else None

    def positions(self) -> dict[str, int]:
        """Number of every tile (1-based, as shown on the tile) by column key; the table header shows the same number."""
        return {k: i for i, k in enumerate(self._keys, start=1)}

    def definition(self, key: str) -> ColumnDefinition | None:
        return next((c for c in self.config.columns if c.source_name == key or c.column_id == key), None)

    def calculated_keys(self) -> set[str]:
        return {str(n.parameters.get("output_key")) for n in self.config.nodes
                if n.operation in DERIVED_OPERATIONS and n.enabled and n.parameters.get("output_key")}

    def is_protected(self, key: str) -> bool:
        return PROT.is_protected(key, self.source.label(key))

    def is_calculated(self, key: str) -> bool:
        return key in self.calculated_keys()

    def tile_name(self, key: str) -> str:
        d = self.definition(key)
        return (d.short_name if d and d.short_name else short_name(self.source.label(key)))

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._keys):
            return None
        key = self._keys[index.row()]
        d = self.definition(key)
        typ = d.output_type if d else ColumnType.TEXT
        if role in (self.KeyRole,):
            return key
        if role in (self.LabelRole, Qt.DisplayRole):
            return self.source.label(key)                          # the label goes through the table header: only read it when needed
        if role == self.ShortRole:
            return self.tile_name(key)
        if role == self.ChipRole:
            return CHIP[typ]
        if role == self.TypeRole:
            return typ.value
        if role == self.HiddenRole:
            return self.source.is_hidden(key)
        if role == self.PositionRole:
            return index.row() + 1
        if role == self.CalculatedRole:
            return self.is_calculated(key) or bool(d and d.calculated)
        if role == self.SelOrderRole:
            return self._sel_order.get(key, 0)
        if role == self.ExportRole:
            return d.include_in_export if d else True
        if role == self.TagColorRole:
            return self.tag_info(key)[1]
        if role == self.TemporaryRole:                                 # display-only column (merged view / duplicates): grey tile
            return self.is_temporary(key)
        if role == self.ProtectedRole:                                 # DCF database index: red bold, cannot be hidden
            return self.is_protected(key)
        if role == self.SplitRole:
            return bool(self._split_key) and key == self._split_key
        if role in (self.GroupColorRole, self.GroupNameRole):         # tile group: frame colour (stronger colour of the group) and name
            g = next((b for b in self.config.bands if key in b["keys"]), None)
            if role == self.GroupNameRole:
                return g["name"] if g else ""
            return "#" + BANDS.colors(g.get("color", 0))[1] if g else ""
        if role == self.RenamedRole:                 # renamed output column: red mark at the right edge of the tile (display only)
            return self.source.label(key) != self.source.original_label(key)
        if role == self.OriginalNameRole:            # the name the column had before the rename - always carried along
            return self.source.original_label(key)
        if role == self.MatchRole:
            return self.matches(key)
        if role == self.TipRole:
            return f"{self.source.label(key)}  ({TYPE_NAMES.get(typ, typ.value)})"
        return None

    # --- source <-> model ----------------------------------------------------------------------------------
    def reload(self) -> None:
        self._tag_colors = None                    # project definitions are read again with the new table
        self.beginResetModel()
        self._keys = self.source.keys()
        self._ensure_definitions()
        self.endResetModel()
        self._state = self._current_state()
        self.countChanged.emit()
        self.statsChanged.emit()

    def refresh_all(self) -> None:
        """Like `reload`, but the tiles stay: when the column order did not change only the data of every tile is re-read, so QML does not
        rebuild all delegates (a model reset makes the grid flash and takes noticeably longer)."""
        if list(self.source.keys()) != self._keys:
            return self.reload()
        self._ensure_definitions()
        if self._keys:
            self.dataChanged.emit(self.index(0), self.index(len(self._keys) - 1))
        self._state = self._current_state()
        self.countChanged.emit()
        self.statsChanged.emit()

    def is_temporary(self, key: str) -> bool:
        f = getattr(self.source, "is_temporary", None)
        return bool(f and f(key))

    def _ensure_definitions(self) -> None:
        known = {c.source_name for c in self.config.columns}
        for key in self._keys:
            if key in known:
                continue
            typ, td = detect_column(self.source.original_label(key), text_values=self.source.samples(key))
            n = len(self.config.columns)
            self.config.columns.append(ColumnDefinition(
                column_id=f"c{n + 1:02d}", source_name=key, output_name=self.source.label(key), source_type=ColumnType.TEXT,
                detected_type=typ, output_type=ColumnType.TEXT, type_detection=td, display_index=n + 1))
        for key in self._keys:                                      # temporary columns: the tile shows the real export state
            if self.is_temporary(key):
                d = self.definition(key)
                if d is not None:
                    d.include_in_export = bool(self.source.temp_exported(key))

    def _current_state(self) -> tuple:
        keys = self.source.keys()
        return (tuple(keys), tuple(self.source.is_hidden(k) for k in keys), tuple(self.source.label(k) for k in keys),
                tuple(bool(self.is_temporary(k) and self.source.temp_exported(k)) for k in keys))

    def _external(self) -> None:
        """The table reports a change (also debounced echoes of our own moves): reload only if order / visibility /
        labels really differ from what the tiles show."""
        if self._internal or self._current_state() == self._state:
            return
        self.reload()                             # the user changed order / visibility / labels in the ListTable

    def keys(self) -> list[str]:
        return list(self._keys)

    def move_row(self, from_row: int, to_row: int) -> bool:
        """The ONLY place that moves a column. Returns False for an invalid / no-op move."""
        n = len(self._keys)
        if not (0 <= from_row < n and 0 <= to_row < n) or from_row == to_row:
            return False
        self._internal = True
        try:
            self.beginMoveRows(QModelIndex(), from_row, from_row, QModelIndex(), to_row + 1 if to_row > from_row else to_row)
            key = self._keys.pop(from_row)
            self._keys.insert(to_row, key)
            self.source.move(key, to_row)
            self.endMoveRows()
        finally:
            self._internal = False
        self._renumber()
        self._state = self._current_state()
        return True

    def _renumber(self) -> None:
        for i, key in enumerate(self._keys, start=1):
            d = self.definition(key)
            if d:
                d.display_index = i
        if self._keys:
            self.dataChanged.emit(self.index(0), self.index(len(self._keys) - 1), [self.PositionRole])

    # --- calculated tiles ----------------------------------------------------------------------------------------
    def add_calculated(self, key: str, row: int, column_id: str, label: str) -> None:
        """A calculated column now exists in the source (appended at the end): show its tile at `row`."""
        self._internal = True
        try:
            row = max(0, min(row, len(self._keys)))
            self.beginInsertRows(QModelIndex(), row, row)
            self._keys.insert(row, key)
            if self.definition(key) is None:
                typ, td = detect_column(label, text_values=self.source.samples(key))
                self.config.columns.append(ColumnDefinition(
                    column_id=column_id, source_name=key, output_name=label, source_type=ColumnType.TEXT, detected_type=typ,
                    output_type=ColumnType.TEXT, type_detection=td, display_index=row + 1, calculated=True))
            self.endInsertRows()
            self.source.move(key, row)
        finally:
            self._internal = False
        self._renumber()
        self._state = self._current_state()
        self.countChanged.emit()
        self.statsChanged.emit()

    def remove_calculated(self, key: str) -> None:
        if key not in self._keys:
            return
        self._internal = True
        try:
            row = self._keys.index(key)
            self.beginRemoveRows(QModelIndex(), row, row)
            self._keys.pop(row)
            self.config.columns[:] = [c for c in self.config.columns if c.source_name != key]
            self.endRemoveRows()
        finally:
            self._internal = False
        self._renumber()
        self._state = self._current_state()
        self.countChanged.emit()
        self.statsChanged.emit()

    def set_selection_order(self, order: dict[str, int]) -> None:
        touched = set(self._sel_order) | set(order)
        self._sel_order = dict(order)
        for key in touched:
            if key in self._keys:
                r = self._keys.index(key)
                self.dataChanged.emit(self.index(r), self.index(r), [self.SelOrderRole])

    def restore_config(self, state: dict) -> None:
        """Put the column configuration (types, convert nodes) back to a saved state (undo / redo)."""
        again = ColumnConfig.from_dict(state)
        self.config.columns[:] = again.columns
        self.config.nodes[:] = again.nodes
        self.config.bands[:] = again.bands

    def refresh_row(self, row: int) -> None:
        self._state = self._current_state()
        if 0 <= row < len(self._keys):
            self.dataChanged.emit(self.index(row), self.index(row))
            self.statsChanged.emit()

    def refresh_groups(self) -> None:
        """Groups changed (group / ungroup / undo / redo): every tile re-reads its group frame."""
        if self._keys:
            self.dataChanged.emit(self.index(0), self.index(len(self._keys) - 1), [self.GroupColorRole, self.GroupNameRole])

    def refresh_key(self, key: str) -> None:
        if key in self._keys:
            self.refresh_row(self._keys.index(key))


class ColumnEditorController(QObject):
    """Everything QML may do: move, hide / show, select (single and Ctrl multi), change type, group, undo / redo."""
    undoChanged = Signal()           # also tells the steps panel that the list of steps may have changed
    selectedChanged = Signal()
    draftChanged = Signal()
    message = Signal(str)
    functionRequested = Signal(str, int)     # ribbon / menus -> QML: open the dialog of a function (name, tile row)
    changeTypeRequested = Signal(int)        # side pane (flow deck) -> tile grid: open "Change column type" next to the tile
    editStepRequested = Signal("QVariantMap")   # side pane -> tile grid: open the dialog of a step with its settings

    def __init__(self, model: ColumnConfigModel, parent: QObject | None = None):
        super().__init__(parent)
        self.model = model
        self.stack = UndoStack()
        self.undoChanged.connect(model.refresh_groups)          # group frames follow group / ungroup / undo / redo
        self._selected = -1
        self._multi: list[str] = []                  # selection order (keys); badges 1, 2, 3 ... when more than one
        self._pick = None                            # callable(key | None) waiting for the next tile click (export split), or None
        self._draft: dict | None = None
        self._draft_cache: dict = {"active": False}
        self._stat_cache: dict[str, tuple[float, dict]] = {}       # hover statistics per column (a few seconds old at most)
        model.modelReset.connect(self._reset)

    def _reset(self) -> None:
        self.stack.clear()
        self._selected = -1
        self._multi = []
        self._draft = None
        self._stat_cache = {}
        self.model._sel_order = {}
        self.undoChanged.emit()
        self.selectedChanged.emit()
        self._emit_draft()

    def _run(self, text: str, redo, undo) -> None:
        """Execute a user action now and record it for undo / redo."""
        redo()
        self.stack.push(Command(text, redo, undo), execute=False)
        self.undoChanged.emit()

    def _key(self, row: int) -> str | None:
        keys = self.model.keys()
        return keys[row] if 0 <= row < len(keys) else None

    # --- moves -----------------------------------------------------------------------------------------------------
    # --- pick a tile for the host (Excel export: split by this column) ----------------------------------------------------
    def begin_pick(self, callback) -> None:
        """The next plain click on a tile calls `callback(key)` once (the host asked "which column?")."""
        self._pick = callback

    def cancel_pick(self) -> None:
        self._pick = None

    @Slot(int)
    def pickTile(self, row: int) -> None:
        cb, self._pick = self._pick, None
        key = self._key(row)
        if cb is not None and key is not None:
            cb(key)

    @Slot(int, int, result=bool)
    def moveColumn(self, from_row: int, to_row: int) -> bool:
        if not (0 <= from_row < self.model.rowCount() and 0 <= to_row < self.model.rowCount()) or from_row == to_row:
            return False
        if self.model.is_temporary(self._key(from_row)) or self.model.is_temporary(self._key(to_row)):
            self.message.emit("Eine temporäre Spalte kann nicht verschoben werden.")
            return False
        block = self._group_keys(self._key(from_row))
        if len(block) > 1:                                                   # a tile of a group: the whole block moves
            order = self.model.keys()
            target = order[to_row]
            if target in block:
                return False
            others = [k for k in order if k not in block]
            at = others.index(target) + (1 if to_row > from_row else 0)
            return self._reorder(others[:at] + block + others[at:], f"{len(block)} Spalten verschieben")
        cmd = Command("Spalte verschieben", lambda: self.model.move_row(from_row, to_row), lambda: self.model.move_row(to_row, from_row))
        self.stack.push(cmd)
        if self._selected == from_row:
            self._selected = to_row
            self.selectedChanged.emit()
        self.undoChanged.emit()
        return True

    # --- targets: one tile, or every tile of a multi selection ------------------------------------------------------------------
    def _targets(self, row: int) -> list[str]:
        """Keys a command acts on: the whole multi selection when `row` belongs to it, otherwise just that tile (display order)."""
        key = self._key(row)
        if key is None or self.model.is_temporary(key):                  # temporary columns: display only, no command acts on them
            return []
        if len(self._multi) > 1 and key in self._multi:
            keys = self.model.keys()
            return sorted((k for k in self._multi if k in keys and not self.model.is_temporary(k)), key=keys.index)
        return [key]

    @Slot(int, result=bool)
    def inSelection(self, row: int) -> bool:
        key = self._key(row)
        return key is not None and len(self._multi) > 1 and key in self._multi

    @Slot(int, result="QVariantMap")
    def menuInfo(self, row: int) -> dict:
        """What the tile menu needs to word its entries: how many tiles it acts on and the common hidden / export state."""
        keys = self._targets(row)
        src = self.model.source
        defs = [d for d in (self.model.definition(k) for k in keys) if d is not None]
        return {"count": len(keys), "multi": len(keys) > 1, "allHidden": bool(keys) and all(src.is_hidden(k) for k in keys),
                "anyExported": any(d.include_in_export for d in defs) if defs else True}

    def _reorder(self, new_keys: list[str], text: str, also=None) -> bool:
        """Bring the tiles into the order `new_keys` with the model's only mover; ONE undo step for the whole block.
        `also` = (do, undo) callables run in the same step (group bookkeeping)."""
        cur = self.model.keys()
        if new_keys == cur or sorted(new_keys) != sorted(cur):
            return False
        work, moves = list(cur), []
        for i, k in enumerate(new_keys):
            j = work.index(k)
            if j != i:
                moves.append((j, i))
                work.insert(i, work.pop(j))
        inverse = [(y, x) for x, y in reversed(moves)]
        active = self._key(self._selected)

        def go(pairs) -> None:
            for x, y in pairs:
                self.model.move_row(x, y)
            keys = self.model.keys()
            if active in keys:
                self._selected = keys.index(active)
            self.selectedChanged.emit()
        if also is None:
            self.stack.push(Command(text, lambda: go(moves), lambda: go(inverse)))
        else:
            self.stack.push(Command(text, lambda: (go(moves), also[0]()), lambda: (go(inverse), also[1]())))
        self.undoChanged.emit()
        return True

    @Slot(int, int, result=bool)
    def moveBy(self, row: int, delta: int) -> bool:
        keys = self._move_targets(row)
        if len(keys) < 2:
            return self.moveColumn(row, row + delta)
        order, sel = self.model.keys(), set(keys)
        for _ in range(abs(delta)):
            idx = [i for i, k in enumerate(order) if k in sel]
            if delta < 0:
                for i in idx:
                    if i > 0 and order[i - 1] not in sel:
                        order[i - 1], order[i] = order[i], order[i - 1]
            else:
                for i in reversed(idx):
                    if i < len(order) - 1 and order[i + 1] not in sel:
                        order[i + 1], order[i] = order[i], order[i + 1]
        return self._reorder(order, f"{len(keys)} Spalten verschieben")

    @Slot(int, bool, result=bool)
    def moveToEdge(self, row: int, to_first: bool) -> bool:
        keys = self._move_targets(row)
        if len(keys) < 2:
            return self.moveColumn(row, 0 if to_first else self.model.rowCount() - 1)
        others = [k for k in self.model.keys() if k not in keys]
        return self._reorder(keys + others if to_first else others + keys, f"{len(keys)} Spalten verschieben")

    @Slot(int, int, result=bool)
    def moveToPosition(self, row: int, position: int) -> bool:
        """`position` is 1-based, as the number on the tile; a multi selection moves as one block starting there."""
        keys = self._move_targets(row)
        if len(keys) < 2:
            return self.moveColumn(row, max(1, min(position, self.model.rowCount())) - 1)
        others = [k for k in self.model.keys() if k not in keys]
        at = max(0, min(position - 1, len(others)))
        return self._reorder(others[:at] + keys + others[at:], f"{len(keys)} Spalten verschieben")

    # --- visibility / export ----------------------------------------------------------------------------------------------
    @Slot(int, result=bool)
    def toggleHidden(self, row: int) -> bool:
        """Hide / show the tile, or all tiles of the multi selection (hide unless all of them are already hidden)."""
        keys = self._targets(row)
        if not keys:
            return False
        src = self.model.source
        hide = not all(src.is_hidden(k) for k in keys)
        if hide:
            keys = self._without_protected(keys)
            if not keys:
                return False
        want = [k for k in keys if src.is_hidden(k) != hide]
        done: list[str] = []
        for k in want:
            if src.set_hidden(k, hide):                                       # applied right here; the stack only records it
                done.append(k)
                self.model.refresh_key(k)
        if len(done) < len(want):
            self.message.emit("Die letzte sichtbare Spalte kann nicht ausgeblendet werden." if len(keys) == 1 else "Mindestens eine Spalte muss sichtbar bleiben.")
        if not done:
            return False

        def apply(h: bool) -> None:
            for k in done:
                src.set_hidden(k, h)
                self.model.refresh_key(k)
        n = len(done)
        self.stack.push(Command(("Spalte ausblenden" if hide else "Spalte einblenden") + ("" if n == 1 else f" ({n} Spalten)"),
                                lambda: apply(hide), lambda: apply(not hide)), execute=False)
        self.undoChanged.emit()
        return True

    @Slot(int, bool, result=bool)
    def setHidden(self, row: int, hidden: bool) -> bool:
        """Put the tile (or every tile of the multi selection) into the Hidden area (`hidden`) or restore it to the
        Exported / Not exported area it already belongs to (export state is never touched here - the two states are
        independent, see `toggleExport`). Drag and drop between the Hidden area and the other two areas uses this."""
        return self._set_hidden_keys(self._targets(row), hidden)

    @Slot(int, result=bool)
    def setAreaHidden(self, area: int) -> bool:
        """Bulk button of an area header. area 1 = 'Not exported': hide every not-exported column in the table below (toggle:
        a second click shows them again). The tiles stay in 'Not exported', the Hidden area is not touched and the export
        state is kept. area 2 = 'Hidden': show every hidden tile again."""
        src = self.model.source
        if area == 1:
            keys = [k for k in self.model.keys() if not src.is_hidden(k) and not self.model.is_protected(k)
                    and self.model.definition(k) is not None and not self.model.definition(k).include_in_export]
            if not hasattr(src, "set_table_hidden"):
                return self._set_hidden_keys(keys, True)
            pending = [k for k in keys if not src.is_table_hidden(k)]
            on = bool(pending)
            want = pending if on else [k for k in keys if src.is_table_hidden(k)]
            done = [k for k in want if src.set_table_hidden(k, on)]
            if not done:
                return False

            def apply(h: bool) -> None:
                for k in done:
                    src.set_table_hidden(k, h)
                    self.model.refresh_key(k)
                self.model.statsChanged.emit()
            for k in done:
                self.model.refresh_key(k)
            self.model.statsChanged.emit()
            n = len(done)
            self.stack.push(Command(f"{n} nicht exportierte Spalte(n) in der Tabelle " + ("ausblenden" if on else "einblenden"),
                                    lambda: apply(on), lambda: apply(not on)), execute=False)
            self.undoChanged.emit()
            return True
        if area == 2:
            return self._set_hidden_keys([k for k in self.model.keys() if src.is_hidden(k)], False)
        return False

    def _without_protected(self, keys: list[str]) -> list[str]:
        """Rule: the DCF index (PnPID) can never be hidden. Says so once if it was among the keys."""
        ok = [k for k in keys if not self.model.is_protected(k)]
        if len(ok) < len(keys):
            self.message.emit(PROT.PROTECTED_NOTE)
        return ok

    def _set_hidden_keys(self, keys: list[str], hidden: bool) -> bool:
        if hidden:
            keys = self._without_protected(keys)
        if not keys:
            return False
        src = self.model.source
        want = [k for k in keys if src.is_hidden(k) != hidden]
        done: list[str] = []
        for k in want:
            if src.set_hidden(k, hidden):
                done.append(k)
                self.model.refresh_key(k)
        if len(done) < len(want):
            self.message.emit("Die letzte sichtbare Spalte kann nicht ausgeblendet werden." if len(keys) == 1 else "Mindestens eine Spalte muss sichtbar bleiben.")
        if not done:
            return False

        def apply(h: bool) -> None:
            for k in done:
                src.set_hidden(k, h)
                self.model.refresh_key(k)
        n = len(done)
        self.stack.push(Command(("Spalte ausblenden" if hidden else "Spalte einblenden") + ("" if n == 1 else f" ({n} Spalten)"),
                                lambda: apply(hidden), lambda: apply(not hidden)), execute=False)
        self.undoChanged.emit()
        return True

    @Slot(int, result=bool)
    def toggleExport(self, row: int) -> bool:
        """Include / exclude the tile, or all tiles of the multi selection (exclude unless none is included any more)."""
        keys = [k for k in self._targets(row) if self.model.definition(k) is not None]
        if not keys:
            return False
        exclude = any(self.model.definition(k).include_in_export for k in keys)
        want = [k for k in keys if self.model.definition(k).include_in_export == exclude]

        def apply(on: bool) -> None:
            for k in want:
                d = self.model.definition(k)                                  # looked up again: undo may have replaced the objects
                if d is not None:
                    d.include_in_export = on
                    self.model.source.set_export_excluded(k, not on)
                self.model.refresh_key(k)
        n = len(want)
        self._run(("Nicht exportieren" if exclude else "Exportieren") + ("" if n == 1 else f" ({n} Spalten)"),
                  lambda: apply(not exclude), lambda: apply(exclude))
        return True

    @Slot(int, bool, result=bool)
    def setExport(self, row: int, include: bool) -> bool:
        """Put the tile (or every tile of the multi selection) into the exported area (`include`) or the 'not exported' area.
        Drag and drop between the two areas of the tile editor uses this; one undo step."""
        keys = [k for k in self._targets(row) if self.model.definition(k) is not None]
        want = [k for k in keys if self.model.definition(k).include_in_export != include]
        if not want:
            return False

        def apply(on: bool) -> None:
            for k in want:
                d = self.model.definition(k)                                  # looked up again: undo may have replaced the objects
                if d is not None:
                    d.include_in_export = on
                    self.model.source.set_export_excluded(k, not on)
                self.model.refresh_key(k)
        n = len(want)
        self._run(("Exportieren" if include else "Nicht exportieren") + ("" if n == 1 else f" ({n} Spalten)"),
                  lambda: apply(include), lambda: apply(not include))
        return True

    @Slot(int, result=bool)
    def exportedAt(self, row: int) -> bool:
        """True when the tile of `row` is in the exported area (False = 'not exported' area; also False for an invalid row)."""
        key = self._key(row)
        d = self.model.definition(key) if key is not None else None
        return bool(d.include_in_export) if d is not None else key is not None

    @Slot(int, int, result=int)
    def neighbour(self, row: int, step: int) -> int:
        """Keyboard navigation inside one area: the row `step` tiles further among the tiles of the same area
        (Exported / Not exported / Hidden are three separate lists). Stays on `row` at the ends of the list."""
        keys = self.model.keys()
        if not (0 <= row < len(keys)):
            return row
        src = self.model.source
        def area(k: str) -> int:
            if src.is_hidden(k):
                return 2
            d = self.model.definition(k)
            return 0 if (d is None or d.include_in_export) else 1
        same = [i for i, k in enumerate(keys) if area(k) == area(keys[row])]
        at = same.index(row)
        return same[max(0, min(len(same) - 1, at + step))]

    def set_tag_color_provider(self, provider) -> None:
        """Host: callable returning {tag type: '#RRGGBB'} (project definitions > Tag structures)."""
        self.model.set_tag_color_provider(provider)

    # --- naming -----------------------------------------------------------------------------------------------------------
    @Slot(int, str, result=str)
    def renameOutput(self, row: int, name: str) -> str:
        key, name = self._key(row), name.strip()
        if key and self.model.is_temporary(key):
            return "Eine temporäre Spalte kann nicht umbenannt werden."
        d = self.model.definition(key) if key else None
        if d is None:
            return "Keine Spalte gewählt."
        if not name:
            return "Der Name ist leer."
        old = self.model.source.label(key)
        if name == old:
            return ""
        if not self.model.source.set_label(key, name):
            return "Diese Spalte kann nicht umbenannt werden."

        def apply(text: str) -> None:
            self.model.source.set_label(key, text)
            d.output_name = text
            self.model.refresh_key(key)
            self.model.statsChanged.emit()
        d.output_name = name
        self.model.refresh_row(row)
        self.model.statsChanged.emit()
        self.stack.push(Command("Ausgabespalte umbenennen", lambda: apply(name), lambda: apply(old)), execute=False)
        self.undoChanged.emit()
        return ""

    @Slot(int, result=int)
    def columnWidth(self, row: int) -> int:
        """Width (px) of the column in the table below; 0 when the source cannot tell."""
        key = self._key(row)
        f = getattr(self.model.source, "column_width", None)
        return int(f(key)) if key and f else 0

    @Slot(int, int, result=str)
    def setColumnWidth(self, row: int, width: int) -> str:
        """Set the width of the column in the table (one undo step). The table's owner remembers it as the default width."""
        key = self._key(row)
        src = self.model.source
        if not key or not hasattr(src, "set_column_width"):
            return "Diese Tabelle kann die Spaltenbreite nicht ändern."
        old, width = int(src.column_width(key)), max(30, min(1200, int(width)))
        if old == width:
            return ""
        src.set_column_width(key, width)
        self.stack.push(Command("Spaltenbreite", lambda: src.set_column_width(key, width), lambda: src.set_column_width(key, old)),
                        execute=False)
        self.undoChanged.emit()
        return ""

    @Slot(int, result="QVariantMap")
    def tagInfo(self, row: int) -> dict:
        """Colour category of the column (project definitions > Tag structures): {tag, color}; empty when there is none."""
        key = self._key(row)
        tag, color = self.model.tag_info(key) if key else ("", "")
        return {"tag": tag or "", "color": color or ""}

    @Slot(result=int)
    def undoDepth(self) -> int:
        """Number of undo steps made so far (the back side of a tile remembers it to offer "Cancel changes")."""
        return len(self.stack._done)

    @Slot(int, result=int)
    def undoTo(self, depth: int) -> int:
        """Undo steps until only `depth` are left. Returns how many were undone."""
        n = 0
        while len(self.stack._done) > depth and self.stack.can_undo():
            self.undo()
            n += 1
        return n

    @Slot(int, str, result=str)
    def setShortName(self, row: int, name: str) -> str:
        key = self._key(row)
        d = self.model.definition(key) if key else None
        if d is None:
            return "Keine Spalte gewählt."
        old, new = d.short_name, name.strip()

        def apply(text: str) -> None:
            d.short_name = text
            self.model.refresh_key(key)
        self._run("Kurzname der Kachel ändern", lambda: apply(new), lambda: apply(old))
        return ""

    @Slot(int, result=bool)
    def resetColumn(self, row: int) -> bool:
        """Back to the source for the tile or the whole multi selection: no convert node, original label, full name, shown and exported."""
        keys = [k for k in self._targets(row) if self.model.definition(k) is not None]
        if not keys:
            return False
        src = self.model.source
        before_cfg = self.model.config.to_dict()
        before = {k: (src.label(k), src.is_hidden(k)) for k in keys}

        def finish() -> None:
            for k in keys:
                self.model.refresh_key(k)
            self.selectedChanged.emit()

        def redo() -> None:
            for k in keys:
                d = self.model.definition(k)
                if d is None:
                    continue
                try:
                    self.model.config.set_output_type(d.column_id, d.source_type)
                except ConvertError:
                    pass
                d.include_in_export, d.short_name = True, ""
                src.set_label(k, src.original_label(k))
                src.set_hidden(k, False)
                src.set_export_excluded(k, False)
            finish()

        def undo() -> None:
            self.model.restore_config(before_cfg)
            for k in keys:
                label, hidden = before[k]
                src.set_label(k, label)
                src.set_hidden(k, hidden)
                dd = self.model.definition(k)
                src.set_export_excluded(k, not (dd.include_in_export if dd else True))
            finish()
        self._run("Spalte zurücksetzen" + ("" if len(keys) == 1 else f" ({len(keys)} Spalten)"), redo, undo)
        return True

    # --- undo / redo -----------------------------------------------------------------------------------------------------
    @Slot()
    def undo(self) -> None:
        if self.stack.undo():
            self.undoChanged.emit()

    @Slot()
    def redo(self) -> None:
        if self.stack.redo():
            self.undoChanged.emit()

    canUndo = Property(bool, lambda self: self.stack.can_undo(), notify=undoChanged)
    canRedo = Property(bool, lambda self: self.stack.can_redo(), notify=undoChanged)
    undoText = Property(str, lambda self: self.stack.undo_text(), notify=undoChanged)
    redoText = Property(str, lambda self: self.stack.redo_text(), notify=undoChanged)

    # --- selection ----------------------------------------------------------------------------------------------------------
    def _publish_selection(self) -> None:
        order = {k: i for i, k in enumerate(self._multi, start=1)} if len(self._multi) > 1 else {}
        self.model.set_selection_order(order)
        self.selectedChanged.emit()

    @Slot(int)
    def select(self, row: int) -> None:
        """Keep the active tile in sync with the grid's current item (does not touch a multi selection)."""
        row = row if 0 <= row < self.model.rowCount() else -1
        if row == self._selected:
            return
        self._selected = row
        key = self._key(row)
        self._multi = [key] if key else []
        self._publish_selection()

    @Slot(int)
    def selectOnly(self, row: int) -> None:
        """Plain click: this tile is the only selected one."""
        self._selected = row if 0 <= row < self.model.rowCount() else -1
        key = self._key(self._selected)
        self._multi = [key] if key else []
        self._anchor = key
        self._publish_selection()

    @Slot(int, bool)
    def selectRange(self, row: int, additive: bool = False) -> None:
        """Shift+Click: every tile from the anchor (last plain / Ctrl click) to this tile, in the order of the grid like in Windows.
        With `additive` (Shift+Ctrl) the range is added to what is already selected."""
        key = self._key(row)
        if key is None:
            return
        keys = self.model.keys()
        anchor = getattr(self, "_anchor", None)
        if anchor not in keys:
            anchor = keys[self._selected] if 0 <= self._selected < len(keys) else key
        a, b = sorted((keys.index(anchor), row))
        rng = keys[a:b + 1]
        self._multi = ([k for k in self._multi if k not in rng] + rng) if additive else rng
        self._selected = row
        self._anchor = anchor
        self._publish_selection()
        if self._draft is not None:                    # open group: Shift+Click adds the whole range to it
            self._draft_add(rng)

    def _draft_add(self, keys: list[str]) -> None:
        new = [k for k in keys if k not in self._draft["keys"]]
        if new:
            self._draft["keys"].extend(new)
            self._auto_target(self._draft)
            self._emit_draft()

    @Slot(int)
    def toggleSelect(self, row: int) -> None:
        """Ctrl+Click: add / remove a tile; the order of clicking is the order of the badges."""
        key = self._key(row)
        if key is None:
            return
        if key in self._multi:
            self._multi.remove(key)
            keys = self.model.keys()
            self._selected = keys.index(self._multi[-1]) if self._multi else -1
        else:
            self._multi.append(key)
            self._selected = row
        self._anchor = key
        self._publish_selection()
        if self._draft is not None:                    # open group: Ctrl+Click adds the tile to it / takes it out again
            if key in self._multi:
                self._draft_add([key])
            elif key in self._draft["keys"]:
                self._draft["keys"].remove(key)
                self._auto_target(self._draft)
                self._emit_draft()

    @Slot()
    def clearSelection(self) -> None:
        self._selected, self._multi = -1, []
        self._publish_selection()

    def select_key(self, key: str) -> bool:
        """The table's current column changed (click in the table): make its tile the active one. A multi selection that
        already contains the tile is kept. False = no tile for this column (e.g. a display-only column)."""
        keys = self.model.keys()
        if key not in keys:
            return False
        row = keys.index(key)
        if row == self._selected or (key in self._multi and len(self._multi) > 1):
            return True
        self.selectOnly(row)
        return True

    @Slot(str)
    def setSearch(self, text: str) -> None:
        """Search field above the tiles: show only the matching tiles; the first match becomes the active tile (the table
        below jumps to that column)."""
        self.model.set_search(text)
        rows = self.model.match_rows() if self.model.searchText else []
        if rows and self._selected not in rows:
            self.selectOnly(rows[0])

    @Slot(int)
    def searchStep(self, step: int) -> None:
        """Enter / Down = next match, Shift+Enter / Up = previous match (wraps around)."""
        rows = self.model.match_rows()
        if not rows:
            return
        if self._selected in rows:
            nxt = rows[(rows.index(self._selected) + step) % len(rows)]
        else:
            nxt = rows[0] if step >= 0 else rows[-1]
        self.selectOnly(nxt)

    selectedRow = Property(int, lambda self: self._selected, notify=selectedChanged)
    selectionCount = Property(int, lambda self: len(self._multi), notify=selectedChanged)

    # --- inspector -----------------------------------------------------------------------------------------------------------
    @Slot(int, result="QVariantMap")
    def inspect(self, row: int) -> dict:
        """Texts for the inspector (D9): names, types, detection source, confidence, sample, null count, steps."""
        key = self._key(row)
        if key is None:
            return {}
        src = self.model.source
        d = self.model.definition(key)
        out: dict = {"label": src.label(key), "key": key, "visible": not src.is_hidden(key),
                     "calculated": self.model.is_calculated(key), "originalName": src.original_label(key)}
        if d is None:
            return out
        values = src.samples(key)
        non_empty = [v for v in values if not is_empty(v)]
        out.update(sourceName=d.source_name if not out["calculated"] else "(calculated)", outputName=src.label(key),
                   shortName=self.model.tile_name(key), sourceTypeName=TYPE_NAMES.get(d.source_type, d.source_type.value),
                   outputTypeName=TYPE_NAMES.get(d.output_type, d.output_type.value), sampleValue=str(non_empty[0]) if non_empty else "",
                   nullCount=len(values) - len(non_empty), inExport=d.include_in_export, steps=self._steps(d, key))
        td = d.type_detection
        if td is not None:
            typ, origin, conf = td.describe(d.detected_type)
            out.update(detected=typ, source=origin, confidence=conf, sourceType=d.source_type.value,
                       outputType=d.output_type.value, override=td.override, invalid=td.invalid_values,
                       samples=td.sample_non_empty, suggested=td.suggested_type.value if td.suggested_type else "")
        return out

    def _column_stats(self, key: str) -> dict:
        """rows / filled / empty / different values of the whole column; cached for 30 s because the hover asks often."""
        now = time.monotonic()
        hit = self._stat_cache.get(key)
        if hit and now - hit[0] < 30:
            return hit[1]
        src = self.model.source
        values = src.column_values(key) if hasattr(src, "column_values") else src.samples(key)
        filled = [v for v in values if not is_empty(v)]
        stats = {"rows": len(values), "filled": len(filled), "empty": len(values) - len(filled), "distinct": len({str(v) for v in filled}),
                 "example": str(filled[0]) if filled else ""}
        self._stat_cache[key] = (now, stats)
        return stats

    @Slot(int, result=str)
    def tileTip(self, row: int) -> str:
        """Hover text of a tile: full column name, type, number of elements, function (as far as there is one), state."""
        key = self._key(row)
        if key is None:
            return ""
        src, d = self.model.source, self.model.definition(key)
        lines = [src.label(key)]
        if src.label(key) != src.original_label(key):
            lines.append(f"Umbenannt – Originalname: {src.original_label(key)}  (nur Anzeige, die Daten bleiben unverändert)")
        if d is not None:
            out, srct = TYPE_NAMES.get(d.output_type, d.output_type.value), TYPE_NAMES.get(d.source_type, d.source_type.value)
            lines.append(f"Type: {out}" + (f"  (source: {srct})" if d.output_type != d.source_type else ""))
        st = self._column_stats(key)
        lines.append(f"Werte: {st['rows']:,} Zeilen  ·  {st['filled']:,} gefüllt  ·  {st['empty']:,} leer  ·  {st['distinct']:,} verschiedene")
        steps = self._steps(d, key) if d is not None else []
        calc = self.model.is_calculated(key) or bool(d and d.calculated)
        if calc and not steps:
            steps = ["Berechnete Spalte"]
        if steps:
            lines.append("Function: " + "; ".join(steps))
        else:
            lines.append("Funktion: keine – Werte wie in der Quelle")
        if d is not None and not calc and d.source_name != src.label(key):
            lines.append(f"Quellspalte: {d.source_name}")
        if st["example"]:
            ex = st["example"].replace("\n", " ")
            lines.append("Example: " + (ex if len(ex) <= 48 else ex[:45] + "..."))
        tag, color = self.model.tag_info(key)
        if tag:
            lines.append(f"Farbkategorie: {tag} ({color})")
        flags = []
        if src.is_hidden(key):
            flags.append("hidden")
        if d is not None and not d.include_in_export:
            flags.append("nicht exportiert")
        if src.label(key) != src.original_label(key):
            flags.append("renamed")
        if len(self._multi) > 1 and key in self._multi:
            flags.append(f"gewählt mit {len(self._multi) - 1} weiteren Kachel(n)")
        if flags:
            lines.append("State: " + ", ".join(flags))
        return "\n".join(lines)

    def _steps(self, d: ColumnDefinition, key: str) -> list[str]:
        steps: list[str] = []
        for n in self.model.config.nodes:
            if n.operation == "convert" and n.input_ids == (d.column_id,):
                p = ConvertParameters.from_dict(n.parameters)
                fmt = f" ({p.date_format})" if p.date_format else ""
                steps.append(f"Umwandeln {TYPE_NAMES.get(p.from_type)} → {TYPE_NAMES.get(p.to_type)}{fmt}")
            elif n.operation == "join" and n.parameters.get("output_key") == key:
                names = " + ".join(str(x) for x in n.parameters.get("input_names") or ())
                steps.append(f"Verbinden {names}, Trennzeichen '{n.parameters.get('separator', '')}'")
            elif D.is_derived(n) and n.operation != "join" and D.output_key(n) == key:
                try:
                    steps.append(D.describe(n, self._label_of))
                except Exception:  # noqa: BLE001
                    steps.append(n.operation)
        return steps


    # --- calculated columns: shared helpers -----------------------------------------------------------------------------------
    class _Ids:
        """Hands out node / column ids that are free in the config and not yet given to another job of the same command."""
        def __init__(self, cfg):
            self.cfg, self.used = cfg, set()

        def next(self, prefix: str) -> str:
            taken = {n.node_id for n in self.cfg.nodes} | {n.output.column_id for n in self.cfg.nodes} | self.used
            i = 1
            while f"{prefix}{i:02d}" in taken:
                i += 1
            self.used.add(f"{prefix}{i:02d}")
            return f"{prefix}{i:02d}"

    def _label_of(self, key: str) -> str:
        return self.model.source.label(key) if key in self.model.keys() else key

    def _get(self, key: str) -> list:
        return self.model.source.column_values(key or self.model.keys()[0])      # "" = any column (index column: row count only)

    def _free_label(self, base: str, taken: set) -> str:
        label, n = base, 2
        while label in taken:
            label, n = f"{base} {n}", n + 1
        taken.add(label)
        return label

    def _commit(self, specs: list, text: str, original_keys: list, replace_original: bool, note: str) -> str:
        """Create the calculated columns of `specs` (one undo step). spec = {node, label, values, after (key of the tile it is
        placed behind)}. With `replace_original` the input tiles in `original_keys` are hidden and left out of the export.
        Returns '' or a readable error; on an error nothing changes."""
        model, src, cfg = self.model, self.model.source, self.model.config
        before_cfg = cfg.to_dict()
        was_hidden = {k: src.is_hidden(k) for k in original_keys}

        def redo() -> None:
            for sp in specs:
                key = D.output_key(sp["node"])
                if not src.add_derived(key, sp["label"], sp["values"]):
                    raise RuntimeError("diese Tabelle kann keine berechneten Spalten aufnehmen")
                if sp["node"] not in cfg.nodes:
                    cfg.nodes.append(sp["node"])
                after = sp["after"] if sp["after"] in model.keys() else model.keys()[-1]
                at = 0 if sp["after"] == "" else model.keys().index(after) + 1          # "" = first column
                model.add_calculated(key, at, sp["node"].output.column_id, sp["label"])
            if replace_original:
                for k in original_keys:
                    src.set_hidden(k, True)
                    src.set_export_excluded(k, True)
                    dd = model.definition(k)
                    if dd:
                        dd.include_in_export = False
                    model.refresh_key(k)

        def undo() -> None:
            for sp in reversed(specs):
                key = D.output_key(sp["node"])
                model.remove_calculated(key)
                src.remove_derived(key)
            model.restore_config(before_cfg)
            for k in original_keys:
                src.set_hidden(k, was_hidden[k])
                src.set_export_excluded(k, False)
                model.refresh_key(k)
        try:
            redo()
        except RuntimeError as e:
            undo()
            return str(e)
        self.stack.push(Command(text, redo, undo), execute=False)
        self._multi = []
        self._selected = model.keys().index(D.output_key(specs[-1]["node"]))
        self._publish_selection()
        self.undoChanged.emit()
        if note:
            self.message.emit(note)
        return ""

    # --- text functions (Transform / Replace / Format / Fill / Extract): one calculated column per input column ------------------
    @Slot(result="QVariantList")
    def textOps(self) -> list:
        """The functions of the Transform menu: id, label, one-line help, needs a dialog."""
        return [{"op": k, "label": v[0], "help": v[1], "dialog": v[3]} for k, v in TO.OPS.items()]

    @staticmethod
    def _tparams(op: str, options: dict) -> TO.TextOpParameters:
        def num(k: str) -> int:
            try:
                return max(0, int(options.get(k) or 0))
            except (TypeError, ValueError):
                return 0
        return TO.TextOpParameters(
            op=op, find=str(options.get("find") or ""), replace_with=str(options.get("replaceWith") or ""),
            whole_cell=bool(options.get("wholeCell", False)), match_case=bool(options.get("matchCase", False)),
            prefix=str(options.get("prefix") or ""), suffix=str(options.get("suffix") or ""), pad_width=num("padWidth"),
            bare_numbers="dn" if str(options.get("bareNumbers")) == "dn" else "inch", number=num("number"), start=num("start"),
            find2=str(options.get("find2") or ""), start_row=num("startRow"))

    @staticmethod
    def _toptions(p: TO.TextOpParameters) -> dict:
        """Parameters back into the dialog's option names (edit a step)."""
        return {"find": p.find, "replaceWith": p.replace_with, "wholeCell": p.whole_cell, "matchCase": p.match_case,
                "prefix": p.prefix, "suffix": p.suffix, "padWidth": p.pad_width, "bareNumbers": p.bare_numbers,
                "number": p.number, "start": p.start, "find2": p.find2, "startRow": p.start_row}

    @Slot(int, str, "QVariantMap", result="QVariantMap")
    def previewTextOp(self, row: int, op: str, options: dict) -> dict:
        """Before -> After of the first changing cells of the tile (sampled rows) and the counts, for the dialog."""
        key = self._key(row)
        if key is None:
            return {"ok": False, "error": "Keine Spalte gewählt.", "rows": [], "changed": 0, "total": 0, "unrecognised": 0}
        res = TO.preview(self.model.source.samples(key), self._tparams(op, options))
        res["label"] = self.model.source.label(key)
        res["targets"] = len(self._targets(row))
        return res

    def _text_spec(self, key: str, p: TO.TextOpParameters, ids, taken: set, replace_original: bool, after: str | None = None) -> dict:
        model, cfg = self.model, self.model.config
        d = model.definition(key)
        if d is None:
            raise TO.TextOpError("Keine Spalte gewählt.")
        p = replace(p, source_key=key, replaced_original=replace_original)
        label = self._free_label(TO.new_column_name(self.model.source.label(key), p), taken)
        out_id = ids.next("x")
        p = replace(p, output_key=f"calc_{out_id}")
        node = TO.build_text_node(node_id=ids.next("n"), input_id=d.column_id, out_id=out_id, out_name=label, params=p)
        before = self._get(key)
        values = TO.apply_column(before, p)
        return {"node": node, "label": label, "values": values, "after": after or key, "changed": TO.changed_count(before, values)}

    @Slot(int, str, "QVariantMap", result=str)
    def applyTextOp(self, row: int, op: str, options: dict) -> str:
        """Run the function on the tile or on every tile of the multi selection. Each input gets a calculated column
        (green tile, 'name (suffix)'); with `replaceOriginal` the original is hidden and left out of the export.
        One undo step. Returns '' or a readable error; on an error nothing changes."""
        keys = self._targets(row)
        if not keys:
            return "Keine Spalte gewählt."
        params = self._tparams(op, options)
        if op == "fill_from":
            params = replace(params, start_row=self._source_row(row, options))
        err = TO.validate(params)
        if err:
            return err
        replace_original = bool(options.get("replaceOriginal", True))
        ids, taken = self._Ids(self.model.config), {self.model.source.label(k) for k in self.model.keys()}
        specs = []
        try:
            for k in keys:
                specs.append(self._text_spec(k, params, ids, taken, replace_original))
        except TO.TextOpError as e:
            return str(e)
        changed = sum(sp["changed"] for sp in specs)
        if changed == 0 and op not in TO.FILL_OPS and op != "duplicate":
            return "Es würde sich nichts ändern: keine Zelle ist betroffen."
        n = len(keys)
        return self._commit(specs, TO.OPS[op][0] + ("" if n == 1 else f" ({n} Spalten)"), keys, replace_original,
                            f"{TO.OPS[op][0]}: neue Spalte {', '.join(sp['label'] for sp in specs)}." if op == "duplicate"
                            else f"{TO.OPS[op][0]}: {changed:,} Zellen geändert. Neue Spalte: {', '.join(sp['label'] for sp in specs)}.")

    def _source_row(self, row: int, options: dict) -> int:
        try:
            return max(0, int(options.get("startRow") or 0))
        except (TypeError, ValueError):
            return 0

    # --- split into several columns ------------------------------------------------------------------------------------------------
    @staticmethod
    def _split_lengths(text: str) -> list:
        out = []
        for part in str(text or "").replace(";", ",").split(","):
            part = part.strip()
            if part.isdigit() and int(part) > 0:
                out.append(int(part))
        return out

    def _split_params(self, options: dict, count_hint: list) -> list:
        """One TextOpParameters per new column (the modes of Power Query's "Split column"). mode 'delimiter' (separator + number
        of parts, 0 = as many as the data has), 'fixed' (comma separated lengths, e.g. 3,2,3), 'count' (every N characters),
        'positions' (comma separated 0-based start positions, e.g. 0,3,5) or a TO.TRANSITIONS key (change of character type)."""
        mode = str(options.get("mode") or "delimiter")
        if mode == "fixed":
            pos, out = 1, []
            for i, ln in enumerate(self._split_lengths(options.get("lengths"))):
                out.append(TO.TextOpParameters("split_fixed", start=pos, number=ln, part_label=f"part {i + 1}"))
                pos += ln
            return out
        if mode == "count":
            try:
                size = int(options.get("size") or 0)
            except (TypeError, ValueError):
                size = 0
            if size < 1:
                return []
            longest = max((len(str(v)) for v in count_hint if str(v or "").strip()), default=1)
            n = max(1, min(24, -(-longest // size)))
            return [TO.TextOpParameters("split_fixed", start=i * size + 1, number=size, part_label=f"part {i + 1}") for i in range(n)]
        if mode == "positions":
            starts = []
            for part in str(options.get("positions") or "").replace(";", ",").split(","):
                part = part.strip()
                if part.isdigit() and int(part) not in starts:
                    starts.append(int(part))
            starts.sort()
            return [TO.TextOpParameters("split_fixed", start=s + 1, number=(starts[i + 1] - s) if i + 1 < len(starts) else 100000,
                                        part_label=f"part {i + 1}") for i, s in enumerate(starts[:24])]
        if mode in TO.TRANSITIONS:
            n = TO.transition_parts(count_hint, mode)
            return [TO.TextOpParameters("split_transition", find=mode, number=i + 1, part_label=f"part {i + 1}") for i in range(n)]
        delim = str(options.get("find") or "")
        try:
            n = int(options.get("parts") or 0)
        except (TypeError, ValueError):
            n = 0
        n = n if n > 0 else TO.split_parts(count_hint, delim)
        return [TO.TextOpParameters("split_part", find=delim, number=i + 1, part_label=f"part {i + 1}") for i in range(min(n, 24))]

    @Slot(int, "QVariantMap", result="QVariantMap")
    def previewSplit(self, row: int, options: dict) -> dict:
        key = self._key(row)
        if key is None:
            return {"ok": False, "error": "Keine Spalte gewählt.", "rows": [], "parts": 0}
        sample = self.model.source.samples(key)
        plist = self._split_params(options, sample)
        if not plist:
            return {"ok": False, "error": "Einstellungen der gewählten Teilung ausfüllen (Trennzeichen, Längen wie 3,2,3, Anzahl Zeichen oder Positionen wie 0,3,5).", "rows": [], "parts": 0,
                    "label": self.model.source.label(key)}
        err = TO.validate(plist[0])
        if err:
            return {"ok": False, "error": err, "rows": [], "parts": len(plist), "label": self.model.source.label(key)}
        rows = []
        for v in sample:
            if is_empty(v):
                continue
            rows.append({"before": str(v), "after": "  |  ".join(TO.apply_value(v, p) for p in plist)})
            if len(rows) >= 5:
                break
        return {"ok": True, "error": "", "rows": rows, "parts": len(plist), "label": self.model.source.label(key),
                "changed": len(plist), "total": len(sample), "unrecognised": 0}

    @Slot(int, "QVariantMap", result=str)
    def applySplit(self, row: int, options: dict) -> str:
        key = self._key(row)
        if key is None:
            return "Keine Spalte gewählt."
        plist = self._split_params(options, self.model.source.samples(key))
        if not plist:
            return "Einstellungen der gewählten Teilung ausfüllen (Trennzeichen, Längen wie 3,2,3, Anzahl Zeichen oder Positionen wie 0,3,5)."
        for p in plist:
            err = TO.validate(p)
            if err:
                return err
        replace_original = bool(options.get("replaceOriginal", True))
        ids, taken = self._Ids(self.model.config), {self.model.source.label(k) for k in self.model.keys()}
        specs, after = [], key
        try:
            for p in plist:
                sp = self._text_spec(key, p, ids, taken, replace_original, after)
                specs.append(sp)
                after = D.output_key(sp["node"])
        except TO.TextOpError as e:
            return str(e)
        return self._commit(specs, f"In {len(specs)} Spalten teilen", [key], replace_original,
                            f"'{self.model.source.label(key)}' in {len(specs)} Spalten geteilt.")

    # --- If ... then ... (conditional column) ---------------------------------------------------------------------------------------
    @Slot(result="QVariantList")
    def columnChoices(self) -> list:
        src = self.model.source
        return [{"key": k, "label": src.label(k)} for k in self.model.keys()]

    @Slot(result="QVariantList")
    def conditionOperators(self) -> list:
        return [{"key": k, "label": v, "noValue": k in CO.NO_VALUE_OPERATORS} for k, v in CO.OPERATORS]

    @staticmethod
    def _cparams(spec: dict, output_key: str = "") -> CO.ConditionalParameters:
        rules = tuple(CO.Rule(str(r.get("column") or ""), str(r.get("operator") or "equals"), str(r.get("value") or ""),
                              str(r.get("result") or ""), str(r.get("resultColumn") or "")) for r in (spec.get("rules") or ()))
        return CO.ConditionalParameters(rules, str(spec.get("elseValue") or ""), str(spec.get("elseColumn") or ""),
                                        bool(spec.get("ignoreCase", True)), output_key)

    @staticmethod
    def _cspec(p: CO.ConditionalParameters) -> dict:
        return {"rules": [{"column": r.column, "operator": r.operator, "value": r.value, "result": r.result,
                           "resultColumn": r.result_column} for r in p.rules],
                "elseValue": p.else_value, "elseColumn": p.else_column, "ignoreCase": p.ignore_case}

    @Slot("QVariantMap", result="QVariantMap")
    def previewConditional(self, spec: dict) -> dict:
        p = self._cparams(spec)
        err = CO.validate(p)
        if err:
            return {"ok": False, "error": err, "rows": [], "counts": []}
        src = self.model.source
        res = CO.compute(p, lambda k: src.samples(k))
        first = p.rules[0].column
        base = src.samples(first)
        rows = [{"before": f"{self._label_of(first)}: {base[i] if i < len(base) else ''}", "after": res[i]} for i in range(min(5, len(res)))]
        counts: dict = {}
        for v in res:
            counts[v] = counts.get(v, 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:4]
        return {"ok": True, "error": "", "rows": rows, "counts": [f"{k or '(empty)'}: {n:,}" for k, n in top]}

    @Slot(str, "QVariantMap", result=str)
    def applyConditional(self, name: str, spec: dict) -> str:
        model, src, cfg = self.model, self.model.source, self.model.config
        p = self._cparams(spec)
        err = CO.validate(p)
        if err:
            return err
        name = name.strip()
        if not name:
            return "Der Name der Zielspalte ist leer."
        if any(src.label(k) == name for k in model.keys()):
            return f"Eine Spalte '{name}' gibt es schon."
        used = p.keys_used()
        defs = [model.definition(k) for k in used]
        if any(d is None for d in defs):
            return "Eine Spalte einer Regel gibt es nicht."
        ids = self._Ids(cfg)
        out_id = ids.next("x")
        p = replace(p, output_key=f"calc_{out_id}")
        try:
            node = CO.build_node(node_id=ids.next("n"), input_ids=tuple(d.column_id for d in defs), out_id=out_id, out_name=name, params=p)
        except CO.ConditionalError as e:
            return str(e)
        after = max(used, key=lambda k: model.keys().index(k) if k in model.keys() else -1)
        spec_ = {"node": node, "label": name, "values": CO.compute(p, self._get), "after": after}
        return self._commit([spec_], "Wenn-dann-Spalte", [], False, f"Neue Spalte '{name}' aus {len(p.rules)} Regel(n).")

    # --- add columns from another list (lookup) ----------------------------------------------------------------------------------------
    def _lparams(self, key: str, options: dict, take: str) -> LK.LookupParameters:
        return LK.LookupParameters(str(options.get("file") or ""), str(options.get("sheet") or ""), key,
                                   str(options.get("matchLabel") or ""), take, bool(options.get("matchCase", False)),
                                   str(options.get("missingText") or ""))

    @Slot(int, "QVariantMap", result="QVariantMap")
    def previewLookup(self, row: int, options: dict) -> dict:
        key = self._key(row)
        takes = [str(t) for t in (options.get("takeLabels") or ())]
        if key is None or not takes:
            return {"ok": False, "error": "Zu übernehmende Spalte(n) wählen.", "rows": [], "found": 0, "total": 0}
        try:
            p = self._lparams(key, options, takes[0])
            err = LK.validate(p)
            if err:
                return {"ok": False, "error": err, "rows": [], "found": 0, "total": 0}
            sample = self.model.source.samples(key)
            res = LK.compute(p, lambda _k: sample)
        except LK.LookupError_ as e:
            return {"ok": False, "error": str(e), "rows": [], "found": 0, "total": 0}
        rows = [{"before": str(a), "after": b} for a, b in zip(sample, res) if str(a).strip()][:5]
        found = sum(1 for a, b in zip(sample, res) if str(a).strip() and b != p.missing_text)
        return {"ok": True, "error": "", "rows": rows, "found": found, "total": sum(1 for a in sample if str(a).strip())}

    @Slot(int, "QVariantMap", result=str)
    def applyLookup(self, row: int, options: dict) -> str:
        key = self._key(row)
        d = self.model.definition(key) if key else None
        takes = [str(t) for t in (options.get("takeLabels") or ())]
        if d is None or not takes:
            return "Zu übernehmende Spalte(n) wählen."
        ids, taken = self._Ids(self.model.config), {self.model.source.label(k) for k in self.model.keys()}
        specs, after = [], key
        try:
            for t in takes:
                p = self._lparams(key, options, t)
                label = self._free_label(t, taken)
                out_id = ids.next("x")
                p = replace(p, output_key=f"calc_{out_id}")
                node = LK.build_node(node_id=ids.next("n"), input_id=d.column_id, out_id=out_id, out_name=label, params=p)
                specs.append({"node": node, "label": label, "values": LK.compute(p, self._get), "after": after})
                after = p.output_key
        except LK.LookupError_ as e:
            return str(e)
        return self._commit(specs, "Spalten aus einer anderen Liste", [], False,
                            f"Hinzugefügt: {', '.join(sp['label'] for sp in specs)} aus {Path(str(options.get('file'))).name}.")

    # --- index column (Add column tab): running number, always the FIRST column ------------------------------------------------------
    @Slot(str, int, int, int, result=str)
    def addIndexColumn(self, name: str, start: int, step: int, digits: int = 0) -> str:
        """Insert a calculated column "Pos." (digits: leading zeros, 0 = automatic) as the first column: start, start + step, start + 2 * step ... (one undo step).
        Returns '' or a readable error."""
        model, src, cfg = self.model, self.model.source, self.model.config
        if not model.keys():
            return "Es gibt keine Tabelle."
        p = IX.IndexParameters(int(start), int(step), digits=max(0, int(digits)))
        err = IX.validate(p)
        if err:
            return err
        ids, taken = self._Ids(cfg), {src.label(k) for k in model.keys()}
        label = self._free_label((name or IX.DEFAULT_NAME).strip() or IX.DEFAULT_NAME, taken)
        out_id = ids.next("x")
        p = replace(p, output_key=f"calc_{out_id}")
        node = IX.build_node(node_id=ids.next("n"), out_id=out_id, out_name=label, params=p)
        values = IX.compute(p, len(self._get("")))
        return self._commit([{"node": node, "label": label, "values": values, "after": ""}], "Indexspalte hinzufügen", [], False,
                            f"Indexspalte '{label}' als erste Spalte eingefügt ({p.start}, {p.start + p.step}, {p.start + 2 * p.step} ...).")

    # --- Yes / No column (Add column tab): logical field, every row starts with the chosen value ------------------------------------
    @Slot(str, str, str, str, int, result=str)
    def addYesNoColumn(self, name: str, yes_text: str, no_text: str, default: str, row: int = -1) -> str:
        """Insert a calculated Yes / No column behind the tile `row` (-1 = at the end); every row starts with `default`
        ('yes' / 'no' / '' = empty). One undo step. Returns '' or a readable error."""
        model, src, cfg = self.model, self.model.source, self.model.config
        if not model.keys():
            return "Es gibt keine Tabelle."
        p = YN.YesNoParameters(str(yes_text or "").strip(), str(no_text or "").strip(), str(default or ""))
        err = YN.validate(p)
        if err:
            return err
        ids, taken = self._Ids(cfg), {src.label(k) for k in model.keys()}
        label = self._free_label((name or YN.DEFAULT_NAME).strip() or YN.DEFAULT_NAME, taken)
        out_id = ids.next("x")
        p = replace(p, output_key=f"calc_{out_id}")
        node = YN.build_node(node_id=ids.next("n"), out_id=out_id, out_name=label, params=p)
        after = self._key(row) or model.keys()[-1]
        return self._commit([{"node": node, "label": label, "values": YN.compute(p, len(self._get(""))), "after": after}],
                            "Ja/Nein-Spalte hinzufügen", [], False, f"Ja/Nein-Spalte '{label}' eingefügt ('{p.yes_text}' / '{p.no_text}').")

    # --- fill empty cells with a value of the user's choice (Transform tab) --------------------------------------------------------
    def fill_targets(self, row: int, whole_group: bool) -> list[str]:
        """Columns the fill acts on: the tile / multi selection, or every tile of the group of the tile."""
        if whole_group:
            keys = [k for k in self._group_keys(self._key(row)) if not self.model.is_temporary(k)]
            return keys if len(keys) > 1 else self._targets(row)
        return self._targets(row)

    def empty_count(self, keys: list[str]) -> int:
        return sum(1 for k in keys for v in self._get(k) if is_empty(v))

    def fillEmpty(self, row: int, value: str, whole_group: bool = False, replace_original: bool = True) -> str:
        """Every empty cell of the target columns gets `value`; one calculated column 'name (filled)' per column, one undo step.
        Returns '' or a readable error; on an error nothing changes."""
        keys = self.fill_targets(row, whole_group)
        if not keys:
            return "Keine Spalte gewählt."
        params = TO.TextOpParameters("fill_value", replace_with=str(value or "").strip())
        err = TO.validate(params)
        if err:
            return err
        ids, taken = self._Ids(self.model.config), {self.model.source.label(k) for k in self.model.keys()}
        try:
            specs = [self._text_spec(k, params, ids, taken, replace_original) for k in keys]
        except TO.TextOpError as e:
            return str(e)
        changed, n = sum(sp["changed"] for sp in specs), len(keys)
        return self._commit(specs, TO.OPS["fill_value"][0] + ("" if n == 1 else f" ({n} Spalten)"), keys, replace_original,
                            f"{TO.OPS['fill_value'][0]} '{params.replace_with}': {changed:,} Zellen gefüllt. "
                            f"Neue Spalte: {', '.join(sp['label'] for sp in specs)}.")

    # --- check against a code list -------------------------------------------------------------------------------------------------------
    @Slot(int, "QVariantMap", result="QVariantMap")
    def previewCheck(self, row: int, options: dict) -> dict:
        key = self._key(row)
        if key is None:
            return {"ok": False, "error": "Keine Spalte gewählt.", "bad": 0, "total": 0, "examples": []}
        p = self._chparams(key, options)
        err = CK.validate(p)
        if err:
            return {"ok": False, "error": err, "bad": 0, "total": 0, "examples": []}
        vals = self._get(key)
        res = CK.compute(p, lambda _k: vals)
        bad = [str(v) for v, r in zip(vals, res) if r == p.bad_text]
        distinct = []
        for v in bad:
            if v not in distinct:
                distinct.append(v)
        return {"ok": True, "error": "", "bad": len(bad), "total": len(vals), "examples": distinct[:6], "distinct": len(distinct)}

    @staticmethod
    def _chparams(key: str, options: dict) -> CK.CheckParameters:
        vals = tuple(sorted({str(v).strip() for v in (options.get("values") or ()) if str(v).strip()}))
        return CK.CheckParameters(vals, str(options.get("listName") or ""), bool(options.get("ignoreCase", True)),
                                  bool(options.get("emptyOk", True)), "OK", str(options.get("badText") or "NICHT IN LISTE"), key)

    @Slot(int, "QVariantMap", result=str)
    def applyCheck(self, row: int, options: dict) -> str:
        key = self._key(row)
        d = self.model.definition(key) if key else None
        if d is None:
            return "Keine Spalte gewählt."
        p = self._chparams(key, options)
        err = CK.validate(p)
        if err:
            return err
        ids, taken = self._Ids(self.model.config), {self.model.source.label(k) for k in self.model.keys()}
        label = self._free_label(f"{self.model.source.label(key)} (check)", taken)
        out_id = ids.next("x")
        p = replace(p, output_key=f"calc_{out_id}")
        try:
            node = CK.build_node(node_id=ids.next("n"), input_id=d.column_id, out_id=out_id, out_name=label, params=p)
        except CK.CheckError as e:
            return str(e)
        vals = CK.compute(p, self._get)
        bad = sum(1 for v in vals if v == p.bad_text)
        return self._commit([{"node": node, "label": label, "values": vals, "after": key}], "Gegen Codeliste prüfen", [], False,
                            f"{bad:,} of {len(vals):,} Werte stehen nicht in {p.list_name or 'der Liste'}.")

    # --- steps panel: list, reorder, edit, delete ----------------------------------------------------------------------------------------
    def _producers(self, nodes: list) -> dict:
        return {D.output_key(n): i for i, n in enumerate(nodes) if D.is_derived(n) and D.output_key(n)}

    def _order_ok(self, nodes: list) -> bool:
        """Every step comes after the steps that make the columns it reads."""
        made = self._producers(nodes)
        for i, n in enumerate(nodes):
            if D.is_derived(n) and any(made.get(k, -1) > i for k in D.input_keys(n)):
                return False
        return True

    def _step_list(self) -> list:
        src, cfg = self.model.source, self.model.config
        by_id = {d.column_id: d for d in cfg.columns}
        used = {i for n in cfg.nodes for i in n.input_ids}

        def name(column_id: str) -> str:
            d = by_id.get(column_id)
            return src.label(d.source_name) if d is not None and d.source_name in self.model.keys() else (d.output_name if d else column_id)
        out = []
        for i, n in enumerate(cfg.nodes):
            if not n.enabled:
                continue
            key = D.output_key(n)
            if n.operation == "convert":
                p = ConvertParameters.from_dict(n.parameters)
                text = f"Typ ändern '{name(n.input_ids[0])}': {TYPE_NAMES.get(p.from_type)} → {TYPE_NAMES.get(p.to_type)}"
                d = by_id.get(n.input_ids[0])
                key = d.source_name if d else ""
            elif D.is_derived(n):
                try:
                    text = D.describe(n, self._label_of) + f" → '{n.output.name}'"
                except Exception:  # noqa: BLE001 - a step must never break the panel
                    text = f"{n.operation} → '{n.output.name}'"
            else:
                text = f"{n.operation} → '{n.output.name}'"
            can = n.operation == "convert" or (D.is_derived(n) and n.output.column_id not in used)
            swap_up = list(cfg.nodes)
            swap_dn = list(cfg.nodes)
            if i > 0:
                swap_up[i - 1], swap_up[i] = swap_up[i], swap_up[i - 1]
            if i < len(cfg.nodes) - 1:
                swap_dn[i + 1], swap_dn[i] = swap_dn[i], swap_dn[i + 1]
            out.append({"index": i, "text": text, "kind": n.operation, "key": key, "canDelete": bool(can),
                        "why": "" if can else "Ein anderer Schritt nutzt diese Spalte. Zuerst diesen Schritt löschen.",
                        "canEdit": bool(D.is_derived(n) and D.editable(n)),
                        "canUp": i > 0 and self._order_ok(swap_up), "canDown": i < len(cfg.nodes) - 1 and self._order_ok(swap_dn)})
        names = {n.output.name for n in cfg.nodes}
        keys_now = self.model.keys()
        for bi, b in enumerate(cfg.bands):                     # "Group only" has no node: the group itself is the step (after the node steps)
            if b.get("name") in names:                           # a join node of the same name already is the step
                continue
            members = [k for k in b.get("keys", []) if k in keys_now]
            if len(members) < 2:
                continue
            out.append({"index": -1, "bandIndex": bi, "text": f"Kacheln gruppieren '{b.get('name', '')}': " + ", ".join(f"'{src.label(k)}'" for k in members),
                        "kind": "group", "key": members[0], "canDelete": True, "why": "", "canEdit": False, "canUp": False, "canDown": False})
        return out

    @Slot(int, result=str)
    def removeGroupStep(self, band_index: int) -> str:
        """Remove ONE group step (dissolve that group only; the columns stay as they are). One undo step."""
        cfg = self.model.config
        if not 0 <= band_index < len(cfg.bands):
            return "Diese Gruppe gibt es nicht mehr."
        before = [dict(b) for b in cfg.bands]
        after = [dict(b) for i, b in enumerate(cfg.bands) if i != band_index]
        name = before[band_index].get("name", "")

        def put(bands: list[dict]) -> None:
            cfg.bands[:] = [dict(b) for b in bands]
        self.stack.push(Command(f"Gruppe auflösen '{name}'", lambda: put(after), lambda: put(before)))
        self.undoChanged.emit()
        return ""

    steps = Property("QVariantList", _step_list, notify=undoChanged)

    @Slot(str, result=int)
    def rowOfKey(self, key: str) -> int:
        keys = self.model.keys()
        return keys.index(key) if key in keys else -1

    @Slot(int, int, result=str)
    def moveStep(self, index: int, delta: int) -> str:
        """Move a step up (-1) or down (+1) in the list (undoable). A step cannot move before the step that makes a column it reads."""
        cfg = self.model.config
        j = index + delta
        if not (0 <= index < len(cfg.nodes) and 0 <= j < len(cfg.nodes)):
            return ""
        new = list(cfg.nodes)
        new[index], new[j] = new[j], new[index]
        if not self._order_ok(new):
            return "Ein Schritt kann nicht vor den Schritt rücken, der seine Spalte erzeugt."
        old = list(cfg.nodes)

        def set_nodes(nodes: list) -> None:
            cfg.nodes[:] = nodes
            self.undoChanged.emit()
        set_nodes(new)
        self.stack.push(Command("Schritt verschieben", lambda: set_nodes(new), lambda: set_nodes(old)), execute=False)
        return ""

    @Slot(int, result="QVariantMap")
    def stepInfo(self, index: int) -> dict:
        """What the edit dialog of a step starts with."""
        cfg = self.model.config
        if not 0 <= index < len(cfg.nodes):
            return {}
        n = cfg.nodes[index]
        if n.operation == "text_op":
            p = TO.TextOpParameters.from_dict(n.parameters)
            return {"kind": "text_op", "op": p.op, "options": self._toptions(p), "row": self.rowOfKey(p.source_key),
                    "name": n.output.name}
        if n.operation == "conditional":
            return {"kind": "conditional", "spec": self._cspec(CO.ConditionalParameters.from_dict(n.parameters)), "name": n.output.name}
        if n.operation == "check_list":
            p = CK.CheckParameters.from_dict(n.parameters)
            return {"kind": "check_list", "row": self.rowOfKey(p.source_key), "options": {
                "values": list(p.values), "listName": p.list_name, "ignoreCase": p.ignore_case, "emptyOk": p.empty_ok, "badText": p.bad_text}}
        return {"kind": n.operation}

    def _change_node(self, index: int, new_node: TransformationNode, text: str) -> str:
        """Replace the settings of one step and recalculate it and every step that reads its column (one undo step)."""
        model, src, cfg = self.model, self.model.source, self.model.config
        old_nodes = list(cfg.nodes)
        nodes = list(old_nodes)
        nodes[index] = new_node
        changed_keys = {D.output_key(new_node)}
        new_vals: dict = {}
        old_vals: dict = {}

        def get(k: str) -> list:
            return new_vals[k] if k in new_vals else src.column_values(k or model.keys()[0])
        try:
            for i in range(index, len(nodes)):
                n = nodes[i]
                if not D.is_derived(n) or (i != index and not (set(D.input_keys(n)) & changed_keys)):
                    continue
                key = D.output_key(n)
                old_vals[key] = src.column_values(key)
                new_vals[key] = D.compute(n, get)
                changed_keys.add(key)
        except Exception as e:  # noqa: BLE001 - a bad setting must leave everything as it is
            return str(e) or "Der Schritt ließ sich nicht neu berechnen."

        def apply(nodes_: list, vals: dict) -> None:
            cfg.nodes[:] = nodes_
            for k, v in vals.items():
                src.update_derived(k, v)
                model.refresh_key(k)
            self.undoChanged.emit()
            self.selectedChanged.emit()
        apply(nodes, new_vals)
        self.stack.push(Command(text, lambda: apply(nodes, new_vals), lambda: apply(old_nodes, old_vals)), execute=False)
        return ""

    @Slot(int, "QVariantMap", result=str)
    def editTextStep(self, index: int, options: dict) -> str:
        cfg = self.model.config
        if not 0 <= index < len(cfg.nodes) or cfg.nodes[index].operation != "text_op":
            return "Dieser Schritt lässt sich hier nicht ändern."
        n = cfg.nodes[index]
        old = TO.TextOpParameters.from_dict(n.parameters)
        p = self._tparams(old.op, options)
        if old.op in ("split_part", "split_fixed", "split_transition"):
            p = replace(p, number=p.number or old.number, start=p.start or old.start)
        if old.op == "split_transition":
            p = replace(p, find=old.find)                 # the kind of change is set in the Split dialog, not in the step editor
        p = replace(p, source_key=old.source_key, output_key=old.output_key, replaced_original=old.replaced_original,
                    part_label=old.part_label)
        err = TO.validate(p)
        if err:
            return err
        return self._change_node(index, replace(n, parameters=p.to_dict()), "Schritt ändern")

    @Slot(int, "QVariantMap", result=str)
    def editConditionalStep(self, index: int, spec: dict) -> str:
        cfg = self.model.config
        if not 0 <= index < len(cfg.nodes) or cfg.nodes[index].operation != "conditional":
            return "Dieser Schritt lässt sich hier nicht ändern."
        n = cfg.nodes[index]
        p = self._cparams(spec, D.output_key(n))
        err = CO.validate(p)
        if err:
            return err
        by_key = {d.source_name: d.column_id for d in cfg.columns}
        ids = tuple(by_key[k] for k in p.keys_used() if k in by_key)
        return self._change_node(index, replace(n, parameters=p.to_dict(), input_ids=ids), "Schritt ändern")

    @Slot(int, "QVariantMap", result=str)
    def editCheckStep(self, index: int, options: dict) -> str:
        cfg = self.model.config
        if not 0 <= index < len(cfg.nodes) or cfg.nodes[index].operation != "check_list":
            return "Dieser Schritt lässt sich hier nicht ändern."
        n = cfg.nodes[index]
        old = CK.CheckParameters.from_dict(n.parameters)
        p = replace(self._chparams(old.source_key, options), output_key=old.output_key)
        err = CK.validate(p)
        if err:
            return err
        return self._change_node(index, replace(n, parameters=p.to_dict()), "Schritt ändern")

    @Slot(int)
    def requestChangeType(self, row: int) -> None:
        self.changeTypeRequested.emit(row)

    @Slot("QVariantMap")
    def requestEditStep(self, step: dict) -> None:
        self.editStepRequested.emit(step)

    @Slot(str, int)
    def requestFunction(self, name: str, row: int) -> None:
        """Ask the tile editor (QML) to open the dialog of a function for a tile; names: replace, format, normalise_size, extract_first,
        extract_last, extract_before, extract_after, extract_between, split, conditional, check, lookup."""
        self.functionRequested.emit(name, row)

    FUNCTION_NAMES = ("replace", "format", "normalise_size", "extract_first", "extract_last", "extract_before", "extract_after",
                      "extract_between", "split", "conditional", "check", "lookup")
    ONE_CLICK_OPS = ("trim", "clean", "upper", "lower", "capitalise", "fill_down", "fill_up", "duplicate")

    def run_one_click(self, op: str, row: int) -> str:
        """The functions without a dialog (Transform menu / ribbon); returns an error text or ''."""
        if op not in self.ONE_CLICK_OPS:
            return f"Unbekannte Funktion '{op}'."
        return self.applyTextOp(row, op, {"replaceOriginal": op != "duplicate"})      # a copy leaves the original visible

    # --- helpers of the check / lookup dialogs ------------------------------------------------------------------------------------
    code_list_provider = None          # set by the host: callable returning {list name: [codes]} (project definitions); may be None

    def set_code_list_provider(self, provider) -> None:
        self.code_list_provider = provider

    def _code_lists(self) -> dict:
        try:
            return dict(self.code_list_provider() or {}) if self.code_list_provider else {}
        except Exception:  # noqa: BLE001 - a missing / broken project definition just means no ready-made lists
            return {}

    @Slot(result="QVariantList")
    def codeLists(self) -> list:
        """Ready-made lists (building, system, function, pipe class codes ...) for 'Check against a code list'."""
        return [{"name": k, "count": len(v)} for k, v in self._code_lists().items()]

    @Slot(str, result="QVariantList")
    def codeListValues(self, name: str) -> list:
        return [str(v) for v in self._code_lists().get(name, ())]

    @Slot(int, result="QVariantList")
    def columnDistinctValues(self, row: int) -> list:
        """The distinct non-empty values of a tile (to build a list from a column)."""
        key = self._key(row)
        if key is None:
            return []
        seen, out = set(), []
        for v in self._get(key):
            t = str(v).strip()
            if t and t not in seen:
                seen.add(t)
                out.append(t)
        return out

    @Slot(str, result="QVariantMap")
    def lookupSheets(self, file: str) -> dict:
        """Sheets of another workbook (csv = one entry); error text when the file cannot be read."""
        try:
            return {"ok": True, "error": "", "sheets": list(LK.sheet_names(file))}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e) or "Die Datei ließ sich nicht lesen.", "sheets": []}

    @Slot(str, str, result="QVariantMap")
    def lookupHeaders(self, file: str, sheet: str) -> dict:
        try:
            headers, rows = LK.read_list(file, sheet)
            return {"ok": True, "error": "", "headers": list(headers), "rows": len(rows)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": str(e) or "Die Liste ließ sich nicht lesen.", "headers": [], "rows": 0}

    @Slot(int, result=str)
    def deleteStep(self, index: int) -> str:
        """Remove one step (undoable). A function step removes its calculated column and gives the original back;
        a type change goes back to the source type. Returns '' or a readable reason."""
        model, src, cfg = self.model, self.model.source, self.model.config
        if not 0 <= index < len(cfg.nodes):
            return "Diesen Schritt gibt es nicht mehr."
        node = cfg.nodes[index]
        if node.operation == "convert":
            d = next((c for c in cfg.columns if c.column_id == node.input_ids[0]), None)
            r = self.rowOfKey(d.source_name) if d else -1
            return self.applyType(r, "source", {}) if r >= 0 else "Die Spalte dieses Schritts fehlt."
        if not D.is_derived(node):
            return "Dieser Schritt lässt sich hier nicht löschen."
        if any(node.output.column_id in n.input_ids for n in cfg.nodes if n is not node):
            return "Ein anderer Schritt nutzt diese Spalte. Zuerst diesen Schritt löschen."
        out_key = D.output_key(node)
        if out_key not in model.keys():
            return "Die berechnete Spalte dieses Schritts fehlt."
        in_ids = set(node.input_ids)
        inputs = [d.source_name for d in cfg.columns if d.column_id in in_ids and d.source_name in model.keys()]
        gave_back = bool(node.parameters.get("replaced_original")) or (node.operation == "join" and (
            not node.keep_inputs or not node.parameters.get("include_originals_in_export", True)))
        label, values = src.label(out_key), src.column_values(out_key)
        row = model.keys().index(out_key)
        before_cfg = cfg.to_dict()
        was = {k: (src.is_hidden(k), (model.definition(k).include_in_export if model.definition(k) else True)) for k in inputs}
        trimmed = ColumnConfig.from_dict(before_cfg)
        trimmed.nodes[:] = [n for i, n in enumerate(trimmed.nodes) if i != index]
        trimmed.columns[:] = [c for c in trimmed.columns if c.source_name != out_key]
        after_cfg = trimmed.to_dict()

        def redo() -> None:
            model.remove_calculated(out_key)
            src.remove_derived(out_key)
            model.restore_config(after_cfg)
            if gave_back:
                for k in inputs:
                    src.set_hidden(k, False)
                    src.set_export_excluded(k, False)
                    dd = model.definition(k)
                    if dd:
                        dd.include_in_export = True
            for k in inputs:
                model.refresh_key(k)

        def undo() -> None:
            src.add_derived(out_key, label, values)
            model.restore_config(before_cfg)
            model.add_calculated(out_key, row, node.output.column_id, label)
            for k, (hid, exp) in was.items():
                src.set_hidden(k, hid)
                src.set_export_excluded(k, not exp)
                model.refresh_key(k)
        redo()
        self.stack.push(Command("Schritt löschen", redo, undo), execute=False)
        self._multi = []
        self._selected = -1
        self._publish_selection()
        self.undoChanged.emit()
        return ""

    # --- output type: the 'Change column type' dialog -------------------------------------------------------------------------
    def _target(self, d: ColumnDefinition, type_name: str) -> ColumnType:
        if type_name == "source":
            return d.source_type
        if type_name == "auto":
            return d.source_type if d.detected_type in (ColumnType.UNKNOWN, ColumnType.NULL) else d.detected_type
        return ColumnType(type_name)

    @staticmethod
    def _on_invalid(options: dict) -> OnInvalid:
        try:
            return OnInvalid(str(options.get("onInvalid") or "empty_flag"))
        except ValueError:
            return OnInvalid.EMPTY_FLAG

    def _params(self, key: str, d: ColumnDefinition, to: ColumnType, options: dict) -> ConvertParameters:
        """Everything the conversion needs. Raises ConvertError (readable) when a date format is missing / ambiguous."""
        fmt = str(options.get("dateFormat") or "") or None
        if to in (ColumnType.DATE, ColumnType.DATETIME) and d.source_type == ColumnType.TEXT and not fmt:
            fmt = resolve_date_format(self.model.source.samples(key), to)
        return ConvertParameters(d.source_type, to, str(options.get("decimalSeparator") or "."),
                                 str(options.get("thousandsSeparator") if options.get("thousandsSeparator") is not None else ","),
                                 self._on_invalid(options), fmt)

    @Slot(int, result="QVariantMap")
    def typeInfo(self, row: int) -> dict:
        """Current state for the dialog."""
        key = self._key(row)
        d = self.model.definition(key) if key else None
        if d is None:
            return {}
        p = self.model.config.convert_params(d.column_id)
        return {"label": self.model.source.label(key), "sourceType": TYPE_NAMES.get(d.source_type),
                "outputType": d.output_type.value, "dateFormat": (p.date_format or "") if p else "",
                "decimalSeparator": p.decimal_separator if p else ".", "thousandsSeparator": p.thousands_separator if p else ",",
                "onInvalid": p.on_invalid.value if p else "empty_flag",
                "detected": TYPE_NAMES.get(d.detected_type)}

    @Slot(int, str, "QVariantMap", result="QVariantMap")
    def previewType(self, row: int, type_name: str, options: dict) -> dict:
        """Live preview of an explicit convert step: format, invalid-value behavior and the first results."""
        key = self._key(row)
        d = self.model.definition(key) if key else None
        if d is None:
            return {"error": "Keine Spalte gewählt.", "rows": []}
        try:
            to = self._target(d, type_name)
        except ValueError:
            return {"error": f"Unbekannter Typ '{type_name}'.", "rows": []}
        if to == d.source_type:
            return {"error": "", "rows": [], "note": "Quelltyp beibehalten: kein Umwandlungsschritt."}
        if to in (ColumnType.UNKNOWN, ColumnType.NULL):
            return {"error": f"Eine Spalte kann nicht in '{to.value}' umgewandelt werden.", "rows": []}
        try:
            params = self._params(key, d, to, options)
        except ConvertError as e:
            return {"error": str(e), "rows": []}
        rows = preview_convert(self.model.source.samples(key), params)
        bad = sum(1 for r in rows if not r["valid"])
        return {"error": "", "rows": rows, "format": params.date_format or "", "invalidInPreview": bad,
                "note": f"{bad} von {len(rows)} gezeigten Werten sind ungültig." if bad else ""}

    @Slot(int, str, result=str)
    def setOutputType(self, row: int, type_name: str) -> str:
        return self.applyType(row, type_name, {})

    @Slot(int, str, "QVariantMap", result=str)
    def applyType(self, row: int, type_name: str, options: dict) -> str:
        """Change the OUTPUT type of the tile or of every tile of the multi selection through explicit convert nodes.
        Returns '' or a readable error; on an error NOTHING changes (all or nothing)."""
        keys = self._targets(row)
        if not keys:
            return "Keine Spalte gewählt."
        snapshot = self.model.config.to_dict()
        for k in keys:
            err = self._convert_one(k, type_name, options)
            if err:
                self.model.restore_config(snapshot)
                return err if len(keys) == 1 else f"{self.model.source.label(k)}: {err}"
        after = self.model.config.to_dict()
        for k in keys:
            self.model.refresh_key(k)
        self.selectedChanged.emit()
        n = len(keys)
        self.stack.push(Command("Ausgabetyp ändern" + ("" if n == 1 else f" ({n} Spalten)"),
                                lambda: self._restore(after, keys), lambda: self._restore(snapshot, keys)), execute=False)
        self.undoChanged.emit()
        return ""

    def _convert_one(self, key: str, type_name: str, options: dict) -> str:
        d = self.model.definition(key)
        if d is None:
            return "Keine Spalte gewählt."
        try:
            to = self._target(d, type_name)
        except ValueError:
            return f"Unbekannter Typ '{type_name}'."
        on_invalid = self._on_invalid(options)
        values = self.model.source.column_values(key) if hasattr(self.model.source, "column_values") else []
        try:
            params = self._params(key, d, to, options) if to != d.source_type else None
            if params is not None and on_invalid == OnInvalid.ABORT:
                bad = sum(1 for v in values if not is_empty(v) and not _ok(v, params))
                if bad:
                    return f"{bad:,} Werte lassen sich nicht in {TYPE_NAMES.get(to)} umwandeln. Abgebrochen."
                on_invalid = OnInvalid.EMPTY_FLAG
            self.model.config.set_output_type(
                d.column_id, to, text_values=self.model.source.samples(key), on_invalid=on_invalid,
                date_format=params.date_format if params else None,
                decimal_separator=str(options.get("decimalSeparator") or "."),
                thousands_separator=str(options.get("thousandsSeparator") if options.get("thousandsSeparator") is not None else ","))
        except ConvertError as e:
            return str(e)
        return ""

    def _restore(self, state: dict, keys) -> None:
        self.model.restore_config(state)
        for k in ([keys] if isinstance(keys, str) else keys):
            self.model.refresh_key(k)
        self.selectedChanged.emit()

    # --- grouping: draft -> apply ------------------------------------------------------------------------------------------------
    def _new_draft(self, keys: list[str]) -> dict:
        # defaults = the owner's usual choice (2026-10-28): only "Group name as header" is on, all other check boxes are off
        d = {"keys": list(keys), "separator": "_", "trim": False, "skip": False, "target": "", "target_custom": False,
             "out_type": ColumnType.TEXT, "keep": False, "include": False, "band": True, "combine": False, "invalid": OnInvalid.EMPTY_FLAG}
        self._auto_target(d)
        return d

    def _labels(self, d: dict) -> list[str]:
        return [self.model.source.label(k) for k in d["keys"]]

    def _auto_target(self, d: dict) -> None:
        if not d["target_custom"]:
            d["target"] = d["separator"].join(self._labels(d))

    def _jparams(self, d: dict) -> JoinParameters:
        return JoinParameters(separator=d["separator"], trim=d["trim"], skip_empty=d["skip"], output_type=d["out_type"],
                              on_invalid=d["invalid"], include_originals_in_export=d["include"],
                              input_names=tuple(d["keys"]))

    def _draft_map(self) -> dict:
        d = self._draft
        if d is None:
            return {"active": False}
        labels = self._labels(d)
        params = self._jparams(d)
        cols = [self.model.source.samples(k) for k in d["keys"]]
        example, ok = join_row(example_row(cols), params)
        return {"active": True, "keys": list(d["keys"]), "labels": labels, "count": len(labels), "separator": d["separator"],
                "trim": d["trim"], "skipEmpty": d["skip"], "target": d["target"], "outputType": d["out_type"].value,
                "outputTypeName": TYPE_NAMES.get(d["out_type"]), "keep": d["keep"], "include": d["include"], "band": d["band"], "combine": d["combine"],
                "invalid": d["invalid"].value, "resultNames": d["separator"].join(labels), "example": example,
                "exampleValid": ok, "canApply": len(labels) >= 2 and bool(d["target"].strip())}

    def _emit_draft(self) -> None:
        self._draft_cache = self._draft_map()          # computed once per change, not on every QML read
        self.draftChanged.emit()

    draft = Property("QVariantMap", lambda self: self._draft_cache, notify=draftChanged)
    hasDraft = Property(bool, lambda self: self._draft is not None, notify=draftChanged)

    @Slot(result=bool)
    def startGroup(self) -> bool:
        """'Group / Combine columns': the Ctrl-selected tiles, in selection order, become a draft."""
        if len(self._multi) < 2:
            self.message.emit("Mindestens zwei Kacheln mit Strg+Klick wählen.")
            return False
        keys = [k for k in self._multi if not self.model.is_temporary(k)]       # temporary columns are not grouped
        if len(keys) < 2:
            self.message.emit("Mindestens zwei echte Spalten wählen (temporäre lassen sich nicht gruppieren).")
            return False
        self._draft = self._new_draft(keys)
        self._emit_draft()
        return True

    @Slot(int)
    def addToGroup(self, row: int) -> None:
        """Context menu 'Add to group': starts a draft (with the selected tiles) or adds the tile to the open one."""
        key = self._key(row)
        if key is None:
            return
        if self._draft is None:
            keys = list(self._multi) if key in self._multi else [*self._multi, key]
            self._draft = self._new_draft(keys if len(keys) > 1 else [key])
        elif key not in self._draft["keys"]:
            self._draft["keys"].append(key)
            self._auto_target(self._draft)
        self._emit_draft()

    def _edit(self, fn) -> None:
        if self._draft is not None:
            fn(self._draft)
            self._auto_target(self._draft)
            self._emit_draft()

    @Slot(int, int)
    def moveDraftItem(self, frm: int, to: int) -> None:
        def f(d):
            if 0 <= frm < len(d["keys"]) and 0 <= to < len(d["keys"]):
                d["keys"].insert(to, d["keys"].pop(frm))
        self._edit(f)

    @Slot(int)
    def removeDraftItem(self, i: int) -> None:
        self._edit(lambda d: d["keys"].pop(i) if 0 <= i < len(d["keys"]) else None)

    @Slot(str)
    def setSeparator(self, sep: str) -> None:
        self._edit(lambda d: d.__setitem__("separator", sep))

    @Slot(bool)
    def setTrim(self, on: bool) -> None:
        self._edit(lambda d: d.__setitem__("trim", on))

    @Slot(bool)
    def setSkipEmpty(self, on: bool) -> None:
        self._edit(lambda d: d.__setitem__("skip", on))

    @Slot(bool)
    def setKeepOriginals(self, on: bool) -> None:
        self._edit(lambda d: d.__setitem__("keep", on))

    @Slot(bool)
    def setIncludeOriginals(self, on: bool) -> None:
        self._edit(lambda d: d.__setitem__("include", on))

    @Slot(bool)
    def setBand(self, on: bool) -> None:
        """Ticked: the group name is also the collective header over the grouped columns (table, preview and Excel export).
        Not ticked: the group only lets the tiles move as one block in the tile editor."""
        self._edit(lambda d: d.__setitem__("band", on))

    @Slot(bool)
    def setCombine(self, on: bool) -> None:
        """Ticked (as before): also create a calculated column that joins the values. Not ticked: group only."""
        self._edit(lambda d: d.__setitem__("combine", on))

    # --- tile groups (block of tiles; optional collective header) ---------------------------------------------------------------
    def _group_of(self, key: str | None) -> dict | None:
        return next((b for b in self.model.config.bands if key in b["keys"]), None) if key else None

    def _group_keys(self, key: str | None) -> list[str]:
        """The tiles that move together with `key` (display order); just [key] when it is in no group."""
        g = self._group_of(key)
        if g is None:
            return [key] if key else []
        order = self.model.keys()
        return sorted((k for k in g["keys"] if k in order), key=order.index)

    def _move_targets(self, row: int) -> list[str]:
        """Keys a MOVE acts on: the targets of the command (tile / multi selection) plus every member of their groups."""
        keys = self._targets(row)
        out: set[str] = set()
        for k in keys:
            out.update(self._group_keys(k))
        order = self.model.keys()
        return sorted(out, key=order.index) if len(out) > len(keys) else keys

    @Slot(int, result=bool)
    def inGroup(self, row: int) -> bool:
        return self._group_of(self._key(row)) is not None

    @Slot(int, result=str)
    def groupName(self, row: int) -> str:
        g = self._group_of(self._key(row))
        return g["name"] if g else ""

    @Slot(int, result=bool)
    def selectGroup(self, row: int) -> bool:
        """Pick a group: select all tiles of the group the tile belongs to (then e.g. "Ungroup", move, hide ...)."""
        keys = self._group_keys(self._key(row))
        if len(keys) < 2:
            return False
        order = self.model.keys()
        self._multi = list(keys)
        self._selected = order.index(keys[0])
        self._anchor = keys[0]
        self._publish_selection()
        return True

    @Slot(int, result=bool)
    def ungroup(self, row: int) -> bool:
        """Dissolve the group(s) of the selected tile(s) (the columns stay as they are; only the block / header band is gone).
        One undo step; with a multi selection every group that contains one of the tiles is dissolved."""
        keys = set(self._targets(row))
        cfg = self.model.config
        before = cfg.to_dict()
        after = cfg.to_dict()
        after["bands"] = [b for b in after["bands"] if not (keys & set(b["keys"]))]
        n = len(before["bands"]) - len(after["bands"])
        if n == 0:
            return False

        def put(state: dict) -> None:
            cfg.bands[:] = [dict(b) for b in state["bands"]]
        self.stack.push(Command("Gruppe auflösen" if n == 1 else f"{n} Gruppen auflösen", lambda: put(after), lambda: put(before)))
        self.undoChanged.emit()
        return True

    def _new_band(self, name: str, keys: list[str], band: bool) -> dict:
        used = {int(b.get("color", 0)) for b in self.model.config.bands}
        color = next((i for i in range(len(BANDS.PALETTE)) if i not in used), len(self.model.config.bands))
        return {"name": name, "keys": list(keys), "color": color % len(BANDS.PALETTE), "band": bool(band)}

    def _group_apply(self, group: dict, keys: list[str]) -> str:
        """Group only (no joined column): the tiles move next to each other (one block) and the group is recorded - one undo step."""
        cfg = self.model.config
        before = cfg.to_dict()
        after_bands = [dict(b, keys=[k for k in b["keys"] if k not in keys]) for b in before["bands"]]    # a tile is in ONE group
        after_bands = [b for b in after_bands if len(b["keys"]) > 1] + [group]

        def put(bands: list[dict]) -> None:
            cfg.bands[:] = [dict(b) for b in bands]
        order = self.model.keys()
        first = min(order.index(k) for k in keys)
        at = sum(1 for k in order[:first] if k not in keys)
        others = [k for k in order if k not in keys]
        new = others[:at] + keys + others[at:]
        text = f"Kacheln gruppieren '{group['name']}'"
        if new == order:
            self.stack.push(Command(text, lambda: put(after_bands), lambda: put(before["bands"])))
        elif not self._reorder(new, text, also=(lambda: put(after_bands), lambda: put(before["bands"]))):
            return "Die Kacheln ließen sich nicht zusammenschieben."
        self._draft = None
        self._multi = []
        self._publish_selection()
        self._emit_draft()
        self.undoChanged.emit()
        return ""

    @Slot(str)
    def setTargetName(self, name: str) -> None:
        def f(d):
            d["target"], d["target_custom"] = name, bool(name.strip())
        self._edit(f)

    @Slot(str)
    def setGroupOutputType(self, type_name: str) -> None:
        try:
            t = ColumnType(type_name)
        except ValueError:
            return
        self._edit(lambda d: d.__setitem__("out_type", t))

    @Slot(str)
    def setGroupInvalid(self, name: str) -> None:
        try:
            v = OnInvalid(name)
        except ValueError:
            return
        self._edit(lambda d: d.__setitem__("invalid", v))

    @Slot()
    def cancelGroup(self) -> None:
        """Discard the draft completely: no node, no column, no data change."""
        if self._draft is not None:
            self._draft = None
            self._emit_draft()

    @Slot(result=str)
    def applyGroup(self) -> str:
        """'Apply to preview': neutral join node + calculated column (green tile). One undo step. Returns '' or an error."""
        d = self._draft
        if d is None:
            return "No group."
        model, src, cfg = self.model, self.model.source, self.model.config
        keys = list(d["keys"])
        defs = [model.definition(k) for k in keys]
        if len(keys) < 2 or any(x is None for x in defs):
            return "Mindestens zwei Spalten zum Gruppieren wählen."
        target = d["target"].strip()
        if not target:
            return "Der Name der Zielspalte ist leer."
        if not d["combine"]:                                                  # group only: block of tiles (+ optional header band)
            return self._group_apply(self._new_band(target, keys, d["band"]), keys)
        if any(src.label(k) == target for k in model.keys()):
            return f"Eine Spalte '{target}' gibt es schon."
        params = self._jparams(d)
        node_id, out_id = cfg._next_id("n"), cfg._next_id("x")
        out_key = f"calc_{out_id}"
        params = replace(params, output_key=out_key)
        try:
            node = build_join_node(node_id=node_id, input_ids=tuple(x.column_id for x in defs), out_id=out_id, out_name=target,
                                   params=params, keep_inputs=d["keep"])
        except JoinError as e:
            return str(e)
        values, bad = join_columns([src.column_values(k) for k in keys], params)
        if bad and params.on_invalid == OnInvalid.ABORT:
            return f"{bad:,} verbundene Werte lassen sich nicht in {TYPE_NAMES.get(params.output_type)} umwandeln. Abgebrochen."
        before_cfg = cfg.to_dict()
        row = max(model.keys().index(k) for k in keys) + 1
        was_hidden = {k: src.is_hidden(k) for k in keys}
        group = self._new_band(target, keys, True) if d["band"] else None

        def redo() -> None:
            if not src.add_derived(out_key, target, values):
                raise RuntimeError("diese Tabelle kann keine berechneten Spalten aufnehmen")
            if node not in cfg.nodes:
                cfg.nodes.append(node)
            model.add_calculated(out_key, row, out_id, target)
            if group is not None:                       # "group name in Excel": the originals get a collective header
                left = [dict(b, keys=[k for k in b["keys"] if k not in keys]) for b in cfg.bands]
                cfg.bands[:] = [b for b in left if len(b["keys"]) > 1] + [dict(group)]
            if not d["keep"]:
                for k in keys:
                    src.set_hidden(k, True)
            if not d["include"]:
                for k in keys:
                    src.set_export_excluded(k, True)
                    dd = model.definition(k)
                    if dd:
                        dd.include_in_export = False
            for k in keys:
                model.refresh_key(k)

        def undo() -> None:
            model.remove_calculated(out_key)
            src.remove_derived(out_key)
            model.restore_config(before_cfg)
            for k in keys:
                src.set_hidden(k, was_hidden[k])
                src.set_export_excluded(k, False)
                model.refresh_key(k)
        try:
            redo()
        except RuntimeError as e:
            return str(e)
        self.stack.push(Command("Spalten gruppieren", redo, undo), execute=False)
        self._draft = None
        self._multi = []
        new_row = model.keys().index(out_key)
        self._selected = new_row
        self._publish_selection()
        self._emit_draft()
        self.undoChanged.emit()
        if bad:
            self.message.emit(f"{bad:,} verbundene Werte ließen sich nicht umwandeln und wurden markiert.")
        return ""

    # --- bulk "Add columns" (Add column tab): several blank columns at once, one undo step ---------------------------------
    def addColumns(self, items: list[tuple[str, str]]) -> str:
        """Create `items` (name, `ColumnType.value`) as new, empty calculated columns (reuses add_derived /
        add_calculated, same as every other calculated column - D9: the type is set through an explicit convert node,
        never by overwriting a "source type"). Appended at the end, in the given order, one "Add N columns" undo step.
        Returns '' or a readable error (nothing is changed on an error)."""
        model, src, cfg = self.model, self.model.source, self.model.config
        if not items:
            return "Keine Spalte zum Hinzufügen."
        existing = {src.label(k).strip().casefold() for k in model.keys()}
        seen: set[str] = set()
        for name, _type_value in items:
            key = name.strip().casefold()
            if not name.strip():
                return "Ein Spaltenname ist leer."
            if key in existing or key in seen:
                return f"Eine Spalte '{name}' gibt es schon."
            seen.add(key)
        n_rows = len(src.column_values(model.keys()[0])) if model.keys() else 0
        blank = [""] * n_rows
        wanted_types: list[tuple[str, ColumnType]] = []          # (name, wanted type)
        for name, type_value in items:
            try:
                wanted_types.append((name.strip(), ColumnType(type_value)))
            except ValueError:
                return f"Unbekanntes Format '{type_value}'."
        before_cfg = cfg.to_dict()
        start_row = model.rowCount()
        made: list[str] = []                                      # out_keys created by the last redo()

        def redo() -> None:
            made.clear()
            for i, (name, wanted) in enumerate(wanted_types):
                out_id = cfg._next_id("x")                        # one at a time: each column is registered (and gets its id) before the next
                out_key = f"col_{out_id}"
                if not src.add_derived(out_key, name, blank):
                    continue                                      # should not happen (names were checked above)
                made.append(out_key)
                model.add_calculated(out_key, start_row + i, out_id, name)
                if wanted != ColumnType.TEXT:
                    try:
                        cfg.set_output_type(out_id, wanted, text_values=[])
                    except ConvertError:
                        pass                                       # an empty column always converts; defensive only
                model.refresh_key(out_key)

        def undo() -> None:
            for out_key in reversed(made):
                model.remove_calculated(out_key)
                src.remove_derived(out_key)
            model.restore_config(before_cfg)
        redo()
        n = len(made)
        self.stack.push(Command(f"{n} Spalte(n) hinzufügen", redo, undo), execute=False)
        self.undoChanged.emit()
        return ""


def _ok(value: object, params: ConvertParameters) -> bool:
    from ..domain.convert import convert_value
    return convert_value(value, params)[1]
