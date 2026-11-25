// One tile. States: ACTIVE / SELECTED (thin green border), passive (compact), selected in a group (badge 1..n), calculated (green fill),
// hidden (grey, dashed grey border), not exported (orange). Tiles are only a view: the data lives in columnConfigModel, a drag only reports
// positions to columnEditorController. Double-click on the type chip = "Spaltentyp ändern"; right-click / "⋮" = menu.
import QtQuick
import QtQuick.Controls

Rectangle {
    id: card

    property int slotIndex: -1
    property string shortName: ""
    property bool protectedColumn: false        // DCF database index (PnPID): red bold, cannot be hidden
    property bool renamed: false                // output column renamed: red mark at the right edge, text in red (display only)
    property string originalName: ""            // name before the rename (carried along; the data keeps its original column)
    property bool showOriginal: false           // the "Umbenannt" area also shows the original name on the tile
    property string chip: "ABC"
    property int position: 0
    property bool hiddenColumn: false
    property bool computed: false
    property bool active: false
    property int selOrder: 0              // 1, 2, 3 ... when several tiles are selected (order of clicking)
    property bool inExport: true
    property bool dragging: false
    property string tip: ""
    property string tagColor: ""         // colour category from the project definitions (Tag structures); empty = neutral
    property string groupColor: ""        // tile group: colour of the group frame (empty = not in a group)
    property string groupName: ""
    property bool splitTile: false        // column the Excel export splits by (set from the export dialog): light green
    property bool temporary: false        // display-only column (merged view / duplicates): grey tile, not moved / renamed / grouped
    property string tipText: ""          // hover text: full name, number of elements, function (asked from the controller on hover)
    property alias mouse: mouseArea
    readonly property bool multi: selOrder > 0

    signal clicked()
    signal ctrlClicked()
    signal shiftClicked(bool additive)       // Shift+Click = range from the anchor; Shift+Ctrl adds the range
    signal typeRequested()
    signal backRequested()                   // double-click on the tile (not on the type chip): the back side with all properties
    signal contextRequested()

    width: 90
    height: active ? 64 : 56
    radius: 6
    readonly property bool marked: active || multi
    readonly property bool tagged: tagColor !== ""
    readonly property color tagTint: tagged ? Qt.tint("#ffffff", Qt.rgba(Qt.color(tagColor).r, Qt.color(tagColor).g, Qt.color(tagColor).b, marked ? 0.30 : 0.20))
                                            : "#ffffff"
    // fill: hidden (grey) > not exported (orange) > colour category > calculated (green) > marked > white
    // split column of the Excel export: light green fill (wins over everything but a hidden tile)
    color: splitTile && !hiddenColumn ? "#b9eec6" : temporary ? "#eceff1" : hiddenColumn ? "#e5e7eb" : (!inExport ? "#fff3e0" : (tagged ? tagTint : (computed ? "#dff3e3" : (marked ? "#eef8f1" : "#ffffff"))))
    border.width: marked ? 1.5 : (hiddenColumn ? 0 : (!inExport ? 2 : 1))
    border.color: marked ? "#2e9e4f" : temporary ? "#7b8794" : (!inExport ? "#f08c00" : (computed ? "#4c9f5f" : "#c3ccd6"))
    opacity: hiddenColumn ? 0.85 : 1.0
    scale: dragging ? 1.06 : 1.0
    z: dragging ? 10 : (active ? 2 : 0)

    Drag.active: mouseArea.drag.active
    Drag.source: card
    Drag.hotSpot.x: width / 2
    Drag.hotSpot.y: height / 2

    Accessible.role: Accessible.Button
    Accessible.name: tip

    Rectangle {                                // group frame: tiles of one group carry the same coloured frame (block in the tile editor)
        visible: card.groupColor !== ""
        anchors.fill: parent
        anchors.margins: -3
        radius: card.radius + 2
        color: "transparent"
        border.width: 2.5
        border.color: card.groupColor
        z: -1
    }

    Canvas {                                   // dashed border of a hidden tile (orange when it is also not exported)
        id: dashed
        anchors.fill: parent
        visible: card.hiddenColumn && !card.marked
        property bool ex: card.inExport
        onExChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onVisibleChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = card.inExport ? "#7b8794" : "#f08c00"
            ctx.lineWidth = 1.5
            ctx.setLineDash([4, 3])
            ctx.strokeRect(1, 1, width - 2, height - 2)
        }
    }

    Rectangle {                                // colour category stripe (stays visible on hidden / not exported tiles)
        visible: card.tagged
        x: 3; y: 6
        width: 3
        height: card.height - 12
        radius: 1.5
        color: card.tagColor
    }
    Text {
        id: posText
        x: 8; y: 5
        text: card.position
        font.pixelSize: 10
        color: card.hiddenColumn ? "#6b7280" : "#7b8794"
    }
    Rectangle {
        id: chipBox
        x: 8 + Math.max(14, posText.implicitWidth) + 3
        y: 4
        width: chipText.implicitWidth + 10
        height: 16
        radius: 3
        color: card.hiddenColumn ? "#d1d5db" : (card.marked ? "#d5eedc" : "#e8eef5")
        Text { id: chipText; anchors.centerIn: parent; text: card.chip; font.pixelSize: 10; font.bold: true; color: "#34495e" }
    }
    Text {                                     // function marker of a calculated tile
        visible: card.computed
        x: chipBox.x + chipBox.width + 4
        y: 4
        text: "ƒx"
        font.pixelSize: 11
        font.bold: true
        color: "#2f7d44"
    }
    Text {
        id: dots
        anchors.right: parent.right; anchors.rightMargin: 6
        y: 1
        text: "⋮"
        font.pixelSize: 16
        color: "#52606d"
    }
    Rectangle {                                // renamed: red mark at the right edge of the tile
        visible: card.renamed
        anchors { right: parent.right; top: parent.top; bottom: parent.bottom; topMargin: 6; bottomMargin: 6 }
        width: 4
        radius: 2
        color: "#d32f2f"
        z: 3
    }
    Text {                                     // "Umbenannt" area: original name above the new one
        visible: card.renamed && card.showOriginal
        anchors.left: parent.left; anchors.leftMargin: 7
        anchors.right: parent.right; anchors.rightMargin: 10
        anchors.bottom: parent.bottom; anchors.bottomMargin: card.active ? 25 : 22
        text: card.originalName
        elide: Text.ElideRight
        font.pixelSize: 10
        font.strikeout: true
        color: "#7b8794"
    }
    Text {
        visible: !card.inExport || card.temporary
        anchors.right: parent.right; anchors.rightMargin: 6
        y: 21
        text: card.temporary ? "temporary" : "nicht exportiert"
        font.pixelSize: 8
        font.italic: true
        color: card.temporary ? "#52606d" : "#c2620a"
    }
    Text {
        anchors.left: parent.left; anchors.leftMargin: 7
        anchors.right: parent.right; anchors.rightMargin: card.renamed ? 10 : 7
        anchors.bottom: parent.bottom; anchors.bottomMargin: card.active ? 9 : 7
        text: card.shortName
        elide: Text.ElideRight
        font.pixelSize: card.active ? 13 : 12
        font.bold: card.active || card.protectedColumn
        color: card.protectedColumn || card.renamed ? "#c0392b" : card.hiddenColumn ? "#6b7280" : "#1f2933"
    }

    Rectangle {                                // selection-order badge
        visible: card.multi
        x: -6; y: -6
        width: 20; height: 20
        radius: 10
        color: "#2e9e4f"
        border.color: "#ffffff"
        border.width: 2
        z: 20
        Text { anchors.centerIn: parent; text: card.selOrder; font.pixelSize: 11; font.bold: true; color: "#ffffff" }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        drag.target: card.temporary || card.showOriginal ? null : card     // temporary columns and the tiles of the "Umbenannt" view cannot be dragged
        drag.axis: Drag.XAndYAxis
        property bool pendingSingle: false
        hoverEnabled: true
        onContainsMouseChanged: {
            if (containsMouse && typeof columnEditorController !== "undefined") card.tipText = columnEditorController.tileTip(card.slotIndex)
        }
        function overChip(m) {
            var p = mapToItem(chipBox, m.x, m.y)
            return p.x >= 0 && p.y >= 0 && p.x <= chipBox.width && p.y <= chipBox.height
        }
        onPressed: function (m) {
            if (m.button !== Qt.LeftButton) return
            if (m.modifiers & Qt.ShiftModifier) card.shiftClicked(!!(m.modifiers & Qt.ControlModifier))
            else if (m.modifiers & Qt.ControlModifier) card.ctrlClicked()
            else if (typeof columnEditorController !== "undefined" && columnEditorController.inSelection(card.slotIndex))
                mouseArea.pendingSingle = true          // press inside a multi selection: keep it, so the whole group can be dragged
            else mouseArea.pendingSingle = true         // plain click: acts on release, never while the tile is picked up / dragged
        }
        onReleased: function (m) {                      // plain click (no drag) inside a multi selection = select only this tile
            if (pendingSingle && !drag.active && m.button === Qt.LeftButton) card.clicked()
            pendingSingle = false
        }
        onCanceled: pendingSingle = false
        onClicked: function (m) {
            if (m.button === Qt.RightButton || m.x >= dots.x - 4 && m.y < 24) card.contextRequested()
        }
        onDoubleClicked: function (m) {
            if (m.button !== Qt.LeftButton) return
            if (overChip(m)) card.typeRequested()
            else if (!card.temporary) card.backRequested()
        }
    }

    ToolTip.visible: mouseArea.containsMouse && !mouseArea.drag.active && card.tipText !== ""
    ToolTip.delay: 450
    ToolTip.timeout: 25000
    ToolTip.text: card.tipText

    states: State {
        when: mouseArea.drag.active
        AnchorChanges { target: card; anchors.horizontalCenter: undefined; anchors.verticalCenter: undefined }
    }
}
