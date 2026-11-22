// Add columns from another list: look a tile's value up in a column of another Excel / CSV file and bring columns over.
// The first matching row of the list wins; a value that is not found gets the "nicht gefunden" text. The other file is only read.
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

Popup {
    id: dlg
    property int row: -1
    property var sheets: []
    property var headers: []
    property var preview: ({ ok: false, error: "", rows: [], found: 0, total: 0 })
    property string applyError: ""
    property string fileError: ""

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0
    margins: 6
    padding: 8
    width: Math.min(380, (Overlay.overlay ? Overlay.overlay.width : 380) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 5 }

    function takeLabels() {
        var out = []
        for (var i = 0; i < takeRepeater.count; i++) { var it = takeRepeater.itemAt(i); if (it && it.checked) out.push(dlg.headers[i]) }
        return out
    }
    function options() {
        return { file: fileField.text, sheet: sheetBox.currentText, matchLabel: matchBox.currentText, takeLabels: takeLabels(),
                 matchCase: caseCheck.checked, missingText: missingField.text }
    }
    function refresh() {
        if (row >= 0 && headers.length > 0 && takeLabels().length > 0) preview = columnEditorController.previewLookup(row, options())
        else preview = { ok: false, error: headers.length ? "Zu übernehmende Spalte(n) anhaken." : "", rows: [], found: 0, total: 0 }
    }
    function loadFile() {
        fileError = ""; sheets = []; headers = []
        var r = columnEditorController.lookupSheets(fileField.text)
        if (!r.ok) { fileError = r.error; refresh(); return }
        sheets = r.sheets
        sheetBox.currentIndex = 0
        loadSheet()
    }
    function loadSheet() {
        var r = columnEditorController.lookupHeaders(fileField.text, sheetBox.currentText)
        fileError = r.ok ? "" : r.error
        headers = r.ok ? r.headers : []
        matchBox.currentIndex = 0
        refresh()
    }
    function openFor(r) {
        row = r
        applyError = ""; fileError = ""; sheets = []; headers = []
        fileField.text = ""; missingField.text = ""; caseCheck.checked = false
        refresh()
        open()
    }

    FileDialog {
        id: picker
        title: "Andere Liste wählen"
        nameFilters: ["Listen (*.xlsx *.xlsm *.csv)", "Alle Dateien (*)"]
        onAccepted: { fileField.text = selectedFile.toString().replace(/^file:\/\/\//, ""); dlg.loadFile() }
    }

    contentItem: Flickable {
        clip: true
        implicitHeight: Math.min(body.implicitHeight, 470)
        contentHeight: body.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: body
            width: parent.width
            spacing: 5
            Text { text: "Spalten aus einer anderen Liste"; font.bold: true; font.pixelSize: 12 }
            Row {
                spacing: 6
                Text { text: "Listendatei"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 70 }
                TextField { id: fileField; width: 215; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "Pfad zu .xlsx / .csv"; Accessible.name: "Listendatei"; onEditingFinished: dlg.loadFile() }
                Button { text: "…"; implicitHeight: 26; implicitWidth: 30; Accessible.name: "Listendatei suchen"; onClicked: picker.open() }
            }
            Text { visible: dlg.fileError !== ""; text: dlg.fileError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                visible: dlg.sheets.length > 1; spacing: 6
                Text { text: "Blatt"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 70 }
                ComboBox { id: sheetBox; model: dlg.sheets; implicitWidth: 250; implicitHeight: 26; font.pixelSize: 11; Accessible.name: "Blatt der Liste"; onActivated: dlg.loadSheet() }
            }
            Row {
                visible: dlg.headers.length > 0; spacing: 6
                Text { text: "Abgleichen mit"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 70 }
                ComboBox { id: matchBox; model: dlg.headers; implicitWidth: 250; implicitHeight: 26; font.pixelSize: 11; Accessible.name: "Spalte der Liste mit denselben Werten"; onActivated: dlg.refresh() }
            }
            Text { visible: dlg.headers.length > 0; text: "Übernehmen:"; font.pixelSize: 10; color: "#52606d" }
            Repeater {
                id: takeRepeater
                model: dlg.headers
                delegate: CheckBox { text: modelData; font.pixelSize: 11; implicitHeight: 24; onToggled: dlg.refresh() }
            }
            Row {
                visible: dlg.headers.length > 0; spacing: 6
                Text { text: "Nicht gefunden"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 70 }
                TextField { id: missingField; width: 150; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "(leer)"; Accessible.name: "Text, wenn ein Wert fehlt"; onTextEdited: dlg.refresh() }
            }
            CheckBox { id: caseCheck; visible: dlg.headers.length > 0; text: "Groß-/Kleinschreibung beachten"; font.pixelSize: 11; onToggled: dlg.refresh() }
            Text { visible: !!preview.error; text: preview.error || ""; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Text {
                visible: !preview.error && preview.total > 0
                text: (preview.found || 0).toLocaleString() + " von " + (preview.total || 0).toLocaleString() + " Vorschauzellen stehen in der Liste"
                font.pixelSize: 10; font.bold: true; color: "#34495e"; wrapMode: Text.Wrap; width: parent.width
            }
            Repeater {
                model: (preview.rows || []).slice(0, 4)
                delegate: Row {
                    spacing: 6
                    Text { text: modelData.before; font.pixelSize: 10; width: 150; elide: Text.ElideRight }
                    Text { text: "→"; font.pixelSize: 10 }
                    Text { text: modelData.after === "" ? "(leer)" : modelData.after; font.pixelSize: 10; width: 150; elide: Text.ElideRight }
                }
            }
            Text { visible: dlg.applyError !== ""; text: dlg.applyError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                spacing: 6
                Button {
                    text: "Anwenden"; implicitHeight: 26; font.pixelSize: 11
                    enabled: !!preview.ok
                    onClicked: { dlg.applyError = columnEditorController.applyLookup(dlg.row, dlg.options()); if (dlg.applyError === "") dlg.close() }
                }
                Button { text: "Abbrechen"; implicitHeight: 26; font.pixelSize: 11; onClicked: dlg.close() }
            }
        }
    }
}
