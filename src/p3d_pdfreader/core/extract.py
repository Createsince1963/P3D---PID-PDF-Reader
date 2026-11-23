"""PID-Tags, Metadaten und Schriftfeld aus Plant-3D-PDF-Plots lesen (ohne Qt, nur PyMuPDF).

Instrumente stehen im Plot als zwei Woerter in der Blase (Kuerzel oben, Nummer darunter) und werden ueber ihre Lage
zusammengesetzt. Rohrleitungsnummern (optional, ``pipes=True``) stehen waagerecht oder senkrecht an der Leitung; ein
Label kann in mehrere Woerter zerfallen (``201_07_092PS_ST03`` ``_205_1`` ``1/2"``) und wird wieder zusammengesetzt. Das Schriftfeld (rechts unten) hat beschriftete Felder ``DRAWN:``, ``CHECKED:`` ... - der Wert steht
auf derselben Grundlinie rechts vom Label. Am rechten Rand steht der Plotpfad ``C:\\Users\\<benutzer>\\...``.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pymupdf

from .patterns import PIPE, Patterns, has_placeholder, load

TITLE_LABELS = ("DESIGNED:", "DRAWN:", "CHECKED:", "DATE:", "SCALE:")
_MONTHS = {m: i for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV",
                                       "DEC"), start=1)}
_USER_RE = re.compile(r"[A-Za-z]:\\Users\\([^\\]+)\\", re.I)
_DRAWING_NO_RE = re.compile(r"-PID-")


@dataclass
class Tag:
    """Ein Tag einer PDF mit allen Fundstellen ``hits`` = [(Seite, Rechteck)] (Seite 0-basiert, sichtbare Lage).

    ``count`` = Anzahl auf der Seite mit den meisten Fundstellen. Mehrseitige Plots enthalten oft dieselbe Zeichnung
    mehrfach (z. B. Seite 2 = Kopie mit Markup-Kommentaren) - ein Tag, der auf jeder Seite einmal steht, ist darum
    **nicht** doppelt. Doppelt ist er nur, wenn er auf einer Seite mehrfach vorkommt."""
    tag: str
    type: str
    count: int = 1
    x: float = 0.0
    y: float = 0.0
    rect: tuple = ()
    hits: list = field(default_factory=list)

    @property
    def duplicate(self) -> bool:
        return self.count > 1

    @property
    def page(self) -> int:
        """Seite der ersten Fundstelle (bei Doppelten: erste Seite, auf der er mehrfach steht)."""
        per = self.per_page()
        multi = [p for p, n in per.items() if n > 1]
        return min(multi) if multi else (min(per) if per else 0)

    @property
    def pages(self) -> list[int]:
        return sorted({p for p, _r in self.hits})

    def per_page(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for p, _r in self.hits:
            out[p] = out.get(p, 0) + 1
        return out

    def rects_on(self, page: int) -> list[tuple]:
        return [r for p, r in self.hits if p == page]

    @property
    def rects(self) -> list[tuple]:
        """Fundstellen auf der massgeblichen Seite (``page``)."""
        return self.rects_on(self.page)

    @property
    def pages_text(self) -> str:
        """z. B. "1" oder "1, 2 (2×)" - Seitennummern 1-basiert, Mehrfach-Anzahl je Seite in Klammern."""
        return ", ".join(f"{p + 1}" + (f" ({n}×)" if n > 1 else "") for p, n in sorted(self.per_page().items()))


@dataclass
class PdfResult:
    path: Path
    pages: int = 0
    created: datetime | None = None
    modified: datetime | None = None
    creator: str = ""
    producer: str = ""
    author: str = ""
    title: str = ""
    size_kb: int = 0
    drawing_no: str = ""
    drawing_title: str = ""
    designed: str = ""
    drawn: str = ""
    checked: str = ""
    title_date: str = ""
    revision: str = ""
    revision_date: str = ""
    revision_text: str = ""
    revision_by: str = ""
    plot_user: str = ""
    tags: list[Tag] = field(default_factory=list)
    error: str = ""

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def author_display(self) -> str:
        """Ersteller: DRAWN im Schriftfeld, sonst Revisions-Kuerzel, sonst PDF-Author, sonst Plot-Benutzer."""
        return self.drawn or self.revision_by or self.author or self.plot_user


def pdf_date(value: str) -> datetime | None:
    """``D:20261019103250+01'00'`` -> datetime (ohne Zeitzone)."""
    m = re.match(r"D:(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?", value or "")
    if not m:
        return None
    parts = [int(p) if p else d for p, d in zip(m.groups(), (0, 1, 1, 0, 0, 0))]
    try:
        return datetime(*parts)
    except ValueError:
        return None


def _date_key(text: str) -> tuple:
    parts = text.split()
    try:
        return int(parts[2]), _MONTHS.get(parts[1], 0), int(parts[0])
    except (IndexError, ValueError):
        return (0, 0, 0)


def _lines(words, x_min: float, y_min: float, tol: float = 2.5) -> list[list]:
    """Woerter im Bereich zu Zeilen gruppieren (gleiche Grundlinie), links nach rechts."""
    rows: list[list] = []
    for w in sorted((w for w in words if w[0] >= x_min and w[1] >= y_min), key=lambda w: (w[3], w[0])):
        if rows and abs(rows[-1][0][3] - w[3]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return [sorted(r, key=lambda w: w[0]) for r in rows]


def _font_size(w) -> float:
    """Schriftgroesse eines Worts = kuerzere Seite seines Rahmens (senkrecht geschriebene Verweise haben einen hohen,
    schmalen Rahmen und galten sonst als groesste Schrift - falsche Zeichnungsnummer, 1.0.38)."""
    return min(w[2] - w[0], w[3] - w[1])


def _drawing_no_fallback(words, width: float, height: float) -> str:
    """Zeichnungsnummer, wenn sie nicht ganz rechts im Schriftfeld steht (z. B. Schriftfeld mit Kunden- und
    Exyte-Nummer: Nummer beginnt bei ~82 % der Breite, 1.0.38). Gesucht wird im unteren Zehntel ab 60 % der Breite,
    aber nur in deutlich groesserer Schrift als der uebliche Text - so zaehlen Anschlussverweise auf andere
    Zeichnungen (normale Schrift) nicht."""
    sizes = sorted(s for s in map(_font_size, words) if s > 0)
    if not sizes:
        return ""
    usual = sizes[len(sizes) // 2]
    numbers = [w for w in words if _DRAWING_NO_RE.search(w[4]) and w[1] > height * 0.9 and w[0] >= width * 0.6
               and _font_size(w) >= usual * 1.3]
    return max(numbers, key=_font_size)[4] if numbers else ""


def _value_below(label, right: float, lines: list[list]) -> str:
    """Wert direkt unter einem Schriftfeld-Label („CHECKED:“ / naechste Zeile „I.MURALT“): die Zeile, die hoechstens
    eine halbe Schrifthoehe unter dem Label beginnt, in der Spalte des Labels (bis zum naechsten Label rechts). Zeilen
    mit einem weiteren Label oder einem Doppelpunkt-Begriff zaehlen nicht."""
    h = label[3] - label[1]
    for row in lines:
        cell = [w for w in row if label[0] - h * 0.5 <= w[0] < right]
        if not cell or not (label[1] + h * 0.5 < min(w[1] for w in cell) <= label[3] + h * 0.5):
            continue
        if any(w[4].upper() in TITLE_LABELS or w[4].endswith(":") for w in cell):
            continue
        return " ".join(w[4] for w in cell if w[4] not in ("-", ":")).strip()
    return ""


def _title_block(result: PdfResult, words, width: float, height: float, pat: Patterns) -> None:
    for w in words:
        m = _USER_RE.search(w[4])
        if m:
            result.plot_user = m.group(1)
            break
    lines = _lines(words, width * 0.85, height * 0.45)
    alone = []                                       # Labels ohne jeden Text rechts daneben (Wert evtl. darunter)
    for row in lines:
        labels = [i for i, w in enumerate(row) if w[4].upper() in TITLE_LABELS]
        for n, i in enumerate(labels):
            end = labels[n + 1] if n + 1 < len(labels) else len(row)
            value = " ".join(w[4] for w in row[i + 1:end] if w[4] not in ("-", ":")).strip()
            label = row[i][4].upper().rstrip(":")
            attr = {"DESIGNED": "designed", "DRAWN": "drawn", "CHECKED": "checked", "DATE": "title_date"}.get(label)
            if attr and value and value.upper() != "NA":
                setattr(result, attr, value)
            elif attr and end == i + 1:
                alone.append((attr, row[i], row[labels[n + 1]][0] if n + 1 < len(labels) else width))
    for attr, label, right in alone:                 # 1.0.38: Name in der 2. Zeile (Platz im Plankopf zu knapp)
        if not getattr(result, attr):
            value = _value_below(label, right, lines)
            if value and value.upper() != "NA":
                setattr(result, attr, value)
    # Zeichnungsnummer: groesste Schrift mit -PID- im Schriftfeld
    numbers = [w for row in lines for w in row if _DRAWING_NO_RE.search(w[4]) and w[1] > height * 0.9]
    if numbers:
        result.drawing_no = max(numbers, key=_font_size)[4]
    else:
        result.drawing_no = _drawing_no_fallback(words, width, height)
    # Revisionszeilen: <Rev> <TT MON JJJJ> <Text ...> <Kuerzel> <Kuerzel> <Kuerzel>
    best = None
    for row in lines:
        texts = [w[4] for w in row]
        for i in range(len(texts) - 3):
            date = " ".join(texts[i + 1:i + 4])
            if re.fullmatch(r"[A-Z0-9]{1,3}", texts[i]) and pat.revision_date.match(date):
                rest = texts[i + 4:]
                initials = [t for t in rest[-3:] if re.fullmatch(r"[A-Z]{2,4}", t)]
                text = " ".join(rest[:len(rest) - len(initials)])
                cand = (_date_key(date), texts[i], date, text, initials)
                if best is None or cand[0] > best[0]:
                    best = cand
                break
    if best:
        _, result.revision, result.revision_date, result.revision_text, initials = best
        result.revision_by = initials[0] if initials else ""


def _overlap(a: tuple, b: tuple) -> float:
    """Anteil der Ueberdeckung zweier Rechtecke (bezogen auf das kleinere)."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1])) or 1.0
    return w * h / smaller


