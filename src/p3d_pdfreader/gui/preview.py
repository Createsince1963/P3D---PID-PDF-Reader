"""PDF-Seitenvorschau (PyMuPDF): Grundbild der ganzen Seite plus scharfer Ausschnitt in Bildschirmaufloesung.

Das Grundbild (laengste Seite ``BASE_PIXELS``) dient der Uebersicht. Nach jedem Zoomen oder Verschieben wird der sichtbare
Ausschnitt aus dem Vektor-PDF neu gerendert, passend zur aktuellen Vergroesserung. So bleibt der Plan bei jeder Zoomstufe
scharf, ohne die ganze A0-Seite hochaufgeloest im Speicher zu halten. ``mark()`` umrahmt die Fundstellen eines Tags
(nummeriert) und zeigt die ganze Seite oder zoomt auf eine Fundstelle; ein Hinweis oben links nennt die Position."""
from __future__ import annotations

from pathlib import Path

import pymupdf
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QLabel)

from ..core.render import page_pixmap
from main_gui_kit.theme import LIGHT

from .appearance import DEFAULT_DIRTY, accent
from .design import BAND, BORDER, TEXT

BASE_PIXELS = 4000          # laengste Kante des Uebersichtsbilds
MAX_DETAIL_PIXELS = 12e6    # Obergrenze fuer den scharfen Ausschnitt
MARK_CONTEXT = 0.02        # Umfeld beim Zoom auf einen Tag (Anteil der Seitenbreite)


def _qimage(pix) -> QImage:
    fmt = QImage.Format_Grayscale8 if pix.n == 1 else QImage.Format_RGB888
    return QImage(pix.samples, pix.width, pix.height, pix.stride, fmt).copy()


