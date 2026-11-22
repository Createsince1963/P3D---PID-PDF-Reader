// Side pane of the tile editor as its own view: "Aktive Kachel" (inspector), the group dialog and the Steps / history panel.
// It is shown in the host's flow deck (docked right, full height, floatable) - same controller / model / layout as ColumnGrid.qml.
// Dialogs that belong to a tile (change type, edit a step) open next to the tile in the grid: the pane only asks the controller.
import QtQuick
import QtQuick.Controls

Rectangle {
    id: pane
    color: "#f7f9fb"

    Flickable {
        id: side
        anchors { fill: parent; margins: 8 }
        contentWidth: width
        contentHeight: sideCol.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { }
        Column {
            id: sideCol
            width: side.width - 10
            spacing: 8
            RuleInspector {
                width: parent.width
                row: columnEditorController.selectedRow
                onChangeTypeRequested: function (r) { columnEditorController.requestChangeType(r) }
            }
            Text {
                visible: columnEditorController.selectionCount >= 2 && !columnEditorController.hasDraft
                text: columnEditorController.selectionCount + " Kacheln gewählt. Kacheln gruppieren (Strg+G) öffnet hier den Gruppen-Dialog: Gruppenname, optional verbundene Spalte, optional Kopfzeile in Tabelle / Excel."
                font.pixelSize: 11; color: "#52606d"; wrapMode: Text.Wrap; width: parent.width
            }
            GroupPanel { width: parent.width }
            StepsPanel { width: parent.width; onEditRequested: function (step) { columnEditorController.requestEditStep(step) } }
        }
    }
}
