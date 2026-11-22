"""Persisted layout of the tile editor's side areas: width of the right-hand column (Not exported / Hidden) and the
inspector side pane ("Select a tile" / Steps), and whether either is collapsed.

Shared across every tile editor instance via QSettings, under the module's own organisation/application name - independent
of the host application, so `column_editor` stays usable standalone (see `tile_editor_host.py`, `README_MODULE.md`).
Qt only (QSettings, Property); no dependency on the rest of this package.
"""
from __future__ import annotations

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

ORG, APP = "P3D", "ColumnEditorTileLayout"
MAX_OPEN_AREAS = 2                  # side areas open at the same time

DEFAULT_RIGHT_SHARE = 0.38          # of the tile grid width given to the right-hand column (Not exported / Hidden)
MIN_RIGHT_SHARE, MAX_RIGHT_SHARE = 0.16, 0.6
DEFAULT_SIDE_WIDTH = 300            # px, inspector / steps side pane
MIN_SIDE_WIDTH, MAX_SIDE_WIDTH = 160, 520


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class TileLayoutState(QObject):
    """Exposed to QML as `tileLayout`. Every setter persists at once, so the layout survives a restart."""

    changed = Signal()
    areasChanged = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._open_areas: list[int] = []
        s = QSettings(ORG, APP)
        self._right_share = _clamp(float(s.value("rightShare", DEFAULT_RIGHT_SHARE)), MIN_RIGHT_SHARE, MAX_RIGHT_SHARE)
        self._right_collapsed = _truthy(s.value("rightCollapsed", False))
        self._side_width = int(_clamp(int(s.value("sideWidth", DEFAULT_SIDE_WIDTH)), MIN_SIDE_WIDTH, MAX_SIDE_WIDTH))
        self._side_collapsed = _truthy(s.value("sideCollapsed", False))
        self._side_external = False                      # True: the side pane lives outside (host flow deck); not persisted

    @staticmethod
    def _save(key: str, value) -> None:
        QSettings(ORG, APP).setValue(key, value)

    def _get_right_share(self) -> float:
        return self._right_share

    def _set_right_share(self, value: float) -> None:
        value = _clamp(float(value), MIN_RIGHT_SHARE, MAX_RIGHT_SHARE)
        if value != self._right_share:
            self._right_share = value
            self._save("rightShare", value)
            self.changed.emit()

    rightShare = Property(float, _get_right_share, _set_right_share, notify=changed)

    def _get_right_collapsed(self) -> bool:
        return self._right_collapsed

    def _set_right_collapsed(self, value: bool) -> None:
        value = bool(value)
        if value != self._right_collapsed:
            self._right_collapsed = value
            self._save("rightCollapsed", value)
            self.changed.emit()

    rightCollapsed = Property(bool, _get_right_collapsed, _set_right_collapsed, notify=changed)

    def _get_side_width(self) -> int:
        return self._side_width

    def _set_side_width(self, value: int) -> None:
        value = int(_clamp(int(value), MIN_SIDE_WIDTH, MAX_SIDE_WIDTH))
        if value != self._side_width:
            self._side_width = value
            self._save("sideWidth", value)
            self.changed.emit()

    sideWidth = Property(int, _get_side_width, _set_side_width, notify=changed)

    def _get_side_collapsed(self) -> bool:
        return self._side_collapsed

    def _set_side_collapsed(self, value: bool) -> None:
        value = bool(value)
        if value != self._side_collapsed:
            self._side_collapsed = value
            self._save("sideCollapsed", value)
            self.changed.emit()

    sideCollapsed = Property(bool, _get_side_collapsed, _set_side_collapsed, notify=changed)

    def _get_side_external(self) -> bool:
        return self._side_external

    def _set_side_external(self, value: bool) -> None:
        value = bool(value)
        if value != self._side_external:
            self._side_external = value
            self.changed.emit()

    sideExternal = Property(bool, _get_side_external, _set_side_external, notify=changed)

    # --- open side areas (1 = Not exported, 2 = Hidden, 3 = Renamed): shared by the tile grid and the status strip in the ribbon ----------
    def _get_open_areas(self) -> list:
        return list(self._open_areas)

    openAreas = Property(list, _get_open_areas, notify=areasChanged)

    @Slot(int)
    def toggleArea(self, i: int) -> None:
        """Open / fold one area; a third one folds the area opened first (at most MAX_OPEN_AREAS at a time). Not persisted: all folded at start."""
        areas = list(self._open_areas)
        if i in areas:
            areas.remove(i)
        else:
            areas.append(i)
            while len(areas) > MAX_OPEN_AREAS:
                areas.pop(0)
        self._open_areas = areas
        self.areasChanged.emit()


__all__ = ["TileLayoutState"]
