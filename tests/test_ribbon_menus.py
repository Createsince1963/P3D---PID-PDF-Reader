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
