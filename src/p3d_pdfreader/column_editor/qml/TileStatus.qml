// Status strip of the tile editor. It sits in the ribbon at the height of the icon row (owner 2026-11-16): bulk button "Alle in Tabelle ausblenden",
// and the colour legend (the three area buttons are Qt ribbon buttons right of it). The open / folded state of the areas lives in `tileLayout`
// (shared with ColumnGrid.qml); the counts come from `columnConfigModel`, the bulk action from `columnEditorController`.
import QtQuick
import QtQuick.Controls

Item {
    id: root
    implicitHeight: 34
    implicitWidth: strip.implicitWidth + 8
    readonly property var openAreas: tileLayout.openAreas
    function isOpen(i) { return openAreas.indexOf(i) >= 0 }

    Row {
        id: strip
        anchors { right: parent.right; rightMargin: 4; verticalCenter: parent.verticalCenter }
        spacing: 16

        Rectangle {                                             // neutral bulk button: hide / show the not-exported columns in the table
            id: bulkTop
            visible: root.isOpen(1) && columnConfigModel.notExportedCount > 0
            width: bulkTopText.implicitWidth + 14; height: 18; radius: 3
            anchors.verticalCenter: parent.verticalCenter
            color: bulkTopArea.containsMouse ? "#e5e7eb" : "transparent"
            border.width: 1
            border.color: "#9aa5b1"
            Text { id: bulkTopText; anchors.centerIn: parent; font.pixelSize: 10; color: "#52606d"
                   text: columnConfigModel.tableHiddenCount >= columnConfigModel.notExportedCount ? "Alle in Tabelle einblenden" : "Alle in Tabelle ausblenden" }
            MouseArea { id: bulkTopArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: columnEditorController.setAreaHidden(1) }
            ToolTip.visible: bulkTopArea.containsMouse
            ToolTip.text: columnConfigModel.tableHiddenCount >= columnConfigModel.notExportedCount
                          ? "Nicht exportierte Spalten in der Tabelle unten wieder zeigen (ein Rückgängig-Schritt)"
                          : "Alle nicht exportierten Spalten nur in der Tabelle unten ausblenden; die Kacheln bleiben in „Nicht exportiert“, Bereich „Ausgeblendet“ und Export bleiben unverändert (ein Rückgängig-Schritt)"
        }
        Row {                                                   // colour legend; collapses together with the right-hand column (and when the ribbon is narrow)
            id: legend
            visible: root.openAreas.length > 0 && root.width > 820
            anchors.verticalCenter: parent.verticalCenter
            spacing: 12
            Repeater {
                model: [{ t: "aktiv / gewählt", c: "#2e9e4f", f: "#eef8f1" }, { t: "hidden", c: "#7b8794", f: "#e5e7eb" },
                        { t: "nicht exportiert", c: "#f08c00", f: "#fff3e0" }, { t: "calculated", c: "#4c9f5f", f: "#dff3e3" },
                        { t: "umbenannt (rote Marke)", c: "#d32f2f", f: "#ffffff" }]
                delegate: Row {
                    spacing: 4
                    Rectangle { width: 14; height: 10; radius: 2; color: modelData.f; border.color: modelData.c; border.width: 1.5; anchors.verticalCenter: parent.verticalCenter }
                    Text { text: modelData.t; font.pixelSize: 10; color: "#52606d"; anchors.verticalCenter: parent.verticalCenter }
                }
            }
            Row {
                spacing: 4
                Rectangle { width: 3; height: 12; radius: 1.5; color: "#4f81bd"; anchors.verticalCenter: parent.verticalCenter }
                Text { text: "Farbstreifen = Tag-Typ (Projektdefinitionen)"; font.pixelSize: 10; color: "#52606d"; anchors.verticalCenter: parent.verticalCenter }
            }
        }
    }                                                           // the three area buttons are standard ribbon buttons now (Ribbon.add_area_buttons)
}
