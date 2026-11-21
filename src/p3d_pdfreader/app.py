"""Start der Anwendung: ``python -m p3d_pdfreader`` (PYTHONPATH = src und Tool-Ordner fuer main_gui_kit)."""
from __future__ import annotations

import logging
import sys

from .constants import APP_NAME, ORG
from .core.patterns import write_defaults
from .paths import logs_dir, patterns_file, tool_root


def version() -> str:
    try:
        return (tool_root() / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


def _german_qt_dialogs(app) -> None:
    """Standard-Knoepfe und Dateidialoge von Qt auf Deutsch (Ja/Nein, Speichern, Abbrechen ...)."""
    from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
    translator = QTranslator(app)
    if translator.load(QLocale(QLocale.German, QLocale.Germany), "qtbase", "_",
                       QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        app.installTranslator(translator)
        app._de_translator = translator              # Referenz halten


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--version" in args:
        print(f"{APP_NAME} {version()}")
        return 0
    root = str(tool_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    logging.basicConfig(filename=logs_dir() / "p3d_pdfreader.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", encoding="utf-8")
    write_defaults(patterns_file())
    from PySide6.QtWidgets import QApplication

    from .gui.main_window import MainWindow
    app = QApplication.instance() or QApplication(sys.argv)
    app.setOrganizationName(ORG)
    app.setApplicationName(APP_NAME)
    _german_qt_dialogs(app)
    from . import i18n
    i18n.install(app)                                  # Oberflaechensprache (gemerkte Wahl, Standard Deutsch)
    window = MainWindow(app, version())
    window.show()
    logging.info("Start %s %s", APP_NAME, version())
    return app.exec()
