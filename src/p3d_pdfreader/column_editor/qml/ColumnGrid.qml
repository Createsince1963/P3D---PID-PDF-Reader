// Tile editor. Logical positions only: the areas derive their layout from their width (responsive, DPI independent).
// The exported columns (active tiles) fill the grid. Three more areas sit in a right-hand column and start FOLDED to save space:
//   Not exported (orange) / Hidden (grey) / Renamed (red mark). Buttons in the header line open them; at most TWO of them are open at a time
//   (opening a third folds the one opened first); the open ones share the height of the column (stacked in their fixed order). "Umbenannt" is a view (a renamed tile is also
//   in its normal area) and shows the original name carried along with each tile; its tiles cannot be dragged.
// Drag a tile into the other area (or use the tile menu / ribbon "Export ja/nein") to include / exclude it; the table below shows both.
// Every move goes through columnEditorController.moveColumn(from, to), every export change through setExport / toggleExport.
// Double-click on a tile (not on its type chip) = the back side: all editable properties of that ONE column in a popover (TileBackDialog.qml).
// Mouse: click = active tile, Shift+Click = range from the last clicked tile, Ctrl+Click = add to the multi selection (badges 1, 2, 3 ...), double-click on the type chip
// = "Spaltentyp ändern", right-click / ⋮ = tile menu. While a group draft is open, Ctrl+Click / Shift+Click also add tiles to it.
// Collapsing the right-hand column (Not exported / Hidden) also collapses the colour legend above it.
// Commands (menu, Del, Alt+arrows) act on ALL selected tiles when the tile belongs to a multi selection.
// Dialogs are small popovers that open directly below the tile they belong to.
// Tile menu > Transform / Replace values / Fill create a calculated column (and a line in the Steps panel); the source is never changed.
// Keyboard: arrows move focus inside the area, Alt+Left/Right moves the tile, Del hides / shows, Ctrl+G groups the selected tiles,
// Esc cancels a group draft / clears the selection, Ctrl+Z / Ctrl+Y undo / redo.
// Colour categories: a tile shows the colour of its tag type (project definitions > Tag structures) as a stripe and a light fill.
import QtQuick
import QtQuick.Controls