_FRACTION_RE = re.compile(r'^\d+/\d+"?$')
_SIZE_END_RE = re.compile(r"_\d+$")


def _line_key(w) -> tuple:
    """(Block, Zeile) eines Worts aus ``get_text("words")`` - unabhaengig von der Schreibrichtung."""
    return (w[5], w[6]) if len(w) > 7 else (id(w), 0)


def _pipe_lines(words, pat: Patterns, placeholders: bool = False) -> list[tuple[str, tuple]]:
    """Rohrleitungsnummern einer Seite: [(Nummer, Rechteck)].

    PyMuPDF liefert die Woerter je Textzeile in Schreibrichtung - fuer waagerechte und senkrechte Labels gleich. Folgt
    in derselben Zeile ein Teil mit ``_`` (``_205_1``) wird er direkt angehaengt, eine Bruch-Nennweite (``1/2"``) nach
    ``…_1`` mit Leerzeichen (1 1/2"). Gesucht wird der laengste passende Anfang ab jedem Wort."""
    found: list[tuple[str, tuple]] = []

    def is_pipe(t: str) -> bool:
        return bool(pat.pipe_line.match(t)) or (placeholders and pat.ph_pipe_line is not None
                                                 and has_placeholder(t) and bool(pat.ph_pipe_line.match(t)))
    i = 0
    while i < len(words):
        w = words[i]
        text, rect, best = w[4], list(w[:4]), None
        if is_pipe(text):
            best = (text, tuple(rect), i)
        j = i + 1
        while j < len(words) and _line_key(words[j]) == _line_key(w):
            nxt = words[j][4]
            if nxt.startswith("_"):
                text += nxt
            elif _FRACTION_RE.match(nxt) and _SIZE_END_RE.search(text):
                text += " " + nxt
            else:
                break
            rect = [min(rect[0], words[j][0]), min(rect[1], words[j][1]),
                    max(rect[2], words[j][2]), max(rect[3], words[j][3])]
            if is_pipe(text):
                best = (text, tuple(rect), j)
            j += 1
        if best:
            found.append(best[:2])
            i = best[2] + 1
        else:
            i += 1
    return found


