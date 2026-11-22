"""Protected columns: the DCF database index must always stay in the list. Pure Python, no Qt.

Rule of this tool: "PnPID" is the database index of the DCF. It is shown in red bold (tile and table header) and can
never be hidden, removed or put into the Hidden area - not by the tile editor, the table menus or a saved view.
"""
from __future__ import annotations

PROTECTED_COLUMNS = ("pnpid",)
PROTECTED_NOTE = "PnPID ist der Datenbank-Index: die Spalte muss bleiben und lässt sich nicht ausblenden oder entfernen."


def is_protected(*names: str) -> bool:
    """True if any of the given names (column key / label) is a protected column (case-insensitive, trimmed)."""
    return any(str(n or "").strip().lower() in PROTECTED_COLUMNS for n in names)
