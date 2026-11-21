"""Application shells: the pre-A1 tab shell and the current A1 sidebar shell.

``BaseMainWindow`` is the pre-A1 shell (top QTabWidget). It is carried over
unchanged for bundled/legacy consumers.

``SidebarMainWindow`` is A1 (left Sidebar + QStackedWidget), the current
shell for new and migrated tools — see ``P3D_Data_Manager`` for the
reference consumer and ``FusionTool_GUI_PhaseA_Detailplan.md`` for the
original design notes.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QStatusBar, QTabWidget, QToolButton, QVBoxLayout, QWidget

from .branding import BrandingManager, HeaderBanner
from .theme import ThemeManager


class BaseMainWindow(QMainWindow):
    def __init__(self, app, product_name: str, version: str,
                 branding: Optional[BrandingManager] = None, theme_start: str = "LIGHT"):
        super().__init__()
        self.setWindowTitle(f"{product_name} v{version}")
        self.resize(1200, 800)

        self.theme = ThemeManager(app, start=theme_start)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.header = HeaderBanner(product_name, version, branding=branding)
        layout.addWidget(self.header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def add_tab(self, widget: QWidget, title: str) -> int:
        return self.tabs.addTab(widget, title)

    def toggle_theme(self) -> None:
        self.theme.toggle()

    def status(self, message: str, timeout_ms: int = 4000) -> None:
        self.statusBar().showMessage(message, timeout_ms)


class SidebarMainWindow(QMainWindow):
    """A1 shared header/sidebar/stack shell. Consumers only add their pages."""
    def __init__(self, app, product_name: str, version: str, active_project: str = "(no project)"):
        super().__init__(); self.theme = ThemeManager(app, start="LIGHT"); self.setWindowTitle(f"{product_name} - {active_project}"); self.resize(1200, 780)
        central=QWidget(); root=QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.header = HeaderBanner(product_name, version); root.addWidget(self.header)
        body=QWidget(); body_layout=QHBoxLayout(body); body_layout.setContentsMargins(0,0,0,0); body_layout.setSpacing(0)
        self.sidebar=QFrame(); self.sidebar.setObjectName("Sidebar"); self.sidebar.setFixedWidth(240); self._sidebar_layout=QVBoxLayout(self.sidebar); self._sidebar_layout.setContentsMargins(8,8,8,8); self._sidebar_layout.setSpacing(4)
        self.stack=QStackedWidget(); self._group=QButtonGroup(self); self._group.setExclusive(True); self._group.idClicked.connect(self.stack.setCurrentIndex)
        self._sidebar_layout.addStretch(1); self._sidebar_layout.addWidget(QLabel(f"v{version}")); body_layout.addWidget(self.sidebar); body_layout.addWidget(self.stack,1); root.addWidget(body,1); self.setCentralWidget(central); self.setStatusBar(QStatusBar())
    def add_sidebar_page(self, title: str, page: QWidget) -> int:
        index=self.stack.count(); button=QToolButton(); button.setText(title.replace("&","&&")); button.setCheckable(True); button.setCursor(Qt.PointingHandCursor); button.setMinimumHeight(30); button.setStyleSheet("QToolButton{border:none;text-align:left;padding:6px 10px;border-radius:6px;}QToolButton:checked{background:#2F80ED;color:white;}QToolButton:hover:!checked{background:#E7ECF4;}")
        self._group.addButton(button,index); self._sidebar_layout.insertWidget(self._sidebar_layout.count()-2,button); self.stack.addWidget(page)
        if index==0: button.setChecked(True); self.stack.setCurrentIndex(0)
        return index

    def select_sidebar_page(self, index: int) -> None:
        """Select a registered module page for cross-module workflows."""
        if not 0 <= index < self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        button = self._group.button(index)
        if button is not None:
            button.setChecked(True)

    def toggle_theme(self) -> None:
        self.theme.toggle()

    def status(self, message: str, timeout_ms: int = 4000) -> None:
        self.statusBar().showMessage(message, timeout_ms)
