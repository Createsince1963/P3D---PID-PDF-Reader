// Steps panel: every change made in the tile editor (change type, group, Transform functions) as one line, in the order it was made.
// Click a line = select its tile. Arrows reorder the steps (not past a step they depend on), the pencil changes the settings of the step,
// "x" removes the step (undoable); a step that another step builds on cannot be removed first.
import QtQuick
import QtQuick.Controls

Rectangle {
    id: panel
    readonly property var list: columnEditorController.steps
    color: "#ffffff"
    border.color: "#c3ccd6"
    radius: 6
    implicitHeight: col.implicitHeight + 16
    signal editRequested(var step)

    Column {
        id: col
        x: 8; y: 8
        width: panel.width - 16
        spacing: 4
        Text { text: "Schritte  (" + (panel.list ? panel.list.length : 0) + ")"; font.bold: true; font.pixelSize: 12; color: "#34495e" }
        Text {
            visible: !panel.list || panel.list.length === 0
            text: "Noch keine Schritte. Alles, was Sie mit Umwandeln, Gruppieren oder Typ ändern tun, steht hier und lässt sich wieder entfernen."
            font.pixelSize: 10; color: "#7b8794"; wrapMode: Text.Wrap; width: parent.width
        }
        Repeater {
            model: panel.list
            delegate: Rectangle {
                width: col.width
                height: Math.max(26, label.implicitHeight + 8)
                radius: 4
                color: rowMouse.containsMouse ? "#eef3f8" : "#f7f9fb"
                border.color: "#dde3ea"
                Text {
                    id: label
                    anchors { left: parent.left; right: tools.left; verticalCenter: parent.verticalCenter; leftMargin: 6; rightMargin: 4 }
                    text: (index + 1) + ".  " + modelData.text
                    font.pixelSize: 10; color: "#1f2933"; wrapMode: Text.Wrap
                }
                MouseArea {
                    id: rowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: { var r = columnEditorController.rowOfKey(modelData.key); if (r >= 0) columnEditorController.selectOnly(r) }
                    ToolTip.visible: containsMouse && !!modelData.why
                    ToolTip.delay: 450
                    ToolTip.text: modelData.why
                }
                Row {
                    id: tools
                    anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                    ToolButton {
                        width: 22; height: 24; text: "▲"; font.pixelSize: 9; enabled: modelData.canUp
                        Accessible.name: "Schritt verschieben " + (index + 1) + " nach oben"
                        ToolTip.visible: hovered; ToolTip.delay: 450; ToolTip.text: "Schritt nach oben"
                        onClicked: { var e = columnEditorController.moveStep(modelData.index, -1); if (e !== "") columnEditorController.message(e) }
                    }
                    ToolButton {
                        width: 22; height: 24; text: "▼"; font.pixelSize: 9; enabled: modelData.canDown
                        Accessible.name: "Schritt verschieben " + (index + 1) + " nach unten"
                        ToolTip.visible: hovered; ToolTip.delay: 450; ToolTip.text: "Schritt nach unten"
                        onClicked: { var e = columnEditorController.moveStep(modelData.index, 1); if (e !== "") columnEditorController.message(e) }
                    }
                    ToolButton {
                        width: 22; height: 24; text: "✎"; font.pixelSize: 12; enabled: !!modelData.canEdit
                        Accessible.name: "Schritt ändern " + (index + 1)
                        ToolTip.visible: hovered; ToolTip.delay: 450; ToolTip.text: modelData.canEdit ? "Einstellungen dieses Schritts ändern" : "Dieser Schritt lässt sich nicht ändern; entfernen und neu anlegen"
                        onClicked: panel.editRequested(modelData)
                    }
                    ToolButton {
                        id: del
                        width: 24; height: 24
                        text: "×"
                        enabled: modelData.canDelete
                        font.pixelSize: 14
                        Accessible.name: "Schritt entfernen " + (index + 1)
                        ToolTip.visible: hovered
                        ToolTip.delay: 450
                        ToolTip.text: modelData.canDelete ? "Diesen Schritt entfernen" : modelData.why
                        onClicked: {
                            var e = modelData.kind === "group" ? columnEditorController.removeGroupStep(modelData.bandIndex)
                                                               : columnEditorController.deleteStep(modelData.index)
                            if (e !== "") columnEditorController.message(e)
                        }
                    }
                }
            }
        }
    }
}
