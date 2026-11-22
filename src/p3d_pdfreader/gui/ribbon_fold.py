"""Einklappbare Menueband-Gruppen (Nutzervorgabe 2026-11-22).

Klick auf die dunkelblaue Kopfleiste einer Gruppe klappt sie ein: die Gruppe verschwindet, ihre Kopfleiste steht dann
im Stapel hinter den sichtbaren Gruppen - je Spalte 4 Kopfleisten untereinander (Text linksbuendig), danach beginnt
eine neue Spalte.
Klick auf eine gestapelte Kopfleiste klappt die Gruppe an ihrer urspruenglichen Stelle wieder auf.

Standard (noch nichts gemerkt): nur die erste Gruppe (Projekt) offen, alle anderen eingeklappt. Beim Start stehen die
eingeklappten Kopfleisten in einer Reihe nebeneinander; nach dem ersten Ein-/Aufklappen wird wieder gestapelt.

``ribbon.py`` (Kopie aus P3D XCHANGE) bleibt unveraendert; Aussehen der Kopfleisten wie ``ribbon_heads``."""
from __future__ import annotations

from typing import Callable, Iterable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QPushButton, QSizePolicy, QWidget

from .ribbon import Ribbon, RibbonGroup
from .ribbon_heads import _qss

STACK_HEAD_HEIGHT = 20                                     # gestapelte Kopfleiste (8pt-Text)
STACK_ROWS = 4                                             # Kopfleisten je Spalte, danach neue Spalte (Nutzervorgabe)
COLLAPSE_TIP = "Klicken: Gruppe einklappen (Kopfleiste wandert in den Stapel rechts)"
EXPAND_TIP = "Klicken: Gruppe wieder aufklappen"


class RibbonFold(QObject):
    """Verwaltet ein-/ausgeklappte Gruppen eines ``Ribbon``. Schluessel einer Gruppe = deutscher Titel beim Anlegen."""

    def __init__(self, ribbon: Ribbon, collapsed: Iterable[str] | None = None,
                 on_change: Callable[[list[str]], None] | None = None):
        super().__init__(ribbon)
        self.ribbon = ribbon
        self.on_change = on_change
        body = ribbon.body
        self.groups: list[RibbonGroup] = [body.itemAt(i).widget() for i in range(body.count())
                                          if isinstance(body.itemAt(i).widget(), RibbonGroup)]
        self.keys: dict[int, str] = {id(g): g.title.text() for g in self.groups}
        if collapsed is None:                              # Standard: nur die erste Gruppe (Projekt) aufgeklappt
            collapsed = [g.title.text() for g in self.groups[1:]]
        wanted = set(collapsed)
        self.collapsed: set[str] = {k for k in self.keys.values() if k in wanted}
        # Trennlinie + Stapel hinter der letzten Gruppe (vor dem Abschluss-Stretch des Menuebands)
        self.stack_sep = QFrame()
        self.stack_sep.setObjectName("RibbonSep")
        self.stack_sep.setFixedWidth(1)
        self.stack = QWidget()
        self.stack.setObjectName("RibbonStack")
        self.grid = QGridLayout(self.stack)
        self.grid.setContentsMargins(6, 2, 6, 2)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(2)
        body.insertWidget(body.count() - 1, self.stack_sep)
        body.insertWidget(body.count() - 1, self.stack)
        self.stack_buttons: list[QPushButton] = []
        self.one_row = True                                # Startansicht: Kopfleisten in einer Reihe
        for group in self.groups:
            group.title.setCursor(Qt.PointingHandCursor)
            group.title.setToolTip(COLLAPSE_TIP)
            group.title.installEventFilter(self)
        self._refresh()

    # --- Zustand -------------------------------------------------------------------------------------------------
    def key(self, group: RibbonGroup) -> str:
        return self.keys[id(group)]

    def is_collapsed(self, group: RibbonGroup) -> bool:
        return self.key(group) in self.collapsed

    def set_collapsed(self, group: RibbonGroup, on: bool) -> None:
        key = self.key(group)
        if (key in self.collapsed) == on:
            return
        (self.collapsed.add if on else self.collapsed.discard)(key)
        self.one_row = False                               # ab jetzt wieder stapeln
        self._refresh()
        if self.on_change is not None:
            self.on_change(self.collapsed_keys())

    def collapsed_keys(self) -> list[str]:
        """Eingeklappte Gruppen in Menueband-Reihenfolge (zum Merken)."""
        return [self.key(g) for g in self.groups if self.is_collapsed(g)]

    # --- Anzeige -------------------------------------------------------------------------------------------------
    def _refresh(self) -> None:
        visible_before = False
        for group in self.groups:
            shown = not self.is_collapsed(group)
            group.setHidden(not shown)
            sep = getattr(group, "sep", None)
            if sep is not None:                            # Trennlinie nur zwischen zwei sichtbaren Gruppen
                sep.setHidden(not (shown and visible_before))
            visible_before = visible_before or shown
        for button in self.stack_buttons:
            self.grid.removeWidget(button)
            button.hide()                                  # sofort weg, nicht erst beim verzoegerten Loeschen
            button.deleteLater()
        self.stack_buttons = []
        folded = [g for g in self.groups if self.is_collapsed(g)]
        for index, group in enumerate(folded):
            button = QPushButton(self.stack)                # QPushButton: Text per QSS linksbuendig
            button.setObjectName("RibbonGroupHead")
            button.setStyleSheet(_qss().replace("}", " text-align: left; border: none; padding: 0px 6px;"
                                                     f" min-height: {STACK_HEAD_HEIGHT}px; max-height: {STACK_HEAD_HEIGHT}px; }}"))
            button.setText(group.title.text())
            button.setToolTip(EXPAND_TIP)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumWidth(90)
            button.setFixedHeight(STACK_HEAD_HEIGHT)          # 4 x 20 px + Abstaende = Hoehe einer Gruppe
            button.clicked.connect(lambda _checked=False, g=group: self.set_collapsed(g, False))
            row, col = (0, index) if self.one_row else (index % STACK_ROWS, index // STACK_ROWS)
            self.grid.addWidget(button, row, col, Qt.AlignTop)
            self.stack_buttons.append(button)
        self.grid.setRowStretch(STACK_ROWS, 1)
        self.stack.setHidden(not folded)
        self.stack_sep.setHidden(not (folded and visible_before))

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            for group in self.groups:
                if obj is group.title:
                    self.set_collapsed(group, True)
                    return True
        return super().eventFilter(obj, event)
