"""Ribbon icons of the tile editor (Home / Transform / Add column): outline icons in the style of the main ribbon of the tool
(accent colour, round line ends, light tint, grey disabled state). Drawn with QPainter on a 64 x 64 canvas - no image files, no
external icon set, sharp at every size. The package stays standalone (it does not import the host's icon module).

`ribbon_icon(kind)` -> QIcon (normal + disabled). `KINDS` lists every kind the ribbon uses; an unknown kind gets a plain tile."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

SIZE = 30                                   # logical px of the icon (same as the main ribbon)
ACCENT, DISABLED = "#0F5EA8", "#A9B4C6"


def _pts(v):
    return QPolygonF([QPointF(v[i], v[i + 1]) for i in range(0, len(v) - 1, 2)])


def _line(p, *v):
    p.drawPolyline(_pts(v))


def _poly(p, *v):
    p.drawPolygon(_pts(v))


def _rr(p, x, y, w, h, r=5):
    p.drawRoundedRect(QRectF(x, y, w, h), r, r)


def _arrow_head(p, tip_x, tip_y, dx, dy, size=9):
    """Open arrow head at (tip) pointing along (dx, dy) (unit vector)."""
    nx, ny = -dy, dx
    _line(p, tip_x - dx * size + nx * size * 0.7, tip_y - dy * size + ny * size * 0.7, tip_x, tip_y,
          tip_x - dx * size - nx * size * 0.7, tip_y - dy * size - ny * size * 0.7)


def _text(p, s: str, px: int, rect=QRectF(0, 0, 64, 64)):
    """Glyph text in the current pen colour."""
    f = QFont("Segoe UI")
    f.setBold(True)
    f.setPixelSize(px)
    p.save()
    p.setFont(f)
    p.drawText(rect, int(Qt.AlignCenter), s)
    p.restore()


def _tiles(p, x, y, n=2, size=14, gap=6):
    for i in range(n):
        for j in range(n):
            _rr(p, x + i * (size + gap), y + j * (size + gap), size, size, 3)


# --- Home ------------------------------------------------------------------------------------------------------------------
def _undo(p):
    path = QPainterPath(QPointF(16, 26))
    path.cubicTo(24, 14, 52, 14, 52, 38)
    path.cubicTo(52, 50, 44, 54, 34, 54)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    _line(p, 26, 12, 14, 26, 30, 32)


def _redo(p):
    path = QPainterPath(QPointF(48, 26))
    path.cubicTo(40, 14, 12, 14, 12, 38)
    path.cubicTo(12, 50, 20, 54, 30, 54)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    _line(p, 38, 12, 50, 26, 34, 32)


def _hide(p):                                         # eye
    path = QPainterPath(QPointF(6, 32))
    path.quadTo(32, 6, 58, 32)
    path.quadTo(32, 58, 6, 32)
    p.drawPath(path)
    p.drawEllipse(QPointF(32, 32), 9, 9)


def _export(p):                                       # sheet with a column leaving to the right
    _rr(p, 8, 10, 30, 44, 4)
    _line(p, 8, 24, 38, 24)
    _line(p, 24, 10, 24, 54)
    _line(p, 36, 38, 58, 38)
    _arrow_head(p, 58, 38, 1, 0)


def _group(p):                                        # four tiles inside one frame
    _rr(p, 6, 6, 52, 52, 6)
    _tiles(p, 15, 15, 2, 12, 6)


def _select_group(p):                                 # frame + tiles + marker corners
    _tiles(p, 12, 12, 2, 14, 6)
    p.save()
    p.setPen(QPen(p.pen().color(), p.pen().widthF(), Qt.DashLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawRect(QRectF(6, 6, 52, 52))
    p.restore()


def _ungroup(p):                                      # tiles apart, frame broken
    _tiles(p, 8, 8, 2, 14, 12)
    _line(p, 8, 56, 56, 8)


def _reset(p):                                        # counter-clockwise circular arrow
    path = QPainterPath()
    path.arcMoveTo(QRectF(12, 12, 40, 40), 140)
    path.arcTo(QRectF(12, 12, 40, 40), 140, -280)
    p.setBrush(Qt.NoBrush)
    p.drawPath(path)
    _poly(p, 18, 6, 10, 22, 28, 20)


def _duplicate(p):                                    # two sheets
    _rr(p, 20, 6, 32, 38, 4)
    _rr(p, 10, 20, 32, 38, 4)


def _save_excel(p):                                   # table grid with an arrow down
    _rr(p, 6, 6, 52, 34, 4)
    _line(p, 6, 18, 58, 18)
    _line(p, 6, 29, 58, 29)
    _line(p, 24, 6, 24, 40)
    _line(p, 32, 46, 32, 60)
    _arrow_head(p, 32, 60, 0, 1, 7)


# --- Transform -------------------------------------------------------------------------------------------------------------
def _trim(p):                                         # |<- ->| : remove spaces at the ends
    _line(p, 8, 14, 8, 50)
    _line(p, 56, 14, 56, 50)
    _line(p, 16, 32, 28, 32)
    _arrow_head(p, 28, 32, 1, 0, 7)
    _line(p, 48, 32, 36, 32)
    _arrow_head(p, 36, 32, -1, 0, 7)


def _clean(p):                                        # sparkles
    for cx, cy, r in ((24, 38, 16), (47, 16, 9)):
        _poly(p, cx, cy - r, cx + r * 0.28, cy - r * 0.28, cx + r, cy, cx + r * 0.28, cy + r * 0.28, cx, cy + r,
              cx - r * 0.28, cy + r * 0.28, cx - r, cy, cx - r * 0.28, cy - r * 0.28)


def _upper(p):
    _text(p, "AA", 34)


def _lower(p):
    _text(p, "aa", 34)


def _capitalise(p):
    _text(p, "Aa", 34)


def _replace(p):                                      # a -> b
    _rr(p, 4, 20, 20, 24, 4)
    _rr(p, 40, 20, 20, 24, 4)
    _line(p, 27, 32, 37, 32)
    _arrow_head(p, 37, 32, 1, 0, 6)


def _add_text(p):                                     # box with text lines and a plus
    _rr(p, 6, 14, 38, 36, 4)
    _line(p, 12, 26, 38, 26)
    _line(p, 12, 36, 30, 36)
    _line(p, 52, 8, 52, 24)
    _line(p, 44, 16, 60, 16)


def _pipe_size(p):                                    # pipe end with a dimension line
    p.drawEllipse(QRectF(10, 10, 30, 30))
    p.drawEllipse(QRectF(17, 17, 16, 16))
    _line(p, 10, 52, 40, 52)
    _line(p, 10, 47, 10, 57)
    _line(p, 40, 47, 40, 57)
    _line(p, 50, 18, 50, 44)
    _arrow_head(p, 50, 44, 0, 1, 6)


def _extract(p):                                      # text with a part taken out
    _line(p, 8, 16, 56, 16)
    _line(p, 8, 28, 56, 28)
    p.save()
    p.setBrush(QBrush(p.pen().color()))
    _rr(p, 22, 21, 22, 14, 3)
    p.restore()
    _line(p, 33, 40, 33, 56)
    _arrow_head(p, 33, 56, 0, 1, 7)


def _split(p):                                        # one column becoming two
    _rr(p, 20, 6, 24, 16, 3)
    _line(p, 32, 22, 32, 30)
    _line(p, 32, 30, 16, 40)
    _line(p, 32, 30, 48, 40)
    _rr(p, 6, 42, 20, 16, 3)
    _rr(p, 38, 42, 20, 16, 3)


def _fill(p, down: bool):                             # column of cells with an arrow
    s = 1 if down else -1
    for i in range(4):
        _rr(p, 8, 8 + i * 13, 24, 11, 2)
    y0, y1 = (14, 50) if down else (50, 14)
    _line(p, 46, y0, 46, y1)
    _arrow_head(p, 46, y1, 0, s, 8)


def _fill_down(p):
    _fill(p, True)


def _fill_up(p):
    _fill(p, False)


def _fill_value(p):                                   # empty cell filled with a value
    _rr(p, 6, 10, 34, 20, 3)
    _rr(p, 6, 36, 34, 20, 3)
    _line(p, 14, 46, 32, 46)
    _line(p, 48, 20, 48, 40)
    _arrow_head(p, 48, 40, 0, 1, 7)


# --- Add column ------------------------------------------------------------------------------------------------------------
def _yes_no(p):                                       # switch
    _rr(p, 6, 20, 52, 24, 12)
    p.drawEllipse(QRectF(36, 23, 18, 18))


def _conditional(p):                                  # if / then: diamond with two ways
    _poly(p, 32, 6, 46, 20, 32, 34, 18, 20)
    _line(p, 32, 34, 32, 44)
    _line(p, 32, 44, 14, 52)
    _line(p, 32, 44, 50, 52)
    _arrow_head(p, 14, 52, -1, 0.4, 6)
    _arrow_head(p, 50, 52, 1, 0.4, 6)


def _check(p):                                        # list with a check mark
    _rr(p, 6, 8, 40, 48, 4)
    _line(p, 14, 22, 38, 22)
    _line(p, 14, 34, 38, 34)
    _line(p, 14, 46, 26, 46)
    _line(p, 40, 44, 48, 52, 60, 36)


def _lookup(p):                                       # two tables joined
    _rr(p, 4, 12, 22, 40, 3)
    _rr(p, 38, 12, 22, 40, 3)
    _line(p, 4, 26, 26, 26)
    _line(p, 38, 26, 60, 26)
    _line(p, 26, 38, 38, 38)


def _add_columns(p):                                  # table with a plus
    _rr(p, 4, 12, 36, 40, 3)
    _line(p, 4, 26, 40, 26)
    _line(p, 22, 12, 22, 52)
    _line(p, 52, 22, 52, 42)
    _line(p, 42, 32, 62, 32)


def _index(p):                                        # running numbers
    _text(p, "123", 26, QRectF(0, 6, 64, 36))
    _line(p, 8, 48, 56, 48)
    _line(p, 8, 56, 40, 56)


# --- side areas (buttons right of the icon row) ----------------------------------------------------------------------------------
def _area_not_exported(p):                            # sheet, the way out is barred
    _rr(p, 6, 10, 30, 44, 4)
    _line(p, 6, 24, 36, 24)
    _line(p, 21, 10, 21, 54)
    p.save()
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(46, 40), 12, 12)
    _line(p, 38, 48, 54, 32)
    p.restore()


def _area_hidden(p):                                  # eye, struck through
    _hide(p)
    _line(p, 12, 54, 52, 10)


def _area_renamed(p):                                 # name tag with a pencil
    _rr(p, 6, 18, 36, 30, 5)
    _line(p, 14, 28, 32, 28)
    _line(p, 14, 38, 24, 38)
    _poly(p, 34, 56, 37, 46, 53, 22, 60, 27, 44, 51)


_DRAW = {"area_not_exported": _area_not_exported, "area_hidden": _area_hidden, "area_renamed": _area_renamed,
         "undo": _undo, "redo": _redo, "hide": _hide, "export": _export, "group": _group, "select_group": _select_group,
         "ungroup": _ungroup, "reset": _reset, "duplicate": _duplicate, "save_excel": _save_excel,
         "trim": _trim, "clean": _clean, "upper": _upper, "lower": _lower, "capitalise": _capitalise, "replace": _replace,
         "add_text": _add_text, "pipe_size": _pipe_size, "extract": _extract, "split": _split, "fill_down": _fill_down,
         "fill_up": _fill_up, "fill_value": _fill_value,
         "yes_no": _yes_no, "conditional": _conditional, "check": _check, "lookup": _lookup, "add_columns": _add_columns,
         "index": _index}
KINDS = tuple(_DRAW)


def _tile(p):                                         # unknown kind: a plain tile
    _rr(p, 10, 10, 44, 44, 6)


def _paint(kind: str, color: str) -> QPixmap:
    scale = 2                                          # drawn at double size for sharp edges
    px = SIZE * scale
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
    p.scale(px / 64.0, px / 64.0)
    c = QColor(color)
    tint = QColor(c)
    tint.setAlpha(34)
    p.setPen(QPen(c, 4.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QBrush(tint))
    _DRAW.get(kind, _tile)(p)
    p.end()
    pm.setDevicePixelRatio(scale)
    return pm


def ribbon_icon(kind: str) -> QIcon:
    ic = QIcon()
    ic.addPixmap(_paint(kind, ACCENT), QIcon.Normal)
    ic.addPixmap(_paint(kind, DISABLED), QIcon.Disabled)
    return ic
