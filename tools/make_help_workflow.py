"""Workflow-Kapitel der HTML-Hilfe erzeugen: echte Bildschirmfotos der Oberflaeche je Arbeitsschritt mit
nummerierten Markierungen (1, 2, 3 …) und Erklaerung je Markierung (Nutzervorgabe 2026-11-22).

Ausgabe in ``src/p3d_pdfreader/assets/help``:
* ``img/wf_<name>.png``  Bildschirmfotos (Ausschnitte) aus der laufenden App (offscreen, Windows-Schriften)
* ``workflow.js``        ``const WF = [...]``: Schritte, Bilder, Markierungen (Lage in % des Bildes) und Texte;
                         das Handbuch (Kapitel „Workflow Schritt für Schritt“) zeichnet daraus Nummern und Listen.

Die Lage jeder Nummer wird aus dem Bedienelement berechnet - nach GUI-Aenderungen einfach neu ausfuehren:

    set PYTHONPATH=src;.
    python tools\\make_help_workflow.py [Ordner mit Beispiel-PDFs]

Beispiel-PDFs: Argument, sonst ``P3D_PDFREADER_SAMPLES``, sonst ``%USERPROFILE%\\Downloads\\PID Plots``. Die PDFs werden
nur gelesen; Nutzerdaten bleiben unberuehrt (eigener Temp-Datenordner). Die Datenlink-Liste im Bild ist eine aus den
gescannten Tags gebaute Beispielliste."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")   # Kachel-Editor (QML): offscreen ist die Schrift unlesbar -> mit QT_QPA_PLATFORM=windows starten
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"))
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
os.environ["P3D_PDFREADER_HOME"] = tempfile.mkdtemp(prefix="p3d_help_wf_")     # Nutzerdaten bleiben unberuehrt

HELP = ROOT / "src" / "p3d_pdfreader" / "assets" / "help"
DISPLAY_WIDTH = 1100                                   # Bildbreite im Handbuch (ca.)
SAMPLE_NAMES = ["SGOPS-P-DL1-PID-00-EQPM-001.pdf", "SGOPS-P-DL1-PID-00-EQPM-002.pdf", "SGOPS-P-DL1-PID-00-EQPM-003.pdf"]


class Figure:
    """Ein Bild (Ausschnitt eines Widgets) mit nummerierten Markierungen."""

    def __init__(self, name: str, root, crop=None, caption: str = ""):
        from PySide6.QtCore import QRect
        self.name, self.root, self.caption = name, root, caption
        self.pix = root.grab()
        self.crop = crop if crop is not None else QRect(0, 0, self.pix.width(), self.pix.height())
        self.marks: list[dict] = []
        self._pins: list[tuple[float, float]] = []

    def rect_of(self, widget, rect=None):
        """Rechteck eines Widgets (oder ``rect`` in dessen Koordinaten) im Bildausschnitt."""
        from PySide6.QtCore import QPoint, QRect
        r = rect if rect is not None else QRect(QPoint(0, 0), widget.size())
        top_left = widget.mapTo(self.root, r.topLeft()) if widget is not self.root else r.topLeft()
        return QRect(top_left - self.crop.topLeft(), r.size())

    def mark(self, widget, title: str, text: str, rect=None) -> None:
        r = self.rect_of(widget, rect).intersected(self.crop.translated(-self.crop.topLeft()))
        w, h = self.crop.width(), self.crop.height()
        # Nummer an die linke obere Ecke; liegt dort schon eine, nach rechts ruecken (Abstand ~28 px in der Anzeige,
        # das Handbuch zeigt die Bilder mit ca. 1100 px Breite)
        gap = 28 / min(1.0, DISPLAY_WIDTH / w)
        x, y = float(r.x()), float(r.y())
        while any(abs(x - px) < gap and abs(y - py) < gap for px, py in self._pins):
            x += gap
        self._pins.append((x, y))
        self.marks.append({"rect": [round(100 * r.x() / w, 2), round(100 * r.y() / h, 2),
                                    round(100 * r.width() / w, 2), round(100 * r.height() / h, 2)],
                           "pin": [round(100 * min(x, w - 4) / w, 2), round(100 * y / h, 2)],
                           "title": title, "text": text})

    def save(self, out: Path) -> dict:
        pix = self.pix.copy(self.crop)
        pix.save(str(out / f"wf_{self.name}.png"))
        return {"img": f"img/wf_{self.name}.png", "w": pix.width(), "h": pix.height(), "caption": self.caption,
                "marks": self.marks}


def section_rect(header, logical: int):
    from PySide6.QtCore import QRect, Qt
    x = header.sectionViewportPosition(logical)
    return QRect(x, 0, header.sectionSize(logical), header.height())


def wait(app, seconds: float = 0.3) -> None:
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()


def united(widgets, root):
    from PySide6.QtCore import QPoint, QRect
    r = QRect()
    for wdg in widgets:
        r = r.united(QRect(wdg.mapTo(root, QPoint(0, 0)), wdg.size()))
    return r


def shown(dialog, app, width: int = 0, height: int = 0):
    """Dialog zum Fotografieren oeffnen, ohne ihn auf dem Bildschirm zu zeigen."""
    from PySide6.QtCore import Qt
    dialog.setAttribute(Qt.WA_DontShowOnScreen)
    if width:
        dialog.resize(width, height)
    dialog.show()
    wait(app, 0.4)
    return dialog


def top_of(widget, root, height: int, pad: int = 4):
    r = united([widget], root).adjusted(-pad, -pad, pad, pad)
    r.setHeight(min(r.height(), height))
    return r


def topic_steps(app, w, out: Path, group_fig) -> list[dict]:
    """Ansichten zu den Themen ab 1.0.38: Listenabgleich, Prueftypen, 2TAG, Multi-Tag, Vorschau, Tabellen, Pfade."""
    from PySide6.QtCore import QPoint, QRect
    from p3d_pdfreader.gui.paths_dialog import PathsDialog
    from p3d_pdfreader.gui.table_export import PreviewDialog
    from p3d_pdfreader.gui.type_dialog import TypeDialog
    page, rb, steps = w.page, w.ribbon.buttons, []
    strip = page.tags.layout().itemAt(1).widget()
    multi = page.tags.layout().itemAt(2).widget()
    left = united([page.tags], w).adjusted(-4, -4, 4, 4)

    def step(ident: str, title: str, intro: str, figs: list) -> None:
        steps.append({"id": ident, "title": title, "intro": intro, "figs": figs})

    # --- Pfade ---
    dlg = shown(PathsDialog(w), app)
    f = Figure("paths", dlg, caption="Projekt › Pfade")
    f.mark(dlg, "Quell- und Exportordner", "Quellordner hinzufügen oder entfernen und den Exportordner wählen. "
                                           "„Quellordner scannen“ (F5) liest die Quellordner ein.",
           QRect(0, 0, dlg.width(), dlg.height() // 2))
    step("paths", "Pfade festlegen", "Einmal einstellen: wo die PDFs liegen und wohin die Ausgaben gehen.",
         [f.save(out)])
    dlg.close()

    # --- Abgleich mit der Liste ---
    page.reset_tag_filters()
    wait(app, 0.3)
    f = Figure("listcheck", w, top_of(page.tags, w, 520), "Leisten der Tag-Tabelle: Abgleich mit der Importliste")
    f.mark(strip.buttons["link_cols"], "Importspalten", "Spalten der Liste ein- oder ausblenden.")
    f.mark(strip.buttons["link_menu"], "Importliste", "Link aufheben, Liste neu einlesen, bearbeiten, entfernen.")
    f.mark(strip.buttons["join"], "Abgleich", "Richtung wählen: PDF → Liste, Liste → PDF oder beide. Fehlendes = „n.a.“.")
    th = page.tags.table.horizontalHeader()
    hits = page.tags.headers.index("Datenlink-Treffer")
    f.mark(th, "Datenlink-Treffer", "0 = Tag fehlt in der Liste. Der Bindestrich zwischen Kürzel und Nummer zählt "
                                    "nicht (FV-501 passt zu FV501).", section_rect(th, hits))
    figs = [f.save(out)]
    f = group_fig("listcheck_ribbon", "link_review", "Menüband, Gruppe „3 Prüfen“")
    f.mark(rb["link_review"], "Review Importliste", "Blatt mit dem Prüfergebnis über alle PDFs.")
    figs.append(f.save(out))
    w.show_link_review()
    wait(app, 0.8)
    sheet = w.review_page
    r = top_of(sheet, w, 520)
    r.setWidth(min(r.width(), 1300))
    f = Figure("listcheck_sheet", w, r, "Blatt „Review Importliste“")
    f.mark(sheet.header, "Zählung", "Anzahl je Prüfergebnis.")
    f.mark(sheet.tags.table.viewport(), "Prüfergebnis je Zeile", "OK, Nicht in Liste, Fehlt im PDF, Zeichnung nicht "
                                                                "gescannt.", QRect(0, 0, 260, 120))
    figs.append(f.save(out))
    w._close_widget(sheet)                  # sonst oeffnet jedes Neu-Verknuepfen das Pruefblatt wieder
    w.tabs.setCurrentWidget(page)
    wait(app, 0.3)
    step("listcheck", "PDF-Tags mit der Liste abgleichen",
         "Nach dem Setzen der Datenlink-Felder: Treffer ansehen, Richtung wählen und das Prüfblatt öffnen.", figs)

    # --- Prueftypen ---
    f = group_fig("types_ribbon", "check_types", "Menüband, Gruppe „3 Prüfen“")
    f.mark(rb["check_types"], "Prüftypen", "Öffnet die Optionstabelle.")
    figs = [f.save(out)]
    dlg = TypeDialog(w.results, [], w)
    dlg.only("Instrument")
    shown(dlg, app, 640, 460)
    f = Figure("types_dialog", dlg, caption="Optionstabelle „Prüftypen“ (Beispiel: nur Instrument)")
    t = dlg.table
    f.mark(t.viewport(), "Haken je Typ", "Nur angehakte Typen werden geprüft und ausgegeben.",
           QRect(0, 0, 60, t.rowHeight(0) * t.rowCount()))
    f.mark(t.viewport(), "Doppelklick auf eine Zeile", "Prüft nur diesen Typ.",
           QRect(t.columnViewportPosition(1), 0, t.columnWidth(1), t.rowHeight(0)))
    f.mark(t.horizontalHeader(), "Anzahl Tags und PDFs", "Wie oft der Typ in den gescannten PDFs vorkommt.",
           section_rect(t.horizontalHeader(), 2))
    from PySide6.QtWidgets import QDialogButtonBox
    f.mark(dlg.findChild(QDialogButtonBox), "OK", "Übernimmt die Auswahl; die Kopfzeile nennt die geprüften Typen.")
    figs.append(f.save(out))
    dlg.close()
    step("types", "Prüftypen wählen (Vorfilter)",
         "Vor der Prüfung festlegen, ob alles oder nur z. B. Equipment oder Instrument geprüft wird. Der Filter gilt "
         "auch für Redline, Review-Excel, Bulk und Export.", figs)

    # --- 2TAG ---
    page.two_tag_button.setChecked(True)
    wait(app, 0.8)
    th = page.tags.table.horizontalHeader()
    view = page.tags.table
    model = view.model()
    tag_col = page.tags.headers.index("Tag")
    marked = next((model.index(r, tag_col) for r in range(model.rowCount())
                   if "Multi Tag" in str(model.index(r, tag_col).data(3) or "")), None)
    if marked is not None:
        view.scrollTo(marked, view.ScrollHint.PositionAtTop)
        wait(app, 0.3)
    f = Figure("twotag", w, top_of(page.tags, w, 520), "2TAG eingeschaltet")
    f.mark(page.two_tag_button, "2TAG einschalten", "Plant 3D schreibt doppelt angelegte Tags mit „?“ am Ende in die "
                                                    "Datenbank. Mit 2TAG werden auch diese Zeilen verknüpft.")
    if marked is not None:
        f.mark(view.viewport(), "Hellgelbe Tag-Zelle", "„Multi Tag Eintrag in Projekt“: der Tooltip nennt die andere "
                                                      "PID. Zählt unter „Nur Abweichungen“.", view.visualRect(marked))
    f.mark(th, "Treffer", "Zeigt beide Listenzeilen (mit und ohne „?“).",
           section_rect(th, page.tags.headers.index("Datenlink-Treffer")))
    step("twotag", "Doppelt angelegte Tags (2TAG)",
         "Wenn ein Tag in Plant 3D zweimal existiert, passt der Wert der Datenbank (PI-100?) nicht zur PDF (PI-100). "
         "2TAG schließt diese Lücke und weist darauf hin.", [f.save(out)])

    # --- Multi-Tag-PDF ---
    viewer = page.viewer
    viewer.notes_button.setChecked(True)
    wait(app, 0.8)
    preview = page.preview
    f = Figure("multitag_bar", w, top_of(page.tags, w, 150), "Leiste „Multi Tag“ über der Tag-Tabelle")
    f.mark(multi.buttons["multitag"], "Multi-Tag-PDF", "Kopie der PDF (gewählte oder alle) mit rotem Eintrag je "
                                                       "doppeltem Tag.")
    f.mark(page.review_table_button, "Reviewtabelle", "Hängt Seiten mit allen Reviewpunkten an (Spalten wie in der "
                                                      "Tag-Tabelle).")
    figs = [f.save(out)]
    if preview._notes:
        note = preview._notes[0]
        s = preview._scale
        preview.resetTransform()
        preview.scale(1.6, 1.6)
        preview.centerOn((note.rect[0] + note.rect[2]) / 2 * s, note.box[3] * s)
        preview._render_detail()
        wait(app, 0.5)
    f = Figure("multitag_viewer", w, united([page.viewer], w).adjusted(-4, -4, 4, 4),
               "PDF-Viewer mit „Kommentare bearbeiten“")
    f.mark(viewer.notes_button, "Kommentare bearbeiten", "Zeigt die roten Einträge über der PDF.")
    if preview._notes:
        item = next(i for i in preview._note_items if type(i).__name__ == "NoteItem")
        rect = preview.mapFromScene(item.sceneBoundingRect()).boundingRect()
        f.mark(preview.viewport(), "Eintrag ziehen", "Mit der Maus verschieben; Rechtsklick setzt die Position zurück. "
                                                     "Gilt für die Multi-Tag-PDF.", rect)
    f.mark(viewer.mono_button, "Monochrom", "Eingeschaltet wird auch die ausgegebene PDF schwarz-weiß; "
                                            "Review-Elemente bleiben farbig.")
    figs.append(f.save(out))
    viewer.notes_button.setChecked(False)
    preview.fit()
    step("multitag", "Doppelte Tags in der PDF kommentieren",
         "Einträge ansehen, bei Bedarf verschieben und die kommentierte Kopie erzeugen. Das Original bleibt "
         "unverändert.", figs)
    page.two_tag_button.setChecked(False)
    wait(app, 0.5)

    # --- Excel-Vorschau ---
    f = Figure("preview_bar", w, top_of(page.tags, w, 150), "Leiste der Tag-Tabelle")
    f.mark(strip.buttons["preview_tags"], "Vorschau", "Zeigt den Excel-Export vorher an.")
    f.mark(strip.buttons["excel_tags"], "Excel", "Direkt sichern, ohne Vorschau.")
    figs = [f.save(out)]
    dlg = shown(PreviewDialog(page.tags.table, "Tags"), app, 1100, 520)
    f = Figure("preview_dialog", dlg, caption="Vorschau des Excel-Exports")
    f.mark(dlg.view, "Tabelle wie in der Datei", "Spalten, Reihenfolge, Breiten und Farben der Ansicht.")
    box = dlg.findChild(QDialogButtonBox)
    f.mark(box, "Als Excel sichern …", "Speichert die ganze Tabelle (die Vorschau zeigt höchstens 500 Zeilen).")
    figs.append(f.save(out))
    dlg.close()
    step("preview", "Excel-Export vorher ansehen",
         "Bei allen anderen Tabellen: Rechtsklick auf das Excel-Symbol in der Ecke › „Vorschau ansehen“.", figs)

    # --- Tabellenbedienung ---
    view = page.tags.table
    header = view.horizontalHeader()
    f = Figure("tables", w, united([page.tags], w).adjusted(-4, -4, 4, 4), "Standardfunktionen jeder Tabelle")
    corner = next((c for c in view.children() if type(c).__name__ == "QToolButton"), None)
    if corner is not None:
        f.mark(corner, "Excel-Symbol", "Klick: sichern. Rechtsklick: Vorschau ansehen.")
    f.mark(header, "Spaltenkopf", "Klick sortiert, Feld darunter filtert, Doppelklick im Feld wählt Werte, "
                                  "Rechtsklick öffnet das Spaltenmenü.", section_rect(header, tag_col))
    f.mark(view.viewport(), "Zellen markieren", "Wie in Excel ziehen; Strg+C kopiert, Strg+V fügt in Review-Spalten ein.",
           QRect(0, 0, 320, 4 * view.rowHeight(0)))
    f.mark(page.tags.admin, "Ansicht speichern", "Save / Load / Reset Layout.")
    step("tables", "Mit Tabellen arbeiten", "Diese Bedienung gilt für alle Tabellen des Tools.", [f.save(out)])
    return steps


def main() -> None:
    from PySide6.QtCore import QRect, Qt
    from PySide6.QtWidgets import QApplication, QMenu
    app = QApplication.instance() or QApplication([])
    from p3d_pdfreader import paths
    from p3d_pdfreader.core.data_link import ImportTable
    from p3d_pdfreader.gui import main_window as mw
    from p3d_pdfreader.gui.tile_editor import TileEditorWindow
    from p3d_pdfreader.gui.review_dialog import ReviewDialog
    from p3d_pdfreader.gui.ribbon import RibbonGroup

    folder = Path(sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "P3D_PDFREADER_SAMPLES", Path.home() / "Downloads" / "PID Plots"))
    samples = [str(folder / n) for n in SAMPLE_NAMES if (folder / n).is_file()]
    if not samples:
        samples = [str(p) for p in sorted(folder.glob("*.pdf"))[:3]]
    if not samples:
        raise SystemExit(f"Keine Beispiel-PDFs in {folder}")

    out = HELP / "img"
    out.mkdir(parents=True, exist_ok=True)
    w = mw.MainWindow(app, "help")
    w.setAttribute(Qt.WA_DontShowOnScreen)
    w.resize(2300, 1180)
    w.show()
    for g in w.ribbon_fold.groups:                     # alle Gruppen aufklappen
        w.ribbon_fold.set_collapsed(g, False)
    w.page.scan_button.setChecked(True)
    wait(app)
    w.scan(samples)
    start = time.time()
    while w._thread is not None and time.time() - start < 120:
        app.processEvents()
    wait(app, 0.5)

    # Beispiel-Liste fuer den Datenlink aus den gescannten Tags (Instrumente und Armaturen)
    rows = []
    for r in w.results:
        for t in r.tags:
            if t.type in ("Instrument", "Armatur"):
                rows.append([r.drawing_no, f"203-17-{t.tag}", t.type.upper(), f"Beispiel {t.tag}", "203-3-11B"])
    # doppelt angelegte Tags wie in Plant 3D („?“ am Ende, auf einer anderen Zeichnung) fuer 2TAG und Multi-Tag-PDF
    first = [r for r in rows if r[0] == w.results[0].drawing_no and r[2] == "INSTRUMENT"][:4]
    other = w.results[-1].drawing_no
    rows += [[other, r[1] + "?", *r[2:]] for r in first]
    table = ImportTable(source="Instrumentation_Gesamtliste_Beispiel.xlsx", sheet="Gesamtliste",
                        headers=["P&ID No.", "Tag", "Instrumententyp", "Service", "Location"], rows=rows,
                        link1="P&ID No.", link2="Tag")
    table.save(paths.config_dir())
    w.links.table = table
    w.links.fields = {"files": "Zeichnungsnr.", "tags": "Tag"}
    w.links._build()
    w._relink()
    w.page.files.table.selectRow(0)
    wait(app, 1.5)
    w.sources = ["PID Plots (Beispiel)"]               # keine Pfade aus dem Benutzerordner im Bild
    w._update_bands()
    # Listenspalten der Tag-Tabelle fuer das Bild hinter "Seiten" holen (nur Ansicht im Temp-Datenordner)
    th = w.page.tags.table.horizontalHeader()
    for i, col in enumerate(range(len(mw.TAG_COLS), len(w.page.tags.headers))):
        th.moveSection(th.visualIndex(col), 4 + i)
    wait(app, 0.3)

    rb = w.ribbon.buttons
    group_of = {}
    for key, b in rb.items():
        p = b.parentWidget()
        while p is not None and not isinstance(p, RibbonGroup):
            p = p.parentWidget()
        group_of[key] = p

    def group_fig(name: str, key: str, caption: str = "") -> Figure:
        g = group_of[key]
        r = united([g], w).adjusted(-6, -4, 6, 4)
        return Figure(name, w, r, caption)

    steps = []

    # --- Ueberblick -------------------------------------------------------------------------------------------------
    page = w.page
    f = Figure("overview", w, caption="Hauptfenster mit Beispiel-PDFs")
    titles = {g.title.text(): g for g in w.ribbon_fold.groups}
    for title, text in (("Projekt", "Projekt wählen, Projektmodus, Rohrleitungen, Projektdefinitionen, Pfade, "
                                    "Einstellungen."),
                        ("1  Einlesen", "PDFs einlesen und Excel-Liste für den Datenlink importieren."),
                        ("2  Ansicht", "Blätter wechseln, Viewer auf den 2. Monitor, Tabellen-Vorschau."),
                        ("3  Prüfen", "Fundstellen, Filter, Tabelle bearbeiten, Review speichern."),
                        ("4  Review / Redline", "Redline-PDF und Review-Excel erzeugen."),
                        ("5  Export", "Alle Dateien und Tags als Excel oder CSV."),
                        ("Web", "Web-Server für Kollegen, Offline-Bericht."),
                        ("Hilfe", "Dieses Handbuch, Info und Sprache.")):
        f.mark(titles[title].title, f"Menüband: {title.replace('  ', ' ')}", text)
    f.mark(page.header, "Kopfband", "Projekt, Quelle, Anzahl PDFs, Tags, Fehler und (Projektmodus) Abweichungen.")
    f.mark(page.files, "Tabelle 1 – Dateien", "Eine Zeile je PDF mit Schriftfeld-Werten. Auswahl einer Zeile lädt "
                                              "Tags und PDF.")
    f.mark(page.tags, "Tabelle 2 – Tags der gewählten PDF", "Alle Tags mit Anzahl, Seiten, Review-Spalten und – mit "
                                                             "Datenlink – Spalten aus der Excel-Liste.")
    f.mark(page.viewer, "PDF-Viewer", "Seite mit farbigen Rahmen an den Fundstellen; Klick auf einen Tag zoomt hin.")
    steps.append({"id": "overview", "title": "Überblick – das Hauptfenster",
                  "intro": "So ist das Fenster aufgebaut. Die Gruppen im Menüband entsprechen den Arbeitsschritten; "
                           "ein Klick auf die dunkelblaue Gruppenüberschrift klappt eine Gruppe ein oder aus.",
                  "figs": [f.save(out)]})

    # --- Schritt 1: Projekt ----------------------------------------------------------------------------------------
    f = group_fig("project", "project_pick", "Menüband, Gruppe „Projekt“")
    for key, title, text in (
            ("project_pick", "Projekt wählen", "Projekt anlegen, öffnen oder aus P3D Tag Compliance übernehmen "
                                               "(pidtag_project.db wird nur gelesen)."),
            ("project_mode", "Projektmodus an/aus", "Prüft jeden Tag gegen die Projektdefinitionen. An = Symbol grün; "
                                                    "Spalten „Projekt-Prüfung“ und „Projekt-Hinweis“ erscheinen."),
            ("pipes", "Rohrleitungen an/aus", "Rohrleitungsnummern mit in die Tag-Liste übernehmen; Umschalten liest "
                                              "die PDFs neu ein."),
            ("project_defs", "Projektdefinitionen …", "Codelisten, Listen, Tag-Strukturen und Prüfregeln im "
                                                      "Kachel-Editor bearbeiten; Excel-Export/-Import."),
            ("paths", "Pfade", "Quellordner (für „Quellordner scannen“) und Exportordner festlegen."),
            ("patterns", "Tag-Muster", "tag_patterns.json öffnen: Erkennungsmuster je Tag-Typ."),
            ("settings_menu", "Einstellungen", "Layer für Review im PDF (Redline-Kommentare auf eigener PDF-Ebene).")):
        f.mark(rb[key], title, text)
    steps.append({"id": "project", "title": "Projekt einrichten",
                  "intro": "Einmal je Projekt: Projekt wählen und bei Bedarf den Projektmodus einschalten. Ohne Projekt "
                           "arbeitet das Tool im Standardmodus mit den Tag-Mustern.",
                  "figs": [f.save(out)]})

    # --- Schritt 2: Einlesen ---------------------------------------------------------------------------------------
    f = group_fig("read", "scan", "Menüband, Gruppe „1 Einlesen“")
    for key, title, text in (
            ("scan", "Quellordner scannen", "Alle PDFs der Quellordner (aus „Pfade“) samt Unterordnern einlesen. "
                                            "Taste F5. Ein Fortschrittsfenster zeigt den Stand."),
            ("folder", "Ordner öffnen …", "Einen beliebigen Ordner mit PDF-Plots einlesen."),
            ("files", "Dateien öffnen …", "Einzelne PDF-Dateien wählen."),
            ("data_link", "Liste importieren", "Excel-Liste für den Datenlink importieren – siehe Schritt 3.")):
        f.mark(rb[key], title, text)
    figs = [f.save(out)]
    ft = page.files.table
    r = united([page.files], w).adjusted(-4, -4, 4, 4)
    f = Figure("files", w, r, "Tabelle 1 – Dateien nach dem Einlesen")
    f.mark(page.files.filter, "Blattfilter", "Sucht in allen Spalten der Dateiliste.")
    strip = page.files.layout().itemAt(1).widget()
    f.mark(strip.buttons["mark_all"], "Alle markieren", "Alle PDFs markieren, z. B. für den Review.")
    f.mark(strip.buttons["review"], "Review markierte …", "Redline und Review-Excel für die markierten PDFs (Schritt 6).")
    f.mark(ft.horizontalHeader(), "Spaltenkopf mit Filterzeile", "Klick sortiert, Feld darunter filtert, Doppelklick "
                                                                 "im Feld wählt Werte. Rechtsklick: Spaltenmenü.")
    f.mark(ft.viewport(), "PDF wählen", "Zeile anklicken: Tag-Tabelle und Viewer zeigen diese PDF. Mehrere mit Strg- "
                                        "oder Umschalt-Klick markieren.",
           QRect(0, 0, ft.viewport().width(), min(ft.viewport().height(), 3 * ft.rowHeight(0) + 2)))
    f.mark(page.files.admin, "Tabellenansicht", "Ansicht speichern, laden, zurücksetzen; der Regler rechts zoomt.")
    f.mark(page.tag_filter_box, "Filter der Tag-Tabelle", "Sucht in allen Spalten der Tags der gewählten PDF.")
    figs.append(f.save(out))
    steps.append({"id": "read", "title": "PDFs einlesen",
                  "intro": "PDF-Plots einlesen. Danach steht je PDF eine Zeile in Tabelle 1; die erste PDF wird "
                           "gewählt und angezeigt.", "figs": figs})

    # --- Schritt 3: Datenlink – Liste importieren ------------------------------------------------------------------
    dlg_table = ImportTable(**json.loads(json.dumps(table.__dict__)))
    dlg = TileEditorWindow(dlg_table, w, maximized=False)
    dlg.setWindowModality(Qt.NonModal)
    dlg.setAttribute(Qt.WA_DontShowOnScreen)
    dlg.resize(1600, 900)
    dlg.open()
    wait(app, 0.8)
    f = Figure("import", dlg, caption="Liste importieren › Excel-Liste importieren … – Kachel-Editor im Vollfenster "
                                      "(Beispielliste)")
    f.mark(dlg.source_label, "Quelle", "Gewählte Excel-Datei und Blatt (Blatt „Gesamtliste“ wird vorgeschlagen).")
    f.mark(dlg.b_other, "Andere Excel-Liste …", "Andere Datei oder anderes Blatt einlesen; die Anpassung und die "
                                                "Datenlinks werden darauf angewendet.")
    f.mark(dlg.b_save_cfg, "Anpassung speichern / laden", "Alle Schritte als Datei sichern und auf die nächste "
                                                         "Version der Liste anwenden.")
    f.mark(dlg.b_excel, "Als Excel speichern …", "Die angepasste Liste als kompatible Excel-Datei speichern.")
    f.mark(dlg.link_boxes[1], "Datenlink 1 → Tabelle 1 (Dateien)", "Spalte der Liste mit der Zeichnungsnummer, z. B. "
                                                                   "„P&ID No.“.")
    f.mark(dlg.link_boxes[2], "Datenlink 2 → Tabelle 2 (Tags)", "Spalte der Liste mit dem Tag, z. B. „Tag“.")
    if dlg.panel is not None:
        f.mark(dlg.panel.ribbon, "Bereich 1: Menüband des Kachel-Editors", "Start / Umwandeln / Spalte hinzufügen: "
                                                                          "rückgängig, ausblenden, Export ja/nein, "
                                                                          "gruppieren, teilen, ersetzen, Wenn-dann …")
        if dlg.panel.quick is not None:
            f.mark(dlg.panel.quick, "Kacheln = Spalten", "Ziehen = verschieben, Doppelklick = umbenennen, Kachel in "
                                                         "„Nicht exportiert“ = wird nicht übergeben.")
    if dlg.deck.isVisible():
        f.mark(dlg.deck, "Bereich 2: Seitenleiste", "Aktive Kachel, Gruppe und Verlauf aller Schritte "
                                                    "(einklappbar, als Fenster lösbar).")
    h = dlg.view.horizontalHeader()
    f.mark(h, "Bereich 3: Datentabelle", "Die Liste, wie sie übergeben wird. Rechtsklick auf einen Spaltenkopf: "
                                         "„Als Datenlink 1/2 setzen“ – gesetzte Spalten werden dunkelgrün.",
           section_rect(h, 0).united(section_rect(h, 1)))
    f.mark(dlg.ok_button, "Übernehmen und verlinken", "Speichert Liste und Anpassung und übergibt sie an das Tool.")
    steps.append({"id": "import", "title": "Excel-Liste importieren (Datenlink)",
                  "intro": "Optional: eine Excel-Liste – z. B. die Instrumenten-Gesamtliste – einlesen und im "
                           "Kachel-Editor (Vollfenster) zu einer passenden Importliste anpassen; dann die beiden "
                           "Schlüsselspalten festlegen.", "figs": [f.save(out)]})
    dlg.dirty = False
    dlg.close()

    # --- Schritt 4: Datenlink-Feld in den Tabellen -----------------------------------------------------------------
    figs = []
    fh = page.files.table.horizontalHeader()
    th = page.tags.table.horizontalHeader()
    r = united([page.files, page.tags], w).adjusted(-4, -4, 4, 4)
    r.setHeight(min(r.height(), united([page.tags.table], w).top() - r.top() + 160))
    f = Figure("link_fields", w, r, "Datenlink-Felder gesetzt: Köpfe dunkelgrün, Listenspalten angefügt")
    files_headers, tag_headers = page.files.headers, page.tags.headers
    f.mark(fh, "Datenlink-Feld Tabelle 1", "Rechtsklick auf „Zeichnungsnr.“ › „als Datenlink-Feld setzen“ – der Kopf "
                                           "wird dunkelgrün.", section_rect(fh, files_headers.index("Zeichnungsnr.")))
    f.mark(th, "Datenlink-Feld Tabelle 2", "Rechtsklick auf „Tag“ › „als Datenlink-Feld setzen“.",
           section_rect(th, tag_headers.index("Tag")))
    f.mark(th, "Spalten aus der Liste", "„Datenlink-Treffer“ (0 = Tag fehlt in der Liste) und alle übergebenen "
                                       "Spalten der Liste; gleichnamige mit „ (Liste)“. Spalten bei Bedarf über "
                                       "Rechtsklick › Spalten … nach vorne holen.",
           section_rect(th, len(mw.TAG_COLS)).united(section_rect(th, len(tag_headers) - 1)).intersected(
               QRect(0, 0, th.viewport().width(), th.height())))
    figs.append(f.save(out))
    menu = QMenu()
    page.tags.table._shared_header_menu_hook(menu, tag_headers.index("Tag"))
    page.tags.table._shared_header_menu_hook(menu, tag_headers.index("Typ"))
    menu.setAttribute(Qt.WA_DontShowOnScreen)
    menu.adjustSize()
    menu.show()
    wait(app, 0.2)
    f = Figure("link_menu", menu, caption="Rechtsklick auf einen Spaltenkopf (Ausschnitt mit den Datenlink-Einträgen)")
    acts = [a for a in menu.actions() if not a.isSeparator()]
    f.mark(menu, "Datenlink-Feld entfernen", "Erscheint auf dem gesetzten Feld.", menu.actionGeometry(acts[0]))
    f.mark(menu, "Als Datenlink-Feld setzen", "Auf einer anderen Grundspalte: macht sie zum Datenlink-Feld.",
           menu.actionGeometry(acts[2]))
    f.mark(menu, "Datenlink: Importtabelle …", "Öffnet die Importtabelle im Kachel-Editor.",
           menu.actionGeometry(acts[1]))
    figs.append(f.save(out))
    menu.close()
    steps.append({"id": "link", "title": "Datenlink-Feld in den Tabellen setzen",
                  "intro": "Je Tabelle ein Feld festlegen, das zur Liste passt. Sobald Datenlink und Feld gesetzt "
                           "sind, erscheinen die Listenspalten. Abgleich ohne Groß-/Kleinschreibung; ohne exakten "
                           "Treffer zählt die Endung ab einem Bindestrich („203-17-TI-300“ ↔ „TI-300“).",
                  "figs": figs})

    # --- Schritt 5: Ansicht & Pruefen ------------------------------------------------------------------------------
    figs = []
    f = Figure("check_ribbon", w, united([group_of["sheet_tags"], group_of["prev"]], w).adjusted(-6, -4, 6, 4),
               "Menüband, Gruppen „2 Ansicht“ und „3 Prüfen“")
    for key, title, text in (
            ("sheet_all", "Alle Tags", "Blatt mit den Tags aller PDFs."),
            ("monitor", "Viewer 2. Monitor", "PDF-Viewer in eigenem Fenster."),
            ("next", "Fundstelle weiter", "Nächste Fundstelle des gewählten Tags (F3, zurück: Umschalt+F3)."),
            ("dups", "Nur doppelte Tags", "Nur mehrfach vorkommende Tags (gelb)."),
            ("deviations", "Nur Projektabweichungen", "Nur Tags mit Befund (Projektmodus)."),
            ("edit", "Tabelle bearbeiten", "Review-Spalten freischalten."),
            ("save", "Review speichern", "Review-Einträge sichern (Strg+S).")):
        f.mark(rb[key], title, text)
    figs.append(f.save(out))
    tstrip = page.tags.layout().itemAt(1).widget()
    r = united([page.tags, page.viewer], w).adjusted(-4, -4, 4, 4)
    f = Figure("check", w, r, "Tag-Tabelle mit Leiste und PDF-Viewer")
    b = tstrip.buttons
    for key, title, text in (
            ("scan_fields", "Aus PDF-Scan übernehmen", "Ersteller, Checked, Rev … aus dem Schriftfeld als Spalten "
                                                       "anfügen."),
            ("autofill", "Autofill OK", "Alle OK-Tags: Review = OK, User, Datum; leeres WPO = Checked."),
            ("edit", "Bearbeiten", "Review, Änderung, Neuer Wert, Bemerkung, WPO eintragen (Datum/User automatisch)."),
            ("save", "Speichern", "Review-Einträge dieser PDF speichern."),
            ("duplicates", "Nur doppelte", "Nur Tags, die mehrfach in der PDF stehen."),
            ("filter_reset", "Filter zurücksetzen", "Alle Filter der Tag-Tabelle aufheben."),
            ("next", "Fundstelle", "Zur nächsten Fundstelle springen (◀ zurück)."),
            ("excel_tags", "Excel", "Tag-Tabelle als Excel sichern (mit Listenspalten)."),
            ("preview_tags", "Vorschau", "Excel-Export vorher ansehen.")):
        f.mark(b[key], title, text)
    tv = page.tags.table.viewport()
    f.mark(tv, "Tag anklicken", "Markiert den Tag im Viewer und zoomt hin; gelbe Zeilen = doppelte Tags.",
           QRect(0, 0, tv.width(), min(tv.height(), 3 * page.tags.table.rowHeight(0) + 2)))
    f.mark(page.viewer.strip, "Viewer-Leiste", "Einpassen, Zoom, Drehen, Monochrom, Seiten, Fundstellen, Redline, "
                                               "PDF öffnen, 2. Monitor.")
    f.mark(page.viewer.preview, "PDF-Ansicht", "Rahmen grün = korrekt, rot = fehlerhaft, gelb = doppelt. Mausrad "
                                               "zoomt, Doppelklick passt ein.")
    figs.append(f.save(out))
    steps.append({"id": "check", "title": "Ansehen und prüfen",
                  "intro": "PDF in Tabelle 1 wählen, Tags durchgehen, Fundstellen im Viewer prüfen und den Review "
                           "eintragen.", "figs": figs})

    # --- Schritt 6: Review / Redline -------------------------------------------------------------------------------
    figs = []
    f = group_fig("review_ribbon", "review", "Menüband, Gruppe „4 Review / Redline“")
    for key, title, text in (
            ("review", "Review Auswahl/Bulk …", "Redline und Review-Excel für markierte oder alle PDFs."),
            ("redline", "Redline-PDF gewählte PDF", "Kopie der PDF mit Rahmen, Pos.-Nr. und Kommentaren "
                                                    "(Tabellenfilter gilt)."),
            ("review_xlsx", "Review-Excel gewählte PDF", "Excel mit einer Zeile je Fundstelle und Prüfstatus.")):
        f.mark(rb[key], title, text)
    figs.append(f.save(out))
    rd = ReviewDialog(1, len(w.results), w, linked=True)
    rd.setAttribute(Qt.WA_DontShowOnScreen)
    rd.cb_multitag.setChecked(True)
    rd.folder.setText(r"…\Exporte")
    rd.show()
    wait(app, 0.3)
    f = Figure("review_dialog", rd, caption="Review Auswahl/Bulk …")
    f.mark(rd.rb_marked.parentWidget(), "PDFs", "Markierte oder alle gescannten PDFs.")
    f.mark(rd.cb_redline, "Redline-PDF je PDF", "Farben wie im Viewer.")
    f.mark(rd.cb_multitag, "Multi-Tag-PDF je PDF", "Roter Eintrag über jedem doppelten Tag (braucht Datenlink 2).")
    f.mark(rd.cb_excel_each, "Review-Excel je PDF", "Pos.-Nr., Kommentar, Prüfstatus, Bemerkung.")
    f.mark(rd.cb_excel_total, "Review-Excel gesamt", "Eine Mappe über alle gewählten PDFs.")
    f.mark(rd.folder, "Zielordner", "Wohin geschrieben wird; optional Unterordner mit Zeitstempel.")
    from PySide6.QtWidgets import QDialogButtonBox
    f.mark(rd.findChild(QDialogButtonBox), "Review starten", "Erzeugt die Ausgaben; die Original-PDFs bleiben "
                                                             "unverändert.")
    figs.append(f.save(out))
    rd.close()
    steps.append({"id": "review", "title": "Review und Redline erzeugen",
                  "intro": "Ergebnisse als Redline-PDF und Review-Excel ausgeben – für die gewählte PDF oder viele "
                           "PDFs auf einmal.", "figs": figs})

    # --- Schritt 7: Export / Web -----------------------------------------------------------------------------------
    f = Figure("export", w, united([group_of["xlsx"], group_of["web_server"], group_of["help"]], w)
               .adjusted(-6, -4, 6, 4), "Menüband, Gruppen „5 Export“, „Web“, „Hilfe“")
    for key, title, text in (
            ("xlsx", "Export Excel …", "Blätter „Dateien“ und „Tags“ über alle PDFs."),
            ("csv", "Export CSV …", "Tags plus _Dateien.csv (Trennzeichen ;)."),
            ("open_exports", "Exportordner", "Ordner mit allen Ausgaben öffnen."),
            ("web_server", "Web-Server", "Web-Version für Kollegen im Firmennetz starten/stoppen."),
            ("web_report", "Offline-Bericht …", "Eine HTML-Datei mit Tabellen und Viewer zum Weitergeben."),
            ("help", "Handbuch", "Dieses Handbuch.")):
        f.mark(rb[key], title, text)
    steps.append({"id": "export", "title": "Exportieren und weitergeben",
                  "intro": "Gesamtlisten exportieren oder die Ergebnisse über Web-Server bzw. Offline-Bericht "
                           "teilen. Jede Tabelle hat zusätzlich das Excel-Symbol in ihrer Ecke.",
                  "figs": [f.save(out)]})

    steps += topic_steps(app, w, out, group_fig)
    order = ["overview", "project", "paths", "read", "import", "link", "listcheck", "types", "check", "twotag",
             "multitag", "review", "preview", "export", "tables"]
    steps.sort(key=lambda s: order.index(s["id"]))

    w.page.store = None
    w.close()
    js = ("/* Erzeugt von tools/make_help_workflow.py - nicht von Hand bearbeiten. */\n"
          "const WF = " + json.dumps(steps, ensure_ascii=False, indent=1) + ";\n")
    (HELP / "workflow.js").write_text(js, encoding="utf-8")
    print(sum(len(s["figs"]) for s in steps), "Bilder,", sum(len(f["marks"]) for s in steps for f in s["figs"]),
          "Markierungen ->", HELP)


if __name__ == "__main__":
    main()