def _tags(words, pat: Patterns, pipes: bool = False, placeholders: bool = False) -> list[tuple[str, str, tuple]]:
    """Fundstellen einer Seite: [(Typ, Tag, Rechteck)]. Deckungsgleicher Text (im Plot doppelt uebereinander
    gezeichnet, z. B. Inhalt + eingebettetes Formular-XObject) zaehlt nur einmal. ``placeholders`` (Projektmodus):
    auch Tags mit X/? statt Ziffern (z. B. VHXXX, AV_TL02_XXX_2") - die Projekt-Pruefung meldet sie als unvollstaendig."""
    found: list[tuple[str, str, tuple]] = []

    def add(tag: str, typ: str, w) -> None:
        rect = tuple(round(v, 1) for v in w[:4])
        if any(t == typ and g == tag and _overlap(r, rect) > 0.8 for t, g, r in found):
            return
        found.append((typ, tag, rect))

    if pipes:
        for tag, rect in _pipe_lines(words, pat, placeholders):
            add(tag, PIPE, rect)
    numbers = [w for w in words if pat.number.match(w[4])
               or (placeholders and pat.ph_number is not None and has_placeholder(w[4]) and pat.ph_number.match(w[4]))]
    used = set()
    for w in words:
        text = w[4]
        typ = next((t for t, rx in pat.by_type.items() if rx.match(text)), None)
        if typ is None and placeholders:
            typ = pat.placeholder_type(text)
        if typ:
            add(text, typ, w)
            continue
        if not pat.letters.match(text) or text.upper() in pat.exclude:
            continue
        h = w[3] - w[1]
        cx = (w[0] + w[2]) / 2
        best = None
        for i, n in enumerate(numbers):
            if i in used:
                continue
            dy = n[1] - w[3]
            if -0.5 * h <= dy <= 1.5 * h and n[0] - h <= cx <= n[2] + h:
                if best is None or dy < best[1]:
                    best = (i, dy)
        if best:
            used.add(best[0])
            n = numbers[best[0]]
            add(f"{text}-{n[4]}", "Instrument", (min(w[0], n[0]), w[1], max(w[2], n[2]), n[3]))
    return found


