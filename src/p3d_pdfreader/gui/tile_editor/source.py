"""Datenquelle des Kachel-Editors fuer die Importliste (``ColumnSource`` aus ``column_editor``) und das Tabellenmodell
der Datentabelle darunter (Bereich 3).

* Schluessel einer Spalte = ihr Name in der eingelesenen Excel-Liste (eindeutig, siehe ``core.data_link.read_sheet``);
  berechnete Spalten bekommen ihren Schluessel vom Kachel-Editor.
* Kachel-Editor und Tabelle zeigen immer dieselbe Reihenfolge, dieselben Namen und dieselben ausgeblendeten Spalten.
* ``export_excluded`` = Spalten im Bereich „Nicht exportiert“: sie gehen nicht an das Tool (Importtabelle ``hidden``).
* Zellen der Original-Spalten sind in der Tabelle bearbeitbar; berechnete Spalten nur ueber ihre Schritte."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt, QTimer, Signal

SAMPLE_ROWS = 500           # Zeilen fuer die Typerkennung der Kacheln


def text(value) -> str:
    return "" if value is None else str(value)


class ImportSource(QObject):
    """In-Memory-Quelle (spaltenweise gespeichert, schnell auch bei ~1500 Zeilen x 350 Spalten)."""
    structureChanged = Signal()          # Reihenfolge, Namen, Ein-/Ausblenden, Spalten dazu/weg
    valuesChanged = Signal()             # Werte einer berechneten Spalte neu

    def __init__(self, headers: list[str], rows: list[list[str]], parent=None):
        super().__init__(parent)
        self._base = list(headers)
        self._order = list(headers)
        self._labels = {h: h for h in headers}
        self._orig = dict(self._labels)
        self.n_rows = len(rows)
        self._cols: dict[str, list[str]] = {h: [text(r[i]) if i < len(r) else "" for r in rows]
                                            for i, h in enumerate(headers)}
        self._derived: set[str] = set()
        self._hidden: set[str] = set()
        self.export_excluded: set[str] = set()
        self._cbs: list[Callable[[], None]] = []
        self._pending = False

    # --- ColumnSource ----------------------------------------------------------------------------------------------
    def keys(self) -> list[str]:
        return list(self._order)

    def label(self, key: str) -> str:
        return self._labels.get(key, key)

    def original_label(self, key: str) -> str:
        return self._orig.get(key, key)

    def is_hidden(self, key: str) -> bool:
        return key in self._hidden

    def move(self, key: str, to_row: int) -> None:
        if key not in self._order:
            return
        self._order.remove(key)
        self._order.insert(max(0, min(int(to_row), len(self._order))), key)
        self._changed()

    def set_hidden(self, key: str, hidden: bool) -> bool:
        if hidden:
            if key not in self._hidden and len(self._order) - len(self._hidden) <= 1:
                return False                                   # letzte sichtbare Spalte bleibt
            self._hidden.add(key)
        else:
            self._hidden.discard(key)
        self._changed()
        return True

    def samples(self, key: str) -> list[object]:
        return list(self._cols.get(key, [])[:SAMPLE_ROWS])

    def column_values(self, key: str) -> list[object]:
        return list(self._cols.get(key, []))

    def add_derived(self, key: str, label: str, values: list[str]) -> bool:
        if key in self._cols:
            return False
        vals = [text(v) for v in values][:self.n_rows]
        vals += [""] * (self.n_rows - len(vals))
        self._cols[key] = vals
        self._labels[key] = self._orig[key] = label
        self._order.append(key)
        self._derived.add(key)
        self._changed()
        return True

    def update_derived(self, key: str, values: list[str]) -> None:
        if key in self._derived:
            vals = [text(v) for v in values][:self.n_rows]
            self._cols[key] = vals + [""] * (self.n_rows - len(vals))
            self.valuesChanged.emit()

    def remove_derived(self, key: str) -> None:
        if key not in self._derived:
            return
        self._derived.discard(key)
        self._cols.pop(key, None)
        self._labels.pop(key, None)
        self._orig.pop(key, None)
        if key in self._order:
            self._order.remove(key)
        self._hidden.discard(key)
        self.export_excluded.discard(key)
        self._changed()

    def set_label(self, key: str, label: str) -> bool:
        self._labels[key] = str(label)
        self._changed()
        return True

    def set_export_excluded(self, key: str, excluded: bool) -> None:
        (self.export_excluded.add if excluded else self.export_excluded.discard)(key)
        self._changed()

    def on_external_change(self, callback: Callable[[], None]) -> None:
        self._cbs.append(callback)

    # --- fuer Fenster und Tabelle ----------------------------------------------------------------------------------
    def is_derived(self, key: str) -> bool:
        return key in self._derived

    def value(self, row: int, key: str) -> str:
        col = self._cols.get(key)
        return col[row] if col is not None and 0 <= row < len(col) else ""

    def set_value(self, row: int, key: str, value: str) -> bool:
        """Zelle einer Original-Spalte aendern (berechnete Spalten nicht)."""
        if key in self._derived or key not in self._cols or not 0 <= row < self.n_rows:
            return False
        value = text(value).strip()
        if self._cols[key][row] == value:
            return False
        self._cols[key][row] = value
        return True

    def base_rows(self) -> tuple[list[str], list[list[str]]]:
        """Die Original-Liste (mit bearbeiteten Zellen) in der eingelesenen Reihenfolge."""
        return list(self._base), [[self._cols[h][r] for h in self._base] for r in range(self.n_rows)]

    def result(self) -> tuple[list[str], list[list[str]], list[str]]:
        """(Kopf, Zeilen, nicht exportierte Spalten) in Anzeigereihenfolge, Namen eindeutig."""
        from ...core.data_link import unique_names
        keys = self.keys()
        names = unique_names([self.label(k) for k in keys])
        rows = [[self._cols[k][r] for k in keys] for r in range(self.n_rows)]
        excluded = [n for k, n in zip(keys, names) if k in self.export_excluded]
        return names, rows, excluded

    def key_for_label(self, name: str) -> str:
        if not name:
            return ""
        from ...core.data_link import unique_names
        keys = self.keys()
        for k, n in zip(keys, unique_names([self.label(k) for k in keys])):
            if n == name:
                return k
        return ""

    def _changed(self) -> None:
        """Mehrere Aenderungen hintereinander (z. B. gespeicherte Anpassung anwenden) loesen nur einen Neuaufbau aus."""
        if not self._pending:
            self._pending = True
            QTimer.singleShot(0, self.flush)

    def flush(self) -> None:
        if self._pending:
            self._pending = False
            self.structureChanged.emit()


class SourceTableModel(QAbstractTableModel):
    """Datentabelle (Bereich 3): Spalten in der Reihenfolge der Kacheln."""

    def __init__(self, source: ImportSource, parent=None):
        super().__init__(parent)
        self.src = source
        self._keys = source.keys()
        self.header_label: Callable[[str], str] = source.label
        self.on_edit: Callable[[], None] = lambda: None
        source.valuesChanged.connect(self._values)

    def keys(self) -> list[str]:
        return list(self._keys)

    def reset(self) -> None:
        self.beginResetModel()
        self._keys = self.src.keys()
        self.endResetModel()

    def _values(self) -> None:
        if self._keys and self.src.n_rows:
            self.dataChanged.emit(self.index(0, 0), self.index(self.src.n_rows - 1, len(self._keys) - 1))

    def rowCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else self.src.n_rows

    def columnCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(self._keys)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if orientation == Qt.Vertical:
            return section + 1 if role == Qt.DisplayRole else None
        if not 0 <= section < len(self._keys):
            return None
        key = self._keys[section]
        if role == Qt.DisplayRole:
            return self.header_label(key)
        if role == Qt.ToolTipRole:
            tip = f"Originalspalte: {self.src.original_label(key)}"
            if self.src.is_derived(key):
                tip = "Berechnete Spalte (aus Schritten im Kachel-Editor)"
            if key in self.src.export_excluded:
                tip += "\nNicht exportiert: wird nicht an das Tool übergeben"
            return tip + "\nRechtsklick: Datenlink 1/2 setzen"
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.column() < len(self._keys):
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.src.value(index.row(), self._keys[index.column()])
        if role == Qt.ToolTipRole:
            value = self.src.value(index.row(), self._keys[index.column()])
            return value if len(value) > 30 else None
        return None

    def flags(self, index):
        f = super().flags(index)
        if index.isValid() and 0 <= index.column() < len(self._keys) and not self.src.is_derived(self._keys[index.column()]):
            f |= Qt.ItemIsEditable
        return f

    def setData(self, index, value, role=Qt.EditRole):  # noqa: N802
        if role != Qt.EditRole or not index.isValid():
            return False
        if not self.src.set_value(index.row(), self._keys[index.column()], value):
            return False
        self.dataChanged.emit(index, index)
        self.on_edit()
        return True
