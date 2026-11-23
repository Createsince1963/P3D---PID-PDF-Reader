"""Auswertung von ``QMessageBox`` mit eigenen Buttons.

``box.clickedButton() is button`` ist unzuverlaessig: Uebersetzt der i18n-Filter den Dialog beim Anzeigen (Sprache
nicht Deutsch), wird der Python-Wrapper des gemerkten Buttons ungueltig und ``clickedButton()`` liefert einen neuen
Wrapper - der Vergleich schlaegt fehl ("Verwerfen" wirkte wie "Abbrechen", das Fenster liess sich nicht schliessen).
Verglichen wird deshalb das C++-Objekt."""
from __future__ import annotations

import shiboken6
from PySide6.QtWidgets import QAbstractButton, QMessageBox


def _ptr(button: QAbstractButton | None) -> int | None:
    if button is None:
        return None
    try:
        return shiboken6.getCppPointer(button)[0]
    except (RuntimeError, TypeError):
        return None


def clicked(box: QMessageBox, *buttons: QAbstractButton):
    """Den geklickten unter ``buttons`` liefern (der beim Anlegen gemerkte Button), sonst None."""
    target = _ptr(box.clickedButton())
    if target is None:
        return None
    return next((b for b in buttons if _ptr(b) == target), None)
