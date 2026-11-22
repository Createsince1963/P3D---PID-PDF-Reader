# column_editor - using the tile editor in another application

Layers (outer ones depend on inner ones only):

| Layer | Needs | Contents |
|---|---|---|
| `domain/` | Python standard library (`openpyxl` only to read an Excel file in `lookup.py`) | types, type detection, convert / join / text / conditional / lookup / check / derive nodes, tag colours |
| `models/` | PySide6 (QtCore) | `ColumnConfigModel`, `ColumnEditorController`, `ColumnSource` protocol, undo stack |
| `tile_editor_host.py`, `ribbon.py` | PySide6 Widgets, QtQuick, QtQuickWidgets, Quick Controls 2 | `TileEditorPanel` (ribbon + QML tile grid) |

## Embedding

```python
from column_editor.models.column_source import ListColumnSource      # or your own ColumnSource
from column_editor.tile_editor_host import TileEditorPanel

source = ListColumnSource([("a", "Building"), ("b", "System")], rows=[["203", "04"], ["204", "05"]])
panel = TileEditorPanel(source=source)       # QWidget; panel.state == "ready" when the QML loaded
```

* **Data:** implement `ColumnSource` (`models/column_source.py`): column keys in display order, labels, hidden flag, move,
  sample values, all values of a column, add / update / remove calculated columns, rename, export exclusion and a change callback.
  `TableControllerSource` (Qt table of P3D - Tag Compliance) and `ListColumnSource` (in memory) are the two examples.
* **Saved views:** `profile_bridge.export_into / import_from` work with any object that has `.columns` (items with `key`,
  `source_type`, `detected_type`, `output_type`, `type_detection`, `export`, `short_name`) and `.nodes` (list of dicts).
* **Colours / code lists:** not read by the module - pass them in (`domain/tag_colors`, `CheckParameters.values`).
* **Excel lists (Add columns from another list):** the default reader is the built-in one (or the one of P3D - Tag Compliance when
  `linetag_sources` is importable). Plug in your own with `column_editor.domain.lookup.set_sheet_reader(fn)`.
* **Qt Quick style:** `TileEditorPanel(..., quick_style="Basic")`; importing the module does not touch the environment.
* **QML resources:** the QML files are compiled into `qml_resources.py`. Rebuild after changing a `.qml` file:
  `python -m column_editor.build_resources` (uses the PySide6 `rcc`, `--no-compress`). A packaged EXE must not exclude
  QtQml / QtQuick / QtQuickWidgets / QtQuickControls2.
* **Status:** the reuse changes (2026-10-23) are checked by `tests/test_module_reuse.py` (standard library only). Embedding with a
  non-Tag-Compliance `ColumnSource` has not been run in a GUI yet.

## Public API (2026-10-23, module version 0.1.0; details in `md/XLS_EDITOR_INTERFACES.md` of the workspace)

```python
import column_editor as ce                       # works without Qt
doc = panel.export_config()                      # JSON-able dict, "schema": 3  (store it in your own project file)
notes = panel.load_config(doc)                   # put a saved view back onto the current source; raises ce.ConfigError if unusable
result = ce.apply_to(headers, rows, doc)         # run the saved steps without any window -> ApplyResult(headers, rows, notes)
panel = ce.TileEditorPanel(source=src, providers=ce.Providers(tag_colors=..., code_lists=..., sheet_reader=...))
problems = ce.init()                             # optional check before the first panel: Quick style + compiled QML resources
```
