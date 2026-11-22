// Thin insertion marker next to a tile while another tile is dragged over it.
import QtQuick

Rectangle {
    property bool active: false
    width: 3
    radius: 1.5
    color: "#2b6cb0"
    visible: active
}
