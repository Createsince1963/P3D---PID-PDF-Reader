// Transform dialog (Replace values / Add text / Normalise pipe size) as a small popover below the tile it belongs to.
// It always shows Before -> After for the first changing cells and the number of changed cells before anything happens.
// "Anwenden" creates a calculated column (green tile) and one step in the Steps panel; the source is never changed.
import QtQuick
import QtQuick.Controls

Popup {
    id: dlg
    property int row: -1
    property string op: "replace"
    property int count: 1
    property var preview: ({ rows: [], error: "", changed: 0, total: 0, unrecognised: 0 })
    property string applyError: ""
    property int editIndex: -1                                  // >= 0: change the settings of this step instead of creating a new one
    readonly property bool usesFind: op === "replace" || op === "extract_before" || op === "extract_after" || op === "extract_between" || op === "split_part"
    readonly property var titles: ({ replace: "Werte ersetzen", format: "Text ergänzen / mit Nullen auffüllen", normalise_size: "Rohrgröße vereinheitlichen",
        extract_first: "Erste Zeichen", extract_last: "Letzte Zeichen", extract_before: "Text vor einem Trennzeichen",
        extract_after: "Text nach einem Trennzeichen", extract_between: "Text zwischen zwei Trennzeichen",
        split_part: "Teil", split_fixed: "An festen Positionen teilen", fill_value: "Leere Zellen mit einem Wert füllen" })

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
        return { find: findField.text, replaceWith: withField.text, wholeCell: wholeCheck.checked, matchCase: caseCheck.checked,
                 prefix: preField.text, suffix: sufField.text, padWidth: parseInt(padField.text) || 0,
                 number: parseInt(numField.text) || 0, find2: find2Field.text, start: parseInt(startField.text) || 0,
                 bareNumbers: bareCombo.currentValue, replaceOriginal: origCheck.checked }
    }
    function refresh() { if (row >= 0) preview = columnEditorController.previewTextOp(row, op, options()) }
    function openFor(r, operation, stepIndex) {
        row = r
        op = operation
        editIndex = stepIndex === undefined ? -1 : stepIndex
        count = editIndex >= 0 ? 1 : columnEditorController.menuInfo(r).count
        applyError = ""
        findField.text = ""; withField.text = ""; preField.text = ""; sufField.text = ""; padField.text = ""; numField.text = ""; find2Field.text = ""; startField.text = ""
        wholeCheck.checked = false; caseCheck.checked = false; bareCombo.currentIndex = 0; origCheck.checked = true
        if (editIndex >= 0) {                                   // start with the settings the step has now
            var o = columnEditorController.stepInfo(editIndex).options || {}
            findField.text = o.find || ""; withField.text = o.replaceWith || ""; preField.text = o.prefix || ""; sufField.text = o.suffix || ""
            padField.text = o.padWidth ? String(o.padWidth) : ""; numField.text = o.number ? String(o.number) : ""; find2Field.text = o.find2 || ""; startField.text = o.start ? String(o.start) : ""
            wholeCheck.checked = !!o.wholeCell; caseCheck.checked = !!o.matchCase; bareCombo.currentIndex = o.bareNumbers === "dn" ? 1 : 0
        }
        refresh()
        open()
    }
    onOpened: (usesFind ? findField : (op === "fill_value" ? withField : (op === "format" ? preField : (op === "normalise_size" ? bareCombo : numField)))).forceActiveFocus()

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
                text: (dlg.editIndex >= 0 ? "Schritt ändern: " : "") + (dlg.titles[dlg.op] || dlg.op) + (dlg.count > 1 ? "  (" + dlg.count + " Spalten)" : "")
                font.bold: true; font.pixelSize: 12; elide: Text.ElideRight; width: parent.width
            }
            Text {
                text: dlg.count > 1 ? "Gilt für alle gewählten Kacheln. Vorschau: " + (preview.label || "") : "Spalte: " + (preview.label || "")
                font.pixelSize: 10; color: "#52606d"; elide: Text.ElideRight; width: parent.width
            }
            Row {
                visible: dlg.usesFind; spacing: 6
                Text { text: dlg.op === "replace" ? "Suchen nach" : "Trennzeichen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: findField; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; Accessible.name: "Gesuchter Text"; onTextEdited: dlg.refresh() }
            }
            Row {
                visible: dlg.op === "replace" || dlg.op === "fill_value"; spacing: 6
                Text { text: dlg.op === "fill_value" ? "Füllen mit" : "Ersetzen durch"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: withField; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: dlg.op === "fill_value" ? "Wert für jede leere Zelle" : "(leer = entfernen)"; Accessible.name: dlg.op === "fill_value" ? "Füllen mit" : "Ersetzen durch"; onTextEdited: dlg.refresh() }
            }
            Row {
                visible: dlg.op === "extract_between"; spacing: 6
                Text { text: "Bis"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: find2Field; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "zweites Trennzeichen"; Accessible.name: "Zweites Trennzeichen"; onTextEdited: dlg.refresh() }
            }
            Row {
                visible: dlg.op === "extract_first" || dlg.op === "extract_last" || dlg.op === "split_part" || dlg.op === "split_fixed"; spacing: 6
                Text { text: dlg.op === "split_part" ? "Teil Nr." : "Zeichen"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: numField; width: 60; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; inputMethodHints: Qt.ImhDigitsOnly; Accessible.name: "Anzahl Zeichen"; onTextEdited: dlg.refresh() }
            }
            Row {
                visible: dlg.op === "split_fixed"; spacing: 6
                Text { text: "Beginnt bei"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: startField; width: 60; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; inputMethodHints: Qt.ImhDigitsOnly; Accessible.name: "Startposition"; onTextEdited: dlg.refresh() }
            }
            CheckBox { id: wholeCheck; visible: dlg.op === "replace"; text: "Nur wenn die ganze Zelle gleich ist"; font.pixelSize: 11; onToggled: dlg.refresh() }
            CheckBox { id: caseCheck; visible: dlg.op === "replace"; text: "Groß-/Kleinschreibung beachten"; font.pixelSize: 11; onToggled: dlg.refresh() }
            Row {
                visible: dlg.op === "format"; spacing: 6
                Text { text: "Text vor"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: preField; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; Accessible.name: "Text vor"; onTextEdited: dlg.refresh() }
            }
            Row {
                visible: dlg.op === "format"; spacing: 6
                Text { text: "Text nach"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: sufField; width: 220; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; Accessible.name: "Text nach"; onTextEdited: dlg.refresh() }
            }
            Row {
                visible: dlg.op === "format"; spacing: 6
                Text { text: "Mit 0 auffüllen auf"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: padField; width: 60; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "digits"; inputMethodHints: Qt.ImhDigitsOnly; Accessible.name: "Anzahl Stellen"; onTextEdited: dlg.refresh() }
                Text { text: "Stellen, z. B. 4 -> 0004"; font.pixelSize: 10; color: "#52606d"; anchors.verticalCenter: parent.verticalCenter }
            }
            Row {
                visible: dlg.op === "normalise_size"; spacing: 6
                Text { text: "Reine Zahl"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                ComboBox {
                    id: bareCombo
                    model: [{ text: "ist Zoll  (40 -> 40\")", value: "inch" }, { text: "ist DN  (40 -> 1 1/2\")", value: "dn" }]
                    textRole: "text"; valueRole: "value"
                    implicitWidth: 220; implicitHeight: 26; font.pixelSize: 11
                    Accessible.name: "Bedeutung einer reinen Zahl"
                    onActivated: dlg.refresh()
                }
            }
            CheckBox { id: origCheck; visible: dlg.editIndex < 0; text: "Originalspalte ausblenden und nicht exportieren"; font.pixelSize: 11; checked: true }
            Text {
                visible: !preview.error
                text: (preview.changed || 0).toLocaleString() + " von " + (preview.total || 0).toLocaleString() + " Zellen der Vorschauzeilen ändern sich"
                      + (preview.unrecognised ? "  ·  " + preview.unrecognised + " nicht erkannt (bleiben unverändert)" : "")
                font.pixelSize: 10; font.bold: true; color: "#34495e"; wrapMode: Text.Wrap; width: parent.width
            }
            Text { visible: !!preview.error; text: preview.error || ""; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Repeater {
                model: (preview.rows || []).slice(0, 5)
                delegate: Row {
                    spacing: 6
                    Text { text: modelData.before === "" ? "(leer)" : modelData.before; font.pixelSize: 10; width: 135; elide: Text.ElideRight }
                    Text { text: "→"; font.pixelSize: 10 }
                    Text { text: modelData.after === "" ? "(leer)" : modelData.after; font.pixelSize: 10; width: 135; elide: Text.ElideRight }
                }
            }
            Text { visible: dlg.applyError !== ""; text: dlg.applyError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                spacing: 6
                Button {
                    text: dlg.editIndex >= 0 ? "Änderung speichern" : "Anwenden"
                    implicitHeight: 26; font.pixelSize: 11
                    enabled: !preview.error
                    Accessible.name: "Anwenden"
                    onClicked: {
                        dlg.applyError = dlg.editIndex >= 0 ? columnEditorController.editTextStep(dlg.editIndex, dlg.options())
                                                           : columnEditorController.applyTextOp(dlg.row, dlg.op, dlg.options())
                        if (dlg.applyError === "") dlg.close()
                    }
                }
                Button { text: "Abbrechen"; implicitHeight: 26; font.pixelSize: 11; onClicked: dlg.close() }
            }
        }
    }
}
