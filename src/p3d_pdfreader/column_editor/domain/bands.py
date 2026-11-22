"""Group header bands: a name over several columns (like a collective header in Excel). Qt-free.

A band is stored as {"name": str, "keys": [column keys], "color": palette index}. Where the keys are not side by side in the
table / export any more, the band is split into runs (one header cell per run, same name and colour)."""
from __future__ import annotations

# (band colour, header colour of the grouped columns) - light band above a stronger header, as in the Excel sample
PALETTE: list[tuple[str, str]] = [("92D050", "00B050"), ("9DC3E6", "5B9BD5"), ("F4B183", "ED7D31"), ("C9B3E6", "9F7FCF"),
                                  ("FFE699", "FFC000"), ("8FD3CE", "3FB1A8"), ("F2A6B3", "E0667E"), ("C9C9C9", "A5A5A5")]


def colors(index: int) -> tuple[str, str]:
    return PALETTE[int(index) % len(PALETTE)]


def runs(bands: list[dict], keys: list[str]) -> list[tuple[str, int, int, int]]:
    """[(name, first, last, colour index)] over the positions of `keys` (the columns as shown / exported), left to right."""
    pos = {k: i for i, k in enumerate(keys)}
    out: list[tuple[str, int, int, int]] = []
    for b in bands:
        idx = sorted(pos[k] for k in b.get("keys", ()) if k in pos)
        start = prev = None
        for i in idx:
            if start is None:
                start = prev = i
            elif i == prev + 1:
                prev = i
            else:
                out.append((str(b["name"]), start, prev, int(b.get("color", 0))))
                start = prev = i
        if start is not None:
            out.append((str(b["name"]), start, prev, int(b.get("color", 0))))
    return sorted(out, key=lambda r: r[1])
