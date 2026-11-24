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
FILTER_KEYS = ("column_filters", "value_filters")
# Tabellen, deren gemerkte Ansicht keine Filter enthaelt (1.0.39, Nutzervorgabe: beim Programmstart und nach dem
# Einlesen bzw. PDF-Wechsel keine Filter aktiv). Das Kit wendet die gemerkte Ansicht bei jedem neuen Modell erneut an -
# mit Filtern kaemen sie nach jedem Scan und PDF-Wechsel zurueck.
NO_FILTER_TABLES = ("files", "tags", "tags_link")      # tags_link = Tag-Tabelle mit Importspalten (1.0.43)


class LayoutStore(ViewSettingsStore):
    """Gemerkte Ansicht ohne Filter fuer die Schluessel ``no_filter`` (Laden und Speichern)."""

    def __init__(self, path, no_filter: tuple[str, ...] = ()):
        super().__init__(path)
        self.no_filter = set(no_filter)

    def _strip(self, key: str, settings: dict) -> dict:
        if key not in self.no_filter or not isinstance(settings, dict):
            return settings
        return {k: v for k, v in settings.items() if k not in FILTER_KEYS}

    def load(self, key: str, profile: str | None = None) -> dict:
        return self._strip(key, super().load(key, profile))

    def save(self, key: str, profile: str, settings: dict) -> None:
        super().save(key, profile, self._strip(key, settings))


def store() -> ViewSettingsStore:
    return ViewSettingsStore(config_dir() / FILE_NAME)


def layout_store() -> LayoutStore:
    """Speicher der automatisch gemerkten Ansichten (``auto|…``)."""
    return LayoutStore(config_dir() / FILE_NAME, tuple("auto|" + k for k in NO_FILTER_TABLES))


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
        return layout_store(), "auto|" + table_key(view)
    set_layout_provider(provider)
