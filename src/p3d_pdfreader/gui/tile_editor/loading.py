"""Ladebildschirm ueber dem ganzen Fenster (uebernommen aus P3D Tag Compliance ``linetag_loading.py`` / ``linetag_busy.py``).

Der Kachel-Editor (QML) und die Tabelle werden im GUI-Thread aufgebaut; ohne Ladebildschirm bliebe das Fenster weiss. Die
Abdeckung zeigt mittig: Titel, ein sich drehendes Zahnrad (nur Umriss), den aktuellen Schritt und eine feine Linie mit
Prozentwert. ``step(anteil, text)`` malt neu und laesst Qt Zeichen-/Timer-Ereignisse verarbeiten (nie Benutzereingaben).

    ov = LoadingOverlay(widget)
    ov.begin("Kachel-Editor wird geladen …")
    ov.step(0.4, "Kachel-Editor wird erstellt …")
    ov.end()

Farben nur aus ``design``/``appearance`` (Akzent = Zahnrad und Linie)."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QEvent, QEventLoop, QObject, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QWidget

from .. import appearance
from ..design import TEXT, TEXT_MUTED

GEAR = 84                       # px, Zahnrad in der Mitte
BAR_W = 450                     # px, feine Linie unter dem Text
BAR_PEN = 1.5
STROKE = 1.7                    # Umriss Zahnrad / Pfeile (Einheiten der 64 x 64-Zeichnung)
GLIDE = 6.0                     # 1/s: so schnell folgt die angezeigte Linie dem gemeldeten Wert
TURN_SECONDS = 1.6              # eine Umdrehung der Pfeile


def gear_polygon(cx: float, cy: float, r_out: float, r_in: float, teeth: int = 8) -> QPolygonF:
    pts: list[QPointF] = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step - math.pi / 2
        for frac, r in ((-0.30, r_in), (-0.17, r_out), (0.17, r_out), (0.30, r_in)):
            ang = a + frac * step * 1.6
            pts.append(QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return QPolygonF(pts)


def paint_gear_outline(p: QPainter, size: float, angle: float, color: QColor) -> None:
    """Zahnrad (nur Umriss) mit zwei duennen Pfeilen, die sich darum drehen; ``angle`` in Grad."""
    s = size / 64.0
    p.save()
    p.scale(s, s)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setPen(QPen(color, STROKE, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    gear = QPainterPath()
    gear.addPolygon(gear_polygon(32, 32, 15.5, 11.5))
    gear.closeSubpath()
    p.drawPath(gear)
    p.drawEllipse(QPointF(32, 32), 5.2, 5.2)
    p.translate(32, 32)
    p.rotate(angle)
    r = 26.0
    box = QRectF(-r, -r, 2 * r, 2 * r)
    for k in range(2):
        p.save()
        p.rotate(180 * k)
        arc = QPainterPath()
        arc.arcMoveTo(box, 160)
        arc.arcTo(box, 160, -120)
        p.drawPath(arc)
        end = arc.currentPosition()
        ang = math.radians(160 - 120)
        tx, ty = math.sin(ang), math.cos(ang)
        nx, ny = -ty, tx
        for sign in (1.0, -1.0):
            p.drawLine(end, QPointF(end.x() - tx * 5.0 + sign * nx * 4.0, end.y() - ty * 5.0 + sign * ny * 4.0))
        p.restore()
    p.restore()


class LoadingOverlay(QWidget):
    def __init__(self, host: QWidget):
        super().__init__(host.window())
        self._win = host.window()
        self._title = ""
        self._text = ""
        self._frac = 0.0
        self._shown = 0.0
        self._t0 = time.monotonic()
        self._t_paint = self._t0
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.update)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.hide()

    # --- Schnittstelle -------------------------------------------------------------------------------------------
    def begin(self, title: str, text: str = "") -> None:
        self._title, self._text, self._frac, self._shown = title, text, 0.0, 0.0
        self._t0 = self._t_paint = time.monotonic()
        self._win.installEventFilter(self)
        self.setGeometry(self._win.rect())
        self.show()
        self.raise_()
        self._timer.start()
        self._pump()

    def step(self, frac: float, text: str = "") -> None:
        self._frac = max(0.0, min(1.0, float(frac)))
        if text:
            self._text = text
        self._pump()

    def end(self) -> None:
        self._timer.stop()
        try:
            self._win.removeEventFilter(self)
        except RuntimeError:
            pass
        self.hide()

    @property
    def fraction(self) -> float:
        return self._frac

    @property
    def text(self) -> str:
        return self._text

    @property
    def title(self) -> str:
        return self._title

    # --- intern --------------------------------------------------------------------------------------------------
    def eventFilter(self, obj: QObject, e: QEvent) -> bool:  # noqa: N802
        if obj is self._win and e.type() == QEvent.Resize and self.isVisible():
            self.setGeometry(self._win.rect())
        return False

    def _pump(self) -> None:
        if self.isVisible():
            self.raise_()
            self.repaint()
            QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        e.accept()                                       # waehrend des Ladens nicht klickbar

    def _glide(self) -> float:
        now = time.monotonic()
        dt, self._t_paint = now - self._t_paint, now
        gap = self._frac - self._shown
        if gap <= 0.002:
            self._shown = self._frac
        else:
            self._shown += gap * min(1.0, dt * GLIDE)
        return self._shown

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), QColor(255, 255, 255, 245))
        w, h = float(self.width()), float(self.height())
        cx, cy = w / 2.0, h / 2.0
        col = QColor(appearance.accent())
        base = QFont(self.font())
        base.setBold(False)
        shown = self._glide()
        f = QFont(base)
        f.setPointSizeF(17.0)
        f.setWeight(QFont.Light)
        p.setFont(f)
        p.setPen(QColor(TEXT))
        p.drawText(QRectF(0.0, cy - 150.0, w, 36.0), int(Qt.AlignHCenter | Qt.AlignVCenter), self._title)
        p.save()
        p.translate(cx - GEAR / 2.0, cy - 100.0)
        paint_gear_outline(p, GEAR, ((time.monotonic() - self._t0) / TURN_SECONDS * 360.0) % 360.0, col)
        p.restore()
        f = QFont(base)
        f.setPointSizeF(11.0)
        p.setFont(f)
        p.setPen(QColor(TEXT_MUTED))
        p.drawText(QRectF(0.0, cy + 6.0, w, 26.0), int(Qt.AlignHCenter | Qt.AlignVCenter), self._text)
        x0, y = cx - BAR_W / 2.0, cy + 46.0
        track = QColor(col)
        track.setAlpha(40)
        p.setPen(QPen(track, BAR_PEN, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x0, y), QPointF(x0 + BAR_W, y))
        if shown > 0:
            p.setPen(QPen(col, BAR_PEN, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x0, y), QPointF(x0 + BAR_W * shown, y))
        f = QFont(base)
        f.setPointSizeF(9.0)
        p.setFont(f)
        p.setPen(QColor(TEXT_MUTED))
        p.drawText(QRectF(x0 + BAR_W + 10.0, y - 10.0, 60.0, 20.0), int(Qt.AlignLeft | Qt.AlignVCenter),
                   f"{int(round(shown * 100))} %")
        p.end()
