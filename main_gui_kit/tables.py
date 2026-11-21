"""Shared table-first building blocks extracted from AZ v0.62.

Kit v0.3.0 (2026-07-28) closes the enforcement gap found in the P3D v0.11 review:
every data surface — table, tree and selection list — reaches the same feature set
through this module. Tools no longer rebuild headers, filter dialogs or list
searches locally (WIKI/10_GUI-Vorgabe.md §3, WIKI/11_Lead-Dok-fuer-KIs.md
"Verbindlicher Tabellen- und Baumstandard": erweitern statt kopieren).

P3D v0.14 review, Punkt 08 (2026-08-11): ``ColumnFilterHeader`` gained
Ctrl+Click multi-column selection (highlighted sections) plus a "Move
selected columns to front/end" context-menu pair, enforced centrally for
every table and tree that goes through ``configure_table_view()`` /
``configure_tree_view()``. A plain click still sorts/drags exactly as
before; only Ctrl+Click enters the multi-selection.

P3D v0.20 C04.4 (2026-08-17): ``TableDataModel`` gained an ordered
multi-column sort priority (``set_sort_spec()``/``sort_spec``) alongside the
unchanged single-column ``sort()`` entry point every native header click
still uses. ``ColumnFilterHeader`` gained Shift+Click to add/cycle further
priority sort keys, an optional ``sortable_predicate`` gate (default: every
column allowed, unchanged for every tool that never sets it), a hide-guard
that explains rather than silently blocks hiding an active sort column, and
priority badges painted only when more than one sort key is active. New
``SortColumnsDialog`` covers the full picture including currently hidden
columns, with a confirm-before-unhide step. ``capture_table_layout()``/
``apply_table_layout()`` persist the full priority (``"sort_columns"``),
falling back to the pre-existing single ``"sort_column"``/``"sort_order"``
pair for layouts saved before this change.

All additions are additive. The existing call signatures
``configure_table_view(view, column_filters=...)`` and
``configure_tree_view(view, column_filters=...)`` keep working unchanged, so
BOMFusion, PlantSpecBridge and AZEngineeringProjectTool need no adjustment.
"""
from __future__ import annotations

from datetime import date, datetime

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence
from weakref import ref

import shiboken6
from PySide6.QtCore import QAbstractTableModel, QEvent, QModelIndex, QObject, QSize, QSortFilterProxyModel, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QPushButton, QSlider, QStyledItemDelegate, QTabBar, QTableView, QTableWidget, QTableWidgetItem, QToolTip, QTreeView,
    QVBoxLayout, QWidget, QSizePolicy,
)

from .settings import ViewSettingsStore

#: Every exact-value comparison in this module uses one key function. Leading and
#: trailing whitespace never distinguishes two engineering values, and case never
#: does either — otherwise the same value appears twice in a filter list.
def filter_key(value: object) -> str:
    return "" if value is None else str(value).strip().casefold()


#: A value normalizer maps the raw column values of one column onto the display
#: values a user should choose from. It returns ``(display_values, mapping)`` where
#: ``mapping`` translates every raw value onto its display value. Tools use this to
#: fold typing variants together (P3D drawing register) without the kit knowing
#: anything about the domain rule that produced the grouping.
ValueNormalizer = Callable[[list[str]], "tuple[list[str], dict[str, str]]"]

#: Dedicated model role for the complete filesystem target behind a shortened
#: or project-relative display value.  Proxies forward it automatically.
PATH_ROLE = int(Qt.UserRole) + 0x321

#: Resolved once. ``Qt.DisplayRole``-style short names go through PySide6's enum
#: compatibility layer on every access, which is measurable in per-cell callbacks.
_DISPLAY_ROLE = Qt.ItemDataRole.DisplayRole
_TOOLTIP_ROLE = Qt.ItemDataRole.ToolTipRole


def _ordered_values(values: dict[str, str]) -> list[str]:
    """Blank first, then natural order — identical for every filter list."""
    return [values[key] for key in sorted(values, key=lambda item: (item != "", TableDataModel._sort_key(item)))]


def schedule_autofit(table: QTableView | QTreeView) -> None:
    """Queue bounded AutoFit after both model and Qt layout changes settle."""
    timer = getattr(table, "_shared_autofit_timer", None)
    if timer is None:
        timer = QTimer(table)
        timer.setSingleShot(True)
        view_ref = ref(table)

        def apply_after_layout():
            view = view_ref()
            if view is None or not shiboken6.isValid(view):
                return
            fit_columns_with_margin(view)
            # Proxy/header geometry often settles one event cycle after a
            # model replacement.  The second bounded pass makes dynamic Level
            # columns reliable without continuously resizing a live table.
            def second_pass():
                settled_view = view_ref()
                if settled_view is not None and shiboken6.isValid(settled_view):
                    fit_columns_with_margin(settled_view)

            QTimer.singleShot(0, second_pass)

        timer.timeout.connect(apply_after_layout)
        table._shared_autofit_timer = timer
    timer.start(0)


def _bind_autofit(table: QTableView | QTreeView) -> None:
    model = table.model()
    if model is None or getattr(table, "_shared_autofit_model", None) is model:
        return
    table._shared_autofit_model = model
    for signal_name in (
        "modelReset", "rowsInserted", "rowsRemoved", "columnsInserted",
        "columnsRemoved", "headerDataChanged", "layoutChanged", "dataChanged",
    ):
        signal = getattr(model, signal_name, None)
        if signal is not None:
            signal.connect(lambda *_args, view=table: schedule_autofit(view))
    schedule_autofit(table)


def _path_value(value) -> Path | None:
    full_path = getattr(value, "full_path", None)
    if full_path:
        value = full_path
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text or "\n" in text:
        return None
    if text.casefold().startswith("file://"):
        text = QUrl(text).toLocalFile()
    try:
        path = Path(text)
    except (OSError, TypeError, ValueError):
        return None
    return path if path.is_absolute() else None


def _index_path(index: QModelIndex) -> Path | None:
    if not index.isValid():
        return None
    for role in (PATH_ROLE, Qt.ToolTipRole, Qt.DisplayRole):
        path = _path_value(index.data(role))
        if path is not None:
            return path
    return None


def _path_tooltip(path: Path) -> str:
    action = (
        "Double-click to open this folder in File Explorer."
        if path.is_dir()
        else "Double-click to show and select this file in File Explorer."
    )
    return f"{path}\n\n{action}"


def _open_path_location(view: QTableView | QTreeView, path: Path) -> None:
    if not path.exists():
        QMessageBox.information(view, "Path not found", f"The stored path is no longer available:\n{path}")
        return
    if path.is_dir():
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    elif os.name == "nt":
        try:
            subprocess.Popen(["explorer.exe", "/select,", os.path.normpath(str(path))])
            opened = True
        except OSError:
            opened = False
    else:
        opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
    if not opened:
        QMessageBox.information(view, "Path could not be opened", f"Could not open:\n{path}")


class _PathCellEventFilter(QObject):
    """Central tooltip and Explorer navigation for path-bearing cells."""

    def __init__(self, view):
        super().__init__(view)
        self._view_ref = ref(view)

    def eventFilter(self, watched, event):
        view = self._view_ref()
        if view is None:
            return False
        if event.type() not in (QEvent.ToolTip, QEvent.MouseButtonDblClick):
            return False
        index = view.indexAt(event.pos())
        path = _index_path(index)
        if path is None:
            return False
        if event.type() == QEvent.ToolTip:
            QToolTip.showText(event.globalPos(), _path_tooltip(path), view.viewport())
            return True
        _open_path_location(view, path)
        # Consume only path-cell double-clicks. Existing preview/open handlers
        # remain active for every non-path cell.
        return True


def _bind_path_navigation(view: QTableView | QTreeView) -> None:
    if getattr(view, "_shared_path_navigation", None) is not None:
        return
    handler = _PathCellEventFilter(view)
    view.viewport().installEventFilter(handler)
    view._shared_path_navigation = handler


# ---------------------------------------------------------------- Column text alignment (header context menu)
# Owner request 2026-11-18: left/center/right per column in every configured
# table of every tool. Stored on the view as ``view._col_align`` = {header text:
# side}, keyed by the column's header text so it survives new data and moved
# columns; "left" is the default and never stored. The same attribute and
# format were introduced locally in P3D - InstrumentationList 1.6.0.12, whose
# own delegate keeps reading it unchanged.
ALIGN_FLAGS = {"left": Qt.AlignLeft, "center": Qt.AlignHCenter, "right": Qt.AlignRight}
ALIGN_SIDES = ("left", "center", "right")


def _header_text(model, column: int) -> str:
    return str(model.headerData(column, Qt.Horizontal, Qt.DisplayRole) or "") if model is not None else ""


def column_alignment(view: QTableView | QTreeView, column: int) -> str:
    """``'left'``, ``'center'`` or ``'right'`` for one logical column (default left)."""
    return getattr(view, "_col_align", {}).get(_header_text(view.model(), column), "left")


def apply_alignment_option(view, option, index) -> None:
    """Apply the user's column alignment to a style option. Tools with their own
    delegates call this from ``initStyleOption`` so the menu works there too."""
    align = getattr(view, "_col_align", None) if view is not None else None
    if align and index.isValid():
        side = align.get(_header_text(index.model(), index.column()))
        if side in ALIGN_FLAGS:
            option.displayAlignment = ALIGN_FLAGS[side] | Qt.AlignVCenter


class AlignmentDelegate(QStyledItemDelegate):
    """Default delegate installed by :func:`set_column_alignment` on views that
    still use Qt's plain delegate. Custom delegates are never replaced."""

    def initStyleOption(self, option, index) -> None:
        super().initStyleOption(option, index)
        apply_alignment_option(self.parent(), option, index)


def install_alignment_delegate(view: QTableView | QTreeView) -> None:
    current = view.itemDelegate()
    if current is None or type(current) is QStyledItemDelegate:
        view.setItemDelegate(AlignmentDelegate(view))


def set_column_alignment(view: QTableView | QTreeView, columns, side: str) -> None:
    """Align the text of the given logical columns; saved with the remembered layout."""
    if side not in ALIGN_FLAGS:
        return
    install_alignment_delegate(view)
    align = getattr(view, "_col_align", None)
    if align is None:
        align = view._col_align = {}
    for column in columns:
        name = _header_text(view.model(), column)
        if side == "left":
            align.pop(name, None)
        else:
            align[name] = side
    view.viewport().update()


