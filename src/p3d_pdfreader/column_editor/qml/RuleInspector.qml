// Properties of the ACTIVE tile (D9): names, source / output type, detection, sample, null count, export / visibility,
// applied steps. The type is changed through the "Spaltentyp ändern" dialog (explicit convert step).
import QtQuick
import QtQuick.Controls

Column {
    id: inspector
    property int row: -1
    property var info: ({})
    signal changeTypeRequested(int row)

    spacing: 4
    function refresh() { info = row >= 0 ? columnEditorController.inspect(row) : ({}) }
    onRowChanged: refresh()
    Connections {
        target: columnEditorController
        function onSelectedChanged() { inspector.refresh() }
        function onUndoChanged() { inspector.refresh() }
    }

    component Prop: Row {
        property string name: ""
        property string value: ""
        spacing: 6
        visible: value !== ""
        Text { text: name; font.pixelSize: 11; color: "#7b8794"; width: 92; wrapMode: Text.Wrap }
        Text { text: value; font.pixelSize: 11; color: "#1f2933"; width: inspector.width - 100; wrapMode: Text.Wrap }
    }

    Text {
        text: inspector.row < 0 ? "Eine Kachel wählen" : "Aktive Kachel"
        font.bold: true; font.pixelSize: 13; color: "#1f5fa8"
    }
    Prop { name: "Quellspalte"; value: info.sourceName || "" }
    Prop { name: "Ausgabespalte"; value: info.outputName || "" }
    Prop { name: "Kurzname der Kachel"; value: info.shortName || "" }
    Prop { name: "Quelltyp"; value: info.sourceTypeName || "" }
    Row {
        visible: inspector.row >= 0 && !!info.outputTypeName
        spacing: 6
        Text { text: "Ausgabetyp"; font.pixelSize: 11; color: "#7b8794"; width: 92; anchors.verticalCenter: parent.verticalCenter }
        Text { text: info.outputTypeName || ""; font.pixelSize: 11; font.bold: true; anchors.verticalCenter: parent.verticalCenter }
        Button {
            text: "Typ ändern …"
            implicitHeight: 24
            font.pixelSize: 11
            Accessible.name: "Spaltentyp ändern"
            onClicked: inspector.changeTypeRequested(inspector.row)
        }
    }
    Prop { name: "Erkannt"; value: info.detected ? info.detected + " · " + (info.confidence || "") : "" }
    Prop { name: "Erkennung durch"; value: info.source || "" }
    Prop { name: "Vorschlag"; value: info.suggested ? info.suggested + "  (ungültig: " + (info.invalid || 0) + " von " + (info.samples || 0) + ")" : "" }
    Prop { name: "Beispielwert"; value: info.sampleValue || "" }
    Prop { name: "Leere Zellen"; value: info.nullCount === undefined ? "" : String(info.nullCount) }
    Prop { name: "Status"; value: inspector.row < 0 ? "" : (info.calculated ? "Berechnet" : "Original (Quelle)") }
    CheckBox {
        visible: inspector.row >= 0
        text: "Exportieren"
        checked: info.inExport !== false
        font.pixelSize: 11
        Accessible.name: "Exportieren"
        onToggled: columnEditorController.toggleExport(inspector.row)
    }
    CheckBox {
        visible: inspector.row >= 0
        text: "Im Editor sichtbar"
        checked: info.visible !== false
        font.pixelSize: 11
        Accessible.name: "Im Editor sichtbar"
        onToggled: columnEditorController.toggleHidden(inspector.row)
    }
    Text { visible: (info.steps || []).length > 0; text: "Angewendete Schritte"; font.pixelSize: 11; font.bold: true }
    Repeater {
        model: info.steps || []
        delegate: Text { text: "• " + modelData; font.pixelSize: 11; wrapMode: Text.Wrap; width: inspector.width }
    }
}
