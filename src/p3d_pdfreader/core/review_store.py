"""Review-Eintraege je PDF (Bearbeiten-Modus der Tag-Tabelle): Review, Aenderung, Neuer Wert, Bemerkung, WPO sowie
automatisch Datum und User der letzten Aenderung.

Die PDF selbst wird nie veraendert (nur gelesen). Mit gewaehltem Projekt liegen die Staende in dessen Datenbank
(``project_store``, mit Verlauf); vorhandene JSON-Staende werden beim ersten Laden uebernommen, die Dateien bleiben.
Ohne Projekt: Ablage je PDF in ``<Datenordner>/reviews/<PDF-Name>_<Hash>/``; jedes
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

from . import type_filter
from ..paths import file_timestamp, home_dir
from . import project_store

EDIT_FIELDS = ["Review", "Änderung", "Neuer Wert", "Bemerkung", "WPO"]
AUTO_FIELDS = ["Datum", "User"]
FIELDS = EDIT_FIELDS + AUTO_FIELDS
REVIEW_VALUES = ["", "Offen", "OK", "Korrektur erforderlich", "Klärung", "Nicht relevant", "No Tag"]
REVIEW_UNMARKED = ("No Tag",)                       # kein Tag (Fehlerkennung): keine Markierung in PDF, Viewer, Redline
REVIEW_FAULTY = ("Korrektur erforderlich",)        # Viewer: rot umrandet, alle anderen Tags gruen
REVIEW_ACCEPTED = ("OK", "Nicht relevant")          # Projektmodus: Abweichung vom Reviewer angenommen -> gruen
CHANGE_VALUES = ["", "Keine", "Tag ändern", "Tag ergänzen", "Tag löschen", "Position prüfen", "Doppelten Tag auflösen"]


def status_hits(tags, store=None, checker=None) -> tuple[list, list]:
    """Alle Fundstellen nach Review-Status: (korrekt, fehlerhaft), je Tag eine Liste [(Seite, Rechteck)].
    Fehlerhaft = Review "Korrektur erforderlich"; im Projektmodus (``checker``) zusaetzlich Tags, die nicht zur
    Projektdefinition passen - ausser der Review hat sie als "OK" oder "Nicht relevant" angenommen.
    Alle anderen gefundenen Tags (auch ohne Review) gelten als korrekt; Review "No Tag" wird gar nicht umrandet."""
    ok, faulty = [], []
    for t in marked_tags(tags, store):
        (faulty if is_faulty(t, store, checker) else ok).append(list(t.hits))
    return ok, faulty


def marked_tags(tags, store=None) -> list:
    """Tags, die in der PDF gekennzeichnet werden: alle ausser Review "No Tag"."""
    entries = store.entries if store is not None else {}
    return [t for t in tags if entries.get(key(t.type, t.tag), {}).get("Review", "") not in REVIEW_UNMARKED]


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


_LATEST: dict[Path, tuple] = {}      # Ordner -> (Zeitstempel des Ordners, neuester Stand): spart glob je PDF
_PARSED: dict[Path, tuple] = {}      # Datei -> (mtime_ns, Groesse, Inhalt): spart Lesen und Parsen je Aktualisierung


class ReviewStore:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.db = project_store.active()              # Projekt beim Laden: dorthin wird auch gespeichert
        self._base_name: str | None = None
        self.entries: dict[str, dict[str, str]] = {}
        self.removed: set[str] = set()                # aus dem Review genommene Tags (Schluessel, 1.0.43)
        self.dirty = False
        self.load()

    @staticmethod
    def folder() -> Path:
        path = home_dir() / "reviews"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def _base(self) -> str:
        if self._base_name is None:                  # resolve() + sha1 nur einmal je Instanz
            digest = hashlib.sha1(str(self.pdf_path.resolve()).casefold().encode("utf-8")).hexdigest()[:8]
            self._base_name = f"{self.pdf_path.stem}_{digest}"
        return self._base_name

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
        folder = self.history_dir
        try:
            stamp = folder.stat().st_mtime_ns            # aendert sich, sobald eine neue Version dazukommt
        except OSError:
            stamp = None
        hit = _LATEST.get(folder)
        if hit is not None and hit[0] == stamp:
            latest = hit[1]
        else:
            versions = self.versions()
            latest = versions[-1] if versions else None
            _LATEST[folder] = (stamp, latest)
        if latest is not None:
            return latest
        legacy = self.folder() / f"{self._base}.json"
        return legacy if legacy.is_file() else None

    def _load_data(self) -> dict:
        if self.db is None:
            return self._read(self.file)
        key_ = project_store.path_key(self.pdf_path)
        data = project_store.load_review(self.db, key_)
        if data is None:
            data = self._read(self.file)              # Stand von vor der Datenbank ins Projekt uebernehmen
            if data:
                project_store.save_review(self.db, key_, data)
        return data

    def load(self) -> None:
        data = self._load_data()
        entries = data.get("entries", {}) if isinstance(data, dict) else {}
        self.entries = {k: {f: str(v.get(f, "") or "") for f in FIELDS} for k, v in entries.items() if isinstance(v, dict)}
        removed = data.get("removed", []) if isinstance(data, dict) else []
        self.removed = {str(k) for k in removed} if isinstance(removed, list) else set()
        self.dirty = False

    @staticmethod
    def _read(path: Path | None) -> dict:
        """Inhalt einer Review-Datei; unveraenderte Dateien (Zeit, Groesse) kommen aus dem Zwischenspeicher. Der Inhalt
        wird nur gelesen (``load`` baut daraus neue Eintraege), nie veraendert."""
        if path is None:
            return {}
        try:
            st = path.stat()
            hit = _PARSED.get(path)
            if hit is not None and hit[:2] == (st.st_mtime_ns, st.st_size):
                return hit[2]
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        _PARSED[path] = (st.st_mtime_ns, st.st_size, data)
        return data

    def save(self) -> Path:
        payload = {"pdf": str(self.pdf_path.resolve()), "saved": timestamp(), "user": current_user(),
                   "entries": {k: v for k, v in self.entries.items() if any(v.get(f) for f in EDIT_FIELDS)},
                   "removed": sorted(self.removed)}
        if self.db is not None:
            if not self.db.is_file():
                raise OSError(f"Projekt-Datenbank nicht gefunden: {self.db}")
            project_store.save_review(self.db, project_store.path_key(self.pdf_path), payload)
            self.dirty = False
            return self.db
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

    # --- Tags aus dem Review nehmen (1.0.43, Nutzervorgabe) ---------------------------------------------------------
    # Ein Tag, den das Tool zwar gefunden hat, der aber nicht in den Review gehoert (z. B. Fehlerkennung), wird hier
    # vermerkt: er fehlt dann in Tag-Tabelle, Viewer-Rahmen, Redline, Review-Excel, Export und Vorschau. Wiederherstellen
    # jederzeit; wirksam nach dem Speichern wie jeder Review-Eintrag. Die PDF bleibt unveraendert.
    def is_removed(self, tag_type: str, tag: str) -> bool:
        return key(tag_type, tag) in self.removed

    def set_removed(self, pairs, removed: bool = True) -> int:
        """``pairs`` = [(Typ, Tag), …] aus dem Review nehmen bzw. wiederherstellen. Rueckgabe: Anzahl geaendert."""
        changed = 0
        for tag_type, tag in pairs:
            k = key(tag_type, tag)
            if (k in self.removed) != removed:
                (self.removed.add if removed else self.removed.discard)(k)
                changed += 1
        self.dirty = self.dirty or bool(changed)
        return changed

    def visible(self, tags) -> list:
        """Tags ohne die aus dem Review genommenen und ohne abgewaehlte Prueftypen (``Tag``-Objekte)."""
        tags = type_filter.apply(tags)
        return [t for t in tags if key(t.type, t.tag) not in self.removed] if self.removed else tags


def visible_tags(result) -> list:
    """Tags einer PDF ohne die aus dem Review genommenen (gespeicherter Stand)."""
    try:
        return ReviewStore(result.path).visible(result.tags)
    except OSError:
        return type_filter.apply(result.tags)
