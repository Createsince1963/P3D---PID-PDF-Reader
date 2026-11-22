"""Tabellenprofil als Datei (Nutzervorgabe 2026-11-22): die Ansicht ALLER Tabellen des Tools in einer JSON-Datei
speichern und wieder laden, z. B. zum Weitergeben an Kollegen oder fuer ein anderes Projekt.

Inhalt je Tabelle wie die gemerkte Ansicht des Kits (``capture_table_layout``): Spaltenreihenfolge, Breiten,
ausgeblendete Spalten, Sortierung, Zoom, Filter. Grundlage sind die automatisch gemerkten Ansichten in
``config/table_views.json`` (Schluessel ``auto|…``, siehe ``table_views``); offene Tabellen werden mit ihrem
aktuellen Stand uebernommen. Beim Laden wird jede Ansicht in ``table_views.json`` geschrieben und auf die offenen
Tabellen sofort angewendet; Tabellen, die gerade nicht offen sind, bekommen sie beim naechsten Oeffnen.

Benannte Ansichten je Tabelle (``TableAdminBar``) bleiben davon unberuehrt."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from PySide6.QtWidgets import QApplication, QMessageBox, QTableView, QTreeView

from main_gui_kit.tables import apply_table_layout, capture_table_layout

from . import last_paths, table_views

FORMAT = "p3d-pdfreader-table-profile"
FORMAT_VERSION = 1
AUTO = "auto|"
PROFILE = "Default"                     # Profil, das die automatische Merk-Funktion des Kits verwendet
PROFILE_DIR = "last_table_profile_dir"  # config/state.json: zuletzt gewaehlter Ordner
FILTER = "Tabellenprofil (*.json)"


# --- reine Datenlogik (ohne Fenster, testbar) ------------------------------------------------------------------
def stored_layouts(payload: dict[str, Any]) -> dict[str, dict]:
    """Aktive Ansicht je ``auto|``-Schluessel aus dem Inhalt von ``table_views.json``."""
    out: dict[str, dict] = {}
    for key, entry in payload.items():
        if not str(key).startswith(AUTO) or not isinstance(entry, dict):
            continue
        profiles = entry.get("profiles") if isinstance(entry.get("profiles"), dict) else {PROFILE: entry}
        layout = profiles.get(str(entry.get("last_profile", PROFILE))) or profiles.get(PROFILE)
        if isinstance(layout, dict) and layout:
            out[str(key)] = layout
    return out


def build_profile(stored: dict[str, dict], live: dict[str, dict], version: str = "") -> dict[str, Any]:
    tables = dict(stored)
    tables.update({k: v for k, v in live.items() if v})
    return {"format": FORMAT, "format_version": FORMAT_VERSION, "app_version": version,
            "saved": datetime.now().isoformat(timespec="seconds"), "tables": dict(sorted(tables.items()))}


def parse_profile(payload: Any) -> dict[str, dict]:
    """Tabellen-Ansichten aus einer Profildatei; ``ValueError`` bei fremdem Inhalt."""
    if not isinstance(payload, dict) or payload.get("format") != FORMAT:
        raise ValueError("Die Datei ist kein Tabellenprofil des P3D PDF Readers.")
    tables = payload.get("tables")
    if not isinstance(tables, dict):
        raise ValueError("Das Tabellenprofil enthält keine Tabellen.")
    return {str(k): v for k, v in tables.items() if str(k).startswith(AUTO) and isinstance(v, dict) and v}


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


# --- offene Tabellen -------------------------------------------------------------------------------------------
def live_views() -> Iterable[tuple[str, QTableView | QTreeView]]:
    """Alle offenen Tabellen mit automatisch gemerkter Ansicht (Schluessel des Kits)."""
    seen: set[int] = set()
    for top in QApplication.topLevelWidgets():
        for view in [top, *top.findChildren(QTableView), *top.findChildren(QTreeView)]:
            target = getattr(view, "_shared_layout_store", None)
            if not isinstance(view, (QTableView, QTreeView)) or target is None or id(view) in seen:
                continue
            seen.add(id(view))
            if view.model() is not None and view.model().columnCount():
                yield str(target[1]), view


def save_profile(path: Path, version: str = "") -> int:
    store = table_views.store()
    live = {key: capture_table_layout(view) for key, view in live_views()}
    profile = build_profile(stored_layouts(read_json(store.path)), live, version)
    Path(path).write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(profile["tables"])


def load_profile(path: Path) -> tuple[int, int]:
    """Profil laden: (Anzahl Tabellen im Profil, davon sofort angewendet)."""
    tables = parse_profile(read_json(path) or None)
    store = table_views.store()
    for key, layout in tables.items():
        store.save(key, PROFILE, layout)
    applied = 0
    for key, view in live_views():
        layout = tables.get(key)
        if layout:
            apply_table_layout(view, layout)
            view._shared_user_widths = {str(n) for n in layout.get("column_widths", {})}
            applied += 1
    return len(tables), applied


# --- Bedienung -------------------------------------------------------------------------------------------------
def save_dialog(parent, version: str = "") -> None:
    path = last_paths.save_file(parent, "Tabellenprofil speichern", "Tabellenprofil.json", FILTER, kind=PROFILE_DIR)
    if not path:
        return
    try:
        count = save_profile(Path(path), version)
    except OSError as exc:
        QMessageBox.warning(parent, "Tabellenprofil", f"Das Profil ließ sich nicht speichern:\n{exc}")
        return
    QMessageBox.information(parent, "Tabellenprofil", f"Ansicht von {count} Tabellen gespeichert:\n{path}")


def load_dialog(parent) -> None:
    files = last_paths.open_files(parent, "Tabellenprofil laden", FILTER, kind=PROFILE_DIR)
    if not files:
        return
    try:
        count, applied = load_profile(Path(files[0]))
    except (OSError, ValueError) as exc:
        QMessageBox.warning(parent, "Tabellenprofil", str(exc))
        return
    QMessageBox.information(parent, "Tabellenprofil",
                            f"Ansicht von {count} Tabellen geladen, {applied} davon sofort angewendet.\n"
                            "Die übrigen Tabellen zeigen sie beim nächsten Öffnen.")
