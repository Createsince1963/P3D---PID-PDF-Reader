"""Theme tokens + QSS generation for main_gui_kit (shared Qt6 GUI kit).

Ported/renamed from plant3d_gui_kit. Palette is UNIFIED (one tone per semantic
role, used by both buttons and status/nav) per the GUI-Vorgabe v6 / Slide-17
decision (2026-07-19). LIGHT is the working reference mode; DARK values are
provisional TODOs (Folie 17 liefert keine Dark-Werte).

A3: base font 8pt, page-title 12pt, section 10pt; real hover colors (Qt QSS has
no `opacity`); status colors via dynamic property `level`; no `text-transform`.
A2: semantic button tokens (accent/secondary/process/ok/warn/err/neutral) with
per-kind QSS classes selected by the dynamic property `kind`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Palette:
    """Unified color tokens. Buttons AND status chips/nav read from the same
    role tokens (accent/ok/warn/err/...), so a role has exactly one tone."""

    # structural
    bg: str
    card: str
    hdr: str
    txt: str
    txt_muted: str
    border: str
    # semantic / button roles (unified, Slide-17 in LIGHT)
    accent: str        # Primary + active nav
    secondary: str     # Secondary buttons
    process: str       # Process buttons (Validate/Compare/Query)
    ok: str            # Success buttons + OK status
    warn: str          # Warning buttons + Warn status
    err: str           # Danger buttons + Error status
    neutral: str       # Neutral buttons (light fill, dark text)


# LIGHT = working reference (GUI-Vorgabe: Light-Modus). Values 1:1 aus Slide-17.
LIGHT = Palette(
    bg="#F5F7FB",
    card="#FFFFFF",
    hdr="#EEF3FC",
    txt="#2C3E50",
    txt_muted="#6B7C93",
    border="#E6EBF5",
    accent="#2F80ED",
    secondary="#1A2740",
    process="#0EA5A3",
    ok="#22C55E",
    warn="#F59E0B",
    err="#EF4444",
    neutral="#E7ECF4",
)

# DARK = PROVISIONAL / TODO. Struktur-Tokens sind übernommen; die Button-/Status-
# Töne sind vorläufige Ableitungen und MÜSSEN vor DARK-Freigabe final abgestimmt
# werden (siehe PhaseA-Detailplan, TODO-Dark). Solange ist LIGHT die Vorgabe.
DARK = Palette(
    bg="#12192B",
    card="#1A2236",
    hdr="#1F2A40",
    txt="#D4E1F7",
    txt_muted="#6B8AB8",
    border="#2A3A54",
    accent="#5A9BF5",     # TODO-Dark
    secondary="#24344F",  # TODO-Dark
    process="#2DC4C2",    # TODO-Dark
    ok="#34D373",         # TODO-Dark
    warn="#FBB431",       # TODO-Dark
    err="#F56565",        # TODO-Dark
    neutral="#2A3A54",    # TODO-Dark
)


def _shade(hex_color: str, factor: float) -> str:
    """Return hex_color multiplied by factor (·<1 darker, ·>1 lighter), clamped.
    Used to derive hover/pressed colors in Python (Qt QSS cannot compute them)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    def cl(v: float) -> int:
        return max(0, min(255, int(round(v))))
    return f"#{cl(r*factor):02X}{cl(g*factor):02X}{cl(b*factor):02X}"


# per-kind: (token_attr, text_color_key) — text_color_key: "white" or "txt"
# Owner rule 2026-10-28 ("nur noch grau und blaue Buttons"): every coloured
# kind renders in the accent blue; only `neutral` (and kind-less buttons) stay
# grey. The kinds themselves are kept so call sites and their meaning survive.
_BUTTON_KINDS = {
    "primary":   ("accent",    "white"),
    "secondary": ("accent",    "white"),
    "process":   ("accent",    "white"),
    "success":   ("accent",    "white"),
    "warning":   ("accent",    "white"),
    "danger":    ("accent",    "white"),
    "neutral":   ("neutral",   "txt"),
}


