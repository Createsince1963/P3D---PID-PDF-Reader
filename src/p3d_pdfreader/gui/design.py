"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). EINZIGE Quelle fuer das GUI-Design dieses Moduls (Farben, Schriftgroessen, wiederkehrende Stile).

Regel: Neue Module/Dialoge uebernehmen dieses Design und main_gui_kit (Buttons, Tabellen, Theme) - keine eigenen Farben,
Schriften oder Stile. Vorlage ist die Excel-Mappe (Screenshots); Abweichungen nur nach Abstimmung mit dem Auftraggeber.
Die Akzentfarbe kommt aus ``appearance`` (Einstellungen > Erscheinungsbild)."""
from __future__ import annotations

TEXT = "#1B2B4A"
TEXT_MUTED = "#44546A"
TEXT_SUBTLE = "#6B7C93"
BORDER = "#DDE3EC"
BAND = "#EEF3FA"
ERROR = "#C62828"
LINK = "#1565C0"
DISABLED = "#9AA6B8"

NOTE_QSS = f"color: {TEXT_SUBTLE}; font-size: 7.5pt;"
SECTION_QSS = f"font-size: 8pt; font-weight: 600; color: {TEXT_MUTED};"
TITLE_QSS = "font-size: 13pt; font-weight: 600;"
ERROR_QSS = f"color: {ERROR};"
CARD_QSS = f"QFrame#card {{ background: white; border: 1px solid {BORDER}; }} QFrame#card QLabel {{ background: transparent; }}"
