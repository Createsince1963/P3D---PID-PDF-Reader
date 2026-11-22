"""ColumnSource on top of the existing TableController, so ListTable and the tile grid always agree (decision D8)."""
from __future__ import annotations

from typing import Callable


class TableControllerSource:
    """Adapter. Needs: ctl.header, ctl.key(), ctl.logical(), ctl.label(), ctl.original_label(), ctl.removed, ctl.transient,
    ctl.proxy, ctl.hide(), ctl.show() and the model's column_key() / text_at()."""

    def __init__(self, ctl, max_rows: int = 500):
        self.ctl = ctl
        self.max_rows = max_rows
        self._cbs: list[Callable[[], None]] = []
        self._table_hidden: set[str] = set()       # not-exported columns hidden in the table only (tiles stay in "Not exported")
        ctl.header.sectionMoved.connect(lambda *_: self._fire())
        ctl.changed.connect(self._fire)
        if hasattr(ctl, "transientChanged"):
            ctl.transientChanged.connect(self._fire)                   # a temporary column was shown / hidden: tiles follow

    def _fire(self) -> None:
        for cb in self._cbs:
            cb()

    def on_external_change(self, callback: Callable[[], None]) -> None:
        self._cbs.append(callback)

    def _visual_keys(self) -> list[str]:
        h = self.ctl.header
        out = []
        for v in range(h.count()):
            key = self.ctl.key(h.logicalIndex(v))
            if key in self.ctl.removed or (key in self.ctl.transient and key not in self.ctl._transient_on):   # temporary columns that are shown get a (grey) tile
                continue
            out.append(key)
        return out

    def keys(self) -> list[str]:
        return self._visual_keys()

    def label(self, key: str) -> str:
        return self.ctl.label(key)

    def original_label(self, key: str) -> str:
        return self.ctl.original_label(key)

    def _header_hidden(self, key: str) -> bool:
        lg = self.ctl.logical(key)
        return lg >= 0 and self.ctl.header.isSectionHidden(lg)

    def is_hidden(self, key: str) -> bool:
        """Hidden area state. A column that is only hidden in the table by the "Hide all in table" button does not count."""
        if key in self._table_hidden:
            if self._header_hidden(key):
                return False
            self._table_hidden.discard(key)        # shown again from the table itself
        return self._header_hidden(key)

    def column_width(self, key: str) -> int:
        lg = self.ctl.logical(key)
        return int(self.ctl.header.sectionSize(lg)) if lg >= 0 else 0

    def set_column_width(self, key: str, width: int) -> bool:
        lg = self.ctl.logical(key)
        if lg < 0:
            return False
        self.ctl.header.resizeSection(lg, int(width))          # the table controller reports the change (profile, remembered widths)
        return True

    def is_table_hidden(self, key: str) -> bool:
        return key in self._table_hidden and self._header_hidden(key)

    def set_table_hidden(self, key: str, on: bool) -> bool:
        """Hide / show the column in the table without moving its tile to the Hidden area."""
        if on:
            if key in self._table_hidden or self._header_hidden(key):
                return key in self._table_hidden
            if not self.ctl.hide(key):
                return False
            self._table_hidden.add(key)
            return True
        if key in self._table_hidden:
            self._table_hidden.discard(key)
            self.ctl.show(key)
        return True

    def move(self, key: str, to_row: int) -> None:
        """Move `key` so that it sits at index `to_row` of keys(). Removed / transient sections are skipped."""
        h = self.ctl.header
        keys = self._visual_keys()
        if key not in keys:
            return
        target_key = keys[max(0, min(to_row, len(keys) - 1))]
        if target_key == key:
            return
        h.moveSection(h.visualIndex(self.ctl.logical(key)), h.visualIndex(self.ctl.logical(target_key)))

    def set_hidden(self, key: str, hidden: bool) -> bool:
        if hidden and key in self._table_hidden:     # already hidden in the table: the tile now moves to the Hidden area
            self._table_hidden.discard(key)
            return True
        if not hidden and key in self._table_hidden:
            self.set_table_hidden(key, False)
            return True
        if hidden:
            return bool(self.ctl.hide(key))          # False for the last visible column (the controller shows its own note)
        self.ctl.show(key)
        return True

    def samples(self, key: str) -> list[object]:
        sm = self.ctl.proxy.sourceModel()
        if sm is None:
            return []
        col = next((c for c in range(sm.columnCount()) if sm.column_key(c) == key), -1)
        if col < 0:
            return []
        n = min(sm.rowCount(), self.max_rows)
        return [sm.text_at(r, col) for r in range(n)]

    # --- calculated columns ----------------------------------------------------------------------------------------
    def _model(self):
        return self.ctl.proxy.sourceModel()

    def column_values(self, key: str) -> list[object]:
        sm = self._model()
        if sm is None:
            return []
        col = next((c for c in range(sm.columnCount()) if sm.column_key(c) == key), -1)
        return [sm.text_at(r, col) for r in range(sm.rowCount())] if col >= 0 else []

    def add_derived(self, key: str, label: str, values: list[str]) -> bool:
        sm = self._model()
        if sm is None or not hasattr(sm, "append_derived") or not sm.append_derived(key, label, values):
            return False
        self.ctl.derived_changed(key)
        return True

    def update_derived(self, key: str, values: list[str]) -> None:
        sm = self._model()
        if sm is not None and hasattr(sm, "update_derived") and sm.update_derived(key, values):
            self.ctl.proxy.refilter()                              # values changed, columns did not: only filters / counters follow
            self.ctl._emit_counts()

    def remove_derived(self, key: str) -> None:
        sm = self._model()
        if sm is not None and hasattr(sm, "remove_derived") and sm.remove_derived(key):
            self.ctl.derived_changed(key)

    def set_export_excluded(self, key: str, excluded: bool) -> None:
        if not excluded:
            self.set_table_hidden(key, False)        # an exported column always shows in the table
        (self.ctl.export_excluded.add if excluded else self.ctl.export_excluded.discard)(key)

    def set_label(self, key: str, label: str) -> bool:
        if not self.ctl.can_rename(key):
            return False
        self.ctl.rename(key, label)
        return True

    # --- temporary (display-only) columns: shown as grey tiles, never moved / renamed / exported by the tile editor ---------------
    def is_temporary(self, key: str) -> bool:
        return key in self.ctl.transient

    def temp_exported(self, key: str) -> bool:
        """A temporary column is only part of the Excel export in the merged view."""
        return key in self.ctl.transient_export
