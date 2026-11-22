"""Seitenleiste des Kachel-Editors (Bereich 2: Aktive Kachel, Gruppe, Verlauf) als Dock am rechten Fensterrand.

Uebernommen aus P3D Tag Compliance ``linetag_flowdeck.py``: angedockt rechts ueber die volle Fensterhoehe, einklappbar (nur
die Titelleiste bleibt), abloesbar als eigenes Fenster. Zustand in ``config/state.json`` (``tile_deck``) statt QSettings.
Jeder Kachel-Editor meldet seine Seitenleiste an (``attach``); gezeigt wird die des sichtbaren Editors."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QEvent, QObject, Qt, QTimer, QUrl
from PySide6.QtWidgets import QDockWidget, QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QToolButton, QWidget

from .. import last_paths
from ..design import SECTION_QSS

TITLE = "Aktive Kachel  ·  Gruppe  ·  Verlauf"
WIDTH = 330
STATE_KEY = "tile_deck"


def _state() -> dict:
    value = last_paths.get_value(STATE_KEY, {})
    return value if isinstance(value, dict) else {}


class _TitleBar(QWidget):
    def __init__(self, deck: "SideDeck"):
        super().__init__(deck)
        h = QHBoxLayout(self)
        h.setContentsMargins(8, 2, 4, 2)
        h.setSpacing(2)
        self.lb = QLabel(TITLE)
        self.lb.setStyleSheet(SECTION_QSS)
        h.addWidget(self.lb, 1)
        self.b_fold = QToolButton()
        self.b_fold.setAutoRaise(True)
        self.b_fold.setToolTip("Seitenleiste einklappen (nur die Titelleiste bleibt) / aufklappen")
        self.b_float = QToolButton()
        self.b_float.setAutoRaise(True)
        self.b_float.setText("⧉")
        self.b_float.setToolTip("Seitenleiste als eigenes Fenster lösen / wieder rechts andocken")
        for b in (self.b_fold, self.b_float):
            h.addWidget(b)
        self.b_fold.clicked.connect(deck.toggle_fold)
        self.b_float.clicked.connect(lambda: deck.setFloating(not deck.isFloating()))


class SideDeck(QDockWidget):
    def __init__(self, window: QMainWindow):
        super().__init__(TITLE, window)
        self.win = window
        self.setObjectName("tile_side_deck")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.bar = _TitleBar(self)
        self.setTitleBarWidget(self.bar)
        self.stack = QStackedWidget()
        self.stack.setMinimumWidth(240)
        self._placeholder = QLabel("Eine Kachel im Kachel-Editor wählen.")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self.stack.addWidget(self._placeholder)
        self.setWidget(self.stack)
        self._owners: dict[QObject, QWidget] = {}
        self._folded = bool(_state().get("folded", False))
        window.addDockWidget(Qt.RightDockWidgetArea, self)
        self.hide()
        self._refresh_fold()
        self.topLevelChanged.connect(lambda _f: self._save())
        self.dockLocationChanged.connect(lambda _a: self._save())
        self._restored = False

    # --- Zustand ---------------------------------------------------------------------------------------------------
    def _save(self) -> None:
        geo = bytes(self.saveGeometry().toHex()).decode("ascii") if self.isFloating() else ""
        last_paths.set_value(STATE_KEY, {"folded": self._folded, "floating": self.isFloating(), "geometry": geo})

    def _restore_once(self) -> None:
        if self._restored:
            return
        self._restored = True
        st = _state()
        if st.get("floating"):
            self.setFloating(True)
            if st.get("geometry"):
                self.restoreGeometry(QByteArray.fromHex(str(st["geometry"]).encode("ascii")))
        else:
            QTimer.singleShot(0, lambda: self.win.resizeDocks([self], [WIDTH], Qt.Horizontal))

    # --- Einklappen ------------------------------------------------------------------------------------------------
    def toggle_fold(self) -> None:
        self._folded = not self._folded
        self._refresh_fold()
        self._save()

    @property
    def folded(self) -> bool:
        return self._folded

    def _refresh_fold(self) -> None:
        self.stack.setVisible(not self._folded)
        self.bar.b_fold.setText("▼" if self._folded else "▲")

    # --- Kachel-Editoren -------------------------------------------------------------------------------------------
    def attach(self, owner: QWidget, side: QWidget) -> None:
        self.stack.addWidget(side)
        self._owners[owner] = side
        owner.installEventFilter(self)
        owner.destroyed.connect(lambda _o=None, s=side, o=id(owner): self._detach_id(o, s))
        if owner.isVisible():
            self._show_for(owner)

    def side_for(self, owner: QWidget) -> QWidget | None:
        return self._owners.get(owner)

    def _detach(self, owner: QObject, side: QWidget) -> None:
        self._owners.pop(owner, None)
        try:
            if hasattr(side, "setSource"):
                side.setSource(QUrl())
            self.stack.removeWidget(side)
            side.deleteLater()
        except RuntimeError:
            pass
        self._sync_visible()

    def _detach_id(self, owner_id: int, side: QWidget) -> None:
        owner = next((o for o in list(self._owners) if id(o) == owner_id), None)
        self._detach(owner if owner is not None else QObject(), side)

    def _show_for(self, owner: QWidget) -> None:
        side = self._owners.get(owner)
        if side is None:
            return
        self.stack.setCurrentWidget(side)
        if self.isHidden():
            self.show()
            self._restore_once()
        self._refresh_fold()

    def _sync_visible(self) -> None:
        try:
            vis = [o for o in self._owners if isinstance(o, QWidget) and o.isVisible()]
            if vis:
                self._show_for(vis[-1])
            else:
                self.hide()
        except RuntimeError:                              # Fenster samt Seitenleiste wird gerade geschlossen
            pass

    def eventFilter(self, obj, ev) -> bool:  # noqa: N802
        if obj in self._owners:
            if ev.type() == QEvent.Show:
                self._show_for(obj)
            elif ev.type() == QEvent.Hide:
                QTimer.singleShot(0, self._sync_visible)
        return False
