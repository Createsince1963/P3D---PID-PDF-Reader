"""Review-Eintraege je PDF (Bearbeiten-Modus der Tag-Tabelle): Review, Aenderung, Neuer Wert, Bemerkung, WPO sowie
automatisch Datum und User der letzten Aenderung.

Die PDF selbst wird nie veraendert (nur gelesen). Ablage je PDF in ``<Datenordner>/reviews/<PDF-Name>_<Hash>/``; jedes
Speichern legt eine **neue** Datei ``<PDF-Name>_Review_<Zeitstempel>.json`` an (nichts wird ueberschrieben, Verlauf
bleibt erhalten); geladen wird die neueste. Der Hash des aufgeloesten Pfads trennt gleichnamige PDFs aus verschiedenen
Ordnern. Schluessel je Eintrag: ``"<Typ>|<Tag>"``. Ohne Qt."""
from __future__ import annotations

import getpass
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from ..paths import file_timestamp, home_dir

EDIT_FIELDS = ["Review", "Änderung", "Neuer Wert", "Bemerkung", "WPO"]
AUTO_FIELDS = ["Datum", "User"]
FIELDS = EDIT_FIELDS + AUTO_FIELDS
REVIEW_VALUES = ["", "Offen", "OK", "Korrektur erforderlich", "Klärung", "Nicht relevant"]
REVIEW_FAULTY = ("Korrektur erforderlich",)        # Viewer: rot umrandet, alle anderen Tags gruen
REVIEW_ACCEPTED = ("OK", "Nicht relevant")          # Projektmodus: Abweichung vom Reviewer angenommen -> gruen
CHANGE_VALUES = ["", "Keine", "Tag ändern", "Tag ergänzen", "Tag löschen", "Position prüfen", "Doppelten Tag auflösen"]


def status_hits(tags, store=None, checker=None) -> tuple[list, list]:
    """Alle Fundstellen nach Review-Status: (korrekt, fehlerhaft), je Tag eine Liste [(Seite, Rechteck)].
    Fehlerhaft = Review "Korrektur erforderlich"; im Projektmodus (``checker``) zusaetzlich Tags, die nicht zur
    Projektdefinition passen - ausser der Review hat sie als "OK" oder "Nicht relevant" angenommen.
    Alle anderen gefundenen Tags (auch ohne Review) gelten als korrekt."""
    ok, faulty = [], []
    for t in tags:
        (faulty if is_faulty(t, store, checker) else ok).append(list(t.hits))
    return ok, faulty


def is_faulty(tag, store=None, checker=None) -> bool:
    """Ein Tag gilt als fehlerhaft (Viewer und Redline rot) - Regel siehe ``status_hits``."""
    entries = store.entries if store is not None else {}
    review = entries.get(key(tag.type, tag.tag), {}).get("Review", "")
    return review in REVIEW_FAULTY or (checker is not None and review not in REVIEW_ACCEPTED
                                       and checker.is_fault(tag.type, tag.tag))


def current_user() -> str:
    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001 - kein Benutzername ermittelbar
        return os.environ.get("USERNAME", "")


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def key(tag_type: str, tag: str) -> str:
    return f"{tag_type}|{tag}"


class ReviewStore:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.entries: dict[str, dict[str, str]] = {}
        self.dirty = False
        self.load()

    @staticmethod
    def folder() -> Path:
        path = home_dir() / "reviews"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def _base(self) -> str:
        digest = hashlib.sha1(str(self.pdf_path.resolve()).casefold().encode("utf-8")).hexdigest()[:8]
        return f"{self.pdf_path.stem}_{digest}"

    @property
    def history_dir(self) -> Path:
        return self.folder() / self._base

    def versions(self) -> list[Path]:
        """Gespeicherte Staende, aelteste zuerst (Zeitstempel im Namen sortiert chronologisch)."""
        folder = self.history_dir
        return sorted(folder.glob(f"{self.pdf_path.stem}_Review_*.json")) if folder.is_dir() else []

    @property
    def file(self) -> Path | None:
        """Neuester gespeicherter Stand (Altbestand ohne Zeitstempel als Rueckfall)."""
        versions = self.versions()
        if versions:
            return versions[-1]
        legacy = self.folder() / f"{self._base}.json"
        return legacy if legacy.is_file() else None

    def load(self) -> None:
        try:
            data = json.loads(self.file.read_text(encoding="utf-8")) if self.file else {}
        except (OSError, ValueError):
            data = {}
        entries = data.get("entries", {}) if isinstance(data, dict) else {}
        self.entries = {k: {f: str(v.get(f, "") or "") for f in FIELDS} for k, v in entries.items() if isinstance(v, dict)}
        self.dirty = False

    def save(self) -> Path:
        payload = {"pdf": str(self.pdf_path.resolve()), "saved": timestamp(), "user": current_user(),
                   "entries": {k: v for k, v in self.entries.items() if any(v.get(f) for f in EDIT_FIELDS)}}
        folder = self.history_dir
        folder.mkdir(parents=True, exist_ok=True)
        target, n = folder / f"{self.pdf_path.stem}_Review_{file_timestamp()}.json", 2
        while target.exists():                       # gleiche Sekunde: Zaehler statt ueberschreiben
            target, n = folder / f"{self.pdf_path.stem}_Review_{file_timestamp()}_{n}.json", n + 1
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.dirty = False
        return target

    def values(self, tag_type: str, tag: str) -> list[str]:
        entry = self.entries.get(key(tag_type, tag), {})
        return [entry.get(f, "") for f in FIELDS]

    def autofill_ok(self, tag_type: str, tag: str, wpo: str = "", check_status: str = "") -> bool:
        """Autofill fuer OK-Werte: gilt fuer Review "OK" oder (leerer Review und Projekt-Pruefung "OK"). Leerer Review
        wird "OK", leeres WPO bekommt ``wpo`` (Checked aus dem Schriftfeld), Datum = heutiges Datum ohne Uhrzeit,
        User = angemeldeter Benutzer. Rueckgabe: True, wenn der Eintrag geaendert wurde."""
        entry = self.entries.get(key(tag_type, tag), {})
        review = entry.get("Review", "")
        if not (review == "OK" or (not review and check_status == "OK")):
            return False
        new = dict({f: "" for f in FIELDS}, **entry)
        new["Review"] = "OK"
        if not new.get("WPO") and wpo:
            new["WPO"] = wpo
        new["Datum"], new["User"] = datetime.now().strftime("%Y-%m-%d"), current_user()
        if new == {f: entry.get(f, "") for f in FIELDS}:
            return False
        self.entries[key(tag_type, tag)] = new
        self.dirty = True
        return True

    def set(self, tag_type: str, tag: str, field: str, value: str) -> list[str]:
        """Feld setzen; Datum und User werden automatisch nachgefuehrt. Rueckgabe: alle Felder des Eintrags."""
        entry = self.entries.setdefault(key(tag_type, tag), {f: "" for f in FIELDS})
        if entry.get(field, "") == value:
            return [entry.get(f, "") for f in FIELDS]
        entry[field] = value
        entry["Datum"], entry["User"] = timestamp(), current_user()
        self.dirty = True
        return [entry.get(f, "") for f in FIELDS]