Item {
    id: root
    implicitHeight: 340
    focus: true

    readonly property int minCell: 104
    readonly property int cellH: 72
    readonly property int areaGap: 8
    readonly property int collapsedWidth: 22                  // width of the collapsed side pane (just the expand handle)
    readonly property int maxOpenAreas: 2
    readonly property var openAreas: tileLayout.openAreas      // right-hand column: open areas in the order they were opened (1 = Not exported, 2 = Hidden, 3 = Renamed); [] = all folded (default). The state lives in tileLayout: the status strip in the ribbon (TileStatus.qml) shares it
    readonly property int openArea: openAreas.length ? openAreas[openAreas.length - 1] : 0     // the area opened last (0 = none)
    readonly property var openSorted: openAreas.slice().sort()  // display order top -> bottom in the right-hand column
    property real dragX: -1                                    // centre of the tile being dragged, in `areas` coordinates (-1 = no drag)
    property real dragY: -1
    property int pendingMoveTo: -1                             // row of the tile the dragged tile is hovering over (same area); applied on drop only
    // 0 = exported area, 1 = not exported, 2 = hidden (the open one under the pointer); nothing to drop on while all are folded or over "Umbenannt"
    readonly property int dragTarget: {
        if (dragX < 0) return -1
        if (dragX < areaWidthActive + areaGap / 2) return 0
        var n = openSorted.length
        if (n === 0) return -1
        var a = openSorted[Math.max(0, Math.min(n - 1, Math.floor(dragY / Math.max(1, sideAreaH + areaGap))))]
        return a === 1 || a === 2 ? a : -1
    }
    // right-hand column width: a user-set, persisted share of the grid width; nothing while every area is folded
    readonly property real rightColWidth: openAreas.length === 0 ? 0 : Math.round((areas.width - areaGap) * tileLayout.rightShare)
    readonly property real areaWidthActive: openAreas.length === 0 ? areas.width : areas.width - areaGap - rightColWidth
    readonly property real sideAreaH: openSorted.length < 2 ? areas.height : Math.floor((areas.height - areaGap) / 2)
    function isOpen(i) { return openAreas.indexOf(i) >= 0 }
    function toggleArea(i) { tileLayout.toggleArea(i) }         // open / fold one area; a third one folds the area opened first

    // --- header line: hint text (elided, never overlaps) + colour legend --------------------------------------------------
    Item {
        id: head
        anchors { top: parent.top; left: parent.left; right: sidePane.left; rightMargin: 8 }
        height: 26
        TextField {                                             // search tiles / columns: only matching tiles stay, live while typing
            id: searchField
            objectName: "tileSearch"
            anchors { left: parent.left; verticalCenter: parent.verticalCenter }
            width: 190
            height: 24
            font.pixelSize: 11
            leftPadding: 6
            rightPadding: clearSearch.visible ? 20 : 6
            topPadding: 2
            bottomPadding: 2
            placeholderText: "Kachel / Spalte suchen …"
            selectByMouse: true
            onTextChanged: columnEditorController.setSearch(text)
            Keys.onPressed: function (e) {
                if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) {
                    columnEditorController.searchStep((e.modifiers & Qt.ShiftModifier) ? -1 : 1); e.accepted = true
                } else if (e.key === Qt.Key_Down) { columnEditorController.searchStep(1); e.accepted = true }
                else if (e.key === Qt.Key_Up) { columnEditorController.searchStep(-1); e.accepted = true }
                else if (e.key === Qt.Key_Escape) {
                    if (text !== "") text = ""
                    else root.forceActiveFocus()
                    e.accepted = true
                }
            }
            Text {
                id: clearSearch
                visible: searchField.text !== ""
                anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                text: "✕"
                font.pixelSize: 10
                color: clearSearchArea.containsMouse ? "#2c3e50" : "#9aa5b1"
                MouseArea { id: clearSearchArea; anchors.fill: parent; anchors.margins: -4; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                           onClicked: searchField.text = "" }
            }
        }
        Text {                                                  // number of matches while searching
            id: searchCount
            visible: searchField.text !== ""
            anchors { left: searchField.right; leftMargin: 6; verticalCenter: parent.verticalCenter }
            width: visible ? implicitWidth : 0
            text: columnConfigModel.matchCount + " von " + columnConfigModel.count
            font.pixelSize: 11
            font.bold: columnConfigModel.matchCount === 0
            color: columnConfigModel.matchCount === 0 ? "#b03a2e" : "#2e9e4f"
        }
        // bulk button, colour legend and the area buttons (Not exported / Hidden / Renamed) moved to TileStatus.qml in the ribbon (owner 2026-11-16)
        Text {                                                  // hint text (elided, never overlaps)
            id: hintText
            anchors { left: searchCount.visible ? searchCount.right : searchField.right; leftMargin: 10; verticalCenter: parent.verticalCenter }
            width: Math.min(implicitWidth, Math.max(0, head.width - x - 8))
            elide: Text.ElideRight
            text: columnConfigModel.count + " Spalten   ·   Strg+Klick = hinzufügen / entfernen  ·  Umschalt+Klick = Bereich  ·  Doppelklick auf das Typ-Kürzel = Typ ändern  ·  Kachel in den anderen Bereich ziehen = übergeben / nicht übergeben"
            font.pixelSize: 11
            color: "#7b8794"
        }
    }

    // --- the two areas ----------------------------------------------------------------------------------------------------
    Item {
        id: areas
        objectName: "tileGrid"
        property int count: columnConfigModel.count
        anchors { top: head.bottom; topMargin: 4; left: parent.left; right: sidePane.left; rightMargin: 8; bottom: note.top; bottomMargin: 2 }

        Repeater {
            id: areaRep
            model: 4                                            // 0 = exported, 1 = not exported, 2 = hidden, 3 = renamed (the last three: right column, up to two open)
            delegate: Rectangle {
                id: area
                readonly property bool exportedArea: index === 0
                readonly property bool hiddenArea: index === 2
                readonly property bool renamedArea: index === 3
                readonly property int tileCount: index === 0 ? columnConfigModel.count - columnConfigModel.notExportedCount - columnConfigModel.hiddenCount
                                                 : index === 1 ? columnConfigModel.notExportedCount
                                                 : index === 2 ? columnConfigModel.hiddenCount
                                                 : columnConfigModel.renamedCount
                readonly property int cols: Math.max(1, Math.floor(flow.width / root.minCell))
                readonly property real cellW: Math.floor(flow.width / cols)
                readonly property bool dropHere: root.dragTarget === index
                readonly property int sidePos: root.openSorted.indexOf(index)     // place in the right-hand column (0 = top), -1 = folded
                readonly property string areaColor: exportedArea ? "#2e9e4f" : hiddenArea ? "#7b8794" : renamedArea ? "#d32f2f" : "#f08c00"
                readonly property string areaFill: exportedArea ? "#eef8f1" : hiddenArea ? "#e5e7eb" : renamedArea ? "#fdecea" : "#ffe9c7"
                function slotAt(r) { return tiles.itemAt(r) }
                function reveal(item) {                         // keep a keyboard-selected tile inside the visible part of the area
                    if (!item) return
                    if (item.y < flick.contentY) flick.contentY = item.y
                    else if (item.y + item.height > flick.contentY + flick.height) flick.contentY = item.y + item.height - flick.height
                }
                x: exportedArea ? 0 : root.areaWidthActive + root.areaGap
                y: exportedArea ? 0 : Math.max(0, sidePos) * (root.sideAreaH + root.areaGap)
                width: exportedArea ? root.areaWidthActive : root.rightColWidth
                height: exportedArea ? areas.height : root.sideAreaH       // one open side area: whole height; two: half each
                visible: exportedArea || sidePos >= 0
                radius: 6
                color: dropHere ? area.areaFill : (exportedArea ? "#fbfcfd" : hiddenArea ? "#f5f6f8" : renamedArea ? "#fffafa" : "#fffaf1")
                border.width: dropHere ? 2 : 1
                border.color: dropHere ? area.areaColor : (exportedArea ? "#c3ccd6" : hiddenArea ? "#d3d9e0" : renamedArea ? "#f1b5b0" : "#f2c98f")

                Text {
                    id: title
                    x: 10; y: 4
                    text: (area.exportedArea ? "Exportierte Spalten" : area.hiddenArea ? "Ausgeblendet" : area.renamedArea ? "Umbenannt" : "Nicht exportiert") + "  (" + area.tileCount + ")"
                    font.pixelSize: 11
                    font.bold: true
                    color: area.exportedArea ? "#34495e" : area.hiddenArea ? "#52606d" : area.renamedArea ? "#b3261e" : "#c2620a"
                }
                Text {
                    visible: index !== 1
                    anchors { left: title.right; leftMargin: 8; right: area.exportedArea ? parent.right : bulkBtn.left; rightMargin: 8; verticalCenter: title.verticalCenter }
                    elide: Text.ElideRight
                    font.pixelSize: 10
                    color: "#7b8794"
                    text: area.exportedArea ? "diese Spalten werden übergeben und mit „Als Excel speichern“ geschrieben"
                                            : area.renamedArea ? "neuer Name auf der Kachel, Originalname darüber – nur Anzeige, die Daten bleiben unverändert"
                                            : "in der Datentabelle ausgeblendet; bleibt Teil der Ansicht (Export bleibt)"
                }
                Text {                                          // index 1 only: leave room for the collapse button
                    visible: index === 1
                    anchors { left: title.right; leftMargin: 8; right: bulkBtn.left; rightMargin: 8; verticalCenter: title.verticalCenter }
                    elide: Text.ElideRight
                    font.pixelSize: 10
                    color: "#7b8794"
                    text: "in der Tabelle sichtbar, nicht exportiert"
                }
                Text {                                          // fold this area again (the buttons in the header line do the same)
                    id: collapseBtn
                    visible: !area.exportedArea
                    anchors { top: parent.top; right: parent.right; topMargin: 2; rightMargin: 4 }
                    text: "«"                                // «
                    font.pixelSize: 13
                    color: collapseArea.containsMouse ? "#2c3e50" : "#9aa5b1"
                    MouseArea { id: collapseArea; anchors.margins: -4; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                               onClicked: root.toggleArea(index) }
                    ToolTip.visible: collapseArea.containsMouse
                    ToolTip.text: "Bereich einklappen"
                }
                Rectangle {                                     // bulk button: "Nicht exportiert" -> hide all in the table, "Ausgeblendet" -> show all again
                    id: bulkBtn
                    visible: area.hiddenArea && area.tileCount > 0                                  // the "Nicht exportiert" one sits in the header line
                    width: bulkText.implicitWidth + 14; height: 16; radius: 3
                    anchors { top: parent.top; topMargin: 3; right: collapseBtn.left; rightMargin: 8 }
                    color: bulkArea.containsMouse ? area.areaFill : "transparent"
                    border.width: 1
                    border.color: area.areaColor
                    Text { id: bulkText; anchors.centerIn: parent; font.pixelSize: 10; color: area.hiddenArea ? "#52606d" : "#c2620a"
                           text: area.hiddenArea || columnConfigModel.tableHiddenCount >= columnConfigModel.notExportedCount ? "Alle in Tabelle einblenden" : "Alle in Tabelle ausblenden" }
                    MouseArea { id: bulkArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                               onClicked: columnEditorController.setAreaHidden(area.hiddenArea ? 2 : 1) }
                    ToolTip.visible: bulkArea.containsMouse
                    ToolTip.text: area.hiddenArea ? "Alle ausgeblendeten Spalten wieder in der Tabelle zeigen (ein Rückgängig-Schritt)"
                                                  : (columnConfigModel.tableHiddenCount >= columnConfigModel.notExportedCount ? "Nicht exportierte Spalten in der Tabelle unten wieder zeigen (ein Rückgängig-Schritt)" : "Alle nicht exportierten Spalten nur in der Tabelle unten ausblenden; die Kacheln bleiben hier, Bereich „Ausgeblendet“ und Export bleiben unverändert (ein Rückgängig-Schritt)")
                }
                Text {                                          // empty "nicht exportiert" / "hidden" area
                    visible: !area.exportedArea && area.tileCount === 0
                    anchors.centerIn: parent
                    width: parent.width - 24
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    font.pixelSize: 11
                    color: area.hiddenArea ? "#9aa5b1" : area.renamedArea ? "#c9a09c" : "#b8a27c"
                    text: area.hiddenArea ? "No column is hidden.\nDrag a tile here, or use the tile menu, to hide it."
                                          : area.renamedArea ? "No column is renamed.\nTile menu > Rename output column ... renames it visually; the data is not changed."
                                          : "No column is left out of the export.\nDrag a tile here to exclude it."
                }

                Flickable {
                    id: flick
                    anchors { top: parent.top; topMargin: 24; left: parent.left; right: parent.right; bottom: parent.bottom; margins: 4 }
                    contentWidth: width
                    contentHeight: flow.height
                    clip: true
                    interactive: contentHeight > height               // no flicking (and no mouse stealing from tile drags) when everything fits
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar { }
                    Flow {
                        id: flow
                        width: flick.width - 10
                        Repeater {
                            id: tiles
                            model: columnConfigModel
                            delegate: Item {
                                id: slot
                                readonly property bool here: model.match && (area.renamedArea ? model.renamed
                                                                              : area.hiddenArea ? model.hidden : (!model.hidden && model.inExport === area.exportedArea))
                                visible: here
                                width: here ? area.cellW : 0
                                height: here ? root.cellH : 0

                                DropIndicator {
                                    id: marker
                                    anchors { left: parent.left; top: parent.top; bottom: parent.bottom; topMargin: 4; bottomMargin: 4 }
                                    active: drop.containsDrag
                                }
                                DropArea {
                                    id: drop
                                    anchors.fill: parent
                                    enabled: slot.here && !area.renamedArea
                                    // insertion drop inside ONE area: only the position is remembered while dragging (the marker shows it);
                                    // the move itself - and with it the rebuild of the table below - happens once, on drop (finishDrag)
                                    onEntered: function (d) {
                                        var from = d.source.slotIndex
                                        var fromHere = area.hiddenArea ? d.source.hiddenColumn
                                                                       : (!d.source.hiddenColumn && d.source.inExport === area.exportedArea)
                                        if (from >= 0 && from !== index && fromHere)
                                            root.pendingMoveTo = index
                                    }
                                    onExited: if (root.pendingMoveTo === index) root.pendingMoveTo = -1
                                }
                                ColumnCard {
                                    id: card
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: slot.width - 8
                                    slotIndex: index
                                    shortName: model.shortName
                                    renamed: model.renamed
                                    originalName: model.originalName
                                    showOriginal: area.renamedArea
                                    protectedColumn: model.protectedColumn
                                    groupColor: model.groupColor
                                    groupName: model.groupName
                                    temporary: model.temporary
                                    splitTile: model.isSplit
                                    chip: model.chip
                                    position: model.position
                                    hiddenColumn: model.hidden
                                    computed: model.calculated
                                    inExport: model.inExport
                                    selOrder: model.selOrder
                                    tip: model.tip
                                    tagColor: model.tagColor
                                    active: index === columnEditorController.selectedRow
                                    dragging: mouse.drag.active
                                    onClicked: { columnEditorController.selectOnly(index); columnEditorController.pickTile(index); root.forceActiveFocus() }
                                    onCtrlClicked: { columnEditorController.toggleSelect(index); root.forceActiveFocus() }
                                    onShiftClicked: function (additive) { columnEditorController.selectRange(index, additive); root.forceActiveFocus() }
                                    onTypeRequested: { if (!columnEditorController.inSelection(index)) columnEditorController.selectOnly(index); root.openType(index) }
                                    onBackRequested: { columnEditorController.selectOnly(index); root.openBack(index) }
                                    onContextRequested: root.openMenu(index)
                                    onXChanged: if (dragging) root.noteDrag(card)
                                    onYChanged: if (dragging) root.noteDrag(card)
                                    onDraggingChanged: if (!dragging) root.finishDrag(index)
                                    states: State {
                                        when: card.mouse.drag.active                   // the dragged tile floats above both areas
                                        ParentChange { target: card; parent: dragLayer }
                                        AnchorChanges { target: card; anchors.horizontalCenter: undefined; anchors.verticalCenter: undefined }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // --- draggable splitter between the exported area and the right-hand column; remembers the width (tileLayout) ----
        Rectangle {
            id: rightSplitter
            visible: root.openAreas.length > 0
            width: 6
            x: root.areaWidthActive - width / 2
            anchors { top: areas.top; bottom: areas.bottom }
            color: rightSplitterArea.containsMouse || rightSplitterArea.pressed ? "#9fb4c7" : "transparent"
            MouseArea {
                id: rightSplitterArea
                anchors.fill: parent
                anchors.margins: -3
                hoverEnabled: true
                cursorShape: Qt.SizeHorCursor
                property real startX: 0
                property real startShare: 0
                onPressed: function (m) { startX = mapToItem(areas, m.x, 0).x; startShare = tileLayout.rightShare }
                onPositionChanged: function (m) {
                    if (!pressed) return
                    var curX = mapToItem(areas, m.x, 0).x
                    var span = Math.max(1, areas.width - root.areaGap)
                    tileLayout.rightShare = startShare + (startX - curX) / span
                }
            }
        }
    }
    Item { id: dragLayer; anchors.fill: parent; z: 100 }

    function noteDrag(card) {                                    // where is the dragged tile right now (area decision at the end of the drag)
        var p = card.mapToItem(areas, card.width / 2, card.height / 2)
        if (p.y >= -20 && p.y <= areas.height + 20 && p.x >= 0 && p.x <= areas.width) {
            dragX = p.x; dragY = p.y
        } else {
            dragX = -1; dragY = -1
        }
    }
    function finishDrag(row) {                                   // tile dropped: exported <-> not exported = export state; into/out of "Ausgeblendet" = visibility
        var target = dragTarget
        var moveTo = pendingMoveTo
        pendingMoveTo = -1
        dragX = -1; dragY = -1
        if (target < 0) return
        if (moveTo >= 0 && moveTo !== row && target === areaOf(row)) {   // dropped on a tile of its own area: the one and only move
            columnEditorController.moveColumn(row, moveTo)
            return
        }
        var wasHidden = columnEditorController.menuInfo(row).allHidden
        if (target === 2) {                                      // dropped on "Ausgeblendet": hide it, export state is kept unchanged
            if (!wasHidden) {
                columnEditorController.setHidden(row, true)
                if (!columnEditorController.inSelection(row)) columnEditorController.selectOnly(row)
            }
            return
        }
        if (wasHidden) columnEditorController.setHidden(row, false)    // dropped out of "Ausgeblendet": show it again ...
        var wantExport = target === 0
        var ex = columnEditorController.exportedAt(row)
        if (ex !== wantExport) {
            columnEditorController.setExport(row, wantExport)       // ... and put it where it was dropped (acts on the whole multi selection)
        }
        if (wasHidden || ex !== wantExport) {
            if (!columnEditorController.inSelection(row)) columnEditorController.selectOnly(row)   // a multi selection stays selected
        }
    }
    function areaOf(row) {                                       // 0 = exported, 1 = not exported, 2 = hidden
        if (columnEditorController.menuInfo(row).allHidden) return 2
        return columnEditorController.exportedAt(row) ? 0 : 1
    }
    function selectedArea() { return areaOf(columnEditorController.selectedRow) }
    function moveFocus(step) {                                   // arrow keys: inside the area of the active tile (a folded area is opened first)
        var r = columnEditorController.selectedRow
        if (r < 0) { r = 0 }
        var nr = columnEditorController.neighbour(r, step)
        if (nr < 0 || nr === columnEditorController.selectedRow) return
        columnEditorController.selectOnly(nr)
        var ar = areaOf(nr)
        if (ar > 0 && !isOpen(ar)) toggleArea(ar)
        var a = areaRep.itemAt(ar)
        if (a) a.reveal(a.slotAt(nr))
    }
    function colsOfSelected() {
        var a = areaRep.itemAt(columnEditorController.selectedRow >= 0 ? selectedArea() : 0)
        return a ? a.cols : 1
    }

    Keys.onPressed: function (e) {
        if ((e.modifiers & Qt.AltModifier) && (e.key === Qt.Key_Left || e.key === Qt.Key_Right)) {
            columnEditorController.moveBy(columnEditorController.selectedRow, e.key === Qt.Key_Left ? -1 : 1)
            e.accepted = true
        } else if (e.key === Qt.Key_Left) { moveFocus(-1); e.accepted = true }
        else if (e.key === Qt.Key_Right) { moveFocus(1); e.accepted = true }
        else if (e.key === Qt.Key_Up) { moveFocus(-colsOfSelected()); e.accepted = true }
        else if (e.key === Qt.Key_Down) { moveFocus(colsOfSelected()); e.accepted = true }
        else if (e.key === Qt.Key_Delete) {
            columnEditorController.toggleHidden(columnEditorController.selectedRow); e.accepted = true
        } else if (e.key === Qt.Key_Escape) {
            if (columnEditorController.hasDraft) columnEditorController.cancelGroup()
            else columnEditorController.clearSelection()
            e.accepted = true
        } else if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_F) {
            searchField.forceActiveFocus(); searchField.selectAll(); e.accepted = true
        } else if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_G) {
            columnEditorController.startGroup(); e.accepted = true
        } else if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_Z) {
            columnEditorController.undo(); e.accepted = true
        } else if ((e.modifiers & Qt.ControlModifier) && e.key === Qt.Key_Y) {
            columnEditorController.redo(); e.accepted = true
        } else if (e.key === Qt.Key_Return || e.key === Qt.Key_Enter) {
            columnEditorController.selectOnly(columnEditorController.selectedRow); e.accepted = true
        }
    }

    function tileItem(r) {                                       // the popovers open below this tile (whichever area shows it)
        for (var i = 0; i < areaRep.count; ++i) {
            var a = areaRep.itemAt(i)
            var it = a ? a.slotAt(r) : null
            if (it && it.visible) return it
        }
        return root
    }
    function openType(r) { typeDialog.parent = tileItem(r); typeDialog.openFor(r) }
    function openBack(r) { backDialog.parent = tileItem(r); backDialog.openFor(r) }          // back side of the tile (one tile at a time)
    function openTransform(r, op) { transformDialog.parent = tileItem(r); transformDialog.openFor(r, op) }
    function openSplit(r) { splitDialog.parent = tileItem(r); splitDialog.openFor(r) }
    function openConditional(r) { conditionalDialog.parent = tileItem(r); conditionalDialog.openFor(r) }
    function openCheck(r) { checkDialog.parent = tileItem(r); checkDialog.openFor(r) }
    function openLookup(r) { lookupDialog.parent = tileItem(r); lookupDialog.openFor(r) }
    function editStep(step) {                                   // pencil of the Steps panel: the dialog of the function, filled with the step's settings
        var info = columnEditorController.stepInfo(step.index)
        var r = columnEditorController.rowOfKey(step.key)
        var anchorRow = r >= 0 ? r : 0
        if (info.kind === "text_op") { transformDialog.parent = tileItem(anchorRow); transformDialog.openFor(info.row >= 0 ? info.row : anchorRow, info.op, step.index) }
        else if (info.kind === "conditional") { conditionalDialog.parent = tileItem(anchorRow); conditionalDialog.openFor(anchorRow, step.index) }
        else if (info.kind === "check_list") { checkDialog.parent = tileItem(anchorRow); checkDialog.openFor(info.row, step.index) }
    }
    function runOp(r, op) {                                     // one-click functions run at once, the others ask first
        var e = columnEditorController.applyTextOp(r, op, { replaceOriginal: true })
        if (e !== "") note.text = e
    }
    function openMenu(row) {
        if (!columnEditorController.inSelection(row)) columnEditorController.selectOnly(row)     // right-click outside the selection = new selection
        tileMenu.row = row
        tileMenu.info = columnEditorController.menuInfo(row)
        tileMenu.popup()
    }

    Menu {
        id: tileMenu
        property int row: -1
        property var info: ({ count: 1, multi: false, allHidden: false, anyExported: true })
        readonly property bool multi: !!info.multi
        readonly property string cols: multi ? info.count + " Spalten" : "column"
        MenuItem { text: tileMenu.multi ? tileMenu.info.count + " Kacheln gewählt" : ""; visible: tileMenu.multi; enabled: false; height: visible ? implicitHeight : 0 }
        MenuItem { text: tileMenu.multi ? "Datentyp ändern: " + tileMenu.cols + "…" : "Datentyp ändern …"; onTriggered: root.openType(tileMenu.row) }
        MenuItem { text: "Ausgabespalte umbenennen …";     enabled: !tileMenu.multi; onTriggered: prompt.askRename(tileMenu.row) }
        MenuItem { text: "Kurzname der Kachel ändern …";   enabled: !tileMenu.multi; onTriggered: prompt.askShort(tileMenu.row) }
        Menu {
            title: tileMenu.multi ? "Umwandeln: " + tileMenu.cols : "Umwandeln"
            MenuItem { text: "Überzählige Leerzeichen entfernen";              onTriggered: root.runOp(tileMenu.row, "trim") }
            MenuItem { text: "Versteckte Zeichen entfernen";         onTriggered: root.runOp(tileMenu.row, "clean") }
            MenuItem { text: "GROSSBUCHSTABEN";                       onTriggered: root.runOp(tileMenu.row, "upper") }
            MenuItem { text: "kleinbuchstaben";                       onTriggered: root.runOp(tileMenu.row, "lower") }
            MenuItem { text: "Jedes Wort Groß";             onTriggered: root.runOp(tileMenu.row, "capitalise") }
            MenuSeparator { }
            MenuItem { text: "Rohrgröße vereinheitlichen …";             onTriggered: root.openTransform(tileMenu.row, "normalise_size") }
            MenuItem { text: "Text ergänzen / mit Nullen auffüllen …";      onTriggered: root.openTransform(tileMenu.row, "format") }
            Menu {
                title: "Extrahieren"
                MenuItem { text: "Erste Zeichen …";            onTriggered: root.openTransform(tileMenu.row, "extract_first") }
                MenuItem { text: "Letzte Zeichen …";             onTriggered: root.openTransform(tileMenu.row, "extract_last") }
                MenuItem { text: "Text vor einem Trennzeichen …";     onTriggered: root.openTransform(tileMenu.row, "extract_before") }
                MenuItem { text: "Text nach einem Trennzeichen …";      onTriggered: root.openTransform(tileMenu.row, "extract_after") }
                MenuItem { text: "Text zwischen zwei Trennzeichen …"; onTriggered: root.openTransform(tileMenu.row, "extract_between") }
            }
        }
        MenuItem { text: "Spalte teilen …";                        enabled: !tileMenu.multi; onTriggered: root.openSplit(tileMenu.row) }
        MenuItem { text: "Werte ersetzen …";                      onTriggered: root.openTransform(tileMenu.row, "replace") }
        Menu {
            title: "Füllen"
            MenuItem { text: "Wert nach unten in leere Zellen kopieren"; onTriggered: root.runOp(tileMenu.row, "fill_down") }
            MenuItem { text: "Wert nach oben in leere Zellen kopieren";   onTriggered: root.runOp(tileMenu.row, "fill_up") }
        }
        MenuItem { text: "Wenn … dann-Spalte …";                    onTriggered: root.openConditional(tileMenu.row) }
        Menu {
            title: "Plant 3D / Listen"
            MenuItem { text: "Gegen Codeliste prüfen …";       enabled: !tileMenu.multi; onTriggered: root.openCheck(tileMenu.row) }
            MenuItem { text: "Spalten aus einer anderen Liste …";   enabled: !tileMenu.multi; onTriggered: root.openLookup(tileMenu.row) }
        }
        MenuSeparator { }
        MenuItem { text: "Nach links";                 onTriggered: columnEditorController.moveBy(tileMenu.row, -1) }
        MenuItem { text: "Nach rechts";                onTriggered: columnEditorController.moveBy(tileMenu.row, 1) }
        MenuItem { text: "An Position verschieben …";         onTriggered: prompt.askPosition(tileMenu.row) }
        MenuSeparator { }
        MenuItem { text: "Gewählte Kacheln gruppieren (Strg+G)"; visible: tileMenu.multi; height: visible ? implicitHeight : 0; onTriggered: columnEditorController.startGroup() }
        MenuItem { text: "Zur Gruppe hinzufügen"; visible: !tileMenu.multi; height: visible ? implicitHeight : 0; onTriggered: columnEditorController.addToGroup(tileMenu.row) }
        MenuItem { text: "Gruppe wählen"; visible: columnEditorController.inGroup(tileMenu.row); height: visible ? implicitHeight : 0
                   onTriggered: columnEditorController.selectGroup(tileMenu.row) }
        MenuItem { text: "Gruppe auflösen"; visible: columnEditorController.inGroup(tileMenu.row); height: visible ? implicitHeight : 0
                   onTriggered: columnEditorController.ungroup(tileMenu.row) }
        MenuItem { text: (tileMenu.info.allHidden ? "Einblenden: " : "Ausblenden: ") + tileMenu.cols; onTriggered: columnEditorController.toggleHidden(tileMenu.row) }
        MenuItem { text: (tileMenu.info.anyExported ? "Nicht exportieren: " : "Exportieren: ") + (tileMenu.info.anyExported ? tileMenu.cols + " nicht exportieren" : tileMenu.cols + " exportieren"); onTriggered: columnEditorController.toggleExport(tileMenu.row) }
        MenuSeparator { }
        MenuItem { text: tileMenu.multi ? "Zurücksetzen: " + tileMenu.cols : "Spalte zurücksetzen"; onTriggered: columnEditorController.resetColumn(tileMenu.row) }
    }

    TextPrompt {
        id: prompt
        property string mode: "rename"
        property int row: -1
        function ask2(m, r, titleText, labelText, value) { mode = m; row = r; parent = root.tileItem(r); ask(titleText, labelText, value) }
        function askRename(r) {
            var i = columnEditorController.inspect(r)
            ask2("rename", r, "Ausgabespalte umbenennen", "Neuer Name (die Daten bleiben unverändert):", i.outputName || "")
        }
        function askShort(r) {
            var i = columnEditorController.inspect(r)
            ask2("short", r, "Kurzname der Kachel ändern", "Text auf der Kachel (leer = automatisch):", i.shortName || "")
        }
        function askPosition(r) {
            ask2("position", r, "An Position verschieben", "Position (1 bis " + columnConfigModel.count + "):", String(r + 1))
        }
        onSubmitted: function (value) {
            var err = ""
            if (mode === "short") err = columnEditorController.setShortName(row, value)
            else if (mode === "position") columnEditorController.moveToPosition(row, parseInt(value))
            else err = columnEditorController.renameOutput(row, value)
            if (err !== "") note.text = err
        }
    }
    ChangeTypeDialog { id: typeDialog }
    TileBackDialog { id: backDialog; objectName: "tileBack"; onChangeTypeRequested: function (r) { root.openType(r) } }
    TransformDialog { id: transformDialog }
    SplitDialog { id: splitDialog }
    ConditionalDialog { id: conditionalDialog }
    CheckDialog { id: checkDialog }
    LookupDialog { id: lookupDialog }

    Text {                                      // short messages (e.g. "die letzte sichtbare Spalte kann nicht ausgeblendet werden"); reserves its own line
        id: note
        anchors { left: parent.left; bottom: parent.bottom }
        height: 14
        color: "#b03a2e"
        font.pixelSize: 11
        elide: Text.ElideRight
        width: areas.width
        text: ""
        Timer { interval: 6000; running: note.text !== ""; onTriggered: note.text = "" }
    }
    Connections {
        target: columnEditorController
        function onMessage(text) { note.text = text }
        function onChangeTypeRequested(row) { root.openType(row) }          // asked by the side pane (flow deck)
        function onEditStepRequested(step) { root.editStep(step) }
        function onDraftChanged() {                              // a group was started (Ctrl+G / Group tiles): open the side pane with the dialog
            if (columnEditorController.hasDraft && tileLayout.sideCollapsed) tileLayout.sideCollapsed = false
        }
        function onSelectedChanged() {                            // active tile changed (also from the table / search): keep it in view
            var r = columnEditorController.selectedRow
            if (r < 0 || r >= columnConfigModel.count) return
            var a = areaRep.itemAt(root.areaOf(r))
            if (a && a.visible) a.reveal(a.slotAt(r))
        }
        function onFunctionRequested(name, row) {                 // ribbon of the host window / cell menu of the table
            if (row < 0 || row >= columnConfigModel.count) return
            columnEditorController.selectOnly(row)
            if (name === "split") root.openSplit(row)
            else if (name === "conditional") root.openConditional(row)
            else if (name === "check") root.openCheck(row)
            else if (name === "lookup") root.openLookup(row)
            else if (name === "type") root.openType(row)
            else root.openTransform(row, name)
        }
    }

    Rectangle {
        id: sidePane
        anchors { top: parent.top; right: parent.right; bottom: parent.bottom }
        width: tileLayout.sideExternal ? 0 : (tileLayout.sideCollapsed ? root.collapsedWidth : tileLayout.sideWidth)   // external: the pane lives in the host's flow deck
        visible: !tileLayout.sideCollapsed && !tileLayout.sideExternal
        color: "#f7f9fb"
        border.color: "#c3ccd6"
        radius: 6
        Text {                                      // collapse this side pane ("Eine Kachel wählen" / Steps)
            id: sideCollapseBtn
            anchors { top: parent.top; right: parent.right; topMargin: 2; rightMargin: 4 }
            text: "»"                            // »
            font.pixelSize: 13
            color: sideCollapseArea.containsMouse ? "#2c3e50" : "#9aa5b1"
            MouseArea { id: sideCollapseArea; anchors.margins: -4; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                       onClicked: tileLayout.sideCollapsed = true }
        }
        Flickable {
            id: side
            anchors { top: sideCollapseBtn.bottom; left: parent.left; right: parent.right; bottom: parent.bottom; margins: 8 }
            contentWidth: width
            contentHeight: sideCol.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { }
            Column {
                id: sideCol
                width: side.width - 10
                spacing: 8
                RuleInspector {
                    width: parent.width
                    row: columnEditorController.selectedRow
                    onChangeTypeRequested: function (r) { root.openType(r) }
                }
                Text {
                    visible: columnEditorController.selectionCount >= 2 && !columnEditorController.hasDraft
                    text: columnEditorController.selectionCount + " Kacheln gewählt. Kacheln gruppieren (Strg+G) öffnet hier den Gruppen-Dialog: Gruppenname, optional verbundene Spalte, optional Kopfzeile in Tabelle / Excel."
                    font.pixelSize: 11; color: "#52606d"; wrapMode: Text.Wrap; width: parent.width
                }
                GroupPanel { width: parent.width }
                StepsPanel { width: parent.width; onEditRequested: function (step) { root.editStep(step) } }
            }
        }
    }

    // --- collapsed side pane: a thin strip with an expand handle --------------------------------------------------------
    Rectangle {
        id: sideCollapsedStrip
        visible: tileLayout.sideCollapsed && !tileLayout.sideExternal
        anchors { top: parent.top; right: parent.right; bottom: parent.bottom }
        width: root.collapsedWidth
        radius: 6
        color: sideExpandArea.containsMouse ? "#eef2f7" : "#f7f9fb"
        border.width: 1
        border.color: "#c3ccd6"
        Text {
            anchors.centerIn: parent
            rotation: 90
            font.pixelSize: 10
            color: "#52606d"
            text: "«  Kachel wählen / Schritte"
        }
        MouseArea { id: sideExpandArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                   onClicked: tileLayout.sideCollapsed = false }
    }

    // --- draggable splitter at the left edge of the side pane; remembers the width (tileLayout) -----------------------
    Rectangle {
        id: sideSplitter
        visible: !tileLayout.sideCollapsed && !tileLayout.sideExternal
        width: 6
        x: sidePane.x - width / 2
        anchors { top: parent.top; bottom: parent.bottom }
        color: sideSplitterArea.containsMouse || sideSplitterArea.pressed ? "#9fb4c7" : "transparent"
        MouseArea {
            id: sideSplitterArea
            anchors.fill: parent
            anchors.margins: -3
            hoverEnabled: true
            cursorShape: Qt.SizeHorCursor
            property real startX: 0
            property real startWidth: 0
            onPressed: function (m) { startX = mapToItem(root, m.x, 0).x; startWidth = tileLayout.sideWidth }
            onPositionChanged: function (m) {
                if (!pressed) return
                var curX = mapToItem(root, m.x, 0).x
                tileLayout.sideWidth = startWidth + (startX - curX)
            }
        }
    }
}
