import json
import sys
from pathlib import Path

T = {}


def a(sec, rows):
    for de, en, fr in rows:
        T.setdefault(sec, {})[de] = {"en": en, "fr": fr}


a("Menüband", [
    ("P&ID-PDF-Reader", "P&ID PDF Reader", "Lecteur PDF P&ID"),
    ("1  Einlesen", "1  Import", "1  Importer"), ("2  Prüfen", "2  Check", "2  Contrôler"),
    ("3  Review / Redline", "3  Review / Redline", "3  Revue / Redline"), ("4  Export", "4  Export", "4  Export"),
    ("Ansicht", "View", "Affichage"), ("Einstellungen", "Settings", "Paramètres"), ("Hilfe", "Help", "Aide"),
    ("Quellordner\nscannen", "Scan source\nfolders", "Analyser les\ndossiers source"),
    ("Quellordner scannen", "Scan source folders", "Analyser les dossiers source"),
    ("Ordner\nöffnen …", "Open\nfolder …", "Ouvrir un\ndossier …"), ("Ordner öffnen …", "Open folder …", "Ouvrir un dossier …"),
    ("Dateien\nöffnen …", "Open\nfiles …", "Ouvrir des\nfichiers …"), ("Dateien öffnen …", "Open files …", "Ouvrir des fichiers …"),
    ("Rohr-\nleitungen", "Pipe\nlines", "Tuyau-\nteries"),
    ("Rohrleitungsnummern mit einlesen", "Include pipe line numbers", "Inclure les numéros de ligne"),
    ("Rohrleitungsnummern (z. B. TFHR_SS01_001_1\") als Typ „Rohrleitung“ in die Tag-Liste übernehmen – "
     "waagerecht und senkrecht beschriftet. Umschalten liest die PDFs neu ein.",
     "Add pipe line numbers (e.g. TFHR_SS01_001_1\") to the tag list as type “Rohrleitung” – labelled "
     "horizontally or vertically. Switching re-reads the PDFs.",
     "Ajouter les numéros de ligne (p. ex. TFHR_SS01_001_1\") à la liste des tags, type « Rohrleitung » – "
     "écrits horizontalement ou verticalement. Le changement relit les PDF."),
    ("Fundstelle\nzurück", "Previous\noccurrence", "Occurrence\nprécédente"), ("Fundstelle zurück", "Previous occurrence", "Occurrence précédente"),
    ("Fundstelle\nweiter", "Next\noccurrence", "Occurrence\nsuivante"), ("Fundstelle weiter", "Next occurrence", "Occurrence suivante"),
    ("Nur doppelte\nTags", "Duplicate\ntags only", "Tags en double\nseulement"), ("Nur doppelte Tags", "Duplicate tags only", "Tags en double seulement"),
    ("Filter\nzurücksetzen", "Reset\nfilters", "Réinitialiser\nles filtres"), ("Filter zurücksetzen", "Reset filters", "Réinitialiser les filtres"),
    ("Tabelle\nbearbeiten", "Edit\ntable", "Modifier\nle tableau"), ("Tabelle bearbeiten", "Edit table", "Modifier le tableau"),
    ("Review\nspeichern", "Save\nreview", "Enregistrer\nla revue"), ("Review speichern", "Save review", "Enregistrer la revue"),
    ("Review\nAuswahl/Bulk …", "Review\nselection/bulk …", "Revue\nsélection/lot …"), ("Review Auswahl/Bulk …", "Review selection/bulk …", "Revue sélection/lot …"),
    ("Redline-PDF\ngewählte PDF", "Redline PDF\nselected PDF", "PDF redline\nPDF choisi"), ("Redline-PDF gewählte PDF", "Redline PDF selected PDF", "PDF redline PDF choisi"),
    ("Review-Excel\ngewählte PDF", "Review Excel\nselected PDF", "Excel de revue\nPDF choisi"), ("Review-Excel gewählte PDF", "Review Excel selected PDF", "Excel de revue PDF choisi"),
    ("Export\nExcel …", "Export\nExcel …", "Exporter\nExcel …"), ("Export Excel …", "Export Excel …", "Exporter Excel …"),
    ("Export\nCSV …", "Export\nCSV …", "Exporter\nCSV …"), ("Export CSV …", "Export CSV …", "Exporter CSV …"),
    ("Export-\nordner", "Export\nfolder", "Dossier\nd'export"), ("Export- ordner", "Export folder", "Dossier d'export"),
    ("PID-Tags", "P&ID tags", "Tags P&ID"), ("Alle Tags", "All tags", "Tous les tags"),
    ("Viewer\n2. Monitor", "Viewer\n2nd monitor", "Visionneuse\n2e écran"), ("Viewer 2. Monitor", "Viewer 2nd monitor", "Visionneuse 2e écran"),
    ("Tabellen-\nVorschau …", "Table\npreview …", "Aperçu du\ntableau …"), ("Tabellen- Vorschau …", "Table preview …", "Aperçu du tableau …"),
    ("Pfade", "Paths", "Chemins"), ("Tag-\nMuster", "Tag\npatterns", "Modèles\nde tags"), ("Tag- Muster", "Tag patterns", "Modèles de tags"),
    ("Tag-Muster", "Tag patterns", "Modèles de tags"), ("Handbuch", "Manual", "Manuel"), ("Info", "About", "À propos"),
    ("Sprache", "Language", "Langue"),
    ("Sprache der Oberfläche: Deutsch, English, Français", "User interface language: Deutsch, English, Français",
     "Langue de l'interface : Deutsch, English, Français"),
])
a("Blätter", [
    ("Plant-3D-PDF-Plots: Dateien, Tags je PDF und Seitenvorschau", "Plant 3D PDF plots: files, tags per PDF and page preview",
     "Tracés PDF Plant 3D : fichiers, tags par PDF et aperçu"),
    ("Tags aller gescannten PDFs", "Tags of all scanned PDFs", "Tags de tous les PDF analysés"),
    ("Dateien", "Files", "Fichiers"), ("Tags", "Tags", "Tags"), ("Tags der gewählten PDF", "Tags of the selected PDF", "Tags du PDF choisi"),
    ("Tags aller PDFs", "Tags of all PDFs", "Tags de tous les PDF"), ("In dieser Tabelle filtern …", "Filter this table …", "Filtrer ce tableau …"),
    ("{0} / {1} Zeilen", "{0} / {1} rows", "{0} / {1} lignes"), ("Blatt schließen", "Close sheet", "Fermer la feuille"),
    ("Hilfe zu dieser Ansicht (F1)", "Help for this view (F1)", "Aide pour cette vue (F1)"),
    ("QUELLE", "SOURCE", "SOURCE"), ("PDFS", "PDFS", "PDF"), ("TAGS", "TAGS", "TAGS"), ("FEHLER", "ERRORS", "ERREURS"),
    ("Alle markieren", "Select all", "Tout sélectionner"), ("Alle PDFs der Liste markieren", "Select all PDFs in the list",
                                                             "Sélectionner tous les PDF de la liste"),
    ("Review markierte …", "Review selected …", "Revue de la sélection …"),
    ("Markierte PDFs prüfen: Redline-PDF, Excel je PDF, Gesamt-Excel", "Review selected PDFs: redline PDF, Excel per PDF, overall Excel",
     "Contrôler les PDF sélectionnés : PDF redline, Excel par PDF, Excel global"),
    ("Excel", "Excel", "Excel"), ("Dateiliste als Excel sichern", "Save file list as Excel", "Enregistrer la liste des fichiers en Excel"),
    ("Bearbeiten", "Edit", "Modifier"), ("Speichern", "Save", "Enregistrer"), ("Speichern *", "Save *", "Enregistrer *"),
    ("Bearbeiten-Modus: Review, Änderung, Neuer Wert, Bemerkung, WPO eintragen (Datum und User werden automatisch gesetzt)",
     "Edit mode: enter Review, Change, New value, Remark, WPO (date and user are set automatically)",
     "Mode édition : saisir Revue, Modification, Nouvelle valeur, Remarque, WPO (date et utilisateur automatiques)"),
    ("Review-Einträge dieser PDF speichern (Strg+S)", "Save the review entries of this PDF (Ctrl+S)",
     "Enregistrer les entrées de revue de ce PDF (Ctrl+S)"),
    ("Nur doppelte", "Duplicates only", "Doublons seulement"),
    ("Nur Tags zeigen, die mehrfach in der PDF vorkommen (gelb)", "Show only tags that occur more than once on a page (yellow)",
     "N'afficher que les tags présents plusieurs fois sur une page (jaune)"),
    ("Fundstelle", "Occurrence", "Occurrence"), ("Nächste Fundstelle (F3)", "Next occurrence (F3)", "Occurrence suivante (F3)"),
    ("Vorherige Fundstelle (Umschalt+F3)", "Previous occurrence (Shift+F3)", "Occurrence précédente (Maj+F3)"),
    ("Nächste Fundstelle (F3, oder erneut auf den Tag klicken)", "Next occurrence (F3, or click the tag again)",
     "Occurrence suivante (F3, ou cliquer de nouveau sur le tag)"),
    ("Tags der PDF als Excel sichern (Name: PDF + Zeitstempel)", "Save the PDF's tags as Excel (name: PDF + timestamp)",
     "Enregistrer les tags du PDF en Excel (nom : PDF + horodatage)"),
    ("Redline", "Redline", "Redline"), ("Redline-PDF mit den sichtbaren Tags", "Redline PDF with the visible tags",
                                         "PDF redline avec les tags visibles"),
    ("Tabelle als Excel sichern (sichtbare Spalten und gefilterte Zeilen)\nDateiname: PDF-Name bzw. Tabellenname + Zeitstempel",
     "Save table as Excel (visible columns and filtered rows)\nFile name: PDF or table name + timestamp",
     "Enregistrer le tableau en Excel (colonnes visibles, lignes filtrées)\nNom : nom du PDF ou du tableau + horodatage"),
    ("{0} doppelte Tag(s) gelb hinterlegt", "{0} duplicate tag(s) highlighted yellow", "{0} tag(s) en double surlignés en jaune"),
    ("Rechtsklick: Subtabs aus", "Right-click: subtabs off", "Clic droit : désactiver les sous-onglets"),
    ("Subtabs aus (zurück zur Gesamttabelle)", "Subtabs off (back to the full table)", "Désactiver les sous-onglets (tableau complet)"),
    ("Filter - {0}\nTippen filtert nach Inhalt, Doppelklick wählt exakte Werte.",
     "Filter - {0}\nTyping filters by content, double-click selects exact values.",
     "Filtre - {0}\nSaisir filtre le contenu, double-clic choisit des valeurs exactes."),
])
a("Spalten", [
    ("PDF", "PDF", "PDF"), ("Zeichnungsnr.", "Drawing no.", "N° de plan"), ("Erstellt (PDF)", "Created (PDF)", "Créé (PDF)"),
    ("Ersteller", "Author", "Auteur"), ("Checked", "Checked", "Vérifié"), ("Rev", "Rev", "Rév"), ("Rev-Datum", "Rev date", "Date rév"),
    ("Rev-Text", "Rev text", "Texte rév"), ("Plot-Benutzer", "Plot user", "Utilisateur du tracé"), ("Anzahl Tags", "Tag count", "Nombre de tags"),
    ("Fehler", "Error", "Erreur"), ("Typ", "Type", "Type"), ("Tag", "Tag", "Tag"), ("Anzahl", "Count", "Nombre"), ("Seiten", "Pages", "Pages"),
    ("Review", "Review", "Revue"), ("Änderung", "Change", "Modification"), ("Neuer Wert", "New value", "Nouvelle valeur"),
    ("Bemerkung", "Remark", "Remarque"), ("WPO", "WPO", "WPO"), ("Datum", "Date", "Date"), ("User", "User", "Utilisateur"),
])
a("PDF-Viewer", [
    ("Einpassen", "Fit", "Ajuster"),
    ("Ganze Seite zeigen (Doppelklick in die Vorschau)", "Show whole page (double-click in the preview)",
     "Afficher la page entière (double-clic dans l'aperçu)"),
    ("Vergrößern (Mausrad)", "Zoom in (mouse wheel)", "Agrandir (molette)"), ("Verkleinern (Mausrad)", "Zoom out (mouse wheel)", "Réduire (molette)"),
    ("Drehen", "Rotate", "Pivoter"), ("Ansicht 90° nach links drehen", "Rotate view 90° left", "Pivoter la vue de 90° à gauche"),
    ("Ansicht 90° nach rechts drehen", "Rotate view 90° right", "Pivoter la vue de 90° à droite"),
    ("Seite –", "Page –", "Page –"), ("Seite {0} / {1}", "Page {0} / {1}", "Page {0} / {1}"),
    ("Vorherige Seite (Bild ↑)", "Previous page (Page ↑)", "Page précédente (Page ↑)"),
    ("Nächste Seite (Bild ↓)", "Next page (Page ↓)", "Page suivante (Page ↓)"),
    ("Redline-PDF der gewählten PDF (sichtbare Tags)", "Redline PDF of the selected PDF (visible tags)", "PDF redline du PDF choisi (tags visibles)"),
    ("Öffnen", "Open", "Ouvrir"), ("PDF im Standardprogramm öffnen", "Open PDF in the default program", "Ouvrir le PDF dans le programme par défaut"),
    ("2. Monitor", "2nd monitor", "2e écran"),
    ("PDF-Viewer in eigenem Fenster auf dem zweiten Monitor zeigen", "Show the PDF viewer in its own window on the second monitor",
     "Afficher la visionneuse dans une fenêtre sur le deuxième écran"),
    ("PDF-Viewer ist auf dem zweiten Monitor.", "The PDF viewer is on the second monitor.", "La visionneuse PDF est sur le deuxième écran."),
    ("Viewer zurückholen", "Bring viewer back", "Rapatrier la visionneuse"),
    ("P3D PDF Reader – PDF-Viewer", "P3D PDF Reader – PDF viewer", "P3D PDF Reader – visionneuse PDF"),
])
a("Dialoge", [
    ("Review / Audit", "Review / audit", "Revue / audit"), ("PDFs", "PDFs", "PDF"),
    ("Markierte PDFs ({0})", "Selected PDFs ({0})", "PDF sélectionnés ({0})"),
    ("Alle gescannten PDFs ({0})", "All scanned PDFs ({0})", "Tous les PDF analysés ({0})"),
    ("Mehrere PDFs in der Dateiliste mit Strg- oder Umschalt-Klick markieren.", "Select several PDFs in the file list with Ctrl- or Shift-click.",
     "Sélectionner plusieurs PDF avec Ctrl- ou Maj-clic dans la liste."),
    ("Ausgaben", "Outputs", "Sorties"),
    ("Redline-PDF je PDF (Kommentar an jeder Fundstelle, doppelte Tags orange)",
     "Redline PDF per PDF (comment at every occurrence, duplicate tags orange)",
     "PDF redline par PDF (commentaire à chaque occurrence, doublons en orange)"),
    ("Review-Excel je PDF (Pos.-Nr., Review-Kommentar, Prüfstatus, Bemerkung)", "Review Excel per PDF (item no., review comment, status, remark)",
     "Excel de revue par PDF (n° de pos., commentaire, statut, remarque)"),
    ("Review-Excel gesamt über alle gewählten PDFs", "Overall review Excel for all selected PDFs", "Excel de revue global pour tous les PDF choisis"),
    ("Eigenen Unterordner „Review_<Zeitstempel>“ anlegen", "Create a subfolder \"Review_<timestamp>\"", "Créer un sous-dossier « Review_<horodatage> »"),
    ("Zielordner", "Target folder", "Dossier cible"), ("Review starten", "Start review", "Lancer la revue"),
    ("Pfade verwalten", "Manage paths", "Gérer les chemins"),
    ("PDF-Quellordner (werden beim Scan durchsucht, inkl. Unterordner)", "PDF source folders (searched when scanning, including subfolders)",
     "Dossiers source PDF (analysés avec leurs sous-dossiers)"),
    ("Hinzufügen", "Add", "Ajouter"), ("Entfernen", "Remove", "Supprimer"), ("Im Explorer", "In Explorer", "Dans l'Explorateur"),
    ("Export und Speicherorte", "Export and storage locations", "Export et emplacements"), ("Exportordner", "Export folder", "Dossier d'export"),
    ("Datenordner", "Data folder", "Dossier de données"), ("Konfiguration", "Configuration", "Configuration"), ("Logs", "Logs", "Journaux"),
    ("Datenordner über Umgebungsvariable P3D_PDFREADER_HOME änderbar.",
     "The data folder can be changed with the environment variable P3D_PDFREADER_HOME.",
     "Le dossier de données se change via la variable d'environnement P3D_PDFREADER_HOME."),
    ("Review-Einträge", "Review entries", "Entrées de revue"), ("Verwerfen", "Discard", "Ignorer"), ("Abbrechen", "Cancel", "Annuler"),
    ("Nur gefilterte ({0})", "Filtered only ({0})", "Filtrés seulement ({0})"), ("Alle Tags ({0})", "All tags ({0})", "Tous les tags ({0})"),
])

