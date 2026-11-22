// If-then column: a new calculated column whose value comes from rules (first matching rule wins, otherwise the "else" value).
// Also used to change the rules of an existing step (editIndex >= 0). The source is never changed.
import QtQuick
import QtQuick.Controls

Popup {
    id: dlg
    property int editIndex: -1
    property var rules: []                      // [{column, operator, value, result}]
    property var choices: []                    // [{key, label}]
    property var operators: []                  // [{key, label, noValue}]
    property var preview: ({ ok: false, rows: [], counts: [], error: "" })
    property string applyError: ""

    modal: false
    dim: false
    focus: true
    closePolicy: Popup.CloseOnEscape
    parent: Overlay.overlay
    x: 0
    y: parent ? parent.height - 2 : 0
    margins: 6
    padding: 8
    width: Math.min(470, (Overlay.overlay ? Overlay.overlay.width : 470) - 12)
    background: Rectangle { color: "#ffffff"; border.color: "#7f9bb5"; border.width: 1; radius: 5 }

    function spec() { return { rules: rules, elseValue: elseField.text, ignoreCase: !caseCheck.checked } }
    function refresh() { preview = columnEditorController.previewConditional(spec()) }
    function indexOfKey(list, key) { for (var i = 0; i < list.length; i++) if (list[i].key === key) return i; return 0 }
    function setRule(i, field, value) {                         // edited in place: re-assigning "rules" would rebuild the fields while typing
        rules[i][field] = value
        refresh()
    }
    function addRule() {
        var r = rules.slice()
        r.push({ column: choices.length ? choices[0].key : "", operator: "equals", value: "", result: "" })
        rules = r
        refresh()
    }
    function removeRule(i) { var r = rules.slice(); r.splice(i, 1); rules = r; refresh() }
    function openFor(row, stepIndex) {
        choices = columnEditorController.columnChoices()
        operators = columnEditorController.conditionOperators()
        editIndex = stepIndex === undefined ? -1 : stepIndex
        applyError = ""
        if (editIndex >= 0) {
            var info = columnEditorController.stepInfo(editIndex)
            rules = info.spec.rules
            elseField.text = info.spec.elseValue || ""
            caseCheck.checked = info.spec.ignoreCase === false
            nameField.text = info.name || ""
        } else {
            var key = row >= 0 && row < choices.length ? choices[row].key : (choices.length ? choices[0].key : "")
            rules = [{ column: key, operator: "equals", value: "", result: "" }]
            elseField.text = ""; caseCheck.checked = false; nameField.text = ""
        }
        refresh()
        open()
    }

    contentItem: Flickable {
        clip: true
        implicitHeight: Math.min(body.implicitHeight, 470)
        contentHeight: body.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        Column {
            id: body
            width: parent.width
            spacing: 5
            Text { text: dlg.editIndex >= 0 ? "Schritt ändern: Wenn … dann-Spalte" : "Wenn … dann-Spalte"; font.bold: true; font.pixelSize: 12 }
            Row {
                visible: dlg.editIndex < 0; spacing: 6
                Text { text: "Spaltenname"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: nameField; width: 260; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; Accessible.name: "Name der neuen Spalte" }
            }
            Repeater {
                model: dlg.rules
                delegate: Rectangle {
                    width: body.width; height: ruleCol.implicitHeight + 8
                    color: "#f7f9fb"; border.color: "#dde3ea"; radius: 4
                    Column {
                        id: ruleCol
                        x: 6; y: 4; width: parent.width - 12; spacing: 3
                        Row {
                            spacing: 4
                            Text { text: index === 0 ? "Wenn" : "Sonst wenn"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 40 }
                            ComboBox {
                                model: dlg.choices; textRole: "label"; implicitWidth: 150; implicitHeight: 26; font.pixelSize: 11
                                currentIndex: dlg.indexOfKey(dlg.choices, modelData.column)
                                Accessible.name: "Spalte der Regel " + (index + 1)
                                onActivated: dlg.setRule(index, "column", dlg.choices[currentIndex].key)
                            }
                            ComboBox {
                                id: opBox
                                model: dlg.operators; textRole: "label"; implicitWidth: 130; implicitHeight: 26; font.pixelSize: 11
                                currentIndex: dlg.indexOfKey(dlg.operators, modelData.operator)
                                Accessible.name: "Bedingung der Regel " + (index + 1)
                                onActivated: dlg.setRule(index, "operator", dlg.operators[currentIndex].key)
                            }
                            ToolButton {
                                text: "×"; width: 24; height: 26; enabled: dlg.rules.length > 1; Accessible.name: "Regel entfernen " + (index + 1)
                                onClicked: dlg.removeRule(index)
                            }
                        }
                        Row {
                            spacing: 4
                            Text { text: "value"; font.pixelSize: 10; color: "#52606d"; anchors.verticalCenter: parent.verticalCenter; width: 40 }
                            TextField {
                                width: 130; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true
                                enabled: !dlg.operators[opBox.currentIndex].noValue
                                text: modelData.value; placeholderText: dlg.operators[opBox.currentIndex].key === "in_list" ? "a, b, c" : ""
                                Accessible.name: "Wert der Regel " + (index + 1)
                                onTextEdited: dlg.setRule(index, "value", text)
                            }
                            Text { text: "then"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                            TextField {
                                width: 130; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true
                                text: modelData.result; Accessible.name: "Ergebnis der Regel " + (index + 1)
                                onTextEdited: dlg.setRule(index, "result", text)
                            }
                        }
                    }
                }
            }
            Button { text: "+ Regel hinzufügen"; implicitHeight: 24; font.pixelSize: 11; onClicked: dlg.addRule() }
            Row {
                spacing: 6
                Text { text: "Sonst"; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter; width: 78 }
                TextField { id: elseField; width: 200; implicitHeight: 26; font.pixelSize: 11; selectByMouse: true; placeholderText: "(leer)"; Accessible.name: "Sonst-Wert"; onTextEdited: dlg.refresh() }
            }
            CheckBox { id: caseCheck; text: "Groß-/Kleinschreibung beachten"; font.pixelSize: 11; onToggled: dlg.refresh() }
            Text { visible: !!preview.error; text: preview.error || ""; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Text {
                visible: !preview.error && (preview.counts || []).length > 0
                text: "Ergebnis in den Vorschauzeilen:  " + (preview.counts || []).join("   ·   ")
                font.pixelSize: 10; font.bold: true; color: "#34495e"; wrapMode: Text.Wrap; width: parent.width
            }
            Repeater {
                model: (preview.rows || []).slice(0, 4)
                delegate: Row {
                    spacing: 6
                    Text { text: modelData.before; font.pixelSize: 10; width: 250; elide: Text.ElideRight }
                    Text { text: "→"; font.pixelSize: 10 }
                    Text { text: modelData.after === "" ? "(leer)" : modelData.after; font.pixelSize: 10; width: 120; elide: Text.ElideRight }
                }
            }
            Text { visible: dlg.applyError !== ""; text: dlg.applyError; font.pixelSize: 10; color: "#b03a2e"; wrapMode: Text.Wrap; width: parent.width }
            Row {
                spacing: 6
                Button {
                    text: dlg.editIndex >= 0 ? "Änderung speichern" : "Anwenden"; implicitHeight: 26; font.pixelSize: 11
                    enabled: !!preview.ok
                    onClicked: {
                        dlg.applyError = dlg.editIndex >= 0 ? columnEditorController.editConditionalStep(dlg.editIndex, dlg.spec())
                                                            : columnEditorController.applyConditional(nameField.text, dlg.spec())
                        if (dlg.applyError === "") dlg.close()
                    }
                }
                Button { text: "Abbrechen"; implicitHeight: 26; font.pixelSize: 11; onClicked: dlg.close() }
            }
        }
    }
}
