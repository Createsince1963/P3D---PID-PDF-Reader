"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). Buttonleiste im Stil des Excel-Menuebands: Reiter "Plant3D-Schnittstelle" mit Gruppen (grosse und kleine Knoepfe)."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from main_gui_kit.theme import LIGHT

from .icons import ribbon_icon

_QSS = f"""
#Ribbon {{ background: {LIGHT.card}; border-bottom: 1px solid {LIGHT.border}; }}
#RibbonTab {{ color: {LIGHT.accent}; font-weight: 600; padding: 3px 14px; border-bottom: 2px solid {LIGHT.accent}; background: {LIGHT.card}; }}
#RibbonTabBar {{ background: {LIGHT.hdr}; }}
#RibbonGroupTitle {{ color: {LIGHT.txt_muted}; font-size: 7pt; background: transparent; }}
#RibbonGroup {{ background: {LIGHT.card}; }}
#RibbonSep {{ background: {LIGHT.border}; }}
#RibbonAreaCaption {{ color: {LIGHT.txt_muted}; font-size: 7pt; background: transparent; padding-left: 2px; }}
QToolButton[areaTab="true"] {{ background: {LIGHT.card}; border: 1px solid {LIGHT.border}; border-radius: 3px; padding: 1px 10px; color: {LIGHT.txt}; }}
QToolButton[areaTab="true"]:hover {{ background: {LIGHT.hdr}; }}
QToolButton[areaTab="true"][active="true"] {{ background: {LIGHT.accent}; border: 1px solid {LIGHT.accent}; color: white; font-weight: 600; }}
QToolButton[areaTab="true"]::menu-indicator {{ image: none; }}
QToolButton[ribbon="true"] {{ background: transparent; border: 1px solid transparent; border-radius: 3px; padding: 2px 4px; color: {LIGHT.txt}; }}
QToolButton[ribbon="true"]:hover {{ background: {LIGHT.hdr}; border: 1px solid {LIGHT.border}; }}
QToolButton[ribbon="true"]:pressed {{ background: {LIGHT.neutral}; }}
QToolButton[ribbon="true"]:disabled {{ color: #A9B4C6; }}
QToolButton[ribbon="true"]::menu-indicator {{ image: none; }}
"""


class RibbonGroup(QFrame):
    def __init__(self, ribbon: "Ribbon", title: str):
        super().__init__()
        self.ribbon = ribbon
        self.setObjectName("RibbonGroup")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 2, 6, 0)
        outer.setSpacing(0)
        self.row = QHBoxLayout()
        self.row.setSpacing(2)
        outer.addLayout(self.row, 1)
        self.title = QLabel(title)
        self.title.setObjectName("RibbonGroupTitle")
        self.title.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.title)

    def large(self, key: str, text: str, icon_key: str, slot: Callable, menu: QMenu | None = None) -> QToolButton:
        button = self.ribbon._make(key, text, icon_key, slot, large=True, menu=menu)
        self.row.addWidget(button)
        return button

    def column(self, specs: list[tuple]) -> None:
        """Senkrechte Box mit kleinen Knoepfen: ``(key, text, icon_key, slot[, menu])``."""
        box = QVBoxLayout()
        box.setSpacing(0)
        for spec in specs:
            key, text, icon_key, slot, *rest = spec
            box.addWidget(self.ribbon._make(key, text, icon_key, slot, large=False, menu=rest[0] if rest else None))
        box.addStretch(1)
        self.row.addLayout(box)