def build_qss(p: Palette) -> str:
    """Generate the application-wide QSS stylesheet from a Palette."""
    parts = [f"""
    QWidget {{
        background: {p.bg};
        color: {p.txt};
        font-family: "Segoe UI", sans-serif;
        font-size: 8pt;
    }}
    QLabel[role="page-title"] {{
        font-size: 12pt;
        font-weight: 700;
    }}
    QLabel[role="section"] {{
        font-size: 10pt;
        font-weight: 700;
        color: {p.txt_muted};
    }}
    QTabWidget::pane {{ border: 1px solid {p.border}; background: {p.bg}; }}
    QTabBar::tab {{
        background: {p.hdr}; color: {p.txt};
        min-width: 68px; padding: 5px 14px;
        border: 1px solid {p.border}; border-bottom: none;
    }}
    QTabBar::tab:selected {{ background: {p.card}; font-weight: 600; }}
    QGroupBox {{
        background: {p.card}; border: 1px solid {p.border};
        border-radius: 6px; margin-top: 12px; font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 10px; padding: 0 4px;
        font-size: 10pt; font-weight: 700; color: {p.txt_muted};
    }}
    QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
        background: {p.card}; border: 1px solid {p.border};
        border-radius: 4px; padding: 4px 6px;
    }}
    QStatusBar {{ background: {p.hdr}; color: {p.txt_muted}; }}
    #HeaderBanner {{ background: {p.hdr}; border-bottom: 1px solid {p.border}; }}

    /* Status text via dynamic property `level` (Qt has no CSS class attr) */
    QLabel[level="ok"]   {{ color: {p.ok}; }}
    QLabel[level="warn"] {{ color: {p.warn}; }}
    QLabel[level="err"]  {{ color: {p.err}; }}

    /* Base button; kinds below override the palette. Real hover/pressed states.
       P3D v0.15 owner feedback (2026-08-12): a QPushButton with no ``kind``
       property — every QDialogButtonBox button (Close/OK/Cancel/...) and any
       plain QPushButton not built via action_button() — previously had no
       background at all here, so it rendered flush with the dialog behind it
       and was easy to miss entirely. The base rule now always paints a
       visible, neutral-toned button; a ``kind="..."`` still overrides it
       below for buttons that opt into a semantic color. */
    QPushButton {{
        background: {p.neutral}; color: {p.txt};
        border: 1px solid {p.border}; border-radius: 4px;
        min-height: 24px; max-height: 24px;
        padding: 0 11px; font-size: 8pt; font-weight: 400;
    }}
    QPushButton:hover {{ background: {_shade(p.neutral, 0.94)}; }}
    QPushButton:pressed {{ background: {_shade(p.neutral, 0.88)}; }}
    QPushButton:disabled {{ background: {p.border}; color: {p.txt_muted}; }}
    QPushButton:default {{ border: 1px solid {p.accent}; }}
    """]

    for kind, (attr, text_key) in _BUTTON_KINDS.items():
        base = getattr(p, attr)
        fg = "#FFFFFF" if text_key == "white" else p.txt
        hover = _shade(base, 0.92)
        pressed = _shade(base, 0.84)
        border = "" if kind != "neutral" else f"border: 1px solid {p.border};"
        parts.append(f"""
    QPushButton[kind="{kind}"] {{ background: {base}; color: {fg}; {border} }}
    QPushButton[kind="{kind}"]:hover {{ background: {hover}; }}
    QPushButton[kind="{kind}"]:pressed {{ background: {pressed}; }}
        """)

    return "\n".join(parts)


class ThemeManager:
    """Runtime theme switch. Default LIGHT (working Vorgabe); DARK is provisional."""

    _PALETTES: Dict[str, Palette] = {"LIGHT": LIGHT, "DARK": DARK}

    def __init__(self, app, start: str = "LIGHT"):
        self._app = app
        self._mode = start if start in self._PALETTES else "LIGHT"
        self.apply(self._mode)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def palette(self) -> Palette:
        return self._PALETTES[self._mode]

    def apply(self, mode: str) -> None:
        if mode not in self._PALETTES:
            raise ValueError(f"Unknown theme mode: {mode!r}")
        self._mode = mode
        self._app.setStyleSheet(build_qss(self._PALETTES[mode]))

    def toggle(self) -> str:
        self.apply("DARK" if self._mode == "LIGHT" else "LIGHT")
        return self._mode
