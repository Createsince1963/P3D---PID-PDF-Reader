"""Common composite widgets for main_gui_kit.

card() / field_row() / LogPanel carried over; page_title(), section_label() and
status_label() added for A3 (typography scale + status colors via property).
action_button is re-exported from buttons.py so existing imports keep working.
"""
from __future__ import annotations

from math import ceil

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QSplitter, QTabBar, QTabWidget,
    QVBoxLayout, QWidget, QSizePolicy,
)

from .buttons import ButtonKind, action_button  # re-export for compatibility

__all__ = [
    "card", "configure_combo_box", "configure_form_layout", "configure_module_tabs", "configure_readonly_path", "field_row", "master_detail_splitter", "page_header", "page_title", "section_label", "status_label",
    "LogPanel", "action_button", "ButtonKind",
]


def configure_readonly_path(edit: QLineEdit) -> QLineEdit:
    """Mark a downstream path display as read-only without an edit menu.

    Hub and Workspace own the editable source-path controls.  All other
    modules only display their centrally resolved paths and therefore must not
    offer Cut/Paste/Delete through Qt's standard context menu.
    """
    edit.setReadOnly(True)
    edit.setContextMenuPolicy(Qt.NoContextMenu)
    edit.setCursorPosition(0)
    return edit


class _StableTabBar(QTabBar):
    """Reserve enough room for the selected tab's bold text without eliding it."""

    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        bold_font = QFont(self.font())
        bold_font.setBold(True)
        text_width = QFontMetrics(bold_font).horizontalAdvance(self.tabText(index))
        # 10 percent room protects the label when the active font weight changes.
        required_width = ceil(text_width * 1.10) + 32
        return QSize(max(size.width(), required_width), size.height())


def configure_module_tabs(tabs: QTabWidget) -> QTabWidget:
    """Apply the global module-tab geometry and active-label readability rule."""
    tabs.setTabBar(_StableTabBar(tabs))
    tabs.setDocumentMode(True)
    tabs.setElideMode(Qt.ElideNone)
    tabs.tabBar().setExpanding(False)
    tabs.tabBar().setUsesScrollButtons(True)
    return tabs


def configure_combo_box(combo: QComboBox, reserve: float = 0.10, minimum: int = 110) -> QComboBox:
    """Keep the selected value and popup entries readable with a 10% reserve.

    Plant3D projects contain long area, revision and DCF names.  Qt's default
    combo geometry clips those values, particularly after an item becomes bold
    or a model is populated asynchronously.  The model signals keep this rule
    active for every later item insertion as well.
    """
    def update_width(*_args) -> None:
        metrics = QFontMetrics(combo.font())
        longest = max((metrics.horizontalAdvance(combo.itemText(index))
                       for index in range(combo.count())), default=0)
        width = max(minimum, ceil(longest * (1.0 + reserve)) + 42)
        combo.setMinimumWidth(width)
        combo.view().setMinimumWidth(width)
        # Show the complete value list whenever it fits on the current screen;
        # Qt keeps a scrollbar automatically when the popup would exceed it.
        combo.setMaxVisibleItems(max(1, combo.count()))

    combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
    model = combo.model()
    model.rowsInserted.connect(update_width)
    model.rowsRemoved.connect(update_width)
    model.modelReset.connect(update_width)
    combo.currentTextChanged.connect(update_width)
    update_width()
    return combo


def page_header(
    title: str, *actions: QWidget, subtitle: str = ""
) -> tuple[QHBoxLayout, QLabel]:
    """Return one compact title/action/description row.

    ``subtitle`` is intentionally placed after the flexible space and aligned
    right.  Views no longer need a second section-label row merely to explain
    their purpose, leaving that vertical space to the data surface below.
    """
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    headline = page_title(title)
    row.addWidget(headline)
    for action in actions:
        row.addWidget(action)
    row.addStretch(1)
    if subtitle:
        description = section_label(subtitle)
        description.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        description.setMinimumWidth(0)
        description.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        description.setToolTip(subtitle)
        row.addWidget(description, 1)
        row.description = description
    return row, headline


def card(title: str, body: QWidget) -> QGroupBox:
    """A titled card/section container. Title is upper-cased (BOMFusion/
    PlantSpecBridge convention); the 10pt bold style comes from QSS."""
    box = QGroupBox(title.upper())
    # Information cards stay compact; table/list views own the remaining page height.
    box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
    layout = QVBoxLayout(box)
    layout.addWidget(body)
    return box


def page_title(text: str) -> QLabel:
    """The single top headline of a view (12pt bold, one line) — styled via the
    dynamic property role='page-title'."""
    lbl = QLabel(text)
    lbl.setProperty("role", "page-title")
    return lbl


def section_label(text: str) -> QLabel:
    """A 10pt bold section caption (role='section')."""
    lbl = QLabel(text)
    lbl.setProperty("role", "section")
    return lbl


def status_label(text: str, level: str = "") -> QLabel:
    """A status text colored by semantic level: 'ok' | 'warn' | 'err' (or '' for
    default). Color comes from QSS via the dynamic property `level`."""
    lbl = QLabel(text)
    if level:
        lbl.setProperty("level", level)
    return lbl


def configure_form_layout(form: QFormLayout) -> QFormLayout:
    """Apply the aligned form standard used by engineering input surfaces."""
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    form.setHorizontalSpacing(12)
    form.setVerticalSpacing(10)
    return form


def master_detail_splitter(master: QWidget, detail: QWidget, master_width: int = 420) -> QSplitter:
    """Create the shared engineering master-detail layout for dense source lists."""
    splitter = QSplitter(Qt.Horizontal)
    splitter.addWidget(master)
    splitter.addWidget(detail)
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    splitter.setSizes([master_width, max(master_width, master_width * 2)])
    return splitter


def field_row(label_text: str) -> tuple[QWidget, QLineEdit]:
    """A labeled input row: returns (container_widget, line_edit)."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    label = QLabel(label_text)
    label.setFixedWidth(140)
    edit = QLineEdit()
    layout.addWidget(label)
    layout.addWidget(edit)
    return row, edit


class LogPanel(QPlainTextEdit):
    """Shared session-log widget with color-tagged append helpers.

    Colors are injected from the active Palette (via set_palette) so the log
    follows the theme instead of hard-coding hex values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        # sensible defaults until a palette is injected
        self._colors = {"ok": "#22C55E", "warn": "#F59E0B", "err": "#EF4444"}

    def set_palette(self, palette) -> None:
        """Feed the log colors from a theme.Palette (ok/warn/err tokens)."""
        self._colors = {"ok": palette.ok, "warn": palette.warn, "err": palette.err}

    def log(self, message: str, level: str = "info") -> None:
        color = self._colors.get(level, "")
        if color:
            self.appendHtml(f'<span style="color:{color}">{message}</span>')
        else:
            self.appendPlainText(message)
