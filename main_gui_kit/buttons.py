"""Semantic button system for main_gui_kit (A2).

One helper produces every button; the visual style comes from QSS driven by the
dynamic property `kind` (see theme.build_qss). Rules from the GUI-Vorgabe:
labels are NEVER bold, fixed 24 px desktop height, equal widths within a
workflow group, one primary action per view.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class ButtonKind(Enum):
    """Semantic button roles. `.value` matches the QSS `kind` property."""

    PRIMARY = "primary"       # Import / Export / Run  — one per workflow stage
    SECONDARY = "secondary"   # Select / Scan / Load / Connect
    PROCESS = "process"       # Validate / Compare / Query
    SUCCESS = "success"       # Build / Generate / Apply
    WARNING = "warning"       # Review (only on real review need)
    DANGER = "danger"         # Cancel / Delete (destructive only)
    NEUTRAL = "neutral"       # Reset / Save Config


# Desktop metrics (GUI-Vorgabe). Touch density is handled later via DensityMode.
BUTTON_HEIGHT = 24
BUTTON_MIN_WIDTH = 88
BUTTON_GROUP_WIDTH = 100  # equal default width inside a workflow group


def action_button(text: str,
                  kind: ButtonKind = ButtonKind.SECONDARY,
                  icon: str = "") -> QPushButton:
    """Create a styled button. `kind` selects the QSS class; label stays
    regular weight; height is fixed to the desktop standard."""
    label = f"{icon} {text}".strip() if icon else text
    btn = QPushButton(label)
    btn.setProperty("kind", kind.value)
    btn.setFixedHeight(BUTTON_HEIGHT)
    btn.setMinimumWidth(BUTTON_MIN_WIDTH)
    btn.setCursor(Qt.PointingHandCursor)
    f = btn.font()
    f.setPointSizeF(8)
    f.setBold(False)
    btn.setFont(f)
    return btn


def equalize_widths(buttons: Iterable[QPushButton],
                    width: Optional[int] = None) -> None:
    """Give every button in a workflow group the same fixed width. Without an
    explicit width, use the widest sizeHint (min. BUTTON_GROUP_WIDTH)."""
    buttons = list(buttons)
    if not buttons:
        return
    if width is None:
        width = max([BUTTON_GROUP_WIDTH] + [b.sizeHint().width() for b in buttons])
    for b in buttons:
        b.setFixedWidth(width)
