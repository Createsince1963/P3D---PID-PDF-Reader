"""Filter-/Sortier-Proxy mit zwischengespeicherten Sortierschluesseln (Performance bei grossen Tabellen).

Der Kit-Proxy (``main_gui_kit.tables.MultiColumnFilterProxy``, nicht aenderbar) berechnet bei jedem Vergleich zweier Zeilen
beide Sortierschluessel neu - bei 30 000 Zeilen sind das etwa 400 000 Python-Aufrufe je Sortierung, bei jedem neuen Modell.
Zwei Massnahmen, Sortierreihenfolge und Ergebnis bleiben dieselben wie im Kit:

* Der Schluessel je Zelle und Spalte wird einmal berechnet; ein Vergleich ist dann ein Listenzugriff.
* Ist die Quellreihenfolge schon aufsteigend sortiert (Standard: Spalte 0 aufsteigend, Tabellen werden meist in dieser
  Reihenfolge gefuellt), entfaellt die Sortierung beim Setzen des Modells ganz (stabile Sortierung = unveraenderte
  Reihenfolge). Der Sortierwunsch (Kopfanzeige) bleibt gemerkt und gilt beim naechsten Modell wieder."""
from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt

from main_gui_kit.tables import MultiColumnFilterProxy, TableDataModel

_SIGNALS = ("dataChanged", "modelReset", "layoutChanged", "rowsInserted", "rowsRemoved")


class FastSortProxy(MultiColumnFilterProxy):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._keys: dict[int, list] = {}          # Spalte -> Sortierschluessel je Quellzeile
        self._connected = None
        self._want: tuple[int, Qt.SortOrder] | None = None      # vom Nutzer/Kopf gewuenschte Sortierung
        self._gen = 0                                           # zaehlt Aenderungen der Quelldaten
        self._sorted_gen = -1                                   # Stand der Daten bei der letzten Sortierung

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Wie ``QSortFilterProxyModel.sort``, aber ohne Neusortierung, wenn sie nichts aendern wuerde (der Kit ruft
        ``sort`` nach dem Fuellen mehrfach mit derselben Spalte auf; jede Sortierung kostet bei 30 000 Zeilen Sekunden)."""
        self._want = (column, order)
        model = self.sourceModel()
        if (column >= 0 and order == Qt.AscendingOrder and isinstance(model, TableDataModel)
                and self._is_ascending(model, column)):
            if self.sortColumn() != -1:
                super().sort(-1)                   # Quelle ist schon aufsteigend: Reihenfolge der Quelle behalten
            return
        if (self.sortColumn(), self.sortOrder()) == (column, order) and self._sorted_gen == self._gen:
            return
        super().sort(column, order)
        self._sorted_gen = self._gen

    def setSourceModel(self, model) -> None:  # noqa: N802
        self._keys.clear()
        self._gen += 1
        if self._connected is not None:
            for sig in _SIGNALS:
                try:
                    getattr(self._connected, sig).disconnect(self._drop_keys)
                except (RuntimeError, TypeError):
                    pass
        column, order = self._want or (self.sortColumn(), self.sortOrder())
        presorted = (column >= 0 and order == Qt.AscendingOrder and isinstance(model, TableDataModel)
                     and self._is_ascending(model, column))
        if presorted and self.sortColumn() >= 0:
            super().sort(-1)                       # Quellreihenfolge ist schon die Sortierung: nicht noch einmal sortieren
        super().setSourceModel(model)
        self._connected = model
        if model is not None:
            for sig in _SIGNALS:
                getattr(model, sig).connect(self._drop_keys)
        if not presorted and column >= 0 and self.sortColumn() != column:
            super().sort(column, order)            # nach einem uebersprungenen Modell wieder sortieren
        self._sorted_gen = self._gen

    def _drop_keys(self, *_args) -> None:
        self._keys.clear()
        self._gen += 1

    def _is_ascending(self, model: TableDataModel, column: int) -> bool:
        keys = self._column_keys(model, column)
        return all(a <= b for a, b in zip(keys, keys[1:]))

    def _column_keys(self, model: TableDataModel, column: int) -> list:
        keys = self._keys.get(column)
        if keys is None:
            display, sort_key = TableDataModel._display_text, TableDataModel._sort_key
            keys = self._keys[column] = [sort_key(display(row[column] if column < len(row) else None))
                                         for row in model.rows]
        return keys

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        model = self.sourceModel()
        if isinstance(model, TableDataModel) and model is left.model() and model is right.model():
            keys = self._column_keys(model, left.column())
            if left.row() < len(keys) and right.row() < len(keys):
                return keys[left.row()] < keys[right.row()]
        return super().lessThan(left, right)
