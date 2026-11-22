"""Column Tile Editor - embeddable module (origin: step 1 of P3D - Tag Compliance).

domain/  pure Python, no Qt: type system, type detection, convert / join / text / conditional / lookup / check nodes
api.py   public, Qt-free API: configuration document, apply_to (run steps without a window), Providers
models/  Qt models and controller on top of a ColumnSource (any host table)
qml/     QML files; compiled into the program through qml.qrc -> qml_resources.py (never loose files)

Public names are listed in `__all__`; the Qt-dependent ones (TileEditorPanel, init) are imported on first use, so
`import column_editor` works without Qt. Interface definition: md/XLS_EDITOR_INTERFACES.md; integration guide: README_MODULE.md.
"""
from __future__ import annotations

from .api import (CONFIG_SCHEMA, MODULE_VERSION, ApplyResult, ConfigError, Providers, apply_layout, apply_to,
                  config_from_document, config_to_document, replay_derived)
from .models.column_source import ColumnSource, ListColumnSource

__version__ = MODULE_VERSION

__all__ = ["__version__", "CONFIG_SCHEMA", "ApplyResult", "ConfigError", "Providers", "ColumnSource", "ListColumnSource",
           "apply_to", "apply_layout", "replay_derived", "config_to_document", "config_from_document", "TileEditorPanel", "init"]


def __getattr__(name: str):                       # Qt-dependent names: only loaded when used
    if name in ("TileEditorPanel", "init"):
        from . import tile_editor_host as _h
        return getattr(_h, name)
    raise AttributeError(f"module 'column_editor' has no attribute {name!r}")
