"""Tag-Muster fuer Plant-3D-P&ID-Plots. Standardwerte hier, ueberschreibbar durch ``config/tag_patterns.json``.

Schluessel der JSON-Datei = Schluessel von ``DEFAULTS``; fehlende Schluessel behalten den Standard."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULTS: dict = {
    # Kuerzel in der Instrumentenblase (oben), Nummer darunter. Mindestens 2 Buchstaben: einzelne Buchstaben sind
    # Revisionsdreiecke (A, B), Stutzen (N) o. ae. und ergaben Fehlgriffe wie "B-011".
    "instrument_letters": r"^[A-Z]{2,5}$",
    "instrument_number": r"^\d{3,4}[A-Z]?$",
    # Woerter, die wie Kuerzel aussehen, aber keine sind
    "instrument_exclude": ["MIN", "MIN.", "LO", "LC", "FC", "FO", "NC", "NO", "M", "R", "H", "L", "HH", "LL",
                           "DN", "TC", "PN", "TO", "FROM", "SET", "AT", "SOL", "PFC", "AV", "PVAC", "AVA", "SOLW",
                           "HOLD", "COND.", "REFER", "HALF", "SHORT", "LONG", "FULL", "TYP", "TYP.", "TFCS", "TFHS", "TFCR", "TFHR", "AVHP", "ATRHP", "WWHPP", "OF"],
    "equipment": r"^\d{3}[A-Z]{3}\d{2}$",
    "valve": r"^(VH|VB|VG|VC|VN|VP|CKV|SGL|BDI|PSV|RD|XV|XZV|STR)-?\d{3,4}[A-Z]?$",
    "full_tag": r"^\d{3}-\d{2}-\d{3}-[A-Z]{1,6}-?\d{2,4}[A-Z]?$",
    "drawing_ref": r"^[A-Z0-9]+(-[A-Z0-9]+)*-PID-[A-Z0-9-]+$",
    # Datum der Revisionszeile im Schriftfeld (z. B. 03 AUG 2026)
    "revision_date": r"^\d{2} [A-Z]{3} \d{4}$",
    # Rohrleitungsnummer (Plant 3D Line Number): [Bereich] Medium[_Druckstufe] _ Klasse _ Nummer _ Nennweite["]
    # z. B. TFHR_SS01_001_1", PFC_ST10_015_1/2", TFHR_SS01_004_1 1/2", 203_17_112PFC_ST10_013_1", 151_HOS_206_1".
    # Platzhalter wie AV_TL02_XXX_2" passen bewusst nicht (noch keine Nummer vergeben).
    "pipe_line": r'^(?:\d{3}(?:_\d{2}_\d{3})?_?)?[A-Za-z]{2,8}\d{0,2}(?:_\d+(?:\.\d+)?)?_[A-Z]{2,3}\d{2}_\d{3}_'
                 r'\d+(?: \d+/\d+|/\d+)?"?$'
                 r'|^\d{3}_[A-Z]{3}_\d{3}_\d+(?: \d+/\d+|/\d+)?"?$',
}

#: Fruehere Standardwerte: steht einer davon in der Benutzerdatei, gilt der aktuelle Standard (Datei wurde nie angepasst)
OUTDATED: dict[str, tuple] = {"instrument_letters": (r"^[A-Z]{1,5}$",)}

PIPE = "Rohrleitung"
TAG_TYPES = ("Instrument", "Equipment", "Armatur", "Volltag", "Zeichnungsverweis", PIPE)


@dataclass
class Patterns:
    letters: re.Pattern
    number: re.Pattern
    exclude: frozenset
    by_type: dict[str, re.Pattern]
    revision_date: re.Pattern
    pipe_line: re.Pattern


def load(config_file: Path | None = None) -> Patterns:
    data = dict(DEFAULTS)
    if config_file and Path(config_file).is_file():
        try:
            user = json.loads(Path(config_file).read_text(encoding="utf-8"))
            if isinstance(user, dict):
                for k, v in user.items():
                    if k not in DEFAULTS or v in OUTDATED.get(k, ()):   # alter Standardwert -> neuen nehmen
                        continue
                    data[k] = v
                # Ausschlussliste: eigene Eintraege ergaenzen die Standardliste (neue Standard-Ausschluesse greifen)
                data["instrument_exclude"] = sorted(set(DEFAULTS["instrument_exclude"])
                                                    | set(user.get("instrument_exclude", []) or []))
        except (OSError, ValueError):
            pass
    return Patterns(
        letters=re.compile(data["instrument_letters"]),
        number=re.compile(data["instrument_number"]),
        exclude=frozenset(str(x).upper() for x in data["instrument_exclude"]),
        by_type={
            "Volltag": re.compile(data["full_tag"]),
            "Zeichnungsverweis": re.compile(data["drawing_ref"]),
            "Equipment": re.compile(data["equipment"]),
            "Armatur": re.compile(data["valve"]),
        },
        revision_date=re.compile(data["revision_date"]),
        pipe_line=re.compile(data["pipe_line"]),
    )


def write_defaults(config_file: Path) -> None:
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(DEFAULTS, indent=2, ensure_ascii=False), encoding="utf-8")
