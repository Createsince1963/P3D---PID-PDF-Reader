"""Ribbon (menu band) above the tile editor: Home / Transform / Add column.
Every button does what the matching entry of the tile menu does; functions with a dialog ask the tile editor (QML) to open it next
to the selected tile (`controller.requestFunction`). Buttons that need a column are greyed (with a tooltip) while no tile is selected.
Plain Qt widgets; no data logic here - everything goes through the ColumnEditorController (undo / redo, steps, profile)."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QProgressBar, QStackedWidget, QTabBar, QToolButton, QVBoxLayout, QWidget

from .ribbon_icons import ribbon_icon

BAR_FACTORY: Callable[[], QProgressBar] | None = None     # the host sets its progress bar class here (this package never imports the host)

KIND = {"Undo": "undo", "Redo": "redo", "Hide / show": "hide", "Export yes / no": "export", "Group tiles": "group", "Select group": "select_group", "Ungroup": "ungroup", "Reset column": "reset", "Duplicate column": "duplicate", "Save as Excel": "save_excel",
        "Trim": "trim", "Clean": "clean", "UPPER": "upper", "lower": "lower", "Capitalise": "capitalise", "Replace ...": "replace",
        "Add text ...": "add_text", "Pipe size ...": "pipe_size", "Extract": "extract", "Split ...": "split", "Fill down": "fill_down",
        "Fill up": "fill_up", "Fill empty ...": "fill_value", "Yes / No column ...": "yes_no", "If ... then ...": "conditional", "Check list ...": "check", "From list ...": "lookup",
        "Add columns ...": "add_columns", "Index column ...": "index",
        "Not exported": "area_not_exported", "Hidden": "area_hidden", "Renamed": "area_renamed"}
AREAS = ((1, "Not exported", "notExportedCount"), (2, "Hidden", "hiddenCount"), (3, "Renamed", "renamedCount"))   # side areas of the tile grid

NEEDS_COLUMN = "Select a column tile first.  "
NEEDS_GROUP = "Select a tile that is in a group first.  "
NEEDS_MULTI = "Select two or more tiles first (Ctrl+click).  "


class Ribbon(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.ctl = controller
        self._items: list[tuple[QToolButton, str, str]] = []           # (button, tooltip, needs: "" | "column" | "multi")
        self._host: list[tuple[QToolButton, object, Callable[[], bool]]] = []   # (button, source button of the host, offered?)
        self._host_sep: QWidget | None = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 2)
        lay.setSpacing(0)
        self.tabs = QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setDrawBase(True)
        self.tabs.setAccessibleName("Ribbon tabs")
        self.stack = QStackedWidget()
        for title, items in (("Home", self._home()), ("Transform", self._transform()), ("Add column", self._add())):
            self.tabs.addTab(title)
            self.stack.addWidget(self._page(items))
        self.tabs.currentChanged.connect(self.stack.setCurrentIndex)
        self.bar = BAR_FACTORY() if BAR_FACTORY is not None else QProgressBar()      # Excel export progress: right of "Save as Excel" on the Home tab
        self.bar.setRange(0, 1000)
        self.bar.setFixedHeight(3)                                    # thin line (owner 2026-11-13)
        self.bar.setAccessibleName("Excel export progress")
        self.bar.hide()
        self._home_page = self.stack.widget(0)
        home = self._home_page.layout()
        home.insertWidget(home.count() - 1, self.bar, 1)              # in front of the closing stretch: takes the free space
        self.hint = QLabel()                                          # same place: what to do next (Excel split: click a tile)
        self.hint.setStyleSheet("color: #1e7a3c; font-weight: bold;")
        self.hint.hide()
        home.insertWidget(home.count() - 1, self.hint, 1)
        self._bar_timer = QTimer(self)
        self._bar_timer.setSingleShot(True)
        self._bar_timer.timeout.connect(self.bar.hide)
        lay.addWidget(self.tabs)
        self._row = QHBoxLayout()                                     # icon row: the pages + (right) the status strip of the tile editor
        self._row.setContentsMargins(0, 0, 0, 0)
        self._row.setSpacing(0)
        self._row.addWidget(self.stack, 1)
        lay.addLayout(self._row)
        self.setMaximumHeight(100)
        controller.selectedChanged.connect(self.refresh)
        controller.undoChanged.connect(self.refresh)
        self.refresh()

    # --- what is on the tabs -------------------------------------------------------------------------------------------
    def _one(self, op: str) -> Callable[[], None]:
        def run() -> None:
            err = self.ctl.run_one_click(op, self.ctl.selectedRow)
            if err:
                self.ctl.message.emit(err)
        return run

    def _dlg(self, name: str) -> Callable[[], None]:
        return lambda: self.ctl.requestFunction(name, self.ctl.selectedRow)

    def _home(self) -> list:
        c = self.ctl
        return [("Undo", "Undo the last change (Ctrl+Z)", c.undo, ""), ("Redo", "Redo (Ctrl+Y)", c.redo, ""), None,
                ("Hide / show", "Hide the selected tile(s) in the preview, or show them again", lambda: c.toggleHidden(c.selectedRow), "column"),
                ("Export yes / no", "Leave the selected column(s) out of the export, or put them back",
                 lambda: c.toggleExport(c.selectedRow), "column"),
                ("Group tiles", "Group the selected tiles (name, block, optional header in table and Excel, optional joined column) (Ctrl+G)", c.startGroup, "multi"),
                ("Select group", "Select all tiles of the group of the active tile", lambda: c.selectGroup(c.selectedRow), "group"),
                ("Ungroup", "Dissolve the group of the selected tile(s): the tiles stay, block and header band are gone", lambda: c.ungroup(c.selectedRow), "group"),
                ("Reset column", "Back to the original settings of the selected column", lambda: c.resetColumn(c.selectedRow), "column"),
                ("Duplicate column", "Make a copy of the selected column (to split it or change the copy, the original stays)", self._one("duplicate"), "column"),
                ("Add columns ...", "Create new blank columns (tiles) at once: type or paste the names from Excel", self._add_columns, ""), None,
                ("Save as Excel", "Save the table as it was created (columns, order, labels, calculated and imported columns, values) as an Excel file",
                 self._save_excel, "")]

    def _transform(self) -> list:
        extract = [("First characters ...", "extract_first"), ("Last characters ...", "extract_last"),
                   ("Text before a separator ...", "extract_before"), ("Text after a separator ...", "extract_after"),
                   ("Text between two separators ...", "extract_between")]
        return [("Trim", "Remove extra spaces", self._one("trim"), "column"),
                ("Clean", "Remove hidden characters", self._one("clean"), "column"),
                ("UPPER", "UPPER CASE", self._one("upper"), "column"),
                ("lower", "lower case", self._one("lower"), "column"),
                ("Capitalise", "Capitalise Each Word", self._one("capitalise"), "column"), None,
                ("Replace ...", "Replace values", self._dlg("replace"), "column"),
                ("Add text ...", "Add text before / after, or fill with zeros", self._dlg("format"), "column"),
                ("Pipe size ...", "Normalise pipe size (inch / DN)", self._dlg("normalise_size"), "column"),
                ("Extract", "Take part of the text", [(t, self._dlg(n)) for t, n in extract], "column"),
                ("Split ...", "Split the column into several columns", self._dlg("split"), "column"), None,
                ("Fill down", "Copy the value down into empty cells", self._one("fill_down"), "column"),
                ("Fill up", "Copy the value up into empty cells", self._one("fill_up"), "column"),
                ("Fill empty ...", "Fill the empty cells of the selected column(s) or of the whole group with a value you type", self._fill_empty, "column")]

    def _add(self) -> list:
        return [("If ... then ...", "New column from rules: if a column equals / contains ... then this value", self._dlg("conditional"), "column"),
                ("Check list ...", "Check a column against a code list (OK / NOT IN LIST)", self._dlg("check"), "column"),
                ("From list ...", "Bring columns over from another Excel / CSV list by a matching column", self._dlg("lookup"), "column"),
                None,
                ("Yes / No column ...", "New logical column (Yes / No): you choose the two words and the value every row starts with; placed behind the selected tile (or at the end)", self._add_yes_no, ""),
                ("Index column ...", "Insert a running number (Pos.) as the FIRST column: you choose the start number (default 1), the step (default 1) and the digits with leading zeros (automatic: 1000 rows -> 0001, 10 rows -> 01)", self._add_index, ""),
                ("Add columns ...", "Create several blank columns at once (type or paste names from Excel)", self._add_columns, "")]

    def _save_excel(self) -> None:
        sig = getattr(self.parent(), "exportRequested", None)          # the host (preview) opens its "Export view to Excel" dialog
        if sig is not None:
            sig.emit()

    def set_status_widget(self, w) -> None:
        """Legend + area buttons of the tile editor (a small QML strip): right of the icons, at the height of the icon row, on every tab."""
        self._row.insertWidget(1, w, 0, Qt.AlignVCenter)             # behind the icons, in front of the area buttons

    def add_area_buttons(self, layout_state, model) -> None:
        """Open / fold the three side areas (Not exported / Hidden / Renamed): standard ribbon buttons (icon, text with the count,
        checked = open), at the right end of the icon row on every tab. State: `layout_state` (openAreas, toggleArea, at most two
        open at a time); counts: `model`."""
        box = QWidget()
        box.setObjectName("areaButtons")
        h = QHBoxLayout(box)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(2)
        self.area_buttons: dict[int, QToolButton] = {}
        for i, title, _prop in AREAS:
            b = self._button(title, ribbon_icon(KIND[title]))
            b.setCheckable(True)
            b.setObjectName(f"areaButton{i}")
            b.clicked.connect(lambda _=False, i=i: layout_state.toggleArea(i))
            self.area_buttons[i] = b
            h.addWidget(b)
        self._row.addWidget(box, 0, Qt.AlignVCenter)

        def sync() -> None:
            opened = [int(x) for x in (layout_state.openAreas or [])]
            for i, title, prop in AREAS:
                b = self.area_buttons[i]
                text = f"{title} ({int(model.property(prop) or 0)})"
                b.setText(text)
                b.setAccessibleName(title)
                b.setMinimumWidth(max(60, b.fontMetrics().horizontalAdvance(text) + 16))
                b.setChecked(i in opened)
                b.setToolTip(("Bereich einklappen: '" if i in opened else "Bereich aufklappen: '") + title
                             + "' (höchstens zwei Bereiche zugleich; ein dritter klappt den zuerst geöffneten ein)")
        layout_state.areasChanged.connect(sync)
        model.statsChanged.connect(sync)
        sync()

    def add_host_actions(self, items: list) -> None:
        """Functions of the host on the Home tab, right of "Save as Excel", one row, same size as the other icons.
        items = [(text, icon, source, offered)]: `source` is the host's own (hidden) button - a click here clicks it, enabled state and
        tooltip follow it (`sync_host_actions`); `offered()` False hides the button (the view does not have the function)."""
        home = self._home_page.layout()
        at = home.indexOf(self.bar)
        if self._host_sep is None:
            self._host_sep = QWidget()
            self._host_sep.setFixedWidth(10)
            home.insertWidget(at, self._host_sep)
            at += 1
        for text, icon, src, offered in items:
            b = self._button(text, icon)
            b.clicked.connect(lambda _=False, s=src: s.click() if s.isEnabled() else None)
            self._host.append((b, src, offered))
            home.insertWidget(at, b)
            at += 1
        self.sync_host_actions()

    def add_host_tab(self, title: str, widgets: list, items: list) -> None:
        """An own tab of the host in front of "Home" (e.g. the view profile): one row - first the host's widgets (selector, check box),
        then icon buttons like on the other tabs. `items` as in `add_host_actions`. "Home" stays the tab that is shown."""
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(2)
        for x in widgets:
            h.addWidget(x, 0, Qt.AlignVCenter)
            h.addSpacing(8)
        for text, icon, src, offered in items:
            b = self._button(text, icon)
            b.clicked.connect(lambda _=False, s=src: s.click() if s.isEnabled() else None)
            self._host.append((b, src, offered))
            h.addWidget(b)
        h.addStretch(1)
        self.stack.insertWidget(0, w)
        self.tabs.insertTab(0, title)
        self._show_home()
        self.sync_host_actions()

    def _show_home(self) -> None:
        i = self.stack.indexOf(self._home_page)
        self.tabs.setCurrentIndex(i)
        self.stack.setCurrentIndex(i)

    def sync_host_actions(self) -> None:
        shown = False
        for b, src, offered in self._host:
            on = bool(offered())
            b.setVisible(on)
            b.setEnabled(src.isEnabled())
            if src.toolTip():
                b.setToolTip(src.toolTip())
            shown = shown or on
        if self._host_sep is not None:
            self._host_sep.setVisible(shown)

    def set_hint(self, text: str) -> None:
        """Instruction text in the free ribbon area (empty = hidden)."""
        if text:
            self._show_home()
        self.hint.setText(text)
        self.hint.setVisible(bool(text))

    def set_progress(self, done: float, total: float, label: str = "") -> None:
        """Excel export progress (called by the host while the file is written and read back). done >= total shows 100 % and
        hides the bar after a moment."""
        frac = max(0.0, min(1.0, done / total)) if total > 0 else 1.0
        self._bar_timer.stop()
        self._show_home()
        self.bar.setValue(int(frac * 1000))
        self.bar.setFormat(f"{label}  %p %" if label else "%p %")
        self.bar.show()
        if frac >= 1.0:
            self._bar_timer.start(1500)

    def _add_index(self) -> None:
        """Small dialog: name, start number and step of the index column; OK inserts it as the first column."""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QSpinBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Indexspalte")
        form = QFormLayout(dlg)
        name = QLineEdit("Pos.")
        start, step, digits = QSpinBox(), QSpinBox(), QSpinBox()
        digits.setRange(0, 12)
        digits.setSpecialValueText("automatisch")
        digits.setToolTip("Anzahl Stellen mit führenden Nullen, z. B. 4 -> 0001. Automatisch: so viele, wie die letzte Zahl braucht (1000 Zeilen -> 0001, 10 Zeilen -> 01).")
        try:
            n_rows = len(self.ctl._get(""))
        except Exception:  # noqa: BLE001 - only used for the example text
            n_rows = 1000
        for sb in (start, step):
            sb.setRange(-1_000_000, 1_000_000)
        start.setValue(1)
        step.setValue(1)
        ex = QLabel()

        def show(*_a) -> None:
            from .domain import indexcol as IX
            vals = IX.compute(IX.IndexParameters(start.value(), step.value() or 1, digits=digits.value()), max(n_rows, 1))
            ex.setText(", ".join(vals[:4]) + (" ... " + vals[-1] if len(vals) > 4 else ""))
        start.valueChanged.connect(show)
        step.valueChanged.connect(show)
        digits.valueChanged.connect(show)
        show()
        form.addRow("Spaltenname:", name)
        form.addRow("Startzahl:", start)
        form.addRow("Schritt:", step)
        form.addRow("Stellen (führende Nullen):", digits)
        form.addRow("Ergebnis:", ex)
        form.addRow(QLabel("Die Indexspalte wird als erste Spalte der Tabelle eingefügt."))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec() != QDialog.Accepted:
            return
        err = self.ctl.addIndexColumn(name.text(), start.value(), step.value(), digits.value())
        if err:
            self.ctl.message.emit(err)

    def _add_yes_no(self) -> None:
        """Small dialog: name, the two words and the start value; OK inserts the Yes / No column behind the selected tile."""
        from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit
        from .domain import yesno as YN
        dlg = QDialog(self)
        dlg.setWindowTitle("Ja/Nein-Spalte")
        form = QFormLayout(dlg)
        name = QLineEdit()
        name.setPlaceholderText("Name der neuen Spalte (Pflicht)")
        pairs = QComboBox()
        for y, n in YN.PAIRS:
            pairs.addItem(f"{y} / {n or '(leer)'}", (y, n))
        pairs.addItem("eigene Wörter …", None)
        yes, no = QLineEdit("Ja"), QLineEdit("Nein")
        no.setPlaceholderText("(leer)")
        start = QComboBox()
        info = QLabel()
        info.setWordWrap(True)

        def fill_start() -> None:
            at = start.currentIndex()
            start.clear()
            start.addItem(f"'{yes.text().strip()}'", "yes")
            start.addItem(f"'{no.text().strip()}'" if no.text().strip() else "leer (kein Wort)", "no")
            start.addItem("leer", "")
            start.setCurrentIndex(at if at >= 0 else 1)
            err = YN.validate(YN.YesNoParameters(yes.text().strip(), no.text().strip(), start.currentData() or ""))
            err = err or ("" if name.text().strip() else "Namen für die Spalte eingeben.")
            info.setText(err or "Jede Zeile erhält den Startwert; der Excel-Export bietet nur diese beiden Wörter als Auswahl. "
                                "Einzelne Zellen später in der Tabelle oder mit Ersetzen ändern.")
            info.setStyleSheet("color: #b03a2e;" if err else "color: #52606d;")
            ok_btn.setEnabled(not err)

        def pick_pair() -> None:
            pair = pairs.currentData()
            own = pair is None
            yes.setReadOnly(not own)
            no.setReadOnly(not own)
            if not own:
                yes.setText(pair[0])
                no.setText(pair[1])
            fill_start()
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = bb.button(QDialogButtonBox.Ok)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow("Spaltenname:", name)
        form.addRow("Wörter:", pairs)
        form.addRow("Ja-Wort:", yes)
        form.addRow("Nein-Wort:", no)
        form.addRow("Jede Zeile beginnt mit:", start)
        form.addRow(info)
        form.addRow(bb)
        pairs.currentIndexChanged.connect(lambda _i: pick_pair())
        name.textEdited.connect(lambda _t: fill_start())
        yes.textEdited.connect(lambda _t: fill_start())
        no.textEdited.connect(lambda _t: fill_start())
        start.activated.connect(lambda _i: fill_start())
        pick_pair()
        if dlg.exec() != QDialog.Accepted:
            return
        err = self.ctl.addYesNoColumn(name.text(), yes.text(), no.text(), start.currentData() or "", self.ctl.selectedRow)
        if err:
            self.ctl.message.emit(err)

    def _fill_empty(self) -> None:
        """Small dialog: the value for the empty cells and what it acts on (selected tile(s) or the whole group); OK fills them."""
        from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit
        c = self.ctl
        row = c.selectedRow
        dlg = QDialog(self)
        dlg.setWindowTitle("Leere Zellen füllen")
        form = QFormLayout(dlg)
        value = QLineEdit()
        value.setPlaceholderText("Wert für jede leere Zelle")
        group = QCheckBox("Ganze Gruppe" + (f" '{c.groupName(row)}'" if c.inGroup(row) else ""))
        group.setEnabled(bool(c.inGroup(row)))
        group.setToolTip("Alle Spalten der Gruppe der gewählten Kachel füllen" if c.inGroup(row) else "Die gewählte Kachel ist in keiner Gruppe.")
        keep = QCheckBox("Originalspalte sichtbar lassen")
        info = QLabel()
        info.setWordWrap(True)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_btn = bb.button(QDialogButtonBox.Ok)

        def show(*_a) -> None:
            keys = c.fill_targets(row, group.isChecked())
            labels = [c._label_of(k) for k in keys]
            names = ", ".join(labels[:6]) + (f" ... (+{len(labels) - 6})" if len(labels) > 6 else "")
            info.setText(f"{len(keys)} Spalte(n): {names}\n{c.empty_count(keys):,} leere Zellen erhalten den Wert. "
                         "Jede Spalte erhält eine neue berechnete Spalte „Name (filled)“.")
            ok_btn.setEnabled(bool(value.text().strip()) and bool(keys))
        value.textChanged.connect(show)
        group.toggled.connect(show)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow("Füllen mit:", value)
        form.addRow("Spalten:", group)
        form.addRow("", keep)
        form.addRow(info)
        form.addRow(bb)
        show()
        if dlg.exec() != QDialog.Accepted:
            return
        err = c.fillEmpty(row, value.text(), group.isChecked(), not keep.isChecked())
        if err:
            c.message.emit(err)

    def _add_columns(self) -> None:
        from .add_columns_dialog import AddColumnsDialog
        AddColumnsDialog(self.ctl, self).exec()

    # --- building ---------------------------------------------------------------------------------------------------------
    @staticmethod
    def _button(text: str, icon) -> QToolButton:
        b = QToolButton()
        b.setText(text)
        b.setAutoRaise(True)
        b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)      # icon + text (Power Query style)
        b.setIcon(icon)
        b.setIconSize(QSize(30, 30))                          # outline icons, same size and style as the main ribbon
        b.setAccessibleName(text)
        b.setMinimumSize(max(60, b.fontMetrics().horizontalAdvance(text) + 16), 62)    # the full text is always readable (never cut off); the tooltip adds the explanation
        return b

    def _page(self, items: list) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(2)
        for it in items:
            if it is None:
                sep = QWidget()
                sep.setFixedWidth(10)
                h.addWidget(sep)
                continue
            text, tip, action, needs = it
            b = self._button(text, ribbon_icon(KIND.get(text, "")))
            if isinstance(action, list):                              # a menu (Extract)
                m = QMenu(b)
                for label, fn in action:
                    m.addAction(label, fn)
                b.setMenu(m)
                b.setPopupMode(QToolButton.InstantPopup)
            else:
                b.clicked.connect(lambda _=False, f=action: f())
            self._items.append((b, tip, needs))
            h.addWidget(b)
        h.addStretch(1)
        return w

    def refresh(self) -> None:
        c = self.ctl
        has = c.selectedRow >= 0
        multi = c.selectionCount >= 2
        for b, tip, needs in self._items:
            ok = (needs == "") or (needs == "column" and has) or (needs == "multi" and multi) or (needs == "group" and has and bool(c.inGroup(c.selectedRow)))
            b.setEnabled(ok)
            b.setToolTip(tip if ok else (NEEDS_MULTI if needs == "multi" else NEEDS_GROUP if needs == "group" else NEEDS_COLUMN) + tip)
        undo_b, redo_b = self._items[0][0], self._items[1][0]
        undo_b.setEnabled(bool(c.canUndo))
        redo_b.setEnabled(bool(c.canRedo))
        undo_b.setToolTip(("Rückgängig: " + c.undoText) if c.canUndo else "Nichts rückgängig zu machen")
        redo_b.setToolTip(("Wiederholen: " + c.redoText) if c.canRedo else "Nichts zu wiederholen")
