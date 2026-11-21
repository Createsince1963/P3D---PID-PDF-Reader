"""Bilder fuer die HTML-Hilfe (``src/p3d_pdfreader/assets/help/img``) direkt aus der App erzeugen.

Je Menueband-Knopf ``<schluessel>.png`` (64 px, aus ``icons.ribbon_icon`` - eigene PNG in ``assets/icons`` haben Vorrang,
neue Symbole kommen also automatisch in die Hilfe), dazu ``ribbon.png`` (ganzes Menueband) und ``excel.png``.
Nach dem Austausch von Symbolen erneut ausfuehren:

    set QT_QPA_PLATFORM=offscreen & set PYTHONPATH=src;.
    python tools\\make_help_images.py
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"))
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
os.environ.setdefault("P3D_PDFREADER_HOME", tempfile.mkdtemp(prefix="p3d_help_"))   # Nutzerdaten bleiben unberuehrt


def main() -> None:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from p3d_pdfreader.gui.icons import excel_icon
    from p3d_pdfreader.gui.main_window import MainWindow
    out = ROOT / "src" / "p3d_pdfreader" / "assets" / "help" / "img"
    out.mkdir(parents=True, exist_ok=True)
    w = MainWindow(app, "help")
    w.resize(1900, 1000)
    w.show()
    for _ in range(20):
        app.processEvents()
    w.ribbon.grab().save(str(out / "ribbon.png"))
    for key, button in w.ribbon.buttons.items():
        button.icon().pixmap(64, 64).save(str(out / f"{key}.png"))
    excel_icon().pixmap(32, 32).save(str(out / "excel.png"))
    w.close()
    print(len(w.ribbon.buttons) + 2, "Bilder ->", out)


if __name__ == "__main__":
    main()
