"""Menueband (Gruppenueberschriften oben, Einstellungen nach Einlesen) und Rechtsklick-Menues der Tabellen."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui.main_window import MainWindow
    w = MainWindow(app, "test")
    yield w
    w.close()


def _group_titles(ribbon) -> list[str]:
    from p3d_pdfreader.gui.ribbon import RibbonGroup
    groups = []
    for i in range(ribbon.body.count()):
        widget = ribbon.body.itemAt(i).widget()
        if isinstance(widget, RibbonGroup):
            groups.append(widget)
    return groups


def test_group_heads_on_top_and_settings_after_einlesen(window):
    groups = _group_titles(window.ribbon)
    titles = [g.title.text() for g in groups]
    # Nutzervorgabe 2026-11-21: Einstellungen in der Gruppe Projekt, Ansicht vor Pruefen, neu nummeriert
    assert titles == ["Projekt", "1  Einlesen", "2  Ansicht", "3  Prüfen", "4  Review / Redline", "5  Export", "Web",
                      "Hilfe"]
    project = groups[0]
    keys = [k for k, b in window.ribbon.buttons.items() if project.isAncestorOf(b)]
    # Nutzervorgabe 2026-11-22: hinter "Projekt waehlen" die Umschalter 1. Projektmodus 2. Rohrleitungen
    assert keys == ["project_pick", "project_mode", "pipes", "project_defs", "paths", "patterns", "settings_menu"]
    assert window.ribbon.buttons["pipes"].isCheckable() and window.ribbon.buttons["pipes"].menu() is None
    # Einstellungen › "Layer fuer Review im PDF" (Nutzervorgabe 2026-11-22), umschaltbar und gemerkt
    actions = [a.text() for a in window.settings_menu.actions()]
    assert actions == ["Layer für Review im PDF"] and window.layer_action.isCheckable()
    for group in groups:
        assert group.layout().indexOf(group.title) == 0
        assert group.title.objectName() == "RibbonGroupHead"
        assert "background" in group.title.styleSheet()


def test_cell_menu_copy_filter_and_columns(window, app):
    from p3d_pdfreader.gui import table_menu
    table = window.page.tags
    table.set_rows([["Tag", "P-101", 1] + [""] * (len(table.headers) - 3),
                    ["Tag", "P-102", 1] + [""] * (len(table.headers) - 3)])
    view = table.table
    index = view.model().index(0, 1)
    view.setCurrentIndex(index)
    menu = table_menu.cell_menu(view, index, on_clear_all=table.clear_filters, on_filter=table._count)
    texts = [a.text() for a in menu.actions() if a.text()]
    assert "Kopieren" in texts and "Spalten …" in texts and "Alle Filter zurücksetzen" in texts
    assert table_menu.row_text(view, 0).split("\t")[1] == "P-101"
    assert table_menu.filter_by_value(view, 1, "P-102")
    assert view.model().rowCount() == 1
    table_menu.clear_column_filter(view, 1)
    assert view.model().rowCount() == 2
    table_menu.apply_columns(view, list(range(view.model().columnCount())), {0})
    assert view.isColumnHidden(0)
    dialog = table_menu.ColumnsDialog(view)
    dialog.set_default()
    assert not dialog.hidden()
    dialog.accept()
    assert not view.isColumnHidden(0)


def test_groups_fold_into_stack_of_three(window, app):
    """Nutzervorgabe 2026-11-22: Klick auf die Kopfleiste klappt ein; Kopfleisten stapeln sich hinter den sichtbaren
    Gruppen, 4 je Spalte (Text linksbuendig); Klick auf die gestapelte Kopfleiste klappt wieder auf; Zustand wird gemerkt."""
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from p3d_pdfreader.gui import last_paths
    from p3d_pdfreader.gui.main_window import FOLD_KEY
    fold = window.ribbon_fold
    groups = _group_titles(window.ribbon)
    web, hilfe = groups[-2], groups[-1]
    # Standard beim ersten Start: nur Projekt offen, die anderen 7 Kopfleisten in einer Reihe
    assert not groups[0].isHidden() and all(g.isHidden() for g in groups[1:])
    pos = [fold.grid.getItemPosition(fold.grid.indexOf(b))[:2] for b in fold.stack_buttons]
    assert pos == [(0, c) for c in range(7)]
    for group in groups:
        fold.set_collapsed(group, False)
    assert fold.stack.isHidden() and last_paths.get_value(FOLD_KEY) == []
    QTest.mouseClick(web.title, Qt.LeftButton)
    fold.set_collapsed(hilfe, True)
    assert web.isHidden() and hilfe.isHidden() and not fold.stack.isHidden()
    assert last_paths.get_value(FOLD_KEY) == ["Web", "Hilfe"]
    # wie die beiden blauen Rechtecke: Web oben, Hilfe darunter in derselben Spalte
    pos = [fold.grid.getItemPosition(fold.grid.indexOf(b))[:2] for b in fold.stack_buttons]
    assert [b.text() for b in fold.stack_buttons] == ["Web", "Hilfe"] and pos == [(0, 0), (1, 0)]
    # alle einklappen: 8 Gruppen -> zwei Spalten mit je 4 Kopfleisten
    for group in groups:
        fold.set_collapsed(group, True)
    pos = [fold.grid.getItemPosition(fold.grid.indexOf(b))[:2] for b in fold.stack_buttons]
    assert pos == [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)]
    assert all("text-align: left" in b.styleSheet() for b in fold.stack_buttons)
    assert fold.stack_sep.isHidden()                       # keine sichtbare Gruppe davor -> keine Trennlinie
    # gestapelte Kopfleiste "1  Einlesen" anklicken -> Gruppe wieder an ihrer Stelle sichtbar
    button = next(b for b in fold.stack_buttons if b.text() == "1  Einlesen")
    button.click()
    assert not groups[1].isHidden() and groups[1].sep.isHidden()   # erste sichtbare Gruppe: ohne Trennlinie davor
    assert "1  Einlesen" not in last_paths.get_value(FOLD_KEY) and len(fold.stack_buttons) == 7


def test_fold_state_restored_on_start(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui import last_paths
    from p3d_pdfreader.gui.main_window import FOLD_KEY, MainWindow
    last_paths.set_value(FOLD_KEY, ["Hilfe", "unbekannt"])
    w = MainWindow(app, "test")
    try:
        groups = _group_titles(w.ribbon)
        assert groups[-1].isHidden() and [b.text() for b in w.ribbon_fold.stack_buttons] == ["Hilfe"]
        assert not w.ribbon_fold.stack_sep.isHidden()
    finally:
        w.close()


def test_real_right_click_opens_cell_menu(window, app, monkeypatch):
    """Ein echtes Rechtsklick-Ereignis auf den Zellen oeffnet das Menue (Dateien und Tags)."""
    from PySide6.QtGui import QContextMenuEvent
    from p3d_pdfreader.gui import table_menu
    shown = []
    monkeypatch.setattr(table_menu, "show_menu",
                        lambda menu, _pos: shown.append([x.text() for x in menu.actions() if x.text()]))
    window.show()
    for table in (window.page.files, window.page.tags):
        table.set_rows([["a", "b", 1] + [""] * (len(table.headers) - 3)])
        app.processEvents()
        view = table.table
        pos = view.visualRect(view.model().index(0, 1)).center()
        shown.clear()
        app.sendEvent(view.viewport(), QContextMenuEvent(QContextMenuEvent.Mouse, pos, view.viewport().mapToGlobal(pos)))
        assert len(shown) == 1 and {"Kopieren", "Einfügen", "Zellen leeren", "Alles markieren"} <= set(shown[0])


def test_multi_cell_copy_paste_clear(window, app):
    """Mehrere Zellen: kopieren als Tabulator-Text, ein Wert in alle markierten Zellen, Block ab links oben, leeren;
    ganze Zeilen markiert -> nur die Spalte der aktuellen Zelle."""
    from PySide6.QtCore import QItemSelection, QItemSelectionModel
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.gui import table_menu
    from p3d_pdfreader.gui.main_window import FIRST_FIELD
    pdf = PdfResult(path=paths_home() / "a.pdf", drawing_no="D", tags=[Tag(tag=f"XV-{i}", type="Instrument")
                                                                        for i in (1, 2, 3)])
    window.results = [pdf]
    window._refresh()
    page = window.page
    page.files.table.setCurrentIndex(page.files.proxy.index(0, 0))
    view, proxy = page.tags.table, page.tags.proxy
    comment, wpo = FIRST_FIELD + 3, FIRST_FIELD + 4
    sel = view.selectionModel()

    def block(r0, r1, c0, c1):
        sel.setCurrentIndex(proxy.index(r1, c1), QItemSelectionModel.NoUpdate)      # wie nach dem Ziehen: Ende
        sel.select(QItemSelection(proxy.index(r0, c0), proxy.index(r1, c1)), QItemSelectionModel.ClearAndSelect)

    block(0, 1, comment, wpo)
    QApplication.clipboard().setText("a")
    assert page.paste_cells() == 4                                                    # ein Wert -> alle 4 Zellen
    assert table_menu.selection_text(view).count("a") == 4
    QApplication.clipboard().setText("1\t2\n3\t4")
    assert page.paste_cells() == 4                                                    # Block ab links oben
    assert table_menu.selection_text(view) == "1\t2\n3\t4"
    assert page.clear_cells() == 4 and table_menu.selection_text(view) == "\t\n\t"
    view.selectRow(2)                                                                 # ganze Zeile
    sel.setCurrentIndex(proxy.index(2, comment), QItemSelectionModel.NoUpdate)
    QApplication.clipboard().setText("z")
    assert page.paste_cells() == 1
    assert [proxy.index(2, c).data() for c in (comment, wpo)] == ["z", ""]
    page.store.dirty = False


def paths_home():
    from p3d_pdfreader import paths
    return paths.home_dir()