def visible_words(page) -> list[tuple]:
    """Woerter in der sichtbaren (gedrehten) Lage der Seite.

    PyMuPDF liefert Wortpositionen im ungedrehten Koordinatensystem. Bei Plots mit ``/Rotate`` (z. B. 270) liegen sie
    dann quer zur Ansicht - Blasen-Paarung (Kuerzel ueber Nummer), Schriftfeld und Markierungen wuerden nicht passen.
    Deshalb hier in die Lage umrechnen, in der die Seite angezeigt und gerendert wird (``page.rect``)."""
    words = page.get_text("words")
    if not page.rotation:
        return words
    m = page.rotation_matrix
    out = []
    for w in words:
        r = pymupdf.Rect(w[:4]) * m
        out.append((r.x0, r.y0, r.x1, r.y1, *w[4:]))
    return out


def read_pdf(path: str | Path, patterns: Patterns | None = None, pipes: bool = False,
             placeholders: bool = False) -> PdfResult:
    """PDF lesen. ``pipes``: Rohrleitungsnummern als Typ "Rohrleitung" mit in die Tag-Liste aufnehmen.
    ``placeholders`` (Projektmodus): auch Platzhalter-Tags mit X/? statt Ziffern."""
    path = Path(path)
    result = PdfResult(path=path)
    pat = patterns or load()
    try:
        result.size_kb = round(path.stat().st_size / 1024)
        with pymupdf.open(path) as doc:
            meta = doc.metadata or {}
            result.pages = doc.page_count
            result.created = pdf_date(meta.get("creationDate", ""))
            result.modified = pdf_date(meta.get("modDate", ""))
            result.creator = meta.get("creator", "") or ""
            result.producer = meta.get("producer", "") or ""
            result.author = meta.get("author", "") or ""
            result.title = meta.get("title", "") or ""
            merged: dict[tuple, Tag] = {}
            for page in doc:
                words = visible_words(page)
                if page.number == 0:
                    _title_block(result, words, page.rect.width, page.rect.height, pat)
                for typ, tag, rect in _tags(words, pat, pipes, placeholders):
                    key = (typ, tag)
                    if key not in merged:
                        merged[key] = Tag(tag, typ, 1, rect[0], rect[1], rect)
                    merged[key].hits.append((page.number, rect))
            for t in merged.values():                      # Anzahl = Maximum je Seite (nicht Summe ueber Seiten)
                t.count = max(t.per_page().values())
                first = t.rects[0]
                t.rect, t.x, t.y = first, first[0], first[1]
            result.tags = sorted(merged.values(), key=lambda t: (t.type, t.tag))
            if result.drawing_no:
                result.tags = [t for t in result.tags if t.tag != result.drawing_no]
    except Exception as exc:  # noqa: BLE001 - eine defekte Datei darf den Scan nie abbrechen
        result.error = f"{type(exc).__name__}: {exc}"
    return result


def find_pdfs(folders) -> list[Path]:
    seen, out = set(), []
    for folder in folders:
        folder = Path(folder)
        items = [folder] if folder.is_file() else sorted(folder.rglob("*.pdf"), key=lambda p: p.name.casefold())
        for p in items:
            key = str(p.resolve()).casefold()
            if p.suffix.lower() == ".pdf" and key not in seen:
                seen.add(key)
                out.append(p)
    return out


def summary(results: list[PdfResult]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        for t in r.tags:
            counts[t.type] += 1
    return dict(counts)
