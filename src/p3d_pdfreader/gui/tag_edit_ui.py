"""Zeichen im Tag ersetzen (Oberflaeche): Dialog, gemerkte Regel in ``config/state.json``, Eintraege im Kopfmenue der Spalte
Tag. Die Regel selbst steht in ``core.tag_edit``."""
from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout)

from ..core.tag_edit import RULE, TagEdit
from . import last_paths

KEY = "tag_edit"                    # config/state.json: {"find": "-", "to": ""}
COLUMN = "Tag"
NOTE = "edit"                       # Hinweis im Spaltenkopf (kleine kursive Schrift rechts)


def load() -> None:
    """Gemerkte Regel beim Start uebernehmen (ungueltige oder fehlende Eintraege = keine Regel)."""
    data = last_paths.get_value(KEY, {})
    try:
        RULE.set(str((data or {}).get("find", "")), str((data or {}).get("to", "")))
    except (ValueError, AttributeError):
        RULE.clear()


def save() -> None:
    last_paths.set_value(KEY, {"find": RULE.find, "to": RULE.to})


def ask(parent) -> tuple[str, str] | None:
    """Dialog: gesuchtes Zeichen und Ersatz (leer = Zeichen entfernen). ``None`` bei Abbruch."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Zeichen ersetzen")
    layout = QVBoxLayout(dlg)
    layout.addWidget(QLabel("Zeichen im Tag ersetzen (nur Ansicht, Export und Prüfung – die PDF bleibt unverändert).\n"
                            "Ersatz leer lassen = Zeichen entfernen (z. B. XV-130 → XV130)."))
    form = QFormLayout()
    find, to = QLineEdit(RULE.find), QLineEdit(RULE.to)
    find.setMaxLength(8)
    to.setMaxLength(8)
    form.addRow("Ersetze:", find)
    form.addRow("Durch:", to)
    layout.addLayout(form)
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText("OK")
    buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)
    while dlg.exec() == QDialog.Accepted:
        err = TagEdit.problem(find.text(), to.text())
        if not err:
            return find.text(), to.text()
        QMessageBox.warning(dlg, "Zeichen ersetzen", err)
    return None


def header_menu(menu, column_name: str, window, changed) -> None:
    """Eintraege im Rechtsklick-Menue des Spaltenkopfs „Tag“; ``changed()`` baut die Tabellen neu auf."""
    if column_name != COLUMN:
        return
    menu.addSeparator()

    def replace() -> None:
        result = ask(window)
        if result is None:
            return
        RULE.set(*result)
        save()
        changed()
        window.statusBar().showMessage(f"Tag: Zeichen ersetzen {RULE.describe()} (Spaltenkopf: edit)", 8000)

    def undo() -> None:
        RULE.clear()
        save()
        changed()
        window.statusBar().showMessage("Tag: Ersetzung zurückgenommen.", 6000)

    menu.addAction("Zeichen ersetzen …" + (f"  ({RULE.describe()})" if RULE.active else ""), replace)
    menu.addAction("Ersetzung zurücknehmen", undo).setEnabled(RULE.active)


def notes(headers: list[str]) -> dict[int, str]:
    """Spalten mit Hinweis „edit“ im Kopf."""
    return {headers.index(COLUMN): NOTE} if RULE.active and COLUMN in headers else {}
