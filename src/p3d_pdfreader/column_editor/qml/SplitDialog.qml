// Split dialog: one column becomes several calculated columns - the modes of Power Query's "Spalte teilen": by a separator, by number of
// characters, by positions, by lengths (3,2,3) or at a change of character type (lower->UPPER, UPPER->lower, digit->non-digit, non-digit->digit).
// The preview shows the parts of the first cells; "Anwenden" creates the new tiles right behind the original (one undo step).
import QtQuick
import QtQuick.Controls

Popup {
    id: dlg
    property int row: -1
    property var preview: ({ ok: false, rows: [], error: "", parts: 0 })
    property string applyError: ""

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0
    margins: 6
    padding: 8
    width: Math.min(340, (Overlay.overlay ? Overlay.overlay.width : 340) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 5 }

    function options() {
        return { mode: modeCombo.currentValue, find: sepField.text, parts: parseInt(partsField.text) || 0,
                 lengths: lenField.text, size: parseInt(sizeField.text) || 0, positions: posField.text, replaceOriginal: origCheck.checked }
    }
    function refresh() { if (row >= 0) preview = columnEditorController.previewSplit(row, options()) }
    function openFor(r) {
        row = r
        applyError = ""
        modeCombo.currentIndex = 0; sepField.text = ""; partsField.text = ""; lenField.text = ""; sizeField.text = ""; posField.text = ""; origCheck.checked = true
        refresh()
        open()
    }
    onOpened: sepField.forceActiveFocus()

    contentItem: Column {
        spacing: 5
        Text { text: "Spalte teilen"; font.bold: true; font.pixelSize: 12 }
        Text { text: "Spalte: " + (preview.label || ""); font.pixelSize: 10; color: "#52606d"; elide: Text.ElideRight; width: parent.width }
        Row {
            spacing: 6
            Text { text: "Teilen nach"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
            ComboBox {
                id: modeCombo
                model: [{ text: "ein Trennzeichen", value: "delimiter" }, { text: "Anzahl Zeichen (alle N)", value: "count" },
                        { text: "Positionen (0,3,5)", value: "positions" }, { text: "feste Längen (3,2,3)", value: "fixed" },
                        { text: "klein zu GROSS", value: "lower_upper" }, { text: "GROSS zu klein", value: "upper_lower" },
                        { text: "Ziffer zu Nicht-Ziffer", value: "digit_nondigit" }, { text: "Nicht-Ziffer zu Ziffer", value: "nondigit_digit" }]
                textRole: "text"; valueRole: "value"
                implicitWidth: 220; implicitHeight: 26; font.pixelSize: 11
                Accessible.name: "Art der Teilung"
                onActivated: dlg.refresh()
            }
        }
        Row {
            visible: modeCombo.currentValue === "delimiter"; spacing: 6
            Text { text: "Trennzeichen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
            TextField { id: sepField; width: 60; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; Accessible.name: "Trennzeichen"; onTextEdited: dlg.refresh() }
            Text { text: "Teile"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
            TextField { id: partsField; width: 50; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "auto"; inputMethodHints: Qt.ImhDigitsOnly; Accessible.name: "Anzahl Teile"; onTextEdited: dlg.refresh() }
        }
        Row {
            visible: modeCombo.currentValue === "count"; spacing: 6
            Text { text: "Zeichen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
            TextField { id: sizeField; width: 60; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "N"; inputMethodHints: Qt.ImhDigitsOnly; Accessible.name: "Zeichen je Teil"; onTextEdited: dlg.refresh() }
            Text { text: "je Teil, wiederholt"; font.pixelSize: 10; color: "#52606d"; anchors.verticalCenter: parent.verticalCenter }
        }
        Row {
            visible: modeCombo.currentValue === "positions"; spacing: 6
            Text { text: "Positionen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
            TextField { id: posField; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "Startpositionen ab 0, z. B. 0,3,5"; Accessible.name: "Startpositionen der Teile"; onTextEdited: dlg.refresh() }
        }
        Row {
            visible: modeCombo.currentValue === "fixed"; spacing: 6
            Text { text: "Längen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
            TextField { id: lenField; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "e.g. 3,2,3"; Accessible.name: "Längen der Teile"; onTextEdited: dlg.refresh() }
        }
        CheckBox { id: origCheck; text: "Originalspalte ausblenden und nicht exportieren"; font.pixelSize: 11; checked: true }
        Text {
            visible: !!preview.error; text: preview.error || ""; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width
        }
        Text {
            visible: !preview.error && preview.parts > 0
            text: preview.parts + " neue Spalten, erste Zellen:"; font.pixelSize: 10; font.bold: true; color: "#34495e"
        }
        Repeater {
            model: (preview.rows || []).slice(0, 4)
            delegate: Column {
                width: dlg.availableWidth
                Text { text: modelData.before; font.pixelSize: 10; elide: Text.ElideRight; width: parent.width }
                Text { text: "→ " + modelData.after; font.pixelSize: 10; color: "#1e6f3d"; elide: Text.ElideRight; width: parent.width }
            }
        }
        Text { visible: dlg.applyError !== ""; text: dlg.applyError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
        Row {
            spacing: 6
            Button {
                text: "Anwenden"; implicitHeight: 26; font.pixelSize: 11
                enabled: !!preview.ok
                Accessible.name: "Teilen anwenden"
                onClicked: { dlg.applyError = columnEditorController.applySplit(dlg.row, dlg.options()); if (dlg.applyError === "") dlg.close() }
            }
            Button { text: "Abbrechen"; implicitHeight: 26; font.pixelSize: 11; onClicked: dlg.close() }
        }
    }
}
