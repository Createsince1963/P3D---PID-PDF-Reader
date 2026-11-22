// Group / Combine columns. The group is a DRAFT: nothing in the preview changes until "Anwenden";
// "Abbrechen" discards it completely. The result texts update immediately on every change.
import QtQuick
import QtQuick.Controls

Rectangle {
    id: panel
    readonly property var d: columnEditorController.draft
    property string error: ""
    readonly property real slotW: 78
    readonly property var presets: [{ t: "_", v: "_" }, { t: "-", v: "-" }, { t: "/", v: "/" }, { t: "Leerzeichen", v: " " }, { t: "Keins", v: "" }]

    visible: columnEditorController.hasDraft
    color: "#f1f8f3"
    border.color: "#4c9f5f"
    radius: 6
    implicitHeight: col.implicitHeight + 20

    function presetActive(v) { return d.separator === v }
    function isCustom() {
        for (var i = 0; i < presets.length; i++) if (presets[i].v === d.separator) return false
        return true
    }
    Connections {
        target: columnEditorController
        function onDraftChanged() {
            panel.error = ""
            if (!panel.d.active) return
            if (!targetField.activeFocus && targetField.text !== (panel.d.target || "")) targetField.text = panel.d.target || ""
            if (!customField.activeFocus) customField.text = panel.isCustom() ? panel.d.separator : ""
        }
    }

    Column {
        id: col
        x: 10; y: 10
        width: panel.width - 20
        spacing: 6

        Text { text: "Gruppieren / Spalten verbinden  (" + (d.count || 0) + ")"; font.bold: true; font.pixelSize: 13; color: "#2f7d44" }
        Text { text: "Reihenfolge = Reihenfolge der Werte im Ergebnis. Kürzel ziehen oder ◂ ▸ benutzen. Strg+Klick auf eine Kachel = hinzufügen / entfernen, Umschalt+Klick = Bereich hinzufügen.";font.pixelSize: 10; color: "#52606d"; wrapMode: Text.Wrap; width: parent.width }

        Flickable {                                  // reorderable row of the grouped tiles
            id: strip
            width: parent.width
            height: 46
            contentWidth: Math.max(width, (d.count || 0) * panel.slotW)
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            Repeater {
                model: d.labels || []
                delegate: Rectangle {
                    id: chip
                    width: panel.slotW - 6
                    height: 40
                    y: 2
                    radius: 5
                    color: "#ffffff"
                    border.color: "#4c9f5f"
                    border.width: 1.5
                    property real home: index * panel.slotW
                    x: home
                    z: ma.drag.active ? 5 : 0
                    Rectangle {
                        x: 3; y: 3; width: 16; height: 16; radius: 8; color: "#1f5fa8"
                        Text { anchors.centerIn: parent; text: index + 1; font.pixelSize: 10; font.bold: true; color: "#ffffff" }
                    }
                    Text {
                        x: 3; anchors.bottom: parent.bottom; anchors.bottomMargin: 3
                        width: parent.width - 6
                        text: modelData; elide: Text.ElideRight; font.pixelSize: 11
                    }
                    Text {
                        anchors.right: parent.right; anchors.rightMargin: 3; y: 1
                        text: "×"; font.pixelSize: 14; color: "#9a3b3b"
                        MouseArea { anchors.fill: parent; anchors.margins: -4; onClicked: columnEditorController.removeDraftItem(index) }
                    }
                    Text {
                        x: 22; y: 4; text: "◂"; font.pixelSize: 11; color: "#52606d"; visible: index > 0
                        MouseArea { anchors.fill: parent; anchors.margins: -4; onClicked: columnEditorController.moveDraftItem(index, index - 1) }
                    }
                    Text {
                        x: 34; y: 4; text: "▸"; font.pixelSize: 11; color: "#52606d"; visible: index < (d.count || 0) - 1
                        MouseArea { anchors.fill: parent; anchors.margins: -4; onClicked: columnEditorController.moveDraftItem(index, index + 1) }
                    }
                    MouseArea {
                        id: ma
                        anchors.fill: parent
                        z: -1
                        drag.target: chip
                        drag.axis: Drag.XAxis
                        onReleased: {
                            var to = Math.max(0, Math.min((d.count || 1) - 1, Math.round(chip.x / panel.slotW)))
                            chip.x = Qt.binding(function () { return chip.home })
                            if (to !== index) columnEditorController.moveDraftItem(index, to)
                        }
                    }
                }
            }
        }

        Text { text: "Trennzeichen"; font.pixelSize: 11; font.bold: true }
        Row {
            spacing: 4
            Repeater {
                model: panel.presets
                delegate: Button {
                    text: modelData.t
                    checkable: true
                    checked: panel.presetActive(modelData.v)
                    implicitHeight: 26
                    implicitWidth: modelData.t.length > 2 ? 52 : 32
                    font.pixelSize: 11
                    Accessible.name: "Trennzeichen " + modelData.t
                    onClicked: columnEditorController.setSeparator(modelData.v)
                }
            }
        }
        Row {
            spacing: 6
            Text { text: "Eigenes"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
            TextField {
                id: customField
                width: 90
                maximumLength: 16
                placeholderText: "beliebiger Text"
                selectByMouse: true
                font.pixelSize: 11
                Accessible.name: "Eigenes Trennzeichen"
                onTextEdited: if (text !== "") columnEditorController.setSeparator(text)
            }
        }
        CheckBox { text: "Leerzeichen kürzen"; checked: d.trim === true; font.pixelSize: 11; onToggled: columnEditorController.setTrim(checked) }
        CheckBox { text: "Leere Werte überspringen"; checked: d.skipEmpty === true; font.pixelSize: 11; onToggled: columnEditorController.setSkipEmpty(checked) }
        CheckBox { text: "Originalspalten behalten"; checked: d.keep === true; font.pixelSize: 11; onToggled: columnEditorController.setKeepOriginals(checked) }
        CheckBox { text: "Originale exportieren"; checked: d.include === true; font.pixelSize: 11; onToggled: columnEditorController.setIncludeOriginals(checked) }
        CheckBox { text: "Verbundene Spalte anlegen (Werte der Kacheln verbunden)"; checked: d.combine === true; font.pixelSize: 11
                   ToolTip.visible: hovered; ToolTip.text: "Aus: nur Gruppe – die Kacheln bewegen sich im Kachel-Editor gemeinsam als Block."
                   onToggled: columnEditorController.setCombine(checked) }
        CheckBox { text: "Gruppenname als Kopfzeile in Tabelle und Excel-Export"; checked: d.band === true; font.pixelSize: 11
                   ToolTip.visible: hovered; ToolTip.text: "An: der Gruppenname steht als gemeinsame Kopfzeile über den gruppierten Spalten (Tabelle und Excel). Aus: die Gruppe gibt es nur im Kachel-Editor."
                   onToggled: columnEditorController.setBand(checked) }

        Text { text: "Gruppenname / Name der verbundenen Spalte"; font.pixelSize: 11; font.bold: true }
        TextField {
            id: targetField
            width: parent.width
            selectByMouse: true
            font.pixelSize: 11
            Accessible.name: "Name der Zielspalte"
            onTextEdited: columnEditorController.setTargetName(text)
        }
        Row {
            spacing: 6
            Text { text: "Ausgabetyp"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
            ComboBox {
                id: outCombo
                model: [{ t: "Text", v: "text" }, { t: "Ganzzahl", v: "integer" }, { t: "Dezimalzahl", v: "decimal" },
                        { t: "Prozent", v: "percentage" }, { t: "Wahr/Falsch", v: "boolean" }, { t: "Zeit", v: "time" }, { t: "Dauer", v: "duration" }]
                textRole: "t"; valueRole: "v"
                implicitWidth: 140
                font.pixelSize: 11
                currentIndex: Math.max(0, indexOfValue(d.outputType))
                Accessible.name: "Ausgabetyp der Gruppe"
                onActivated: columnEditorController.setGroupOutputType(currentValue)
            }
        }
        Row {
            spacing: 6
            Text { text: "Ungültige Werte"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
            ComboBox {
                model: [{ t: "Leeren und markieren", v: "empty_flag" }, { t: "Original behalten und markieren", v: "flag" },
                        { t: "Leeren", v: "empty" }, { t: "Vorgang abbrechen", v: "abort" }]
                textRole: "t"; valueRole: "v"
                implicitWidth: 150
                font.pixelSize: 11
                currentIndex: Math.max(0, indexOfValue(d.invalid))
                Accessible.name: "Ungültige Werte der Gruppe"
                onActivated: columnEditorController.setGroupInvalid(currentValue)
            }
        }

        Rectangle { width: parent.width; height: 1; color: "#b9d8c1" }
        Text { text: "Zielspalte: " + (d.target || ""); font.pixelSize: 11; wrapMode: Text.Wrap; width: parent.width }
        Text { text: "Ergebnis-Datentyp: " + (d.outputTypeName || ""); font.pixelSize: 11 }
        Text { text: "Ergebnis: " + (d.resultNames || ""); font.pixelSize: 12; font.bold: true; wrapMode: Text.WrapAnywhere; width: parent.width }
        Text {
            text: "Beispiel: " + (d.example || "")
            font.pixelSize: 12; font.bold: true; color: d.exampleValid === false ? "#b03a2e" : "#2f7d44"
            wrapMode: Text.WrapAnywhere; width: parent.width
        }
        Text { visible: panel.error !== ""; text: panel.error; color: "#b03a2e"; font.pixelSize: 11; wrapMode: Text.Wrap; width: parent.width }
        Row {
            spacing: 8
            Button {
                text: "Anwenden"
                enabled: d.canApply === true
                Accessible.name: "Anwenden"
                onClicked: panel.error = columnEditorController.applyGroup()
            }
            Button { text: "Abbrechen"; Accessible.name: "Gruppe abbrechen"; onClicked: columnEditorController.cancelGroup() }
        }
    }
}
