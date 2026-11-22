// "Spaltentyp ändern" as a small popover that opens right below the selected tile (no dimming, no centred window).
// A change is never silent: it creates an explicit convert step and shows source type, output type, format, invalid-value
// behaviour and a short preview. With several selected tiles the same type is applied to all of them (all or nothing).
import QtQuick
import QtQuick.Controls

Popup {
    id: dlg
    property int row: -1
    property int count: 1                         // tiles the change is applied to
    property var info: ({})
    property var preview: ({ rows: [], error: "" })
    property string applyError: ""
    readonly property string sel: typeCombo.currentValue ? typeCombo.currentValue : "text"
    readonly property bool numeric: sel === "integer" || sel === "decimal" || sel === "percentage"
    readonly property bool dated: sel === "date" || sel === "datetime" || sel === "time"
    readonly property var typeModel: [
        { text: "Text", value: "text" }, { text: "Ganzzahl", value: "integer" },
        { text: "Dezimalzahl", value: "decimal" }, { text: "Prozent", value: "percentage" },
        { text: "Wahr/Falsch", value: "boolean" }, { text: "Datum", value: "date" }, { text: "Zeit", value: "time" },
        { text: "Datum/Zeit", value: "datetime" }, { text: "Dauer", value: "duration" }, { text: "Gemischt", value: "mixed" },
        { text: "Automatisch erkennen", value: "auto" }, { text: "Quelltyp beibehalten", value: "source" }]

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0            // directly below the tile (the grid sets `parent` to the tile before opening)
    margins: 6                                   // Qt keeps the popover inside the window
    padding: 8
    width: Math.min(330, (Overlay.overlay ? Overlay.overlay.width : 330) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 5 }

    function options() {
        return { dateFormat: dateField.text, decimalSeparator: decCombo.currentValue,
                 thousandsSeparator: thouCombo.currentValue, onInvalid: invCombo.currentValue }
    }
    function refresh() {
        if (row < 0) return
        preview = columnEditorController.previewType(row, sel, options())
    }
    function openFor(r) {
        row = r
        info = columnEditorController.typeInfo(r)
        count = columnEditorController.menuInfo(r).count
        applyError = ""
        typeCombo.currentIndex = Math.max(0, typeCombo.indexOfValue(info.outputType))
        dateField.text = info.dateFormat || ""
        decCombo.currentIndex = Math.max(0, decCombo.indexOfValue(info.decimalSeparator))
        thouCombo.currentIndex = Math.max(0, thouCombo.indexOfValue(info.thousandsSeparator))
        invCombo.currentIndex = Math.max(0, invCombo.indexOfValue(info.onInvalid))
        refresh()
        open()
    }

    contentItem: Flickable {
        clip: true
        implicitHeight: Math.min(body.implicitHeight, 430)
        contentHeight: body.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: body
            width: parent.width
            spacing: 5
            Text {
                text: dlg.count > 1 ? "Typ ändern: " + dlg.count + " Spalten" : "Typ von  " + (info.label || "")
                font.bold: true; font.pixelSize: 12; elide: Text.ElideRight; width: parent.width
            }
            Text {
                text: dlg.count > 1 ? "Gilt für alle gewählten Kacheln (alle oder keine). Vorschau: " + (info.label || "")
                                    : "Quelltyp: " + (info.sourceType || "")
                font.pixelSize: 10; color: "#52606d"; elide: Text.ElideRight; width: parent.width
            }
            Row {
                spacing: 6
                Text { text: "Ausgabetyp"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 92 }
                ComboBox {
                    id: typeCombo
                    model: dlg.typeModel
                    textRole: "text"; valueRole: "value"
                    implicitWidth: 190; implicitHeight: 26; font.pixelSize: 11
                    Accessible.name: "Ausgabetyp"
                    onActivated: dlg.refresh()
                }
            }
            Row {
                visible: dlg.dated
                spacing: 6
                Text { text: "Format"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 92 }
                TextField {
                    id: dateField
                    width: 190; implicitHeight: 26; font.pixelSize: 11
                    placeholderText: "automatisch, z. B. %d.%m.%Y"
                    selectByMouse: true
                    Accessible.name: "Datumsformat"
                    onTextEdited: dlg.refresh()
                }
            }
            Row {
                visible: dlg.numeric
                spacing: 6
                Text { text: "Dezimaltr."; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 92 }
                ComboBox {
                    id: decCombo
                    model: [{ text: "Punkt  .", value: "." }, { text: "Komma  ,", value: "," }]
                    textRole: "text"; valueRole: "value"
                    implicitWidth: 190; implicitHeight: 26; font.pixelSize: 11
                    Accessible.name: "Dezimaltrennzeichen"
                    onActivated: dlg.refresh()
                }
            }
            Row {
                visible: dlg.numeric
                spacing: 6
                Text { text: "Tausendertr."; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 92 }
                ComboBox {
                    id: thouCombo
                    model: [{ text: "Komma  ,", value: "," }, { text: "Punkt  .", value: "." }, { text: "Leerzeichen", value: " " }, { text: "Keins", value: "" }]
                    textRole: "text"; valueRole: "value"
                    implicitWidth: 190; implicitHeight: 26; font.pixelSize: 11
                    Accessible.name: "Tausendertrennzeichen"
                    onActivated: dlg.refresh()
                }
            }
            Row {
                spacing: 6
                Text { text: "Ungültige Werte"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 92 }
                ComboBox {
                    id: invCombo
                    model: [{ text: "Leeren und markieren", value: "empty_flag" }, { text: "Original behalten und markieren", value: "flag" },
                            { text: "Leeren", value: "empty" }, { text: "Vorgang abbrechen", value: "abort" }]
                    textRole: "text"; valueRole: "value"
                    implicitWidth: 190; implicitHeight: 26; font.pixelSize: 11
                    Accessible.name: "Verhalten bei ungültigen Werten"
                    onActivated: dlg.refresh()
                }
            }
            Text {
                text: (info.sourceType || "") + "  →  " + typeCombo.currentText + (preview.format ? "   (" + preview.format + ")" : "")
                font.pixelSize: 10; font.bold: true; color: "#34495e"; elide: Text.ElideRight; width: parent.width
            }
            Text { visible: !!preview.note; text: preview.note || ""; font.pixelSize: 10; color: "#52606d"; wrapMode: Text.Wrap; width: parent.width }
            Text { visible: !!preview.error; text: preview.error || ""; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Repeater {
                model: (preview.rows || []).slice(0, 4)
                delegate: Row {
                    spacing: 6
                    Text { text: modelData.source; font.pixelSize: 10; width: 130; elide: Text.ElideRight }
                    Text { text: "→"; font.pixelSize: 10 }
                    Text {
                        text: modelData.result === "" ? "(leer)" : modelData.result
                        font.pixelSize: 10; width: 130; elide: Text.ElideRight
                        color: modelData.valid ? "#1f2933" : "#b03a2e"
                    }
                }
            }
            Text { visible: dlg.applyError !== ""; text: dlg.applyError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                spacing: 6
                Button {
                    text: "Anwenden"
                    implicitHeight: 26; font.pixelSize: 11
                    enabled: !preview.error
                    Accessible.name: "Typänderung anwenden"
                    onClicked: {
                        dlg.applyError = columnEditorController.applyType(dlg.row, dlg.sel, dlg.options())
                        if (dlg.applyError === "") dlg.close()
                    }
                }
                Button { text: "Abbrechen"; implicitHeight: 26; font.pixelSize: 11; onClicked: dlg.close() }
            }
        }
    }
}