class Ribbon(QWidget):
    def __init__(self, tab_title: str = "Plant3D-Schnittstelle", parent=None):
        super().__init__(parent)
        self.setObjectName("Ribbon")
        self.setStyleSheet(_QSS)
        self.buttons: dict[str, QToolButton] = {}
        self.area_tabs: dict[str, QToolButton] = {}
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        bar = QWidget()
        bar.setObjectName("RibbonTabBar")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(8, 0, 8, 0)
        tab = QLabel(tab_title)
        tab.setObjectName("RibbonTab")
        bar_layout.addWidget(tab)
        self._bar_layout = bar_layout
        bar_layout.addStretch(1)
        root.addWidget(bar)
        body = QWidget()
        self.body = QHBoxLayout(body)
        self.body.setContentsMargins(4, 4, 4, 2)
        self.body.setSpacing(0)
        self.body.addStretch(1)
        root.addWidget(body)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def add_area_tabs(self, caption: str, areas: list[str], populate: Callable[[str, QMenu], None]) -> None:
        """Feste, kleine Bereichs-Tabs rechts neben dem Reiter: je Tab eine Aufklappliste (``populate(Bereich, Menue)``),
        kleine Textueberschrift darueber. Aktiver Bereich = wie gedrueckter Button (``set_active_area``)."""
        block = QWidget()
        outer = QVBoxLayout(block)
        outer.setContentsMargins(14, 1, 0, 1)
        outer.setSpacing(0)
        head = QLabel(caption)
        head.setObjectName("RibbonAreaCaption")
        outer.addWidget(head)
        row = QHBoxLayout()
        row.setSpacing(4)
        for area in areas:
            button = QToolButton()
            button.setProperty("areaTab", True)
            button.setProperty("active", False)
            button.setText(area.replace("&", "&&") + "  ▾")
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(f"{area}: Blatt öffnen")
            menu = QMenu(button)
            menu.aboutToShow.connect(lambda m=menu, a=area: (m.clear(), populate(a, m)))
            button.setMenu(menu)
            button.setPopupMode(QToolButton.InstantPopup)
            row.addWidget(button)
            self.area_tabs[area] = button
        self._area_row = row
        outer.addLayout(row)
        self._bar_layout.insertWidget(1, block)

    def set_area_order(self, order: list[str]) -> None:
        """Bereichs-Tabs in die Reihenfolge der Startseite bringen (unbekannte Bereiche bleiben hinten)."""
        row = getattr(self, "_area_row", None)
        if row is None:
            return
        names = [n for n in order if n in self.area_tabs] + [n for n in self.area_tabs if n not in order]
        for name in names:
            row.removeWidget(self.area_tabs[name])
        for name in names:
            row.addWidget(self.area_tabs[name])

    def set_active_area(self, area: str | None) -> None:
        for name, button in self.area_tabs.items():
            on = name == area
            if bool(button.property("active")) != on:
                button.setProperty("active", on)
                button.style().unpolish(button)
                button.style().polish(button)

    def group(self, title: str) -> RibbonGroup:
        group = RibbonGroup(self, title)
        group.sep = None                                   # Trennlinie davor (wird beim Einklappen mit ausgeblendet)
        if self.body.count() > 1:
            sep = QFrame()
            sep.setObjectName("RibbonSep")
            sep.setFixedWidth(1)
            self.body.insertWidget(self.body.count() - 1, sep)
            group.sep = sep
        self.body.insertWidget(self.body.count() - 1, group)
        return group

    def _make(self, key: str, text: str, icon_key: str, slot: Callable, *, large: bool, menu: QMenu | None) -> QToolButton:
        button = QToolButton()
        button.setProperty("ribbon", True)
        button.setText(text.replace("&", "&&"))
        metrics = button.fontMetrics()
        text_width = max(metrics.horizontalAdvance(line) for line in text.split("\n"))
        button.setIcon(ribbon_icon(icon_key, 32 if large else 18))
        button.setToolTip(text.replace("\n", " "))
        button.setCursor(Qt.PointingHandCursor)
        if large:
            button.setIconSize(QSize(30, 30))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setMinimumWidth(max(64, text_width + 22))
            button.setFixedHeight(68)
        else:
            button.setIconSize(QSize(16, 16))
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.setFixedHeight(21)
            button.setMinimumWidth(max(130, text_width + 16 + 26))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if menu is not None:
            button.setMenu(menu)
            button.setPopupMode(QToolButton.InstantPopup)
        else:
            button.clicked.connect(lambda _checked=False: slot())
        self.buttons[key] = button
        return button

    def set_enabled(self, key: str, enabled: bool) -> None:
        if key in self.buttons:
            self.buttons[key].setEnabled(enabled)

    def set_text(self, key: str, text: str) -> None:
        button = self.buttons.get(key)
        if button is not None:
            button.setText(text.replace("&", "&&"))
            button.setMinimumWidth(max(button.minimumWidth(), button.fontMetrics().horizontalAdvance(text) + 22))

    def set_visible(self, key: str, visible: bool) -> None:
        if key in self.buttons:
            self.buttons[key].setVisible(visible)