class TableDataModel(QAbstractTableModel):
    """Simple read-only table model for headers and row sequences."""

    def __init__(self, headers: Sequence[str], rows: Sequence[Sequence[object]], parent=None):
        super().__init__(parent)
        self.headers = [str(header) for header in headers]
        self._source_rows = [(index + 1, list(row)) for index, row in enumerate(rows)]
        self.rows = [row for _number, row in self._source_rows]
        self._row_numbers = [number for number, _row in self._source_rows]
        self.global_filter = ""
        self.column_filters: dict[int, str] = {}
        self.value_filters: dict[int, set[str]] = {}
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        #: C04.4 (WIKI_V0.20 Abschnitt 6, "Mehrspaltige Sortierung ist
        #: erlaubt; Prioritaet und Richtung werden bewusst durch den
        #: Benutzer festgelegt"): ordered ``(column, order)`` list, priority
        #: = list order. ``sort()`` (the single-column entry point every
        #: other Kit consumer's native header-click already uses) keeps
        #: setting this to a one-item list, so nothing changes for tools
        #: that never call ``set_sort_spec()``.
        self._sort_spec: list[tuple[int, Qt.SortOrder]] = []
        #: Optional per-column value normalizers, see ValueNormalizer above.
        self.value_normalizers: dict[int, ValueNormalizer] = {}
        self._normalized_cache: dict[int, dict[str, str]] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self.rows[index.row()][index.column()]
        if role == _DISPLAY_ROLE:
            # Hot path (every painted cell, every filter/sort pass): no path parsing.
            return self._display_text(value)
        if role != PATH_ROLE and role != _TOOLTIP_ROLE:
            return None
        path = _path_value(value)
        if role == PATH_ROLE:
            return str(path) if path is not None else None
        return _path_tooltip(path) if path is not None else None

    @staticmethod
    def _display_text(value: object) -> str:
        """The exact text ``data(..., DisplayRole)`` returns for one cell value."""
        if isinstance(value, (date, datetime)):
            return value.strftime("%d.%m.%Y")
        return "" if value is None else str(value)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers[section]
        # Non-hideable view index: always 1..n in the current visible order.
        # Persistent/source indices remain ordinary data columns unchanged.
        return str(section + 1)

    @staticmethod
    def _sort_key(value: object):
        if isinstance(value, datetime):
            return 0, value.timestamp()
        if isinstance(value, date):
            return 0, float(value.toordinal())
        text = "" if value is None else str(value).strip()
        try:
            return 0, float(text.replace(",", "."))
        except ValueError:
            return 1, text.casefold()

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Single-column sort — the entry point Qt's native header click and
        every existing Kit consumer already use. Always collapses to exactly
        one active sort key, same as before C04.4."""
        self._sort_column, self._sort_order = column, order
        self._sort_spec = [(column, order)] if column >= 0 else []
        self._rebuild()

    @property
    def sort_spec(self) -> list[tuple[int, Qt.SortOrder]]:
        """Current ordered sort keys, priority = list order (C04.4)."""
        return list(self._sort_spec)

    def set_sort_spec(self, spec: list[tuple[int, "Qt.SortOrder"]]) -> None:
        """Set an explicit, user-chosen multi-column sort priority (C04.4,
        WIKI_V0.20 Abschnitt 6). ``spec`` is ``[(column, order), ...]``, first
        entry highest priority. An empty list clears sorting entirely."""
        valid = [(column, order) for column, order in spec if 0 <= column < len(self.headers)]
        self._sort_spec = valid
        self._sort_column = valid[0][0] if valid else -1
        self._sort_order = valid[0][1] if valid else Qt.AscendingOrder
        self._rebuild()

    def set_global_filter(self, text: str) -> None:
        self.global_filter = text.casefold().strip()
        self._rebuild()

    def set_column_filter(self, column: int, text: str) -> None:
        value = text.casefold().strip()
        if value:
            self.column_filters[column] = value
        else:
            self.column_filters.pop(column, None)
        self._rebuild()

    def set_value_normalizer(self, column: int, normalizer: ValueNormalizer | None) -> None:
        """Fold typing/case variants of one column onto shared display values."""
        if normalizer is None:
            self.value_normalizers.pop(column, None)
        else:
            self.value_normalizers[column] = normalizer
        self._normalized_cache.pop(column, None)
        self._rebuild()

    def _raw_column_values(self, column: int) -> list[str]:
        return ["" if column >= len(row) or row[column] is None else str(row[column])
                for _number, row in self._source_rows]

    def _normalization(self, column: int) -> dict[str, str]:
        """Raw filter key -> display value, cached per column."""
        cached = self._normalized_cache.get(column)
        if cached is not None:
            return cached
        normalizer = self.value_normalizers.get(column)
        if normalizer is None:
            mapping = {}
        else:
            _display, raw_mapping = normalizer(self._raw_column_values(column))
            mapping = {filter_key(raw): display for raw, display in raw_mapping.items()}
        self._normalized_cache[column] = mapping
        return mapping

    def _display_key(self, column: int, value: object) -> str:
        """The key a value is filtered by — normalized when the column asks for it."""
        key = filter_key(value)
        mapping = self._normalization(column)
        return filter_key(mapping.get(key, key)) if mapping else key

    def available_values(self, column: int) -> list[str]:
        """Distinct selectable values, blank first, then natural order."""
        values: dict[str, str] = {}
        for raw in self._raw_column_values(column):
            values.setdefault(self._display_key(column, raw), raw.strip())
        mapping = self._normalization(column)
        if mapping:
            for raw, display in mapping.items():
                if raw in values or filter_key(display) in values:
                    values[filter_key(display)] = display
        return _ordered_values(values)

    def set_filter_values(self, column: int, values) -> None:
        """``None`` clears the column filter; a full selection clears it as well."""
        if values is None:
            self.value_filters.pop(column, None)
            self._rebuild()
            return
        selected = {filter_key(value) for value in values}
        available = {filter_key(value) for value in self.available_values(column)}
        if selected and selected != available:
            self.value_filters[column] = selected
        else:
            self.value_filters.pop(column, None)
        self._rebuild()

    def _rebuild(self) -> None:
        records = []
        for number, row in self._source_rows:
            values = [filter_key(value) for value in row]
            if self.global_filter and not any(self.global_filter in value for value in values):
                continue
            if not all(column < len(values) and needle in values[column]
                       for column, needle in self.column_filters.items()):
                continue
            if not all(column < len(row) and self._display_key(column, row[column]) in selected
                       for column, selected in self.value_filters.items()):
                continue
            records.append((number, row))
        # C04.4: stable multi-pass sort — apply lowest priority first, so the
        # final ``records.sort()`` (highest priority, ``_sort_spec[0]``)
        # decides ties last and Python's stable sort preserves everything
        # earlier passes already settled. One-item ``_sort_spec`` (the
        # common case, every pre-C04.4 caller) behaves exactly as before.
        for column, order in reversed(self._sort_spec):
            if not (0 <= column < len(self.headers)):
                continue
            records.sort(
                key=lambda item, column=column: self._sort_key(item[1][column] if column < len(item[1]) else ""),
                reverse=order == Qt.DescendingOrder,
            )
        self.beginResetModel()
        self._row_numbers = [number for number, _row in records]
        self.rows = [row for _number, row in records]
        self.endResetModel()


class MultiColumnFilterProxy(QSortFilterProxyModel):
    """Case-insensitive global and per-column contains filtering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.global_filter = ""
        self.column_filters: dict[int, str] = {}
        self.value_filters: dict[int, set[str]] = {}
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)

    def set_global_filter(self, text: str) -> None:
        self.global_filter = text.casefold().strip()
        self.invalidateFilter()

    def set_column_filter(self, column: int, text: str) -> None:
        value = text.casefold().strip()
        if value:
            self.column_filters[column] = value
        else:
            self.column_filters.pop(column, None)
        self.invalidateFilter()

    def available_values(self, column: int) -> list[str]:
        model = self.sourceModel()
        if model is None:
            return []
        values: dict[str, str] = {}
        def collect(parent=QModelIndex()):
            for row in range(model.rowCount(parent)):
                index = model.index(row, column, parent)
                raw = "" if index.data() is None else str(index.data())
                values.setdefault(filter_key(raw), raw.strip())
                child = model.index(row, 0, parent)
                if model.rowCount(child):
                    collect(child)
        collect()
        return _ordered_values(values)

    def set_filter_values(self, column: int, values) -> None:
        """``None`` clears the column filter; a full selection clears it as well."""
        if values is None:
            self.value_filters.pop(column, None)
            self.invalidateFilter()
            return
        selected = {filter_key(value) for value in values}
        available = {filter_key(value) for value in self.available_values(column)}
        if selected and selected != available:
            self.value_filters[column] = selected
        else:
            self.value_filters.pop(column, None)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not (self.global_filter or self.column_filters or self.value_filters):
            return True  # nothing to match: skip all per-cell work
        model = self.sourceModel()
        if model is None:
            return True
        count = model.columnCount()
        if isinstance(model, TableDataModel) and not source_parent.isValid():
            # Read the row directly instead of one index()/data() round trip per cell.
            row = model.rows[source_row]
            def cell(column: int) -> str:
                return filter_key(TableDataModel._display_text(row[column]) if column < len(row) else None)
        else:
            def cell(column: int) -> str:
                return filter_key(model.index(source_row, column, source_parent).data())
        cache: dict[int, str] = {}
        def value(column: int) -> str:
            if column not in cache:
                cache[column] = cell(column)
            return cache[column]
        if self.global_filter and not any(self.global_filter in value(column) for column in range(count)):
            return False
        return (
            all(needle in value(column) for column, needle in self.column_filters.items()
                if column < count)
            and all(column < count and value(column) in selected
                    for column, selected in self.value_filters.items())
        )

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        model = self.sourceModel()
        if isinstance(model, TableDataModel) and model is left.model() and model is right.model():
            display = TableDataModel._display_text
            return (TableDataModel._sort_key(display(model.rows[left.row()][left.column()]))
                    < TableDataModel._sort_key(display(model.rows[right.row()][right.column()])))
        return TableDataModel._sort_key(left.data()) < TableDataModel._sort_key(right.data())


class HierarchicalFilterProxy(MultiColumnFilterProxy):
    """Natural multi-column filtering that preserves useful tree context."""

    def _matches_row(self, source_row: int, source_parent: QModelIndex) -> bool:
        return super().filterAcceptsRow(source_row, source_parent)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if self._matches_row(source_row, source_parent):
            return True
        model = self.sourceModel()
        if model is None:
            return True
        parent = source_parent
        while parent.isValid():
            if self._matches_row(parent.row(), parent.parent()):
                return True
            parent = parent.parent()
        current = model.index(source_row, 0, source_parent)
        for child in range(model.rowCount(current)):
            if self.filterAcceptsRow(child, current):
                return True
        return False


def configured_filter_proxy(source_model, parent=None, *, hierarchical: bool = False):
    """Return a shared natural-sort/filter proxy already bound to a source model."""
    proxy_type = HierarchicalFilterProxy if hierarchical else MultiColumnFilterProxy
    proxy = proxy_type(parent)
    proxy.setSourceModel(source_model)
    return proxy


