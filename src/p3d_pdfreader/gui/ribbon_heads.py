"""Gruppenueberschriften im Menueband: dunkelblaue Kopfleiste ueber jeder Gruppe (Nutzervorgabe 2026-11-21).

``ribbon.py`` (Kopie aus P3D XCHANGE) bleibt unveraendert: Der vorhandene Gruppentitel wird hier von unten nach oben
verschoben und als Kopfleiste gestaltet. Farbe = Tabellenkopf (``appearance.header_color``, folgt der Akzentfarbe)."""
from __future__ import annotations

from .ribbon import Ribbon, RibbonGroup


def _qss() -> str:
    from . import appearance
    return (f"#RibbonGroupHead {{ background: {appearance.header_color()}; color: white; font-weight: 600;"
            f" font-size: 8pt; padding: 2px 6px; border-radius: 2px; }}")


def apply_group_heads(ribbon: Ribbon) -> None:
    """Jede Gruppe bekommt ihren Titel als Kopfleiste oben (Text unveraendert, z. B. „1  Einlesen“)."""
    for group in ribbon.findChildren(RibbonGroup):
        title = group.title
        layout = group.layout()
        if layout.indexOf(title) != 0:
            layout.removeWidget(title)
            layout.insertWidget(0, title)
            layout.insertSpacing(1, 3)
        title.setObjectName("RibbonGroupHead")
        title.setStyleSheet(_qss())
        layout.setContentsMargins(4, 2, 4, 4)
