"""Widgets host of the QML tile editor (decision D7).

* QQuickWidget loads qrc:/column_editor/ColumnGrid.qml. The QML files are compiled into the EXE (qml.qrc -> qml_resources.py).
* If QML cannot be loaded the panel shows the message below; ListTable and the standard export stay available,
  tile mode is off, profile and source data are untouched.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtWidgets import QLabel, QStackedLayout, QVBoxLayout, QWidget

from . import api
from .domain.column_config import ColumnConfig
from .models.column_model import ColumnConfigModel, ColumnEditorController
from .models.column_source import ColumnSource
from .models.layout_state import TileLayoutState
from .models.widgets_source import TableControllerSource

QUICK_STYLE = "Basic"        # one small style, identical in the EXE (no native style plugins)
QML_URL = "qrc:/column_editor/ColumnGrid.qml"
QML_RESOURCES = (
    "qrc:/column_editor/ColumnGrid.qml",
    "qrc:/column_editor/ColumnCard.qml",
    "qrc:/column_editor/DropIndicator.qml",
    "qrc:/column_editor/FunctionStack.qml",
    "qrc:/column_editor/RuleInspector.qml",
    "qrc:/column_editor/GroupPanel.qml",
    "qrc:/column_editor/ChangeTypeDialog.qml",
    "qrc:/column_editor/TileBackDialog.qml",
    "qrc:/column_editor/TextPrompt.qml",
    "qrc:/column_editor/TransformDialog.qml",
    "qrc:/column_editor/StepsPanel.qml",
    "qrc:/column_editor/SplitDialog.qml",
    "qrc:/column_editor/ConditionalDialog.qml",
    "qrc:/column_editor/CheckDialog.qml",
    "qrc:/column_editor/LookupDialog.qml",
    "qrc:/column_editor/SidePane.qml",
    "qrc:/column_editor/TileStatus.qml",
)
ERROR_HEAD = ("Der Kachel-Editor ließ sich nicht laden.\n"
              "Die Tabelle und der Export bleiben verfügbar.\n\n"
              "Technische Einzelheiten:\n")


# --- flow deck: the side pane (Active tile / group dialog / Steps) can live in a dock of the host window ---------------------
_side_deck = None                      # host-provided object with attach(owner_widget, side_widget); None = the side pane stays inside the tile editor


def set_side_deck(deck) -> None:
    """The host window registers its flow deck once (see linetag_flowdeck.py). Tile editors created afterwards use it."""
    global _side_deck
    _side_deck = deck

def configure_quick_style(style: str = QUICK_STYLE) -> None:
    """Select the Qt Quick Controls style for the tile editor (unless the host already set one). Importing this module no longer
    touches the environment; the panel calls this once before the first QML file is loaded."""
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", style)


def init(quick_style: str = QUICK_STYLE) -> list[str]:
    """Call once before the first panel is created (optional; the panel does it itself when it is not called).
    Selects the Qt Quick Controls style and checks the compiled QML resources. Returns readable problems (empty = ready)."""
    configure_quick_style(quick_style)
    try:
        from . import qml_resources  # noqa: F401
    except Exception as e:  # noqa: BLE001
        return [f"The compiled QML resources cannot be loaded: {type(e).__name__}: {e}"]
    problems = [f"QML resource missing: {u}" for u in missing_resources()]
    return problems or [f"QML resource not readable: {u}" for u in unreadable_resources()]


def error_text(status: str, resource: str, detail: str = "") -> str:
    return f"{ERROR_HEAD}QQuickWidget status: {status}\nResource: {resource}" + (f"\n{detail}" if detail else "")


def missing_resources() -> list[str]:
    """QML resources that are not in the compiled resource module (checked before loading)."""
    from PySide6.QtCore import QFile
    return [u for u in QML_RESOURCES if not QFile.exists(":" + u[len("qrc:"):])]


def unreadable_resources() -> list[str]:
    """QML resources that exist but cannot be read (e.g. compressed with an algorithm the running Qt cannot decompress)."""
    from PySide6.QtCore import QFile, QIODevice
    bad = []
    for u in QML_RESOURCES:
        f = QFile(":" + u[len("qrc:"):])
        if not f.open(QIODevice.ReadOnly) or f.size() <= 0 or f.readAll().isEmpty():
            bad.append(u)
        f.close()
    return bad


def compiled_is_stale() -> bool:
    """Development runs only: a QML file next to this module is newer than the compiled resource module (or is missing from it).
    The EXE has no QML folder, so it always uses the compiled resources. Rebuild with `python build_qml_resources.py`."""
    from pathlib import Path
    here = Path(__file__).resolve().parent
    mod = here / "qml_resources.py"
    qml = here / "qml"
    if not qml.is_dir() or not mod.is_file():
        return False
    return any(f.stat().st_mtime > mod.stat().st_mtime + 1 for f in qml.glob("*.qml"))


def _source_dir_url():
    """file: URL of the QML folder next to this module (development runs only; the EXE has no such folder)."""
    from pathlib import Path
    p = Path(__file__).resolve().parent / "qml" / "ColumnGrid.qml"
    return QUrl.fromLocalFile(str(p)) if p.is_file() else None


class TileEditorPanel(QWidget):
    """Tile grid + inspector for one table.

    The data comes from a `ColumnSource` (models/column_source.py): pass `source=` from any application, or - as in
    P3D - Tag Compliance - the `TableController` of the ListTable below as `ctl` (wrapped in `TableControllerSource`).
    """
    loadFailed = Signal(str)
    stateChanged = Signal(str)          # "loading" | "ready" | "error"
    configChanged = Signal()            # types, steps, order, names or export flags changed (save the configuration now)
    exportRequested = Signal()          # ribbon "Save as Excel": the host exports the table as it is shown

    def __init__(self, ctl=None, parent=None, *, source: ColumnSource | None = None, quick_style: str = QUICK_STYLE,
                 providers: api.Providers | None = None):
        super().__init__(parent)
        if source is None and ctl is None:
            raise ValueError("TileEditorPanel needs a ColumnSource (source=...) or a TableController (ctl).")
        self.setMinimumHeight(340)
        self.state = "loading"
        self._quick_style = quick_style
        self.config = ColumnConfig()
        self.source = source if source is not None else TableControllerSource(ctl)
        self.model = ColumnConfigModel(self.source, self.config, self)
        self.controller = ColumnEditorController(self.model, self)
        self.layout_state = TileLayoutState(self)
        self.providers = providers
        if providers is not None:
            providers.install(self.controller)
        self.controller.undoChanged.connect(self.configChanged)            # every step / undo / redo
        self.model.countChanged.connect(self.configChanged)
        from .ribbon import Ribbon
        outer = QVBoxLayout(self)                                        # ribbon (Home / Transform / Add column) above the tiles
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.ribbon = Ribbon(self.controller, self)
        self.ribbon.add_area_buttons(self.layout_state, self.model)      # Not exported / Hidden / Renamed: standard ribbon buttons
        self.ribbon.hide()                                               # shown when the tiles are ready
        outer.addWidget(self.ribbon)
        self._body = QWidget()
        outer.addWidget(self._body, 1)
        self._stack = QStackedLayout(self._body)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._msg = QLabel("")
        self._msg.setWordWrap(True)
        self._msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._msg.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._msg.setProperty("role", "muted")
        self._stack.addWidget(self._msg)
        self.quick = None
        self.side_widget = None                       # QQuickWidget of SidePane.qml while it lives in the host's flow deck
        self.status_widget = None                     # QQuickWidget of TileStatus.qml (legend + area buttons) in the ribbon
        self._deck_done = False
        self._load()

    # --- side pane in the host's flow deck ---------------------------------------------------------------------------
    def showEvent(self, e) -> None:  # noqa: N802
        super().showEvent(e)
        if not self._deck_done and _side_deck is not None and self.state == "ready":
            self._attach_deck()

    def _attach_deck(self) -> None:
        """Move the side pane out of the tile editor into the host's flow deck (docked right, full height, floatable). Falls back to
        the embedded pane when the pane cannot be loaded."""
        self._deck_done = True
        side = self._create_side_widget()
        if side is None:
            return
        self.side_widget = side
        self.layout_state.sideExternal = True
        _side_deck.attach(self, side)

    def _create_side_widget(self):
        return self._create_quick_widget("SidePane.qml", "Side pane")

    def _ensure_status_widget(self) -> None:
        """The legend and the area buttons (Not exported / Hidden / Renamed) live in a small QML strip in the ribbon, at the height of the
        icon row (owner 2026-11-16). It shares the open / folded state of the areas with the grid through `tileLayout`."""
        if self.status_widget is not None:
            return
        q = self._create_quick_widget("TileStatus.qml", "Status strip")
        if q is None:
            return
        q.setFixedHeight(34)
        q.setMinimumWidth(0)
        self.status_widget = q
        self.ribbon.set_status_widget(q)

    def _create_quick_widget(self, qml_file: str, what: str):
        try:
            from PySide6.QtQuickWidgets import QQuickWidget
        except Exception:  # noqa: BLE001
            return None
        url = QUrl(QML_URL.replace("ColumnGrid.qml", qml_file))
        if missing_resources() or compiled_is_stale():
            src = _source_dir_url()
            if src is None:
                return None
            url = QUrl.fromLocalFile(str(src.toLocalFile()).replace("ColumnGrid.qml", qml_file))
        q = QQuickWidget()
        q.setResizeMode(QQuickWidget.SizeRootObjectToView)
        q.setFocusPolicy(Qt.StrongFocus)
        ctx = q.rootContext()
        ctx.setContextProperty("columnConfigModel", self.model)
        ctx.setContextProperty("columnEditorController", self.controller)
        ctx.setContextProperty("tileLayout", self.layout_state)
        q.setSource(url)
        if q.status() == QQuickWidget.Error:
            self.loadFailed.emit(f"{what} could not be loaded: " + " | ".join(er.toString() for er in q.errors()))
            q.deleteLater()
            return None
        return q

    def shutdown(self) -> None:
        """Release the QML views BEFORE the panel and its models are deleted.

        The side pane (a QQuickWidget that lives in the host's flow deck) outlives the panel for one event-loop turn and its QML still
        binds to the panel's model / controller / layout objects; evaluating those bindings after the C++ objects are gone freezes or
        crashes the application when a tile editor window is closed. Idempotent; safe on a half-built panel."""
        for q in (self.quick, self.side_widget, self.status_widget):
            if q is None:
                continue
            try:
                q.setSource(QUrl())                       # drops the QML scene, so no binding can reach a deleted model any more
                ctx = q.rootContext()
                for name in ("columnConfigModel", "columnEditorController", "tileLayout"):
                    ctx.setContextProperty(name, None)
                q.hide()
            except RuntimeError:                          # already deleted by Qt
                pass
        self.side_widget = None
        self.status_widget = None

    def reload_columns(self) -> None:
        """The table got new data: rebuild the tiles (types are detected again)."""
        self.config.columns.clear()
        self.config.nodes.clear()
        self.model.reload()

    def export_config(self) -> dict:
        """The configuration (types, steps, order, names, export flags) as a JSON-able document (api.config_to_document)."""
        return api.config_to_document(self.config)

    def load_config(self, document: dict) -> list[str]:
        """Apply a saved configuration to the current source: calculated columns, order, names, export flags.
        Returns readable notes (what could not be applied). Raises api.ConfigError for an unusable document (nothing changed)."""
        config, notes = api.config_from_document(document)
        notes += api.replay_derived(self.source, config)
        notes += api.apply_layout(self.source, config)
        self.model.restore_config(config.to_dict())
        self.model.reload()
        self.configChanged.emit()
        return notes

    def _set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            self.stateChanged.emit(state)

    def _fail(self, status: str, resource: str, detail: str = "") -> None:
        self._set_state("error")
        self.ribbon.hide()
        text = error_text(status, resource, detail)
        self._msg.setText(text)
        self._stack.setCurrentWidget(self._msg)
        self.loadFailed.emit(text)

    def _load(self) -> None:
        try:
            from PySide6.QtQuickWidgets import QQuickWidget
            from . import qml_resources  # noqa: F401  (registers the compiled qrc resources; must come before setSource)
        except Exception as e:                                           # missing module / resources in the build
            return self._fail("Error", QML_URL, f"{type(e).__name__}: {e}")
        configure_quick_style(self._quick_style)
        gone = missing_resources()
        stale = compiled_is_stale()
        if gone and _source_dir_url() is None:
            return self._fail("Error", gone[0], "Resource not found in the compiled resources. Rebuild the resources: "
                              "python build_qml_resources.py (or run qa_release.bat).")
        url = QUrl(QML_URL)
        unreadable = unreadable_resources() if not gone else []
        if gone or stale:
            url = _source_dir_url()                                     # development run with outdated resources: use the files on disk
        elif unreadable:
            src = _source_dir_url()
            if src is None:
                return self._fail("Error", unreadable[0], "Resource exists but cannot be read. Rebuild the resources: "
                                  "python build_qml_resources.py (or run qa_release.bat).")
            url = src                                                   # development run: load the QML files from disk
        q = QQuickWidget(self)
        q.setResizeMode(QQuickWidget.SizeRootObjectToView)
        q.setFocusPolicy(Qt.StrongFocus)
        ctx = q.rootContext()
        ctx.setContextProperty("columnConfigModel", self.model)
        ctx.setContextProperty("columnEditorController", self.controller)
        ctx.setContextProperty("tileLayout", self.layout_state)
        q.statusChanged.connect(lambda st, w=q: self._status(w, st))
        self.quick = q
        self._stack.addWidget(q)
        q.setSource(url)
        self._status(q, q.status())

    def _status(self, q, status) -> None:
        from PySide6.QtQuickWidgets import QQuickWidget
        if status == QQuickWidget.Ready:
            self._set_state("ready")
            self.ribbon.show()
            self._ensure_status_widget()
            self._stack.setCurrentWidget(q)
            if _side_deck is not None and not self._deck_done and self.isVisible():
                self._attach_deck()
        elif status == QQuickWidget.Error:
            self._fail("Error", QML_URL, "\n".join(e.toString() for e in q.errors()))
        # Loading / Null: wait for the next status change

    @property
    def tile_mode_enabled(self) -> bool:
        return self.state == "ready"