class ColumnFilterHeader(QHeaderView):
    """Two-level header: sortable labels plus one filter field per column."""

    filterChanged = Signal()
    #: C04.4 (WIKI_V0.20 Abschnitt 6, "Data = Yes"): emitted when the user
    #: tries to add a column excluded by ``sortable_predicate`` as a sort
    #: key (Shift+Click). No default handler — tools that never set the
    #: predicate never emit this, so nothing changes for them.
    sortRejected = Signal(int)
    FILTER_HEIGHT = 26

    def __init__(self, table: QTableView | QTreeView):
        super().__init__(Qt.Horizontal, table)
        # A weak reference, because the header outlives its view during Qt's
        # parent-driven teardown. A strong attribute caused native access faults
        # in the P3D module-switch path; the report header already worked this way.
        self._table_ref = ref(table)
        self.editors: list[QLineEdit] = []
        self.setSectionsClickable(True)
        self.setSectionsMovable(True)
        self.setStyleSheet("QHeaderView::section { padding-bottom: 25px; }")
        self.sectionResized.connect(lambda *_: self._position_editors())
        self.sectionMoved.connect(lambda *_: self._position_editors())
        self.geometriesChanged.connect(self._position_editors)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)
        # --- Multi-column selection (Ctrl+Click) -----------------------------
        # Kit v0.3.2: enforced centrally for every configured table and tree so
        # "select several columns, then move them together" works the same
        # everywhere, instead of every tool inventing its own header handling
        # (WIKI/10_GUI-Vorgabe.md §3: erweitern statt kopieren). A logical
        # index set, not visual — Ctrl+Click adds/removes the section under the
        # cursor; a plain click clears the multi-selection and behaves exactly
        # as before (sort, drag-reorder).
        self._selected_columns: set[int] = set()
        self._suppress_click = False
        # --- Multi-column sort (C04.4, Shift+Click) --------------------------
        #: Optional gate: ``predicate(logical_column) -> bool``. ``None``
        #: (default) means every column is a valid sort key — unchanged
        #: behaviour for every tool that does not set this.
        self.sortable_predicate: Callable[[int], bool] | None = None
        self._suppress_sort_click = False

    @property
    def table(self):
        """The configured view, or None once Qt has torn it down."""
        return self._table_ref()

    def sizeHint(self) -> QSize:
        base = super().sizeHint()
        return QSize(base.width(), max(50, base.height() + self.FILTER_HEIGHT))

    def bind_model(self) -> None:
        for editor in self.editors:
            editor.deleteLater()
        self.editors = []
        table = self.table
        model = table.model() if table is not None else None
        if model is None:
            return
        for column in range(model.columnCount()):
            editor = QLineEdit(self.viewport())
            editor.setPlaceholderText("All")
            editor.setClearButtonEnabled(True)
            editor.setProperty("table-column-filter", True)
            editor.setToolTip(f"Filter - {self._column_name(column)}\n"
                              "Click and type to filter by content.\n"
                              "Double-click to select one or more exact values.")
            # Single click: ordinary text entry (QLineEdit default). Double click: value dialog.
            editor.mousePressEvent = (lambda event, field=editor, index=column:
                                      self._filter_field_pressed(field, index, event))
            editor.mouseDoubleClickEvent = lambda event, index=column: self._open_value_filter(index)
            editor.textEdited.connect(lambda text, index=column: self._typed_filter(index))
            editor.textChanged.connect(lambda text, index=column: self._set_filter(index, text))
            editor.show()
            self.editors.append(editor)
        self.refresh_labels()
        self._position_editors()

    def _column_name(self, column: int) -> str:
        table = self.table
        model = table.model() if table is not None else None
        if model is None:
            return str(column + 1)
        return str(model.headerData(column, Qt.Horizontal, Qt.DisplayRole) or column + 1)

    def _filter_model(self):
        table = self.table
        model = table.model() if table is not None else None
        return model if hasattr(model, "set_column_filter") else None

    def _set_filter(self, column: int, text: str) -> None:
        model = self._filter_model()
        if model is not None:
            model.set_column_filter(column, text)
            self.filterChanged.emit()

    def _typed_filter(self, column: int) -> None:
        """Typing replaces a dialog selection: the field then holds a content filter only.
        The "n / m" label must never act as search text."""
        model = self._filter_model()
        if model is not None and column in getattr(model, "value_filters", {}):
            model.set_filter_values(column, None)
            self.filterChanged.emit()

    def _filter_field_pressed(self, editor: QLineEdit, column: int, event) -> None:
        QLineEdit.mousePressEvent(editor, event)
        model = self._filter_model()
        if model is not None and column in getattr(model, "value_filters", {}):
            editor.selectAll()  # typing replaces the "n / m" label instead of extending it

    def refresh_labels(self) -> None:
        """Show ``All`` or ``selected / available`` per column, never a stale count."""
        model = self._filter_model()
        if model is None or not hasattr(model, "available_values"):
            return
        for column, editor in enumerate(self.editors):
            selected = getattr(model, "value_filters", {}).get(column)
            if selected is None or not selected:
                continue
            total = len(model.available_values(column))
            editor.blockSignals(True)
            editor.setText(f"{len(selected)} / {total}")
            editor.blockSignals(False)

    def _open_value_filter(self, column: int) -> None:
        model = self._filter_model()
        if model is None or not hasattr(model, "available_values"):
            return
        values = model.available_values(column)
        selected = set(getattr(model, "value_filters", {}).get(column) or set())
        dialog = ValueFilterDialog(values, selected, self, column_name=self._column_name(column))
        if dialog.exec() != QDialog.Accepted:
            return
        model.set_column_filter(column, "")
        chosen = dialog.selected_values()
        model.set_filter_values(column, None if not dialog.has_restriction() else chosen)
        editor = self.editors[column]
        editor.blockSignals(True)
        editor.setText("" if not dialog.has_restriction() else f"{len(chosen)} / {len(values)}")
        editor.blockSignals(False)
        self.filterChanged.emit()

    def _position_editors(self) -> None:
        table = self.table
        if table is None:
            return
        top = max(24, self.height() - self.FILTER_HEIGHT)
        for logical, editor in enumerate(self.editors):
            x = self.sectionViewportPosition(logical)
            width = self.sectionSize(logical)
            editor.setGeometry(x + 1, top, max(0, width - 2), self.FILTER_HEIGHT - 2)
            editor.setVisible(not table.isColumnHidden(logical) and width > 0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._position_editors()

    # --- Multi-column selection (Ctrl+Click) ---------------------------------

    def mousePressEvent(self, event) -> None:
        if (event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier
                and not event.modifiers() & Qt.ControlModifier):
            # C04.4 (WIKI_V0.20 Abschnitt 6): Shift+Click adds/cycles this
            # column as an additional, lower-priority sort key instead of
            # replacing the whole sort — a plain click still resets to
            # single-column sort further below, unchanged from before.
            logical = self.logicalIndexAt(event.pos())
            if logical >= 0:
                self._shift_toggle_sort(logical)
                self._suppress_sort_click = True
                return
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.ControlModifier:
            logical = self.logicalIndexAt(event.pos())
            if logical >= 0:
                if logical in self._selected_columns:
                    self._selected_columns.discard(logical)
                else:
                    self._selected_columns.add(logical)
                self._suppress_click = True
                self.viewport().update()
                return
        if self._selected_columns and not (event.modifiers() & Qt.ControlModifier):
            # A plain click anywhere on the header clears the multi-selection
            # and falls straight back through to the normal sort/drag behaviour.
            self._selected_columns.clear()
            self.viewport().update()
        # A plain click (no Shift) falls straight through to Qt's native
        # single-column sort below — that calls ``model.sort()``, which
        # already collapses ``_sort_spec`` back to one entry (TableDataModel),
        # so the priority badges repaint correctly with no separate
        # header-side state to reset here.
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._suppress_click:
            self._suppress_click = False
            return
        if self._suppress_sort_click:
            self._suppress_sort_click = False
            return
        super().mouseReleaseEvent(event)

    def _sort_model(self):
        table = self.table
        model = table.model() if table is not None else None
        return model if hasattr(model, "set_sort_spec") else None

    def _clear_multi_sort_badges_on_plain_click(self) -> None:
        # Nothing to store locally — badges are painted straight from the
        # model's own ``sort_spec``, so once ``model.sort()`` runs (right
        # after this in the normal Qt click path) they repaint correctly
        # with no separate header-side state to reset.
        return

    def _shift_toggle_sort(self, logical: int) -> None:
        model = self._sort_model()
        if model is None:
            return
        predicate = self.sortable_predicate
        if predicate is not None and not predicate(logical):
            self.sortRejected.emit(logical)
            return
        spec = model.sort_spec
        existing = next((entry for entry in spec if entry[0] == logical), None)
        if existing is None:
            spec = spec + [(logical, Qt.AscendingOrder)]
        elif existing[1] == Qt.AscendingOrder:
            spec = [(logical, Qt.DescendingOrder) if c == logical else (c, o) for c, o in spec]
        else:
            # Third click on the same column removes it from the priority
            # list entirely — a clean way back to "not a sort key" without a
            # separate control.
            spec = [(c, o) for c, o in spec if c != logical]
        model.set_sort_spec(spec)
        self.viewport().update()

    def paintSection(self, painter, rect, logical_index) -> None:  # noqa: N802 - Qt override
        super().paintSection(painter, rect, logical_index)
        if logical_index in self._selected_columns:
            painter.save()
            highlight = QColor(self.palette().highlight().color())
            highlight.setAlpha(70)
            painter.fillRect(rect.adjusted(0, 0, 0, -self.FILTER_HEIGHT), highlight)
            painter.restore()
        # C04.4: Qt's native sort arrow only ever marks one section. With two
        # or more active sort keys, a small "1▲"/"2▼"-style badge on every
        # participating section is the only way the priority stays visible
        # at all — a single-key sort (every pre-C04.4 case) paints nothing
        # extra here, identical to before.
        model = self._sort_model()
        spec = model.sort_spec if model is not None else []
        if len(spec) > 1:
            position = next((index for index, (column, _order) in enumerate(spec) if column == logical_index), None)
            if position is not None:
                _column, order = spec[position]
                arrow = "▲" if order == Qt.AscendingOrder else "▼"
                painter.save()
                badge_rect = rect.adjusted(4, 4, -4, -(rect.height() - self.FILTER_HEIGHT - 18))
                painter.setPen(self.palette().highlight().color())
                painter.drawText(badge_rect, Qt.AlignLeft | Qt.AlignTop, f"{position + 1}{arrow}")
                painter.restore()

    def _open_context_menu(self, point) -> None:
        """Tool-wide column administration directly from the shared header."""
        table = self.table
        if table is None:
            return
        logical = self.logicalIndexAt(point)
        model = self._sort_model()
        active_sort_columns = {column for column, _order in (model.sort_spec if model is not None else [])}
        menu = QMenu(self)
        hide = menu.addAction("Hide column")
        # C04.4 (WIKI_V0.20 Abschnitt 6, "Eine aktive Sortierspalte kann erst
        # ausgeblendet werden, nachdem ihre Benutzersortierung entfernt
        # wurde"): stays enabled so a click gets an explanation instead of a
        # silently disabled, unexplained menu item.
        hide.setEnabled(logical >= 0 and not table.isColumnHidden(logical))
        show_all = menu.addAction("Show all columns")
        # Owner request 2026-08-25 ("wie bei Power Query"): a single column's
        # own move-to-front/move-to-end, always offered for whichever header
        # was right-clicked — independent of the multi-column selection
        # below, the same way Power Query's per-column context menu offers
        # "Move to Beginning"/"Move to End" regardless of any other selected
        # columns.
        menu.addSeparator()
        move_column_front = menu.addAction("Move column to first position")
        move_column_front.setEnabled(logical >= 0)
        move_column_end = menu.addAction("Move column to last position")
        move_column_end.setEnabled(logical >= 0)
        move_front = move_end = None
        if len(self._selected_columns) >= 2:
            menu.addSeparator()
            move_front = menu.addAction(f"Move {len(self._selected_columns)} selected columns to front")
            move_end = menu.addAction(f"Move {len(self._selected_columns)} selected columns to end")
            clear_selection = menu.addAction("Clear column selection")
        else:
            clear_selection = None
        # Alignment (owner request 2026-11-18): applies to every selected column
        # when the clicked one belongs to a Ctrl+Click selection.
        menu.addSeparator()
        targets = sorted(self._selected_columns) if logical in self._selected_columns and len(self._selected_columns) >= 2 \
            else [logical]
        align_menu = menu.addMenu(f"Alignment ({len(targets)} selected columns)" if len(targets) > 1 else "Alignment")
        align_menu.setEnabled(logical >= 0)
        current_side = column_alignment(table, logical) if logical >= 0 else "left"
        align_actions = {}
        for side, label in zip(ALIGN_SIDES, ("Left", "Center", "Right")):
            action = align_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(side == current_side)
            align_actions[action] = side
        reset_view = None
        if getattr(table, "_shared_layout_key", None):
            reset_view = menu.addAction("Reset view (columns, filters, sorting, alignment)")
        # Tool hook: ``table._shared_header_menu_hook(menu, logical)`` adds the
        # tool's own entries (connected to their own slots); the kit only
        # handles the actions it created itself.
        hook = getattr(table, "_shared_header_menu_hook", None)
        if callable(hook):
            try:
                hook(menu, logical)
            except Exception:  # noqa: BLE001 - a tool hook must never break the shared menu
                pass
        # Dynamic Subtabs (P3D owner request 2026-08-27, WIKI/10_GUI-Vorgabe.md
        # §3): only present once a tool has opted in via
        # ``configure_dynamic_subtabs(table)``. The user picks the grouping
        # column here — no column is preselected or forbidden.
        subtab_bar = getattr(table, "_shared_subtab_bar", None)
        create_subtabs = remove_subtabs = None
        if subtab_bar is not None:
            menu.addSeparator()
            column_label = self._column_name(logical) if logical >= 0 else ""
            create_subtabs = menu.addAction(
                f"Create Subtabs from '{column_label}'" if column_label else "Create Subtabs from this column"
            )
            create_subtabs.setEnabled(logical >= 0)
            remove_subtabs = menu.addAction("Remove Subtabs (back to base table)")
            remove_subtabs.setEnabled(subtab_bar.is_active)
        selected = menu.exec(self.mapToGlobal(point))
        if selected in align_actions and logical >= 0:
            set_column_alignment(table, targets, align_actions[selected])
        elif reset_view is not None and selected == reset_view:
            reset_remembered_view(table)
            return
        elif selected == hide and logical >= 0:
            if logical in active_sort_columns:
                QMessageBox.information(
                    self, "Column is an active sort key",
                    "This column is part of the current sort. Remove it from the sort "
                    "(Shift+Click it to cycle it out, or use the Sort dialog) before hiding it.",
                )
                return
            table.setColumnHidden(logical, True)
        elif selected == show_all:
            model = table.model()
            for column in range(model.columnCount() if model is not None else 0):
                table.setColumnHidden(column, False)
        elif selected == move_column_front and logical >= 0:
            self.moveSection(self.visualIndex(logical), 0)
        elif selected == move_column_end and logical >= 0:
            self.moveSection(self.visualIndex(logical), self.count() - 1)
        elif move_front is not None and selected == move_front:
            self._move_selected_columns(to_front=True)
        elif move_end is not None and selected == move_end:
            self._move_selected_columns(to_front=False)
        elif clear_selection is not None and selected == clear_selection:
            self._selected_columns.clear()
            self.viewport().update()
            return
        elif create_subtabs is not None and selected == create_subtabs and logical >= 0:
            subtab_bar.request_activate(logical, parent=self)
            return
        elif remove_subtabs is not None and selected == remove_subtabs:
            subtab_bar.deactivate()
            return
        else:
            return
        self._position_editors()
        saver = getattr(table, "_shared_layout_saver", None)
        if saver is not None:
            saver.start(0)

    def _move_selected_columns(self, *, to_front: bool) -> None:
        """Move every selected column together, keeping their relative order.

        Repeated single-section ``moveSection`` calls, driven from the current
        visual order outward-in — the only approach that survives sections
        being moved underneath each other as the loop progresses.
        """
        if len(self._selected_columns) < 2:
            return
        # Visual positions shift every time one section moves, so the target
        # visual index and the still-to-place logical column are recomputed
        # fresh on every step rather than planned once up front.
        if to_front:
            for target in range(len(self._selected_columns)):
                logicals_in_order = sorted(self._selected_columns, key=self.visualIndex)
                self.moveSection(self.visualIndex(logicals_in_order[target]), target)
        else:
            last = self.count() - 1
            for offset in range(len(self._selected_columns)):
                logicals_in_order = sorted(self._selected_columns, key=self.visualIndex, reverse=True)
                self.moveSection(self.visualIndex(logicals_in_order[offset]), last - offset)
        self.viewport().update()


#: Dynamic Subtabs (P3D Data Manager V0.30 owner request, 2026-08-27):
#: "Der Benutzer bestimmt die Gruppierungsspalte... Keine fachliche
#: Whitelist... Bei hoher Kardinalitaet wird gewarnt, nicht blockiert."
#: The user right-clicks any column header (``ColumnFilterHeader`` — see
#: ``_open_context_menu``) and explicitly picks it as the grouping column;
#: nothing is preselected, no column is forbidden, no hardcoded list of
#: "suitable" column names exists anywhere in this module. The kit only
#: measures the data (distinct-value count) and shows a recommendation the
#: user can override.
#:
#: Implementation reuses ``TableDataModel.set_filter_values`` — a single
#: value restriction on the column's already-existing per-column value
#: filter — instead of building N separate table widgets per tab. Every
#: other feature (global search, per-column filters, multi-column sort,
#: layout persistence) keeps working unchanged underneath whichever tab is
#: active, and the underlying row data is never modified: switching tabs,
#: choosing "All" or removing the grouping only changes the active display
#: filter.
NO_ASSIGNMENT_LABEL = "No assignment"
_SUBTAB_ALL = "__SUBTAB_ALL__"
_SUBTAB_BLANK = "__SUBTAB_BLANK__"

#: ``TableDataModel._sort_key`` only tells a wholly-numeric value from a
#: text one — enough for column sort, but "Area 1, Area 2, Area 10, Area A"
#: (owner requirement, mixed alphanumeric subtab labels) needs every embedded
#: run of digits compared as a number while the surrounding text stays a
#: case-insensitive string compare. Split into digit/non-digit chunks once;
#: an all-text value (no digits at all) degrades to a plain casefold sort.
_NATURAL_CHUNK = re.compile(r"(\d+)")


def natural_sort_key(value: object) -> tuple:
    """Natural ascending sort key: numeric runs compared as numbers, the
    rest case-insensitively — ``Area 2`` before ``Area 10`` before ``Area A``.

    Every chunk is tagged ``(0, number)`` or ``(1, text)`` so two keys never
    compare an ``int`` against a ``str`` at the same tuple position (which
    Python raises ``TypeError`` on) even when one value's chunk at some
    position is numeric and the other's is text, e.g. ``"Area 2"`` vs.
    ``"Area A"`` — digits sort before letters at that position by design.
    """
    text = "" if value is None else str(value).strip()
    return tuple(
        (0, int(chunk)) if chunk.isdigit() else (1, chunk.casefold())
        for chunk in _NATURAL_CHUNK.split(text) if chunk != ""
    )


class DynamicSubtabBar(QWidget):
    """Tab strip that groups a configured table by one user-chosen column.

    Generated tabs are always naturally sorted (numeric ascending, then
    case-insensitive alphabetic — the same ``TableDataModel._sort_key`` every
    other sortable surface in this kit already uses) with an "All" tab first
    (the way back to the ungrouped base table) and blank/NULL values folded
    into one trailing :data:`NO_ASSIGNMENT_LABEL` tab instead of scattering
    them across several near-empty tabs.
    """

    #: Emitted after every activation, tab switch or deactivation — a tool
    #: hooks this exactly like ``ColumnFilterHeader.filterChanged`` (which it
    #: effectively rides on top of, since a tab switch is a value-filter
    #: change under the hood).
    changed = Signal()

    #: Recommendation thresholds (distinct value count), deliberately not a
    #: hard cap — "die Zahlen sollten konfigurierbar sein und keine
    #: fachliche Whitelist darstellen". Plain instance attributes, so a tool
    #: can tune them (``bar.WARN_THRESHOLD = 80``) without subclassing.
    HINT_THRESHOLD = 20
    WARN_THRESHOLD = 50
    STRONG_THRESHOLD = 100

    #: Owner report 2026-08-27 (28-value "Package L2" screenshot): past this
    #: many tabs, ``QTabBar`` scroll-button paging squeezes every label out
    #: of view — the strip shows two arrows and nothing readable. A slider
    #: is the usable control past this point; below it, individually
    #: clickable tabs stay the default because jumping straight to a value
    #: by clicking it beats dragging a slider one step at a time.
    SLIDER_THRESHOLD = 12

    def __init__(self, table: QTableView, parent=None):
        super().__init__(parent)
        self._table_ref = ref(table)
        table._shared_subtab_bar = self
        # Two stacked rows (owner report 2026-08-27, "slider nach unten -
        # subtabs oben wie vorherversion sichtbar aktuell durch slider
        # verdeckt"): row 1 always shows *what is currently selected* — the
        # pinned All button plus either the clickable tab strip or, in
        # slider mode, the current value label — so that identity is never
        # covered by the slider control itself. Row 2, below, holds only the
        # slider/Prev/Next navigation and is empty space when tabs are used
        # instead.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(row1)
        # Pinned "All" (owner requirement, 2026-08-27: "all tab farblich
        # hervorheben und immer als ersten stehen lassen - wandert also
        # nicht mit"): a fixed, colour-highlighted button *outside* the
        # scrollable tab strip / slider, so it never scrolls or slides out
        # of view no matter how many values the grouping column has.
        self.all_button = QPushButton("All")
        self.all_button.setCheckable(True)
        self.all_button.setCursor(Qt.PointingHandCursor)
        self.all_button.setToolTip("Show every value again (back to base table)")
        self.all_button.setStyleSheet(
            "QPushButton { padding: 3px 14px; border: 1px solid #2f6fed; border-radius: 3px;"
            " background-color: rgba(47, 111, 237, 40); color: #2f6fed; font-weight: 600; }"
            "QPushButton:checked { background-color: #2f6fed; color: white; }"
            "QPushButton:hover { background-color: rgba(47, 111, 237, 90); }"
            "QPushButton:checked:hover { background-color: #2f6fed; }"
        )
        self.all_button.clicked.connect(lambda: self._select(0))
        row1.addWidget(self.all_button)
        # Engine widget: always populated and kept in sync, but only shown
        # when there are few enough tabs to click directly (see
        # ``SLIDER_THRESHOLD``). ``capture()``/``apply()`` and the filter
        # logic read/drive this regardless of which control is visible.
        # Holds every value *except* "All" — "All" is the pinned button
        # above, never a tab that could scroll away with the rest.
        self.tabbar = QTabBar()
        self.tabbar.setExpanding(False)
        self.tabbar.setUsesScrollButtons(True)
        self.tabbar.setDrawBase(False)
        row1.addWidget(self.tabbar, 1)
        # Current-value label — row 1, next to All, so the active subtab
        # stays as visible as it was with plain clickable tabs even while
        # the slider (row 2) drives it.
        self.value_label = QLabel("")
        self.value_label.setMinimumWidth(160)
        row1.addWidget(self.value_label, 1)
        self.hint = QLabel("")
        self.hint.setStyleSheet("color: palette(mid);")
        row1.addWidget(self.hint)

        self.slider_row = QWidget()
        row2 = QHBoxLayout(self.slider_row)
        row2.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.slider_row)
        # Slider navigation: the visible control once there are too many
        # values for clickable tabs to stay usable (owner requirement,
        # 2026-08-27: "ein slider nicht tabs einzel klickbar - bei vielen
        # tabs ist unbedingt notwendig"), moved to its own row below row 1
        # so it can never visually cover the current-value display above it.
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedWidth(28)
        self.prev_button.setToolTip("Previous value")
        self.prev_button.clicked.connect(lambda: self._step(-1))
        row2.addWidget(self.prev_button)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)
        self.slider.valueChanged.connect(self._slider_changed)
        row2.addWidget(self.slider, 1)
        self.next_button = QPushButton("▶")
        self.next_button.setFixedWidth(28)
        self.next_button.setToolTip("Next value")
        self.next_button.clicked.connect(lambda: self._step(1))
        row2.addWidget(self.next_button)
        self.setVisible(False)
        self.column: int | None = None
        self._values: list[str] = []
        self._current = 0
        self._suspend = False
        self._use_slider = False
        self.tabbar.currentChanged.connect(self._tab_changed)
        self._set_slider_controls_visible(False)

    @property
    def table(self):
        """The configured view, or ``None`` once Qt has torn it down."""
        return self._table_ref()

    @property
    def is_active(self) -> bool:
        return self.column is not None

    def _model(self):
        table = self.table
        model = table.model() if table is not None else None
        return model if hasattr(model, "set_filter_values") else None

    def _clear_tabs(self) -> None:
        # QTabBar has no ``clear()`` (unlike QComboBox/QListWidget) — remove
        # from the end so shifting indices never skip a tab.
        for index in range(self.tabbar.count() - 1, -1, -1):
            self.tabbar.removeTab(index)

    def _column_name(self, column: int) -> str:
        table = self.table
        model = table.model() if table is not None else None
        if model is None:
            return str(column + 1)
        return str(model.headerData(column, Qt.Horizontal, Qt.DisplayRole) or column + 1)

    def cardinality(self, column: int) -> tuple[int, bool, int]:
        """``(distinct non-blank values, has_blank, total rows)`` — based on
        the data actually present, never on the column's name."""
        model = self._model()
        if model is None:
            return 0, False, 0
        values = model.available_values(column)
        has_blank = any(not str(value).strip() for value in values)
        distinct = len(values) - (1 if has_blank else 0)
        return distinct, has_blank, model.rowCount()

    def recommendation(self, column: int) -> tuple[str, str, bool] | None:
        """``(title, message, default_is_yes)`` for the confirmation shown
        before activating a high-cardinality column, or ``None`` when the
        column is unremarkable and no dialog is needed at all."""
        distinct, _has_blank, _rows = self.cardinality(column)
        if distinct <= self.HINT_THRESHOLD:
            return None
        name = self._column_name(column)
        if distinct > self.STRONG_THRESHOLD:
            return (
                "Very many subtabs",
                f"'{name}' has {distinct} distinct values and would create {distinct} subtabs.\n\n"
                "This is very likely unsuitable for subtab navigation (e.g. a free-text, ID or "
                "GUID-like column) and may affect performance. Continue anyway?",
                False,
            )
        if distinct > self.WARN_THRESHOLD:
            return (
                "Many subtabs",
                f"'{name}' has {distinct} distinct values and would create {distinct} subtabs.\n\n"
                "That is a lot for comfortable tab navigation. Continue anyway?",
                True,
            )
        return (
            "Several subtabs",
            f"'{name}' has {distinct} distinct values and would create {distinct} subtabs. Continue?",
            True,
        )

    def request_activate(self, column: int, parent=None) -> bool:
        """Owner-facing entry point (the header's context-menu action): shows
        the cardinality recommendation when one applies, then activates only
        on confirmation. The final decision always stays with the user —
        this only ever adds one extra confirmation step, never a block."""
        if self._model() is None:
            # A handful of tables in the app still use a plain item model
            # instead of TableDataModel (no per-column value filter to drive
            # subtabs from) — say so instead of the menu item silently doing
            # nothing.
            QMessageBox.information(
                parent or self, "Subtabs not available",
                "This table does not support column-based subtabs.",
            )
            return False
        advice = self.recommendation(column)
        if advice is not None:
            title, message, default_yes = advice
            confirmed = QMessageBox.question(
                parent or self, title, message, QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes if default_yes else QMessageBox.No,
            )
            if confirmed != QMessageBox.Yes:
                return False
        self.activate(column)
        return True

    def _ensure_mounted(self) -> None:
        """Place this bar in the table's own layout, directly above it, the
        first time it is actually needed.

        Kit-wide rollout (owner request 2026-08-27, "Funktion global auf
        alle P3DDM anwenden"): ``configure_table_view()`` attaches a bar to
        *every* configured table automatically (see below), but at that
        moment the table itself has often not been added to its parent's
        layout yet — most call sites across the app run
        ``configure_table_view(table)`` before ``layout.addWidget(table)``.
        Deferring the actual mounting to first activation sidesteps that
        entirely: by the time a user right-clicks a live, visible table to
        group it, that table is guaranteed to already sit in a real layout.
        A caller that already placed the bar itself (``DrawingRegisterWidget``
        adds it explicitly right above the table, before either constructor
        call site needs this) is left untouched — this only ever fires once,
        and only when nothing has placed the bar yet.
        """
        table = self.table
        if table is None:
            return
        parent = table.parentWidget()
        if parent is None:
            return
        layout = parent.layout()
        if layout is None or layout.indexOf(self) >= 0:
            return
        index = layout.indexOf(table)
        if index < 0:
            return
        layout.insertWidget(index, self)

    def _set_slider_controls_visible(self, visible: bool) -> None:
        # ``slider_row`` is its own row (below the tab strip / All button) —
        # hiding only the buttons inside it would still leave an empty
        # visible row reserving vertical space, so the container itself is
        # toggled too. ``value_label`` lives in row 1 (next to All) and is
        # slider-mode-only, since the tab strip already shows the active
        # value's own label when tabs are used instead.
        self.slider_row.setVisible(visible)
        for widget in (self.prev_button, self.slider, self.next_button, self.value_label):
            widget.setVisible(visible)

    def activate(self, column: int) -> None:
        """Build subtabs for ``column`` from the data currently loaded."""
        model = self._model()
        if model is None:
            return
        self._ensure_mounted()
        values = model.available_values(column)
        non_blank = sorted((value for value in values if str(value).strip()), key=natural_sort_key)
        has_blank = any(not str(value).strip() for value in values)
        self.column = column
        # Index 0 is always "All" — represented by the pinned button, never
        # a tab/slider position, so it can never scroll or slide away.
        self._values = [_SUBTAB_ALL] + non_blank + ([_SUBTAB_BLANK] if has_blank else [])
        nav_values = self._values[1:]
        self._suspend = True
        self._clear_tabs()
        for value in nav_values:
            self.tabbar.addTab(NO_ASSIGNMENT_LABEL if value == _SUBTAB_BLANK else value)
        self._use_slider = len(nav_values) > self.SLIDER_THRESHOLD
        self.tabbar.setVisible(not self._use_slider)
        self._set_slider_controls_visible(self._use_slider)
        self.slider.setMinimum(0)
        self.slider.setMaximum(max(0, len(nav_values) - 1))
        self.slider.setValue(0)
        self.tabbar.setCurrentIndex(-1)
        self._suspend = False
        self.hint.setText(f"Subtabs: {self._column_name(column)} ({len(non_blank)} values)")
        self.setVisible(True)
        self._current = 0
        self.all_button.setChecked(True)
        self._update_value_label(0)
        model.set_filter_values(column, None)
        self.changed.emit()

    def deactivate(self) -> None:
        """Remove the grouping entirely — the "back to base table" action.
        Only the active display filter is cleared; row data is untouched."""
        model = self._model()
        if model is not None and self.column is not None:
            model.set_filter_values(self.column, None)
        self.column = None
        self._values = []
        self._current = 0
        self._suspend = True
        self._clear_tabs()
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self._suspend = False
        self.setVisible(False)
        self.changed.emit()

    def _apply_filter(self, index: int) -> None:
        model = self._model()
        if model is None or self.column is None:
            return
        value = self._values[index] if 0 <= index < len(self._values) else _SUBTAB_ALL
        if value == _SUBTAB_ALL:
            model.set_filter_values(self.column, None)
        elif value == _SUBTAB_BLANK:
            model.set_filter_values(self.column, [""])
        else:
            model.set_filter_values(self.column, [value])

    def _update_value_label(self, index: int) -> None:
        if index <= 0 or index >= len(self._values):
            self.value_label.setText("")
            return
        value = self._values[index]
        label = NO_ASSIGNMENT_LABEL if value == _SUBTAB_BLANK else value
        self.value_label.setText(f"{label}  ({index}/{len(self._values) - 1})")

    def _select(self, index: int) -> None:
        """Single point of truth for "which value is active" — drives the
        pinned All button, the tab strip, the slider and the model filter
        together, whichever combination of controls is currently visible."""
        if not (0 <= index < len(self._values)):
            return
        self._current = index
        self._suspend = True
        self.all_button.setChecked(index == 0)
        nav_index = index - 1
        if index == 0:
            self.tabbar.setCurrentIndex(-1)
        elif self.tabbar.currentIndex() != nav_index:
            self.tabbar.setCurrentIndex(nav_index)
        if index > 0 and self.slider.value() != nav_index:
            self.slider.setValue(nav_index)
        self._suspend = False
        self._update_value_label(index)
        self._apply_filter(index)
        self.changed.emit()

    def _tab_changed(self, nav_index: int) -> None:
        if self._suspend or self.column is None or nav_index < 0:
            return
        self._select(nav_index + 1)

    def _slider_changed(self, nav_index: int) -> None:
        if self._suspend or self.column is None:
            return
        self._select(nav_index + 1)

    def _step(self, delta: int) -> None:
        """Prev/Next buttons — also reachable from a non-"All" position back
        down to "All" itself, one consistent way to page through everything."""
        if self.column is None:
            return
        self._select(max(0, min(len(self._values) - 1, self._current + delta)))

    def reapply_filter(self) -> None:
        """Re-apply the currently active tab's filter to whatever model the
        table now has (e.g. after a data refresh replaced the model with a
        fresh, unfiltered one). No-op when no grouping is active."""
        if self.column is not None:
            self._apply_filter(self._current)

    def capture(self) -> dict:
        """Grouping column (by name, stable across model rebuilds) plus the
        active value — a tool folds this into its own view-save payload
        exactly like it already does for ``value_filters`` etc."""
        table = self.table
        if table is None or self.column is None:
            return {}
        headers = _headers(table)
        if not (0 <= self.column < len(headers)):
            return {}
        active = self._values[self._current] if 0 <= self._current < len(self._values) else _SUBTAB_ALL
        return {"subtab_column": headers[self.column], "subtab_active": active}

    def apply(self, state: dict) -> None:
        """Restore what :meth:`capture` returned, or deactivate when the
        stored column no longer exists (e.g. after a data-source change)."""
        table = self.table
        if table is None:
            return
        headers = _headers(table)
        name = str(state.get("subtab_column") or "")
        if not name or name not in headers:
            self.deactivate()
            return
        self.activate(headers.index(name))
        active = str(state.get("subtab_active") or _SUBTAB_ALL)
        if active in self._values:
            self._select(self._values.index(active))


