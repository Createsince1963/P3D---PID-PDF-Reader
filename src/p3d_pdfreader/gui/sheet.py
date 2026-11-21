"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). Blattkopf wie in der Excel-Mappe: Titel, Untertitel, Projektzeile (Beschriftung/Wert), blaue Linie, ✕ zum Schliessen."""
from __future__ import annotations

import html
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QToolButton, QVBoxLayout, QWidget

NAVY = "#1B2B4A"


def _accent() -> str:
    from . import appearance
    return appearance.accent()

BLUE = "#0F5EA8"
BAND = "#EEF3FA"
_LABEL = re.compile(r"([A-ZÄÖÜ]{3,}(?: [A-ZÄÖÜ]{3,})*)  +")

def _filter_height() -> int:
    try:
        from main_gui_kit.tables import ColumnFilterHeader
        return int(ColumnFilterHeader.FILTER_HEIGHT)
    except Exception:  # noqa: BLE001 - Kit nicht verfuegbar
        return 0


#: Dunkelblauer Tabellenkopf wie in der Excel-Mappe; bei Kit-Tabellen mit Filterzeile bleibt der Text im oberen Teil des Kopfes.
_TABLE_HEADER_STATIC = ("QHeaderView::section { background: #1F4E79; color: white; border: none; border-right: 1px solid #2F6AA3; "
                    f"padding-left: 6px; padding-bottom: {_filter_height()}px; }}")
#: Ohne Filterzeile (einfache QTableWidget-Tabellen).
_PLAIN_HEADER_STATIC = "QHeaderView::section { background: #1F4E79; color: white; border: none; border-right: 1px solid #2F6AA3; padding: 5px 6px; }"


def label_value_html(line: str) -> str:
    """„PROJEKTNAME  X   PROJEKTNUMMER  Y“ -> kleine graue Beschriftungen + fette Werte."""
    parts = _LABEL.split(line)
    if len(parts) < 3:
        return html.escape(line)
    out = []
    for index in range(1, len(parts), 2):
        value = parts[index + 1].strip() if index + 1 < len(parts) else ""
        out.append(f'<span style="color:#6B7C93; font-size:7pt;">{html.escape(parts[index])}</span>&nbsp;&nbsp;'
                   f'<span style="font-weight:600; font-size:9pt;">{html.escape(value)}</span>')
    return "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;".join(out)