a("Tabellen-Kontextmenü", [
    ("Kopieren", "Copy", "Copier"), ("Zeile kopieren", "Copy row", "Copier la ligne"),
    ("Zeile mit Überschriften kopieren", "Copy row with headers", "Copier la ligne avec les en-têtes"),
    ("Nach diesem Wert filtern", "Filter by this value", "Filtrer sur cette valeur"),
    ("Filter dieser Spalte zurücksetzen", "Reset this column's filter", "Réinitialiser le filtre de cette colonne"),
    ("Alle Filter zurücksetzen", "Reset all filters", "Réinitialiser tous les filtres"),
    ("Spalten …", "Columns …", "Colonnes …"), ("Nach Excel …", "To Excel …", "Vers Excel …"),
    ("Spalten", "Columns", "Colonnes"), ("Spalte", "Column", "Colonne"), ("Anzeigen", "Show", "Afficher"),
    ("Nach oben", "Move up", "Monter"), ("Nach unten", "Move down", "Descendre"), ("Standard", "Default", "Par défaut"),
    ("Übernehmen", "Apply", "Appliquer"), ("Ja", "Yes", "Oui"), ("Nein", "No", "Non"),
    ("Rechtsklick: Spalten …", "Right-click: Columns …", "Clic droit : Colonnes …"),
    ("Projekt", "Project", "Projet"),
])

data = {"_info": "Schluessel = deutscher Originaltext (Standardsprache). Je Eintrag en/fr. Fehlende Texte bleiben deutsch."}
data.update(T)
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
print(sum(len(v) for v in T.values()), "Eintraege ->", out)
