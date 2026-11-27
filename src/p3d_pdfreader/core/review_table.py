"""Tabelle aller Reviewpunkte als zusaetzliche Seite(n) am Ende einer PDF-Kopie (1.0.55). Ohne Qt.

Reviewpunkt = Tag mit mindestens einem Review-Eintrag oder mit Multi-Tag-Befund. Pos.-Nr. wie in Redline und
Review-Excel. Mit ``View`` stehen die Spalten so da wie im Tool eingestellt (Auswahl, Reihenfolge, Breite)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import pymupdf
from main_gui_kit.theme import LIGHT

from .extract import PdfResult, Tag
from .review import positions
from .review_store import FIELDS

HEADERS = ["Pos.", "Seite", "Typ", "Tag", *FIELDS, "Datenbank (Multi Tag)"]
WIDTHS = [48, 34, 62, 100, 66, 70, 70, 150, 50, 52, 52, 360]     # Anteile, werden auf die Blattbreite verteilt
DB_HEAD = "Datenbank (Multi Tag)"
PIXEL = 0.6                 # PDF-Punkte je Bildschirm-Pixel der Spaltenbreite
PAGE = (1191.0, 842.0)      # A3 quer; viele Spalten: groesseres Blatt im gleichen Seitenverhaeltnis
MARGIN = 28.0
SIZE = 7.0
LINE = SIZE * 1.3


@dataclass
class View:
    """Spalten wie in der Tag-Tabelle: Koepfe, Breiten (Pixel) und die Zellen je (Typ, Tag)."""
    headers: list[str]
    widths: list[float]
    cells: Callable[[], dict]


@dataclass
class Table:
    headers: list[str]
    widths: list[float]             # Anteile
    rows: list[list]
    natural: float = 0.0            # gewuenschte Breite in PDF-Punkten (0 = A3)

    def __bool__(self) -> bool:
        return bool(self.rows)


def build(result: PdfResult, tags: list[Tag], store=None, notes: dict | None = None,
          view: View | None = None) -> Table:
    """``notes`` = {(Typ, Tag): [Datenbankzeilen]} aus dem Multi-Tag-Befund."""
    notes = notes or {}
    found: dict[tuple, list] = {}
    for p in positions(tags):
        found.setdefault((p.tag.type, p.tag.tag), []).append(p)
    cells = view.cells() if view is not None else {}
    out = []
    for key, hits in sorted(found.items(), key=lambda kv: kv[1][0].pos):
        values = store.values(*key) if store is not None else [""] * len(FIELDS)
        if not any(values) and key not in notes:
            continue
        numbers = ", ".join(str(p.pos) for p in hits)
        database = "\n".join(notes.get(key, []))
        if view is None:
            pages = ", ".join(str(n) for n in sorted({p.page + 1 for p in hits}))
            out.append([numbers, pages, key[0], key[1], *values, database])
        else:
            row = list(cells.get(key, [""] * len(view.headers)))
            out.append([numbers, *row, *([database] if notes else [])])
    if view is None:
        return Table(HEADERS, WIDTHS, out)
    widths = [48 / PIXEL, *view.widths] + ([360 / PIXEL] if notes else [])
    headers = ["Pos.", *view.headers] + ([DB_HEAD] if notes else [])
    return Table(headers, widths, out, sum(widths) * PIXEL)


def _plain(text) -> str:
    """Zeichen, die die PDF-Standardschrift nicht hat."""
    return str(text).replace("…", "...").replace("–", "-").replace("„", '"').replace("“", '"')


def _wrap(text, width: float, font: str = "helv") -> list[str]:
    def fits(s: str) -> bool:
        return pymupdf.get_text_length(s, font, SIZE) <= width

    out: list[str] = []
    for part in _plain(text).split("\n"):
        line = ""
        for word in part.split(" "):
            trial = f"{line} {word}" if line else word
            if fits(trial):
                line = trial
                continue
            if line:
                out.append(line)
            while len(word) > 1 and not fits(word):          # sehr lange Woerter hart umbrechen
                n = len(word) - 1
                while n > 1 and not fits(word[:n]):
                    n -= 1
                out.append(word[:n])
                word = word[n:]
            line = word
        out.append(line)
    return out


def append(doc, name: str, table: Table | None, layer: int = 0) -> int:
    """Seiten mit der Tabelle anhaengen. Rueckgabe: Anzahl Seiten."""
    if not table:
        return 0
    page_width = max(PAGE[0], table.natural + 2 * MARGIN)
    page_height = page_width * PAGE[1] / PAGE[0]
    scale = (page_width - 2 * MARGIN) / sum(table.widths)
    widths = [w * scale for w in table.widths]
    head = _rgb(LIGHT.hdr)
    line = _rgb(LIGHT.border)
    pages, page, y = 0, None, 0.0

    def draw(cells: list[list[str]], top: float, fill=None, font: str = "helv") -> float:
        height = LINE * max(len(c) for c in cells) + 4
        x = MARGIN
        for cell, width in zip(cells, widths):
            page.draw_rect(pymupdf.Rect(x, top, x + width, top + height), color=line, fill=fill, width=0.5, oc=layer)
            for n, text in enumerate(cell):
                page.insert_text((x + 3, top + 2 + SIZE + n * LINE), text, fontsize=SIZE, fontname=font, oc=layer)
            x += width
        return top + height

    header = [_wrap(h, w - 6, "hebo") for h, w in zip(table.headers, widths)]
    most = int((page_height - 2 * MARGIN - 60) / LINE)           # eine Zeile passt immer auf eine Seite
    for row in table.rows:
        cells = [_wrap(v, w - 6)[:most] for v, w in zip(row, widths)]
        height = LINE * max(len(c) for c in cells) + 4
        if page is None or y + height > page_height - MARGIN:
            page = doc.new_page(width=page_width, height=page_height)
            pages += 1
            page.insert_text((MARGIN, MARGIN + 6), _plain(f"Reviewpunkte - {name} - {datetime.now():%d.%m.%Y %H:%M}"),
                             fontsize=11, fontname="hebo", oc=layer)
            y = draw(header, MARGIN + 16, fill=head, font="hebo")
        y = draw(cells, y)
    return pages


def _rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