class PdfPreview(QGraphicsView):
    page_changed = Signal(int, int)        # (Seite 0-basiert, Seitenzahl)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._page = -1
        self._dup_groups: list = []
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QColor("white"))
        self._path: Path | None = None
        self._doc = None
        self._scale = 1.0               # Szene-Pixel je PDF-Punkt
        self._rotation = 0              # zusaetzliche Ansichtsdrehung in Grad (Buttons "Drehen")
        self._mono = False              # Seite monochrom anzeigen (Button "Monochrom")
        self._base = None
        self._marks: list = []
        self._dup_items: list = []
        self._status_groups: tuple = ([], [])    # (korrekt, fehlerhaft) je Tag [(Seite, Rechteck)]
        self._status_items: list = []
        self._detail = None
        self._info = QLabel(self.viewport())             # Hinweis oben links: "Fundstelle 2 / 4 ..."
        self._info.setObjectName("PreviewInfo")
        self._info.setStyleSheet(f"#PreviewInfo {{ background: {BAND}; color: {TEXT}; border: 1px solid {BORDER}; "
                                 "padding: 3px 8px; }")
        self._info.move(8, 8)
        self._info.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._render_detail)

    # --- Laden / Seiten -------------------------------------------------------------------------------------------
    def show_pdf(self, path: Path | None) -> None:
        if path == self._path:
            return
        if self._doc is not None:
            self._doc.close()
            self._doc = None
        self._path, self._dup_groups, self._status_groups = path, [], ([], [])
        self._page = -1
        self._clear_scene()
        if not path:
            self.page_changed.emit(0, 0)
            return
        try:
            self._doc = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001
            self.scene().addText(f"Vorschau nicht möglich: {exc}")
            return
        self.set_page(0)

    @property
    def page(self) -> int:
        return max(0, self._page)

    def page_count(self) -> int:
        return self._doc.page_count if self._doc is not None else 0

    def _clear_scene(self) -> None:
        self._detail, self._base, self._marks, self._dup_items, self._status_items = None, None, [], [], []
        self.set_info("")
        self.scene().clear()

    def set_page(self, number: int, fit: bool = True) -> None:
        """Seite ``number`` (0-basiert) anzeigen; doppelte Tags dieser Seite gelb hinterlegen."""
        if self._doc is None or not 0 <= number < self._doc.page_count:
            return
        if number == self._page:
            return
        self._page = number
        self._clear_scene()
        try:
            page = self._doc[number]
            self._scale = BASE_PIXELS / max(page.rect.width, page.rect.height)
            pix = page_pixmap(page, pymupdf.Matrix(self._scale, self._scale), mono=self._mono)
        except Exception as exc:  # noqa: BLE001
            self.scene().addText(f"Seite {number + 1} nicht darstellbar: {exc}")
            return
        self._base = self.scene().addPixmap(QPixmap.fromImage(_qimage(pix)))
        self._base.setZValue(0)
        self.scene().setSceneRect(QRectF(0, 0, pix.width, pix.height))
        self._draw_duplicates()
        self._draw_status()
        if fit:
            self.fit()
        self.page_changed.emit(number, self._doc.page_count)

    @property
    def monochrome(self) -> bool:
        return self._mono

    def set_monochrome(self, on: bool) -> None:
        """Seite monochrom (schwarz auf weiss) oder farbig zeigen; Zoom, Drehung und Markierungen bleiben."""
        on = bool(on)
        if on == self._mono:
            return
        self._mono = on
        if self._doc is None or self._page < 0 or self._base is None:
            return
        try:
            pix = page_pixmap(self._doc[self._page], pymupdf.Matrix(self._scale, self._scale), mono=on)
        except Exception:  # noqa: BLE001 - dann bleibt das bisherige Bild
            return
        self._base.setPixmap(QPixmap.fromImage(_qimage(pix)))
        self._render_detail()

    def step_page(self, delta: int) -> None:
        self.set_page(self.page + delta)

    def fit(self) -> None:
        self._reset_view()
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)
        self._schedule()

    def _reset_view(self) -> None:
        """Zoom zuruecksetzen, Ansichtsdrehung (Buttons "Drehen") behalten."""
        self.resetTransform()
        if self._rotation:
            self.rotate(self._rotation)

    def rotate_view(self, degrees: int) -> None:
        """Ansicht drehen (zusaetzlich zur Seitendrehung der PDF, die schon beim Rendern beruecksichtigt ist)."""
        self._rotation = (self._rotation + degrees) % 360
        center = self.mapToScene(self.viewport().rect().center())
        self.rotate(degrees)
        self.centerOn(center)
        self._schedule()

    def zoom(self, factor: float) -> None:
        self.scale(factor, factor)
        self._schedule()

    def current_zoom(self) -> float:
        t = self.transform()
        return (t.m11() ** 2 + t.m12() ** 2) ** 0.5               # auch bei gedrehter Ansicht

    # --- Scharfer Ausschnitt -------------------------------------------------------------------------------------
    def _schedule(self) -> None:
        if self._doc is not None:
            self._timer.start()

    def _render_detail(self) -> None:
        if self._doc is None:
            return
        if self._detail is not None:
            self.scene().removeItem(self._detail)
            self._detail = None
        zoom = self.current_zoom() * self.devicePixelRatioF()      # Bildschirm-Pixel je Szene-Pixel
        if zoom <= 1.05:
            return                                                   # Grundbild ist scharf genug
        visible = self.mapToScene(self.viewport().rect()).boundingRect().intersected(self.sceneRect())
        if visible.isEmpty():
            return
        factor = self._scale * zoom                                  # Pixel je PDF-Punkt
        if visible.width() * visible.height() * zoom * zoom > MAX_DETAIL_PIXELS:
            factor *= (MAX_DETAIL_PIXELS / (visible.width() * visible.height() * zoom * zoom)) ** 0.5
        s = self._scale
        clip = pymupdf.Rect(visible.left() / s, visible.top() / s, visible.right() / s, visible.bottom() / s)
        try:
            pix = page_pixmap(self._doc[self.page], pymupdf.Matrix(factor, factor), clip=clip, mono=self._mono)
        except Exception:  # noqa: BLE001 - dann bleibt das Grundbild
            return
        item = self.scene().addPixmap(QPixmap.fromImage(_qimage(pix)))
        item.setTransformationMode(Qt.SmoothTransformation)
        item.setScale(s / factor)
        item.setPos(clip.x0 * s, clip.y0 * s)
        item.setZValue(1)
        self._detail = item

    # --- Markierung ----------------------------------------------------------------------------------------------
    def _scene_rect(self, rect: tuple) -> QRectF:
        s = self._scale
        return QRectF(rect[0] * s, rect[1] * s, (rect[2] - rect[0]) * s, (rect[3] - rect[1]) * s).adjusted(-4, -4, 4, 4)

    def show_duplicates(self, hit_groups: list[list[tuple]]) -> None:
        """Fundstellen doppelter Tags gelb hinterlegen. ``hit_groups`` = je Tag [(Seite, Rechteck)]; gezeichnet wird
        jeweils nur, was auf der angezeigten Seite liegt (beim Seitenwechsel neu)."""
        self._dup_groups = [list(g) for g in hit_groups]
        self._draw_duplicates()

    def _draw_duplicates(self) -> None:
        for item in self._dup_items:
            if item.scene() is self.scene():
                self.scene().removeItem(item)
        self._dup_items = []
        if self._doc is None:
            return
        fill = QColor(DEFAULT_DIRTY)
        fill.setAlpha(170)
        pen = QPen(fill.darker(160), 1)
        pen.setCosmetic(True)
        for hits in getattr(self, "_dup_groups", []):
            on_page = [r for p, r in hits if p == self._page]
            if len(on_page) < 2:                        # doppelt nur, wenn mehrfach auf derselben Seite
                continue
            for rect in on_page:
                item = self.scene().addRect(self._scene_rect(rect), pen, fill)
                item.setZValue(1.5)
                item.setToolTip("doppelter Tag")
                self._dup_items.append(item)

    def show_status(self, ok_groups: list[list[tuple]], faulty_groups: list[list[tuple]]) -> None:
        """Alle Fundstellen umranden: korrekt gruen, fehlerhaft (Review "Korrektur erforderlich") rot (je Tag [(Seite, Rechteck)]).
        Gezeichnet wird, was auf der angezeigten Seite liegt; die Auswahl-Markierung liegt darueber."""
        self._status_groups = ([list(g) for g in ok_groups], [list(g) for g in faulty_groups])
        self._draw_status()

    def _draw_status(self) -> None:
        for item in self._status_items:
            if item.scene() is self.scene():
                self.scene().removeItem(item)
        self._status_items = []
        if self._doc is None:
            return
        for groups, color, tip in ((self._status_groups[0], LIGHT.ok, "gefundener Tag"),
                                   (self._status_groups[1], LIGHT.err,
                                    "fehlerhaft: Review „Korrektur erforderlich“ oder Projekt-Befund")):
            pen = QPen(QColor(color), 2)
            pen.setCosmetic(True)
            for hits in groups:
                for p, rect in hits:
                    if p != self._page:
                        continue
                    item = self.scene().addRect(self._scene_rect(rect), pen)
                    item.setZValue(1.7)
                    item.setToolTip(tip)
                    self._status_items.append(item)

    def clear_marks(self) -> None:
        for item in self._marks:
            if item.scene() is self.scene():
                self.scene().removeItem(item)
        self._marks = []
        self.set_info("")

    def mark(self, hits: list[tuple], focus: int | None = 0, label: str = "", overview_page: int | None = None) -> None:
        """Fundstellen eines Tags umrahmen. ``hits`` = [(Seite, Rechteck)] in Navigationsreihenfolge.

        ``focus`` = Index der Fundstelle, auf die gezoomt wird (wechselt bei Bedarf die Seite); ``None`` = Uebersicht der
        ganzen Seite ``overview_page``. Jede Fundstelle der angezeigten Seite bekommt ihre Nummer (bleibt in jeder
        Zoomstufe lesbar), die fokussierte ist hervorgehoben. Der Hinweis oben links nennt Fundstelle und Seite."""
        self.clear_marks()
        if not hits or self._doc is None:
            return
        page = hits[focus][0] if focus is not None else (hits[0][0] if overview_page is None else overview_page)
        self.set_page(page, fit=False)
        self.clear_marks()
        color = QColor(accent())
        many = len(hits) > 1
        multi_page = len({p for p, _r in hits}) > 1
        for number, (p, rect) in enumerate(hits, start=1):
            if p != page:
                continue
            focused = focus is not None and number - 1 == focus
            pen = QPen(color, 4 if focused or not many else 2)
            pen.setCosmetic(True)
            if many and not focused:
                pen.setStyle(Qt.DashLine)
            box = self.scene().addRect(self._scene_rect(rect), pen)
            box.setZValue(2)
            self._marks.append(box)
            if many:
                self._marks.append(self._badge(number, self._scene_rect(rect), focused))
        where = f" (Seite {page + 1} von {self.page_count()})" if self.page_count() > 1 else ""
        more = " – erneut klicken oder F3 für die nächste" if many else ""
        if focus is None:
            self.fit()
            on_page = sum(1 for p, _r in hits if p == page)
            text = f"{label}: {on_page} Fundstelle(n) auf dieser Seite" + \
                (f", {len(hits)} insgesamt" if multi_page else "") + where + more if many else label + where
        else:
            area = self._scene_rect(hits[focus][1])
            pad = self.sceneRect().width() * MARK_CONTEXT
            self.fitInView(area.adjusted(-pad, -pad * 0.7, pad, pad * 0.7), Qt.KeepAspectRatio)
            self.centerOn(area.center())
            self._schedule()
            text = (f"{label}: Fundstelle {focus + 1} / {len(hits)}" if many else label) + where + more
        self.set_info(text)

    def _badge(self, number: int, rect: QRectF, focused: bool):
        """Nummer neben der Fundstelle; ignoriert den Zoom (immer gleich gross)."""
        text = QGraphicsSimpleTextItem(str(number))
        font = text.font()
        font.setBold(True)
        font.setPointSizeF(10 if focused else 9)
        text.setFont(font)
        text.setBrush(QColor("white"))
        bounds = text.boundingRect().adjusted(-4, -1, 4, 1)
        badge = QGraphicsRectItem(bounds)
        badge.setBrush(QColor(accent()) if focused else QColor(accent()).lighter(140))
        badge.setPen(QPen(Qt.NoPen))
        text.setParentItem(badge)
        badge.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        badge.setPos(rect.right(), rect.top())
        badge.setZValue(3)
        self.scene().addItem(badge)
        return badge

    def set_info(self, text: str) -> None:
        self._info.setText(text)
        self._info.setVisible(bool(text))
        self._info.adjustSize()

    # --- Interaktion ---------------------------------------------------------------------------------------------
    def wheelEvent(self, event) -> None:
        self.zoom(1.25 if event.angleDelta().y() > 0 else 0.8)

    def mouseDoubleClickEvent(self, event) -> None:
        self.fit()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self._schedule()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._schedule()
