"""Reusable preview dialog for tabular, read-only engineering data."""
from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QVBoxLayout

from .tables import MultiColumnFilterProxy, TableDataModel, configure_table_view, fit_columns_with_margin


class DataPreviewDialog(QDialog):
    """Searchable and sortable data preview built on the shared table standard."""

    def __init__(self, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1280, 760)
        self.model = TableDataModel(headers, rows, self)
        self.proxy = MultiColumnFilterProxy(self)
        self.proxy.setSourceModel(self.model)

        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Filter"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter all values...")
        self.filter_edit.textChanged.connect(self._filter_changed)
        controls.addWidget(self.filter_edit, 1)
        self.count_label = QLabel()
        controls.addWidget(self.count_label)
        clear_button = QPushButton("Clear Filter")
        clear_button.setProperty("kind", "neutral")
        clear_button.clicked.connect(self.filter_edit.clear)
        controls.addWidget(clear_button)
        layout.addLayout(controls)

        self.table = configure_table_view(QTableView())
        self.table.setModel(self.proxy)
        configure_table_view(self.table)
        fit_columns_with_margin(self.table)
        layout.addWidget(self.table, 1)
        self.proxy.modelReset.connect(self._update_count)
        self.proxy.rowsInserted.connect(lambda *_: self._update_count())
        self.proxy.rowsRemoved.connect(lambda *_: self._update_count())
        header = self.table.horizontalHeader()
        if hasattr(header, "filterChanged"):
            header.filterChanged.connect(self._update_count)
        self._update_count()

    def _filter_changed(self, text: str) -> None:
        self.proxy.set_global_filter(text)
        self._update_count()

    def _update_count(self) -> None:
        self.count_label.setText(f"{self.proxy.rowCount()} / {self.model.rowCount()} rows")
