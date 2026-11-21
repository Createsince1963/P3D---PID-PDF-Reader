"""Zuletzt verwendete Ordner (Muster: P3D XCHANGE 0.5.0 ``gui/last_paths.py``), in ``config/state.json``.

Fehlt der gemerkte Ordner, greift der Standardpfad; Fehler beim Lesen oder Schreiben brechen nie ab."""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from ..paths import config_dir

IMPORT, EXPORT = "last_import_dir", "last_export_dir"


def _file() -> Path:
    return config_dir() / "state.json"


def _read() -> dict:
    try:
        data = json.loads(_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def get(kind: str, fallback="") -> str:
    value = str(_read().get(kind, "") or "")
    return value if value and Path(value).exists() else str(fallback or "")


def remember(kind: str, path) -> None:
    if not path:
        return
    path = Path(path)
    folder = path if path.is_dir() else path.parent
    data = _read()
    data[kind] = str(folder.resolve())
    try:
        _file().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def get_value(key: str, default=None):
    return _read().get(key, default)


def set_value(key: str, value) -> None:
    data = _read()
    data[key] = value
    try:
        _file().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def open_dir(parent, title: str, fallback="", kind: str = IMPORT) -> str:
    folder = QFileDialog.getExistingDirectory(parent, title, get(kind, fallback))
    remember(kind, folder)
    return folder


def open_files(parent, title: str, filter_: str, fallback="", kind: str = IMPORT) -> list[str]:
    files, _ = QFileDialog.getOpenFileNames(parent, title, get(kind, fallback), filter_)
    if files:
        remember(kind, files[0])
    return files


def save_file(parent, title: str, name: str, filter_: str, fallback="", kind: str = EXPORT) -> str:
    """Speicherort fuer eine Ausgabe waehlen. Regeln (Vorgabe des Nutzers): Ausgaben haben immer einen Zeitstempel im
    Namen (wird sonst ergaenzt), ueberschreiben nie eine vorhandene Datei, und eingelesene Original-PDFs sind tabu."""
    from PySide6.QtWidgets import QMessageBox

    from ..paths import ensure_timestamp, is_protected
    path, _ = QFileDialog.getSaveFileName(parent, title, str(Path(get(kind, fallback)) / name), filter_,
                                          options=QFileDialog.DontConfirmOverwrite)
    if not path:
        return ""
    if is_protected(path):
        QMessageBox.warning(parent, title, "Die Original-PDF ist schreibgeschützt und wird nie überschrieben.\n"
                                           "Bitte einen anderen Namen oder Ordner wählen.")
        return ""
    target = ensure_timestamp(path)
    remember(kind, target)
    return str(target)
