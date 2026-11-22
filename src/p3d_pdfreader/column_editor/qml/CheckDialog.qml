// Check against a code list: a new calculated column says OK or NOT IN LIST for every cell of the tile.
// The list comes from the project definitions (building, system, function, pipe class ...), from the distinct values of another
// tile, or is typed / pasted. Also used to change the list of an existing step (editIndex >= 0).
import QtQuick
import QtQuick.Controls

Popup {
    id: dlg
    property int row: -1
    property int editIndex: -1
    property var lists: []                       // [{name, count}] ready-made lists
    property var columns: []                     // [{key, label}] for "Werte der Kachel"
    property var preview: ({ ok: false, error: "", bad: 0, total: 0, examples: [] })
    property string applyError: ""
    property string listName: ""

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0
    margins: 6
    padding: 8
    width: Math.min(360, (Overlay.overlay ? Overlay.overlay.width : 360) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 5 }

    function values() { return valuesArea.text.split(/[\n,;]+/).map(function (t) { return t.trim() }).filter(function (t) { return t !== "" }) }
    function options() { return { values: values(), listName: listName, ignoreCase: !caseCheck.checked, emptyOk: emptyCheck.checked, badText: badField.text } }
    function refresh() { if (row >= 0) preview = columnEditorController.previewCheck(row, options()) }
    function openFor(r, stepIndex) {
        editIndex = stepIndex === undefined ? -1 : stepIndex
        row = r
        lists = columnEditorController.codeLists()
        columns = columnEditorController.columnChoices()
        applyError = ""
        valuesArea.text = ""; listName = ""; caseCheck.checked = false; emptyCheck.checked = true; badField.text = "NICHT IN LISTE"
        if (editIndex >= 0) {
            var info = columnEditorController.stepInfo(editIndex)
            row = info.row
            valuesArea.text = (info.options.values || []).join("\n")
            listName = info.options.listName || ""
            caseCheck.checked = info.options.ignoreCase === false
            emptyCheck.checked = info.options.emptyOk !== false
            badField.text = info.options.badText || "NICHT IN LISTE"
        }
        refresh()
        open()
    }
    function useList(name) { listName = name; valuesArea.text = columnEditorController.codeListValues(name).join("\n"); refresh() }
    function useTile(i) {
        listName = "Werte von " + columns[i].label
        valuesArea.text = columnEditorController.columnDistinctValues(i).join("\n")
        refresh()
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
            Text { text: dlg.editIndex >= 0 ? "Schritt ändern: Gegen Codeliste prüfen" : "Gegen Codeliste prüfen"; font.bold: true; font.pixelSize: 12 }
            Text { text: "Spalte: " + (columns.length && row >= 0 && row < columns.length ? columns[row].label : ""); font.pixelSize: 10; color: "#52606d"; elide: Text.ElideRight; width: parent.width }
            Row {
                spacing: 6
                Text { text: "Liste übernehmen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 70 }
                ComboBox {
                    id: fromProject
                    model: [{ name: "aus Projektdefinitionen …" }].concat(dlg.lists.map(function (l) { return { name: l.name + "  (" + l.count + ")", raw: l.name } }))
                    textRole: "name"; implicitWidth: 250; implicitHeight: 26; font.pixelSize: 11
                    enabled: dlg.lists.length > 0
                    Accessible.name: "Liste aus den Projektdefinitionen"
                    onActivated: if (currentIndex > 0) dlg.useList(model[currentIndex].raw)
                }
            }
            Text { visible: dlg.lists.length === 0; text: "Hier sind keine Projektdefinitionen geladen: Werte einer Kachel nehmen oder eintippen / einfügen."; font.pixelSize: 10; color: "#7b8794"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                spacing: 6
                Text { text: "oder aus"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 70 }
                ComboBox {
                    model: [{ label: "Werte einer Kachel …" }].concat(dlg.columns)
                    textRole: "label"; implicitWidth: 250; implicitHeight: 26; font.pixelSize: 11
                    Accessible.name: "Liste aus den Werten einer Kachel"
                    onActivated: if (currentIndex > 0) dlg.useTile(currentIndex - 1)
                }
            }
            Text { text: "Erlaubte Werte (einer je Zeile oder getrennt durch , oder ;)"; font.pixelSize: 10; color: "#52606d" }
            ScrollView {
                width: parent.width; height: 96
                TextArea { id: valuesArea; font.pixelSize: 11; selectByMouse: true; wrapMode: TextArea.NoWrap; Accessible.name: "Erlaubte Werte"; onTextChanged: dlg.refresh(); background: Rectangle { color: "#fbfcfd"; border.color: "#c3ccd6" } }
            }
            Row {
                spacing: 6
                Text { text: "Falsche Zellen erhalten"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                TextField { id: badField; width: 150; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; Accessible.name: "Text für eine falsche Zelle"; onTextEdited: dlg.refresh() }
            }
            CheckBox { id: emptyCheck; text: "Leere Zelle ist in Ordnung"; font.pixelSize: 11; checked: true; onToggled: dlg.refresh() }
            CheckBox { id: caseCheck; text: "Groß-/Kleinschreibung beachten"; font.pixelSize: 11; onToggled: dlg.refresh() }
            Text { visible: !!preview.error; text: preview.error || ""; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Text {
                visible: !preview.error
                text: (preview.bad || 0).toLocaleString() + " von " + (preview.total || 0).toLocaleString() + " Vorschauzellen stehen nicht in der Liste"
                      + ((preview.examples || []).length ? ":  " + preview.examples.join(", ") : "")
                font.pixelSize: 10; font.bold: true; color: preview.bad ? "#b03a2e" : "#1e6f3d"; wrapMode: Text.Wrap; width: parent.width
            }
            Text { visible: dlg.applyError !== ""; text: dlg.applyError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                spacing: 6
                Button {
                    text: dlg.editIndex >= 0 ? "Änderung speichern" : "Anwenden"; implicitHeight: 26; font.pixelSize: 11
                    enabled: !!preview.ok
                    onClicked: {
                        dlg.applyError = dlg.editIndex >= 0 ? columnEditorController.editCheckStep(dlg.editIndex, dlg.options())
                                                            : columnEditorController.applyCheck(dlg.row, dlg.options())
                        if (dlg.applyError === "") dlg.close()
                    }
                }
                Button { text: "Abbrechen"; implicitHeight: 26; font.pixelSize: 11; onClicked: dlg.close() }
            }
        }
    }
}
