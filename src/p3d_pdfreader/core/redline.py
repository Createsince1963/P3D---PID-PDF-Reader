"""Redline-PDF: Kopie des Plots mit PDF-Kommentaren (Annotationen) an jeder erkannten Tag-Fundstelle.

Das Original bleibt unveraendert. Jede Fundstelle bekommt einen Rahmen mit Kommentar (Autor, Betreff "Pos. n - Tag",
Text) - in Acrobat/Bluebeam/PDF-XChange in der Kommentarliste. Die Pos.-Nr. ist dieselbe wie in der Review-Excel
(``review.positions``). Farben und Rahmen wie im Viewer der App: korrekte Tags gruen, fehlerhafte (Review "Korrektur
erforderlich" bzw. im Projektmodus Abweichung) rot, doppelte Tags (Anzahl > 1 auf der Seite) zusaetzlich gelb
hinterlegt; neben jedem Rahmen steht die Pos.-Nr. in Rahmenfarbe. Oben links steht ein Uebersichtskommentar.
Tags mit Review "No Tag" werden nicht gekennzeichnet; die Pos.-Nr. der uebrigen bleiben wie in der Review-Excel.

Optional (Einstellung "Layer fuer Review im PDF", Standard an) liegen alle Kommentare auf einer eigenen PDF-Ebene
(Optional Content Group) ``Review_TT.MM.JJJJ`` - in Acrobat/PDF-XChange/Bluebeam unter "Ebenen" ein- und ausblendbar."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pymupdf
from main_gui_kit.theme import LIGHT

from ..paths import config_dir
from . import mono, review_table, type_filter
from .extract import PdfResult, Tag
from .review import positions
from .review_store import ReviewStore, is_faulty, marked_tags

AUTHOR = "P3D PDF Reader"
DIRTY = "#FFF2CC"              # = gui.appearance.DEFAULT_DIRTY (doppelte Tags; appearance importiert Qt)
PAD = 3.0                      # Abstand des Rahmens um den Text (PDF-Punkte), wie im Web-Viewer
BORDER = 1.5                   # Rahmenbreite wie im Viewer
LAYER_KEY = "redline_review_layer"   # config/state.json (Desktop: Projekt › Einstellungen; gilt auch fuer den Web-Server)


def review_layer_enabled() -> bool:
    """Einstellung "Layer fuer Review im PDF" (Standard an); ohne Qt lesbar, damit auch der Web-Server sie nutzt."""
    try:
        data = json.loads((config_dir() / "state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return bool(data.get(LAYER_KEY, True)) if isinstance(data, dict) else True


def review_layer_name(when: datetime | None = None) -> str:
    return f"Review_{(when or datetime.now()):%d.%m.%Y}"


def _rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def write_redline(result: PdfResult, out_path: str | Path, tags: list[Tag] | None = None,
                  store: ReviewStore | None = None, checker=None, layer: bool | None = None,
                  table: bool | review_table.View = False, monochrome: bool = False) -> int:
    """Redline-PDF schreiben. ``tags`` = Auswahl (z. B. gefilterte Tabelle), sonst alle Tags. ``store`` = Review-Eintraege
    der PDF (sonst der gespeicherte Stand), ``checker`` = Projektpruefung (Projektmodus). ``layer`` = Kommentare auf die
    Ebene ``Review_TT.MM.JJJJ`` legen (``None`` = Einstellung). Rueckgabe: Anzahl Rahmen."""
    tags = type_filter.apply(result.tags if tags is None else tags)
    out_path = Path(out_path)
    if store is None:
        try:
            store = ReviewStore(result.path)
        except OSError:
            store = None
    if callable(getattr(store, "visible", None)):
        tags = store.visible(tags)                   # aus dem Review genommene Tags nicht markieren (1.0.43)
    review = review_table.build(result, tags, store, view=table if isinstance(table, review_table.View)
                                else None) if table else None          # vor „No Tag“ weglassen
    ok, bad, dirty = _rgb(LIGHT.ok), _rgb(LIGHT.err), _rgb(DIRTY)
    marked = marked_tags(tags, store)                # Review "No Tag": nicht kennzeichnen
    shown = {(t.type, t.tag) for t in marked}
    faulty = {(t.type, t.tag) for t in marked if is_faulty(t, store, checker)}
    # Pos.-Nr. ueber alle Tags vergeben (gleich wie in der Review-Excel), erst danach "No Tag" weglassen
    items = [p for p in positions(tags) if (p.tag.type, p.tag.tag) in shown]
    unmarked = len(tags) - len(marked)
    tags = marked
    layer = review_layer_enabled() if layer is None else layer
    with pymupdf.open(result.path) as doc:
        if monochrome:
            mono.make_monochrome(doc)                    # vor den Kommentaren: diese behalten ihre Farben
        ocg = doc.add_ocg(review_layer_name(), on=True) if layer else 0

        def done(annot) -> None:
            if ocg:
                annot.set_oc(ocg)
            annot.update()

        for p in items:
            page = doc[p.page]                          # Fundstelle auf ihrer Seite (mehrseitige Plots)
            # Tag-Positionen liegen in der sichtbaren (gedrehten) Lage, Annotationen erwartet PyMuPDF ungedreht
            derotate = page.derotation_matrix
            wrong = (p.tag.type, p.tag.tag) in faulty
            color = bad if wrong else ok
            box = pymupdf.Rect(p.rect) + (-PAD, -PAD, PAD, PAD)
            annot = page.add_rect_annot(box * derotate)
            annot.set_colors(stroke=color, fill=dirty if p.total > 1 else None)
            annot.set_border(width=BORDER)
            if p.total > 1:
                annot.set_blendmode(pymupdf.PDF_BM_Multiply)     # gelb hinterlegt, Plotlinien bleiben sichtbar
            text = f"Pos. {p.pos}\nTyp: {p.tag.type}\nTag: {p.tag.tag}"
            if doc.page_count > 1:
                text += f"\nSeite: {p.page + 1}"
            if wrong:
                text += "\nStatus: fehlerhaft"
            if p.total > 1:
                text += f"\nDoppelter Tag: Fundstelle {p.occurrence} / {p.total} auf dieser Seite"
            annot.set_info(title=AUTHOR, subject=f"Pos. {p.pos} – {p.tag.tag}", content=text)
            done(annot)
            label = page.add_freetext_annot(
                pymupdf.Rect(box.x1 + 1, box.y0 - 9, box.x1 + 1 + 8 + 5 * len(str(p.pos)), box.y0) * derotate,
                str(p.pos), fontsize=6, text_color=color, rotate=page.rotation)
            label.set_info(title=AUTHOR, subject=f"Pos. {p.pos}")      # content = angezeigter Text (die Nummer)
            done(label)
        per_type = Counter(t.type for t in tags)
        dups = sum(1 for t in tags if t.duplicate)
        summary = (f"{AUTHOR} – Redline\nDatei: {result.name}\nErstellt: {datetime.now():%Y-%m-%d %H:%M}\n"
                   f"Tags: {len(tags)} ({', '.join(f'{k} {v}' for k, v in sorted(per_type.items()))})\n"
                   f"Positionen: {len(items)} (Pos.-Nr. wie in der Review-Excel)\n"
                   f"Rahmen grün = korrekt, rot = fehlerhaft: {len(faulty)} Tag(s)\n"
                   f"Doppelte Tags (gelb hinterlegt): {dups}"
                   + (f"\nReview „No Tag“ (nicht markiert): {unmarked}" if unmarked else "")
                   + (f"\nEbene: {review_layer_name()}" if ocg else ""))
        page = doc[0]
        note = page.add_text_annot(pymupdf.Point(20, 20) * page.derotation_matrix, summary, icon="Note")
        note.set_info(title=AUTHOR, subject="Übersicht")
        done(note)
        review_table.append(doc, result.name, review, ocg)
        doc.save(out_path, garbage=3, deflate=True)
    return len(items)