def configure_dynamic_subtabs(table: QTableView) -> DynamicSubtabBar:
    """Attach the Dynamic Subtabs strip to an already-configured table and
    wire it into ``ColumnFilterHeader``'s right-click menu ("Create Subtabs
    from '<column>'" / "Remove Subtabs (back to base table)"). Call once per
    table; returns the existing bar on a repeat call for the same table.

    The caller places the returned widget in its own layout directly above
    ``table`` — one line, the same pattern as every other Kit widget:

        self.subtabs = configure_dynamic_subtabs(self.table)
        self.layout_main.addWidget(self.subtabs)
        self.layout_main.addWidget(self.table, 1)
    """
    existing = getattr(table, "_shared_subtab_bar", None)
    if isinstance(existing, DynamicSubtabBar):
        return existing
    return DynamicSubtabBar(table)


class ValueFilterDialog(QDialog):
    """Searchable exact-value selection shared by every configured table."""

    def __init__(self, values, selected, parent=None, *, column_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle(f"Filter values - {column_name}" if column_name else "Filter values")
        self.resize(360, 480)
        self._all_values = list(values)
        self._initial = set(selected)
        layout = QVBoxLayout(self)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search values...")
        layout.addWidget(self.search)
        actions = QHBoxLayout()
        select_all = QPushButton("Select All"); clear = QPushButton("Clear")
        self.count = QLabel()
        actions.addWidget(select_all); actions.addWidget(clear); actions.addStretch(1); actions.addWidget(self.count)
        layout.addLayout(actions)
        self.list = QListWidget(); self.list.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.list, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        self._ok = buttons.button(QDialogButtonBox.Ok)
        layout.addWidget(buttons)
        self.search.textChanged.connect(self._apply_search)
        select_all.clicked.connect(lambda: self._set_visible(Qt.Checked))
        clear.clicked.connect(lambda: self._set_visible(Qt.Unchecked))
        self._populate()

    def _populate(self):
        self.list.clear()
        selected = {filter_key(value) for value in self._initial} or {filter_key(value) for value in self._all_values}
        for value in self._all_values:
            item = QListWidgetItem("(Blank)" if not str(value).strip() else value)
            item.setData(Qt.UserRole, value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if filter_key(value) in selected else Qt.Unchecked)
            self.list.addItem(item)
        self.list.itemChanged.connect(lambda _item: self._update_count())
        self._update_count()

    def _matches_search(self, item) -> bool:
        needle = self.search.text().casefold().strip()
        return not needle or needle in str(item.data(Qt.UserRole)).casefold()

    def _apply_search(self, text):
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setHidden(not self._matches_search(item))
        self._update_count()

    def _set_visible(self, state):
        for row in range(self.list.count()):
            item = self.list.item(row)
            if self._matches_search(item):
                item.setCheckState(state)

    def _update_count(self):
        chosen = len(self.selected_values())
        self.count.setText(f"{chosen} / {self.list.count()} values")
        self._ok.setEnabled(chosen > 0)  # nothing chosen would silently mean "show all"

    def selected_values(self):
        """Checked values; with a search text only the matching ones (Excel AutoFilter):
        values hidden by the search are never part of the result, even if checked."""
        return [str(self.list.item(row).data(Qt.UserRole)) for row in range(self.list.count())
                if self.list.item(row).checkState() == Qt.Checked
                and self._matches_search(self.list.item(row))]

    def has_restriction(self):
        return len(self.selected_values()) != self.list.count()


class SortColumnsDialog(QDialog):
    """Full multi-column sort configuration (C04.4, WIKI_V0.20 Abschnitt 6):
    priority list with explicit direction per key, including hidden columns
    — Shift+Click on a visible header is the quick path for the common case,
    this dialog is the only way to add a currently-hidden column (which has
    no clickable header at all) and covers the confirm-before-unhide rule.
    """

    def __init__(self, headers: list[str], hidden: set[int], sortable: set[int] | None,
                 current_spec: list[tuple[int, "Qt.SortOrder"]], parent=None, *,
                 extra_flag_label: str | None = None, extra_flag_hint: str = "",
                 current_extra_value: str = ""):
        """``extra_flag_label`` opts into one extra per-dialog choice below the
        priority list — a single column picked from the *active* sort levels,
        exposed as ``result_extra_value`` (its header name, or ``""``). Added
        2026-08-25 (owner request, "Sort / Levels" tool-wide rollout) to let
        ``SortColumnsDialog`` also cover Drawing Register's "Excel split"
        column — one flag attached to a sort level — instead of that staying
        a separate, local dialog. ``None`` (the default) keeps every existing
        caller's dialog pixel-identical to before this change."""
        super().__init__(parent)
        self.setWindowTitle("Sort")
        self.resize(420, 360 if extra_flag_label is None else 410)
        self._headers = list(headers)
        self._hidden = set(hidden)
        self._sortable = sortable  # None = every column allowed
        self._extra_flag_label = extra_flag_label
        self._extra_value = str(current_extra_value or "")
        self.result_spec: list[tuple[int, "Qt.SortOrder"]] = []
        self.result_unhide: set[int] = set()
        self.result_extra_value: str = ""

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Sort priority, highest first. Direction toggles per column. A hidden "
            "column can be added here — you will be asked before it is shown."
        ))
        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        controls = QHBoxLayout()
        self.picker = QComboBox()
        controls.addWidget(self.picker, 1)
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_selected)
        controls.addWidget(add_button)
        layout.addLayout(controls)

        row_buttons = QHBoxLayout()
        up_button = QPushButton("Move up"); up_button.clicked.connect(lambda: self._move(-1))
        down_button = QPushButton("Move down"); down_button.clicked.connect(lambda: self._move(1))
        toggle_button = QPushButton("Toggle direction"); toggle_button.clicked.connect(self._toggle_direction)
        remove_button = QPushButton("Remove"); remove_button.clicked.connect(self._remove_selected)
        for button in (up_button, down_button, toggle_button, remove_button):
            row_buttons.addWidget(button)
        layout.addLayout(row_buttons)

        clear_button = QPushButton("Clear all")
        clear_button.clicked.connect(self._clear_all)
        layout.addWidget(clear_button)

        self.extra_picker = None
        if extra_flag_label:
            extra_row = QHBoxLayout()
            extra_row.addWidget(QLabel(f"{extra_flag_label}:"))
            self.extra_picker = QComboBox()
            if extra_flag_hint:
                self.extra_picker.setToolTip(extra_flag_hint)
            self.extra_picker.currentIndexChanged.connect(self._extra_picker_changed)
            extra_row.addWidget(self.extra_picker, 1)
            layout.addLayout(extra_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._spec = [(column, order) for column, order in current_spec if self._allowed(column)]
        self._refresh_picker()
        self._refresh_list()

    def _allowed(self, column: int) -> bool:
        return 0 <= column < len(self._headers) and (self._sortable is None or column in self._sortable)

    def _label(self, column: int) -> str:
        name = self._headers[column] if 0 <= column < len(self._headers) else str(column)
        return f"{name} (hidden)" if column in self._hidden else name

    def _refresh_picker(self) -> None:
        self.picker.clear()
        used = {column for column, _order in self._spec}
        for column, header in enumerate(self._headers):
            if self._allowed(column) and column not in used:
                self.picker.addItem(self._label(column), column)

    def _refresh_list(self) -> None:
        self.list.clear()
        for position, (column, order) in enumerate(self._spec, start=1):
            arrow = "ascending" if order == Qt.AscendingOrder else "descending"
            item = QListWidgetItem(f"{position}. {self._label(column)} — {arrow}")
            item.setData(Qt.UserRole, column)
            self.list.addItem(item)
        self._refresh_picker()
        self._refresh_extra_picker()

    def _refresh_extra_picker(self) -> None:
        """The extra flag can only attach to a column that is an active sort
        level — mirrors the original Drawing Register "Excel split" rule."""
        if self.extra_picker is None:
            return
        self.extra_picker.blockSignals(True)
        self.extra_picker.clear()
        self.extra_picker.addItem("(none)", "")
        select_index = 0
        for column, _order in self._spec:
            name = self._headers[column] if 0 <= column < len(self._headers) else str(column)
            self.extra_picker.addItem(name, name)
            if name == self._extra_value:
                select_index = self.extra_picker.count() - 1
        if self._extra_value not in {self._headers[column] for column, _order in self._spec}:
            self._extra_value = ""
        self.extra_picker.setCurrentIndex(select_index)
        self.extra_picker.blockSignals(False)

    def _extra_picker_changed(self, _index: int) -> None:
        self._extra_value = str(self.extra_picker.currentData() or "")

    def _add_selected(self) -> None:
        column = self.picker.currentData()
        if column is None:
            return
        self._spec.append((int(column), Qt.AscendingOrder))
        self._refresh_list()

    def _selected_row(self) -> int:
        return self.list.currentRow()

    def _move(self, offset: int) -> None:
        row = self._selected_row()
        target = row + offset
        if row < 0 or not (0 <= target < len(self._spec)):
            return
        self._spec[row], self._spec[target] = self._spec[target], self._spec[row]
        self._refresh_list()
        self.list.setCurrentRow(target)

    def _toggle_direction(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        column, order = self._spec[row]
        self._spec[row] = (column, Qt.DescendingOrder if order == Qt.AscendingOrder else Qt.AscendingOrder)
        self._refresh_list()
        self.list.setCurrentRow(row)

    def _remove_selected(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        del self._spec[row]
        self._refresh_list()

    def _clear_all(self) -> None:
        self._spec = []
        self._refresh_list()

    def _accept(self) -> None:
        newly_hidden = {column for column, _order in self._spec if column in self._hidden}
        if newly_hidden:
            names = ", ".join(self._headers[column] for column in sorted(newly_hidden, key=lambda c: self._headers[c]))
            confirmed = QMessageBox.question(
                self, "Show hidden column(s) to sort by them?",
                f"These columns are currently hidden: {names}.\n\n"
                "They must be shown to sort by them. Show them now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirmed != QMessageBox.Yes:
                return
            self.result_unhide = newly_hidden
        self.result_spec = list(self._spec)
        self.result_extra_value = self._extra_value if self.extra_picker is not None else ""
        self.accept()


class ViewManagerDialog(QDialog):
    """Save, load and reset a named "view" of arbitrary caller-defined state.

    Generalised 2026-08-25 (owner request: Drawing Register's "Table
    Views..." button, "Hide Linked Fields"/"Sort / Levels..." pattern made
    the tool-wide standard) from what was previously P3D's
    ``DrawingRegisterWidget._show_view_manager`` — a bespoke, undocumented
    dialog only that one table had. A "view" here is not limited to table
    layout (column order/width/visibility/sort, already covered separately
    by :func:`bind_layout_persistence`/:class:`TableAdminBar`): it is
    whatever ``capture()``/``apply_settings()`` say it is — filters, search
    text, custom per-tool toggles, or a package/tile selection state that
    is not backed by a ``QTableView`` at all. This is what makes the same
    dialog reusable for a table AND for something like a package-selection
    checkbox grid.

    ``local_store``/``local_key`` are mandatory (every view is at least
    locally rememberable). ``project_views``/``save_project_view`` are
    optional callables — supply both to additionally offer "Store in active
    project profile" the way Drawing Register does; omit both (default) to
    hide that checkbox entirely for callers with no project-profile concept.
    """

    def __init__(self, *, title: str, capture, apply_settings, reset=None,
                 local_store: ViewSettingsStore, local_key: str,
                 project_views=None, save_project_view=None, project_scope_available: bool = True,
                 description: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(620)
        self._capture = capture
        self._apply_settings = apply_settings
        self._reset = reset
        self._local_store = local_store
        self._local_key = local_key
        self._project_views = project_views
        self._save_project_view = save_project_view
        project_capable = project_views is not None and save_project_view is not None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.choice = QComboBox()
        form.addRow("Saved view:", self.choice)
        self.project_scope = QCheckBox("Store in active project profile")
        self.project_scope.setVisible(project_capable)
        # ``project_scope_available=False`` (e.g. no active named project
        # profile) keeps the checkbox visible but disabled instead of hiding
        # it, so its presence still hints the feature exists.
        self.project_scope.setEnabled(project_scope_available)
        self.project_scope.setToolTip(
            "When enabled, the view is saved in the active named project profile and travels with that profile."
        )
        if project_capable:
            form.addRow("Storage:", self.project_scope)
        layout.addLayout(form)
        self.state = QLabel(description or "A view stores whatever this tool captures for it.")
        self.state.setWordWrap(True)
        layout.addWidget(self.state)

        actions = QHBoxLayout()
        buttons_spec = [("Save View", self._save), ("Load View", self._load)]
        if reset is not None:
            buttons_spec.insert(0, ("New View", self._new))
        for label, callback in buttons_spec:
            button = QPushButton(label)
            button.clicked.connect(callback)
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)
        layout.addWidget(close_buttons)
        self._refresh_choices()

    def _refresh_choices(self, selected: str = "") -> None:
        self.choice.clear()
        for name in self._local_store.profiles(self._local_key):
            self.choice.addItem(f"{name} — Local", f"local\0{name}")
        if self._project_views is not None:
            for name in sorted(self._project_views(), key=str.casefold):
                self.choice.addItem(f"{name} — Project profile", f"project\0{name}")
        if selected:
            index = self.choice.findData(selected)
            if index >= 0:
                self.choice.setCurrentIndex(index)

    def _new(self) -> None:
        self._reset()
        self.choice.setCurrentIndex(-1)
        self.state.setText("New unsaved view created from the defaults. Adjust it, then select Save View.")

    def _save(self) -> None:
        default_name = self.choice.currentText().split(" — ", 1)[0] if self.choice.currentIndex() >= 0 else ""
        name, accepted = QInputDialog.getText(self, "Save view", "View name", text=default_name)
        name = name.strip()
        if not accepted or not name:
            return
        settings = self._capture()
        if self.project_scope.isChecked():
            views = self._project_views()
            if name in views and QMessageBox.question(
                self, "Replace project view", f"Replace project view '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            self._save_project_view(name, settings)
            key = f"project\0{name}"
            self.state.setText(f"Project-profile view '{name}' saved.")
        else:
            if name in self._local_store.profiles(self._local_key) and QMessageBox.question(
                self, "Replace local view", f"Replace local view '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            self._local_store.save(self._local_key, name, settings)
            key = f"local\0{name}"
            self.state.setText(f"Local view '{name}' saved.")
        self._refresh_choices(key)

    def _load(self) -> None:
        value = str(self.choice.currentData() or "")
        scope, separator, name = value.partition("\0")
        if not separator:
            self.state.setText("Select a saved view first.")
            return
        settings = (
            self._project_views().get(name, {})
            if scope == "project" else self._local_store.load(self._local_key, name)
        )
        if not settings:
            self.state.setText(f"View '{name}' is no longer available.")
            self._refresh_choices()
            return
        self._apply_settings(settings)
        self.state.setText(f"{scope.title()} view '{name}' loaded.")


class TableViewAndSortDialog(QDialog):
    """One dialog for "Table Views" (:class:`ViewManagerDialog`) and "Sort /
    Levels" (:class:`SortColumnsDialog`) — owner review (V0.21+0.22 Review,
    Folie 9: "Tabel view und sort/Level in einer dialogbox zusammenfassen -
    layout und funktionen exakt uebernehmen"; Folie 10's exact legacy
    Pipe-class-output-profile layout was explicitly deferred by the owner —
    only Folie 9's merge itself is in scope here).

    A saved view already captures the full multi-column sort spec
    (:func:`capture_table_layout`'s ``sort_columns``), so the two dialogs
    were already overlapping, not two unrelated concerns: Save View here
    persists whatever sort priority is currently applied, same as before.

    Kept as an *additional* class next to :class:`ViewManagerDialog` and
    :class:`SortColumnsDialog` rather than replacing them — neither existing
    class is touched, so any caller not yet rolled onto this one keeps
    working exactly as it does today (Regel 26 still holds: one shared
    implementation going forward, introduced without breaking the two it
    grew out of).

    View section (Saved view / Storage / New / Save / Load) behaves exactly
    like :class:`ViewManagerDialog` — those actions apply immediately, no
    separate confirm step. The Sort section keeps the deferred-until-
    confirmed model (edits stay local until "Apply Sort", which is also
    where a currently-hidden column being added still gets the
    confirm-before-unhide question, WIKI_V0.20 Abschnitt 6), but its layout
    is the pre-v0.21 local ``DrawingSortLevelsDialog`` table (Level/Column/
    Direction/extra-flag columns, one row per priority, extra-flag as an
    in-row checkbox) rather than :class:`SortColumnsDialog`'s list — owner
    follow-up (V0.21+0.22 Review, Folie 9): the first cut used
    ``SortColumnsDialog``'s list-plus-dropdown editor, which the owner
    flagged as not matching Folie 9's lower box ("layout ... exakt
    uebernehmen" meant this table, not just the merge). Loading or
    resetting a view refreshes the sort editor from the table's new state
    so the two sections never show stale, contradictory information.
    """

    def __init__(self, *, title: str, capture, apply_settings, reset=None,
                 local_store: ViewSettingsStore, local_key: str,
                 project_views=None, save_project_view=None, project_scope_available: bool = True,
                 description: str = "",
                 headers_getter, hidden_getter, sortable_getter, spec_getter, apply_sort,
                 extra_flag_label: str | None = None, extra_flag_hint: str = "",
                 extra_value_getter=None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(640)
        self._capture = capture
        self._apply_settings = apply_settings
        self._reset = reset
        self._local_store = local_store
        self._local_key = local_key
        self._project_views = project_views
        self._save_project_view = save_project_view
        project_capable = project_views is not None and save_project_view is not None

        self._headers_getter = headers_getter
        self._hidden_getter = hidden_getter
        self._sortable_getter = sortable_getter
        self._spec_getter = spec_getter
        self._apply_sort = apply_sort
        self._extra_flag_label = extra_flag_label
        self._extra_value_getter = extra_value_getter or (lambda: "")
        self._headers: list[str] = []
        self._hidden: set[int] = set()
        self._sortable: set[int] | None = None
        self._spec: list[tuple[int, "Qt.SortOrder"]] = []
        self._extra_value: str = ""

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.choice = QComboBox()
        form.addRow("Saved view:", self.choice)
        self.project_scope = QCheckBox("Store in active project profile")
        self.project_scope.setVisible(project_capable)
        self.project_scope.setEnabled(project_scope_available)
        self.project_scope.setToolTip(
            "When enabled, the view is saved in the active named project profile and travels with that profile."
        )
        if project_capable:
            form.addRow("Storage:", self.project_scope)
        layout.addLayout(form)
        self.state = QLabel(description or "A view stores whatever this tool captures for it.")
        self.state.setWordWrap(True)
        layout.addWidget(self.state)

        view_actions = QHBoxLayout()
        buttons_spec = [("Save View", self._save), ("Load View", self._load)]
        if reset is not None:
            buttons_spec.insert(0, ("New View", self._new))
        for label, callback in buttons_spec:
            button = QPushButton(label)
            button.clicked.connect(callback)
            view_actions.addWidget(button)
        view_actions.addStretch(1)
        layout.addLayout(view_actions)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Owner review (V0.21+0.22 Review, Folie 9): the sort section reuses
        # the pre-v0.21 ``DrawingSortLevelsDialog`` table layout (Level/
        # Column/Direction[/extra-flag], one row per priority, checkbox
        # in-row for the extra flag) instead of the shared kit's list-based
        # ``SortColumnsDialog`` — "layout und funktionen exakt uebernehmen".
        layout.addWidget(QLabel(
            "Level 1 is the highest priority. Text and embedded numbers use natural "
            "order (for example DWG-2 before DWG-10). A hidden column can be added "
            "here — you will be asked before it is shown. Apply Sort updates the "
            "table now; Save View above also keeps it with the rest of the view."
        ))
        column_labels = ["Level", "Column", "Direction"] + ([extra_flag_label] if extra_flag_label else [])
        self.level_table = QTableWidget(0, len(column_labels))
        self.level_table.setHorizontalHeaderLabels(column_labels)
        self.level_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.level_table.setSelectionMode(QTableWidget.SingleSelection)
        self.level_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.level_table.horizontalHeader().setStretchLastSection(True)
        if extra_flag_label and extra_flag_hint:
            self.level_table.horizontalHeaderItem(3).setToolTip(extra_flag_hint)
        self.level_table.itemChanged.connect(self._split_changed)
        layout.addWidget(self.level_table, 1)

        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Column:"))
        self.picker = QComboBox()
        add_row.addWidget(self.picker, 1)
        add_button = QPushButton("Add")
        add_button.clicked.connect(self._add_selected)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        sort_row_buttons = QHBoxLayout()
        up_button = QPushButton("Move up"); up_button.clicked.connect(lambda: self._move(-1))
        down_button = QPushButton("Move down"); down_button.clicked.connect(lambda: self._move(1))
        toggle_button = QPushButton("Toggle direction"); toggle_button.clicked.connect(self._toggle_direction)
        remove_button = QPushButton("Remove"); remove_button.clicked.connect(self._remove_selected)
        clear_button = QPushButton("Clear all"); clear_button.clicked.connect(self._clear_all)
        for button in (up_button, down_button, toggle_button, remove_button, clear_button):
            sort_row_buttons.addWidget(button)
        layout.addLayout(sort_row_buttons)

        apply_row = QHBoxLayout()
        apply_row.addStretch(1)
        apply_sort_button = QPushButton("Apply Sort")
        apply_sort_button.clicked.connect(self._apply_sort_clicked)
        apply_row.addWidget(apply_sort_button)
        layout.addLayout(apply_row)

        close_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.reject)
        layout.addWidget(close_buttons)

        self._refresh_choices()
        self._reload_sort_state()

    # -- View section (mirrors ViewManagerDialog) --------------------------
    def _refresh_choices(self, selected: str = "") -> None:
        self.choice.clear()
        for name in self._local_store.profiles(self._local_key):
            self.choice.addItem(f"{name} — Local", f"local\0{name}")
        if self._project_views is not None:
            for name in sorted(self._project_views(), key=str.casefold):
                self.choice.addItem(f"{name} — Project profile", f"project\0{name}")
        if selected:
            index = self.choice.findData(selected)
            if index >= 0:
                self.choice.setCurrentIndex(index)

    def _new(self) -> None:
        self._reset()
        self.choice.setCurrentIndex(-1)
        self.state.setText("New unsaved view created from the defaults. Adjust it, then select Save View.")
        self._reload_sort_state()

    def _save(self) -> None:
        default_name = self.choice.currentText().split(" — ", 1)[0] if self.choice.currentIndex() >= 0 else ""
        name, accepted = QInputDialog.getText(self, "Save view", "View name", text=default_name)
        name = name.strip()
        if not accepted or not name:
            return
        settings = self._capture()
        if self.project_scope.isChecked():
            views = self._project_views()
            if name in views and QMessageBox.question(
                self, "Replace project view", f"Replace project view '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            self._save_project_view(name, settings)
            key = f"project\0{name}"
            self.state.setText(f"Project-profile view '{name}' saved.")
        else:
            if name in self._local_store.profiles(self._local_key) and QMessageBox.question(
                self, "Replace local view", f"Replace local view '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
            ) != QMessageBox.Yes:
                return
            self._local_store.save(self._local_key, name, settings)
            key = f"local\0{name}"
            self.state.setText(f"Local view '{name}' saved.")
        self._refresh_choices(key)

    def _load(self) -> None:
        value = str(self.choice.currentData() or "")
        scope, separator, name = value.partition("\0")
        if not separator:
            self.state.setText("Select a saved view first.")
            return
        settings = (
            self._project_views().get(name, {})
            if scope == "project" else self._local_store.load(self._local_key, name)
        )
        if not settings:
            self.state.setText(f"View '{name}' is no longer available.")
            self._refresh_choices()
            return
        self._apply_settings(settings)
        self.state.setText(f"{scope.title()} view '{name}' loaded.")
        self._reload_sort_state()

    # -- Sort section (mirrors SortColumnsDialog) ---------------------------
    def _reload_sort_state(self) -> None:
        """Re-reads headers/hidden/sortable/spec from the caller's getters —
        called after any action (Load/New View) that can move the table out
        from under the sort editor while this dialog stays open."""
        self._headers = list(self._headers_getter())
        self._hidden = set(self._hidden_getter())
        self._sortable = self._sortable_getter()
        self._extra_value = str(self._extra_value_getter() or "")
        self._spec = [(column, order) for column, order in self._spec_getter_safe() if self._allowed(column)]
        self._refresh_list()

    def _spec_getter_safe(self):
        try:
            return list(self._spec_getter())
        except TypeError:
            return []

    def _allowed(self, column: int) -> bool:
        return 0 <= column < len(self._headers) and (self._sortable is None or column in self._sortable)

    def _label(self, column: int) -> str:
        name = self._headers[column] if 0 <= column < len(self._headers) else str(column)
        return f"{name} (hidden)" if column in self._hidden else name

    def _refresh_picker(self) -> None:
        self.picker.clear()
        used = {column for column, _order in self._spec}
        for column, header in enumerate(self._headers):
            if self._allowed(column) and column not in used:
                self.picker.addItem(self._label(column), column)

    def _refresh_list(self, selected: int = -1) -> None:
        self.level_table.blockSignals(True)
        self.level_table.setRowCount(len(self._spec))
        for row, (column, order) in enumerate(self._spec):
            values = (
                str(row + 1),
                self._label(column),
                "A-Z / 1-xxx" if order == Qt.AscendingOrder else "Z-A / xxx-1",
            )
            for index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.level_table.setItem(row, index, item)
            if self._extra_flag_label:
                name = self._headers[column] if 0 <= column < len(self._headers) else ""
                split_item = QTableWidgetItem("")
                split_item.setFlags((split_item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable)
                split_item.setCheckState(Qt.Checked if name == self._extra_value else Qt.Unchecked)
                self.level_table.setItem(row, 3, split_item)
        self.level_table.blockSignals(False)
        self.level_table.resizeColumnsToContents()
        if 0 <= selected < len(self._spec):
            self.level_table.selectRow(selected)
        self._refresh_picker()

    def _split_changed(self, item: QTableWidgetItem) -> None:
        # Owner review (V0.21+0.22 Review, Folie 9): exclusive checkbox per
        # row, exactly like the pre-v0.21 DrawingSortLevelsDialog — checking
        # one row's flag unchecks whichever row carried it before.
        if item.column() != 3 or not self._extra_flag_label:
            return
        row = item.row()
        if not (0 <= row < len(self._spec)):
            return
        column, _order = self._spec[row]
        name = self._headers[column] if 0 <= column < len(self._headers) else ""
        if item.checkState() == Qt.Checked:
            self._extra_value = name
        elif self._extra_value == name:
            self._extra_value = ""
        self._refresh_list(row)

    def _add_selected(self) -> None:
        column = self.picker.currentData()
        if column is None:
            return
        self._spec.append((int(column), Qt.AscendingOrder))
        self._refresh_list(len(self._spec) - 1)

    def _selected_row(self) -> int:
        return self.level_table.currentRow()

    def _move(self, offset: int) -> None:
        row = self._selected_row()
        target = row + offset
        if row < 0 or not (0 <= target < len(self._spec)):
            return
        self._spec[row], self._spec[target] = self._spec[target], self._spec[row]
        self._refresh_list(target)

    def _toggle_direction(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        column, order = self._spec[row]
        self._spec[row] = (column, Qt.DescendingOrder if order == Qt.AscendingOrder else Qt.AscendingOrder)
        self._refresh_list(row)

    def _remove_selected(self) -> None:
        row = self._selected_row()
        if row < 0:
            return
        column, _order = self._spec[row]
        name = self._headers[column] if 0 <= column < len(self._headers) else ""
        if self._extra_value == name:
            self._extra_value = ""
        del self._spec[row]
        self._refresh_list(min(row, len(self._spec) - 1))

    def _clear_all(self) -> None:
        self._spec = []
        self._extra_value = ""
        self._refresh_list()

    def _apply_sort_clicked(self) -> None:
        newly_hidden = {column for column, _order in self._spec if column in self._hidden}
        if newly_hidden:
            names = ", ".join(self._headers[column] for column in sorted(newly_hidden, key=lambda c: self._headers[c]))
            confirmed = QMessageBox.question(
                self, "Show hidden column(s) to sort by them?",
                f"These columns are currently hidden: {names}.\n\n"
                "They must be shown to sort by them. Show them now?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if confirmed != QMessageBox.Yes:
                return
        else:
            newly_hidden = set()
        self._apply_sort(list(self._spec), self._extra_value if self._extra_flag_label else "", newly_hidden)
        self._hidden -= newly_hidden
        self.state.setText("Sort applied to the table.")
        self._refresh_list()


def configure_table_view(table: QTableView, column_filters: bool = True) -> QTableView:
    """Apply the quiet, dense shared standard for read-only data tables."""
    table.setAlternatingRowColors(True)
    table.setSelectionBehavior(QTableView.SelectRows)
    table.setSelectionMode(QTableView.ExtendedSelection)
    table.setSortingEnabled(True)
    table.setWordWrap(False)
    table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    table.setMinimumHeight(220)
    table.verticalHeader().setVisible(True)
    table.verticalHeader().setDefaultSectionSize(22)
    table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
    digits = max(2, len(str(max(1, table.model().rowCount() if table.model() else 1))))
    table.verticalHeader().setFixedWidth(max(34, table.fontMetrics().horizontalAdvance("9" * digits) + 14))
    header = table.horizontalHeader()
    if column_filters and not isinstance(header, ColumnFilterHeader):
        header = ColumnFilterHeader(table)
        table.setHorizontalHeader(header)
    if isinstance(header, ColumnFilterHeader):
        header.bind_model()
        QTimer.singleShot(0, header.bind_model)
        header.filterChanged.connect(lambda view=table: schedule_autofit(view))
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setSectionsMovable(True)
    header.setStretchLastSection(True)
    # Every data surface opens in one predictable order: the first data
    # column ascending (natural numbers first, then case-insensitive text).
    # A later user click can still choose any other column or direction.
    if table.model() is not None and table.model().columnCount() > 0:
        table.sortByColumn(0, Qt.AscendingOrder)
    _bind_autofit(table)
    _bind_path_navigation(table)
    _persist_layout(table)
    # Dynamic Subtabs, rolled out kit-wide (owner request 2026-08-27,
    # "Funktion global auf alle P3DDM anwenden"): every flat table that goes
    # through the shared standard gets the header's "Create Subtabs from
    # this column" / "Remove Subtabs" menu for free, with nothing to change
    # at the individual call site. Deliberately not applied to
    # ``configure_tree_view`` — a value filter on a hierarchical model would
    # change parent/child visibility in ways a plain flat-table subtab strip
    # was never designed for, and no tree view asked for this feature yet.
    configure_dynamic_subtabs(table)
    return table


def configure_tree_view(tree: QTreeView, column_filters: bool = True, *, compact: bool = False) -> QTreeView:
    """Apply the shared sortable/filterable standard to hierarchical data.

    ``compact=True`` is the dense source/folder variant: taller default area,
    horizontal scrolling instead of a stretched last column. It replaces the local
    ``_configure_source_tree`` copies that used to re-set these properties by hand.
    """
    tree.setAlternatingRowColors(True)
    tree.setSelectionBehavior(QTreeView.SelectRows)
    tree.setSelectionMode(QTreeView.ExtendedSelection)
    tree.setSortingEnabled(True)
    tree.setWordWrap(False)
    tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    tree.setMinimumHeight(360 if compact else 220)
    if compact:
        tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    header = tree.header()
    if column_filters and not isinstance(header, ColumnFilterHeader):
        header = ColumnFilterHeader(tree)
        tree.setHeader(header)
    if isinstance(header, ColumnFilterHeader):
        header.bind_model()
        QTimer.singleShot(0, header.bind_model)
        header.filterChanged.connect(lambda view=tree: schedule_autofit(view))
    header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setSectionsMovable(True)
    header.setStretchLastSection(not compact)
    if tree.model() is not None and tree.model().columnCount() > 0:
        tree.sortByColumn(0, Qt.AscendingOrder)
    _bind_autofit(tree)
    _bind_path_navigation(tree)
    _persist_layout(tree)
    return tree


#: Row cap Qt scans per column in ``resizeColumnToContents()`` before
#: estimating the rest. ``-1`` (no limit) forces Qt to measure every row of
#: every column, on the GUI thread, on every model change — a real freeze on
#: tables with thousands of rows (owner report 2026-08-25: DCF Structure with
#: 10,000 loaded rows made the window "Not Responding" during this exact
#: call), and a direct violation of AGENTS.md Regel 8 ("kein Voll-Autofit
#: über zehntausende Zeilen"). 500 matches Qt's own historical default and is
#: enough rows to size columns sensibly without an unbounded full-table scan.
AUTOFIT_ROW_SAMPLE_LIMIT = 500


def fit_columns_with_margin(table: QTableView | QTreeView, margin: float = 0.10) -> None:
    """Fit a bounded table/tree and add 10 percent reading room per column.

    Call after a model change, not continuously during data loading. Column
    width is estimated from at most ``AUTOFIT_ROW_SAMPLE_LIMIT`` rows per
    column, never a full scan — see that constant's docstring.
    """
    if table is None:
        return
    model = table.model()
    if model is None:
        return
    header = _view_header(table)
    header.setResizeContentsPrecision(AUTOFIT_ROW_SAMPLE_LIMIT)
    # A column the user sized themselves is never re-fitted. Without this, the
    # automatic layout persistence and the automatic AutoFit would fight each
    # other and the remembered width would be lost on the next model change.
    protected = getattr(table, "_shared_user_widths", frozenset())
    names = _headers(table)
    previous = getattr(table, "_shared_autofit_running", False)
    table._shared_autofit_running = True
    try:
        # Column by column, never resizeColumnsToContents(): that would overwrite a
        # protected column before the loop below could exclude it.
        for column in range(model.columnCount()):
            if (names[column] if column < len(names) else "") not in protected:
                table.resizeColumnToContents(column)
        for column in range(model.columnCount()):
            if (names[column] if column < len(names) else "") in protected:
                continue
            width = table.columnWidth(column)
            reserve = table.indentation() if isinstance(table, QTreeView) and column == 0 else 0
            table.setColumnWidth(column, min(500, max(80, int((width + reserve) * (1.0 + margin)))))
    finally:
        table._shared_autofit_running = previous


#: --- Table size (zoom) ------------------------------------------------------
#:
#: A shared control, not a per-module rebuild: without it every module that
#: wants "show me more rows at once" invents its own font/row-height handling
#: and the surfaces drift apart (WIKI/10_GUI-Vorgabe.md §3: erweitern statt
#: kopieren).
#:
#: The range starts at 60 % because below that the header filter fields stop
#: being usable, and ends at 100 % because 100 % *is* the shared standard —
#: the control shrinks a dense table to fit more on screen, it does not invent
#: a second, larger look.
MIN_TABLE_ZOOM = 60
MAX_TABLE_ZOOM = 100
DEFAULT_TABLE_ZOOM = 100


def _zoom_baseline(view: QTableView | QTreeView) -> tuple[float, int]:
    """Font size and row height at 100 %, captured once per view.

    Captured on first use rather than recomputed, so repeated zooming never
    drifts (scaling an already scaled value shrinks a table to nothing).
    """
    baseline = getattr(view, "_shared_zoom_baseline", None)
    if baseline is None:
        font = view.font()
        points = font.pointSizeF() if font.pointSizeF() > 0 else 9.0
        rows = view.verticalHeader().defaultSectionSize() if isinstance(view, QTableView) else 22
        baseline = (float(points), int(max(14, rows)))
        view._shared_zoom_baseline = baseline
    return baseline


def table_zoom(view: QTableView | QTreeView) -> int:
    """Current size in percent — ``DEFAULT_TABLE_ZOOM`` when never changed."""
    return int(getattr(view, "_shared_table_zoom", DEFAULT_TABLE_ZOOM))


def apply_table_zoom(view: QTableView | QTreeView, percent: int) -> int:
    """Scale font and row height of one view; returns the applied percentage.

    Column widths are re-fitted afterwards, otherwise a shrunken table keeps
    its old, now far too wide columns and the zoom gains nothing. Columns the
    user sized by hand stay protected — ``fit_columns_with_margin()`` skips
    them, and that must not change just because the size changed.
    """
    percent = max(MIN_TABLE_ZOOM, min(MAX_TABLE_ZOOM, int(percent)))
    points, rows = _zoom_baseline(view)
    factor = percent / 100.0
    font = view.font()
    font.setPointSizeF(max(6.0, points * factor))
    view.setFont(font)
    if isinstance(view, QTableView):
        header = view.verticalHeader()
        header.setDefaultSectionSize(max(14, int(round(rows * factor))))
        digits = max(2, len(str(max(1, view.model().rowCount() if view.model() else 1))))
        header.setFixedWidth(max(28, view.fontMetrics().horizontalAdvance("9" * digits) + 14))
    view._shared_table_zoom = percent
    # Keep a bound slider in sync when the size is changed from elsewhere
    # (stored layout, Reset Layout) — a control showing 100 % on a 70 % table
    # is worse than no control.
    slider = getattr(view, "_shared_zoom_slider", None)
    if slider is not None and slider.value() != percent:
        slider.slider.blockSignals(True)
        slider.slider.setValue(percent)
        slider.slider.blockSignals(False)
        slider.value_label.setText(f"{percent} %")
    schedule_autofit(view)
    # The size is remembered like every other layout decision. The AutoFit above
    # runs with the "not a user resize" flag set, so without this the saver would
    # never hear about a zoom change.
    saver = getattr(view, "_shared_layout_saver", None)
    if saver is not None and not getattr(view, "_shared_zoom_applying", False):
        saver.start(400)
    return percent


class TableZoomSlider(QWidget):
    """``Size [====] 100 %`` — the shared table size control.

    Bound to one view. Tools place it in their table header row; the label is
    part of the widget so every module shows the value the same way.
    """

    zoomChanged = Signal(int)

    def __init__(self, view: QTableView | QTreeView, parent=None, *,
                 minimum: int = MIN_TABLE_ZOOM, maximum: int = MAX_TABLE_ZOOM,
                 label: str = "Size", width: int = 120):
        super().__init__(parent)
        self._view_ref = ref(view)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        if label:
            layout.addWidget(QLabel(label, self))
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(int(minimum), int(maximum))
        self.slider.setSingleStep(5)
        self.slider.setPageStep(10)
        self.slider.setFixedWidth(int(width))
        self.slider.setProperty("table-zoom", True)
        self.slider.setToolTip("Table size — smaller values fit more rows on screen")
        layout.addWidget(self.slider)
        self.value_label = QLabel(self)
        self.value_label.setMinimumWidth(38)
        layout.addWidget(self.value_label)
        self.slider.valueChanged.connect(self._changed)
        view._shared_zoom_slider = self
        self.slider.setValue(table_zoom(view))
        self._changed(self.slider.value())

    @property
    def view(self):
        """The bound view, or ``None`` once Qt has torn it down."""
        return self._view_ref()

    def value(self) -> int:
        return int(self.slider.value())

    def setValue(self, percent: int) -> None:  # noqa: N802 - Qt naming
        self.slider.setValue(int(percent))

    def _changed(self, percent: int) -> None:
        self.value_label.setText(f"{int(percent)} %")
        view = self.view
        if view is None:
            return
        applied = apply_table_zoom(view, percent)
        self.zoomChanged.emit(applied)


def table_zoom_slider(view: QTableView | QTreeView, parent=None, **kwargs) -> TableZoomSlider:
    """Convenience factory, mirroring ``configure_table_view`` in style."""
    return TableZoomSlider(view, parent, **kwargs)


def fit_table_height(table: QTableView, visible_rows: int = 12) -> None:
    """Avoid oversized empty table areas while retaining a useful scrolling view."""
    model = table.model()
    rows = model.rowCount() if model is not None else 0
    shown = max(1, min(rows, visible_rows))
    header_height = table.horizontalHeader().height() or 24
    height = header_height + shown * table.verticalHeader().defaultSectionSize() + 8
    table.setMinimumHeight(min(height, 120))
    table.setMaximumHeight(height)


def _view_header(view: QTableView | QTreeView) -> QHeaderView:
    """One accessor for both view types — trees expose header(), tables don't."""
    return view.header() if isinstance(view, QTreeView) else view.horizontalHeader()


def _headers(table: QTableView) -> list[str]:
    model = table.model()
    if model is None:
        return []
    return [str(model.headerData(index, Qt.Horizontal, Qt.DisplayRole) or "")
            for index in range(model.columnCount())]


def _typed_filter_text(header, column: int, fallback: str) -> str:
    """The content filter as the user typed it (the model keeps it case-folded)."""
    editors = getattr(header, "editors", [])
    text = editors[column].text().strip() if column < len(editors) else ""
    return text if text and text.casefold() == fallback else fallback


def capture_table_layout(table: QTableView | QTreeView) -> dict[str, Any]:
    headers = _headers(table)
    header = _view_header(table)
    model = table.model()
    sort_spec = model.sort_spec if hasattr(model, "sort_spec") else []
    return {
        "column_order": [headers[header.logicalIndex(visual)] for visual in range(header.count())],
        "hidden_columns": [name for index, name in enumerate(headers) if table.isColumnHidden(index)],
        "column_widths": {name: table.columnWidth(index) for index, name in enumerate(headers)},
        # Kept for tools/layouts predating C04.4 (single-column sort only) —
        # always the first/highest-priority entry of "sort_columns" below.
        "sort_column": headers[header.sortIndicatorSection()] if headers and 0 <= header.sortIndicatorSection() < len(headers) else "",
        "sort_order": "descending" if header.sortIndicatorOrder() == Qt.DescendingOrder else "ascending",
        # C04.4 (WIKI_V0.20 Abschnitt 6): the full user-chosen sort priority,
        # not just one column — empty when the model does not support it
        # (any consumer still on the pre-C04.4 single-key ``sort()`` API).
        "sort_columns": [
            {"column": headers[column], "order": "descending" if order == Qt.DescendingOrder else "ascending"}
            for column, order in sort_spec if 0 <= column < len(headers)
        ],
        # Part of "the surface as the user left it" — a remembered layout with
        # forgotten size would jump back to 100 % on every open.
        "table_zoom": table_zoom(table),
        # Owner request 2026-11-18 ("Tool merkt sich die vom User editierte
        # Tabelle"): alignment and the per-column filters belong to that too.
        # Keyed by header text like everything above; the global search box
        # is deliberately not part of a remembered view.
        "column_alignment": dict(getattr(table, "_col_align", {}) or {}),
        "column_filters": {headers[c]: _typed_filter_text(header, c, text)
                           for c, text in (getattr(model, "column_filters", {}) or {}).items() if 0 <= c < len(headers)},
        "value_filters": {headers[c]: sorted(values) for c, values in (getattr(model, "value_filters", {}) or {}).items()
                          if 0 <= c < len(headers)},
    }


def apply_table_layout(table: QTableView | QTreeView, layout: dict[str, Any]) -> None:
    headers = _headers(table)
    if not headers:
        return
    header = _view_header(table)
    for target, name in enumerate(str(item) for item in layout.get("column_order", [])):
        if name in headers:
            logical = headers.index(name)
            if header.visualIndex(logical) != target:
                header.moveSection(header.visualIndex(logical), target)
    hidden = {str(item) for item in layout.get("hidden_columns", [])}
    widths = layout.get("column_widths", {})
    for index, name in enumerate(headers):
        table.setColumnHidden(index, name in hidden)
        if name in widths:
            table.setColumnWidth(index, max(40, min(int(widths[name]), 900)))
    # C04.4: prefer the full multi-column spec when present; fall back to the
    # single "sort_column"/"sort_order" pair for layouts saved before C04.4.
    stored_spec = layout.get("sort_columns")
    model = table.model()
    if stored_spec and hasattr(model, "set_sort_spec"):
        spec = []
        for entry in stored_spec:
            name = str(entry.get("column", ""))
            if name in headers:
                order = Qt.DescendingOrder if entry.get("order") == "descending" else Qt.AscendingOrder
                spec.append((headers.index(name), order))
        if spec:
            # Keep Qt's own arrow pointed at the highest-priority column for
            # the native single-arrow visual, without letting its internal
            # click-simulated sort() call collapse the multi-column spec
            # we are about to set right after.
            header.blockSignals(True)
            header.setSortIndicator(spec[0][0], spec[0][1])
            header.blockSignals(False)
            model.set_sort_spec(spec)
    else:
        sort_name = str(layout.get("sort_column", ""))
        if sort_name in headers:
            order = Qt.DescendingOrder if layout.get("sort_order") == "descending" else Qt.AscendingOrder
            table.sortByColumn(headers.index(sort_name), order)
    _apply_alignment_and_filters(table, layout, headers)
    # Older stored layouts carry no size — those views stay at 100 %.
    if layout.get("table_zoom") is not None:
        table._shared_zoom_applying = True
        try:
            apply_table_zoom(table, int(layout["table_zoom"]))
        except (TypeError, ValueError):
            pass
        finally:
            table._shared_zoom_applying = False


def _apply_alignment_and_filters(table, layout: dict[str, Any], headers: list[str]) -> None:
    """Alignment and per-column filters of a remembered layout (keys absent in older layouts: nothing changes)."""
    if "column_alignment" in layout:
        table._col_align = {}
        stored = layout.get("column_alignment") or {}
        for side in ("center", "right"):
            columns = [headers.index(name) for name, value in stored.items() if value == side and name in headers]
            if columns:
                set_column_alignment(table, columns, side)
        table.viewport().update()
    model = table.model()
    header = _view_header(table)
    if "column_filters" in layout and hasattr(model, "set_column_filter"):
        texts = {headers.index(name): str(text) for name, text in (layout.get("column_filters") or {}).items() if name in headers}
        editors = getattr(header, "editors", [])
        for column in range(len(headers)):
            text = texts.get(column, "")
            if column < len(editors):
                editors[column].setText(text)          # the editor's signal sets the model filter
            else:
                model.set_column_filter(column, text)
    if "value_filters" in layout and hasattr(model, "set_filter_values"):
        stored = {name: values for name, values in (layout.get("value_filters") or {}).items() if name in headers}
        for column, name in enumerate(headers):
            active = column in (getattr(model, "value_filters", {}) or {})
            if name in stored:
                model.set_filter_values(column, [str(v) for v in stored[name]])
            elif active:
                model.set_filter_values(column, None)
                editors = getattr(header, "editors", [])
                if column < len(editors) and column not in (getattr(model, "column_filters", {}) or {}):
                    editors[column].blockSignals(True)
                    editors[column].setText("")
                    editors[column].blockSignals(False)
        if hasattr(header, "refresh_labels"):
            header.refresh_labels()
        if hasattr(header, "filterChanged"):
            header.filterChanged.emit()


def _default_layout(view) -> dict[str, Any]:
    """Optional tool-supplied default view: ``view._shared_layout_default`` = callable returning a layout dict."""
    provider = getattr(view, "_shared_layout_default", None)
    if not callable(provider):
        return {}
    try:
        layout = provider()
    except Exception:  # noqa: BLE001 - a broken default must never break the GUI
        return {}
    return layout if isinstance(layout, dict) else {}


def reset_remembered_view(table: QTableView | QTreeView) -> None:
    """Back to the standard: the tool's default view when it supplies one, otherwise column order/visibility of the
    model, no filters, left alignment, no sort. The remembered view is overwritten with that state."""
    reset_table_layout(table)
    _apply_alignment_and_filters(table, {"column_alignment": {}, "column_filters": {}, "value_filters": {}}, _headers(table))
    model = table.model()
    if hasattr(model, "set_sort_spec"):
        model.set_sort_spec([])
    header = _view_header(table)
    header.blockSignals(True)
    header.setSortIndicator(-1, Qt.AscendingOrder)
    header.blockSignals(False)
    default = _default_layout(table)
    if default:
        apply_table_layout(table, default)
    if hasattr(header, "_position_editors"):
        header._position_editors()
    saver = getattr(table, "_shared_layout_saver", None)
    if saver is not None:
        saver.start(0)


def reset_table_layout(table: QTableView | QTreeView) -> None:
    header = _view_header(table)
    for logical in range(header.count()):
        visual = header.visualIndex(logical)
        if visual != logical:
            header.moveSection(visual, logical)
        table.setColumnHidden(logical, False)
    # "Reset" means the shared standard, and that includes the size.
    apply_table_zoom(table, DEFAULT_TABLE_ZOOM)


#: A tool registers one provider and every configured surface is persisted from
#: then on. Without a provider nothing changes, so tools that have not opted in
#: keep their previous behaviour exactly.
_layout_provider: Callable[[QTableView | QTreeView], "tuple[ViewSettingsStore, str] | None"] | None = None


def set_layout_provider(provider) -> None:
    """Register where remembered column layouts are stored for this application.

    ``provider(view)`` returns ``(store, key)`` or ``None`` when a surface should
    not be persisted. The kit deliberately never decides the location or the
    project scope itself — that is the tool's knowledge.
    """
    global _layout_provider
    _layout_provider = provider


def _persist_layout(view: QTableView | QTreeView) -> None:
    if _layout_provider is None:
        return
    try:
        target = _layout_provider(view)
    except Exception:  # noqa: BLE001 - a settings problem must never break the GUI
        return
    if target:
        bind_layout_persistence(view, target[0], target[1])


def searchable_list(list_widget: QListWidget, *, placeholder: str = "Search...") -> QWidget:
    """Wrap an existing selection list in the shared search box.

    The list itself is returned unchanged inside the container, so every caller
    keeps its existing item API (``addItem``, ``currentItemChanged``, check states).
    Only non-matching entries are hidden — selection and indices stay intact.
    Reachable afterwards as ``container.list``.
    """
    container = QWidget(list_widget.parent())
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    search = QLineEdit(container)
    search.setPlaceholderText(placeholder)
    search.setClearButtonEnabled(True)
    search.setProperty("list-search", True)
    layout.addWidget(search)
    layout.addWidget(list_widget, 1)

    def apply(text: str) -> None:
        needle = filter_key(text)
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            item.setHidden(bool(needle and needle not in filter_key(item.text())))

    search.textChanged.connect(apply)
    container.list = list_widget
    container.search = search
    container.apply_search = apply
    return container


def bind_layout_persistence(view: QTableView | QTreeView, store: ViewSettingsStore, key: str,
                            profile: str = "Default") -> None:
    """Remember column width, order, visibility and sorting for one view.

    Saving is debounced and silent: the user simply finds the surface as they left
    it. Named layout profiles via :class:`TableAdminBar` stay available on top of
    this and use the same store. ``key`` is supplied by the tool and should carry
    the project identity, so two projects never overwrite each other's layout.
    """
    # Applied deferred: tools finish their own setup (default hidden columns,
    # reset to model order, first sort) synchronously after configure_*; the
    # remembered view the user left wins over that.
    def deferred(v=view) -> None:
        QTimer.singleShot(0, lambda: _ensure_layout_applied(v))

    if getattr(view, "_shared_layout_key", None) == key:
        deferred()                              # configured again (new model): re-apply for the new data
        return
    first_bind = getattr(view, "_shared_layout_key", None) is None
    view._shared_layout_key = key
    view._shared_layout_store = (store, key, profile)
    view._shared_layout_applied = None
    header = _view_header(view)
    if not first_bind:                          # re-bound to another key (e.g. another project): apply that one
        deferred()
        return

    saver = QTimer(view)
    saver.setSingleShot(True)
    #: Reachable for ``apply_table_zoom()``, which is not a header signal.
    view._shared_layout_saver = saver

    def store_layout() -> None:
        model = view.model()
        if model is None or model.columnCount() == 0:
            return
        # Owner request 2026-11-18: a view that receives its columns later (data
        # loaded after the view was configured) first gets its remembered layout;
        # only a layout applied to exactly these columns is ever written back, so
        # an empty or different table never overwrites what the user left.
        if _ensure_layout_applied(view):
            return
        current_store, current_key, current_profile = view._shared_layout_store
        try:
            current_store.save(current_key, current_profile, capture_table_layout(view))
        except (OSError, ValueError):
            # A read-only or missing configuration directory must never break the GUI.
            return

    saver.timeout.connect(store_layout)
    header.sectionCountChanged.connect(lambda *_args: deferred())
    if isinstance(header, ColumnFilterHeader):
        header.filterChanged.connect(lambda: saver.start(400))

    def user_resized(logical: int, _old: int, _new: int) -> None:
        # Only a resize outside our own AutoFit/apply run is the user's decision.
        if getattr(view, "_shared_autofit_running", False):
            return
        names = _headers(view)
        if 0 <= logical < len(names):
            view._shared_user_widths = set(getattr(view, "_shared_user_widths", ())) | {names[logical]}
        saver.start(400)

    header.sectionResized.connect(user_resized)
    header.sectionMoved.connect(lambda *_args: saver.start(400))
    header.sortIndicatorChanged.connect(lambda *_args: saver.start(400))

    deferred()


def _ensure_layout_applied(view) -> bool:
    """Apply the remembered layout once per model and set of columns. ``True`` when it was applied now
    (the caller then must not save in the same step), ``False`` when already current or nothing to apply."""
    if not shiboken6.isValid(view) or getattr(view, "_shared_layout_store", None) is None:
        return False
    model = view.model()
    headers = tuple(_headers(view))
    state = (id(model), headers)
    if not headers or state == getattr(view, "_shared_layout_applied", None):
        return False
    store, key, profile = view._shared_layout_store
    view._shared_layout_applied = state
    try:
        settings = store.load(key, profile)
    except (OSError, ValueError):
        settings = {}
    if not settings:
        settings = _default_layout(view)        # the tool's shared default view (e.g. saved with the list)
    if not settings:
        return True
    previous = getattr(view, "_shared_autofit_running", False)
    view._shared_autofit_running = True
    try:
        apply_table_layout(view, settings)
    finally:
        view._shared_autofit_running = previous
    view._shared_user_widths = {str(name) for name in settings.get("column_widths", {})}
    header = _view_header(view)
    if hasattr(header, "_position_editors"):
        header._position_editors()
    return True


class TableAdminBar(QWidget):
    """Save, load and reset named layouts for a configured table view."""

    def __init__(self, table: QTableView, store: ViewSettingsStore, key: str, parent=None):
        super().__init__(parent)
        self.table, self.store, self.key = table, store, key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Table layout"))
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        for label, callback in (("Save Layout", self._save), ("Load Layout", self._load), ("Reset Layout", self._reset)):
            button = QPushButton(label)
            button.setProperty("kind", "neutral")
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch(1)
        self.apply_last()

    def apply_last(self) -> None:
        name = self.store.last_profile(self.key)
        if name != "Default" or self.store.profiles(self.key):
            apply_table_layout(self.table, self.store.load(self.key, name))
        self.status_label.setText(f"Profile: {name}")

    def _save(self) -> None:
        name, accepted = QInputDialog.getText(self, "Save table layout", "Layout name", text=self.store.last_profile(self.key))
        if not accepted or not name.strip():
            return
        name = name.strip()
        if name in self.store.profiles(self.key):
            answer = QMessageBox.question(self, "Replace table layout", f"Replace '{name}'?", QMessageBox.Yes | QMessageBox.No)
            if answer != QMessageBox.Yes:
                return
        self.store.save(self.key, name, capture_table_layout(self.table))
        self.status_label.setText(f"Profile: {name}")

    def _load(self) -> None:
        names = self.store.profiles(self.key)
        if not names:
            QMessageBox.information(self, "Load table layout", "No saved layouts are available.")
            return
        name, accepted = QInputDialog.getItem(self, "Load table layout", "Layout name", names, editable=False)
        if accepted:
            apply_table_layout(self.table, self.store.load(self.key, name))
            self.status_label.setText(f"Profile: {name}")

    def _reset(self) -> None:
        reset_table_layout(self.table)
        self.status_label.setText("Profile: Default")