class SheetHeader(QFrame):
    close_requested = Signal()

    def __init__(self, closable: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("SheetHeader")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setStyleSheet("#SheetHeader { background: #FFFFFF; border: none; } #SheetHeader QLabel { background: transparent; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        top = QHBoxLayout()
        top.setContentsMargins(14, 8, 10, 4)
        self.text_box = QVBoxLayout()
        self.text_box.setSpacing(1)
        top.addLayout(self.text_box, 1)
        self.close_button = QToolButton()
        self.close_button.setText("✕")
        self.close_button.setToolTip("Blatt schließen")
        self.close_button.setStyleSheet("QToolButton { border: 1px solid #D0D7E2; border-radius: 4px; background: white; padding: 4px 8px; color: #44546A; }"
                                        "QToolButton:hover { background: #EEF3FA; }")
        self.close_button.clicked.connect(self.close_requested.emit)
        self.help_button = QToolButton()
        self.help_button.setText("?")
        self.help_button.setToolTip("Hilfe zu dieser Ansicht (F1)")
        self.help_button.setStyleSheet(self.close_button.styleSheet())
        self.help_button.clicked.connect(self._open_help)
        top.addWidget(self.help_button, 0, Qt.AlignTop)
        top.addWidget(self.close_button, 0, Qt.AlignTop)
        outer.addLayout(top)
        self.close_button.setVisible(closable)      # erst wenn der Knopf ein Eltern-Widget hat (sonst blitzt er als eigenes Fenster auf)
        self.band = QLabel()
        self.band.setTextFormat(Qt.RichText)
        self.band.setStyleSheet(f"background: {BAND}; padding: 6px 14px;")
        outer.addWidget(self.band)
        line = QFrame()
        line.setFixedHeight(3)
        line.setStyleSheet(f"background: {_accent()};")
        outer.addWidget(line)

    def _open_help(self) -> None:
        window = self.window()
        if hasattr(window, "show_help"):
            window.show_help()

    def set_lines(self, lines: list[str]) -> None:
        while self.text_box.count():
            item = self.text_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        label_lines = [l for l in lines[2:] if _LABEL.search(l)]
        plain = [l for l in lines[:2]]
        for index, text in enumerate(plain):
            label = QLabel(text)
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setStyleSheet(f"font-size: 15pt; font-weight: 700; color: {NAVY};" if index == 0 else "color: #6B7C93; font-size: 8pt;")
            self.text_box.addWidget(label)
        self.band.setText("<br>".join(label_value_html(l) for l in label_lines) if label_lines else "")
        self.band.setVisible(bool(label_lines))
        self.setVisible(bool(lines))


def _search_aware_dialog_class():
    """Wertauswahl des Kits, bei der ein eingetippter Suchtext als Filterwert gilt: mit aktiver Suche zaehlen nur die
    sichtbaren, angehakten Werte (der Kit zaehlt auch ausgeblendete mit - dann wurde der Suchtext nie als Filter uebernommen)."""
    global _SEARCH_DIALOG
    if _SEARCH_DIALOG is not None:
        return _SEARCH_DIALOG
    from main_gui_kit.tables import ValueFilterDialog

    class SearchAwareValueFilterDialog(ValueFilterDialog):
        def selected_values(self):
            searching = bool(self.search.text().strip())
            return [str(self.list.item(row).data(Qt.UserRole)) for row in range(self.list.count())
                    if self.list.item(row).checkState() == Qt.Checked and not (searching and self.list.item(row).isHidden())]

        def _apply_search(self, text):
            super()._apply_search(text)
            self._update_count()                       # Zaehler zeigt die Treffer der Suche

    _SEARCH_DIALOG = SearchAwareValueFilterDialog
    return _SEARCH_DIALOG


_SEARCH_DIALOG = None


def open_value_filter(header, column: int) -> None:
    """Wertauswahl fuer ``column`` oeffnen und uebernehmen (Logik des Kits, aber mit Suchtext als Filterwert)."""
    model = header._filter_model()
    if model is None or not hasattr(model, "available_values"):
        return
    values = model.available_values(column)
    selected = set(getattr(model, "value_filters", {}).get(column) or set())
    dialog = _search_aware_dialog_class()(values, selected, header, column_name=header._column_name(column))
    if dialog.exec() != QDialog.Accepted:
        return
    model.set_column_filter(column, "")
    chosen = dialog.selected_values()
    restricted = dialog.has_restriction()
    model.set_filter_values(column, chosen if restricted else None)
    editor = header.editors[column]
    editor.blockSignals(True)
    editor.setText(f"{len(chosen)} / {len(values)}" if restricted else "")
    editor.blockSignals(False)
    header.filterChanged.emit()


def filter_value_dialog_on_double_click(header) -> None:
    """Filterfeld: einfacher Klick setzt den Cursor ins Feld (Wert eintippen = nach Inhalt filtern), erst ein Doppelklick
    oeffnet die Wertauswahl. Der Kit oeffnet sie sonst schon beim ersten Klick und das Feld bekommt nie den Fokus
    (``mousePressEvent`` des Kits wird hier fuer jedes Filterfeld ersetzt; idempotent, auch nach erneutem ``bind_model``)."""
    for index, editor in enumerate(getattr(header, "editors", None) or []):
        if editor.property("p3d_double_click"):
            continue
        editor.setProperty("p3d_double_click", True)
        editor.mousePressEvent = lambda event, e=editor: QLineEdit.mousePressEvent(e, event)
        editor.mouseDoubleClickEvent = lambda event, i=index, h=header: open_value_filter(h, i)
        editor.setToolTip(f"Filter - {header._column_name(index)}\nTippen filtert nach Inhalt, Doppelklick wählt exakte Werte.")


def mark_active_filters(header) -> None:
    """Zeigt in jedem Filterfeld mit aktivem Filter (Text oder Wertauswahl) ein kleines Trichter-Symbol und stellt die
    Bedienung der Filterfelder ein (Doppelklick = Wertauswahl, siehe ``filter_value_dialog_on_double_click``)."""
    from .icons import filter_icon
    editors = getattr(header, "editors", None)
    if not editors:
        return
    filter_value_dialog_on_double_click(header)
    if not header.property("p3d_filter_icons"):
        header.setProperty("p3d_filter_icons", True)
        header.filterChanged.connect(lambda: mark_active_filters(header))
    icon = filter_icon(_accent())
    for editor in editors:
        action = editor.property("p3d_filter_action")
        if action is None:
            action = editor.addAction(icon, QLineEdit.LeadingPosition)
            editor.setProperty("p3d_filter_action", action)
            # Tippen aktualisiert das Symbol sofort (Wertauswahl setzt den Text ohne Signal -> filterChanged)
            editor.textChanged.connect(lambda text, a=action: a.setVisible(bool(text)))
        action.setIcon(icon)
        action.setVisible(bool(editor.text()))


def configure_subtabs(table) -> None:
    """Teilreiter (Rechtsklick auf Spaltenkopf > Teilreiter erstellen) immer als echte, einzeln anklickbare Reiter zeigen.

    Der Kit-Standard wechselt ab 12 Werten auf einen Schieberegler; hier bleibt es bei Reitern (bewusste Aktion des Nutzers,
    die Vorwarnung bei vielen Werten bleibt unveraendert). Farben folgen der Akzentfarbe."""
    bar = getattr(table, "_shared_subtab_bar", None)
    if bar is None:
        return
    bar.SLIDER_THRESHOLD = 10 ** 9
    accent = _accent()
    bar.all_button.setStyleSheet(
        f"QPushButton {{ padding: 3px 14px; border: 1px solid {accent}; border-radius: 3px; background: white; color: {accent}; font-weight: 600; }}"
        f"QPushButton:checked {{ background: {accent}; color: white; }}"
        f"QPushButton:hover {{ background: {_selection()}; }} QPushButton:checked:hover {{ background: {accent}; }}")
    bar.tabbar.setStyleSheet(
        f"QTabBar::tab {{ padding: 4px 12px; border: 1px solid #DDE3EC; border-bottom: none; background: #EEF3FA; color: #44546A; }}"
        f"QTabBar::tab:selected {{ background: {accent}; color: white; font-weight: 600; border-color: {accent}; }}"
        f"QTabBar::tab:hover:!selected {{ background: {_selection()}; }}")
    bar.tabbar.setElideMode(Qt.ElideNone)


def _selection() -> str:
    from . import appearance
    return appearance.selection_color()


def table_header_qss() -> str:
    from . import appearance
    return appearance.header_qss()


def plain_header_qss() -> str:
    from . import appearance
    return appearance.plain_header_qss()


TABLE_HEADER_QSS = _TABLE_HEADER_STATIC      # Alt-Namen (Standardfarben); neue Stellen nutzen table_header_qss()/plain_header_qss()
PLAIN_HEADER_QSS = _PLAIN_HEADER_STATIC
