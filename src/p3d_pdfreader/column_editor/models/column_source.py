"""Where the tile editor gets order / visibility / labels from (Qt-free protocol).

The production source is the existing TableController (widgets_source.py), so ListTable and the tiles always agree on
column order, visibility and labels (decision D8). `ListColumnSource` is a plain in-memory source for tests.
"""
from __future__ import annotations

from typing import Callable, Protocol


class ColumnSource(Protocol):
    def keys(self) -> list[str]: ...                       # column keys in display order (removed / transient excluded)
    def label(self, key: str) -> str: ...
    def original_label(self, key: str) -> str: ...
    def is_hidden(self, key: str) -> bool: ...
    def move(self, key: str, to_row: int) -> None: ...      # to_row = index within keys() after the move
    def set_hidden(self, key: str, hidden: bool) -> bool: ...   # False if refused (last visible column)
    def samples(self, key: str) -> list[object]: ...        # raw cell values of the preview rows (for type detection)
    def on_external_change(self, callback: Callable[[], None]) -> None: ...
    # calculated (derived) columns: a real column of the table, created / removed by a node
    def column_values(self, key: str) -> list[object]: ...  # ALL rows of a column (joins run over everything)
    def add_derived(self, key: str, label: str, values: list[str]) -> bool: ...
    def remove_derived(self, key: str) -> None: ...
    def update_derived(self, key: str, values: list[str]) -> None: ...      # new values for an existing calculated column
    def set_label(self, key: str, label: str) -> bool: ...   # rename the output column (False if not allowed)
    def set_export_excluded(self, key: str, excluded: bool) -> None: ...   # visible in the table, not in the export


class ListColumnSource:
    """In-memory ColumnSource (tests, fallback)."""

    def __init__(self, columns: list[tuple[str, str]], rows: list[list[object]] | None = None):
        self._keys = [k for k, _ in columns]
        self._labels = dict(columns)
        self._orig = dict(columns)
        self._rows = rows or []
        self._hidden: set[str] = set()
        self._cb: list[Callable[[], None]] = []
        self._derived: dict[str, list[str]] = {}
        self.export_excluded: set[str] = set()

    def keys(self) -> list[str]:
        return list(self._keys)

    def label(self, key: str) -> str:
        return self._labels.get(key, key)

    def original_label(self, key: str) -> str:
        return self._orig.get(key, key)

    def is_hidden(self, key: str) -> bool:
        return key in self._hidden

    def move(self, key: str, to_row: int) -> None:
        self._keys.remove(key)
        self._keys.insert(max(0, min(to_row, len(self._keys))), key)

    def set_hidden(self, key: str, hidden: bool) -> bool:
        if hidden:
            if len(self._keys) - len(self._hidden) <= 1 and key not in self._hidden:
                return False
            self._hidden.add(key)
        else:
            self._hidden.discard(key)
        return True

    def samples(self, key: str) -> list[object]:
        if key in self._derived:
            return list(self._derived[key])
        i = self._keys_original().index(key)
        return [r[i] for r in self._rows if i < len(r)]

    def column_values(self, key: str) -> list[object]:
        return self.samples(key)

    def add_derived(self, key: str, label: str, values: list[str]) -> bool:
        if key in self._labels:
            return False
        self._labels[key] = label
        self._keys.append(key)
        self._derived[key] = list(values)
        return True

    def update_derived(self, key: str, values: list[str]) -> None:
        if key in self._derived:
            self._derived[key] = list(values)

    def remove_derived(self, key: str) -> None:
        if key in self._derived:
            del self._derived[key], self._labels[key]
            self._keys.remove(key)
            self._hidden.discard(key)
            self.export_excluded.discard(key)

    def set_label(self, key: str, label: str) -> bool:
        self._labels[key] = label
        return True

    def set_export_excluded(self, key: str, excluded: bool) -> None:
        (self.export_excluded.add if excluded else self.export_excluded.discard)(key)

    def _keys_original(self) -> list[str]:
        return list(self._labels)

    def on_external_change(self, callback: Callable[[], None]) -> None:
        self._cb.append(callback)

    def external_change(self) -> None:                      # test helper: simulate a header drag in the ListTable
        for cb in self._cb:
            cb()
