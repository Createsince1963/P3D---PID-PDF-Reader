"""Kachel-Editor als eigenstaendiges Modul (Vollfenster) fuer die Datenlink-Importliste.

* ``window.TileEditorWindow``  Vollfenster mit den drei Bereichen aus P3D Tag Compliance (Kachel-Editor, Seitenleiste,
                               Datentabelle) und Ladebildschirm
* ``loading.LoadingOverlay``   Ladebildschirm (Zahnrad, Schritt, Prozent)
* ``deck.SideDeck``            Seitenleiste als Dock (aktive Kachel, Gruppe, Verlauf)
* ``source.ImportSource``      ``ColumnSource`` ueber der Importliste + Tabellenmodell
* ``german``                   deutsche Beschriftung des Menuebands

Die Kacheln selbst kommen aus ``p3d_pdfreader.column_editor`` (unveraenderte Kopie aus P3D Tag Compliance)."""
from __future__ import annotations

from .window import TileEditorWindow

__all__ = ["TileEditorWindow"]
