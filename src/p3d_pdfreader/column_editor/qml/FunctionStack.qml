// Function stack (Sprint 2): dropping a tile ONTO another tile will start a stack here. Sprint 1 only shows the hint;
// moving (drop between tiles) is handled by ColumnGrid.
import QtQuick

Rectangle {
    id: stack
    property bool dropTarget: false
    color: dropTarget ? "#eaf3ff" : "#f7f9fb"
    border.color: "#c3ccd6"
    radius: 6
    implicitHeight: 34
    Text {
        anchors.centerIn: parent
        text: "Funktionsstapel: im nächsten Schritt verfügbar (Kachel auf eine andere ziehen)"
        font.pixelSize: 11
        color: "#7b8794"
    }
}
