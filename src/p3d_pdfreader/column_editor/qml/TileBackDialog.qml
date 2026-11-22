// Back side of a tile ("flip card"): every editable property of ONE column in a popover below the tile (double-click on the tile;
// the double-click on the type chip still opens "Spaltentyp ändern"). The grid stays untouched: the tile does not grow, no neighbour moves.
// Every change is stored at once as its own undo step (Ctrl+Z works as usual); "Änderungen verwerfen" undoes all steps made since the popover opened.
// Esc, a click outside and the X button close it in exactly the same way (a text that was typed is committed first).
// The original name is read only; "Name zurücksetzen" gives the column its original name back. The rename is visual: the data stays.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: dlg
    property string key: ""                       // the tile is followed by its key: the row changes when the position is changed
    property int startDepth: 0
    property int depth: 0                         // undo steps now (grows with every change made here)
    property var info: ({})
    property var tag: ({ tag: "", color: "" })
    property string group: ""
    property string problem: ""
    property bool busy: false
    signal changeTypeRequested(int row)

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0
    margins: 6
    padding: 10
    width: Math.min(360, (Overlay.overlay ? Overlay.overlay.width : 360) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 6 }

    function row() { return key === "" ? -1 : columnEditorController.rowOfKey(key) }
    function openFor(r) {
        key = columnEditorController.inspect(r).key
        startDepth = columnEditorController.undoDepth()
        problem = ""
        refresh()
        open()
    }
    function refresh() {
        var r = row()
        if (r < 0) return
        busy = true
        depth = columnEditorController.undoDepth()
        info = columnEditorController.inspect(r)
        tag = columnEditorController.tagInfo(r)
        group = columnEditorController.inGroup(r) ? columnEditorController.groupName(r) : ""
        nameField.text = info.outputName || ""
        shortField.text = info.shortName || ""
        posBox.to = columnConfigModel.count
        posBox.value = r + 1
        widthBox.value = columnEditorController.columnWidth(r)
        busy = false
    }
    function say(err) { problem = err || "" }
    function commitTexts() {                      // typed but not confirmed yet (Esc / click outside): still counts
        var r = row()
        if (r < 0 || busy) return
        if (nameField.text !== (info.outputName || "") && nameField.text.trim() !== "") say(columnEditorController.renameOutput(r, nameField.text))
        if (shortField.text !== (info.shortName || "")) say(columnEditorController.setShortName(r, shortField.text))
    }
    onAboutToHide: commitTexts()
    onOpened: nameField.forceActiveFocus()
    Connections {
        target: columnEditorController
        function onUndoChanged() { if (dlg.visible) dlg.refresh() }
    }

    contentItem: ColumnLayout {
        spacing: 6
        RowLayout {
            Layout.fillWidth: true
            Text { text: "Spalteneigenschaften"; font.pixelSize: 12; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
            Text {
                text: "✕"; font.pixelSize: 13; color: closeArea.containsMouse ? "#2c3e50" : "#9aa5b1"
                MouseArea { id: closeArea; anchors.fill: parent; anchors.margins: -5; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: dlg.close() }
            }
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 8
            rowSpacing: 5

            Text { text: "Originalname"; font.pixelSize: 11; color: "#52606d" }
            TextField {
                Layout.fillWidth: true; implicitHeight: 26; font.pixelSize: 11
                readOnly: true; text: dlg.info.originalName || ""; color: "#52606d"
                background: Rectangle { color: "#f3f5f7"; border.color: "#d3d9e0"; radius: 3 }
                Accessible.name: "Originalname (nur lesen)"
            }

            Text { text: "Spaltenname"; font.pixelSize: 11; color: "#52606d" }
            RowLayout {
                Layout.fillWidth: true; spacing: 4
                TextField {
                    id: nameField
                    objectName: "backName"
                    Layout.fillWidth: true; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true
                    color: dlg.info.outputName !== dlg.info.originalName ? "#c0392b" : "#1f2933"
                    onEditingFinished: dlg.commitTexts()
                    Accessible.name: "Spaltenname"
                }
                Button {
                    objectName: "backReset"
                    text: "Name zurücksetzen"; implicitHeight: 26; font.pixelSize: 11
                    enabled: dlg.info.outputName !== dlg.info.originalName
                    onClicked: dlg.say(columnEditorController.renameOutput(dlg.row(), dlg.info.originalName))
                }
            }

            Text { text: "Kachelname"; font.pixelSize: 11; color: "#52606d" }
            TextField {
                id: shortField
                objectName: "backShort"
                Layout.fillWidth: true; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true
                placeholderText: "automatic"
                onEditingFinished: dlg.commitTexts()
                Accessible.name: "Kurzname der Kachel"
            }

            Text { text: "Datentyp"; font.pixelSize: 11; color: "#52606d" }
            RowLayout {
                Layout.fillWidth: true; spacing: 4
                Text { text: dlg.info.outputTypeName || ""; font.pixelSize: 11; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
                Button { text: "Ändern …"; implicitHeight: 26; font.pixelSize: 11
                         onClicked: { var r = dlg.row(); dlg.close(); if (r >= 0) dlg.changeTypeRequested(r) } }
            }

            Text { text: "Export"; font.pixelSize: 11; color: "#52606d" }
            CheckBox {
                objectName: "backExport"
                text: "Exportieren"; font.pixelSize: 11
                checked: dlg.info.inExport === true
                onToggled: { columnEditorController.setExport(dlg.row(), checked); dlg.refresh() }
            }

            Text { text: "Sichtbarkeit"; font.pixelSize: 11; color: "#52606d" }
            CheckBox {
                objectName: "backHidden"
                text: "Ausgeblendet (nicht in der Tabelle)"; font.pixelSize: 11
                checked: dlg.info.visible === false
                onToggled: {
                    if (!columnEditorController.setHidden(dlg.row(), checked)) dlg.say("Die letzte sichtbare Spalte kann nicht ausgeblendet werden.")
                    dlg.refresh()
                }
            }

            Text { text: "Position"; font.pixelSize: 11; color: "#52606d" }
            SpinBox {
                id: posBox
                objectName: "backPosition"
                from: 1; to: 1; editable: true; implicitHeight: 28; font.pixelSize: 11
                onValueModified: { if (!dlg.busy) { columnEditorController.moveToPosition(dlg.row(), value); dlg.refresh() } }
            }

            Text { text: "Gruppe"; font.pixelSize: 11; color: "#52606d" }
            RowLayout {
                Layout.fillWidth: true; spacing: 4
                Text { text: dlg.group !== "" ? dlg.group : "(keine)"; font.pixelSize: 11; Layout.fillWidth: true; elide: Text.ElideRight
                       color: dlg.group !== "" ? "#1f2933" : "#9aa5b1" }
                Button { text: "Gruppe auflösen"; implicitHeight: 26; font.pixelSize: 11; visible: dlg.group !== ""
                         onClicked: { columnEditorController.ungroup(dlg.row()); dlg.refresh() } }
                Button { text: "Zur Gruppe hinzufügen"; implicitHeight: 26; font.pixelSize: 11; visible: dlg.group === ""
                         onClicked: { columnEditorController.addToGroup(dlg.row()); dlg.close() } }
            }

            Text { text: "Spaltenbreite"; font.pixelSize: 11; color: "#52606d" }
            RowLayout {
                spacing: 4
                SpinBox {
                    id: widthBox
                    objectName: "backWidth"
                    from: 30; to: 1200; stepSize: 10; editable: true; implicitHeight: 28; font.pixelSize: 11
                    onValueModified: { if (!dlg.busy) { dlg.say(columnEditorController.setColumnWidth(dlg.row(), value)); } }
                }
                Text { text: "px  (Standardbreite dieser Spalte)"; font.pixelSize: 10; color: "#7b8794" }
            }

            Text { text: "Tag-Farbe"; font.pixelSize: 11; color: "#52606d" }
            RowLayout {
                spacing: 6
                Rectangle { width: 16; height: 12; radius: 2; border.color: "#9aa5b1"; color: dlg.tag.color !== "" ? dlg.tag.color : "transparent" }
                Text { font.pixelSize: 11; color: "#52606d"
                       text: dlg.tag.tag !== "" ? dlg.tag.tag + "  (Projektdefinitionen > Tag-Strukturen)" : "keine – in den Projektdefinitionen festlegen" }
            }
        }
        Text {
            visible: dlg.problem !== ""
            text: dlg.problem; color: "#b03a2e"; font.pixelSize: 10; wrapMode: Text.Wrap; Layout.fillWidth: true
        }
        RowLayout {
            Layout.fillWidth: true; spacing: 6
            Text { text: "Änderungen gelten sofort (rückgängig: Strg+Z)"; font.pixelSize: 10; color: "#7b8794"; Layout.fillWidth: true; elide: Text.ElideRight }
            Button {
                objectName: "backCancel"
                text: "Änderungen verwerfen"; implicitHeight: 26; font.pixelSize: 11
                enabled: dlg.depth > dlg.startDepth
                onClicked: { columnEditorController.undoTo(dlg.startDepth); dlg.refresh() }
            }
        }
    }
}
