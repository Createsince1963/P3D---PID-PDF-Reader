"""Gemerkte Tabellenansicht fuer alle Tabellen (Muster: P3D XCHANGE 0.5.0 ``gui/table_views.py``).

Das Kit merkt je Tabelle Spaltenreihenfolge, Breite, Ausblendung, Sortierung, Zoom und Filter, sobald ein Speicherort
gemeldet ist. Schluessel: ``layout_key()`` der umgebenden Seite, sonst ein Hash der Spaltennamen. Datei:
``config/table_views.json``. Benannte Ansichten (Speichern, Laden, Zuruecksetzen ueber ``TableAdminBar``) liegen in
derselben Datei."""
from __future__ import annotations

import hashlib

from PySide6.QtCore import Qt

from main_gui_kit.settings import ViewSettingsStore
from main_gui_kit.tables import set_layout_provider

from ..paths import config_dir

FILE_NAME = "table_views.json"


def store() -> ViewSettingsStore:
    return ViewSettingsStore(config_dir() / FILE_NAME)


def table_key(view) -> str:
    key = getattr(view, "layout_key", "")
    if key:
        return str(key)
    model = view.model()
    headers = [str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "") for c in range(model.columnCount())]
    return "table|" + hashlib.sha1("\x1f".join(headers).encode("utf-8")).hexdigest()[:12]


def install() -> None:
    def provider(view):
        if view.model() is None or view.model().columnCount() == 0:
            return None
        return store(), "auto|" + table_key(view)
    set_layout_provider(provider)
