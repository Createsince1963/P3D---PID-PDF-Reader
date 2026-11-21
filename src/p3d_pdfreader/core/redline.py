"""Redline-PDF: Kopie des Plots mit PDF-Kommentaren (Annotationen) an jeder erkannten Tag-Fundstelle.

Das Original bleibt unveraendert. Jede Fundstelle bekommt einen Rahmen mit Kommentar (Autor, Betreff "Pos. n - Tag",
Text) - in Acrobat/Bluebeam/PDF-XChange in der Kommentarliste. Die Pos.-Nr. ist dieselbe wie in der Review-Excel
(``review.positions``). Normale Tags rot, doppelte Tags (Anzahl > 1) orange; neben jedem Rahmen steht die Pos.-Nr.
Oben links steht ein Uebersichtskommentar. Nur Seite 1 (Plant-3D-Plots sind einseitig)."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

import pymupdf

from .extract import PdfResult, Tag
from .review import positions

AUTHOR = "P3D PDF Reader"
RED = (0.85, 0.1, 0.1)
ORANGE = (0.95, 0.55, 0.0)
PAD = 2.0                      # Abstand des Rahmens um den Text (PDF-Punkte)


def write_redline(result: PdfResult, out_path: str | Path, tags: list[Tag] | None = None) -> int:
    """Redline-PDF schreiben. ``tags`` = Auswahl (z. B. gefilterte Tabelle), sonst alle Tags. Rueckgabe: Anzahl Kommentare."""
    tags = result.tags if tags is None else tags
    out_path = Path(out_path)
    items = positions(tags)
    with pymupdf.open(result.path) as doc:
        for p in items:
            page = doc[p.page]                          # Fundstelle auf ihrer Seite (mehrseitige Plots)
            # Tag-Positionen liegen in der sichtbaren (gedrehten) Lage, Annotationen erwartet PyMuPDF ungedreht
            derotate = page.derotation_matrix
            color = ORANGE if p.total > 1 else RED
            box = pymupdf.Rect(p.rect) + (-PAD, -PAD, PAD, PAD)
            annot = page.add_rect_annot(box * derotate)
            annot.set_colors(stroke=color)
            annot.set_border(width=1.5)
            text = f"Pos. {p.pos}\nTyp: {p.tag.type}\nTag: {p.tag.tag}"
            if doc.page_count > 1:
                text += f"\nSeite: {p.page + 1}"
            if p.total > 1:
                text += f"\nDoppelter Tag: Fundstelle {p.occurrence} / {p.total} auf dieser Seite"
            annot.set_info(title=AUTHOR, subject=f"Pos. {p.pos} – {p.tag.tag}", content=text)
            annot.update()
            label = page.add_freetext_annot(
                pymupdf.Rect(box.x1 + 1, box.y0 - 9, box.x1 + 1 + 8 + 5 * len(str(p.pos)), box.y0) * derotate,
                str(p.pos), fontsize=6, text_color=color, rotate=page.rotation)
            label.set_info(title=AUTHOR, subject=f"Pos. {p.pos}")      # content = angezeigter Text (die Nummer)
            label.update()
        per_type = Counter(t.type for t in tags)
        dups = sum(1 for t in tags if t.duplicate)
        summary = (f"{AUTHOR} – Redline\nDatei: {result.name}\nErstellt: {datetime.now():%Y-%m-%d %H:%M}\n"
                   f"Tags: {len(tags)} ({', '.join(f'{k} {v}' for k, v in sorted(per_type.items()))})\n"
                   f"Positionen: {len(items)} (Pos.-Nr. wie in der Review-Excel)\nDoppelte Tags (orange): {dups}")
        page = doc[0]
        note = page.add_text_annot(pymupdf.Point(20, 20) * page.derotation_matrix, summary, icon="Note")
        note.set_info(title=AUTHOR, subject="Übersicht")
        note.update()
        doc.save(out_path, garbage=3, deflate=True)
    return len(items)
