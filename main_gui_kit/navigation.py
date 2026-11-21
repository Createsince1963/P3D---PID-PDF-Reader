"""Shared cross-module navigation helpers for the A1 sidebar shell.

Generalized from ``P3D_Data_Manager/src/p3d_data_manager/modules/base.py``
(the first consumer of ``SidebarMainWindow``) so other Qt6 tools migrating
onto the A1 shell — e.g. AZ Engineering Project Tool v0.70 — get the same
Back/Dashboard navigation and refresh convention from the kit instead of
re-implementing it locally.

``TopNavBar`` is intentionally host-agnostic: the "home" target (module +
tab to jump to when "Dashboard"/"Home" is pressed) is a constructor
parameter instead of a hardcoded P3D-specific default.
"""
from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from .buttons import ButtonKind, action_button
from .widgets import configure_module_tabs, page_title, section_label


def refresh_widget(widget: QWidget) -> bool:
    """Queue the standard refresh entry point of a newly selected view.

    Common switch/navigation rule for hosts built on ``SidebarMainWindow``:
    views keep their existing implementation; the shell only calls the first
    supported read-only load entry point and never invokes export, save,
    edit or write actions.
    """
    if widget is None:
        return False
    job = getattr(widget, "_job", None)
    if job is not None and hasattr(job, "isRunning") and job.isRunning():
        return False
    from PySide6.QtCore import QTimer

    for name in ("refresh_view", "_refresh", "_load_active_dcfs", "_prepare", "_load"):
        callback = getattr(widget, name, None)
        if callable(callback):
            QTimer.singleShot(0, callback)
            return True
    return False


def mark_tab_migration(tabs: QTabWidget, *indices: int, reason: str = "Function migration is not complete.") -> None:
    """Make incomplete functionality visible instead of presenting it as done."""
    for index in indices:
        if not 0 <= index < tabs.count():
            continue
        label = tabs.tabText(index)
        if "[IN MIGRATION]" not in label:
            tabs.setTabText(index, f"{label} [IN MIGRATION]")
        tabs.setTabToolTip(index, reason)


class TopNavBar(QWidget):
    """Shared 'Back' / home-target navigation row for module pages.

    Any module whose page includes this widget gets the two navigation
    buttons wired by the host's ``navigate_to(module_title, tab_title)``
    method — connect ``navigate_requested`` to it once per page.
    """

    navigate_requested = Signal(str, str)

    def __init__(self, home_module: str = "Dashboard", home_tab: str = "", home_label: str = "Dashboard", parent=None):
        super().__init__(parent)
        self._home_module = home_module
        self._home_tab = home_tab
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(6)
        self.back_button = action_button("< Back", ButtonKind.NEUTRAL)
        self.back_button.setAccessibleName("Back to the previously active tab")
        self.back_button.setToolTip("Return to the previously active module/tab")
        self.back_button.clicked.connect(lambda: self.navigate_requested.emit("__back__", ""))
        self.home_button = action_button(home_label, ButtonKind.NEUTRAL)
        self.home_button.setAccessibleName(f"Go to {home_label}")
        self.home_button.clicked.connect(lambda: self.navigate_requested.emit(self._home_module, self._home_tab))
        layout.addWidget(self.back_button)
        layout.addWidget(self.home_button)
        layout.addStretch(1)


def placeholder_page(title: str, subareas: Sequence[str]) -> QWidget:
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(4)
    lay.addWidget(page_title(title))
    lay.addWidget(section_label("placeholder — no business logic yet"))
    lay.addSpacing(10)  # clear gap so the tab bar never overlaps the heading

    tabs = configure_module_tabs(QTabWidget())
    for name in subareas:
        sub = QWidget()
        sl = QVBoxLayout(sub)
        lbl = QLabel(f"{name}\n\n(placeholder — to be implemented)")
        lbl.setAlignment(Qt.AlignCenter)
        sl.addWidget(lbl)
        tabs.addTab(sub, name)
    lay.addWidget(tabs, 1)
    return page
