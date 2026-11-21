r"""Pfadverwaltung (Muster: P3D XCHANGE 0.5.0 ``paths.py``). Keine festen Laufwerksbuchstaben (A: ist nur ein Subst-Laufwerk).

``home_dir()`` = ``%P3D_PDFREADER_HOME%``, sonst ``<tool_root>\data`` (als EXE ``%LOCALAPPDATA%\P3D_PDFREADER``).
``config/paths.json`` haelt die Quellordner der PDFs und den Exportordner. Alle Pfade werden ueber ``resolve()``
normalisiert (Subst-Laufwerke -> C:) und nur so verglichen.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from .constants import ENV_HOME


def tool_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def default_home() -> Path:
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA", "").strip() or str(Path.home() / "AppData" / "Local")
        return Path(base) / "P3D_PDFREADER"
    return tool_root() / "data"


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def home_dir() -> Path:
    env = os.environ.get(ENV_HOME, "").strip()
    return _ensure((Path(env) if env else default_home()).resolve())


def config_dir() -> Path:
    return _ensure(home_dir() / "config")


def logs_dir() -> Path:
    return _ensure(home_dir() / "logs")


def exports_dir() -> Path:
    custom = PathSettings.load().export_dir
    if custom and Path(custom).is_dir():
        return Path(custom).resolve()
    return _ensure(home_dir() / "exports")


def projects_dir() -> Path:
    """Ablage der Projekt-Datenbanken (Projektmodus); Projekte koennen auch an anderer Stelle liegen (Projekt oeffnen)."""
    return _ensure(home_dir() / "projects")


def patterns_file() -> Path:
    return config_dir() / "tag_patterns.json"


def same_path(a, b) -> bool:
    return str(Path(a).resolve()).casefold() == str(Path(b).resolve()).casefold()


def display_path(path) -> str:
    return str(Path(path).resolve())


def file_timestamp(moment: datetime | None = None) -> str:
    """Zeitstempel fuer Dateinamen, sekundengenau (zwei Ausgaben in derselben Minute ueberschreiben sich nicht)."""
    return (moment or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")


_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(-\d{2})?")


def has_timestamp(name: str) -> bool:
    return bool(_TIMESTAMP_RE.search(name))


def ensure_timestamp(path: str | Path) -> Path:
    """Ausgabedatei immer mit Zeitstempel: fehlt er im Namen, wird ``_<Zeitstempel>`` angehaengt. Existiert die Datei
    schon, wird ein Zaehler ergaenzt - eine vorhandene Datei wird nie ueberschrieben."""
    path = Path(path)
    if not has_timestamp(path.stem):
        path = path.with_name(f"{path.stem}_{file_timestamp()}{path.suffix}")
    candidate, n = path, 2
    while candidate.exists():
        candidate, n = path.with_name(f"{path.stem}_{n}{path.suffix}"), n + 1
    return candidate


#: Eingelesene Original-PDFs (aufgeloeste Pfade, casefold): werden nur gelesen, nie als Ausgabeziel verwendet.
_PROTECTED: set[str] = set()


def protect(paths_) -> None:
    for p in paths_:
        _PROTECTED.add(str(Path(p).resolve()).casefold())


def is_protected(path: str | Path) -> bool:
    return str(Path(path).resolve()).casefold() in _PROTECTED


class PathSettings:
    """Quellordner (Liste) und Exportordner in ``config/paths.json``. Lese-/Schreibfehler brechen nie ab."""

    FILE = "paths.json"

    def __init__(self, sources: list[str] | None = None, export_dir: str = ""):
        self.sources = sources or []
        self.export_dir = export_dir

    @classmethod
    def file(cls) -> Path:
        return config_dir() / cls.FILE

    @classmethod
    def load(cls) -> "PathSettings":
        try:
            data = json.loads(cls.file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        sources = [str(s) for s in data.get("sources", []) if str(s).strip()]
        return cls(sources, str(data.get("export_dir", "") or ""))

    def save(self) -> None:
        try:
            self.file().write_text(json.dumps({"sources": self.sources, "export_dir": self.export_dir}, indent=2,
                                              ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def add_source(self, folder) -> bool:
        folder = str(Path(folder).resolve())
        if any(same_path(folder, s) for s in self.sources):
            return False
        self.sources.append(folder)
        return True

    def remove_source(self, folder) -> None:
        self.sources = [s for s in self.sources if not same_path(s, folder)]

    def existing_sources(self) -> list[Path]:
        return [Path(s) for s in self.sources if Path(s).exists()]
