"""Multi-Tag-PDF (1.0.55): Kopie des Plots mit rotem Eintrag oberhalb jedes doppelten Tags. Ohne Qt.

Markiert werden Tags, die in der Importliste (Datenbank) auch mit „?“ stehen, und Tags, die mehrfach in der PDF
vorkommen. Der Eintrag nennt je Datenbankzeile das komplette Tag (Datenlink-2-Spalte) und die PID-Nummer
(Datenlink-1-Spalte). Eintraege lassen sich im Viewer verschieben (``placed``); ein verschobener Eintrag bekommt eine
rote Linie zum Tag. Das Original bleibt unveraendert."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import pymupdf
from main_gui_kit.theme import LIGHT

from . import mono, review_table, type_filter
from .data_link import MULTI_NOTE, DataLink
from .extract import PdfResult, Tag
from .redline import AUTHOR, BORDER, PAD, _rgb, review_layer_enabled
from .review import positions
from .review_store import ReviewStore, marked_tags

FONT_SIZE = 6.0
LINE = FONT_SIZE * 1.25
MAX_LINES = 6           # sichtbare Datenbankzeilen je Eintrag; alle stehen im PDF-Kommentar
NO_TAGS = ("Zeichnungsverweis",)    # Verweise auf andere Zeichnungen sind keine Tags


@dataclass
class MultiTag:
    tag: Tag
    entries: list[tuple[str, str]]      # (komplettes Tag, PID-Nummer) je Datenbankzeile
    marked: bool                        # in der Datenbank auch mit „?“ eingetragen

    def database_lines(self) -> list[str]:
        return [f"{tag}   {drawing}".rstrip() for tag, drawing in self.entries]

    def lines(self, limit: int | None = MAX_LINES) -> list[str]:
        out = self.database_lines()
        if limit is not None and len(out) > limit:
            out = out[:limit] + [f"... (+{len(out) - limit} weitere, siehe Kommentar)"]
        if self.tag.duplicate:
            out.append(f"{self.tag.tag}: {self.tag.count}× in dieser PDF")
        return out


@dataclass
class Note:
    """Ein roter Eintrag. Rechtecke in PDF-Punkten der sichtbaren (gedrehten) Seite."""
    key: str                            # Typ|Tag|Seite|Fundstelle - Schluessel fuer eigene Positionen
    page: int
    tag: str
    box: tuple                          # Rahmen um das Tag
    rect: tuple                         # Textfeld
    lines: list[str]
    content: str                        # PDF-Kommentar (alle Zeilen)
    moved: bool                         # vom Nutzer verschoben
    line: bool = False                  # steht nicht direkt am Tag -> Linie zum Tag


def find_multi_tags(link: DataLink, tags: list[Tag], file_value=None,
                    value_of: Callable[[Tag], str] = lambda t: t.tag) -> list[MultiTag]:
    """Doppelte Tags einer PDF. ``link`` muss mit ``two_tag=True`` gebaut sein, ``value_of`` = Wert fuer Datenlink 2."""
    out = []
    for tag in tags:
        if tag.type in NO_TAGS:
            continue
        entries, marked = link.entries(value_of(tag), file_value)
        if marked or tag.duplicate:
            out.append(MultiTag(tag, entries, marked))
    return out


def _visible(result: PdfResult, store) -> tuple[list[Tag], object]:
    if store is None:
        try:
            store = ReviewStore(result.path)
        except OSError:
            store = None
    tags = type_filter.apply(result.tags)
    if callable(getattr(store, "visible", None)):
        tags = store.visible(tags)                   # aus dem Review genommene Tags nicht
    return tags, store


def _free_spot(box, width: float, height: float, page, taken: list) -> tuple[float, float, bool]:
    """Erste Lage ohne Ueberdeckung anderer Eintraege und Tag-Rahmen: ueber dem Tag, dann weiter oben, darunter,
    rechts und links. Rueckgabe (x, y, direkt am Tag)."""
    above, below, gap = box.y0 - height - 1, box.y1 + 1, height + 1
    spots = [(box.x0, above)]
    for i in range(0, 8):
        spots += [(box.x0, above - i * gap), (box.x0, below + i * gap),
                  (box.x1 + 2, above - i * gap), (box.x0 - width - 2, above - i * gap),
                  (box.x1 + 2, below + i * gap), (box.x0 - width - 2, below + i * gap)]
    for n, (x, y) in enumerate(spots):
        x = max(0.0, min(x, page.rect.width - width))
        if y < 0 or y + height > page.rect.height:
            continue
        rect = pymupdf.Rect(x, y, x + width, y + height)
        if not any(rect.intersects(other) for other in taken):
            return x, y, n <= 2
    x = max(0.0, min(box.x0, page.rect.width - width))      # alles belegt: am Tag, der Nutzer verschiebt
    return x, above if above >= 0 else below, True


def layout_notes(doc, found: list[MultiTag], placed: dict | None = None) -> list[Note]:
    """Eintraege fuer alle Fundstellen: nahe am Tag ohne gegenseitige Ueberdeckung bzw. an der Position aus ``placed``
    {key: [x, y]}. Die automatischen Lagen haengen nicht von ``placed`` ab (Verschieben laesst die anderen stehen)."""
    placed = placed or {}
    by_key = {(m.tag.type, m.tag.tag): m for m in found}
    hits = positions([m.tag for m in found])
    taken: dict[int, list] = {}
    for p in hits:
        taken.setdefault(p.page, []).append(pymupdf.Rect(p.rect) + (-PAD, -PAD, PAD, PAD))
    out = []
    for p in sorted(hits, key=lambda h: (h.page, round(h.rect[1]), h.rect[0])):
        multi = by_key[(p.tag.type, p.tag.tag)]
        page = doc[p.page]
        box = pymupdf.Rect(p.rect) + (-PAD, -PAD, PAD, PAD)
        lines = multi.lines()
        width = max(pymupdf.get_text_length(t, "helv", FONT_SIZE) for t in lines) + 8
        height = LINE * len(lines) + 4
        x, y, near = _free_spot(box, width, height, page, taken[p.page])
        taken[p.page].append(pymupdf.Rect(x, y, x + width, y + height))
        key = f"{p.tag.type}|{p.tag.tag}|{p.page}|{p.occurrence}"
        moved = key in placed
        if moved:
            x = max(0.0, min(placed[key][0], page.rect.width - width))
            y = max(0.0, min(placed[key][1], page.rect.height - height))
        content = "\n".join([MULTI_NOTE if multi.marked else "Doppelter Tag", *multi.database_lines(),
                             *lines[len(lines) - 1:] * multi.tag.duplicate])
        out.append(Note(key, p.page, p.tag.tag, tuple(box), (x, y, x + width, y + height), lines, content, moved,
                        moved or not near))
    return out


def notes_for(result: PdfResult, link: DataLink, file_value=None, value_of: Callable[[Tag], str] = lambda t: t.tag,
              store=None, placed: dict | None = None) -> list[Note]:
    """Eintraege einer PDF (fuer den Viewer)."""
    tags, store = _visible(result, store)
    found = find_multi_tags(link, marked_tags(tags, store), file_value, value_of)
    if not found:
        return []
    with pymupdf.open(result.path) as doc:
        return layout_notes(doc, found, placed)


def leader(note: Note) -> tuple[tuple[float, float], tuple[float, float]]:
    """Linie vom Tag-Rahmen zum Textfeld (jeweils naechster Punkt)."""
    def nearest(rect, x, y):
        return min(max(x, rect[0]), rect[2]), min(max(y, rect[1]), rect[3])

    r = note.rect
    start = nearest(note.box, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
    return start, nearest(r, *start)


def write_multitag_pdf(result: PdfResult, out_path: str | Path, link: DataLink, file_value=None,
                       value_of: Callable[[Tag], str] = lambda t: t.tag, store: ReviewStore | None = None,
                       layer: bool | None = None, placed: dict | None = None, table: bool | review_table.View = False,
                       monochrome: bool = False) -> int | None:
    """Kopie der PDF mit rotem Rahmen und rotem Text je Fundstelle eines doppelten Tags. Aus dem Review genommene und
    „No Tag“-Eintraege bleiben frei. ``table`` haengt die Tabelle aller Reviewpunkte an. Rueckgabe: Anzahl
    Fundstellen; ``None`` = nichts zu zeigen, keine Datei geschrieben."""
    tags, store = _visible(result, store)
    found = find_multi_tags(link, marked_tags(tags, store), file_value, value_of)
    notes_by_tag = {(m.tag.type, m.tag.tag): m.database_lines() or [f"{m.tag.count}× in dieser PDF"] for m in found}
    view = table if isinstance(table, review_table.View) else None
    review = review_table.build(result, tags, store, notes_by_tag, view) if table else None
    if not found and not review:
        return None
    red = _rgb(LIGHT.err)
    layer = review_layer_enabled() if layer is None else layer
    with pymupdf.open(result.path) as doc:
        if monochrome:
            mono.make_monochrome(doc)
        ocg = doc.add_ocg(f"MultiTag_{datetime.now():%d.%m.%Y}", on=True) if layer else 0
        notes = layout_notes(doc, found, placed)
        for note in notes:
            page = doc[note.page]
            derotate = page.derotation_matrix      # Positionen = sichtbare Lage, Annotationen ungedreht
            frame = page.add_rect_annot(pymupdf.Rect(note.box) * derotate)
            frame.set_colors(stroke=red)
            frame.set_border(width=BORDER)
            text = "\n".join(note.lines)
            label = page.add_freetext_annot(pymupdf.Rect(note.rect) * derotate, text, fontsize=FONT_SIZE,
                                            text_color=red, rotate=page.rotation)
            annots = [(frame, note.content), (label, text)]
            if note.line:
                start, end = leader(note)
                line = page.add_line_annot(pymupdf.Point(start) * derotate, pymupdf.Point(end) * derotate)
                line.set_colors(stroke=red)
                line.set_border(width=0.8)
                annots.append((line, note.content))
            for annot, info in annots:
                annot.set_info(title=AUTHOR, subject=f"Multi Tag – {note.tag}", content=info)
                if ocg:
                    annot.set_oc(ocg)
                annot.update()
        review_table.append(doc, result.name, review, ocg)
        doc.save(out_path, garbage=3, deflate=True)
    return len(notes)
