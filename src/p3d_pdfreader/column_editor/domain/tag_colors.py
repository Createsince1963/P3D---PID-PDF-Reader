"""Colour categories of the tile editor: tag type colours of the project definitions (Tag structures) -> column tiles. Qt-free.

The project definitions give every tag type an optional colour (`#RRGGBB` or `#RRGGBB@NN` with an opacity of NN = 10 ... 90 %,
empty = neutral); the tiles get the colour as it looks on white (`solid_color`). A column tile takes the colour of
the tag type its name stands for (e.g. column "Building" -> tag type "Building", "System Code" -> "System"). The full line
number is neutral on purpose, columns that match no tag type are neutral too.
"""
from __future__ import annotations

import re

# tag types that stand for the complete line number: never coloured (the single tags it is made of carry the colours)
NEUTRAL_TAG_TYPES = frozenset({"linenumber", "linetag", "line", "linenumbertag", "pidlinenumber"})
MIN_NAME_LENGTH = 3
_COLOR = re.compile(r"^#([0-9A-Fa-f]{6})(?:@(\d{1,3}))?$")


def solid_color(value) -> str:
    """'#RRGGBB' of a stored tag colour with its opacity blended onto white; '' when empty or invalid."""
    m = _COLOR.match(str(value or "").strip())
    if not m:
        return ""
    opacity = 100 if m.group(2) is None else int(m.group(2))
    if opacity not in range(10, 101, 10):
        return ""
    a = opacity / 100.0
    rgb = [round(int(m.group(1)[i:i + 2], 16) * a + 255 * (1 - a)) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(rgb)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).casefold())


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", str(text).casefold()) if w]


def match_tag_type(label: str, colors: dict[str, str]) -> tuple[str, str]:
    """(tag type, '#RRGGBB') for a column label, or ('', '') when the column is neutral.

    Order: exact name, then the label starts with the tag type name ("System Code" -> "System"), then the tag type name is one
    word of the label. The longest tag type name wins. Tag types of the full line number and invalid colours are ignored."""
    n = _norm(label)
    if not n:
        return "", ""
    words = set(_words(label))
    best: tuple[int, str, str] | None = None
    for tag, color in colors.items():
        t = _norm(tag)
        c = solid_color(color)
        if len(t) < MIN_NAME_LENGTH or t in NEUTRAL_TAG_TYPES or not c:
            continue
        if n == t:
            rank = 3
        elif n.startswith(t):
            rank = 2
        elif t in words:
            rank = 1
        else:
            continue
        cand = (rank * 1000 + len(t), str(tag), c)
        if best is None or cand[0] > best[0]:
            best = cand
    return (best[1], best[2]) if best else ("", "")
