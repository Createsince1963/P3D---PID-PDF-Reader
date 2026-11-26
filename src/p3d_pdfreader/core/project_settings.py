"""Projekt mit allen Einstellungen (Nutzervorgabe 2026-11-22): die Einstellungen des Tools werden in der
Projekt-Datenbank gespeichert und beim Laden des Projekts wieder hergestellt – eine Projektdatei enthaelt damit alles.

Gespeichert (``config_dir()``):

* Dateien ``FILES``: Quell-/Exportordner (``paths.json``), Tag-Muster, Importtabelle mit Kachel-Editor-Anpassung
  (``data_link.json``) und die gemerkten Tabellenansichten (``table_views.json``);
* aus ``state.json`` die Schluessel ``STATE_KEYS`` (Datenlink-Felder, Rohrleitungen, PDF-Scan-Spalten, Review-Layer,
  Review-Optionen, Projektmodus).

Ablage: Meta-Eintrag ``tool_settings`` (JSON) der Projekt-Datenbank. Ohne Qt (auch fuer den Web-Server nutzbar)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

META_KEY = "tool_settings"
FORMAT_VERSION = 1
FILES = ("paths.json", "tag_patterns.json", "data_link.json", "table_views.json")
STATE_KEYS = ("data_link_fields", "read_pipe_lines", "tags_scan_fields", "redline_review_layer", "review_options",
              "project_mode", "tag_edit")
BACKUP_DAYS = 5                       # je Tag der erste ueberschriebene Stand, die letzten Tage bleiben erhalten
STATE_FILE = "state.json"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def collect(config: Path, version: str = "") -> dict[str, Any]:
    """Aktuelle Einstellungen aus dem Konfigurationsordner einsammeln."""
    config = Path(config)
    files = {name: data for name in FILES if (data := _read_json(config / name)) is not None}
    state = _read_json(config / STATE_FILE)
    state = {k: state[k] for k in STATE_KEYS if k in state} if isinstance(state, dict) else {}
    return {"format_version": FORMAT_VERSION, "app_version": version,
            "saved": datetime.now().isoformat(timespec="seconds"), "files": files, "state": state}


def apply(config: Path, bundle: dict[str, Any]) -> list[str]:
    """Einstellungen in den Konfigurationsordner schreiben. Dateien, die im Projekt fehlen, werden entfernt
    (z. B. keine Importtabelle im Projekt -> keine Importtabelle im Tool); ``state.json`` behaelt alle Schluessel
    ausser ``STATE_KEYS``. Rueckgabe: geschriebene Dateinamen."""
    config = Path(config)
    config.mkdir(parents=True, exist_ok=True)
    files = bundle.get("files") if isinstance(bundle.get("files"), dict) else {}
    written = []
    for name in FILES:
        target = config / name
        if name in files:
            target.write_text(json.dumps(files[name], indent=2, ensure_ascii=False), encoding="utf-8")
            written.append(name)
        elif target.is_file():
            target.unlink()
    state = _read_json(config / STATE_FILE)
    state = state if isinstance(state, dict) else {}
    for k in STATE_KEYS:
        state.pop(k, None)
    state.update({k: v for k, v in (bundle.get("state") or {}).items() if k in STATE_KEYS})
    (config / STATE_FILE).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return written


def save_to_project(db, config: Path, version: str = "") -> dict[str, Any]:
    bundle = collect(config, version)
    db.set_meta(META_KEY, json.dumps(bundle, ensure_ascii=False))
    return bundle


def autosave(db, config: Path, version: str = "") -> bool:
    """Einstellungen speichern, wenn sie sich geaendert haben. Der ueberschriebene Stand bleibt je Tag einmal in der
    Tabelle ``settings_backups`` erhalten. Rueckgabe: True, wenn geschrieben wurde."""
    bundle = collect(config, version)
    stored = load_from_project(db)
    if stored is not None:
        if stored.get("files") == bundle["files"] and stored.get("state") == bundle["state"]:
            return False
        with db.con:
            db.con.execute("create table if not exists settings_backups(day text primary key, saved text, bundle text)")
            db.con.execute("insert or ignore into settings_backups(day, saved, bundle) values(?,?,?)",
                           (bundle["saved"][:10], str(stored.get("saved", "")),
                            json.dumps(stored, ensure_ascii=False)))
            db.con.execute("delete from settings_backups where day not in "
                           "(select day from settings_backups order by day desc limit ?)", (BACKUP_DAYS,))
    db.set_meta(META_KEY, json.dumps(bundle, ensure_ascii=False))
    return True


def load_from_project(db) -> dict[str, Any] | None:
    """Gespeicherte Einstellungen des Projekts (None, wenn das Projekt noch keine hat)."""
    try:
        bundle = json.loads(db.meta(META_KEY, "") or "null")
    except ValueError:
        return None
    return bundle if isinstance(bundle, dict) and bundle.get("format_version") else None
