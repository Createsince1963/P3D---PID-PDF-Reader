"""Monochrome Ausgabe (1.0.55): Farben der Zeichnung in einer PDF-Kopie wie im Viewer auf Schwarz-Weiss setzen -
Grauwert = (dunkelster Farbkanal) ** ``MONO_GAMMA``. Geaendert werden nur die Farbbefehle im Seiteninhalt, die
Zeichnung bleibt Vektorgrafik. Vor dem Anlegen der Review-Kommentare aufrufen, dann behalten diese ihre Farben.
Rasterbilder (z. B. Logos) und Farbverlaeufe bleiben unveraendert. Ohne Qt."""
from __future__ import annotations

import re

from .render import MONO_GAMMA

_TOKEN = re.compile(rb"%[^\r\n]*|\((?:\\.|[^\\()]|\((?:\\.|[^\\()])*\))*\)|<<|>>|<[0-9A-Fa-f\s]*>|\[|\]"
                    rb"|/[^\s()<>\[\]{}/%]*|[^\s()<>\[\]{}/%]+", re.DOTALL)
_NUMBER = re.compile(rb"[+-]?(?:\d+\.?\d*|\.\d+)$")
_END_IMAGE = re.compile(rb"\sEI(?=\s|$)")
_FIXED = {b"g": 1, b"G": 1, b"rg": 3, b"RG": 3, b"k": 4, b"K": 4}
_ANY = (b"sc", b"SC", b"scn", b"SCN")


def _gray(values: list[float]) -> float:
    if len(values) == 4:                                    # CMYK
        k = values[3]
        values = [(1 - v) * (1 - k) for v in values[:3]]
    return max(0.0, min(1.0, min(values))) ** MONO_GAMMA


def _replacement(operator: bytes, values: list[float]) -> bytes:
    v = _gray(values)
    if len(values) == 4:
        parts = [0, 0, 0, 1 - v]
    else:
        parts = [v] * len(values)
    return b" ".join(b"%g" % round(p, 3) for p in parts) + b" " + operator


def recolor_stream(data: bytes) -> bytes:
    out, done, pos = [], 0, 0
    numbers: list[tuple[int, float]] = []                   # (Beginn, Wert) der Operanden davor
    while True:
        match = _TOKEN.search(data, pos)
        if match is None:
            break
        token, pos = match.group(), match.end()
        if token.startswith(b"%"):
            continue
        if _NUMBER.match(token):
            numbers.append((match.start(), float(token)))
            continue
        count = _FIXED.get(token) or (len(numbers) if token in _ANY and len(numbers) in (1, 3, 4) else 0)
        if token in _ANY and count == 1:                    # Grau-, Sonder- oder Palettenfarbe: unveraendert
            count = 0
        if count and len(numbers) >= count:
            used = numbers[-count:]
            out += [data[done:used[0][0]], _replacement(token, [v for _s, v in used])]
            done = match.end()
        elif token == b"ID":                                # Bilddaten im Inhaltsstrom ueberspringen
            end = _END_IMAGE.search(data, pos)
            pos = end.end() if end else len(data)
        numbers = []
    out.append(data[done:])
    return b"".join(out)


def make_monochrome(doc) -> None:
    """Alle Seiten und ihre Form-Objekte umfaerben (Kommentare nicht)."""
    seen: set[int] = set()
    for page in doc:
        page.clean_contents(sanitize=False)                 # ein Inhaltsstrom je Seite
        for xref in [*page.get_contents(), *(item[0] for item in page.get_xobjects())]:
            if xref in seen or not doc.xref_is_stream(xref):
                continue
            seen.add(xref)
            data = doc.xref_stream(xref)
            changed = recolor_stream(data)
            if changed != data:
                doc.update_stream(xref, changed)
