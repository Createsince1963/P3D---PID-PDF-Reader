// Small "Text eingeben" popover (rename output column, short tile name, move to position). It opens right below the tile it
// belongs to (the grid sets `parent` to the tile before `ask`), has no dimming and closes with Enter / Esc / click outside.
import QtQuick
import QtQuick.Controls

Popup {
    id: dlg
    property string label: ""
    property string initial: ""
    property string title: ""
    signal submitted(string value)

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0
    margins: 6
    padding: 8
    width: Math.min(300, (Overlay.overlay ? Overlay.overlay.width : 300) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 5 }

    function ask(titleText, labelText, value) {
        title = titleText
        label = labelText
        initial = value
        field.text = value
        open()
    }
    function accept() { var v = field.text; close(); submitted(v) }
    onOpened: { field.forceActiveFocus(); field.selectAll() }

    contentItem: Column {
        spacing: 5
        Text { text: dlg.title; font.pixelSize: 12; font.bold: true; width: parent.width; elide: Text.ElideRight }
        Text { text: dlg.label; font.pixelSize: 10; color: "#52606d"; wrapMode: Text.Wrap; width: parent.width }
        Row {
            spacing: 6
            TextField {
                id: field
                width: dlg.width - dlg.padding * 2 - 110
                implicitHeight: 26; font.pixelSize: 11
                selectByMouse: true
                Accessible.name: dlg.label
                onAccepted: dlg.accept()
            }
            Button { text: "OK"; implicitHeight: 26; implicitWidth: 48; font.pixelSize: 11; onClicked: dlg.accept() }
            Button { text: "Abbrechen"; implicitHeight: 26; implicitWidth: 52; font.pixelSize: 11; onClicked: dlg.close() }
        }
    }
}
