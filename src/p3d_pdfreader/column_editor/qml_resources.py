# Resource object code (Python 3)
# Created by: object code
# Created by: The Resource Compiler for Qt version 6.11.0
# WARNING! All changes made in this file will be lost!

from PySide6 import QtCore

qt_resource_data = b"\
\x00\x00$S\
/\
/ \x22Spaltentyp \xc3\xa4\
ndern\x22 as a smal\
l popover that o\
pens right below\
 the selected ti\
le (no dimming, \
no centred windo\
w).\x0d\x0a// A change\
 is never silent\
: it creates an \
explicit convert\
 step and shows \
source type, out\
put type, format\
, invalid-value\x0d\
\x0a// behaviour an\
d a short previe\
w. With several \
selected tiles t\
he same type is \
applied to all o\
f them (all or n\
othing).\x0d\x0aimport\
 QtQuick\x0d\x0aimport\
 QtQuick.Control\
s\x0d\x0a\x0d\x0aPopup {\x0d\x0a  \
  id: dlg\x0d\x0a    p\
roperty int row:\
 -1\x0d\x0a    propert\
y int count: 1  \
                \
       // tiles \
the change is ap\
plied to\x0d\x0a    pr\
operty var info:\
 ({})\x0d\x0a    prope\
rty var preview:\
 ({ rows: [], er\
ror: \x22\x22 })\x0d\x0a    \
property string \
applyError: \x22\x22\x0d\x0a\
    readonly pro\
perty string sel\
: typeCombo.curr\
entValue ? typeC\
ombo.currentValu\
e : \x22text\x22\x0d\x0a    \
readonly propert\
y bool numeric: \
sel === \x22integer\
\x22 || sel === \x22de\
cimal\x22 || sel ==\
= \x22percentage\x22\x0d\x0a\
    readonly pro\
perty bool dated\
: sel === \x22date\x22\
 || sel === \x22dat\
etime\x22 || sel ==\
= \x22time\x22\x0d\x0a    re\
adonly property \
var typeModel: [\
\x0d\x0a        { text\
: \x22Text\x22, value:\
 \x22text\x22 }, { tex\
t: \x22Ganzzahl\x22, v\
alue: \x22integer\x22 \
},\x0d\x0a        { te\
xt: \x22Dezimalzahl\
\x22, value: \x22decim\
al\x22 }, { text: \x22\
Prozent\x22, value:\
 \x22percentage\x22 },\
\x0d\x0a        { text\
: \x22Wahr/Falsch\x22,\
 value: \x22boolean\
\x22 }, { text: \x22Da\
tum\x22, value: \x22da\
te\x22 }, { text: \x22\
Zeit\x22, value: \x22t\
ime\x22 },\x0d\x0a       \
 { text: \x22Datum/\
Zeit\x22, value: \x22d\
atetime\x22 }, { te\
xt: \x22Dauer\x22, val\
ue: \x22duration\x22 }\
, { text: \x22Gemis\
cht\x22, value: \x22mi\
xed\x22 },\x0d\x0a       \
 { text: \x22Automa\
tisch erkennen\x22,\
 value: \x22auto\x22 }\
, { text: \x22Quell\
typ beibehalten\x22\
, value: \x22source\
\x22 }]\x0d\x0a\x0d\x0a    moda\
l: false\x0d\x0a    di\
m: false\x0d\x0a    fo\
cus: true\x0d\x0a    c\
losePolicy: Popu\
p.CloseOnEscape \
| Popup.CloseOnP\
ressOutside\x0d\x0a   \
 parent: Overlay\
.overlay\x0d\x0a    x:\
 0\x0d\x0a    y: paren\
t ? parent.heigh\
t - 2 : 0       \
     // directly\
 below the tile \
(the grid sets `\
parent` to the t\
ile before openi\
ng)\x0d\x0a    margins\
: 6             \
                \
      // Qt keep\
s the popover in\
side the window\x0d\
\x0a    padding: 8\x0d\
\x0a    width: Math\
.min(330, (Overl\
ay.overlay ? Ove\
rlay.overlay.wid\
th : 330) - 12)\x0d\
\x0a    background:\
 Rectangle { col\
or: \x22#ffffff\x22; b\
order.color: \x22#7\
f9bb5\x22; border.w\
idth: 1; radius:\
 5 }\x0d\x0a\x0d\x0a    func\
tion options() {\
\x0d\x0a        return\
 { dateFormat: d\
ateField.text, d\
ecimalSeparator:\
 decCombo.curren\
tValue,\x0d\x0a       \
          thousa\
ndsSeparator: th\
ouCombo.currentV\
alue, onInvalid:\
 invCombo.curren\
tValue }\x0d\x0a    }\x0d\
\x0a    function re\
fresh() {\x0d\x0a     \
   if (row < 0) \
return\x0d\x0a        \
preview = column\
EditorController\
.previewType(row\
, sel, options()\
)\x0d\x0a    }\x0d\x0a    fu\
nction openFor(r\
) {\x0d\x0a        row\
 = r\x0d\x0a        in\
fo = columnEdito\
rController.type\
Info(r)\x0d\x0a       \
 count = columnE\
ditorController.\
menuInfo(r).coun\
t\x0d\x0a        apply\
Error = \x22\x22\x0d\x0a    \
    typeCombo.cu\
rrentIndex = Mat\
h.max(0, typeCom\
bo.indexOfValue(\
info.outputType)\
)\x0d\x0a        dateF\
ield.text = info\
.dateFormat || \x22\
\x22\x0d\x0a        decCo\
mbo.currentIndex\
 = Math.max(0, d\
ecCombo.indexOfV\
alue(info.decima\
lSeparator))\x0d\x0a  \
      thouCombo.\
currentIndex = M\
ath.max(0, thouC\
ombo.indexOfValu\
e(info.thousands\
Separator))\x0d\x0a   \
     invCombo.cu\
rrentIndex = Mat\
h.max(0, invComb\
o.indexOfValue(i\
nfo.onInvalid))\x0d\
\x0a        refresh\
()\x0d\x0a        open\
()\x0d\x0a    }\x0d\x0a\x0d\x0a   \
 contentItem: Fl\
ickable {\x0d\x0a     \
   clip: true\x0d\x0a \
       implicitH\
eight: Math.min(\
body.implicitHei\
ght, 430)\x0d\x0a     \
   contentHeight\
: body.implicitH\
eight\x0d\x0a        b\
oundsBehavior: F\
lickable.StopAtB\
ounds\x0d\x0a        C\
olumn {\x0d\x0a       \
     id: body\x0d\x0a \
           width\
: parent.width\x0d\x0a\
            spac\
ing: 5\x0d\x0a        \
    Text {\x0d\x0a    \
            text\
: dlg.count > 1 \
? \x22Typ \xc3\xa4ndern: \
\x22 + dlg.count + \
\x22 Spalten\x22 : \x22Ty\
p von  \x22 + (info\
.label || \x22\x22)\x0d\x0a \
               f\
ont.bold: true; \
font.pixelSize: \
12; elide: Text.\
ElideRight; widt\
h: parent.width\x0d\
\x0a            }\x0d\x0a\
            Text\
 {\x0d\x0a            \
    text: dlg.co\
unt > 1 ? \x22Gilt \
f\xc3\xbcr alle gew\xc3\xa4h\
lten Kacheln (al\
le oder keine). \
Vorschau: \x22 + (i\
nfo.label || \x22\x22)\
\x0d\x0a              \
                \
      : \x22Quellty\
p: \x22 + (info.sou\
rceType || \x22\x22)\x0d\x0a\
                \
font.pixelSize: \
10; color: \x22#526\
06d\x22; elide: Tex\
t.ElideRight; wi\
dth: parent.widt\
h\x0d\x0a            }\
\x0d\x0a            Ro\
w {\x0d\x0a           \
     spacing: 6\x0d\
\x0a               \
 Text { text: \x22A\
usgabetyp\x22; font\
.pixelSize: 11; \
anchors.vertical\
Center: parent.v\
erticalCenter; w\
idth: 92 }\x0d\x0a    \
            Comb\
oBox {\x0d\x0a        \
            id: \
typeCombo\x0d\x0a     \
               m\
odel: dlg.typeMo\
del\x0d\x0a           \
         textRol\
e: \x22text\x22; value\
Role: \x22value\x22\x0d\x0a \
                \
   implicitWidth\
: 190; implicitH\
eight: 26; font.\
pixelSize: 11\x0d\x0a \
                \
   Accessible.na\
me: \x22Ausgabetyp\x22\
\x0d\x0a              \
      onActivate\
d: dlg.refresh()\
\x0d\x0a              \
  }\x0d\x0a           \
 }\x0d\x0a            \
Row {\x0d\x0a         \
       visible: \
dlg.dated\x0d\x0a     \
           spaci\
ng: 6\x0d\x0a         \
       Text { te\
xt: \x22Format\x22; fo\
nt.pixelSize: 11\
; anchors.vertic\
alCenter: parent\
.verticalCenter;\
 width: 92 }\x0d\x0a  \
              Te\
xtField {\x0d\x0a     \
               i\
d: dateField\x0d\x0a  \
                \
  width: 190; im\
plicitHeight: 26\
; font.pixelSize\
: 11\x0d\x0a          \
          placeh\
olderText: \x22auto\
matisch, z. B. %\
d.%m.%Y\x22\x0d\x0a      \
              se\
lectByMouse: tru\
e\x0d\x0a             \
       Accessibl\
e.name: \x22Datumsf\
ormat\x22\x0d\x0a        \
            onTe\
xtEdited: dlg.re\
fresh()\x0d\x0a       \
         }\x0d\x0a    \
        }\x0d\x0a     \
       Row {\x0d\x0a  \
              vi\
sible: dlg.numer\
ic\x0d\x0a            \
    spacing: 6\x0d\x0a\
                \
Text { text: \x22De\
zimaltr.\x22; font.\
pixelSize: 11; a\
nchors.verticalC\
enter: parent.ve\
rticalCenter; wi\
dth: 92 }\x0d\x0a     \
           Combo\
Box {\x0d\x0a         \
           id: d\
ecCombo\x0d\x0a       \
             mod\
el: [{ text: \x22Pu\
nkt  .\x22, value: \
\x22.\x22 }, { text: \x22\
Komma  ,\x22, value\
: \x22,\x22 }]\x0d\x0a      \
              te\
xtRole: \x22text\x22; \
valueRole: \x22valu\
e\x22\x0d\x0a            \
        implicit\
Width: 190; impl\
icitHeight: 26; \
font.pixelSize: \
11\x0d\x0a            \
        Accessib\
le.name: \x22Dezima\
ltrennzeichen\x22\x0d\x0a\
                \
    onActivated:\
 dlg.refresh()\x0d\x0a\
                \
}\x0d\x0a            }\
\x0d\x0a            Ro\
w {\x0d\x0a           \
     visible: dl\
g.numeric\x0d\x0a     \
           spaci\
ng: 6\x0d\x0a         \
       Text { te\
xt: \x22Tausendertr\
.\x22; font.pixelSi\
ze: 11; anchors.\
verticalCenter: \
parent.verticalC\
enter; width: 92\
 }\x0d\x0a            \
    ComboBox {\x0d\x0a\
                \
    id: thouComb\
o\x0d\x0a             \
       model: [{\
 text: \x22Komma  ,\
\x22, value: \x22,\x22 },\
 { text: \x22Punkt \
 .\x22, value: \x22.\x22 \
}, { text: \x22Leer\
zeichen\x22, value:\
 \x22 \x22 }, { text: \
\x22Keins\x22, value: \
\x22\x22 }]\x0d\x0a         \
           textR\
ole: \x22text\x22; val\
ueRole: \x22value\x22\x0d\
\x0a               \
     implicitWid\
th: 190; implici\
tHeight: 26; fon\
t.pixelSize: 11\x0d\
\x0a               \
     Accessible.\
name: \x22Tausender\
trennzeichen\x22\x0d\x0a \
                \
   onActivated: \
dlg.refresh()\x0d\x0a \
               }\
\x0d\x0a            }\x0d\
\x0a            Row\
 {\x0d\x0a            \
    spacing: 6\x0d\x0a\
                \
Text { text: \x22Un\
g\xc3\xbcltige Werte\x22;\
 font.pixelSize:\
 11; anchors.ver\
ticalCenter: par\
ent.verticalCent\
er; width: 92 }\x0d\
\x0a               \
 ComboBox {\x0d\x0a   \
                \
 id: invCombo\x0d\x0a \
                \
   model: [{ tex\
t: \x22Leeren und m\
arkieren\x22, value\
: \x22empty_flag\x22 }\
, { text: \x22Origi\
nal behalten und\
 markieren\x22, val\
ue: \x22flag\x22 },\x0d\x0a \
                \
           { tex\
t: \x22Leeren\x22, val\
ue: \x22empty\x22 }, {\
 text: \x22Vorgang \
abbrechen\x22, valu\
e: \x22abort\x22 }]\x0d\x0a \
                \
   textRole: \x22te\
xt\x22; valueRole: \
\x22value\x22\x0d\x0a       \
             imp\
licitWidth: 190;\
 implicitHeight:\
 26; font.pixelS\
ize: 11\x0d\x0a       \
             Acc\
essible.name: \x22V\
erhalten bei ung\
\xc3\xbcltigen Werten\x22\
\x0d\x0a              \
      onActivate\
d: dlg.refresh()\
\x0d\x0a              \
  }\x0d\x0a           \
 }\x0d\x0a            \
Text {\x0d\x0a        \
        text: (i\
nfo.sourceType |\
| \x22\x22) + \x22  \xe2\x86\x92  \
\x22 + typeCombo.cu\
rrentText + (pre\
view.format ? \x22 \
  (\x22 + preview.f\
ormat + \x22)\x22 : \x22\x22\
)\x0d\x0a             \
   font.pixelSiz\
e: 10; font.bold\
: true; color: \x22\
#34495e\x22; elide:\
 Text.ElideRight\
; width: parent.\
width\x0d\x0a         \
   }\x0d\x0a          \
  Text { visible\
: !!preview.note\
; text: preview.\
note || \x22\x22; font\
.pixelSize: 10; \
color: \x22#52606d\x22\
; wrapMode: Text\
.Wrap; width: pa\
rent.width }\x0d\x0a  \
          Text {\
 visible: !!prev\
iew.error; text:\
 preview.error |\
| \x22\x22; font.pixel\
Size: 10; color:\
 \x22#b03a2e\x22; wrap\
Mode: Text.Wrap;\
 width: parent.w\
idth }\x0d\x0a        \
    Repeater {\x0d\x0a\
                \
model: (preview.\
rows || []).slic\
e(0, 4)\x0d\x0a       \
         delegat\
e: Row {\x0d\x0a      \
              sp\
acing: 6\x0d\x0a      \
              Te\
xt { text: model\
Data.source; fon\
t.pixelSize: 10;\
 width: 130; eli\
de: Text.ElideRi\
ght }\x0d\x0a         \
           Text \
{ text: \x22\xe2\x86\x92\x22; f\
ont.pixelSize: 1\
0 }\x0d\x0a           \
         Text {\x0d\
\x0a               \
         text: m\
odelData.result \
=== \x22\x22 ? \x22(leer)\
\x22 : modelData.re\
sult\x0d\x0a          \
              fo\
nt.pixelSize: 10\
; width: 130; el\
ide: Text.ElideR\
ight\x0d\x0a          \
              co\
lor: modelData.v\
alid ? \x22#1f2933\x22\
 : \x22#b03a2e\x22\x0d\x0a  \
                \
  }\x0d\x0a           \
     }\x0d\x0a        \
    }\x0d\x0a         \
   Text { visibl\
e: dlg.applyErro\
r !== \x22\x22; text: \
dlg.applyError; \
font.pixelSize: \
10; color: \x22#b03\
a2e\x22; wrapMode: \
Text.Wrap; width\
: parent.width }\
\x0d\x0a            Ro\
w {\x0d\x0a           \
     spacing: 6\x0d\
\x0a               \
 Button {\x0d\x0a     \
               t\
ext: \x22Anwenden\x22\x0d\
\x0a               \
     implicitHei\
ght: 26; font.pi\
xelSize: 11\x0d\x0a   \
                \
 enabled: !previ\
ew.error\x0d\x0a      \
              Ac\
cessible.name: \x22\
Typ\xc3\xa4nderung anw\
enden\x22\x0d\x0a        \
            onCl\
icked: {\x0d\x0a      \
                \
  dlg.applyError\
 = columnEditorC\
ontroller.applyT\
ype(dlg.row, dlg\
.sel, dlg.option\
s())\x0d\x0a          \
              if\
 (dlg.applyError\
 === \x22\x22) dlg.clo\
se()\x0d\x0a          \
          }\x0d\x0a   \
             }\x0d\x0a\
                \
Button { text: \x22\
Abbrechen\x22; impl\
icitHeight: 26; \
font.pixelSize: \
11; onClicked: d\
lg.close() }\x0d\x0a  \
          }\x0d\x0a   \
     }\x0d\x0a    }\x0d\x0a}\
\x0d\x0a\
\x00\x00\x13\xbe\
/\
/ Steps panel: e\
very change made\
 in the tile edi\
tor (change type\
, group, Transfo\
rm functions) as\
 one line, in th\
e order it was m\
ade.\x0d\x0a// Click a\
 line = select i\
ts tile. Arrows \
reorder the step\
s (not past a st\
ep they depend o\
n), the pencil c\
hanges the setti\
ngs of the step,\
\x0d\x0a// \x22x\x22 removes\
 the step (undoa\
ble); a step tha\
t another step b\
uilds on cannot \
be removed first\
.\x0d\x0aimport QtQuic\
k\x0d\x0aimport QtQuic\
k.Controls\x0d\x0a\x0d\x0aRe\
ctangle {\x0d\x0a    i\
d: panel\x0d\x0a    re\
adonly property \
var list: column\
EditorController\
.steps\x0d\x0a    colo\
r: \x22#ffffff\x22\x0d\x0a  \
  border.color: \
\x22#c3ccd6\x22\x0d\x0a    r\
adius: 6\x0d\x0a    im\
plicitHeight: co\
l.implicitHeight\
 + 16\x0d\x0a    signa\
l editRequested(\
var step)\x0d\x0a\x0d\x0a   \
 Column {\x0d\x0a     \
   id: col\x0d\x0a    \
    x: 8; y: 8\x0d\x0a\
        width: p\
anel.width - 16\x0d\
\x0a        spacing\
: 4\x0d\x0a        Tex\
t { text: \x22Schri\
tte  (\x22 + (panel\
.list ? panel.li\
st.length : 0) +\
 \x22)\x22; font.bold:\
 true; font.pixe\
lSize: 12; color\
: \x22#34495e\x22 }\x0d\x0a \
       Text {\x0d\x0a \
           visib\
le: !panel.list \
|| panel.list.le\
ngth === 0\x0d\x0a    \
        text: \x22N\
och keine Schrit\
te. Alles, was S\
ie mit Umwandeln\
, Gruppieren ode\
r Typ \xc3\xa4ndern tu\
n, steht hier un\
d l\xc3\xa4sst sich wi\
eder entfernen.\x22\
\x0d\x0a            fo\
nt.pixelSize: 10\
; color: \x22#7b879\
4\x22; wrapMode: Te\
xt.Wrap; width: \
parent.width\x0d\x0a  \
      }\x0d\x0a       \
 Repeater {\x0d\x0a   \
         model: \
panel.list\x0d\x0a    \
        delegate\
: Rectangle {\x0d\x0a \
               w\
idth: col.width\x0d\
\x0a               \
 height: Math.ma\
x(26, label.impl\
icitHeight + 8)\x0d\
\x0a               \
 radius: 4\x0d\x0a    \
            colo\
r: rowMouse.cont\
ainsMouse ? \x22#ee\
f3f8\x22 : \x22#f7f9fb\
\x22\x0d\x0a             \
   border.color:\
 \x22#dde3ea\x22\x0d\x0a    \
            Text\
 {\x0d\x0a            \
        id: labe\
l\x0d\x0a             \
       anchors {\
 left: parent.le\
ft; right: tools\
.left; verticalC\
enter: parent.ve\
rticalCenter; le\
ftMargin: 6; rig\
htMargin: 4 }\x0d\x0a \
                \
   text: (index \
+ 1) + \x22.  \x22 + m\
odelData.text\x0d\x0a \
                \
   font.pixelSiz\
e: 10; color: \x22#\
1f2933\x22; wrapMod\
e: Text.Wrap\x0d\x0a  \
              }\x0d\
\x0a               \
 MouseArea {\x0d\x0a  \
                \
  id: rowMouse\x0d\x0a\
                \
    anchors.fill\
: parent\x0d\x0a      \
              ho\
verEnabled: true\
\x0d\x0a              \
      onClicked:\
 { var r = colum\
nEditorControlle\
r.rowOfKey(model\
Data.key); if (r\
 >= 0) columnEdi\
torController.se\
lectOnly(r) }\x0d\x0a \
                \
   ToolTip.visib\
le: containsMous\
e && !!modelData\
.why\x0d\x0a          \
          ToolTi\
p.delay: 450\x0d\x0a  \
                \
  ToolTip.text: \
modelData.why\x0d\x0a \
               }\
\x0d\x0a              \
  Row {\x0d\x0a       \
             id:\
 tools\x0d\x0a        \
            anch\
ors { right: par\
ent.right; verti\
calCenter: paren\
t.verticalCenter\
 }\x0d\x0a            \
        ToolButt\
on {\x0d\x0a          \
              wi\
dth: 22; height:\
 24; text: \x22\xe2\x96\xb2\x22\
; font.pixelSize\
: 9; enabled: mo\
delData.canUp\x0d\x0a \
                \
       Accessibl\
e.name: \x22Schritt\
 verschieben \x22 +\
 (index + 1) + \x22\
 nach oben\x22\x0d\x0a   \
                \
     ToolTip.vis\
ible: hovered; T\
oolTip.delay: 45\
0; ToolTip.text:\
 \x22Schritt nach o\
ben\x22\x0d\x0a          \
              on\
Clicked: { var e\
 = columnEditorC\
ontroller.moveSt\
ep(modelData.ind\
ex, -1); if (e !\
== \x22\x22) columnEdi\
torController.me\
ssage(e) }\x0d\x0a    \
                \
}\x0d\x0a             \
       ToolButto\
n {\x0d\x0a           \
             wid\
th: 22; height: \
24; text: \x22\xe2\x96\xbc\x22;\
 font.pixelSize:\
 9; enabled: mod\
elData.canDown\x0d\x0a\
                \
        Accessib\
le.name: \x22Schrit\
t verschieben \x22 \
+ (index + 1) + \
\x22 nach unten\x22\x0d\x0a \
                \
       ToolTip.v\
isible: hovered;\
 ToolTip.delay: \
450; ToolTip.tex\
t: \x22Schritt nach\
 unten\x22\x0d\x0a       \
                \
 onClicked: { va\
r e = columnEdit\
orController.mov\
eStep(modelData.\
index, 1); if (e\
 !== \x22\x22) columnE\
ditorController.\
message(e) }\x0d\x0a  \
                \
  }\x0d\x0a           \
         ToolBut\
ton {\x0d\x0a         \
               w\
idth: 22; height\
: 24; text: \x22\xe2\x9c\x8e\
\x22; font.pixelSiz\
e: 12; enabled: \
!!modelData.canE\
dit\x0d\x0a           \
             Acc\
essible.name: \x22S\
chritt \xc3\xa4ndern \x22\
 + (index + 1)\x0d\x0a\
                \
        ToolTip.\
visible: hovered\
; ToolTip.delay:\
 450; ToolTip.te\
xt: modelData.ca\
nEdit ? \x22Einstel\
lungen dieses Sc\
hritts \xc3\xa4ndern\x22 \
: \x22Dieser Schrit\
t l\xc3\xa4sst sich ni\
cht \xc3\xa4ndern; ent\
fernen und neu a\
nlegen\x22\x0d\x0a       \
                \
 onClicked: pane\
l.editRequested(\
modelData)\x0d\x0a    \
                \
}\x0d\x0a             \
       ToolButto\
n {\x0d\x0a           \
             id:\
 del\x0d\x0a          \
              wi\
dth: 24; height:\
 24\x0d\x0a           \
             tex\
t: \x22\xc3\x97\x22\x0d\x0a       \
                \
 enabled: modelD\
ata.canDelete\x0d\x0a \
                \
       font.pixe\
lSize: 14\x0d\x0a     \
                \
   Accessible.na\
me: \x22Schritt ent\
fernen \x22 + (inde\
x + 1)\x0d\x0a        \
                \
ToolTip.visible:\
 hovered\x0d\x0a      \
                \
  ToolTip.delay:\
 450\x0d\x0a          \
              To\
olTip.text: mode\
lData.canDelete \
? \x22Diesen Schrit\
t entfernen\x22 : m\
odelData.why\x0d\x0a  \
                \
      onClicked:\
 {\x0d\x0a            \
                \
var e = modelDat\
a.kind === \x22grou\
p\x22 ? columnEdito\
rController.remo\
veGroupStep(mode\
lData.bandIndex)\
\x0d\x0a              \
                \
                \
                \
 : columnEditorC\
ontroller.delete\
Step(modelData.i\
ndex)\x0d\x0a         \
                \
   if (e !== \x22\x22)\
 columnEditorCon\
troller.message(\
e)\x0d\x0a            \
            }\x0d\x0a \
                \
   }\x0d\x0a          \
      }\x0d\x0a       \
     }\x0d\x0a        \
}\x0d\x0a    }\x0d\x0a}\x0d\x0a\
\x00\x00*(\
/\
/ Group / Combin\
e columns. The g\
roup is a DRAFT:\
 nothing in the \
preview changes \
until \x22Anwenden\x22\
;\x0d\x0a// \x22Abbrechen\
\x22 discards it co\
mpletely. The re\
sult texts updat\
e immediately on\
 every change.\x0d\x0a\
import QtQuick\x0d\x0a\
import QtQuick.C\
ontrols\x0d\x0a\x0d\x0aRecta\
ngle {\x0d\x0a    id: \
panel\x0d\x0a    reado\
nly property var\
 d: columnEditor\
Controller.draft\
\x0d\x0a    property s\
tring error: \x22\x22\x0d\
\x0a    readonly pr\
operty real slot\
W: 78\x0d\x0a    reado\
nly property var\
 presets: [{ t: \
\x22_\x22, v: \x22_\x22 }, {\
 t: \x22-\x22, v: \x22-\x22 \
}, { t: \x22/\x22, v: \
\x22/\x22 }, { t: \x22Lee\
rzeichen\x22, v: \x22 \
\x22 }, { t: \x22Keins\
\x22, v: \x22\x22 }]\x0d\x0a\x0d\x0a \
   visible: colu\
mnEditorControll\
er.hasDraft\x0d\x0a   \
 color: \x22#f1f8f3\
\x22\x0d\x0a    border.co\
lor: \x22#4c9f5f\x22\x0d\x0a\
    radius: 6\x0d\x0a \
   implicitHeigh\
t: col.implicitH\
eight + 20\x0d\x0a\x0d\x0a  \
  function prese\
tActive(v) { ret\
urn d.separator \
=== v }\x0d\x0a    fun\
ction isCustom()\
 {\x0d\x0a        for \
(var i = 0; i < \
presets.length; \
i++) if (presets\
[i].v === d.sepa\
rator) return fa\
lse\x0d\x0a        ret\
urn true\x0d\x0a    }\x0d\
\x0a    Connections\
 {\x0d\x0a        targ\
et: columnEditor\
Controller\x0d\x0a    \
    function onD\
raftChanged() {\x0d\
\x0a            pan\
el.error = \x22\x22\x0d\x0a \
           if (!\
panel.d.active) \
return\x0d\x0a        \
    if (!targetF\
ield.activeFocus\
 && targetField.\
text !== (panel.\
d.target || \x22\x22))\
 targetField.tex\
t = panel.d.targ\
et || \x22\x22\x0d\x0a      \
      if (!custo\
mField.activeFoc\
us) customField.\
text = panel.isC\
ustom() ? panel.\
d.separator : \x22\x22\
\x0d\x0a        }\x0d\x0a   \
 }\x0d\x0a\x0d\x0a    Column\
 {\x0d\x0a        id: \
col\x0d\x0a        x: \
10; y: 10\x0d\x0a     \
   width: panel.\
width - 20\x0d\x0a    \
    spacing: 6\x0d\x0a\
\x0d\x0a        Text {\
 text: \x22Gruppier\
en / Spalten ver\
binden  (\x22 + (d.\
count || 0) + \x22)\
\x22; font.bold: tr\
ue; font.pixelSi\
ze: 13; color: \x22\
#2f7d44\x22 }\x0d\x0a    \
    Text { text:\
 \x22Reihenfolge = \
Reihenfolge der \
Werte im Ergebni\
s. K\xc3\xbcrzel ziehe\
n oder \xe2\x97\x82 \xe2\x96\xb8 b\
enutzen. Strg+Kl\
ick auf eine Kac\
hel = hinzuf\xc3\xbcge\
n / entfernen, U\
mschalt+Klick = \
Bereich hinzuf\xc3\xbc\
gen.\x22;font.pixel\
Size: 10; color:\
 \x22#52606d\x22; wrap\
Mode: Text.Wrap;\
 width: parent.w\
idth }\x0d\x0a\x0d\x0a      \
  Flickable {   \
                \
               /\
/ reorderable ro\
w of the grouped\
 tiles\x0d\x0a        \
    id: strip\x0d\x0a \
           width\
: parent.width\x0d\x0a\
            heig\
ht: 46\x0d\x0a        \
    contentWidth\
: Math.max(width\
, (d.count || 0)\
 * panel.slotW)\x0d\
\x0a            cli\
p: true\x0d\x0a       \
     boundsBehav\
ior: Flickable.S\
topAtBounds\x0d\x0a   \
         Repeate\
r {\x0d\x0a           \
     model: d.la\
bels || []\x0d\x0a    \
            dele\
gate: Rectangle \
{\x0d\x0a             \
       id: chip\x0d\
\x0a               \
     width: pane\
l.slotW - 6\x0d\x0a   \
                \
 height: 40\x0d\x0a   \
                \
 y: 2\x0d\x0a         \
           radiu\
s: 5\x0d\x0a          \
          color:\
 \x22#ffffff\x22\x0d\x0a    \
                \
border.color: \x22#\
4c9f5f\x22\x0d\x0a       \
             bor\
der.width: 1.5\x0d\x0a\
                \
    property rea\
l home: index * \
panel.slotW\x0d\x0a   \
                \
 x: home\x0d\x0a      \
              z:\
 ma.drag.active \
? 5 : 0\x0d\x0a       \
             Rec\
tangle {\x0d\x0a      \
                \
  x: 3; y: 3; wi\
dth: 16; height:\
 16; radius: 8; \
color: \x22#1f5fa8\x22\
\x0d\x0a              \
          Text {\
 anchors.centerI\
n: parent; text:\
 index + 1; font\
.pixelSize: 10; \
font.bold: true;\
 color: \x22#ffffff\
\x22 }\x0d\x0a           \
         }\x0d\x0a    \
                \
Text {\x0d\x0a        \
                \
x: 3; anchors.bo\
ttom: parent.bot\
tom; anchors.bot\
tomMargin: 3\x0d\x0a  \
                \
      width: par\
ent.width - 6\x0d\x0a \
                \
       text: mod\
elData; elide: T\
ext.ElideRight; \
font.pixelSize: \
11\x0d\x0a            \
        }\x0d\x0a     \
               T\
ext {\x0d\x0a         \
               a\
nchors.right: pa\
rent.right; anch\
ors.rightMargin:\
 3; y: 1\x0d\x0a      \
                \
  text: \x22\xc3\x97\x22; fo\
nt.pixelSize: 14\
; color: \x22#9a3b3\
b\x22\x0d\x0a            \
            Mous\
eArea { anchors.\
fill: parent; an\
chors.margins: -\
4; onClicked: co\
lumnEditorContro\
ller.removeDraft\
Item(index) }\x0d\x0a \
                \
   }\x0d\x0a          \
          Text {\
\x0d\x0a              \
          x: 22;\
 y: 4; text: \x22\xe2\x97\
\x82\x22; font.pixelSi\
ze: 11; color: \x22\
#52606d\x22; visibl\
e: index > 0\x0d\x0a  \
                \
      MouseArea \
{ anchors.fill: \
parent; anchors.\
margins: -4; onC\
licked: columnEd\
itorController.m\
oveDraftItem(ind\
ex, index - 1) }\
\x0d\x0a              \
      }\x0d\x0a       \
             Tex\
t {\x0d\x0a           \
             x: \
34; y: 4; text: \
\x22\xe2\x96\xb8\x22; font.pixe\
lSize: 11; color\
: \x22#52606d\x22; vis\
ible: index < (d\
.count || 0) - 1\
\x0d\x0a              \
          MouseA\
rea { anchors.fi\
ll: parent; anch\
ors.margins: -4;\
 onClicked: colu\
mnEditorControll\
er.moveDraftItem\
(index, index + \
1) }\x0d\x0a          \
          }\x0d\x0a   \
                \
 MouseArea {\x0d\x0a  \
                \
      id: ma\x0d\x0a  \
                \
      anchors.fi\
ll: parent\x0d\x0a    \
                \
    z: -1\x0d\x0a     \
                \
   drag.target: \
chip\x0d\x0a          \
              dr\
ag.axis: Drag.XA\
xis\x0d\x0a           \
             onR\
eleased: {\x0d\x0a    \
                \
        var to =\
 Math.max(0, Mat\
h.min((d.count |\
| 1) - 1, Math.r\
ound(chip.x / pa\
nel.slotW)))\x0d\x0a  \
                \
          chip.x\
 = Qt.binding(fu\
nction () { retu\
rn chip.home })\x0d\
\x0a               \
             if \
(to !== index) c\
olumnEditorContr\
oller.moveDraftI\
tem(index, to)\x0d\x0a\
                \
        }\x0d\x0a     \
               }\
\x0d\x0a              \
  }\x0d\x0a           \
 }\x0d\x0a        }\x0d\x0a\x0d\
\x0a        Text { \
text: \x22Trennzeic\
hen\x22; font.pixel\
Size: 11; font.b\
old: true }\x0d\x0a   \
     Row {\x0d\x0a    \
        spacing:\
 4\x0d\x0a            \
Repeater {\x0d\x0a    \
            mode\
l: panel.presets\
\x0d\x0a              \
  delegate: Butt\
on {\x0d\x0a          \
          text: \
modelData.t\x0d\x0a   \
                \
 checkable: true\
\x0d\x0a              \
      checked: p\
anel.presetActiv\
e(modelData.v)\x0d\x0a\
                \
    implicitHeig\
ht: 26\x0d\x0a        \
            impl\
icitWidth: model\
Data.t.length > \
2 ? 52 : 32\x0d\x0a   \
                \
 font.pixelSize:\
 11\x0d\x0a           \
         Accessi\
ble.name: \x22Trenn\
zeichen \x22 + mode\
lData.t\x0d\x0a       \
             onC\
licked: columnEd\
itorController.s\
etSeparator(mode\
lData.v)\x0d\x0a      \
          }\x0d\x0a   \
         }\x0d\x0a    \
    }\x0d\x0a        R\
ow {\x0d\x0a          \
  spacing: 6\x0d\x0a  \
          Text {\
 text: \x22Eigenes\x22\
; font.pixelSize\
: 11; anchors.ve\
rticalCenter: pa\
rent.verticalCen\
ter }\x0d\x0a         \
   TextField {\x0d\x0a\
                \
id: customField\x0d\
\x0a               \
 width: 90\x0d\x0a    \
            maxi\
mumLength: 16\x0d\x0a \
               p\
laceholderText: \
\x22beliebiger Text\
\x22\x0d\x0a             \
   selectByMouse\
: true\x0d\x0a        \
        font.pix\
elSize: 11\x0d\x0a    \
            Acce\
ssible.name: \x22Ei\
genes Trennzeich\
en\x22\x0d\x0a           \
     onTextEdite\
d: if (text !== \
\x22\x22) columnEditor\
Controller.setSe\
parator(text)\x0d\x0a \
           }\x0d\x0a  \
      }\x0d\x0a       \
 CheckBox { text\
: \x22Leerzeichen k\
\xc3\xbcrzen\x22; checked\
: d.trim === tru\
e; font.pixelSiz\
e: 11; onToggled\
: columnEditorCo\
ntroller.setTrim\
(checked) }\x0d\x0a   \
     CheckBox { \
text: \x22Leere Wer\
te \xc3\xbcberspringen\
\x22; checked: d.sk\
ipEmpty === true\
; font.pixelSize\
: 11; onToggled:\
 columnEditorCon\
troller.setSkipE\
mpty(checked) }\x0d\
\x0a        CheckBo\
x { text: \x22Origi\
nalspalten behal\
ten\x22; checked: d\
.keep === true; \
font.pixelSize: \
11; onToggled: c\
olumnEditorContr\
oller.setKeepOri\
ginals(checked) \
}\x0d\x0a        Check\
Box { text: \x22Ori\
ginale exportier\
en\x22; checked: d.\
include === true\
; font.pixelSize\
: 11; onToggled:\
 columnEditorCon\
troller.setInclu\
deOriginals(chec\
ked) }\x0d\x0a        \
CheckBox { text:\
 \x22Verbundene Spa\
lte anlegen (Wer\
te der Kacheln v\
erbunden)\x22; chec\
ked: d.combine =\
== true; font.pi\
xelSize: 11\x0d\x0a   \
                \
ToolTip.visible:\
 hovered; ToolTi\
p.text: \x22Aus: nu\
r Gruppe \xe2\x80\x93 die\
 Kacheln bewegen\
 sich im Kachel-\
Editor gemeinsam\
 als Block.\x22\x0d\x0a  \
                \
 onToggled: colu\
mnEditorControll\
er.setCombine(ch\
ecked) }\x0d\x0a      \
  CheckBox { tex\
t: \x22Gruppenname \
als Kopfzeile in\
 Tabelle und Exc\
el-Export\x22; chec\
ked: d.band === \
true; font.pixel\
Size: 11\x0d\x0a      \
             Too\
lTip.visible: ho\
vered; ToolTip.t\
ext: \x22An: der Gr\
uppenname steht \
als gemeinsame K\
opfzeile \xc3\xbcber d\
en gruppierten S\
palten (Tabelle \
und Excel). Aus:\
 die Gruppe gibt\
 es nur im Kache\
l-Editor.\x22\x0d\x0a    \
               o\
nToggled: column\
EditorController\
.setBand(checked\
) }\x0d\x0a\x0d\x0a        T\
ext { text: \x22Gru\
ppenname / Name \
der verbundenen \
Spalte\x22; font.pi\
xelSize: 11; fon\
t.bold: true }\x0d\x0a\
        TextFiel\
d {\x0d\x0a           \
 id: targetField\
\x0d\x0a            wi\
dth: parent.widt\
h\x0d\x0a            s\
electByMouse: tr\
ue\x0d\x0a            \
font.pixelSize: \
11\x0d\x0a            \
Accessible.name:\
 \x22Name der Ziels\
palte\x22\x0d\x0a        \
    onTextEdited\
: columnEditorCo\
ntroller.setTarg\
etName(text)\x0d\x0a  \
      }\x0d\x0a       \
 Row {\x0d\x0a        \
    spacing: 6\x0d\x0a\
            Text\
 { text: \x22Ausgab\
etyp\x22; font.pixe\
lSize: 11; ancho\
rs.verticalCente\
r: parent.vertic\
alCenter }\x0d\x0a    \
        ComboBox\
 {\x0d\x0a            \
    id: outCombo\
\x0d\x0a              \
  model: [{ t: \x22\
Text\x22, v: \x22text\x22\
 }, { t: \x22Ganzza\
hl\x22, v: \x22integer\
\x22 }, { t: \x22Dezim\
alzahl\x22, v: \x22dec\
imal\x22 },\x0d\x0a      \
                \
  { t: \x22Prozent\x22\
, v: \x22percentage\
\x22 }, { t: \x22Wahr/\
Falsch\x22, v: \x22boo\
lean\x22 }, { t: \x22Z\
eit\x22, v: \x22time\x22 \
}, { t: \x22Dauer\x22,\
 v: \x22duration\x22 }\
]\x0d\x0a             \
   textRole: \x22t\x22\
; valueRole: \x22v\x22\
\x0d\x0a              \
  implicitWidth:\
 140\x0d\x0a          \
      font.pixel\
Size: 11\x0d\x0a      \
          curren\
tIndex: Math.max\
(0, indexOfValue\
(d.outputType))\x0d\
\x0a               \
 Accessible.name\
: \x22Ausgabetyp de\
r Gruppe\x22\x0d\x0a     \
           onAct\
ivated: columnEd\
itorController.s\
etGroupOutputTyp\
e(currentValue)\x0d\
\x0a            }\x0d\x0a\
        }\x0d\x0a     \
   Row {\x0d\x0a      \
      spacing: 6\
\x0d\x0a            Te\
xt { text: \x22Ung\xc3\
\xbcltige Werte\x22; f\
ont.pixelSize: 1\
1; anchors.verti\
calCenter: paren\
t.verticalCenter\
 }\x0d\x0a            \
ComboBox {\x0d\x0a    \
            mode\
l: [{ t: \x22Leeren\
 und markieren\x22,\
 v: \x22empty_flag\x22\
 }, { t: \x22Origin\
al behalten und \
markieren\x22, v: \x22\
flag\x22 },\x0d\x0a      \
                \
  { t: \x22Leeren\x22,\
 v: \x22empty\x22 }, {\
 t: \x22Vorgang abb\
rechen\x22, v: \x22abo\
rt\x22 }]\x0d\x0a        \
        textRole\
: \x22t\x22; valueRole\
: \x22v\x22\x0d\x0a         \
       implicitW\
idth: 150\x0d\x0a     \
           font.\
pixelSize: 11\x0d\x0a \
               c\
urrentIndex: Mat\
h.max(0, indexOf\
Value(d.invalid)\
)\x0d\x0a             \
   Accessible.na\
me: \x22Ung\xc3\xbcltige \
Werte der Gruppe\
\x22\x0d\x0a             \
   onActivated: \
columnEditorCont\
roller.setGroupI\
nvalid(currentVa\
lue)\x0d\x0a          \
  }\x0d\x0a        }\x0d\x0a\
\x0d\x0a        Rectan\
gle { width: par\
ent.width; heigh\
t: 1; color: \x22#b\
9d8c1\x22 }\x0d\x0a      \
  Text { text: \x22\
Zielspalte: \x22 + \
(d.target || \x22\x22)\
; font.pixelSize\
: 11; wrapMode: \
Text.Wrap; width\
: parent.width }\
\x0d\x0a        Text {\
 text: \x22Ergebnis\
-Datentyp: \x22 + (\
d.outputTypeName\
 || \x22\x22); font.pi\
xelSize: 11 }\x0d\x0a \
       Text { te\
xt: \x22Ergebnis: \x22\
 + (d.resultName\
s || \x22\x22); font.p\
ixelSize: 12; fo\
nt.bold: true; w\
rapMode: Text.Wr\
apAnywhere; widt\
h: parent.width \
}\x0d\x0a        Text \
{\x0d\x0a            t\
ext: \x22Beispiel: \
\x22 + (d.example |\
| \x22\x22)\x0d\x0a         \
   font.pixelSiz\
e: 12; font.bold\
: true; color: d\
.exampleValid ==\
= false ? \x22#b03a\
2e\x22 : \x22#2f7d44\x22\x0d\
\x0a            wra\
pMode: Text.Wrap\
Anywhere; width:\
 parent.width\x0d\x0a \
       }\x0d\x0a      \
  Text { visible\
: panel.error !=\
= \x22\x22; text: pane\
l.error; color: \
\x22#b03a2e\x22; font.\
pixelSize: 11; w\
rapMode: Text.Wr\
ap; width: paren\
t.width }\x0d\x0a     \
   Row {\x0d\x0a      \
      spacing: 8\
\x0d\x0a            Bu\
tton {\x0d\x0a        \
        text: \x22A\
nwenden\x22\x0d\x0a      \
          enable\
d: d.canApply ==\
= true\x0d\x0a        \
        Accessib\
le.name: \x22Anwend\
en\x22\x0d\x0a           \
     onClicked: \
panel.error = co\
lumnEditorContro\
ller.applyGroup(\
)\x0d\x0a            }\
\x0d\x0a            Bu\
tton { text: \x22Ab\
brechen\x22; Access\
ible.name: \x22Grup\
pe abbrechen\x22; o\
nClicked: column\
EditorController\
.cancelGroup() }\
\x0d\x0a        }\x0d\x0a   \
 }\x0d\x0a}\x0d\x0a\
\x00\x00\x0fo\
/\
/ Status strip o\
f the tile edito\
r. It sits in th\
e ribbon at the \
height of the ic\
on row (owner 20\
26-11-16): bulk \
button \x22Alle in \
Tabelle ausblend\
en\x22,\x0d\x0a// and the\
 colour legend (\
the three area b\
uttons are Qt ri\
bbon buttons rig\
ht of it). The o\
pen / folded sta\
te of the areas \
lives in `tileLa\
yout`\x0d\x0a// (share\
d with ColumnGri\
d.qml); the coun\
ts come from `co\
lumnConfigModel`\
, the bulk actio\
n from `columnEd\
itorController`.\
\x0d\x0aimport QtQuick\
\x0d\x0aimport QtQuick\
.Controls\x0d\x0a\x0d\x0aIte\
m {\x0d\x0a    id: roo\
t\x0d\x0a    implicitH\
eight: 34\x0d\x0a    i\
mplicitWidth: st\
rip.implicitWidt\
h + 8\x0d\x0a    reado\
nly property var\
 openAreas: tile\
Layout.openAreas\
\x0d\x0a    function i\
sOpen(i) { retur\
n openAreas.inde\
xOf(i) >= 0 }\x0d\x0a\x0d\
\x0a    Row {\x0d\x0a    \
    id: strip\x0d\x0a \
       anchors {\
 right: parent.r\
ight; rightMargi\
n: 4; verticalCe\
nter: parent.ver\
ticalCenter }\x0d\x0a \
       spacing: \
16\x0d\x0a\x0d\x0a        Re\
ctangle {       \
                \
                \
      // neutral\
 bulk button: hi\
de / show the no\
t-exported colum\
ns in the table\x0d\
\x0a            id:\
 bulkTop\x0d\x0a      \
      visible: r\
oot.isOpen(1) &&\
 columnConfigMod\
el.notExportedCo\
unt > 0\x0d\x0a       \
     width: bulk\
TopText.implicit\
Width + 14; heig\
ht: 18; radius: \
3\x0d\x0a            a\
nchors.verticalC\
enter: parent.ve\
rticalCenter\x0d\x0a  \
          color:\
 bulkTopArea.con\
tainsMouse ? \x22#e\
5e7eb\x22 : \x22transp\
arent\x22\x0d\x0a        \
    border.width\
: 1\x0d\x0a           \
 border.color: \x22\
#9aa5b1\x22\x0d\x0a      \
      Text { id:\
 bulkTopText; an\
chors.centerIn: \
parent; font.pix\
elSize: 10; colo\
r: \x22#52606d\x22\x0d\x0a  \
                \
 text: columnCon\
figModel.tableHi\
ddenCount >= col\
umnConfigModel.n\
otExportedCount \
? \x22Alle in Tabel\
le einblenden\x22 :\
 \x22Alle in Tabell\
e ausblenden\x22 }\x0d\
\x0a            Mou\
seArea { id: bul\
kTopArea; anchor\
s.fill: parent; \
hoverEnabled: tr\
ue; cursorShape:\
 Qt.PointingHand\
Cursor\x0d\x0a        \
                \
onClicked: colum\
nEditorControlle\
r.setAreaHidden(\
1) }\x0d\x0a          \
  ToolTip.visibl\
e: bulkTopArea.c\
ontainsMouse\x0d\x0a  \
          ToolTi\
p.text: columnCo\
nfigModel.tableH\
iddenCount >= co\
lumnConfigModel.\
notExportedCount\
\x0d\x0a              \
            ? \x22N\
icht exportierte\
 Spalten in der \
Tabelle unten wi\
eder zeigen (ein\
 R\xc3\xbcckg\xc3\xa4ngig-Sc\
hritt)\x22\x0d\x0a       \
                \
   : \x22Alle nicht\
 exportierten Sp\
alten nur in der\
 Tabelle unten a\
usblenden; die K\
acheln bleiben i\
n \xe2\x80\x9eNicht expor\
tiert\xe2\x80\x9c, Bereic\
h \xe2\x80\x9eAusgeblende\
t\xe2\x80\x9c und Export \
bleiben unver\xc3\xa4n\
dert (ein R\xc3\xbcckg\
\xc3\xa4ngig-Schritt)\x22\
\x0d\x0a        }\x0d\x0a   \
     Row {      \
                \
                \
             // \
colour legend; c\
ollapses togethe\
r with the right\
-hand column (an\
d when the ribbo\
n is narrow)\x0d\x0a  \
          id: le\
gend\x0d\x0a          \
  visible: root.\
openAreas.length\
 > 0 && root.wid\
th > 820\x0d\x0a      \
      anchors.ve\
rticalCenter: pa\
rent.verticalCen\
ter\x0d\x0a           \
 spacing: 12\x0d\x0a  \
          Repeat\
er {\x0d\x0a          \
      model: [{ \
t: \x22aktiv / gew\xc3\
\xa4hlt\x22, c: \x22#2e9e\
4f\x22, f: \x22#eef8f1\
\x22 }, { t: \x22hidde\
n\x22, c: \x22#7b8794\x22\
, f: \x22#e5e7eb\x22 }\
,\x0d\x0a             \
           { t: \
\x22nicht exportier\
t\x22, c: \x22#f08c00\x22\
, f: \x22#fff3e0\x22 }\
, { t: \x22calculat\
ed\x22, c: \x22#4c9f5f\
\x22, f: \x22#dff3e3\x22 \
},\x0d\x0a            \
            { t:\
 \x22umbenannt (rot\
e Marke)\x22, c: \x22#\
d32f2f\x22, f: \x22#ff\
ffff\x22 }]\x0d\x0a      \
          delega\
te: Row {\x0d\x0a     \
               s\
pacing: 4\x0d\x0a     \
               R\
ectangle { width\
: 14; height: 10\
; radius: 2; col\
or: modelData.f;\
 border.color: m\
odelData.c; bord\
er.width: 1.5; a\
nchors.verticalC\
enter: parent.ve\
rticalCenter }\x0d\x0a\
                \
    Text { text:\
 modelData.t; fo\
nt.pixelSize: 10\
; color: \x22#52606\
d\x22; anchors.vert\
icalCenter: pare\
nt.verticalCente\
r }\x0d\x0a           \
     }\x0d\x0a        \
    }\x0d\x0a         \
   Row {\x0d\x0a      \
          spacin\
g: 4\x0d\x0a          \
      Rectangle \
{ width: 3; heig\
ht: 12; radius: \
1.5; color: \x22#4f\
81bd\x22; anchors.v\
erticalCenter: p\
arent.verticalCe\
nter }\x0d\x0a        \
        Text { t\
ext: \x22Farbstreif\
en = Tag-Typ (Pr\
ojektdefinitione\
n)\x22; font.pixelS\
ize: 10; color: \
\x22#52606d\x22; ancho\
rs.verticalCente\
r: parent.vertic\
alCenter }\x0d\x0a    \
        }\x0d\x0a     \
   }\x0d\x0a    }     \
                \
                \
                \
      // the thr\
ee area buttons \
are standard rib\
bon buttons now \
(Ribbon.add_area\
_buttons)\x0d\x0a}\x0d\x0a\
\x00\x00\x02H\
/\
/ Function stack\
 (Sprint 2): dro\
pping a tile ONT\
O another tile w\
ill start a stac\
k here. Sprint 1\
 only shows the \
hint;\x0d\x0a// moving\
 (drop between t\
iles) is handled\
 by ColumnGrid.\x0d\
\x0aimport QtQuick\x0d\
\x0a\x0d\x0aRectangle {\x0d\x0a\
    id: stack\x0d\x0a \
   property bool\
 dropTarget: fal\
se\x0d\x0a    color: d\
ropTarget ? \x22#ea\
f3ff\x22 : \x22#f7f9fb\
\x22\x0d\x0a    border.co\
lor: \x22#c3ccd6\x22\x0d\x0a\
    radius: 6\x0d\x0a \
   implicitHeigh\
t: 34\x0d\x0a    Text \
{\x0d\x0a        ancho\
rs.centerIn: par\
ent\x0d\x0a        tex\
t: \x22Funktionssta\
pel: im n\xc3\xa4chste\
n Schritt verf\xc3\xbc\
gbar (Kachel auf\
 eine andere zie\
hen)\x22\x0d\x0a        f\
ont.pixelSize: 1\
1\x0d\x0a        color\
: \x22#7b8794\x22\x0d\x0a   \
 }\x0d\x0a}\x0d\x0a\
\x00\x00\x06\xdc\
/\
/ Side pane of t\
he tile editor a\
s its own view: \
\x22Aktive Kachel\x22 \
(inspector), the\
 group dialog an\
d the Steps / hi\
story panel.\x0d\x0a//\
 It is shown in \
the host's flow \
deck (docked rig\
ht, full height,\
 floatable) - sa\
me controller / \
model / layout a\
s ColumnGrid.qml\
.\x0d\x0a// Dialogs th\
at belong to a t\
ile (change type\
, edit a step) o\
pen next to the \
tile in the grid\
: the pane only \
asks the control\
ler.\x0d\x0aimport QtQ\
uick\x0d\x0aimport QtQ\
uick.Controls\x0d\x0a\x0d\
\x0aRectangle {\x0d\x0a  \
  id: pane\x0d\x0a    \
color: \x22#f7f9fb\x22\
\x0d\x0a\x0d\x0a    Flickabl\
e {\x0d\x0a        id:\
 side\x0d\x0a        a\
nchors { fill: p\
arent; margins: \
8 }\x0d\x0a        con\
tentWidth: width\
\x0d\x0a        conten\
tHeight: sideCol\
.implicitHeight\x0d\
\x0a        clip: t\
rue\x0d\x0a        bou\
ndsBehavior: Fli\
ckable.StopAtBou\
nds\x0d\x0a        Scr\
ollBar.vertical:\
 ScrollBar { }\x0d\x0a\
        Column {\
\x0d\x0a            id\
: sideCol\x0d\x0a     \
       width: si\
de.width - 10\x0d\x0a \
           spaci\
ng: 8\x0d\x0a         \
   RuleInspector\
 {\x0d\x0a            \
    width: paren\
t.width\x0d\x0a       \
         row: co\
lumnEditorContro\
ller.selectedRow\
\x0d\x0a              \
  onChangeTypeRe\
quested: functio\
n (r) { columnEd\
itorController.r\
equestChangeType\
(r) }\x0d\x0a         \
   }\x0d\x0a          \
  Text {\x0d\x0a      \
          visibl\
e: columnEditorC\
ontroller.select\
ionCount >= 2 &&\
 !columnEditorCo\
ntroller.hasDraf\
t\x0d\x0a             \
   text: columnE\
ditorController.\
selectionCount +\
 \x22 Kacheln gew\xc3\xa4\
hlt. Kacheln gru\
ppieren (Strg+G)\
 \xc3\xb6ffnet hier de\
n Gruppen-Dialog\
: Gruppenname, o\
ptional verbunde\
ne Spalte, optio\
nal Kopfzeile in\
 Tabelle / Excel\
.\x22\x0d\x0a            \
    font.pixelSi\
ze: 11; color: \x22\
#52606d\x22; wrapMo\
de: Text.Wrap; w\
idth: parent.wid\
th\x0d\x0a            \
}\x0d\x0a            G\
roupPanel { widt\
h: parent.width \
}\x0d\x0a            S\
tepsPanel { widt\
h: parent.width;\
 onEditRequested\
: function (step\
) { columnEditor\
Controller.reque\
stEditStep(step)\
 } }\x0d\x0a        }\x0d\
\x0a    }\x0d\x0a}\x0d\x0a\
\x00\x00.\xd5\
/\
/ Transform dial\
og (Replace valu\
es / Add text / \
Normalise pipe s\
ize) as a small \
popover below th\
e tile it belong\
s to.\x0d\x0a// It alw\
ays shows Before\
 -> After for th\
e first changing\
 cells and the n\
umber of changed\
 cells before an\
ything happens.\x0d\
\x0a// \x22Anwenden\x22 c\
reates a calcula\
ted column (gree\
n tile) and one \
step in the Step\
s panel; the sou\
rce is never cha\
nged.\x0d\x0aimport Qt\
Quick\x0d\x0aimport Qt\
Quick.Controls\x0d\x0a\
\x0d\x0aPopup {\x0d\x0a    i\
d: dlg\x0d\x0a    prop\
erty int row: -1\
\x0d\x0a    property s\
tring op: \x22repla\
ce\x22\x0d\x0a    propert\
y int count: 1\x0d\x0a\
    property var\
 preview: ({ row\
s: [], error: \x22\x22\
, changed: 0, to\
tal: 0, unrecogn\
ised: 0 })\x0d\x0a    \
property string \
applyError: \x22\x22\x0d\x0a\
    property int\
 editIndex: -1  \
                \
                \
// >= 0: change \
the settings of \
this step instea\
d of creating a \
new one\x0d\x0a    rea\
donly property b\
ool usesFind: op\
 === \x22replace\x22 |\
| op === \x22extrac\
t_before\x22 || op \
=== \x22extract_aft\
er\x22 || op === \x22e\
xtract_between\x22 \
|| op === \x22split\
_part\x22\x0d\x0a    read\
only property va\
r titles: ({ rep\
lace: \x22Werte ers\
etzen\x22, format: \
\x22Text erg\xc3\xa4nzen \
/ mit Nullen auf\
f\xc3\xbcllen\x22, normal\
ise_size: \x22Rohrg\
r\xc3\xb6\xc3\x9fe vereinhei\
tlichen\x22,\x0d\x0a     \
   extract_first\
: \x22Erste Zeichen\
\x22, extract_last:\
 \x22Letzte Zeichen\
\x22, extract_befor\
e: \x22Text vor ein\
em Trennzeichen\x22\
,\x0d\x0a        extra\
ct_after: \x22Text \
nach einem Trenn\
zeichen\x22, extrac\
t_between: \x22Text\
 zwischen zwei T\
rennzeichen\x22,\x0d\x0a \
       split_par\
t: \x22Teil\x22, split\
_fixed: \x22An fest\
en Positionen te\
ilen\x22, fill_valu\
e: \x22Leere Zellen\
 mit einem Wert \
f\xc3\xbcllen\x22 })\x0d\x0a\x0d\x0a \
   modal: false\x0d\
\x0a    dim: false\x0d\
\x0a    focus: true\
\x0d\x0a    closePolic\
y: Popup.CloseOn\
Escape | Popup.C\
loseOnPressOutsi\
de\x0d\x0a    parent: \
Overlay.overlay\x0d\
\x0a    x: 0\x0d\x0a    y\
: parent ? paren\
t.height - 2 : 0\
\x0d\x0a    margins: 6\
\x0d\x0a    padding: 8\
\x0d\x0a    width: Mat\
h.min(340, (Over\
lay.overlay ? Ov\
erlay.overlay.wi\
dth : 340) - 12)\
\x0d\x0a    background\
: Rectangle { co\
lor: \x22#ffffff\x22; \
border.color: \x22#\
7f9bb5\x22; border.\
width: 1; radius\
: 5 }\x0d\x0a\x0d\x0a    fun\
ction options() \
{\x0d\x0a        retur\
n { find: findFi\
eld.text, replac\
eWith: withField\
.text, wholeCell\
: wholeCheck.che\
cked, matchCase:\
 caseCheck.check\
ed,\x0d\x0a           \
      prefix: pr\
eField.text, suf\
fix: sufField.te\
xt, padWidth: pa\
rseInt(padField.\
text) || 0,\x0d\x0a   \
              nu\
mber: parseInt(n\
umField.text) ||\
 0, find2: find2\
Field.text, star\
t: parseInt(star\
tField.text) || \
0,\x0d\x0a            \
     bareNumbers\
: bareCombo.curr\
entValue, replac\
eOriginal: origC\
heck.checked }\x0d\x0a\
    }\x0d\x0a    funct\
ion refresh() { \
if (row >= 0) pr\
eview = columnEd\
itorController.p\
reviewTextOp(row\
, op, options())\
 }\x0d\x0a    function\
 openFor(r, oper\
ation, stepIndex\
) {\x0d\x0a        row\
 = r\x0d\x0a        op\
 = operation\x0d\x0a  \
      editIndex \
= stepIndex === \
undefined ? -1 :\
 stepIndex\x0d\x0a    \
    count = edit\
Index >= 0 ? 1 :\
 columnEditorCon\
troller.menuInfo\
(r).count\x0d\x0a     \
   applyError = \
\x22\x22\x0d\x0a        find\
Field.text = \x22\x22;\
 withField.text \
= \x22\x22; preField.t\
ext = \x22\x22; sufFie\
ld.text = \x22\x22; pa\
dField.text = \x22\x22\
; numField.text \
= \x22\x22; find2Field\
.text = \x22\x22; star\
tField.text = \x22\x22\
\x0d\x0a        wholeC\
heck.checked = f\
alse; caseCheck.\
checked = false;\
 bareCombo.curre\
ntIndex = 0; ori\
gCheck.checked =\
 true\x0d\x0a        i\
f (editIndex >= \
0) {            \
                \
       // start \
with the setting\
s the step has n\
ow\x0d\x0a            \
var o = columnEd\
itorController.s\
tepInfo(editInde\
x).options || {}\
\x0d\x0a            fi\
ndField.text = o\
.find || \x22\x22; wit\
hField.text = o.\
replaceWith || \x22\
\x22; preField.text\
 = o.prefix || \x22\
\x22; sufField.text\
 = o.suffix || \x22\
\x22\x0d\x0a            p\
adField.text = o\
.padWidth ? Stri\
ng(o.padWidth) :\
 \x22\x22; numField.te\
xt = o.number ? \
String(o.number)\
 : \x22\x22; find2Fiel\
d.text = o.find2\
 || \x22\x22; startFie\
ld.text = o.star\
t ? String(o.sta\
rt) : \x22\x22\x0d\x0a      \
      wholeCheck\
.checked = !!o.w\
holeCell; caseCh\
eck.checked = !!\
o.matchCase; bar\
eCombo.currentIn\
dex = o.bareNumb\
ers === \x22dn\x22 ? 1\
 : 0\x0d\x0a        }\x0d\
\x0a        refresh\
()\x0d\x0a        open\
()\x0d\x0a    }\x0d\x0a    o\
nOpened: (usesFi\
nd ? findField :\
 (op === \x22fill_v\
alue\x22 ? withFiel\
d : (op === \x22for\
mat\x22 ? preField \
: (op === \x22norma\
lise_size\x22 ? bar\
eCombo : numFiel\
d)))).forceActiv\
eFocus()\x0d\x0a\x0d\x0a    \
contentItem: Fli\
ckable {\x0d\x0a      \
  clip: true\x0d\x0a  \
      implicitHe\
ight: Math.min(b\
ody.implicitHeig\
ht, 430)\x0d\x0a      \
  contentHeight:\
 body.implicitHe\
ight\x0d\x0a        bo\
undsBehavior: Fl\
ickable.StopAtBo\
unds\x0d\x0a        Co\
lumn {\x0d\x0a        \
    id: body\x0d\x0a  \
          width:\
 parent.width\x0d\x0a \
           spaci\
ng: 5\x0d\x0a         \
   Text {\x0d\x0a     \
           text:\
 (dlg.editIndex \
>= 0 ? \x22Schritt \
\xc3\xa4ndern: \x22 : \x22\x22)\
 + (dlg.titles[d\
lg.op] || dlg.op\
) + (dlg.count >\
 1 ? \x22  (\x22 + dlg\
.count + \x22 Spalt\
en)\x22 : \x22\x22)\x0d\x0a    \
            font\
.bold: true; fon\
t.pixelSize: 12;\
 elide: Text.Eli\
deRight; width: \
parent.width\x0d\x0a  \
          }\x0d\x0a   \
         Text {\x0d\
\x0a               \
 text: dlg.count\
 > 1 ? \x22Gilt f\xc3\xbc\
r alle gew\xc3\xa4hlte\
n Kacheln. Vorsc\
hau: \x22 + (previe\
w.label || \x22\x22) :\
 \x22Spalte: \x22 + (p\
review.label || \
\x22\x22)\x0d\x0a           \
     font.pixelS\
ize: 10; color: \
\x22#52606d\x22; elide\
: Text.ElideRigh\
t; width: parent\
.width\x0d\x0a        \
    }\x0d\x0a         \
   Row {\x0d\x0a      \
          visibl\
e: dlg.usesFind;\
 spacing: 6\x0d\x0a   \
             Tex\
t { text: dlg.op\
 === \x22replace\x22 ?\
 \x22Suchen nach\x22 :\
 \x22Trennzeichen\x22;\
 font.pixelSize:\
 11; anchors.ver\
ticalCenter: par\
ent.verticalCent\
er; width: 78 }\x0d\
\x0a               \
 TextField { id:\
 findField; widt\
h: 220; implicit\
Height: 26; font\
.pixelSize: 11; \
selectByMouse: t\
rue; Accessible.\
name: \x22Gesuchter\
 Text\x22; onTextEd\
ited: dlg.refres\
h() }\x0d\x0a         \
   }\x0d\x0a          \
  Row {\x0d\x0a       \
         visible\
: dlg.op === \x22re\
place\x22 || dlg.op\
 === \x22fill_value\
\x22; spacing: 6\x0d\x0a \
               T\
ext { text: dlg.\
op === \x22fill_val\
ue\x22 ? \x22F\xc3\xbcllen m\
it\x22 : \x22Ersetzen \
durch\x22; font.pix\
elSize: 11; anch\
ors.verticalCent\
er: parent.verti\
calCenter; width\
: 78 }\x0d\x0a        \
        TextFiel\
d { id: withFiel\
d; width: 220; i\
mplicitHeight: 2\
6; font.pixelSiz\
e: 11; selectByM\
ouse: true; plac\
eholderText: dlg\
.op === \x22fill_va\
lue\x22 ? \x22Wert f\xc3\xbc\
r jede leere Zel\
le\x22 : \x22(leer = e\
ntfernen)\x22; Acce\
ssible.name: dlg\
.op === \x22fill_va\
lue\x22 ? \x22F\xc3\xbcllen \
mit\x22 : \x22Ersetzen\
 durch\x22; onTextE\
dited: dlg.refre\
sh() }\x0d\x0a        \
    }\x0d\x0a         \
   Row {\x0d\x0a      \
          visibl\
e: dlg.op === \x22e\
xtract_between\x22;\
 spacing: 6\x0d\x0a   \
             Tex\
t { text: \x22Bis\x22;\
 font.pixelSize:\
 11; anchors.ver\
ticalCenter: par\
ent.verticalCent\
er; width: 78 }\x0d\
\x0a               \
 TextField { id:\
 find2Field; wid\
th: 220; implici\
tHeight: 26; fon\
t.pixelSize: 11;\
 selectByMouse: \
true; placeholde\
rText: \x22zweites \
Trennzeichen\x22; A\
ccessible.name: \
\x22Zweites Trennze\
ichen\x22; onTextEd\
ited: dlg.refres\
h() }\x0d\x0a         \
   }\x0d\x0a          \
  Row {\x0d\x0a       \
         visible\
: dlg.op === \x22ex\
tract_first\x22 || \
dlg.op === \x22extr\
act_last\x22 || dlg\
.op === \x22split_p\
art\x22 || dlg.op =\
== \x22split_fixed\x22\
; spacing: 6\x0d\x0a  \
              Te\
xt { text: dlg.o\
p === \x22split_par\
t\x22 ? \x22Teil Nr.\x22 \
: \x22Zeichen\x22; fon\
t.pixelSize: 11;\
 anchors.vertica\
lCenter: parent.\
verticalCenter; \
width: 78 }\x0d\x0a   \
             Tex\
tField { id: num\
Field; width: 60\
; implicitHeight\
: 26; font.pixel\
Size: 11; select\
ByMouse: true; i\
nputMethodHints:\
 Qt.ImhDigitsOnl\
y; Accessible.na\
me: \x22Anzahl Zeic\
hen\x22; onTextEdit\
ed: dlg.refresh(\
) }\x0d\x0a           \
 }\x0d\x0a            \
Row {\x0d\x0a         \
       visible: \
dlg.op === \x22spli\
t_fixed\x22; spacin\
g: 6\x0d\x0a          \
      Text { tex\
t: \x22Beginnt bei\x22\
; font.pixelSize\
: 11; anchors.ve\
rticalCenter: pa\
rent.verticalCen\
ter; width: 78 }\
\x0d\x0a              \
  TextField { id\
: startField; wi\
dth: 60; implici\
tHeight: 26; fon\
t.pixelSize: 11;\
 selectByMouse: \
true; inputMetho\
dHints: Qt.ImhDi\
gitsOnly; Access\
ible.name: \x22Star\
tposition\x22; onTe\
xtEdited: dlg.re\
fresh() }\x0d\x0a     \
       }\x0d\x0a      \
      CheckBox {\
 id: wholeCheck;\
 visible: dlg.op\
 === \x22replace\x22; \
text: \x22Nur wenn \
die ganze Zelle \
gleich ist\x22; fon\
t.pixelSize: 11;\
 onToggled: dlg.\
refresh() }\x0d\x0a   \
         CheckBo\
x { id: caseChec\
k; visible: dlg.\
op === \x22replace\x22\
; text: \x22Gro\xc3\x9f-/\
Kleinschreibung \
beachten\x22; font.\
pixelSize: 11; o\
nToggled: dlg.re\
fresh() }\x0d\x0a     \
       Row {\x0d\x0a  \
              vi\
sible: dlg.op ==\
= \x22format\x22; spac\
ing: 6\x0d\x0a        \
        Text { t\
ext: \x22Text vor\x22;\
 font.pixelSize:\
 11; anchors.ver\
ticalCenter: par\
ent.verticalCent\
er; width: 78 }\x0d\
\x0a               \
 TextField { id:\
 preField; width\
: 220; implicitH\
eight: 26; font.\
pixelSize: 11; s\
electByMouse: tr\
ue; Accessible.n\
ame: \x22Text vor\x22;\
 onTextEdited: d\
lg.refresh() }\x0d\x0a\
            }\x0d\x0a \
           Row {\
\x0d\x0a              \
  visible: dlg.o\
p === \x22format\x22; \
spacing: 6\x0d\x0a    \
            Text\
 { text: \x22Text n\
ach\x22; font.pixel\
Size: 11; anchor\
s.verticalCenter\
: parent.vertica\
lCenter; width: \
78 }\x0d\x0a          \
      TextField \
{ id: sufField; \
width: 220; impl\
icitHeight: 26; \
font.pixelSize: \
11; selectByMous\
e: true; Accessi\
ble.name: \x22Text \
nach\x22; onTextEdi\
ted: dlg.refresh\
() }\x0d\x0a          \
  }\x0d\x0a           \
 Row {\x0d\x0a        \
        visible:\
 dlg.op === \x22for\
mat\x22; spacing: 6\
\x0d\x0a              \
  Text { text: \x22\
Mit 0 auff\xc3\xbcllen\
 auf\x22; font.pixe\
lSize: 11; ancho\
rs.verticalCente\
r: parent.vertic\
alCenter; width:\
 78 }\x0d\x0a         \
       TextField\
 { id: padField;\
 width: 60; impl\
icitHeight: 26; \
font.pixelSize: \
11; selectByMous\
e: true; placeho\
lderText: \x22digit\
s\x22; inputMethodH\
ints: Qt.ImhDigi\
tsOnly; Accessib\
le.name: \x22Anzahl\
 Stellen\x22; onTex\
tEdited: dlg.ref\
resh() }\x0d\x0a      \
          Text {\
 text: \x22Stellen,\
 z. B. 4 -> 0004\
\x22; font.pixelSiz\
e: 10; color: \x22#\
52606d\x22; anchors\
.verticalCenter:\
 parent.vertical\
Center }\x0d\x0a      \
      }\x0d\x0a       \
     Row {\x0d\x0a    \
            visi\
ble: dlg.op === \
\x22normalise_size\x22\
; spacing: 6\x0d\x0a  \
              Te\
xt { text: \x22Rein\
e Zahl\x22; font.pi\
xelSize: 11; anc\
hors.verticalCen\
ter: parent.vert\
icalCenter; widt\
h: 78 }\x0d\x0a       \
         ComboBo\
x {\x0d\x0a           \
         id: bar\
eCombo\x0d\x0a        \
            mode\
l: [{ text: \x22ist\
 Zoll  (40 -> 40\
\x5c\x22)\x22, value: \x22in\
ch\x22 }, { text: \x22\
ist DN  (40 -> 1\
 1/2\x5c\x22)\x22, value:\
 \x22dn\x22 }]\x0d\x0a      \
              te\
xtRole: \x22text\x22; \
valueRole: \x22valu\
e\x22\x0d\x0a            \
        implicit\
Width: 220; impl\
icitHeight: 26; \
font.pixelSize: \
11\x0d\x0a            \
        Accessib\
le.name: \x22Bedeut\
ung einer reinen\
 Zahl\x22\x0d\x0a        \
            onAc\
tivated: dlg.ref\
resh()\x0d\x0a        \
        }\x0d\x0a     \
       }\x0d\x0a      \
      CheckBox {\
 id: origCheck; \
visible: dlg.edi\
tIndex < 0; text\
: \x22Originalspalt\
e ausblenden und\
 nicht exportier\
en\x22; font.pixelS\
ize: 11; checked\
: true }\x0d\x0a      \
      Text {\x0d\x0a  \
              vi\
sible: !preview.\
error\x0d\x0a         \
       text: (pr\
eview.changed ||\
 0).toLocaleStri\
ng() + \x22 von \x22 +\
 (preview.total \
|| 0).toLocaleSt\
ring() + \x22 Zelle\
n der Vorschauze\
ilen \xc3\xa4ndern sic\
h\x22\x0d\x0a            \
          + (pre\
view.unrecognise\
d ? \x22  \xc2\xb7  \x22 + p\
review.unrecogni\
sed + \x22 nicht er\
kannt (bleiben u\
nver\xc3\xa4ndert)\x22 : \
\x22\x22)\x0d\x0a           \
     font.pixelS\
ize: 10; font.bo\
ld: true; color:\
 \x22#34495e\x22; wrap\
Mode: Text.Wrap;\
 width: parent.w\
idth\x0d\x0a          \
  }\x0d\x0a           \
 Text { visible:\
 !!preview.error\
; text: preview.\
error || \x22\x22; fon\
t.pixelSize: 10;\
 color: \x22#b03a2e\
\x22; wrapMode: Tex\
t.Wrap; width: p\
arent.width }\x0d\x0a \
           Repea\
ter {\x0d\x0a         \
       model: (p\
review.rows || [\
]).slice(0, 5)\x0d\x0a\
                \
delegate: Row {\x0d\
\x0a               \
     spacing: 6\x0d\
\x0a               \
     Text { text\
: modelData.befo\
re === \x22\x22 ? \x22(le\
er)\x22 : modelData\
.before; font.pi\
xelSize: 10; wid\
th: 135; elide: \
Text.ElideRight \
}\x0d\x0a             \
       Text { te\
xt: \x22\xe2\x86\x92\x22; font.\
pixelSize: 10 }\x0d\
\x0a               \
     Text { text\
: modelData.afte\
r === \x22\x22 ? \x22(lee\
r)\x22 : modelData.\
after; font.pixe\
lSize: 10; width\
: 135; elide: Te\
xt.ElideRight }\x0d\
\x0a               \
 }\x0d\x0a            \
}\x0d\x0a            T\
ext { visible: d\
lg.applyError !=\
= \x22\x22; text: dlg.\
applyError; font\
.pixelSize: 10; \
color: \x22#b03a2e\x22\
; wrapMode: Text\
.Wrap; width: pa\
rent.width }\x0d\x0a  \
          Row {\x0d\
\x0a               \
 spacing: 6\x0d\x0a   \
             But\
ton {\x0d\x0a         \
           text:\
 dlg.editIndex >\
= 0 ? \x22\xc3\x84nderung\
 speichern\x22 : \x22A\
nwenden\x22\x0d\x0a      \
              im\
plicitHeight: 26\
; font.pixelSize\
: 11\x0d\x0a          \
          enable\
d: !preview.erro\
r\x0d\x0a             \
       Accessibl\
e.name: \x22Anwende\
n\x22\x0d\x0a            \
        onClicke\
d: {\x0d\x0a          \
              dl\
g.applyError = d\
lg.editIndex >= \
0 ? columnEditor\
Controller.editT\
extStep(dlg.edit\
Index, dlg.optio\
ns())\x0d\x0a         \
                \
                \
                \
  : columnEditor\
Controller.apply\
TextOp(dlg.row, \
dlg.op, dlg.opti\
ons())\x0d\x0a        \
                \
if (dlg.applyErr\
or === \x22\x22) dlg.c\
lose()\x0d\x0a        \
            }\x0d\x0a \
               }\
\x0d\x0a              \
  Button { text:\
 \x22Abbrechen\x22; im\
plicitHeight: 26\
; font.pixelSize\
: 11; onClicked:\
 dlg.close() }\x0d\x0a\
            }\x0d\x0a \
       }\x0d\x0a    }\x0d\
\x0a}\x0d\x0a\
\x00\x00\xb1\xd2\
/\
/ Tile editor. L\
ogical positions\
 only: the areas\
 derive their la\
yout from their \
width (responsiv\
e, DPI independe\
nt).\x0d\x0a// The exp\
orted columns (a\
ctive tiles) fil\
l the grid. Thre\
e more areas sit\
 in a right-hand\
 column and star\
t FOLDED to save\
 space:\x0d\x0a//   No\
t exported (oran\
ge) / Hidden (gr\
ey) / Renamed (r\
ed mark). Button\
s in the header \
line open them; \
at most TWO of t\
hem are open at \
a time\x0d\x0a//   (op\
ening a third fo\
lds the one open\
ed first); the o\
pen ones share t\
he height of the\
 column (stacked\
 in their fixed \
order). \x22Umbenan\
nt\x22 is a view (a\
 renamed tile is\
 also\x0d\x0a//   in i\
ts normal area) \
and shows the or\
iginal name carr\
ied along with e\
ach tile; its ti\
les cannot be dr\
agged.\x0d\x0a// Drag \
a tile into the \
other area (or u\
se the tile menu\
 / ribbon \x22Expor\
t ja/nein\x22) to i\
nclude / exclude\
 it; the table b\
elow shows both.\
\x0d\x0a// Every move \
goes through col\
umnEditorControl\
ler.moveColumn(f\
rom, to), every \
export change th\
rough setExport \
/ toggleExport.\x0d\
\x0a// Double-click\
 on a tile (not \
on its type chip\
) = the back sid\
e: all editable \
properties of th\
at ONE column in\
 a popover (Tile\
BackDialog.qml).\
\x0d\x0a// Mouse: clic\
k = active tile,\
 Shift+Click = r\
ange from the la\
st clicked tile,\
 Ctrl+Click = ad\
d to the multi s\
election (badges\
 1, 2, 3 ...), d\
ouble-click on t\
he type chip\x0d\x0a//\
 = \x22Spaltentyp \xc3\
\xa4ndern\x22, right-c\
lick / \xe2\x8b\xae = til\
e menu. While a \
group draft is o\
pen, Ctrl+Click \
/ Shift+Click al\
so add tiles to \
it.\x0d\x0a// Collapsi\
ng the right-han\
d column (Not ex\
ported / Hidden)\
 also collapses \
the colour legen\
d above it.\x0d\x0a// \
Commands (menu, \
Del, Alt+arrows)\
 act on ALL sele\
cted tiles when \
the tile belongs\
 to a multi sele\
ction.\x0d\x0a// Dialo\
gs are small pop\
overs that open \
directly below t\
he tile they bel\
ong to.\x0d\x0a// Tile\
 menu > Transfor\
m / Replace valu\
es / Fill create\
 a calculated co\
lumn (and a line\
 in the Steps pa\
nel); the source\
 is never change\
d.\x0d\x0a// Keyboard:\
 arrows move foc\
us inside the ar\
ea, Alt+Left/Rig\
ht moves the til\
e, Del hides / s\
hows, Ctrl+G gro\
ups the selected\
 tiles,\x0d\x0a// Esc \
cancels a group \
draft / clears t\
he selection, Ct\
rl+Z / Ctrl+Y un\
do / redo.\x0d\x0a// C\
olour categories\
: a tile shows t\
he colour of its\
 tag type (proje\
ct definitions >\
 Tag structures)\
 as a stripe and\
 a light fill.\x0d\x0a\
import QtQuick\x0d\x0a\
import QtQuick.C\
ontrols\x0d\x0a\x0d\x0aItem \
{\x0d\x0a    id: root\x0d\
\x0a    implicitHei\
ght: 340\x0d\x0a    fo\
cus: true\x0d\x0a\x0d\x0a   \
 readonly proper\
ty int minCell: \
104\x0d\x0a    readonl\
y property int c\
ellH: 72\x0d\x0a    re\
adonly property \
int areaGap: 8\x0d\x0a\
    readonly pro\
perty int collap\
sedWidth: 22    \
              //\
 width of the co\
llapsed side pan\
e (just the expa\
nd handle)\x0d\x0a    \
readonly propert\
y int maxOpenAre\
as: 2\x0d\x0a    reado\
nly property var\
 openAreas: tile\
Layout.openAreas\
      // right-h\
and column: open\
 areas in the or\
der they were op\
ened (1 = Not ex\
ported, 2 = Hidd\
en, 3 = Renamed)\
; [] = all folde\
d (default). The\
 state lives in \
tileLayout: the \
status strip in \
the ribbon (Tile\
Status.qml) shar\
es it\x0d\x0a    reado\
nly property int\
 openArea: openA\
reas.length ? op\
enAreas[openArea\
s.length - 1] : \
0     // the are\
a opened last (0\
 = none)\x0d\x0a    re\
adonly property \
var openSorted: \
openAreas.slice(\
).sort()  // dis\
play order top -\
> bottom in the \
right-hand colum\
n\x0d\x0a    property \
real dragX: -1  \
                \
                \
  // centre of t\
he tile being dr\
agged, in `areas\
` coordinates (-\
1 = no drag)\x0d\x0a  \
  property real \
dragY: -1\x0d\x0a    p\
roperty int pend\
ingMoveTo: -1   \
                \
          // row\
 of the tile the\
 dragged tile is\
 hovering over (\
same area); appl\
ied on drop only\
\x0d\x0a    // 0 = exp\
orted area, 1 = \
not exported, 2 \
= hidden (the op\
en one under the\
 pointer); nothi\
ng to drop on wh\
ile all are fold\
ed or over \x22Umbe\
nannt\x22\x0d\x0a    read\
only property in\
t dragTarget: {\x0d\
\x0a        if (dra\
gX < 0) return -\
1\x0d\x0a        if (d\
ragX < areaWidth\
Active + areaGap\
 / 2) return 0\x0d\x0a\
        var n = \
openSorted.lengt\
h\x0d\x0a        if (n\
 === 0) return -\
1\x0d\x0a        var a\
 = openSorted[Ma\
th.max(0, Math.m\
in(n - 1, Math.f\
loor(dragY / Mat\
h.max(1, sideAre\
aH + areaGap))))\
]\x0d\x0a        retur\
n a === 1 || a =\
== 2 ? a : -1\x0d\x0a \
   }\x0d\x0a    // rig\
ht-hand column w\
idth: a user-set\
, persisted shar\
e of the grid wi\
dth; nothing whi\
le every area is\
 folded\x0d\x0a    rea\
donly property r\
eal rightColWidt\
h: openAreas.len\
gth === 0 ? 0 : \
Math.round((area\
s.width - areaGa\
p) * tileLayout.\
rightShare)\x0d\x0a   \
 readonly proper\
ty real areaWidt\
hActive: openAre\
as.length === 0 \
? areas.width : \
areas.width - ar\
eaGap - rightCol\
Width\x0d\x0a    reado\
nly property rea\
l sideAreaH: ope\
nSorted.length <\
 2 ? areas.heigh\
t : Math.floor((\
areas.height - a\
reaGap) / 2)\x0d\x0a  \
  function isOpe\
n(i) { return op\
enAreas.indexOf(\
i) >= 0 }\x0d\x0a    f\
unction toggleAr\
ea(i) { tileLayo\
ut.toggleArea(i)\
 }         // op\
en / fold one ar\
ea; a third one \
folds the area o\
pened first\x0d\x0a\x0d\x0a \
   // --- header\
 line: hint text\
 (elided, never \
overlaps) + colo\
ur legend ------\
----------------\
----------------\
------------\x0d\x0a  \
  Item {\x0d\x0a      \
  id: head\x0d\x0a    \
    anchors { to\
p: parent.top; l\
eft: parent.left\
; right: sidePan\
e.left; rightMar\
gin: 8 }\x0d\x0a      \
  height: 26\x0d\x0a  \
      TextField \
{               \
                \
              //\
 search tiles / \
columns: only ma\
tching tiles sta\
y, live while ty\
ping\x0d\x0a          \
  id: searchFiel\
d\x0d\x0a            o\
bjectName: \x22tile\
Search\x22\x0d\x0a       \
     anchors { l\
eft: parent.left\
; verticalCenter\
: parent.vertica\
lCenter }\x0d\x0a     \
       width: 19\
0\x0d\x0a            h\
eight: 24\x0d\x0a     \
       font.pixe\
lSize: 11\x0d\x0a     \
       leftPaddi\
ng: 6\x0d\x0a         \
   rightPadding:\
 clearSearch.vis\
ible ? 20 : 6\x0d\x0a \
           topPa\
dding: 2\x0d\x0a      \
      bottomPadd\
ing: 2\x0d\x0a        \
    placeholderT\
ext: \x22Kachel / S\
palte suchen \xe2\x80\xa6\
\x22\x0d\x0a            s\
electByMouse: tr\
ue\x0d\x0a            \
onTextChanged: c\
olumnEditorContr\
oller.setSearch(\
text)\x0d\x0a         \
   Keys.onPresse\
d: function (e) \
{\x0d\x0a             \
   if (e.key ===\
 Qt.Key_Return |\
| e.key === Qt.K\
ey_Enter) {\x0d\x0a   \
                \
 columnEditorCon\
troller.searchSt\
ep((e.modifiers \
& Qt.ShiftModifi\
er) ? -1 : 1); e\
.accepted = true\
\x0d\x0a              \
  } else if (e.k\
ey === Qt.Key_Do\
wn) { columnEdit\
orController.sea\
rchStep(1); e.ac\
cepted = true }\x0d\
\x0a               \
 else if (e.key \
=== Qt.Key_Up) {\
 columnEditorCon\
troller.searchSt\
ep(-1); e.accept\
ed = true }\x0d\x0a   \
             els\
e if (e.key === \
Qt.Key_Escape) {\
\x0d\x0a              \
      if (text !\
== \x22\x22) text = \x22\x22\
\x0d\x0a              \
      else root.\
forceActiveFocus\
()\x0d\x0a            \
        e.accept\
ed = true\x0d\x0a     \
           }\x0d\x0a  \
          }\x0d\x0a   \
         Text {\x0d\
\x0a               \
 id: clearSearch\
\x0d\x0a              \
  visible: searc\
hField.text !== \
\x22\x22\x0d\x0a            \
    anchors { ri\
ght: parent.righ\
t; rightMargin: \
6; verticalCente\
r: parent.vertic\
alCenter }\x0d\x0a    \
            text\
: \x22\xe2\x9c\x95\x22\x0d\x0a       \
         font.pi\
xelSize: 10\x0d\x0a   \
             col\
or: clearSearchA\
rea.containsMous\
e ? \x22#2c3e50\x22 : \
\x22#9aa5b1\x22\x0d\x0a     \
           Mouse\
Area { id: clear\
SearchArea; anch\
ors.fill: parent\
; anchors.margin\
s: -4; hoverEnab\
led: true; curso\
rShape: Qt.Point\
ingHandCursor\x0d\x0a \
                \
          onClic\
ked: searchField\
.text = \x22\x22 }\x0d\x0a  \
          }\x0d\x0a   \
     }\x0d\x0a        \
Text {          \
                \
                \
        // numbe\
r of matches whi\
le searching\x0d\x0a  \
          id: se\
archCount\x0d\x0a     \
       visible: \
searchField.text\
 !== \x22\x22\x0d\x0a       \
     anchors { l\
eft: searchField\
.right; leftMarg\
in: 6; verticalC\
enter: parent.ve\
rticalCenter }\x0d\x0a\
            widt\
h: visible ? imp\
licitWidth : 0\x0d\x0a\
            text\
: columnConfigMo\
del.matchCount +\
 \x22 von \x22 + colum\
nConfigModel.cou\
nt\x0d\x0a            \
font.pixelSize: \
11\x0d\x0a            \
font.bold: colum\
nConfigModel.mat\
chCount === 0\x0d\x0a \
           color\
: columnConfigMo\
del.matchCount =\
== 0 ? \x22#b03a2e\x22\
 : \x22#2e9e4f\x22\x0d\x0a  \
      }\x0d\x0a       \
 // bulk button,\
 colour legend a\
nd the area butt\
ons (Not exporte\
d / Hidden / Ren\
amed) moved to T\
ileStatus.qml in\
 the ribbon (own\
er 2026-11-16)\x0d\x0a\
        Text {  \
                \
                \
                \
// hint text (el\
ided, never over\
laps)\x0d\x0a         \
   id: hintText\x0d\
\x0a            anc\
hors { left: sea\
rchCount.visible\
 ? searchCount.r\
ight : searchFie\
ld.right; leftMa\
rgin: 10; vertic\
alCenter: parent\
.verticalCenter \
}\x0d\x0a            w\
idth: Math.min(i\
mplicitWidth, Ma\
th.max(0, head.w\
idth - x - 8))\x0d\x0a\
            elid\
e: Text.ElideRig\
ht\x0d\x0a            \
text: columnConf\
igModel.count + \
\x22 Spalten   \xc2\xb7  \
 Strg+Klick = hi\
nzuf\xc3\xbcgen / entf\
ernen  \xc2\xb7  Umsch\
alt+Klick = Bere\
ich  \xc2\xb7  Doppelk\
lick auf das Typ\
-K\xc3\xbcrzel = Typ \xc3\
\xa4ndern  \xc2\xb7  Kach\
el in den andere\
n Bereich ziehen\
 = \xc3\xbcbergeben / \
nicht \xc3\xbcbergeben\
\x22\x0d\x0a            f\
ont.pixelSize: 1\
1\x0d\x0a            c\
olor: \x22#7b8794\x22\x0d\
\x0a        }\x0d\x0a    \
}\x0d\x0a\x0d\x0a    // --- \
the two areas --\
----------------\
----------------\
----------------\
----------------\
----------------\
----------------\
--\x0d\x0a    Item {\x0d\x0a\
        id: area\
s\x0d\x0a        objec\
tName: \x22tileGrid\
\x22\x0d\x0a        prope\
rty int count: c\
olumnConfigModel\
.count\x0d\x0a        \
anchors { top: h\
ead.bottom; topM\
argin: 4; left: \
parent.left; rig\
ht: sidePane.lef\
t; rightMargin: \
8; bottom: note.\
top; bottomMargi\
n: 2 }\x0d\x0a\x0d\x0a      \
  Repeater {\x0d\x0a  \
          id: ar\
eaRep\x0d\x0a         \
   model: 4     \
                \
                \
       // 0 = ex\
ported, 1 = not \
exported, 2 = hi\
dden, 3 = rename\
d (the last thre\
e: right column,\
 up to two open)\
\x0d\x0a            de\
legate: Rectangl\
e {\x0d\x0a           \
     id: area\x0d\x0a \
               r\
eadonly property\
 bool exportedAr\
ea: index === 0\x0d\
\x0a               \
 readonly proper\
ty bool hiddenAr\
ea: index === 2\x0d\
\x0a               \
 readonly proper\
ty bool renamedA\
rea: index === 3\
\x0d\x0a              \
  readonly prope\
rty int tileCoun\
t: index === 0 ?\
 columnConfigMod\
el.count - colum\
nConfigModel.not\
ExportedCount - \
columnConfigMode\
l.hiddenCount\x0d\x0a \
                \
                \
                \
: index === 1 ? \
columnConfigMode\
l.notExportedCou\
nt\x0d\x0a            \
                \
                \
     : index ===\
 2 ? columnConfi\
gModel.hiddenCou\
nt\x0d\x0a            \
                \
                \
     : columnCon\
figModel.renamed\
Count\x0d\x0a         \
       readonly \
property int col\
s: Math.max(1, M\
ath.floor(flow.w\
idth / root.minC\
ell))\x0d\x0a         \
       readonly \
property real ce\
llW: Math.floor(\
flow.width / col\
s)\x0d\x0a            \
    readonly pro\
perty bool dropH\
ere: root.dragTa\
rget === index\x0d\x0a\
                \
readonly propert\
y int sidePos: r\
oot.openSorted.i\
ndexOf(index)   \
  // place in th\
e right-hand col\
umn (0 = top), -\
1 = folded\x0d\x0a    \
            read\
only property st\
ring areaColor: \
exportedArea ? \x22\
#2e9e4f\x22 : hidde\
nArea ? \x22#7b8794\
\x22 : renamedArea \
? \x22#d32f2f\x22 : \x22#\
f08c00\x22\x0d\x0a       \
         readonl\
y property strin\
g areaFill: expo\
rtedArea ? \x22#eef\
8f1\x22 : hiddenAre\
a ? \x22#e5e7eb\x22 : \
renamedArea ? \x22#\
fdecea\x22 : \x22#ffe9\
c7\x22\x0d\x0a           \
     function sl\
otAt(r) { return\
 tiles.itemAt(r)\
 }\x0d\x0a            \
    function rev\
eal(item) {     \
                \
    // keep a ke\
yboard-selected \
tile inside the \
visible part of \
the area\x0d\x0a      \
              if\
 (!item) return\x0d\
\x0a               \
     if (item.y \
< flick.contentY\
) flick.contentY\
 = item.y\x0d\x0a     \
               e\
lse if (item.y +\
 item.height > f\
lick.contentY + \
flick.height) fl\
ick.contentY = i\
tem.y + item.hei\
ght - flick.heig\
ht\x0d\x0a            \
    }\x0d\x0a         \
       x: export\
edArea ? 0 : roo\
t.areaWidthActiv\
e + root.areaGap\
\x0d\x0a              \
  y: exportedAre\
a ? 0 : Math.max\
(0, sidePos) * (\
root.sideAreaH +\
 root.areaGap)\x0d\x0a\
                \
width: exportedA\
rea ? root.areaW\
idthActive : roo\
t.rightColWidth\x0d\
\x0a               \
 height: exporte\
dArea ? areas.he\
ight : root.side\
AreaH       // o\
ne open side are\
a: whole height;\
 two: half each\x0d\
\x0a               \
 visible: export\
edArea || sidePo\
s >= 0\x0d\x0a        \
        radius: \
6\x0d\x0a             \
   color: dropHe\
re ? area.areaFi\
ll : (exportedAr\
ea ? \x22#fbfcfd\x22 :\
 hiddenArea ? \x22#\
f5f6f8\x22 : rename\
dArea ? \x22#fffafa\
\x22 : \x22#fffaf1\x22)\x0d\x0a\
                \
border.width: dr\
opHere ? 2 : 1\x0d\x0a\
                \
border.color: dr\
opHere ? area.ar\
eaColor : (expor\
tedArea ? \x22#c3cc\
d6\x22 : hiddenArea\
 ? \x22#d3d9e0\x22 : r\
enamedArea ? \x22#f\
1b5b0\x22 : \x22#f2c98\
f\x22)\x0d\x0a\x0d\x0a         \
       Text {\x0d\x0a \
                \
   id: title\x0d\x0a  \
                \
  x: 10; y: 4\x0d\x0a \
                \
   text: (area.e\
xportedArea ? \x22E\
xportierte Spalt\
en\x22 : area.hidde\
nArea ? \x22Ausgebl\
endet\x22 : area.re\
namedArea ? \x22Umb\
enannt\x22 : \x22Nicht\
 exportiert\x22) + \
\x22  (\x22 + area.til\
eCount + \x22)\x22\x0d\x0a  \
                \
  font.pixelSize\
: 11\x0d\x0a          \
          font.b\
old: true\x0d\x0a     \
               c\
olor: area.expor\
tedArea ? \x22#3449\
5e\x22 : area.hidde\
nArea ? \x22#52606d\
\x22 : area.renamed\
Area ? \x22#b3261e\x22\
 : \x22#c2620a\x22\x0d\x0a  \
              }\x0d\
\x0a               \
 Text {\x0d\x0a       \
             vis\
ible: index !== \
1\x0d\x0a             \
       anchors {\
 left: title.rig\
ht; leftMargin: \
8; right: area.e\
xportedArea ? pa\
rent.right : bul\
kBtn.left; right\
Margin: 8; verti\
calCenter: title\
.verticalCenter \
}\x0d\x0a             \
       elide: Te\
xt.ElideRight\x0d\x0a \
                \
   font.pixelSiz\
e: 10\x0d\x0a         \
           color\
: \x22#7b8794\x22\x0d\x0a   \
                \
 text: area.expo\
rtedArea ? \x22dies\
e Spalten werden\
 \xc3\xbcbergeben und \
mit \xe2\x80\x9eAls Excel\
 speichern\xe2\x80\x9c ge\
schrieben\x22\x0d\x0a    \
                \
                \
        : area.r\
enamedArea ? \x22ne\
uer Name auf der\
 Kachel, Origina\
lname dar\xc3\xbcber \xe2\
\x80\x93 nur Anzeige, \
die Daten bleibe\
n unver\xc3\xa4ndert\x22\x0d\
\x0a               \
                \
             : \x22\
in der Datentabe\
lle ausgeblendet\
; bleibt Teil de\
r Ansicht (Expor\
t bleibt)\x22\x0d\x0a    \
            }\x0d\x0a \
               T\
ext {           \
                \
               /\
/ index 1 only: \
leave room for t\
he collapse butt\
on\x0d\x0a            \
        visible:\
 index === 1\x0d\x0a  \
                \
  anchors { left\
: title.right; l\
eftMargin: 8; ri\
ght: bulkBtn.lef\
t; rightMargin: \
8; verticalCente\
r: title.vertica\
lCenter }\x0d\x0a     \
               e\
lide: Text.Elide\
Right\x0d\x0a         \
           font.\
pixelSize: 10\x0d\x0a \
                \
   color: \x22#7b87\
94\x22\x0d\x0a           \
         text: \x22\
in der Tabelle s\
ichtbar, nicht e\
xportiert\x22\x0d\x0a    \
            }\x0d\x0a \
               T\
ext {           \
                \
               /\
/ fold this area\
 again (the butt\
ons in the heade\
r line do the sa\
me)\x0d\x0a           \
         id: col\
lapseBtn\x0d\x0a      \
              vi\
sible: !area.exp\
ortedArea\x0d\x0a     \
               a\
nchors { top: pa\
rent.top; right:\
 parent.right; t\
opMargin: 2; rig\
htMargin: 4 }\x0d\x0a \
                \
   text: \x22\xc2\xab\x22   \
                \
             // \
\xc2\xab\x0d\x0a            \
        font.pix\
elSize: 13\x0d\x0a    \
                \
color: collapseA\
rea.containsMous\
e ? \x22#2c3e50\x22 : \
\x22#9aa5b1\x22\x0d\x0a     \
               M\
ouseArea { id: c\
ollapseArea; anc\
hors.margins: -4\
; anchors.fill: \
parent; hoverEna\
bled: true; curs\
orShape: Qt.Poin\
tingHandCursor\x0d\x0a\
                \
               o\
nClicked: root.t\
oggleArea(index)\
 }\x0d\x0a            \
        ToolTip.\
visible: collaps\
eArea.containsMo\
use\x0d\x0a           \
         ToolTip\
.text: \x22Bereich \
einklappen\x22\x0d\x0a   \
             }\x0d\x0a\
                \
Rectangle {     \
                \
                \
// bulk button: \
\x22Nicht exportier\
t\x22 -> hide all i\
n the table, \x22Au\
sgeblendet\x22 -> s\
how all again\x0d\x0a \
                \
   id: bulkBtn\x0d\x0a\
                \
    visible: are\
a.hiddenArea && \
area.tileCount >\
 0              \
                \
    // the \x22Nich\
t exportiert\x22 on\
e sits in the he\
ader line\x0d\x0a     \
               w\
idth: bulkText.i\
mplicitWidth + 1\
4; height: 16; r\
adius: 3\x0d\x0a      \
              an\
chors { top: par\
ent.top; topMarg\
in: 3; right: co\
llapseBtn.left; \
rightMargin: 8 }\
\x0d\x0a              \
      color: bul\
kArea.containsMo\
use ? area.areaF\
ill : \x22transpare\
nt\x22\x0d\x0a           \
         border.\
width: 1\x0d\x0a      \
              bo\
rder.color: area\
.areaColor\x0d\x0a    \
                \
Text { id: bulkT\
ext; anchors.cen\
terIn: parent; f\
ont.pixelSize: 1\
0; color: area.h\
iddenArea ? \x22#52\
606d\x22 : \x22#c2620a\
\x22\x0d\x0a             \
              te\
xt: area.hiddenA\
rea || columnCon\
figModel.tableHi\
ddenCount >= col\
umnConfigModel.n\
otExportedCount \
? \x22Alle in Tabel\
le einblenden\x22 :\
 \x22Alle in Tabell\
e ausblenden\x22 }\x0d\
\x0a               \
     MouseArea {\
 id: bulkArea; a\
nchors.fill: par\
ent; hoverEnable\
d: true; cursorS\
hape: Qt.Pointin\
gHandCursor\x0d\x0a   \
                \
            onCl\
icked: columnEdi\
torController.se\
tAreaHidden(area\
.hiddenArea ? 2 \
: 1) }\x0d\x0a        \
            Tool\
Tip.visible: bul\
kArea.containsMo\
use\x0d\x0a           \
         ToolTip\
.text: area.hidd\
enArea ? \x22Alle a\
usgeblendeten Sp\
alten wieder in \
der Tabelle zeig\
en (ein R\xc3\xbcckg\xc3\xa4\
ngig-Schritt)\x22\x0d\x0a\
                \
                \
                \
  : (columnConfi\
gModel.tableHidd\
enCount >= colum\
nConfigModel.not\
ExportedCount ? \
\x22Nicht exportier\
te Spalten in de\
r Tabelle unten \
wieder zeigen (e\
in R\xc3\xbcckg\xc3\xa4ngig-\
Schritt)\x22 : \x22All\
e nicht exportie\
rten Spalten nur\
 in der Tabelle \
unten ausblenden\
; die Kacheln bl\
eiben hier, Bere\
ich \xe2\x80\x9eAusgeblen\
det\xe2\x80\x9c und Expor\
t bleiben unver\xc3\
\xa4ndert (ein R\xc3\xbcc\
kg\xc3\xa4ngig-Schritt\
)\x22)\x0d\x0a           \
     }\x0d\x0a        \
        Text {  \
                \
                \
        // empty\
 \x22nicht exportie\
rt\x22 / \x22hidden\x22 a\
rea\x0d\x0a           \
         visible\
: !area.exported\
Area && area.til\
eCount === 0\x0d\x0a  \
                \
  anchors.center\
In: parent\x0d\x0a    \
                \
width: parent.wi\
dth - 24\x0d\x0a      \
              ho\
rizontalAlignmen\
t: Text.AlignHCe\
nter\x0d\x0a          \
          wrapMo\
de: Text.Wrap\x0d\x0a \
                \
   font.pixelSiz\
e: 11\x0d\x0a         \
           color\
: area.hiddenAre\
a ? \x22#9aa5b1\x22 : \
area.renamedArea\
 ? \x22#c9a09c\x22 : \x22\
#b8a27c\x22\x0d\x0a      \
              te\
xt: area.hiddenA\
rea ? \x22No column\
 is hidden.\x5cnDra\
g a tile here, o\
r use the tile m\
enu, to hide it.\
\x22\x0d\x0a             \
                \
             : a\
rea.renamedArea \
? \x22No column is \
renamed.\x5cnTile m\
enu > Rename out\
put column ... r\
enames it visual\
ly; the data is \
not changed.\x22\x0d\x0a \
                \
                \
         : \x22No c\
olumn is left ou\
t of the export.\
\x5cnDrag a tile he\
re to exclude it\
.\x22\x0d\x0a            \
    }\x0d\x0a\x0d\x0a       \
         Flickab\
le {\x0d\x0a          \
          id: fl\
ick\x0d\x0a           \
         anchors\
 { top: parent.t\
op; topMargin: 2\
4; left: parent.\
left; right: par\
ent.right; botto\
m: parent.bottom\
; margins: 4 }\x0d\x0a\
                \
    contentWidth\
: width\x0d\x0a       \
             con\
tentHeight: flow\
.height\x0d\x0a       \
             cli\
p: true\x0d\x0a       \
             int\
eractive: conten\
tHeight > height\
               /\
/ no flicking (a\
nd no mouse stea\
ling from tile d\
rags) when every\
thing fits\x0d\x0a    \
                \
boundsBehavior: \
Flickable.StopAt\
Bounds\x0d\x0a        \
            Scro\
llBar.vertical: \
ScrollBar { }\x0d\x0a \
                \
   Flow {\x0d\x0a     \
                \
   id: flow\x0d\x0a   \
                \
     width: flic\
k.width - 10\x0d\x0a  \
                \
      Repeater {\
\x0d\x0a              \
              id\
: tiles\x0d\x0a       \
                \
     model: colu\
mnConfigModel\x0d\x0a \
                \
           deleg\
ate: Item {\x0d\x0a   \
                \
             id:\
 slot\x0d\x0a         \
                \
       readonly \
property bool he\
re: model.match \
&& (area.renamed\
Area ? model.ren\
amed\x0d\x0a          \
                \
                \
                \
                \
    : area.hidde\
nArea ? model.hi\
dden : (!model.h\
idden && model.i\
nExport === area\
.exportedArea))\x0d\
\x0a               \
                \
 visible: here\x0d\x0a\
                \
                \
width: here ? ar\
ea.cellW : 0\x0d\x0a  \
                \
              he\
ight: here ? roo\
t.cellH : 0\x0d\x0a\x0d\x0a \
                \
               D\
ropIndicator {\x0d\x0a\
                \
                \
    id: marker\x0d\x0a\
                \
                \
    anchors { le\
ft: parent.left;\
 top: parent.top\
; bottom: parent\
.bottom; topMarg\
in: 4; bottomMar\
gin: 4 }\x0d\x0a      \
                \
              ac\
tive: drop.conta\
insDrag\x0d\x0a       \
                \
         }\x0d\x0a    \
                \
            Drop\
Area {\x0d\x0a        \
                \
            id: \
drop\x0d\x0a          \
                \
          anchor\
s.fill: parent\x0d\x0a\
                \
                \
    enabled: slo\
t.here && !area.\
renamedArea\x0d\x0a   \
                \
                \
 // insertion dr\
op inside ONE ar\
ea: only the pos\
ition is remembe\
red while draggi\
ng (the marker s\
hows it);\x0d\x0a     \
                \
               /\
/ the move itsel\
f - and with it \
the rebuild of t\
he table below -\
 happens once, o\
n drop (finishDr\
ag)\x0d\x0a           \
                \
         onEnter\
ed: function (d)\
 {\x0d\x0a            \
                \
            var \
from = d.source.\
slotIndex\x0d\x0a     \
                \
                \
   var fromHere \
= area.hiddenAre\
a ? d.source.hid\
denColumn\x0d\x0a     \
                \
                \
                \
                \
  : (!d.source.h\
iddenColumn && d\
.source.inExport\
 === area.export\
edArea)\x0d\x0a       \
                \
                \
 if (from >= 0 &\
& from !== index\
 && fromHere)\x0d\x0a \
                \
                \
           root.\
pendingMoveTo = \
index\x0d\x0a         \
                \
           }\x0d\x0a  \
                \
                \
  onExited: if (\
root.pendingMove\
To === index) ro\
ot.pendingMoveTo\
 = -1\x0d\x0a         \
                \
       }\x0d\x0a      \
                \
          Column\
Card {\x0d\x0a        \
                \
            id: \
card\x0d\x0a          \
                \
          anchor\
s.horizontalCent\
er: parent.horiz\
ontalCenter\x0d\x0a   \
                \
                \
 anchors.vertica\
lCenter: parent.\
verticalCenter\x0d\x0a\
                \
                \
    width: slot.\
width - 8\x0d\x0a     \
                \
               s\
lotIndex: index\x0d\
\x0a               \
                \
     shortName: \
model.shortName\x0d\
\x0a               \
                \
     renamed: mo\
del.renamed\x0d\x0a   \
                \
                \
 originalName: m\
odel.originalNam\
e\x0d\x0a             \
                \
       showOrigi\
nal: area.rename\
dArea\x0d\x0a         \
                \
           prote\
ctedColumn: mode\
l.protectedColum\
n\x0d\x0a             \
                \
       groupColo\
r: model.groupCo\
lor\x0d\x0a           \
                \
         groupNa\
me: model.groupN\
ame\x0d\x0a           \
                \
         tempora\
ry: model.tempor\
ary\x0d\x0a           \
                \
         splitTi\
le: model.isSpli\
t\x0d\x0a             \
                \
       chip: mod\
el.chip\x0d\x0a       \
                \
             pos\
ition: model.pos\
ition\x0d\x0a         \
                \
           hidde\
nColumn: model.h\
idden\x0d\x0a         \
                \
           compu\
ted: model.calcu\
lated\x0d\x0a         \
                \
           inExp\
ort: model.inExp\
ort\x0d\x0a           \
                \
         selOrde\
r: model.selOrde\
r\x0d\x0a             \
                \
       tip: mode\
l.tip\x0d\x0a         \
                \
           tagCo\
lor: model.tagCo\
lor\x0d\x0a           \
                \
         active:\
 index === colum\
nEditorControlle\
r.selectedRow\x0d\x0a \
                \
                \
   dragging: mou\
se.drag.active\x0d\x0a\
                \
                \
    onClicked: {\
 columnEditorCon\
troller.selectOn\
ly(index); colum\
nEditorControlle\
r.pickTile(index\
); root.forceAct\
iveFocus() }\x0d\x0a  \
                \
                \
  onCtrlClicked:\
 { columnEditorC\
ontroller.toggle\
Select(index); r\
oot.forceActiveF\
ocus() }\x0d\x0a      \
                \
              on\
ShiftClicked: fu\
nction (additive\
) { columnEditor\
Controller.selec\
tRange(index, ad\
ditive); root.fo\
rceActiveFocus()\
 }\x0d\x0a            \
                \
        onTypeRe\
quested: { if (!\
columnEditorCont\
roller.inSelecti\
on(index)) colum\
nEditorControlle\
r.selectOnly(ind\
ex); root.openTy\
pe(index) }\x0d\x0a   \
                \
                \
 onBackRequested\
: { columnEditor\
Controller.selec\
tOnly(index); ro\
ot.openBack(inde\
x) }\x0d\x0a          \
                \
          onCont\
extRequested: ro\
ot.openMenu(inde\
x)\x0d\x0a            \
                \
        onXChang\
ed: if (dragging\
) root.noteDrag(\
card)\x0d\x0a         \
                \
           onYCh\
anged: if (dragg\
ing) root.noteDr\
ag(card)\x0d\x0a      \
                \
              on\
DraggingChanged:\
 if (!dragging) \
root.finishDrag(\
index)\x0d\x0a        \
                \
            stat\
es: State {\x0d\x0a   \
                \
                \
     when: card.\
mouse.drag.activ\
e               \
    // the dragg\
ed tile floats a\
bove both areas\x0d\
\x0a               \
                \
         ParentC\
hange { target: \
card; parent: dr\
agLayer }\x0d\x0a     \
                \
                \
   AnchorChanges\
 { target: card;\
 anchors.horizon\
talCenter: undef\
ined; anchors.ve\
rticalCenter: un\
defined }\x0d\x0a     \
                \
               }\
\x0d\x0a              \
                \
  }\x0d\x0a           \
                \
 }\x0d\x0a            \
            }\x0d\x0a \
                \
   }\x0d\x0a          \
      }\x0d\x0a       \
     }\x0d\x0a        \
}\x0d\x0a\x0d\x0a        // \
--- draggable sp\
litter between t\
he exported area\
 and the right-h\
and column; reme\
mbers the width \
(tileLayout) ---\
-\x0d\x0a        Recta\
ngle {\x0d\x0a        \
    id: rightSpl\
itter\x0d\x0a         \
   visible: root\
.openAreas.lengt\
h > 0\x0d\x0a         \
   width: 6\x0d\x0a   \
         x: root\
.areaWidthActive\
 - width / 2\x0d\x0a  \
          anchor\
s { top: areas.t\
op; bottom: area\
s.bottom }\x0d\x0a    \
        color: r\
ightSplitterArea\
.containsMouse |\
| rightSplitterA\
rea.pressed ? \x22#\
9fb4c7\x22 : \x22trans\
parent\x22\x0d\x0a       \
     MouseArea {\
\x0d\x0a              \
  id: rightSplit\
terArea\x0d\x0a       \
         anchors\
.fill: parent\x0d\x0a \
               a\
nchors.margins: \
-3\x0d\x0a            \
    hoverEnabled\
: true\x0d\x0a        \
        cursorSh\
ape: Qt.SizeHorC\
ursor\x0d\x0a         \
       property \
real startX: 0\x0d\x0a\
                \
property real st\
artShare: 0\x0d\x0a   \
             onP\
ressed: function\
 (m) { startX = \
mapToItem(areas,\
 m.x, 0).x; star\
tShare = tileLay\
out.rightShare }\
\x0d\x0a              \
  onPositionChan\
ged: function (m\
) {\x0d\x0a           \
         if (!pr\
essed) return\x0d\x0a \
                \
   var curX = ma\
pToItem(areas, m\
.x, 0).x\x0d\x0a      \
              va\
r span = Math.ma\
x(1, areas.width\
 - root.areaGap)\
\x0d\x0a              \
      tileLayout\
.rightShare = st\
artShare + (star\
tX - curX) / spa\
n\x0d\x0a             \
   }\x0d\x0a          \
  }\x0d\x0a        }\x0d\x0a\
    }\x0d\x0a    Item \
{ id: dragLayer;\
 anchors.fill: p\
arent; z: 100 }\x0d\
\x0a\x0d\x0a    function \
noteDrag(card) {\
                \
                \
    // where is \
the dragged tile\
 right now (area\
 decision at the\
 end of the drag\
)\x0d\x0a        var p\
 = card.mapToIte\
m(areas, card.wi\
dth / 2, card.he\
ight / 2)\x0d\x0a     \
   if (p.y >= -2\
0 && p.y <= area\
s.height + 20 &&\
 p.x >= 0 && p.x\
 <= areas.width)\
 {\x0d\x0a            \
dragX = p.x; dra\
gY = p.y\x0d\x0a      \
  } else {\x0d\x0a    \
        dragX = \
-1; dragY = -1\x0d\x0a\
        }\x0d\x0a    }\
\x0d\x0a    function f\
inishDrag(row) {\
                \
                \
   // tile dropp\
ed: exported <->\
 not exported = \
export state; in\
to/out of \x22Ausge\
blendet\x22 = visib\
ility\x0d\x0a        v\
ar target = drag\
Target\x0d\x0a        \
var moveTo = pen\
dingMoveTo\x0d\x0a    \
    pendingMoveT\
o = -1\x0d\x0a        \
dragX = -1; drag\
Y = -1\x0d\x0a        \
if (target < 0) \
return\x0d\x0a        \
if (moveTo >= 0 \
&& moveTo !== ro\
w && target === \
areaOf(row)) {  \
 // dropped on a\
 tile of its own\
 area: the one a\
nd only move\x0d\x0a  \
          column\
EditorController\
.moveColumn(row,\
 moveTo)\x0d\x0a      \
      return\x0d\x0a  \
      }\x0d\x0a       \
 var wasHidden =\
 columnEditorCon\
troller.menuInfo\
(row).allHidden\x0d\
\x0a        if (tar\
get === 2) {    \
                \
                \
  // dropped on \
\x22Ausgeblendet\x22: \
hide it, export \
state is kept un\
changed\x0d\x0a       \
     if (!wasHid\
den) {\x0d\x0a        \
        columnEd\
itorController.s\
etHidden(row, tr\
ue)\x0d\x0a           \
     if (!column\
EditorController\
.inSelection(row\
)) columnEditorC\
ontroller.select\
Only(row)\x0d\x0a     \
       }\x0d\x0a      \
      return\x0d\x0a  \
      }\x0d\x0a       \
 if (wasHidden) \
columnEditorCont\
roller.setHidden\
(row, false)    \
// dropped out o\
f \x22Ausgeblendet\x22\
: show it again \
...\x0d\x0a        var\
 wantExport = ta\
rget === 0\x0d\x0a    \
    var ex = col\
umnEditorControl\
ler.exportedAt(r\
ow)\x0d\x0a        if \
(ex !== wantExpo\
rt) {\x0d\x0a         \
   columnEditorC\
ontroller.setExp\
ort(row, wantExp\
ort)       // ..\
. and put it whe\
re it was droppe\
d (acts on the w\
hole multi selec\
tion)\x0d\x0a        }\
\x0d\x0a        if (wa\
sHidden || ex !=\
= wantExport) {\x0d\
\x0a            if \
(!columnEditorCo\
ntroller.inSelec\
tion(row)) colum\
nEditorControlle\
r.selectOnly(row\
)   // a multi s\
election stays s\
elected\x0d\x0a       \
 }\x0d\x0a    }\x0d\x0a    f\
unction areaOf(r\
ow) {           \
                \
            // 0\
 = exported, 1 =\
 not exported, 2\
 = hidden\x0d\x0a     \
   if (columnEdi\
torController.me\
nuInfo(row).allH\
idden) return 2\x0d\
\x0a        return \
columnEditorCont\
roller.exportedA\
t(row) ? 0 : 1\x0d\x0a\
    }\x0d\x0a    funct\
ion selectedArea\
() { return area\
Of(columnEditorC\
ontroller.select\
edRow) }\x0d\x0a    fu\
nction moveFocus\
(step) {        \
                \
           // ar\
row keys: inside\
 the area of the\
 active tile (a \
folded area is o\
pened first)\x0d\x0a  \
      var r = co\
lumnEditorContro\
ller.selectedRow\
\x0d\x0a        if (r \
< 0) { r = 0 }\x0d\x0a\
        var nr =\
 columnEditorCon\
troller.neighbou\
r(r, step)\x0d\x0a    \
    if (nr < 0 |\
| nr === columnE\
ditorController.\
selectedRow) ret\
urn\x0d\x0a        col\
umnEditorControl\
ler.selectOnly(n\
r)\x0d\x0a        var \
ar = areaOf(nr)\x0d\
\x0a        if (ar \
> 0 && !isOpen(a\
r)) toggleArea(a\
r)\x0d\x0a        var \
a = areaRep.item\
At(ar)\x0d\x0a        \
if (a) a.reveal(\
a.slotAt(nr))\x0d\x0a \
   }\x0d\x0a    functi\
on colsOfSelecte\
d() {\x0d\x0a        v\
ar a = areaRep.i\
temAt(columnEdit\
orController.sel\
ectedRow >= 0 ? \
selectedArea() :\
 0)\x0d\x0a        ret\
urn a ? a.cols :\
 1\x0d\x0a    }\x0d\x0a\x0d\x0a   \
 Keys.onPressed:\
 function (e) {\x0d\
\x0a        if ((e.\
modifiers & Qt.A\
ltModifier) && (\
e.key === Qt.Key\
_Left || e.key =\
== Qt.Key_Right)\
) {\x0d\x0a           \
 columnEditorCon\
troller.moveBy(c\
olumnEditorContr\
oller.selectedRo\
w, e.key === Qt.\
Key_Left ? -1 : \
1)\x0d\x0a            \
e.accepted = tru\
e\x0d\x0a        } els\
e if (e.key === \
Qt.Key_Left) { m\
oveFocus(-1); e.\
accepted = true \
}\x0d\x0a        else \
if (e.key === Qt\
.Key_Right) { mo\
veFocus(1); e.ac\
cepted = true }\x0d\
\x0a        else if\
 (e.key === Qt.K\
ey_Up) { moveFoc\
us(-colsOfSelect\
ed()); e.accepte\
d = true }\x0d\x0a    \
    else if (e.k\
ey === Qt.Key_Do\
wn) { moveFocus(\
colsOfSelected()\
); e.accepted = \
true }\x0d\x0a        \
else if (e.key =\
== Qt.Key_Delete\
) {\x0d\x0a           \
 columnEditorCon\
troller.toggleHi\
dden(columnEdito\
rController.sele\
ctedRow); e.acce\
pted = true\x0d\x0a   \
     } else if (\
e.key === Qt.Key\
_Escape) {\x0d\x0a    \
        if (colu\
mnEditorControll\
er.hasDraft) col\
umnEditorControl\
ler.cancelGroup(\
)\x0d\x0a            e\
lse columnEditor\
Controller.clear\
Selection()\x0d\x0a   \
         e.accep\
ted = true\x0d\x0a    \
    } else if ((\
e.modifiers & Qt\
.ControlModifier\
) && e.key === Q\
t.Key_F) {\x0d\x0a    \
        searchFi\
eld.forceActiveF\
ocus(); searchFi\
eld.selectAll();\
 e.accepted = tr\
ue\x0d\x0a        } el\
se if ((e.modifi\
ers & Qt.Control\
Modifier) && e.k\
ey === Qt.Key_G)\
 {\x0d\x0a            \
columnEditorCont\
roller.startGrou\
p(); e.accepted \
= true\x0d\x0a        \
} else if ((e.mo\
difiers & Qt.Con\
trolModifier) &&\
 e.key === Qt.Ke\
y_Z) {\x0d\x0a        \
    columnEditor\
Controller.undo(\
); e.accepted = \
true\x0d\x0a        } \
else if ((e.modi\
fiers & Qt.Contr\
olModifier) && e\
.key === Qt.Key_\
Y) {\x0d\x0a          \
  columnEditorCo\
ntroller.redo();\
 e.accepted = tr\
ue\x0d\x0a        } el\
se if (e.key ===\
 Qt.Key_Return |\
| e.key === Qt.K\
ey_Enter) {\x0d\x0a   \
         columnE\
ditorController.\
selectOnly(colum\
nEditorControlle\
r.selectedRow); \
e.accepted = tru\
e\x0d\x0a        }\x0d\x0a  \
  }\x0d\x0a\x0d\x0a    funct\
ion tileItem(r) \
{               \
                \
        // the p\
opovers open bel\
ow this tile (wh\
ichever area sho\
ws it)\x0d\x0a        \
for (var i = 0; \
i < areaRep.coun\
t; ++i) {\x0d\x0a     \
       var a = a\
reaRep.itemAt(i)\
\x0d\x0a            va\
r it = a ? a.slo\
tAt(r) : null\x0d\x0a \
           if (i\
t && it.visible)\
 return it\x0d\x0a    \
    }\x0d\x0a        r\
eturn root\x0d\x0a    \
}\x0d\x0a    function \
openType(r) { ty\
peDialog.parent \
= tileItem(r); t\
ypeDialog.openFo\
r(r) }\x0d\x0a    func\
tion openBack(r)\
 { backDialog.pa\
rent = tileItem(\
r); backDialog.o\
penFor(r) }     \
     // back sid\
e of the tile (o\
ne tile at a tim\
e)\x0d\x0a    function\
 openTransform(r\
, op) { transfor\
mDialog.parent =\
 tileItem(r); tr\
ansformDialog.op\
enFor(r, op) }\x0d\x0a\
    function ope\
nSplit(r) { spli\
tDialog.parent =\
 tileItem(r); sp\
litDialog.openFo\
r(r) }\x0d\x0a    func\
tion openConditi\
onal(r) { condit\
ionalDialog.pare\
nt = tileItem(r)\
; conditionalDia\
log.openFor(r) }\
\x0d\x0a    function o\
penCheck(r) { ch\
eckDialog.parent\
 = tileItem(r); \
checkDialog.open\
For(r) }\x0d\x0a    fu\
nction openLooku\
p(r) { lookupDia\
log.parent = til\
eItem(r); lookup\
Dialog.openFor(r\
) }\x0d\x0a    functio\
n editStep(step)\
 {              \
                \
     // pencil o\
f the Steps pane\
l: the dialog of\
 the function, f\
illed with the s\
tep's settings\x0d\x0a\
        var info\
 = columnEditorC\
ontroller.stepIn\
fo(step.index)\x0d\x0a\
        var r = \
columnEditorCont\
roller.rowOfKey(\
step.key)\x0d\x0a     \
   var anchorRow\
 = r >= 0 ? r : \
0\x0d\x0a        if (i\
nfo.kind === \x22te\
xt_op\x22) { transf\
ormDialog.parent\
 = tileItem(anch\
orRow); transfor\
mDialog.openFor(\
info.row >= 0 ? \
info.row : ancho\
rRow, info.op, s\
tep.index) }\x0d\x0a  \
      else if (i\
nfo.kind === \x22co\
nditional\x22) { co\
nditionalDialog.\
parent = tileIte\
m(anchorRow); co\
nditionalDialog.\
openFor(anchorRo\
w, step.index) }\
\x0d\x0a        else i\
f (info.kind ===\
 \x22check_list\x22) {\
 checkDialog.par\
ent = tileItem(a\
nchorRow); check\
Dialog.openFor(i\
nfo.row, step.in\
dex) }\x0d\x0a    }\x0d\x0a \
   function runO\
p(r, op) {      \
                \
               /\
/ one-click func\
tions run at onc\
e, the others as\
k first\x0d\x0a       \
 var e = columnE\
ditorController.\
applyTextOp(r, o\
p, { replaceOrig\
inal: true })\x0d\x0a \
       if (e !==\
 \x22\x22) note.text =\
 e\x0d\x0a    }\x0d\x0a    f\
unction openMenu\
(row) {\x0d\x0a       \
 if (!columnEdit\
orController.inS\
election(row)) c\
olumnEditorContr\
oller.selectOnly\
(row)     // rig\
ht-click outside\
 the selection =\
 new selection\x0d\x0a\
        tileMenu\
.row = row\x0d\x0a    \
    tileMenu.inf\
o = columnEditor\
Controller.menuI\
nfo(row)\x0d\x0a      \
  tileMenu.popup\
()\x0d\x0a    }\x0d\x0a\x0d\x0a   \
 Menu {\x0d\x0a       \
 id: tileMenu\x0d\x0a \
       property \
int row: -1\x0d\x0a   \
     property va\
r info: ({ count\
: 1, multi: fals\
e, allHidden: fa\
lse, anyExported\
: true })\x0d\x0a     \
   readonly prop\
erty bool multi:\
 !!info.multi\x0d\x0a \
       readonly \
property string \
cols: multi ? in\
fo.count + \x22 Spa\
lten\x22 : \x22column\x22\
\x0d\x0a        MenuIt\
em { text: tileM\
enu.multi ? tile\
Menu.info.count \
+ \x22 Kacheln gew\xc3\
\xa4hlt\x22 : \x22\x22; visi\
ble: tileMenu.mu\
lti; enabled: fa\
lse; height: vis\
ible ? implicitH\
eight : 0 }\x0d\x0a   \
     MenuItem { \
text: tileMenu.m\
ulti ? \x22Datentyp\
 \xc3\xa4ndern: \x22 + ti\
leMenu.cols + \x22\xe2\
\x80\xa6\x22 : \x22Datentyp \
\xc3\xa4ndern \xe2\x80\xa6\x22; on\
Triggered: root.\
openType(tileMen\
u.row) }\x0d\x0a      \
  MenuItem { tex\
t: \x22Ausgabespalt\
e umbenennen \xe2\x80\xa6\
\x22;     enabled: \
!tileMenu.multi;\
 onTriggered: pr\
ompt.askRename(t\
ileMenu.row) }\x0d\x0a\
        MenuItem\
 { text: \x22Kurzna\
me der Kachel \xc3\xa4\
ndern \xe2\x80\xa6\x22;   en\
abled: !tileMenu\
.multi; onTrigge\
red: prompt.askS\
hort(tileMenu.ro\
w) }\x0d\x0a        Me\
nu {\x0d\x0a          \
  title: tileMen\
u.multi ? \x22Umwan\
deln: \x22 + tileMe\
nu.cols : \x22Umwan\
deln\x22\x0d\x0a         \
   MenuItem { te\
xt: \x22\xc3\x9cberz\xc3\xa4hli\
ge Leerzeichen e\
ntfernen\x22;      \
        onTrigge\
red: root.runOp(\
tileMenu.row, \x22t\
rim\x22) }\x0d\x0a       \
     MenuItem { \
text: \x22Versteckt\
e Zeichen entfer\
nen\x22;         on\
Triggered: root.\
runOp(tileMenu.r\
ow, \x22clean\x22) }\x0d\x0a\
            Menu\
Item { text: \x22GR\
OSSBUCHSTABEN\x22; \
                \
      onTriggere\
d: root.runOp(ti\
leMenu.row, \x22upp\
er\x22) }\x0d\x0a        \
    MenuItem { t\
ext: \x22kleinbuchs\
taben\x22;         \
              on\
Triggered: root.\
runOp(tileMenu.r\
ow, \x22lower\x22) }\x0d\x0a\
            Menu\
Item { text: \x22Je\
des Wort Gro\xc3\x9f\x22;\
             onT\
riggered: root.r\
unOp(tileMenu.ro\
w, \x22capitalise\x22)\
 }\x0d\x0a            \
MenuSeparator { \
}\x0d\x0a            M\
enuItem { text: \
\x22Rohrgr\xc3\xb6\xc3\x9fe ver\
einheitlichen \xe2\x80\
\xa6\x22;             \
onTriggered: roo\
t.openTransform(\
tileMenu.row, \x22n\
ormalise_size\x22) \
}\x0d\x0a            M\
enuItem { text: \
\x22Text erg\xc3\xa4nzen \
/ mit Nullen auf\
f\xc3\xbcllen \xe2\x80\xa6\x22;   \
   onTriggered: \
root.openTransfo\
rm(tileMenu.row,\
 \x22format\x22) }\x0d\x0a  \
          Menu {\
\x0d\x0a              \
  title: \x22Extrah\
ieren\x22\x0d\x0a        \
        MenuItem\
 { text: \x22Erste \
Zeichen \xe2\x80\xa6\x22;   \
         onTrigg\
ered: root.openT\
ransform(tileMen\
u.row, \x22extract_\
first\x22) }\x0d\x0a     \
           MenuI\
tem { text: \x22Let\
zte Zeichen \xe2\x80\xa6\x22\
;             on\
Triggered: root.\
openTransform(ti\
leMenu.row, \x22ext\
ract_last\x22) }\x0d\x0a \
               M\
enuItem { text: \
\x22Text vor einem \
Trennzeichen \xe2\x80\xa6\
\x22;     onTrigger\
ed: root.openTra\
nsform(tileMenu.\
row, \x22extract_be\
fore\x22) }\x0d\x0a      \
          MenuIt\
em { text: \x22Text\
 nach einem Tren\
nzeichen \xe2\x80\xa6\x22;  \
    onTriggered:\
 root.openTransf\
orm(tileMenu.row\
, \x22extract_after\
\x22) }\x0d\x0a          \
      MenuItem {\
 text: \x22Text zwi\
schen zwei Trenn\
zeichen \xe2\x80\xa6\x22; on\
Triggered: root.\
openTransform(ti\
leMenu.row, \x22ext\
ract_between\x22) }\
\x0d\x0a            }\x0d\
\x0a        }\x0d\x0a    \
    MenuItem { t\
ext: \x22Spalte tei\
len \xe2\x80\xa6\x22;       \
                \
 enabled: !tileM\
enu.multi; onTri\
ggered: root.ope\
nSplit(tileMenu.\
row) }\x0d\x0a        \
MenuItem { text:\
 \x22Werte ersetzen\
 \xe2\x80\xa6\x22;          \
            onTr\
iggered: root.op\
enTransform(tile\
Menu.row, \x22repla\
ce\x22) }\x0d\x0a        \
Menu {\x0d\x0a        \
    title: \x22F\xc3\xbcl\
len\x22\x0d\x0a          \
  MenuItem { tex\
t: \x22Wert nach un\
ten in leere Zel\
len kopieren\x22; o\
nTriggered: root\
.runOp(tileMenu.\
row, \x22fill_down\x22\
) }\x0d\x0a           \
 MenuItem { text\
: \x22Wert nach obe\
n in leere Zelle\
n kopieren\x22;   o\
nTriggered: root\
.runOp(tileMenu.\
row, \x22fill_up\x22) \
}\x0d\x0a        }\x0d\x0a  \
      MenuItem {\
 text: \x22Wenn \xe2\x80\xa6\
 dann-Spalte \xe2\x80\xa6\
\x22;              \
      onTriggere\
d: root.openCond\
itional(tileMenu\
.row) }\x0d\x0a       \
 Menu {\x0d\x0a       \
     title: \x22Pla\
nt 3D / Listen\x22\x0d\
\x0a            Men\
uItem { text: \x22G\
egen Codeliste p\
r\xc3\xbcfen \xe2\x80\xa6\x22;    \
   enabled: !til\
eMenu.multi; onT\
riggered: root.o\
penCheck(tileMen\
u.row) }\x0d\x0a      \
      MenuItem {\
 text: \x22Spalten \
aus einer andere\
n Liste \xe2\x80\xa6\x22;   \
enabled: !tileMe\
nu.multi; onTrig\
gered: root.open\
Lookup(tileMenu.\
row) }\x0d\x0a        \
}\x0d\x0a        MenuS\
eparator { }\x0d\x0a  \
      MenuItem {\
 text: \x22Nach lin\
ks\x22;            \
     onTriggered\
: columnEditorCo\
ntroller.moveBy(\
tileMenu.row, -1\
) }\x0d\x0a        Men\
uItem { text: \x22N\
ach rechts\x22;    \
            onTr\
iggered: columnE\
ditorController.\
moveBy(tileMenu.\
row, 1) }\x0d\x0a     \
   MenuItem { te\
xt: \x22An Position\
 verschieben \xe2\x80\xa6\
\x22;         onTri\
ggered: prompt.a\
skPosition(tileM\
enu.row) }\x0d\x0a    \
    MenuSeparato\
r { }\x0d\x0a        M\
enuItem { text: \
\x22Gew\xc3\xa4hlte Kache\
ln gruppieren (S\
trg+G)\x22; visible\
: tileMenu.multi\
; height: visibl\
e ? implicitHeig\
ht : 0; onTrigge\
red: columnEdito\
rController.star\
tGroup() }\x0d\x0a    \
    MenuItem { t\
ext: \x22Zur Gruppe\
 hinzuf\xc3\xbcgen\x22; v\
isible: !tileMen\
u.multi; height:\
 visible ? impli\
citHeight : 0; o\
nTriggered: colu\
mnEditorControll\
er.addToGroup(ti\
leMenu.row) }\x0d\x0a \
       MenuItem \
{ text: \x22Gruppe \
w\xc3\xa4hlen\x22; visibl\
e: columnEditorC\
ontroller.inGrou\
p(tileMenu.row);\
 height: visible\
 ? implicitHeigh\
t : 0\x0d\x0a         \
          onTrig\
gered: columnEdi\
torController.se\
lectGroup(tileMe\
nu.row) }\x0d\x0a     \
   MenuItem { te\
xt: \x22Gruppe aufl\
\xc3\xb6sen\x22; visible:\
 columnEditorCon\
troller.inGroup(\
tileMenu.row); h\
eight: visible ?\
 implicitHeight \
: 0\x0d\x0a           \
        onTrigge\
red: columnEdito\
rController.ungr\
oup(tileMenu.row\
) }\x0d\x0a        Men\
uItem { text: (t\
ileMenu.info.all\
Hidden ? \x22Einble\
nden: \x22 : \x22Ausbl\
enden: \x22) + tile\
Menu.cols; onTri\
ggered: columnEd\
itorController.t\
oggleHidden(tile\
Menu.row) }\x0d\x0a   \
     MenuItem { \
text: (tileMenu.\
info.anyExported\
 ? \x22Nicht export\
ieren: \x22 : \x22Expo\
rtieren: \x22) + (t\
ileMenu.info.any\
Exported ? tileM\
enu.cols + \x22 nic\
ht exportieren\x22 \
: tileMenu.cols \
+ \x22 exportieren\x22\
); onTriggered: \
columnEditorCont\
roller.toggleExp\
ort(tileMenu.row\
) }\x0d\x0a        Men\
uSeparator { }\x0d\x0a\
        MenuItem\
 { text: tileMen\
u.multi ? \x22Zur\xc3\xbc\
cksetzen: \x22 + ti\
leMenu.cols : \x22S\
palte zur\xc3\xbcckset\
zen\x22; onTriggere\
d: columnEditorC\
ontroller.resetC\
olumn(tileMenu.r\
ow) }\x0d\x0a    }\x0d\x0a\x0d\x0a\
    TextPrompt {\
\x0d\x0a        id: pr\
ompt\x0d\x0a        pr\
operty string mo\
de: \x22rename\x22\x0d\x0a  \
      property i\
nt row: -1\x0d\x0a    \
    function ask\
2(m, r, titleTex\
t, labelText, va\
lue) { mode = m;\
 row = r; parent\
 = root.tileItem\
(r); ask(titleTe\
xt, labelText, v\
alue) }\x0d\x0a       \
 function askRen\
ame(r) {\x0d\x0a      \
      var i = co\
lumnEditorContro\
ller.inspect(r)\x0d\
\x0a            ask\
2(\x22rename\x22, r, \x22\
Ausgabespalte um\
benennen\x22, \x22Neue\
r Name (die Date\
n bleiben unver\xc3\
\xa4ndert):\x22, i.out\
putName || \x22\x22)\x0d\x0a\
        }\x0d\x0a     \
   function askS\
hort(r) {\x0d\x0a     \
       var i = c\
olumnEditorContr\
oller.inspect(r)\
\x0d\x0a            as\
k2(\x22short\x22, r, \x22\
Kurzname der Kac\
hel \xc3\xa4ndern\x22, \x22T\
ext auf der Kach\
el (leer = autom\
atisch):\x22, i.sho\
rtName || \x22\x22)\x0d\x0a \
       }\x0d\x0a      \
  function askPo\
sition(r) {\x0d\x0a   \
         ask2(\x22p\
osition\x22, r, \x22An\
 Position versch\
ieben\x22, \x22Positio\
n (1 bis \x22 + col\
umnConfigModel.c\
ount + \x22):\x22, Str\
ing(r + 1))\x0d\x0a   \
     }\x0d\x0a        \
onSubmitted: fun\
ction (value) {\x0d\
\x0a            var\
 err = \x22\x22\x0d\x0a     \
       if (mode \
=== \x22short\x22) err\
 = columnEditorC\
ontroller.setSho\
rtName(row, valu\
e)\x0d\x0a            \
else if (mode ==\
= \x22position\x22) co\
lumnEditorContro\
ller.moveToPosit\
ion(row, parseIn\
t(value))\x0d\x0a     \
       else err \
= columnEditorCo\
ntroller.renameO\
utput(row, value\
)\x0d\x0a            i\
f (err !== \x22\x22) n\
ote.text = err\x0d\x0a\
        }\x0d\x0a    }\
\x0d\x0a    ChangeType\
Dialog { id: typ\
eDialog }\x0d\x0a    T\
ileBackDialog { \
id: backDialog; \
objectName: \x22til\
eBack\x22; onChange\
TypeRequested: f\
unction (r) { ro\
ot.openType(r) }\
 }\x0d\x0a    Transfor\
mDialog { id: tr\
ansformDialog }\x0d\
\x0a    SplitDialog\
 { id: splitDial\
og }\x0d\x0a    Condit\
ionalDialog { id\
: conditionalDia\
log }\x0d\x0a    Check\
Dialog { id: che\
ckDialog }\x0d\x0a    \
LookupDialog { i\
d: lookupDialog \
}\x0d\x0a\x0d\x0a    Text { \
                \
                \
     // short me\
ssages (e.g. \x22di\
e letzte sichtba\
re Spalte kann n\
icht ausgeblende\
t werden\x22); rese\
rves its own lin\
e\x0d\x0a        id: n\
ote\x0d\x0a        anc\
hors { left: par\
ent.left; bottom\
: parent.bottom \
}\x0d\x0a        heigh\
t: 14\x0d\x0a        c\
olor: \x22#b03a2e\x22\x0d\
\x0a        font.pi\
xelSize: 11\x0d\x0a   \
     elide: Text\
.ElideRight\x0d\x0a   \
     width: area\
s.width\x0d\x0a       \
 text: \x22\x22\x0d\x0a     \
   Timer { inter\
val: 6000; runni\
ng: note.text !=\
= \x22\x22; onTriggere\
d: note.text = \x22\
\x22 }\x0d\x0a    }\x0d\x0a    \
Connections {\x0d\x0a \
       target: c\
olumnEditorContr\
oller\x0d\x0a        f\
unction onMessag\
e(text) { note.t\
ext = text }\x0d\x0a  \
      function o\
nChangeTypeReque\
sted(row) { root\
.openType(row) }\
          // ask\
ed by the side p\
ane (flow deck)\x0d\
\x0a        functio\
n onEditStepRequ\
ested(step) { ro\
ot.editStep(step\
) }\x0d\x0a        fun\
ction onDraftCha\
nged() {        \
                \
      // a group\
 was started (Ct\
rl+G / Group til\
es): open the si\
de pane with the\
 dialog\x0d\x0a       \
     if (columnE\
ditorController.\
hasDraft && tile\
Layout.sideColla\
psed) tileLayout\
.sideCollapsed =\
 false\x0d\x0a        \
}\x0d\x0a        funct\
ion onSelectedCh\
anged() {       \
                \
     // active t\
ile changed (als\
o from the table\
 / search): keep\
 it in view\x0d\x0a   \
         var r =\
 columnEditorCon\
troller.selected\
Row\x0d\x0a           \
 if (r < 0 || r \
>= columnConfigM\
odel.count) retu\
rn\x0d\x0a            \
var a = areaRep.\
itemAt(root.area\
Of(r))\x0d\x0a        \
    if (a && a.v\
isible) a.reveal\
(a.slotAt(r))\x0d\x0a \
       }\x0d\x0a      \
  function onFun\
ctionRequested(n\
ame, row) {     \
            // r\
ibbon of the hos\
t window / cell \
menu of the tabl\
e\x0d\x0a            i\
f (row < 0 || ro\
w >= columnConfi\
gModel.count) re\
turn\x0d\x0a          \
  columnEditorCo\
ntroller.selectO\
nly(row)\x0d\x0a      \
      if (name =\
== \x22split\x22) root\
.openSplit(row)\x0d\
\x0a            els\
e if (name === \x22\
conditional\x22) ro\
ot.openCondition\
al(row)\x0d\x0a       \
     else if (na\
me === \x22check\x22) \
root.openCheck(r\
ow)\x0d\x0a           \
 else if (name =\
== \x22lookup\x22) roo\
t.openLookup(row\
)\x0d\x0a            e\
lse if (name ===\
 \x22type\x22) root.op\
enType(row)\x0d\x0a   \
         else ro\
ot.openTransform\
(row, name)\x0d\x0a   \
     }\x0d\x0a    }\x0d\x0a\x0d\
\x0a    Rectangle {\
\x0d\x0a        id: si\
dePane\x0d\x0a        \
anchors { top: p\
arent.top; right\
: parent.right; \
bottom: parent.b\
ottom }\x0d\x0a       \
 width: tileLayo\
ut.sideExternal \
? 0 : (tileLayou\
t.sideCollapsed \
? root.collapsed\
Width : tileLayo\
ut.sideWidth)   \
// external: the\
 pane lives in t\
he host's flow d\
eck\x0d\x0a        vis\
ible: !tileLayou\
t.sideCollapsed \
&& !tileLayout.s\
ideExternal\x0d\x0a   \
     color: \x22#f7\
f9fb\x22\x0d\x0a        b\
order.color: \x22#c\
3ccd6\x22\x0d\x0a        \
radius: 6\x0d\x0a     \
   Text {       \
                \
               /\
/ collapse this \
side pane (\x22Eine\
 Kachel w\xc3\xa4hlen\x22\
 / Steps)\x0d\x0a     \
       id: sideC\
ollapseBtn\x0d\x0a    \
        anchors \
{ top: parent.to\
p; right: parent\
.right; topMargi\
n: 2; rightMargi\
n: 4 }\x0d\x0a        \
    text: \x22\xc2\xbb\x22  \
                \
          // \xc2\xbb\x0d\
\x0a            fon\
t.pixelSize: 13\x0d\
\x0a            col\
or: sideCollapse\
Area.containsMou\
se ? \x22#2c3e50\x22 :\
 \x22#9aa5b1\x22\x0d\x0a    \
        MouseAre\
a { id: sideColl\
apseArea; anchor\
s.margins: -4; a\
nchors.fill: par\
ent; hoverEnable\
d: true; cursorS\
hape: Qt.Pointin\
gHandCursor\x0d\x0a   \
                \
    onClicked: t\
ileLayout.sideCo\
llapsed = true }\
\x0d\x0a        }\x0d\x0a   \
     Flickable {\
\x0d\x0a            id\
: side\x0d\x0a        \
    anchors { to\
p: sideCollapseB\
tn.bottom; left:\
 parent.left; ri\
ght: parent.righ\
t; bottom: paren\
t.bottom; margin\
s: 8 }\x0d\x0a        \
    contentWidth\
: width\x0d\x0a       \
     contentHeig\
ht: sideCol.impl\
icitHeight\x0d\x0a    \
        clip: tr\
ue\x0d\x0a            \
boundsBehavior: \
Flickable.StopAt\
Bounds\x0d\x0a        \
    ScrollBar.ve\
rtical: ScrollBa\
r { }\x0d\x0a         \
   Column {\x0d\x0a   \
             id:\
 sideCol\x0d\x0a      \
          width:\
 side.width - 10\
\x0d\x0a              \
  spacing: 8\x0d\x0a  \
              Ru\
leInspector {\x0d\x0a \
                \
   width: parent\
.width\x0d\x0a        \
            row:\
 columnEditorCon\
troller.selected\
Row\x0d\x0a           \
         onChang\
eTypeRequested: \
function (r) { r\
oot.openType(r) \
}\x0d\x0a             \
   }\x0d\x0a          \
      Text {\x0d\x0a  \
                \
  visible: colum\
nEditorControlle\
r.selectionCount\
 >= 2 && !column\
EditorController\
.hasDraft\x0d\x0a     \
               t\
ext: columnEdito\
rController.sele\
ctionCount + \x22 K\
acheln gew\xc3\xa4hlt.\
 Kacheln gruppie\
ren (Strg+G) \xc3\xb6f\
fnet hier den Gr\
uppen-Dialog: Gr\
uppenname, optio\
nal verbundene S\
palte, optional \
Kopfzeile in Tab\
elle / Excel.\x22\x0d\x0a\
                \
    font.pixelSi\
ze: 11; color: \x22\
#52606d\x22; wrapMo\
de: Text.Wrap; w\
idth: parent.wid\
th\x0d\x0a            \
    }\x0d\x0a         \
       GroupPane\
l { width: paren\
t.width }\x0d\x0a     \
           Steps\
Panel { width: p\
arent.width; onE\
ditRequested: fu\
nction (step) { \
root.editStep(st\
ep) } }\x0d\x0a       \
     }\x0d\x0a        \
}\x0d\x0a    }\x0d\x0a\x0d\x0a    \
// --- collapsed\
 side pane: a th\
in strip with an\
 expand handle -\
----------------\
----------------\
----------------\
-------\x0d\x0a    Rec\
tangle {\x0d\x0a      \
  id: sideCollap\
sedStrip\x0d\x0a      \
  visible: tileL\
ayout.sideCollap\
sed && !tileLayo\
ut.sideExternal\x0d\
\x0a        anchors\
 { top: parent.t\
op; right: paren\
t.right; bottom:\
 parent.bottom }\
\x0d\x0a        width:\
 root.collapsedW\
idth\x0d\x0a        ra\
dius: 6\x0d\x0a       \
 color: sideExpa\
ndArea.containsM\
ouse ? \x22#eef2f7\x22\
 : \x22#f7f9fb\x22\x0d\x0a  \
      border.wid\
th: 1\x0d\x0a        b\
order.color: \x22#c\
3ccd6\x22\x0d\x0a        \
Text {\x0d\x0a        \
    anchors.cent\
erIn: parent\x0d\x0a  \
          rotati\
on: 90\x0d\x0a        \
    font.pixelSi\
ze: 10\x0d\x0a        \
    color: \x22#526\
06d\x22\x0d\x0a          \
  text: \x22\xc2\xab  Kac\
hel w\xc3\xa4hlen / Sc\
hritte\x22\x0d\x0a       \
 }\x0d\x0a        Mous\
eArea { id: side\
ExpandArea; anch\
ors.fill: parent\
; hoverEnabled: \
true; cursorShap\
e: Qt.PointingHa\
ndCursor\x0d\x0a      \
             onC\
licked: tileLayo\
ut.sideCollapsed\
 = false }\x0d\x0a    \
}\x0d\x0a\x0d\x0a    // --- \
draggable splitt\
er at the left e\
dge of the side \
pane; remembers \
the width (tileL\
ayout) ---------\
--------------\x0d\x0a\
    Rectangle {\x0d\
\x0a        id: sid\
eSplitter\x0d\x0a     \
   visible: !til\
eLayout.sideColl\
apsed && !tileLa\
yout.sideExterna\
l\x0d\x0a        width\
: 6\x0d\x0a        x: \
sidePane.x - wid\
th / 2\x0d\x0a        \
anchors { top: p\
arent.top; botto\
m: parent.bottom\
 }\x0d\x0a        colo\
r: sideSplitterA\
rea.containsMous\
e || sideSplitte\
rArea.pressed ? \
\x22#9fb4c7\x22 : \x22tra\
nsparent\x22\x0d\x0a     \
   MouseArea {\x0d\x0a\
            id: \
sideSplitterArea\
\x0d\x0a            an\
chors.fill: pare\
nt\x0d\x0a            \
anchors.margins:\
 -3\x0d\x0a           \
 hoverEnabled: t\
rue\x0d\x0a           \
 cursorShape: Qt\
.SizeHorCursor\x0d\x0a\
            prop\
erty real startX\
: 0\x0d\x0a           \
 property real s\
tartWidth: 0\x0d\x0a  \
          onPres\
sed: function (m\
) { startX = map\
ToItem(root, m.x\
, 0).x; startWid\
th = tileLayout.\
sideWidth }\x0d\x0a   \
         onPosit\
ionChanged: func\
tion (m) {\x0d\x0a    \
            if (\
!pressed) return\
\x0d\x0a              \
  var curX = map\
ToItem(root, m.x\
, 0).x\x0d\x0a        \
        tileLayo\
ut.sideWidth = s\
tartWidth + (sta\
rtX - curX)\x0d\x0a   \
         }\x0d\x0a    \
    }\x0d\x0a    }\x0d\x0a}\x0d\
\x0a\
\x00\x00\x1e\x1c\
/\
/ Check against \
a code list: a n\
ew calculated co\
lumn says OK or \
NOT IN LIST for \
every cell of th\
e tile.\x0d\x0a// The \
list comes from \
the project defi\
nitions (buildin\
g, system, funct\
ion, pipe class \
...), from the d\
istinct values o\
f another\x0d\x0a// ti\
le, or is typed \
/ pasted. Also u\
sed to change th\
e list of an exi\
sting step (edit\
Index >= 0).\x0d\x0aim\
port QtQuick\x0d\x0aim\
port QtQuick.Con\
trols\x0d\x0a\x0d\x0aPopup {\
\x0d\x0a    id: dlg\x0d\x0a \
   property int \
row: -1\x0d\x0a    pro\
perty int editIn\
dex: -1\x0d\x0a    pro\
perty var lists:\
 []             \
          // [{n\
ame, count}] rea\
dy-made lists\x0d\x0a \
   property var \
columns: []     \
                \
// [{key, label}\
] for \x22Werte der\
 Kachel\x22\x0d\x0a    pr\
operty var previ\
ew: ({ ok: false\
, error: \x22\x22, bad\
: 0, total: 0, e\
xamples: [] })\x0d\x0a\
    property str\
ing applyError: \
\x22\x22\x0d\x0a    property\
 string listName\
: \x22\x22\x0d\x0a\x0d\x0a    moda\
l: false\x0d\x0a    di\
m: false\x0d\x0a    fo\
cus: true\x0d\x0a    c\
losePolicy: Popu\
p.CloseOnEscape\x0d\
\x0a    parent: Ove\
rlay.overlay\x0d\x0a  \
  x: 0\x0d\x0a    y: p\
arent ? parent.h\
eight - 2 : 0\x0d\x0a \
   margins: 6\x0d\x0a \
   padding: 8\x0d\x0a \
   width: Math.m\
in(360, (Overlay\
.overlay ? Overl\
ay.overlay.width\
 : 360) - 12)\x0d\x0a \
   background: R\
ectangle { color\
: \x22#ffffff\x22; bor\
der.color: \x22#7f9\
bb5\x22; border.wid\
th: 1; radius: 5\
 }\x0d\x0a\x0d\x0a    functi\
on values() { re\
turn valuesArea.\
text.split(/[\x5cn,\
;]+/).map(functi\
on (t) { return \
t.trim() }).filt\
er(function (t) \
{ return t !== \x22\
\x22 }) }\x0d\x0a    func\
tion options() {\
 return { values\
: values(), list\
Name: listName, \
ignoreCase: !cas\
eCheck.checked, \
emptyOk: emptyCh\
eck.checked, bad\
Text: badField.t\
ext } }\x0d\x0a    fun\
ction refresh() \
{ if (row >= 0) \
preview = column\
EditorController\
.previewCheck(ro\
w, options()) }\x0d\
\x0a    function op\
enFor(r, stepInd\
ex) {\x0d\x0a        e\
ditIndex = stepI\
ndex === undefin\
ed ? -1 : stepIn\
dex\x0d\x0a        row\
 = r\x0d\x0a        li\
sts = columnEdit\
orController.cod\
eLists()\x0d\x0a      \
  columns = colu\
mnEditorControll\
er.columnChoices\
()\x0d\x0a        appl\
yError = \x22\x22\x0d\x0a   \
     valuesArea.\
text = \x22\x22; listN\
ame = \x22\x22; caseCh\
eck.checked = fa\
lse; emptyCheck.\
checked = true; \
badField.text = \
\x22NICHT IN LISTE\x22\
\x0d\x0a        if (ed\
itIndex >= 0) {\x0d\
\x0a            var\
 info = columnEd\
itorController.s\
tepInfo(editInde\
x)\x0d\x0a            \
row = info.row\x0d\x0a\
            valu\
esArea.text = (i\
nfo.options.valu\
es || []).join(\x22\
\x5cn\x22)\x0d\x0a          \
  listName = inf\
o.options.listNa\
me || \x22\x22\x0d\x0a      \
      caseCheck.\
checked = info.o\
ptions.ignoreCas\
e === false\x0d\x0a   \
         emptyCh\
eck.checked = in\
fo.options.empty\
Ok !== false\x0d\x0a  \
          badFie\
ld.text = info.o\
ptions.badText |\
| \x22NICHT IN LIST\
E\x22\x0d\x0a        }\x0d\x0a \
       refresh()\
\x0d\x0a        open()\
\x0d\x0a    }\x0d\x0a    fun\
ction useList(na\
me) { listName =\
 name; valuesAre\
a.text = columnE\
ditorController.\
codeListValues(n\
ame).join(\x22\x5cn\x22);\
 refresh() }\x0d\x0a  \
  function useTi\
le(i) {\x0d\x0a       \
 listName = \x22Wer\
te von \x22 + colum\
ns[i].label\x0d\x0a   \
     valuesArea.\
text = columnEdi\
torController.co\
lumnDistinctValu\
es(i).join(\x22\x5cn\x22)\
\x0d\x0a        refres\
h()\x0d\x0a    }\x0d\x0a\x0d\x0a  \
  contentItem: F\
lickable {\x0d\x0a    \
    clip: true\x0d\x0a\
        implicit\
Height: Math.min\
(body.implicitHe\
ight, 470)\x0d\x0a    \
    contentHeigh\
t: body.implicit\
Height\x0d\x0a        \
boundsBehavior: \
Flickable.StopAt\
Bounds\x0d\x0a        \
Column {\x0d\x0a      \
      id: body\x0d\x0a\
            widt\
h: parent.width\x0d\
\x0a            spa\
cing: 5\x0d\x0a       \
     Text { text\
: dlg.editIndex \
>= 0 ? \x22Schritt \
\xc3\xa4ndern: Gegen C\
odeliste pr\xc3\xbcfen\
\x22 : \x22Gegen Codel\
iste pr\xc3\xbcfen\x22; f\
ont.bold: true; \
font.pixelSize: \
12 }\x0d\x0a          \
  Text { text: \x22\
Spalte: \x22 + (col\
umns.length && r\
ow >= 0 && row <\
 columns.length \
? columns[row].l\
abel : \x22\x22); font\
.pixelSize: 10; \
color: \x22#52606d\x22\
; elide: Text.El\
ideRight; width:\
 parent.width }\x0d\
\x0a            Row\
 {\x0d\x0a            \
    spacing: 6\x0d\x0a\
                \
Text { text: \x22Li\
ste \xc3\xbcbernehmen\x22\
; font.pixelSize\
: 11; anchors.ve\
rticalCenter: pa\
rent.verticalCen\
ter; width: 70 }\
\x0d\x0a              \
  ComboBox {\x0d\x0a  \
                \
  id: fromProjec\
t\x0d\x0a             \
       model: [{\
 name: \x22aus Proj\
ektdefinitionen \
\xe2\x80\xa6\x22 }].concat(d\
lg.lists.map(fun\
ction (l) { retu\
rn { name: l.nam\
e + \x22  (\x22 + l.co\
unt + \x22)\x22, raw: \
l.name } }))\x0d\x0a  \
                \
  textRole: \x22nam\
e\x22; implicitWidt\
h: 250; implicit\
Height: 26; font\
.pixelSize: 11\x0d\x0a\
                \
    enabled: dlg\
.lists.length > \
0\x0d\x0a             \
       Accessibl\
e.name: \x22Liste a\
us den Projektde\
finitionen\x22\x0d\x0a   \
                \
 onActivated: if\
 (currentIndex >\
 0) dlg.useList(\
model[currentInd\
ex].raw)\x0d\x0a      \
          }\x0d\x0a   \
         }\x0d\x0a    \
        Text { v\
isible: dlg.list\
s.length === 0; \
text: \x22Hier sind\
 keine Projektde\
finitionen gelad\
en: Werte einer \
Kachel nehmen od\
er eintippen / e\
inf\xc3\xbcgen.\x22; font\
.pixelSize: 10; \
color: \x22#7b8794\x22\
; wrapMode: Text\
.Wrap; width: pa\
rent.width }\x0d\x0a  \
          Row {\x0d\
\x0a               \
 spacing: 6\x0d\x0a   \
             Tex\
t { text: \x22oder \
aus\x22; font.pixel\
Size: 11; anchor\
s.verticalCenter\
: parent.vertica\
lCenter; width: \
70 }\x0d\x0a          \
      ComboBox {\
\x0d\x0a              \
      model: [{ \
label: \x22Werte ei\
ner Kachel \xe2\x80\xa6\x22 \
}].concat(dlg.co\
lumns)\x0d\x0a        \
            text\
Role: \x22label\x22; i\
mplicitWidth: 25\
0; implicitHeigh\
t: 26; font.pixe\
lSize: 11\x0d\x0a     \
               A\
ccessible.name: \
\x22Liste aus den W\
erten einer Kach\
el\x22\x0d\x0a           \
         onActiv\
ated: if (curren\
tIndex > 0) dlg.\
useTile(currentI\
ndex - 1)\x0d\x0a     \
           }\x0d\x0a  \
          }\x0d\x0a   \
         Text { \
text: \x22Erlaubte \
Werte (einer je \
Zeile oder getre\
nnt durch , oder\
 ;)\x22; font.pixel\
Size: 10; color:\
 \x22#52606d\x22 }\x0d\x0a  \
          Scroll\
View {\x0d\x0a        \
        width: p\
arent.width; hei\
ght: 96\x0d\x0a       \
         TextAre\
a { id: valuesAr\
ea; font.pixelSi\
ze: 11; selectBy\
Mouse: true; wra\
pMode: TextArea.\
NoWrap; Accessib\
le.name: \x22Erlaub\
te Werte\x22; onTex\
tChanged: dlg.re\
fresh(); backgro\
und: Rectangle {\
 color: \x22#fbfcfd\
\x22; border.color:\
 \x22#c3ccd6\x22 } }\x0d\x0a\
            }\x0d\x0a \
           Row {\
\x0d\x0a              \
  spacing: 6\x0d\x0a  \
              Te\
xt { text: \x22Fals\
che Zellen erhal\
ten\x22; font.pixel\
Size: 11; anchor\
s.verticalCenter\
: parent.vertica\
lCenter }\x0d\x0a     \
           TextF\
ield { id: badFi\
eld; width: 150;\
 implicitHeight:\
 26; font.pixelS\
ize: 11; selectB\
yMouse: true; Ac\
cessible.name: \x22\
Text f\xc3\xbcr eine f\
alsche Zelle\x22; o\
nTextEdited: dlg\
.refresh() }\x0d\x0a  \
          }\x0d\x0a   \
         CheckBo\
x { id: emptyChe\
ck; text: \x22Leere\
 Zelle ist in Or\
dnung\x22; font.pix\
elSize: 11; chec\
ked: true; onTog\
gled: dlg.refres\
h() }\x0d\x0a         \
   CheckBox { id\
: caseCheck; tex\
t: \x22Gro\xc3\x9f-/Klein\
schreibung beach\
ten\x22; font.pixel\
Size: 11; onTogg\
led: dlg.refresh\
() }\x0d\x0a          \
  Text { visible\
: !!preview.erro\
r; text: preview\
.error || \x22\x22; fo\
nt.pixelSize: 10\
; color: \x22#b03a2\
e\x22; wrapMode: Te\
xt.Wrap; width: \
parent.width }\x0d\x0a\
            Text\
 {\x0d\x0a            \
    visible: !pr\
eview.error\x0d\x0a   \
             tex\
t: (preview.bad \
|| 0).toLocaleSt\
ring() + \x22 von \x22\
 + (preview.tota\
l || 0).toLocale\
String() + \x22 Vor\
schauzellen steh\
en nicht in der \
Liste\x22\x0d\x0a        \
              + \
((preview.exampl\
es || []).length\
 ? \x22:  \x22 + previ\
ew.examples.join\
(\x22, \x22) : \x22\x22)\x0d\x0a  \
              fo\
nt.pixelSize: 10\
; font.bold: tru\
e; color: previe\
w.bad ? \x22#b03a2e\
\x22 : \x22#1e6f3d\x22; w\
rapMode: Text.Wr\
ap; width: paren\
t.width\x0d\x0a       \
     }\x0d\x0a        \
    Text { visib\
le: dlg.applyErr\
or !== \x22\x22; text:\
 dlg.applyError;\
 font.pixelSize:\
 10; color: \x22#b0\
3a2e\x22; wrapMode:\
 Text.Wrap; widt\
h: parent.width \
}\x0d\x0a            R\
ow {\x0d\x0a          \
      spacing: 6\
\x0d\x0a              \
  Button {\x0d\x0a    \
                \
text: dlg.editIn\
dex >= 0 ? \x22\xc3\x84nd\
erung speichern\x22\
 : \x22Anwenden\x22; i\
mplicitHeight: 2\
6; font.pixelSiz\
e: 11\x0d\x0a         \
           enabl\
ed: !!preview.ok\
\x0d\x0a              \
      onClicked:\
 {\x0d\x0a            \
            dlg.\
applyError = dlg\
.editIndex >= 0 \
? columnEditorCo\
ntroller.editChe\
ckStep(dlg.editI\
ndex, dlg.option\
s())\x0d\x0a          \
                \
                \
                \
  : columnEditor\
Controller.apply\
Check(dlg.row, d\
lg.options())\x0d\x0a \
                \
       if (dlg.a\
pplyError === \x22\x22\
) dlg.close()\x0d\x0a \
                \
   }\x0d\x0a          \
      }\x0d\x0a       \
         Button \
{ text: \x22Abbrech\
en\x22; implicitHei\
ght: 26; font.pi\
xelSize: 11; onC\
licked: dlg.clos\
e() }\x0d\x0a         \
   }\x0d\x0a        }\x0d\
\x0a    }\x0d\x0a}\x0d\x0a\
\x00\x00\x08\x0a\
/\
/ Small \x22Text ei\
ngeben\x22 popover \
(rename output c\
olumn, short til\
e name, move to \
position). It op\
ens right below \
the tile it\x0d\x0a// \
belongs to (the \
grid sets `paren\
t` to the tile b\
efore `ask`), ha\
s no dimming and\
 closes with Ent\
er / Esc / click\
 outside.\x0d\x0aimpor\
t QtQuick\x0d\x0aimpor\
t QtQuick.Contro\
ls\x0d\x0a\x0d\x0aPopup {\x0d\x0a \
   id: dlg\x0d\x0a    \
property string \
label: \x22\x22\x0d\x0a    p\
roperty string i\
nitial: \x22\x22\x0d\x0a    \
property string \
title: \x22\x22\x0d\x0a    s\
ignal submitted(\
string value)\x0d\x0a\x0d\
\x0a    modal: fals\
e\x0d\x0a    dim: fals\
e\x0d\x0a    focus: tr\
ue\x0d\x0a    closePol\
icy: Popup.Close\
OnEscape | Popup\
.CloseOnPressOut\
side\x0d\x0a    parent\
: Overlay.overla\
y\x0d\x0a    x: 0\x0d\x0a   \
 y: parent ? par\
ent.height - 2 :\
 0\x0d\x0a    margins:\
 6\x0d\x0a    padding:\
 8\x0d\x0a    width: M\
ath.min(300, (Ov\
erlay.overlay ? \
Overlay.overlay.\
width : 300) - 1\
2)\x0d\x0a    backgrou\
nd: Rectangle { \
color: \x22#ffffff\x22\
; border.color: \
\x22#7f9bb5\x22; borde\
r.width: 1; radi\
us: 5 }\x0d\x0a\x0d\x0a    f\
unction ask(titl\
eText, labelText\
, value) {\x0d\x0a    \
    title = titl\
eText\x0d\x0a        l\
abel = labelText\
\x0d\x0a        initia\
l = value\x0d\x0a     \
   field.text = \
value\x0d\x0a        o\
pen()\x0d\x0a    }\x0d\x0a  \
  function accep\
t() { var v = fi\
eld.text; close(\
); submitted(v) \
}\x0d\x0a    onOpened:\
 { field.forceAc\
tiveFocus(); fie\
ld.selectAll() }\
\x0d\x0a\x0d\x0a    contentI\
tem: Column {\x0d\x0a \
       spacing: \
5\x0d\x0a        Text \
{ text: dlg.titl\
e; font.pixelSiz\
e: 12; font.bold\
: true; width: p\
arent.width; eli\
de: Text.ElideRi\
ght }\x0d\x0a        T\
ext { text: dlg.\
label; font.pixe\
lSize: 10; color\
: \x22#52606d\x22; wra\
pMode: Text.Wrap\
; width: parent.\
width }\x0d\x0a       \
 Row {\x0d\x0a        \
    spacing: 6\x0d\x0a\
            Text\
Field {\x0d\x0a       \
         id: fie\
ld\x0d\x0a            \
    width: dlg.w\
idth - dlg.paddi\
ng * 2 - 110\x0d\x0a  \
              im\
plicitHeight: 26\
; font.pixelSize\
: 11\x0d\x0a          \
      selectByMo\
use: true\x0d\x0a     \
           Acces\
sible.name: dlg.\
label\x0d\x0a         \
       onAccepte\
d: dlg.accept()\x0d\
\x0a            }\x0d\x0a\
            Butt\
on { text: \x22OK\x22;\
 implicitHeight:\
 26; implicitWid\
th: 48; font.pix\
elSize: 11; onCl\
icked: dlg.accep\
t() }\x0d\x0a         \
   Button { text\
: \x22Abbrechen\x22; i\
mplicitHeight: 2\
6; implicitWidth\
: 52; font.pixel\
Size: 11; onClic\
ked: dlg.close()\
 }\x0d\x0a        }\x0d\x0a \
   }\x0d\x0a}\x0d\x0a\
\x00\x00\x0e\x09\
/\
/ Properties of \
the ACTIVE tile \
(D9): names, sou\
rce / output typ\
e, detection, sa\
mple, null count\
, export / visib\
ility,\x0d\x0a// appli\
ed steps. The ty\
pe is changed th\
rough the \x22Spalt\
entyp \xc3\xa4ndern\x22 d\
ialog (explicit \
convert step).\x0d\x0a\
import QtQuick\x0d\x0a\
import QtQuick.C\
ontrols\x0d\x0a\x0d\x0aColum\
n {\x0d\x0a    id: ins\
pector\x0d\x0a    prop\
erty int row: -1\
\x0d\x0a    property v\
ar info: ({})\x0d\x0a \
   signal change\
TypeRequested(in\
t row)\x0d\x0a\x0d\x0a    sp\
acing: 4\x0d\x0a    fu\
nction refresh()\
 { info = row >=\
 0 ? columnEdito\
rController.insp\
ect(row) : ({}) \
}\x0d\x0a    onRowChan\
ged: refresh()\x0d\x0a\
    Connections \
{\x0d\x0a        targe\
t: columnEditorC\
ontroller\x0d\x0a     \
   function onSe\
lectedChanged() \
{ inspector.refr\
esh() }\x0d\x0a       \
 function onUndo\
Changed() { insp\
ector.refresh() \
}\x0d\x0a    }\x0d\x0a\x0d\x0a    \
component Prop: \
Row {\x0d\x0a        p\
roperty string n\
ame: \x22\x22\x0d\x0a       \
 property string\
 value: \x22\x22\x0d\x0a    \
    spacing: 6\x0d\x0a\
        visible:\
 value !== \x22\x22\x0d\x0a \
       Text { te\
xt: name; font.p\
ixelSize: 11; co\
lor: \x22#7b8794\x22; \
width: 92; wrapM\
ode: Text.Wrap }\
\x0d\x0a        Text {\
 text: value; fo\
nt.pixelSize: 11\
; color: \x22#1f293\
3\x22; width: inspe\
ctor.width - 100\
; wrapMode: Text\
.Wrap }\x0d\x0a    }\x0d\x0a\
\x0d\x0a    Text {\x0d\x0a  \
      text: insp\
ector.row < 0 ? \
\x22Eine Kachel w\xc3\xa4\
hlen\x22 : \x22Aktive \
Kachel\x22\x0d\x0a       \
 font.bold: true\
; font.pixelSize\
: 13; color: \x22#1\
f5fa8\x22\x0d\x0a    }\x0d\x0a \
   Prop { name: \
\x22Quellspalte\x22; v\
alue: info.sourc\
eName || \x22\x22 }\x0d\x0a \
   Prop { name: \
\x22Ausgabespalte\x22;\
 value: info.out\
putName || \x22\x22 }\x0d\
\x0a    Prop { name\
: \x22Kurzname der \
Kachel\x22; value: \
info.shortName |\
| \x22\x22 }\x0d\x0a    Prop\
 { name: \x22Quellt\
yp\x22; value: info\
.sourceTypeName \
|| \x22\x22 }\x0d\x0a    Row\
 {\x0d\x0a        visi\
ble: inspector.r\
ow >= 0 && !!inf\
o.outputTypeName\
\x0d\x0a        spacin\
g: 6\x0d\x0a        Te\
xt { text: \x22Ausg\
abetyp\x22; font.pi\
xelSize: 11; col\
or: \x22#7b8794\x22; w\
idth: 92; anchor\
s.verticalCenter\
: parent.vertica\
lCenter }\x0d\x0a     \
   Text { text: \
info.outputTypeN\
ame || \x22\x22; font.\
pixelSize: 11; f\
ont.bold: true; \
anchors.vertical\
Center: parent.v\
erticalCenter }\x0d\
\x0a        Button \
{\x0d\x0a            t\
ext: \x22Typ \xc3\xa4nder\
n \xe2\x80\xa6\x22\x0d\x0a        \
    implicitHeig\
ht: 24\x0d\x0a        \
    font.pixelSi\
ze: 11\x0d\x0a        \
    Accessible.n\
ame: \x22Spaltentyp\
 \xc3\xa4ndern\x22\x0d\x0a     \
       onClicked\
: inspector.chan\
geTypeRequested(\
inspector.row)\x0d\x0a\
        }\x0d\x0a    }\
\x0d\x0a    Prop { nam\
e: \x22Erkannt\x22; va\
lue: info.detect\
ed ? info.detect\
ed + \x22 \xc2\xb7 \x22 + (i\
nfo.confidence |\
| \x22\x22) : \x22\x22 }\x0d\x0a  \
  Prop { name: \x22\
Erkennung durch\x22\
; value: info.so\
urce || \x22\x22 }\x0d\x0a  \
  Prop { name: \x22\
Vorschlag\x22; valu\
e: info.suggeste\
d ? info.suggest\
ed + \x22  (ung\xc3\xbclt\
ig: \x22 + (info.in\
valid || 0) + \x22 \
von \x22 + (info.sa\
mples || 0) + \x22)\
\x22 : \x22\x22 }\x0d\x0a    Pr\
op { name: \x22Beis\
pielwert\x22; value\
: info.sampleVal\
ue || \x22\x22 }\x0d\x0a    \
Prop { name: \x22Le\
ere Zellen\x22; val\
ue: info.nullCou\
nt === undefined\
 ? \x22\x22 : String(i\
nfo.nullCount) }\
\x0d\x0a    Prop { nam\
e: \x22Status\x22; val\
ue: inspector.ro\
w < 0 ? \x22\x22 : (in\
fo.calculated ? \
\x22Berechnet\x22 : \x22O\
riginal (Quelle)\
\x22) }\x0d\x0a    CheckB\
ox {\x0d\x0a        vi\
sible: inspector\
.row >= 0\x0d\x0a     \
   text: \x22Export\
ieren\x22\x0d\x0a        \
checked: info.in\
Export !== false\
\x0d\x0a        font.p\
ixelSize: 11\x0d\x0a  \
      Accessible\
.name: \x22Exportie\
ren\x22\x0d\x0a        on\
Toggled: columnE\
ditorController.\
toggleExport(ins\
pector.row)\x0d\x0a   \
 }\x0d\x0a    CheckBox\
 {\x0d\x0a        visi\
ble: inspector.r\
ow >= 0\x0d\x0a       \
 text: \x22Im Edito\
r sichtbar\x22\x0d\x0a   \
     checked: in\
fo.visible !== f\
alse\x0d\x0a        fo\
nt.pixelSize: 11\
\x0d\x0a        Access\
ible.name: \x22Im E\
ditor sichtbar\x22\x0d\
\x0a        onToggl\
ed: columnEditor\
Controller.toggl\
eHidden(inspecto\
r.row)\x0d\x0a    }\x0d\x0a \
   Text { visibl\
e: (info.steps |\
| []).length > 0\
; text: \x22Angewen\
dete Schritte\x22; \
font.pixelSize: \
11; font.bold: t\
rue }\x0d\x0a    Repea\
ter {\x0d\x0a        m\
odel: info.steps\
 || []\x0d\x0a        \
delegate: Text {\
 text: \x22\xe2\x80\xa2 \x22 + \
modelData; font.\
pixelSize: 11; w\
rapMode: Text.Wr\
ap; width: inspe\
ctor.width }\x0d\x0a  \
  }\x0d\x0a}\x0d\x0a\
\x00\x00\x1a\x8a\
/\
/ Split dialog: \
one column becom\
es several calcu\
lated columns - \
the modes of Pow\
er Query's \x22Spal\
te teilen\x22: by a\
 separator, by n\
umber of\x0d\x0a// cha\
racters, by posi\
tions, by length\
s (3,2,3) or at \
a change of char\
acter type (lowe\
r->UPPER, UPPER-\
>lower, digit->n\
on-digit, non-di\
git->digit).\x0d\x0a//\
 The preview sho\
ws the parts of \
the first cells;\
 \x22Anwenden\x22 crea\
tes the new tile\
s right behind t\
he original (one\
 undo step).\x0d\x0aim\
port QtQuick\x0d\x0aim\
port QtQuick.Con\
trols\x0d\x0a\x0d\x0aPopup {\
\x0d\x0a    id: dlg\x0d\x0a \
   property int \
row: -1\x0d\x0a    pro\
perty var previe\
w: ({ ok: false,\
 rows: [], error\
: \x22\x22, parts: 0 }\
)\x0d\x0a    property \
string applyErro\
r: \x22\x22\x0d\x0a\x0d\x0a    mod\
al: false\x0d\x0a    d\
im: false\x0d\x0a    f\
ocus: true\x0d\x0a    \
closePolicy: Pop\
up.CloseOnEscape\
 | Popup.CloseOn\
PressOutside\x0d\x0a  \
  parent: Overla\
y.overlay\x0d\x0a    x\
: 0\x0d\x0a    y: pare\
nt ? parent.heig\
ht - 2 : 0\x0d\x0a    \
margins: 6\x0d\x0a    \
padding: 8\x0d\x0a    \
width: Math.min(\
340, (Overlay.ov\
erlay ? Overlay.\
overlay.width : \
340) - 12)\x0d\x0a    \
background: Rect\
angle { color: \x22\
#ffffff\x22; border\
.color: \x22#7f9bb5\
\x22; border.width:\
 1; radius: 5 }\x0d\
\x0a\x0d\x0a    function \
options() {\x0d\x0a   \
     return { mo\
de: modeCombo.cu\
rrentValue, find\
: sepField.text,\
 parts: parseInt\
(partsField.text\
) || 0,\x0d\x0a       \
          length\
s: lenField.text\
, size: parseInt\
(sizeField.text)\
 || 0, positions\
: posField.text,\
 replaceOriginal\
: origCheck.chec\
ked }\x0d\x0a    }\x0d\x0a  \
  function refre\
sh() { if (row >\
= 0) preview = c\
olumnEditorContr\
oller.previewSpl\
it(row, options(\
)) }\x0d\x0a    functi\
on openFor(r) {\x0d\
\x0a        row = r\
\x0d\x0a        applyE\
rror = \x22\x22\x0d\x0a     \
   modeCombo.cur\
rentIndex = 0; s\
epField.text = \x22\
\x22; partsField.te\
xt = \x22\x22; lenFiel\
d.text = \x22\x22; siz\
eField.text = \x22\x22\
; posField.text \
= \x22\x22; origCheck.\
checked = true\x0d\x0a\
        refresh(\
)\x0d\x0a        open(\
)\x0d\x0a    }\x0d\x0a    on\
Opened: sepField\
.forceActiveFocu\
s()\x0d\x0a\x0d\x0a    conte\
ntItem: Column {\
\x0d\x0a        spacin\
g: 5\x0d\x0a        Te\
xt { text: \x22Spal\
te teilen\x22; font\
.bold: true; fon\
t.pixelSize: 12 \
}\x0d\x0a        Text \
{ text: \x22Spalte:\
 \x22 + (preview.la\
bel || \x22\x22); font\
.pixelSize: 10; \
color: \x22#52606d\x22\
; elide: Text.El\
ideRight; width:\
 parent.width }\x0d\
\x0a        Row {\x0d\x0a\
            spac\
ing: 6\x0d\x0a        \
    Text { text:\
 \x22Teilen nach\x22; \
font.pixelSize: \
11; anchors.vert\
icalCenter: pare\
nt.verticalCente\
r; width: 78 }\x0d\x0a\
            Comb\
oBox {\x0d\x0a        \
        id: mode\
Combo\x0d\x0a         \
       model: [{\
 text: \x22ein Tren\
nzeichen\x22, value\
: \x22delimiter\x22 },\
 { text: \x22Anzahl\
 Zeichen (alle N\
)\x22, value: \x22coun\
t\x22 },\x0d\x0a         \
               {\
 text: \x22Position\
en (0,3,5)\x22, val\
ue: \x22positions\x22 \
}, { text: \x22fest\
e L\xc3\xa4ngen (3,2,3\
)\x22, value: \x22fixe\
d\x22 },\x0d\x0a         \
               {\
 text: \x22klein zu\
 GROSS\x22, value: \
\x22lower_upper\x22 },\
 { text: \x22GROSS \
zu klein\x22, value\
: \x22upper_lower\x22 \
},\x0d\x0a            \
            { te\
xt: \x22Ziffer zu N\
icht-Ziffer\x22, va\
lue: \x22digit_nond\
igit\x22 }, { text:\
 \x22Nicht-Ziffer z\
u Ziffer\x22, value\
: \x22nondigit_digi\
t\x22 }]\x0d\x0a         \
       textRole:\
 \x22text\x22; valueRo\
le: \x22value\x22\x0d\x0a   \
             imp\
licitWidth: 220;\
 implicitHeight:\
 26; font.pixelS\
ize: 11\x0d\x0a       \
         Accessi\
ble.name: \x22Art d\
er Teilung\x22\x0d\x0a   \
             onA\
ctivated: dlg.re\
fresh()\x0d\x0a       \
     }\x0d\x0a        \
}\x0d\x0a        Row {\
\x0d\x0a            vi\
sible: modeCombo\
.currentValue ==\
= \x22delimiter\x22; s\
pacing: 6\x0d\x0a     \
       Text { te\
xt: \x22Trennzeiche\
n\x22; font.pixelSi\
ze: 11; anchors.\
verticalCenter: \
parent.verticalC\
enter; width: 78\
 }\x0d\x0a            \
TextField { id: \
sepField; width:\
 60; implicitHei\
ght: 26; font.pi\
xelSize: 11; sel\
ectByMouse: true\
; Accessible.nam\
e: \x22Trennzeichen\
\x22; onTextEdited:\
 dlg.refresh() }\
\x0d\x0a            Te\
xt { text: \x22Teil\
e\x22; font.pixelSi\
ze: 11; anchors.\
verticalCenter: \
parent.verticalC\
enter }\x0d\x0a       \
     TextField {\
 id: partsField;\
 width: 50; impl\
icitHeight: 26; \
font.pixelSize: \
11; selectByMous\
e: true; placeho\
lderText: \x22auto\x22\
; inputMethodHin\
ts: Qt.ImhDigits\
Only; Accessible\
.name: \x22Anzahl T\
eile\x22; onTextEdi\
ted: dlg.refresh\
() }\x0d\x0a        }\x0d\
\x0a        Row {\x0d\x0a\
            visi\
ble: modeCombo.c\
urrentValue === \
\x22count\x22; spacing\
: 6\x0d\x0a           \
 Text { text: \x22Z\
eichen\x22; font.pi\
xelSize: 11; anc\
hors.verticalCen\
ter: parent.vert\
icalCenter; widt\
h: 78 }\x0d\x0a       \
     TextField {\
 id: sizeField; \
width: 60; impli\
citHeight: 26; f\
ont.pixelSize: 1\
1; selectByMouse\
: true; placehol\
derText: \x22N\x22; in\
putMethodHints: \
Qt.ImhDigitsOnly\
; Accessible.nam\
e: \x22Zeichen je T\
eil\x22; onTextEdit\
ed: dlg.refresh(\
) }\x0d\x0a           \
 Text { text: \x22j\
e Teil, wiederho\
lt\x22; font.pixelS\
ize: 10; color: \
\x22#52606d\x22; ancho\
rs.verticalCente\
r: parent.vertic\
alCenter }\x0d\x0a    \
    }\x0d\x0a        R\
ow {\x0d\x0a          \
  visible: modeC\
ombo.currentValu\
e === \x22positions\
\x22; spacing: 6\x0d\x0a \
           Text \
{ text: \x22Positio\
nen\x22; font.pixel\
Size: 11; anchor\
s.verticalCenter\
: parent.vertica\
lCenter; width: \
78 }\x0d\x0a          \
  TextField { id\
: posField; widt\
h: 220; implicit\
Height: 26; font\
.pixelSize: 11; \
selectByMouse: t\
rue; placeholder\
Text: \x22Startposi\
tionen ab 0, z. \
B. 0,3,5\x22; Acces\
sible.name: \x22Sta\
rtpositionen der\
 Teile\x22; onTextE\
dited: dlg.refre\
sh() }\x0d\x0a        \
}\x0d\x0a        Row {\
\x0d\x0a            vi\
sible: modeCombo\
.currentValue ==\
= \x22fixed\x22; spaci\
ng: 6\x0d\x0a         \
   Text { text: \
\x22L\xc3\xa4ngen\x22; font.\
pixelSize: 11; a\
nchors.verticalC\
enter: parent.ve\
rticalCenter; wi\
dth: 78 }\x0d\x0a     \
       TextField\
 { id: lenField;\
 width: 220; imp\
licitHeight: 26;\
 font.pixelSize:\
 11; selectByMou\
se: true; placeh\
olderText: \x22e.g.\
 3,2,3\x22; Accessi\
ble.name: \x22L\xc3\xa4ng\
en der Teile\x22; o\
nTextEdited: dlg\
.refresh() }\x0d\x0a  \
      }\x0d\x0a       \
 CheckBox { id: \
origCheck; text:\
 \x22Originalspalte\
 ausblenden und \
nicht exportiere\
n\x22; font.pixelSi\
ze: 11; checked:\
 true }\x0d\x0a       \
 Text {\x0d\x0a       \
     visible: !!\
preview.error; t\
ext: preview.err\
or || \x22\x22; font.p\
ixelSize: 10; co\
lor: \x22#b03a2e\x22; \
wrapMode: Text.W\
rap; width: pare\
nt.width\x0d\x0a      \
  }\x0d\x0a        Tex\
t {\x0d\x0a           \
 visible: !previ\
ew.error && prev\
iew.parts > 0\x0d\x0a \
           text:\
 preview.parts +\
 \x22 neue Spalten,\
 erste Zellen:\x22;\
 font.pixelSize:\
 10; font.bold: \
true; color: \x22#3\
4495e\x22\x0d\x0a        \
}\x0d\x0a        Repea\
ter {\x0d\x0a         \
   model: (previ\
ew.rows || []).s\
lice(0, 4)\x0d\x0a    \
        delegate\
: Column {\x0d\x0a    \
            widt\
h: dlg.available\
Width\x0d\x0a         \
       Text { te\
xt: modelData.be\
fore; font.pixel\
Size: 10; elide:\
 Text.ElideRight\
; width: parent.\
width }\x0d\x0a       \
         Text { \
text: \x22\xe2\x86\x92 \x22 + m\
odelData.after; \
font.pixelSize: \
10; color: \x22#1e6\
f3d\x22; elide: Tex\
t.ElideRight; wi\
dth: parent.widt\
h }\x0d\x0a           \
 }\x0d\x0a        }\x0d\x0a \
       Text { vi\
sible: dlg.apply\
Error !== \x22\x22; te\
xt: dlg.applyErr\
or; font.pixelSi\
ze: 10; color: \x22\
#b03a2e\x22; wrapMo\
de: Text.Wrap; w\
idth: parent.wid\
th }\x0d\x0a        Ro\
w {\x0d\x0a           \
 spacing: 6\x0d\x0a   \
         Button \
{\x0d\x0a             \
   text: \x22Anwend\
en\x22; implicitHei\
ght: 26; font.pi\
xelSize: 11\x0d\x0a   \
             ena\
bled: !!preview.\
ok\x0d\x0a            \
    Accessible.n\
ame: \x22Teilen anw\
enden\x22\x0d\x0a        \
        onClicke\
d: { dlg.applyEr\
ror = columnEdit\
orController.app\
lySplit(dlg.row,\
 dlg.options());\
 if (dlg.applyEr\
ror === \x22\x22) dlg.\
close() }\x0d\x0a     \
       }\x0d\x0a      \
      Button { t\
ext: \x22Abbrechen\x22\
; implicitHeight\
: 26; font.pixel\
Size: 11; onClic\
ked: dlg.close()\
 }\x0d\x0a        }\x0d\x0a \
   }\x0d\x0a}\x0d\x0a\
\x00\x00\x00\xdd\
/\
/ Thin insertion\
 marker next to \
a tile while ano\
ther tile is dra\
gged over it.\x0d\x0ai\
mport QtQuick\x0d\x0a\x0d\
\x0aRectangle {\x0d\x0a  \
  property bool \
active: false\x0d\x0a \
   width: 3\x0d\x0a   \
 radius: 1.5\x0d\x0a  \
  color: \x22#2b6cb\
0\x22\x0d\x0a    visible:\
 active\x0d\x0a}\x0d\x0a\
\x00\x00\x1c\xc4\
/\
/ Add columns fr\
om another list:\
 look a tile's v\
alue up in a col\
umn of another E\
xcel / CSV file \
and bring column\
s over.\x0d\x0a// The \
first matching r\
ow of the list w\
ins; a value tha\
t is not found g\
ets the \x22nicht g\
efunden\x22 text. T\
he other file is\
 only read.\x0d\x0aimp\
ort QtQuick\x0d\x0aimp\
ort QtQuick.Cont\
rols\x0d\x0aimport QtQ\
uick.Dialogs\x0d\x0a\x0d\x0a\
Popup {\x0d\x0a    id:\
 dlg\x0d\x0a    proper\
ty int row: -1\x0d\x0a\
    property var\
 sheets: []\x0d\x0a   \
 property var he\
aders: []\x0d\x0a    p\
roperty var prev\
iew: ({ ok: fals\
e, error: \x22\x22, ro\
ws: [], found: 0\
, total: 0 })\x0d\x0a \
   property stri\
ng applyError: \x22\
\x22\x0d\x0a    property \
string fileError\
: \x22\x22\x0d\x0a\x0d\x0a    moda\
l: false\x0d\x0a    di\
m: false\x0d\x0a    fo\
cus: true\x0d\x0a    c\
losePolicy: Popu\
p.CloseOnEscape\x0d\
\x0a    parent: Ove\
rlay.overlay\x0d\x0a  \
  x: 0\x0d\x0a    y: p\
arent ? parent.h\
eight - 2 : 0\x0d\x0a \
   margins: 6\x0d\x0a \
   padding: 8\x0d\x0a \
   width: Math.m\
in(380, (Overlay\
.overlay ? Overl\
ay.overlay.width\
 : 380) - 12)\x0d\x0a \
   background: R\
ectangle { color\
: \x22#ffffff\x22; bor\
der.color: \x22#7f9\
bb5\x22; border.wid\
th: 1; radius: 5\
 }\x0d\x0a\x0d\x0a    functi\
on takeLabels() \
{\x0d\x0a        var o\
ut = []\x0d\x0a       \
 for (var i = 0;\
 i < takeRepeate\
r.count; i++) { \
var it = takeRep\
eater.itemAt(i);\
 if (it && it.ch\
ecked) out.push(\
dlg.headers[i]) \
}\x0d\x0a        retur\
n out\x0d\x0a    }\x0d\x0a  \
  function optio\
ns() {\x0d\x0a        \
return { file: f\
ileField.text, s\
heet: sheetBox.c\
urrentText, matc\
hLabel: matchBox\
.currentText, ta\
keLabels: takeLa\
bels(),\x0d\x0a       \
          matchC\
ase: caseCheck.c\
hecked, missingT\
ext: missingFiel\
d.text }\x0d\x0a    }\x0d\
\x0a    function re\
fresh() {\x0d\x0a     \
   if (row >= 0 \
&& headers.lengt\
h > 0 && takeLab\
els().length > 0\
) preview = colu\
mnEditorControll\
er.previewLookup\
(row, options())\
\x0d\x0a        else p\
review = { ok: f\
alse, error: hea\
ders.length ? \x22Z\
u \xc3\xbcbernehmende \
Spalte(n) anhake\
n.\x22 : \x22\x22, rows: \
[], found: 0, to\
tal: 0 }\x0d\x0a    }\x0d\
\x0a    function lo\
adFile() {\x0d\x0a    \
    fileError = \
\x22\x22; sheets = [];\
 headers = []\x0d\x0a \
       var r = c\
olumnEditorContr\
oller.lookupShee\
ts(fileField.tex\
t)\x0d\x0a        if (\
!r.ok) { fileErr\
or = r.error; re\
fresh(); return \
}\x0d\x0a        sheet\
s = r.sheets\x0d\x0a  \
      sheetBox.c\
urrentIndex = 0\x0d\
\x0a        loadShe\
et()\x0d\x0a    }\x0d\x0a   \
 function loadSh\
eet() {\x0d\x0a       \
 var r = columnE\
ditorController.\
lookupHeaders(fi\
leField.text, sh\
eetBox.currentTe\
xt)\x0d\x0a        fil\
eError = r.ok ? \
\x22\x22 : r.error\x0d\x0a  \
      headers = \
r.ok ? r.headers\
 : []\x0d\x0a        m\
atchBox.currentI\
ndex = 0\x0d\x0a      \
  refresh()\x0d\x0a   \
 }\x0d\x0a    function\
 openFor(r) {\x0d\x0a \
       row = r\x0d\x0a\
        applyErr\
or = \x22\x22; fileErr\
or = \x22\x22; sheets \
= []; headers = \
[]\x0d\x0a        file\
Field.text = \x22\x22;\
 missingField.te\
xt = \x22\x22; caseChe\
ck.checked = fal\
se\x0d\x0a        refr\
esh()\x0d\x0a        o\
pen()\x0d\x0a    }\x0d\x0a\x0d\x0a\
    FileDialog {\
\x0d\x0a        id: pi\
cker\x0d\x0a        ti\
tle: \x22Andere Lis\
te w\xc3\xa4hlen\x22\x0d\x0a   \
     nameFilters\
: [\x22Listen (*.xl\
sx *.xlsm *.csv)\
\x22, \x22Alle Dateien\
 (*)\x22]\x0d\x0a        \
onAccepted: { fi\
leField.text = s\
electedFile.toSt\
ring().replace(/\
^file:\x5c/\x5c/\x5c//, \x22\
\x22); dlg.loadFile\
() }\x0d\x0a    }\x0d\x0a\x0d\x0a \
   contentItem: \
Flickable {\x0d\x0a   \
     clip: true\x0d\
\x0a        implici\
tHeight: Math.mi\
n(body.implicitH\
eight, 470)\x0d\x0a   \
     contentHeig\
ht: body.implici\
tHeight\x0d\x0a       \
 boundsBehavior:\
 Flickable.StopA\
tBounds\x0d\x0a       \
 Column {\x0d\x0a     \
       id: body\x0d\
\x0a            wid\
th: parent.width\
\x0d\x0a            sp\
acing: 5\x0d\x0a      \
      Text { tex\
t: \x22Spalten aus \
einer anderen Li\
ste\x22; font.bold:\
 true; font.pixe\
lSize: 12 }\x0d\x0a   \
         Row {\x0d\x0a\
                \
spacing: 6\x0d\x0a    \
            Text\
 { text: \x22Listen\
datei\x22; font.pix\
elSize: 11; anch\
ors.verticalCent\
er: parent.verti\
calCenter; width\
: 70 }\x0d\x0a        \
        TextFiel\
d { id: fileFiel\
d; width: 215; i\
mplicitHeight: 2\
6; font.pixelSiz\
e: 11; selectByM\
ouse: true; plac\
eholderText: \x22Pf\
ad zu .xlsx / .c\
sv\x22; Accessible.\
name: \x22Listendat\
ei\x22; onEditingFi\
nished: dlg.load\
File() }\x0d\x0a      \
          Button\
 { text: \x22\xe2\x80\xa6\x22; \
implicitHeight: \
26; implicitWidt\
h: 30; Accessibl\
e.name: \x22Listend\
atei suchen\x22; on\
Clicked: picker.\
open() }\x0d\x0a      \
      }\x0d\x0a       \
     Text { visi\
ble: dlg.fileErr\
or !== \x22\x22; text:\
 dlg.fileError; \
font.pixelSize: \
10; color: \x22#b03\
a2e\x22; wrapMode: \
Text.Wrap; width\
: parent.width }\
\x0d\x0a            Ro\
w {\x0d\x0a           \
     visible: dl\
g.sheets.length \
> 1; spacing: 6\x0d\
\x0a               \
 Text { text: \x22B\
latt\x22; font.pixe\
lSize: 11; ancho\
rs.verticalCente\
r: parent.vertic\
alCenter; width:\
 70 }\x0d\x0a         \
       ComboBox \
{ id: sheetBox; \
model: dlg.sheet\
s; implicitWidth\
: 250; implicitH\
eight: 26; font.\
pixelSize: 11; A\
ccessible.name: \
\x22Blatt der Liste\
\x22; onActivated: \
dlg.loadSheet() \
}\x0d\x0a            }\
\x0d\x0a            Ro\
w {\x0d\x0a           \
     visible: dl\
g.headers.length\
 > 0; spacing: 6\
\x0d\x0a              \
  Text { text: \x22\
Abgleichen mit\x22;\
 font.pixelSize:\
 11; anchors.ver\
ticalCenter: par\
ent.verticalCent\
er; width: 70 }\x0d\
\x0a               \
 ComboBox { id: \
matchBox; model:\
 dlg.headers; im\
plicitWidth: 250\
; implicitHeight\
: 26; font.pixel\
Size: 11; Access\
ible.name: \x22Spal\
te der Liste mit\
 denselben Werte\
n\x22; onActivated:\
 dlg.refresh() }\
\x0d\x0a            }\x0d\
\x0a            Tex\
t { visible: dlg\
.headers.length \
> 0; text: \x22\xc3\x9cbe\
rnehmen:\x22; font.\
pixelSize: 10; c\
olor: \x22#52606d\x22 \
}\x0d\x0a            R\
epeater {\x0d\x0a     \
           id: t\
akeRepeater\x0d\x0a   \
             mod\
el: dlg.headers\x0d\
\x0a               \
 delegate: Check\
Box { text: mode\
lData; font.pixe\
lSize: 11; impli\
citHeight: 24; o\
nToggled: dlg.re\
fresh() }\x0d\x0a     \
       }\x0d\x0a      \
      Row {\x0d\x0a   \
             vis\
ible: dlg.header\
s.length > 0; sp\
acing: 6\x0d\x0a      \
          Text {\
 text: \x22Nicht ge\
funden\x22; font.pi\
xelSize: 11; anc\
hors.verticalCen\
ter: parent.vert\
icalCenter; widt\
h: 70 }\x0d\x0a       \
         TextFie\
ld { id: missing\
Field; width: 15\
0; implicitHeigh\
t: 26; font.pixe\
lSize: 11; selec\
tByMouse: true; \
placeholderText:\
 \x22(leer)\x22; Acces\
sible.name: \x22Tex\
t, wenn ein Wert\
 fehlt\x22; onTextE\
dited: dlg.refre\
sh() }\x0d\x0a        \
    }\x0d\x0a         \
   CheckBox { id\
: caseCheck; vis\
ible: dlg.header\
s.length > 0; te\
xt: \x22Gro\xc3\x9f-/Klei\
nschreibung beac\
hten\x22; font.pixe\
lSize: 11; onTog\
gled: dlg.refres\
h() }\x0d\x0a         \
   Text { visibl\
e: !!preview.err\
or; text: previe\
w.error || \x22\x22; f\
ont.pixelSize: 1\
0; color: \x22#b03a\
2e\x22; wrapMode: T\
ext.Wrap; width:\
 parent.width }\x0d\
\x0a            Tex\
t {\x0d\x0a           \
     visible: !p\
review.error && \
preview.total > \
0\x0d\x0a             \
   text: (previe\
w.found || 0).to\
LocaleString() +\
 \x22 von \x22 + (prev\
iew.total || 0).\
toLocaleString()\
 + \x22 Vorschauzel\
len stehen in de\
r Liste\x22\x0d\x0a      \
          font.p\
ixelSize: 10; fo\
nt.bold: true; c\
olor: \x22#34495e\x22;\
 wrapMode: Text.\
Wrap; width: par\
ent.width\x0d\x0a     \
       }\x0d\x0a      \
      Repeater {\
\x0d\x0a              \
  model: (previe\
w.rows || []).sl\
ice(0, 4)\x0d\x0a     \
           deleg\
ate: Row {\x0d\x0a    \
                \
spacing: 6\x0d\x0a    \
                \
Text { text: mod\
elData.before; f\
ont.pixelSize: 1\
0; width: 150; e\
lide: Text.Elide\
Right }\x0d\x0a       \
             Tex\
t { text: \x22\xe2\x86\x92\x22;\
 font.pixelSize:\
 10 }\x0d\x0a         \
           Text \
{ text: modelDat\
a.after === \x22\x22 ?\
 \x22(leer)\x22 : mode\
lData.after; fon\
t.pixelSize: 10;\
 width: 150; eli\
de: Text.ElideRi\
ght }\x0d\x0a         \
       }\x0d\x0a      \
      }\x0d\x0a       \
     Text { visi\
ble: dlg.applyEr\
ror !== \x22\x22; text\
: dlg.applyError\
; font.pixelSize\
: 10; color: \x22#b\
03a2e\x22; wrapMode\
: Text.Wrap; wid\
th: parent.width\
 }\x0d\x0a            \
Row {\x0d\x0a         \
       spacing: \
6\x0d\x0a             \
   Button {\x0d\x0a   \
                \
 text: \x22Anwenden\
\x22; implicitHeigh\
t: 26; font.pixe\
lSize: 11\x0d\x0a     \
               e\
nabled: !!previe\
w.ok\x0d\x0a          \
          onClic\
ked: { dlg.apply\
Error = columnEd\
itorController.a\
pplyLookup(dlg.r\
ow, dlg.options(\
)); if (dlg.appl\
yError === \x22\x22) d\
lg.close() }\x0d\x0a  \
              }\x0d\
\x0a               \
 Button { text: \
\x22Abbrechen\x22; imp\
licitHeight: 26;\
 font.pixelSize:\
 11; onClicked: \
dlg.close() }\x0d\x0a \
           }\x0d\x0a  \
      }\x0d\x0a    }\x0d\x0a\
}\x0d\x0a\
\x00\x00*E\
/\
/ One tile. Stat\
es: ACTIVE / SEL\
ECTED (thin gree\
n border), passi\
ve (compact), se\
lected in a grou\
p (badge 1..n), \
calculated (gree\
n fill),\x0d\x0a// hid\
den (grey, dashe\
d grey border), \
not exported (or\
ange). Tiles are\
 only a view: th\
e data lives in \
columnConfigMode\
l, a drag only r\
eports\x0d\x0a// posit\
ions to columnEd\
itorController. \
Double-click on \
the type chip = \
\x22Spaltentyp \xc3\xa4nd\
ern\x22; right-clic\
k / \x22\xe2\x8b\xae\x22 = menu\
.\x0d\x0aimport QtQuic\
k\x0d\x0aimport QtQuic\
k.Controls\x0d\x0a\x0d\x0aRe\
ctangle {\x0d\x0a    i\
d: card\x0d\x0a\x0d\x0a    p\
roperty int slot\
Index: -1\x0d\x0a    p\
roperty string s\
hortName: \x22\x22\x0d\x0a  \
  property bool \
protectedColumn:\
 false        //\
 DCF database in\
dex (PnPID): red\
 bold, cannot be\
 hidden\x0d\x0a    pro\
perty bool renam\
ed: false       \
         // outp\
ut column rename\
d: red mark at t\
he right edge, t\
ext in red (disp\
lay only)\x0d\x0a    p\
roperty string o\
riginalName: \x22\x22 \
           // na\
me before the re\
name (carried al\
ong; the data ke\
eps its original\
 column)\x0d\x0a    pr\
operty bool show\
Original: false \
          // the\
 \x22Umbenannt\x22 are\
a also shows the\
 original name o\
n the tile\x0d\x0a    \
property string \
chip: \x22ABC\x22\x0d\x0a   \
 property int po\
sition: 0\x0d\x0a    p\
roperty bool hid\
denColumn: false\
\x0d\x0a    property b\
ool computed: fa\
lse\x0d\x0a    propert\
y bool active: f\
alse\x0d\x0a    proper\
ty int selOrder:\
 0              \
// 1, 2, 3 ... w\
hen several tile\
s are selected (\
order of clickin\
g)\x0d\x0a    property\
 bool inExport: \
true\x0d\x0a    proper\
ty bool dragging\
: false\x0d\x0a    pro\
perty string tip\
: \x22\x22\x0d\x0a    proper\
ty string tagCol\
or: \x22\x22         /\
/ colour categor\
y from the proje\
ct definitions (\
Tag structures);\
 empty = neutral\
\x0d\x0a    property s\
tring groupColor\
: \x22\x22        // t\
ile group: colou\
r of the group f\
rame (empty = no\
t in a group)\x0d\x0a \
   property stri\
ng groupName: \x22\x22\
\x0d\x0a    property b\
ool splitTile: f\
alse        // c\
olumn the Excel \
export splits by\
 (set from the e\
xport dialog): l\
ight green\x0d\x0a    \
property bool te\
mporary: false  \
      // display\
-only column (me\
rged view / dupl\
icates): grey ti\
le, not moved / \
renamed / groupe\
d\x0d\x0a    property \
string tipText: \
\x22\x22          // h\
over text: full \
name, number of \
elements, functi\
on (asked from t\
he controller on\
 hover)\x0d\x0a    pro\
perty alias mous\
e: mouseArea\x0d\x0a  \
  readonly prope\
rty bool multi: \
selOrder > 0\x0d\x0a\x0d\x0a\
    signal click\
ed()\x0d\x0a    signal\
 ctrlClicked()\x0d\x0a\
    signal shift\
Clicked(bool add\
itive)       // \
Shift+Click = ra\
nge from the anc\
hor; Shift+Ctrl \
adds the range\x0d\x0a\
    signal typeR\
equested()\x0d\x0a    \
signal backReque\
sted()          \
         // doub\
le-click on the \
tile (not on the\
 type chip): the\
 back side with \
all properties\x0d\x0a\
    signal conte\
xtRequested()\x0d\x0a\x0d\
\x0a    width: 90\x0d\x0a\
    height: acti\
ve ? 64 : 56\x0d\x0a  \
  radius: 6\x0d\x0a   \
 readonly proper\
ty bool marked: \
active || multi\x0d\
\x0a    readonly pr\
operty bool tagg\
ed: tagColor !==\
 \x22\x22\x0d\x0a    readonl\
y property color\
 tagTint: tagged\
 ? Qt.tint(\x22#fff\
fff\x22, Qt.rgba(Qt\
.color(tagColor)\
.r, Qt.color(tag\
Color).g, Qt.col\
or(tagColor).b, \
marked ? 0.30 : \
0.20))\x0d\x0a        \
                \
                \
    : \x22#ffffff\x22\x0d\
\x0a    // fill: hi\
dden (grey) > no\
t exported (oran\
ge) > colour cat\
egory > calculat\
ed (green) > mar\
ked > white\x0d\x0a   \
 // split column\
 of the Excel ex\
port: light gree\
n fill (wins ove\
r everything but\
 a hidden tile)\x0d\
\x0a    color: spli\
tTile && !hidden\
Column ? \x22#b9eec\
6\x22 : temporary ?\
 \x22#eceff1\x22 : hid\
denColumn ? \x22#e5\
e7eb\x22 : (!inExpo\
rt ? \x22#fff3e0\x22 :\
 (tagged ? tagTi\
nt : (computed ?\
 \x22#dff3e3\x22 : (ma\
rked ? \x22#eef8f1\x22\
 : \x22#ffffff\x22))))\
\x0d\x0a    border.wid\
th: marked ? 1.5\
 : (hiddenColumn\
 ? 0 : (!inExpor\
t ? 2 : 1))\x0d\x0a   \
 border.color: m\
arked ? \x22#2e9e4f\
\x22 : temporary ? \
\x22#7b8794\x22 : (!in\
Export ? \x22#f08c0\
0\x22 : (computed ?\
 \x22#4c9f5f\x22 : \x22#c\
3ccd6\x22))\x0d\x0a    op\
acity: hiddenCol\
umn ? 0.85 : 1.0\
\x0d\x0a    scale: dra\
gging ? 1.06 : 1\
.0\x0d\x0a    z: dragg\
ing ? 10 : (acti\
ve ? 2 : 0)\x0d\x0a\x0d\x0a \
   Drag.active: \
mouseArea.drag.a\
ctive\x0d\x0a    Drag.\
source: card\x0d\x0a  \
  Drag.hotSpot.x\
: width / 2\x0d\x0a   \
 Drag.hotSpot.y:\
 height / 2\x0d\x0a\x0d\x0a \
   Accessible.ro\
le: Accessible.B\
utton\x0d\x0a    Acces\
sible.name: tip\x0d\
\x0a\x0d\x0a    Rectangle\
 {              \
                \
  // group frame\
: tiles of one g\
roup carry the s\
ame coloured fra\
me (block in the\
 tile editor)\x0d\x0a \
       visible: \
card.groupColor \
!== \x22\x22\x0d\x0a        \
anchors.fill: pa\
rent\x0d\x0a        an\
chors.margins: -\
3\x0d\x0a        radiu\
s: card.radius +\
 2\x0d\x0a        colo\
r: \x22transparent\x22\
\x0d\x0a        border\
.width: 2.5\x0d\x0a   \
     border.colo\
r: card.groupCol\
or\x0d\x0a        z: -\
1\x0d\x0a    }\x0d\x0a\x0d\x0a    \
Canvas {        \
                \
           // da\
shed border of a\
 hidden tile (or\
ange when it is \
also not exporte\
d)\x0d\x0a        id: \
dashed\x0d\x0a        \
anchors.fill: pa\
rent\x0d\x0a        vi\
sible: card.hidd\
enColumn && !car\
d.marked\x0d\x0a      \
  property bool \
ex: card.inExpor\
t\x0d\x0a        onExC\
hanged: requestP\
aint()\x0d\x0a        \
onWidthChanged: \
requestPaint()\x0d\x0a\
        onHeight\
Changed: request\
Paint()\x0d\x0a       \
 onVisibleChange\
d: requestPaint(\
)\x0d\x0a        onPai\
nt: {\x0d\x0a         \
   var ctx = get\
Context(\x222d\x22)\x0d\x0a \
           ctx.r\
eset()\x0d\x0a        \
    ctx.strokeSt\
yle = card.inExp\
ort ? \x22#7b8794\x22 \
: \x22#f08c00\x22\x0d\x0a   \
         ctx.lin\
eWidth = 1.5\x0d\x0a  \
          ctx.se\
tLineDash([4, 3]\
)\x0d\x0a            c\
tx.strokeRect(1,\
 1, width - 2, h\
eight - 2)\x0d\x0a    \
    }\x0d\x0a    }\x0d\x0a\x0d\x0a\
    Rectangle { \
                \
               /\
/ colour categor\
y stripe (stays \
visible on hidde\
n / not exported\
 tiles)\x0d\x0a       \
 visible: card.t\
agged\x0d\x0a        x\
: 3; y: 6\x0d\x0a     \
   width: 3\x0d\x0a   \
     height: car\
d.height - 12\x0d\x0a \
       radius: 1\
.5\x0d\x0a        colo\
r: card.tagColor\
\x0d\x0a    }\x0d\x0a    Tex\
t {\x0d\x0a        id:\
 posText\x0d\x0a      \
  x: 8; y: 5\x0d\x0a  \
      text: card\
.position\x0d\x0a     \
   font.pixelSiz\
e: 10\x0d\x0a        c\
olor: card.hidde\
nColumn ? \x22#6b72\
80\x22 : \x22#7b8794\x22\x0d\
\x0a    }\x0d\x0a    Rect\
angle {\x0d\x0a       \
 id: chipBox\x0d\x0a  \
      x: 8 + Mat\
h.max(14, posTex\
t.implicitWidth)\
 + 3\x0d\x0a        y:\
 4\x0d\x0a        widt\
h: chipText.impl\
icitWidth + 10\x0d\x0a\
        height: \
16\x0d\x0a        radi\
us: 3\x0d\x0a        c\
olor: card.hidde\
nColumn ? \x22#d1d5\
db\x22 : (card.mark\
ed ? \x22#d5eedc\x22 :\
 \x22#e8eef5\x22)\x0d\x0a   \
     Text { id: \
chipText; anchor\
s.centerIn: pare\
nt; text: card.c\
hip; font.pixelS\
ize: 10; font.bo\
ld: true; color:\
 \x22#34495e\x22 }\x0d\x0a  \
  }\x0d\x0a    Text { \
                \
                \
    // function \
marker of a calc\
ulated tile\x0d\x0a   \
     visible: ca\
rd.computed\x0d\x0a   \
     x: chipBox.\
x + chipBox.widt\
h + 4\x0d\x0a        y\
: 4\x0d\x0a        tex\
t: \x22\xc6\x92x\x22\x0d\x0a      \
  font.pixelSize\
: 11\x0d\x0a        fo\
nt.bold: true\x0d\x0a \
       color: \x22#\
2f7d44\x22\x0d\x0a    }\x0d\x0a\
    Text {\x0d\x0a    \
    id: dots\x0d\x0a  \
      anchors.ri\
ght: parent.righ\
t; anchors.right\
Margin: 6\x0d\x0a     \
   y: 1\x0d\x0a       \
 text: \x22\xe2\x8b\xae\x22\x0d\x0a  \
      font.pixel\
Size: 16\x0d\x0a      \
  color: \x22#52606\
d\x22\x0d\x0a    }\x0d\x0a    R\
ectangle {      \
                \
          // ren\
amed: red mark a\
t the right edge\
 of the tile\x0d\x0a  \
      visible: c\
ard.renamed\x0d\x0a   \
     anchors { r\
ight: parent.rig\
ht; top: parent.\
top; bottom: par\
ent.bottom; topM\
argin: 6; bottom\
Margin: 6 }\x0d\x0a   \
     width: 4\x0d\x0a \
       radius: 2\
\x0d\x0a        color:\
 \x22#d32f2f\x22\x0d\x0a    \
    z: 3\x0d\x0a    }\x0d\
\x0a    Text {     \
                \
                \
// \x22Umbenannt\x22 a\
rea: original na\
me above the new\
 one\x0d\x0a        vi\
sible: card.rena\
med && card.show\
Original\x0d\x0a      \
  anchors.left: \
parent.left; anc\
hors.leftMargin:\
 7\x0d\x0a        anch\
ors.right: paren\
t.right; anchors\
.rightMargin: 10\
\x0d\x0a        anchor\
s.bottom: parent\
.bottom; anchors\
.bottomMargin: c\
ard.active ? 25 \
: 22\x0d\x0a        te\
xt: card.origina\
lName\x0d\x0a        e\
lide: Text.Elide\
Right\x0d\x0a        f\
ont.pixelSize: 1\
0\x0d\x0a        font.\
strikeout: true\x0d\
\x0a        color: \
\x22#7b8794\x22\x0d\x0a    }\
\x0d\x0a    Text {\x0d\x0a  \
      visible: !\
card.inExport ||\
 card.temporary\x0d\
\x0a        anchors\
.right: parent.r\
ight; anchors.ri\
ghtMargin: 6\x0d\x0a  \
      y: 21\x0d\x0a   \
     text: card.\
temporary ? \x22tem\
porary\x22 : \x22nicht\
 exportiert\x22\x0d\x0a  \
      font.pixel\
Size: 8\x0d\x0a       \
 font.italic: tr\
ue\x0d\x0a        colo\
r: card.temporar\
y ? \x22#52606d\x22 : \
\x22#c2620a\x22\x0d\x0a    }\
\x0d\x0a    Text {\x0d\x0a  \
      anchors.le\
ft: parent.left;\
 anchors.leftMar\
gin: 7\x0d\x0a        \
anchors.right: p\
arent.right; anc\
hors.rightMargin\
: card.renamed ?\
 10 : 7\x0d\x0a       \
 anchors.bottom:\
 parent.bottom; \
anchors.bottomMa\
rgin: card.activ\
e ? 9 : 7\x0d\x0a     \
   text: card.sh\
ortName\x0d\x0a       \
 elide: Text.Eli\
deRight\x0d\x0a       \
 font.pixelSize:\
 card.active ? 1\
3 : 12\x0d\x0a        \
font.bold: card.\
active || card.p\
rotectedColumn\x0d\x0a\
        color: c\
ard.protectedCol\
umn || card.rena\
med ? \x22#c0392b\x22 \
: card.hiddenCol\
umn ? \x22#6b7280\x22 \
: \x22#1f2933\x22\x0d\x0a   \
 }\x0d\x0a\x0d\x0a    Rectan\
gle {           \
                \
     // selectio\
n-order badge\x0d\x0a \
       visible: \
card.multi\x0d\x0a    \
    x: -6; y: -6\
\x0d\x0a        width:\
 20; height: 20\x0d\
\x0a        radius:\
 10\x0d\x0a        col\
or: \x22#2e9e4f\x22\x0d\x0a \
       border.co\
lor: \x22#ffffff\x22\x0d\x0a\
        border.w\
idth: 2\x0d\x0a       \
 z: 20\x0d\x0a        \
Text { anchors.c\
enterIn: parent;\
 text: card.selO\
rder; font.pixel\
Size: 11; font.b\
old: true; color\
: \x22#ffffff\x22 }\x0d\x0a \
   }\x0d\x0a\x0d\x0a    Mous\
eArea {\x0d\x0a       \
 id: mouseArea\x0d\x0a\
        anchors.\
fill: parent\x0d\x0a  \
      acceptedBu\
ttons: Qt.LeftBu\
tton | Qt.RightB\
utton\x0d\x0a        d\
rag.target: card\
.temporary || ca\
rd.showOriginal \
? null : card   \
  // temporary c\
olumns and the t\
iles of the \x22Umb\
enannt\x22 view can\
not be dragged\x0d\x0a\
        drag.axi\
s: Drag.XAndYAxi\
s\x0d\x0a        prope\
rty bool pending\
Single: false\x0d\x0a \
       hoverEnab\
led: true\x0d\x0a     \
   onContainsMou\
seChanged: {\x0d\x0a  \
          if (co\
ntainsMouse && t\
ypeof columnEdit\
orController !==\
 \x22undefined\x22) ca\
rd.tipText = col\
umnEditorControl\
ler.tileTip(card\
.slotIndex)\x0d\x0a   \
     }\x0d\x0a        \
function overChi\
p(m) {\x0d\x0a        \
    var p = mapT\
oItem(chipBox, m\
.x, m.y)\x0d\x0a      \
      return p.x\
 >= 0 && p.y >= \
0 && p.x <= chip\
Box.width && p.y\
 <= chipBox.heig\
ht\x0d\x0a        }\x0d\x0a \
       onPressed\
: function (m) {\
\x0d\x0a            if\
 (m.button !== Q\
t.LeftButton) re\
turn\x0d\x0a          \
  if (m.modifier\
s & Qt.ShiftModi\
fier) card.shift\
Clicked(!!(m.mod\
ifiers & Qt.Cont\
rolModifier))\x0d\x0a \
           else \
if (m.modifiers \
& Qt.ControlModi\
fier) card.ctrlC\
licked()\x0d\x0a      \
      else if (t\
ypeof columnEdit\
orController !==\
 \x22undefined\x22 && \
columnEditorCont\
roller.inSelecti\
on(card.slotInde\
x))\x0d\x0a           \
     mouseArea.p\
endingSingle = t\
rue          // \
press inside a m\
ulti selection: \
keep it, so the \
whole group can \
be dragged\x0d\x0a    \
        else mou\
seArea.pendingSi\
ngle = true     \
    // plain cli\
ck: acts on rele\
ase, never while\
 the tile is pic\
ked up / dragged\
\x0d\x0a        }\x0d\x0a   \
     onReleased:\
 function (m) { \
                \
     // plain cl\
ick (no drag) in\
side a multi sel\
ection = select \
only this tile\x0d\x0a\
            if (\
pendingSingle &&\
 !drag.active &&\
 m.button === Qt\
.LeftButton) car\
d.clicked()\x0d\x0a   \
         pending\
Single = false\x0d\x0a\
        }\x0d\x0a     \
   onCanceled: p\
endingSingle = f\
alse\x0d\x0a        on\
Clicked: functio\
n (m) {\x0d\x0a       \
     if (m.butto\
n === Qt.RightBu\
tton || m.x >= d\
ots.x - 4 && m.y\
 < 24) card.cont\
extRequested()\x0d\x0a\
        }\x0d\x0a     \
   onDoubleClick\
ed: function (m)\
 {\x0d\x0a            \
if (m.button !==\
 Qt.LeftButton) \
return\x0d\x0a        \
    if (overChip\
(m)) card.typeRe\
quested()\x0d\x0a     \
       else if (\
!card.temporary)\
 card.backReques\
ted()\x0d\x0a        }\
\x0d\x0a    }\x0d\x0a\x0d\x0a    T\
oolTip.visible: \
mouseArea.contai\
nsMouse && !mous\
eArea.drag.activ\
e && card.tipTex\
t !== \x22\x22\x0d\x0a    To\
olTip.delay: 450\
\x0d\x0a    ToolTip.ti\
meout: 25000\x0d\x0a  \
  ToolTip.text: \
card.tipText\x0d\x0a\x0d\x0a\
    states: Stat\
e {\x0d\x0a        whe\
n: mouseArea.dra\
g.active\x0d\x0a      \
  AnchorChanges \
{ target: card; \
anchors.horizont\
alCenter: undefi\
ned; anchors.ver\
ticalCenter: und\
efined }\x0d\x0a    }\x0d\
\x0a}\x0d\x0a\
\x00\x00$\xfd\
/\
/ If-then column\
: a new calculat\
ed column whose \
value comes from\
 rules (first ma\
tching rule wins\
, otherwise the \
\x22else\x22 value).\x0d\x0a\
// Also used to \
change the rules\
 of an existing \
step (editIndex \
>= 0). The sourc\
e is never chang\
ed.\x0d\x0aimport QtQu\
ick\x0d\x0aimport QtQu\
ick.Controls\x0d\x0a\x0d\x0a\
Popup {\x0d\x0a    id:\
 dlg\x0d\x0a    proper\
ty int editIndex\
: -1\x0d\x0a    proper\
ty var rules: []\
                \
      // [{colum\
n, operator, val\
ue, result}]\x0d\x0a  \
  property var c\
hoices: []      \
              //\
 [{key, label}]\x0d\
\x0a    property va\
r operators: [] \
                \
 // [{key, label\
, noValue}]\x0d\x0a   \
 property var pr\
eview: ({ ok: fa\
lse, rows: [], c\
ounts: [], error\
: \x22\x22 })\x0d\x0a    pro\
perty string app\
lyError: \x22\x22\x0d\x0a\x0d\x0a \
   modal: false\x0d\
\x0a    dim: false\x0d\
\x0a    focus: true\
\x0d\x0a    closePolic\
y: Popup.CloseOn\
Escape\x0d\x0a    pare\
nt: Overlay.over\
lay\x0d\x0a    x: 0\x0d\x0a \
   y: parent ? p\
arent.height - 2\
 : 0\x0d\x0a    margin\
s: 6\x0d\x0a    paddin\
g: 8\x0d\x0a    width:\
 Math.min(470, (\
Overlay.overlay \
? Overlay.overla\
y.width : 470) -\
 12)\x0d\x0a    backgr\
ound: Rectangle \
{ color: \x22#fffff\
f\x22; border.color\
: \x22#7f9bb5\x22; bor\
der.width: 1; ra\
dius: 5 }\x0d\x0a\x0d\x0a   \
 function spec()\
 { return { rule\
s: rules, elseVa\
lue: elseField.t\
ext, ignoreCase:\
 !caseCheck.chec\
ked } }\x0d\x0a    fun\
ction refresh() \
{ preview = colu\
mnEditorControll\
er.previewCondit\
ional(spec()) }\x0d\
\x0a    function in\
dexOfKey(list, k\
ey) { for (var i\
 = 0; i < list.l\
ength; i++) if (\
list[i].key === \
key) return i; r\
eturn 0 }\x0d\x0a    f\
unction setRule(\
i, field, value)\
 {              \
           // ed\
ited in place: r\
e-assigning \x22rul\
es\x22 would rebuil\
d the fields whi\
le typing\x0d\x0a     \
   rules[i][fiel\
d] = value\x0d\x0a    \
    refresh()\x0d\x0a \
   }\x0d\x0a    functi\
on addRule() {\x0d\x0a\
        var r = \
rules.slice()\x0d\x0a \
       r.push({ \
column: choices.\
length ? choices\
[0].key : \x22\x22, op\
erator: \x22equals\x22\
, value: \x22\x22, res\
ult: \x22\x22 })\x0d\x0a    \
    rules = r\x0d\x0a \
       refresh()\
\x0d\x0a    }\x0d\x0a    fun\
ction removeRule\
(i) { var r = ru\
les.slice(); r.s\
plice(i, 1); rul\
es = r; refresh(\
) }\x0d\x0a    functio\
n openFor(row, s\
tepIndex) {\x0d\x0a   \
     choices = c\
olumnEditorContr\
oller.columnChoi\
ces()\x0d\x0a        o\
perators = colum\
nEditorControlle\
r.conditionOpera\
tors()\x0d\x0a        \
editIndex = step\
Index === undefi\
ned ? -1 : stepI\
ndex\x0d\x0a        ap\
plyError = \x22\x22\x0d\x0a \
       if (editI\
ndex >= 0) {\x0d\x0a  \
          var in\
fo = columnEdito\
rController.step\
Info(editIndex)\x0d\
\x0a            rul\
es = info.spec.r\
ules\x0d\x0a          \
  elseField.text\
 = info.spec.els\
eValue || \x22\x22\x0d\x0a  \
          caseCh\
eck.checked = in\
fo.spec.ignoreCa\
se === false\x0d\x0a  \
          nameFi\
eld.text = info.\
name || \x22\x22\x0d\x0a    \
    } else {\x0d\x0a  \
          var ke\
y = row >= 0 && \
row < choices.le\
ngth ? choices[r\
ow].key : (choic\
es.length ? choi\
ces[0].key : \x22\x22)\
\x0d\x0a            ru\
les = [{ column:\
 key, operator: \
\x22equals\x22, value:\
 \x22\x22, result: \x22\x22 \
}]\x0d\x0a            \
elseField.text =\
 \x22\x22; caseCheck.c\
hecked = false; \
nameField.text =\
 \x22\x22\x0d\x0a        }\x0d\x0a\
        refresh(\
)\x0d\x0a        open(\
)\x0d\x0a    }\x0d\x0a\x0d\x0a    \
contentItem: Fli\
ckable {\x0d\x0a      \
  clip: true\x0d\x0a  \
      implicitHe\
ight: Math.min(b\
ody.implicitHeig\
ht, 470)\x0d\x0a      \
  contentHeight:\
 body.implicitHe\
ight\x0d\x0a        bo\
undsBehavior: Fl\
ickable.StopAtBo\
unds\x0d\x0a        Co\
lumn {\x0d\x0a        \
    id: body\x0d\x0a  \
          width:\
 parent.width\x0d\x0a \
           spaci\
ng: 5\x0d\x0a         \
   Text { text: \
dlg.editIndex >=\
 0 ? \x22Schritt \xc3\xa4\
ndern: Wenn \xe2\x80\xa6 \
dann-Spalte\x22 : \x22\
Wenn \xe2\x80\xa6 dann-Sp\
alte\x22; font.bold\
: true; font.pix\
elSize: 12 }\x0d\x0a  \
          Row {\x0d\
\x0a               \
 visible: dlg.ed\
itIndex < 0; spa\
cing: 6\x0d\x0a       \
         Text { \
text: \x22Spaltenna\
me\x22; font.pixelS\
ize: 11; anchors\
.verticalCenter:\
 parent.vertical\
Center; width: 7\
8 }\x0d\x0a           \
     TextField {\
 id: nameField; \
width: 260; impl\
icitHeight: 26; \
font.pixelSize: \
11; selectByMous\
e: true; Accessi\
ble.name: \x22Name \
der neuen Spalte\
\x22 }\x0d\x0a           \
 }\x0d\x0a            \
Repeater {\x0d\x0a    \
            mode\
l: dlg.rules\x0d\x0a  \
              de\
legate: Rectangl\
e {\x0d\x0a           \
         width: \
body.width; heig\
ht: ruleCol.impl\
icitHeight + 8\x0d\x0a\
                \
    color: \x22#f7f\
9fb\x22; border.col\
or: \x22#dde3ea\x22; r\
adius: 4\x0d\x0a      \
              Co\
lumn {\x0d\x0a        \
                \
id: ruleCol\x0d\x0a   \
                \
     x: 6; y: 4;\
 width: parent.w\
idth - 12; spaci\
ng: 3\x0d\x0a         \
               R\
ow {\x0d\x0a          \
                \
  spacing: 4\x0d\x0a  \
                \
          Text {\
 text: index ===\
 0 ? \x22Wenn\x22 : \x22S\
onst wenn\x22; font\
.pixelSize: 11; \
anchors.vertical\
Center: parent.v\
erticalCenter; w\
idth: 40 }\x0d\x0a    \
                \
        ComboBox\
 {\x0d\x0a            \
                \
    model: dlg.c\
hoices; textRole\
: \x22label\x22; impli\
citWidth: 150; i\
mplicitHeight: 2\
6; font.pixelSiz\
e: 11\x0d\x0a         \
                \
       currentIn\
dex: dlg.indexOf\
Key(dlg.choices,\
 modelData.colum\
n)\x0d\x0a            \
                \
    Accessible.n\
ame: \x22Spalte der\
 Regel \x22 + (inde\
x + 1)\x0d\x0a        \
                \
        onActiva\
ted: dlg.setRule\
(index, \x22column\x22\
, dlg.choices[cu\
rrentIndex].key)\
\x0d\x0a              \
              }\x0d\
\x0a               \
             Com\
boBox {\x0d\x0a       \
                \
         id: opB\
ox\x0d\x0a            \
                \
    model: dlg.o\
perators; textRo\
le: \x22label\x22; imp\
licitWidth: 130;\
 implicitHeight:\
 26; font.pixelS\
ize: 11\x0d\x0a       \
                \
         current\
Index: dlg.index\
OfKey(dlg.operat\
ors, modelData.o\
perator)\x0d\x0a      \
                \
          Access\
ible.name: \x22Bedi\
ngung der Regel \
\x22 + (index + 1)\x0d\
\x0a               \
                \
 onActivated: dl\
g.setRule(index,\
 \x22operator\x22, dlg\
.operators[curre\
ntIndex].key)\x0d\x0a \
                \
           }\x0d\x0a  \
                \
          ToolBu\
tton {\x0d\x0a        \
                \
        text: \x22\xc3\
\x97\x22; width: 24; h\
eight: 26; enabl\
ed: dlg.rules.le\
ngth > 1; Access\
ible.name: \x22Rege\
l entfernen \x22 + \
(index + 1)\x0d\x0a   \
                \
             onC\
licked: dlg.remo\
veRule(index)\x0d\x0a \
                \
           }\x0d\x0a  \
                \
      }\x0d\x0a       \
                \
 Row {\x0d\x0a        \
                \
    spacing: 4\x0d\x0a\
                \
            Text\
 { text: \x22value\x22\
; font.pixelSize\
: 10; color: \x22#5\
2606d\x22; anchors.\
verticalCenter: \
parent.verticalC\
enter; width: 40\
 }\x0d\x0a            \
                \
TextField {\x0d\x0a   \
                \
             wid\
th: 130; implici\
tHeight: 26; fon\
t.pixelSize: 11;\
 selectByMouse: \
true\x0d\x0a          \
                \
      enabled: !\
dlg.operators[op\
Box.currentIndex\
].noValue\x0d\x0a     \
                \
           text:\
 modelData.value\
; placeholderTex\
t: dlg.operators\
[opBox.currentIn\
dex].key === \x22in\
_list\x22 ? \x22a, b, \
c\x22 : \x22\x22\x0d\x0a       \
                \
         Accessi\
ble.name: \x22Wert \
der Regel \x22 + (i\
ndex + 1)\x0d\x0a     \
                \
           onTex\
tEdited: dlg.set\
Rule(index, \x22val\
ue\x22, text)\x0d\x0a    \
                \
        }\x0d\x0a     \
                \
       Text { te\
xt: \x22then\x22; font\
.pixelSize: 11; \
anchors.vertical\
Center: parent.v\
erticalCenter }\x0d\
\x0a               \
             Tex\
tField {\x0d\x0a      \
                \
          width:\
 130; implicitHe\
ight: 26; font.p\
ixelSize: 11; se\
lectByMouse: tru\
e\x0d\x0a             \
                \
   text: modelDa\
ta.result; Acces\
sible.name: \x22Erg\
ebnis der Regel \
\x22 + (index + 1)\x0d\
\x0a               \
                \
 onTextEdited: d\
lg.setRule(index\
, \x22result\x22, text\
)\x0d\x0a             \
               }\
\x0d\x0a              \
          }\x0d\x0a   \
                \
 }\x0d\x0a            \
    }\x0d\x0a         \
   }\x0d\x0a          \
  Button { text:\
 \x22+ Regel hinzuf\
\xc3\xbcgen\x22; implicit\
Height: 24; font\
.pixelSize: 11; \
onClicked: dlg.a\
ddRule() }\x0d\x0a    \
        Row {\x0d\x0a \
               s\
pacing: 6\x0d\x0a     \
           Text \
{ text: \x22Sonst\x22;\
 font.pixelSize:\
 11; anchors.ver\
ticalCenter: par\
ent.verticalCent\
er; width: 78 }\x0d\
\x0a               \
 TextField { id:\
 elseField; widt\
h: 200; implicit\
Height: 26; font\
.pixelSize: 11; \
selectByMouse: t\
rue; placeholder\
Text: \x22(leer)\x22; \
Accessible.name:\
 \x22Sonst-Wert\x22; o\
nTextEdited: dlg\
.refresh() }\x0d\x0a  \
          }\x0d\x0a   \
         CheckBo\
x { id: caseChec\
k; text: \x22Gro\xc3\x9f-\
/Kleinschreibung\
 beachten\x22; font\
.pixelSize: 11; \
onToggled: dlg.r\
efresh() }\x0d\x0a    \
        Text { v\
isible: !!previe\
w.error; text: p\
review.error || \
\x22\x22; font.pixelSi\
ze: 10; color: \x22\
#b03a2e\x22; wrapMo\
de: Text.Wrap; w\
idth: parent.wid\
th }\x0d\x0a          \
  Text {\x0d\x0a      \
          visibl\
e: !preview.erro\
r && (preview.co\
unts || []).leng\
th > 0\x0d\x0a        \
        text: \x22E\
rgebnis in den V\
orschauzeilen:  \
\x22 + (preview.cou\
nts || []).join(\
\x22   \xc2\xb7   \x22)\x0d\x0a   \
             fon\
t.pixelSize: 10;\
 font.bold: true\
; color: \x22#34495\
e\x22; wrapMode: Te\
xt.Wrap; width: \
parent.width\x0d\x0a  \
          }\x0d\x0a   \
         Repeate\
r {\x0d\x0a           \
     model: (pre\
view.rows || [])\
.slice(0, 4)\x0d\x0a  \
              de\
legate: Row {\x0d\x0a \
                \
   spacing: 6\x0d\x0a \
                \
   Text { text: \
modelData.before\
; font.pixelSize\
: 10; width: 250\
; elide: Text.El\
ideRight }\x0d\x0a    \
                \
Text { text: \x22\xe2\x86\
\x92\x22; font.pixelSi\
ze: 10 }\x0d\x0a      \
              Te\
xt { text: model\
Data.after === \x22\
\x22 ? \x22(leer)\x22 : m\
odelData.after; \
font.pixelSize: \
10; width: 120; \
elide: Text.Elid\
eRight }\x0d\x0a      \
          }\x0d\x0a   \
         }\x0d\x0a    \
        Text { v\
isible: dlg.appl\
yError !== \x22\x22; t\
ext: dlg.applyEr\
ror; font.pixelS\
ize: 10; color: \
\x22#b03a2e\x22; wrapM\
ode: Text.Wrap; \
width: parent.wi\
dth }\x0d\x0a         \
   Row {\x0d\x0a      \
          spacin\
g: 6\x0d\x0a          \
      Button {\x0d\x0a\
                \
    text: dlg.ed\
itIndex >= 0 ? \x22\
\xc3\x84nderung speich\
ern\x22 : \x22Anwenden\
\x22; implicitHeigh\
t: 26; font.pixe\
lSize: 11\x0d\x0a     \
               e\
nabled: !!previe\
w.ok\x0d\x0a          \
          onClic\
ked: {\x0d\x0a        \
                \
dlg.applyError =\
 dlg.editIndex >\
= 0 ? columnEdit\
orController.edi\
tConditionalStep\
(dlg.editIndex, \
dlg.spec())\x0d\x0a   \
                \
                \
                \
         : colum\
nEditorControlle\
r.applyCondition\
al(nameField.tex\
t, dlg.spec())\x0d\x0a\
                \
        if (dlg.\
applyError === \x22\
\x22) dlg.close()\x0d\x0a\
                \
    }\x0d\x0a         \
       }\x0d\x0a      \
          Button\
 { text: \x22Abbrec\
hen\x22; implicitHe\
ight: 26; font.p\
ixelSize: 11; on\
Clicked: dlg.clo\
se() }\x0d\x0a        \
    }\x0d\x0a        }\
\x0d\x0a    }\x0d\x0a}\x0d\x0a\
\x00\x00(\xbd\
/\
/ Back side of a\
 tile (\x22flip car\
d\x22): every edita\
ble property of \
ONE column in a \
popover below th\
e tile (double-c\
lick on the tile\
;\x0d\x0a// the double\
-click on the ty\
pe chip still op\
ens \x22Spaltentyp \
\xc3\xa4ndern\x22). The g\
rid stays untouc\
hed: the tile do\
es not grow, no \
neighbour moves.\
\x0d\x0a// Every chang\
e is stored at o\
nce as its own u\
ndo step (Ctrl+Z\
 works as usual)\
; \x22\xc3\x84nderungen v\
erwerfen\x22 undoes\
 all steps made \
since the popove\
r opened.\x0d\x0a// Es\
c, a click outsi\
de and the X but\
ton close it in \
exactly the same\
 way (a text tha\
t was typed is c\
ommitted first).\
\x0d\x0a// The origina\
l name is read o\
nly; \x22Name zur\xc3\xbc\
cksetzen\x22 gives \
the column its o\
riginal name bac\
k. The rename is\
 visual: the dat\
a stays.\x0d\x0aimport\
 QtQuick\x0d\x0aimport\
 QtQuick.Control\
s\x0d\x0aimport QtQuic\
k.Layouts\x0d\x0a\x0d\x0aPop\
up {\x0d\x0a    id: dl\
g\x0d\x0a    property \
string key: \x22\x22  \
                \
     // the tile\
 is followed by \
its key: the row\
 changes when th\
e position is ch\
anged\x0d\x0a    prope\
rty int startDep\
th: 0\x0d\x0a    prope\
rty int depth: 0\
                \
         // undo\
 steps now (grow\
s with every cha\
nge made here)\x0d\x0a\
    property var\
 info: ({})\x0d\x0a   \
 property var ta\
g: ({ tag: \x22\x22, c\
olor: \x22\x22 })\x0d\x0a   \
 property string\
 group: \x22\x22\x0d\x0a    \
property string \
problem: \x22\x22\x0d\x0a   \
 property bool b\
usy: false\x0d\x0a    \
signal changeTyp\
eRequested(int r\
ow)\x0d\x0a\x0d\x0a    modal\
: false\x0d\x0a    dim\
: false\x0d\x0a    foc\
us: true\x0d\x0a    cl\
osePolicy: Popup\
.CloseOnEscape |\
 Popup.CloseOnPr\
essOutside\x0d\x0a    \
parent: Overlay.\
overlay\x0d\x0a    x: \
0\x0d\x0a    y: parent\
 ? parent.height\
 - 2 : 0\x0d\x0a    ma\
rgins: 6\x0d\x0a    pa\
dding: 10\x0d\x0a    w\
idth: Math.min(3\
60, (Overlay.ove\
rlay ? Overlay.o\
verlay.width : 3\
60) - 12)\x0d\x0a    b\
ackground: Recta\
ngle { color: \x22#\
ffffff\x22; border.\
color: \x22#7f9bb5\x22\
; border.width: \
1; radius: 6 }\x0d\x0a\
\x0d\x0a    function r\
ow() { return ke\
y === \x22\x22 ? -1 : \
columnEditorCont\
roller.rowOfKey(\
key) }\x0d\x0a    func\
tion openFor(r) \
{\x0d\x0a        key =\
 columnEditorCon\
troller.inspect(\
r).key\x0d\x0a        \
startDepth = col\
umnEditorControl\
ler.undoDepth()\x0d\
\x0a        problem\
 = \x22\x22\x0d\x0a        r\
efresh()\x0d\x0a      \
  open()\x0d\x0a    }\x0d\
\x0a    function re\
fresh() {\x0d\x0a     \
   var r = row()\
\x0d\x0a        if (r \
< 0) return\x0d\x0a   \
     busy = true\
\x0d\x0a        depth \
= columnEditorCo\
ntroller.undoDep\
th()\x0d\x0a        in\
fo = columnEdito\
rController.insp\
ect(r)\x0d\x0a        \
tag = columnEdit\
orController.tag\
Info(r)\x0d\x0a       \
 group = columnE\
ditorController.\
inGroup(r) ? col\
umnEditorControl\
ler.groupName(r)\
 : \x22\x22\x0d\x0a        n\
ameField.text = \
info.outputName \
|| \x22\x22\x0d\x0a        s\
hortField.text =\
 info.shortName \
|| \x22\x22\x0d\x0a        p\
osBox.to = colum\
nConfigModel.cou\
nt\x0d\x0a        posB\
ox.value = r + 1\
\x0d\x0a        widthB\
ox.value = colum\
nEditorControlle\
r.columnWidth(r)\
\x0d\x0a        busy =\
 false\x0d\x0a    }\x0d\x0a \
   function say(\
err) { problem =\
 err || \x22\x22 }\x0d\x0a  \
  function commi\
tTexts() {      \
                \
// typed but not\
 confirmed yet (\
Esc / click outs\
ide): still coun\
ts\x0d\x0a        var \
r = row()\x0d\x0a     \
   if (r < 0 || \
busy) return\x0d\x0a  \
      if (nameFi\
eld.text !== (in\
fo.outputName ||\
 \x22\x22) && nameFiel\
d.text.trim() !=\
= \x22\x22) say(column\
EditorController\
.renameOutput(r,\
 nameField.text)\
)\x0d\x0a        if (s\
hortField.text !\
== (info.shortNa\
me || \x22\x22)) say(c\
olumnEditorContr\
oller.setShortNa\
me(r, shortField\
.text))\x0d\x0a    }\x0d\x0a\
    onAboutToHid\
e: commitTexts()\
\x0d\x0a    onOpened: \
nameField.forceA\
ctiveFocus()\x0d\x0a  \
  Connections {\x0d\
\x0a        target:\
 columnEditorCon\
troller\x0d\x0a       \
 function onUndo\
Changed() { if (\
dlg.visible) dlg\
.refresh() }\x0d\x0a  \
  }\x0d\x0a\x0d\x0a    conte\
ntItem: ColumnLa\
yout {\x0d\x0a        \
spacing: 6\x0d\x0a    \
    RowLayout {\x0d\
\x0a            Lay\
out.fillWidth: t\
rue\x0d\x0a           \
 Text { text: \x22S\
palteneigenschaf\
ten\x22; font.pixel\
Size: 12; font.b\
old: true; Layou\
t.fillWidth: tru\
e; elide: Text.E\
lideRight }\x0d\x0a   \
         Text {\x0d\
\x0a               \
 text: \x22\xe2\x9c\x95\x22; fo\
nt.pixelSize: 13\
; color: closeAr\
ea.containsMouse\
 ? \x22#2c3e50\x22 : \x22\
#9aa5b1\x22\x0d\x0a      \
          MouseA\
rea { id: closeA\
rea; anchors.fil\
l: parent; ancho\
rs.margins: -5; \
hoverEnabled: tr\
ue; cursorShape:\
 Qt.PointingHand\
Cursor\x0d\x0a        \
                \
    onClicked: d\
lg.close() }\x0d\x0a  \
          }\x0d\x0a   \
     }\x0d\x0a        \
GridLayout {\x0d\x0a  \
          Layout\
.fillWidth: true\
\x0d\x0a            co\
lumns: 2\x0d\x0a      \
      columnSpac\
ing: 8\x0d\x0a        \
    rowSpacing: \
5\x0d\x0a\x0d\x0a           \
 Text { text: \x22O\
riginalname\x22; fo\
nt.pixelSize: 11\
; color: \x22#52606\
d\x22 }\x0d\x0a          \
  TextField {\x0d\x0a \
               L\
ayout.fillWidth:\
 true; implicitH\
eight: 26; font.\
pixelSize: 11\x0d\x0a \
               r\
eadOnly: true; t\
ext: dlg.info.or\
iginalName || \x22\x22\
; color: \x22#52606\
d\x22\x0d\x0a            \
    background: \
Rectangle { colo\
r: \x22#f3f5f7\x22; bo\
rder.color: \x22#d3\
d9e0\x22; radius: 3\
 }\x0d\x0a            \
    Accessible.n\
ame: \x22Originalna\
me (nur lesen)\x22\x0d\
\x0a            }\x0d\x0a\
\x0d\x0a            Te\
xt { text: \x22Spal\
tenname\x22; font.p\
ixelSize: 11; co\
lor: \x22#52606d\x22 }\
\x0d\x0a            Ro\
wLayout {\x0d\x0a     \
           Layou\
t.fillWidth: tru\
e; spacing: 4\x0d\x0a \
               T\
extField {\x0d\x0a    \
                \
id: nameField\x0d\x0a \
                \
   objectName: \x22\
backName\x22\x0d\x0a     \
               L\
ayout.fillWidth:\
 true; implicitH\
eight: 26; font.\
pixelSize: 11; s\
electByMouse: tr\
ue\x0d\x0a            \
        color: d\
lg.info.outputNa\
me !== dlg.info.\
originalName ? \x22\
#c0392b\x22 : \x22#1f2\
933\x22\x0d\x0a          \
          onEdit\
ingFinished: dlg\
.commitTexts()\x0d\x0a\
                \
    Accessible.n\
ame: \x22Spaltennam\
e\x22\x0d\x0a            \
    }\x0d\x0a         \
       Button {\x0d\
\x0a               \
     objectName:\
 \x22backReset\x22\x0d\x0a  \
                \
  text: \x22Name zu\
r\xc3\xbccksetzen\x22; im\
plicitHeight: 26\
; font.pixelSize\
: 11\x0d\x0a          \
          enable\
d: dlg.info.outp\
utName !== dlg.i\
nfo.originalName\
\x0d\x0a              \
      onClicked:\
 dlg.say(columnE\
ditorController.\
renameOutput(dlg\
.row(), dlg.info\
.originalName))\x0d\
\x0a               \
 }\x0d\x0a            \
}\x0d\x0a\x0d\x0a           \
 Text { text: \x22K\
achelname\x22; font\
.pixelSize: 11; \
color: \x22#52606d\x22\
 }\x0d\x0a            \
TextField {\x0d\x0a   \
             id:\
 shortField\x0d\x0a   \
             obj\
ectName: \x22backSh\
ort\x22\x0d\x0a          \
      Layout.fil\
lWidth: true; im\
plicitHeight: 26\
; font.pixelSize\
: 11; selectByMo\
use: true\x0d\x0a     \
           place\
holderText: \x22aut\
omatic\x22\x0d\x0a       \
         onEditi\
ngFinished: dlg.\
commitTexts()\x0d\x0a \
               A\
ccessible.name: \
\x22Kurzname der Ka\
chel\x22\x0d\x0a         \
   }\x0d\x0a\x0d\x0a        \
    Text { text:\
 \x22Datentyp\x22; fon\
t.pixelSize: 11;\
 color: \x22#52606d\
\x22 }\x0d\x0a           \
 RowLayout {\x0d\x0a  \
              La\
yout.fillWidth: \
true; spacing: 4\
\x0d\x0a              \
  Text { text: d\
lg.info.outputTy\
peName || \x22\x22; fo\
nt.pixelSize: 11\
; font.bold: tru\
e; Layout.fillWi\
dth: true; elide\
: Text.ElideRigh\
t }\x0d\x0a           \
     Button { te\
xt: \x22\xc3\x84ndern \xe2\x80\xa6\
\x22; implicitHeigh\
t: 26; font.pixe\
lSize: 11\x0d\x0a     \
                \
    onClicked: {\
 var r = dlg.row\
(); dlg.close();\
 if (r >= 0) dlg\
.changeTypeReque\
sted(r) } }\x0d\x0a   \
         }\x0d\x0a\x0d\x0a  \
          Text {\
 text: \x22Export\x22;\
 font.pixelSize:\
 11; color: \x22#52\
606d\x22 }\x0d\x0a       \
     CheckBox {\x0d\
\x0a               \
 objectName: \x22ba\
ckExport\x22\x0d\x0a     \
           text:\
 \x22Exportieren\x22; \
font.pixelSize: \
11\x0d\x0a            \
    checked: dlg\
.info.inExport =\
== true\x0d\x0a       \
         onToggl\
ed: { columnEdit\
orController.set\
Export(dlg.row()\
, checked); dlg.\
refresh() }\x0d\x0a   \
         }\x0d\x0a\x0d\x0a  \
          Text {\
 text: \x22Sichtbar\
keit\x22; font.pixe\
lSize: 11; color\
: \x22#52606d\x22 }\x0d\x0a \
           Check\
Box {\x0d\x0a         \
       objectNam\
e: \x22backHidden\x22\x0d\
\x0a               \
 text: \x22Ausgeble\
ndet (nicht in d\
er Tabelle)\x22; fo\
nt.pixelSize: 11\
\x0d\x0a              \
  checked: dlg.i\
nfo.visible === \
false\x0d\x0a         \
       onToggled\
: {\x0d\x0a           \
         if (!co\
lumnEditorContro\
ller.setHidden(d\
lg.row(), checke\
d)) dlg.say(\x22Die\
 letzte sichtbar\
e Spalte kann ni\
cht ausgeblendet\
 werden.\x22)\x0d\x0a    \
                \
dlg.refresh()\x0d\x0a \
               }\
\x0d\x0a            }\x0d\
\x0a\x0d\x0a            T\
ext { text: \x22Pos\
ition\x22; font.pix\
elSize: 11; colo\
r: \x22#52606d\x22 }\x0d\x0a\
            Spin\
Box {\x0d\x0a         \
       id: posBo\
x\x0d\x0a             \
   objectName: \x22\
backPosition\x22\x0d\x0a \
               f\
rom: 1; to: 1; e\
ditable: true; i\
mplicitHeight: 2\
8; font.pixelSiz\
e: 11\x0d\x0a         \
       onValueMo\
dified: { if (!d\
lg.busy) { colum\
nEditorControlle\
r.moveToPosition\
(dlg.row(), valu\
e); dlg.refresh(\
) } }\x0d\x0a         \
   }\x0d\x0a\x0d\x0a        \
    Text { text:\
 \x22Gruppe\x22; font.\
pixelSize: 11; c\
olor: \x22#52606d\x22 \
}\x0d\x0a            R\
owLayout {\x0d\x0a    \
            Layo\
ut.fillWidth: tr\
ue; spacing: 4\x0d\x0a\
                \
Text { text: dlg\
.group !== \x22\x22 ? \
dlg.group : \x22(ke\
ine)\x22; font.pixe\
lSize: 11; Layou\
t.fillWidth: tru\
e; elide: Text.E\
lideRight\x0d\x0a     \
                \
  color: dlg.gro\
up !== \x22\x22 ? \x22#1f\
2933\x22 : \x22#9aa5b1\
\x22 }\x0d\x0a           \
     Button { te\
xt: \x22Gruppe aufl\
\xc3\xb6sen\x22; implicit\
Height: 26; font\
.pixelSize: 11; \
visible: dlg.gro\
up !== \x22\x22\x0d\x0a     \
                \
    onClicked: {\
 columnEditorCon\
troller.ungroup(\
dlg.row()); dlg.\
refresh() } }\x0d\x0a \
               B\
utton { text: \x22Z\
ur Gruppe hinzuf\
\xc3\xbcgen\x22; implicit\
Height: 26; font\
.pixelSize: 11; \
visible: dlg.gro\
up === \x22\x22\x0d\x0a     \
                \
    onClicked: {\
 columnEditorCon\
troller.addToGro\
up(dlg.row()); d\
lg.close() } }\x0d\x0a\
            }\x0d\x0a\x0d\
\x0a            Tex\
t { text: \x22Spalt\
enbreite\x22; font.\
pixelSize: 11; c\
olor: \x22#52606d\x22 \
}\x0d\x0a            R\
owLayout {\x0d\x0a    \
            spac\
ing: 4\x0d\x0a        \
        SpinBox \
{\x0d\x0a             \
       id: width\
Box\x0d\x0a           \
         objectN\
ame: \x22backWidth\x22\
\x0d\x0a              \
      from: 30; \
to: 1200; stepSi\
ze: 10; editable\
: true; implicit\
Height: 28; font\
.pixelSize: 11\x0d\x0a\
                \
    onValueModif\
ied: { if (!dlg.\
busy) { dlg.say(\
columnEditorCont\
roller.setColumn\
Width(dlg.row(),\
 value)); } }\x0d\x0a \
               }\
\x0d\x0a              \
  Text { text: \x22\
px  (Standardbre\
ite dieser Spalt\
e)\x22; font.pixelS\
ize: 10; color: \
\x22#7b8794\x22 }\x0d\x0a   \
         }\x0d\x0a\x0d\x0a  \
          Text {\
 text: \x22Tag-Farb\
e\x22; font.pixelSi\
ze: 11; color: \x22\
#52606d\x22 }\x0d\x0a    \
        RowLayou\
t {\x0d\x0a           \
     spacing: 6\x0d\
\x0a               \
 Rectangle { wid\
th: 16; height: \
12; radius: 2; b\
order.color: \x22#9\
aa5b1\x22; color: d\
lg.tag.color !==\
 \x22\x22 ? dlg.tag.co\
lor : \x22transpare\
nt\x22 }\x0d\x0a         \
       Text { fo\
nt.pixelSize: 11\
; color: \x22#52606\
d\x22\x0d\x0a            \
           text:\
 dlg.tag.tag !==\
 \x22\x22 ? dlg.tag.ta\
g + \x22  (Projektd\
efinitionen > Ta\
g-Strukturen)\x22 :\
 \x22keine \xe2\x80\x93 in d\
en Projektdefini\
tionen festlegen\
\x22 }\x0d\x0a           \
 }\x0d\x0a        }\x0d\x0a \
       Text {\x0d\x0a \
           visib\
le: dlg.problem \
!== \x22\x22\x0d\x0a        \
    text: dlg.pr\
oblem; color: \x22#\
b03a2e\x22; font.pi\
xelSize: 10; wra\
pMode: Text.Wrap\
; Layout.fillWid\
th: true\x0d\x0a      \
  }\x0d\x0a        Row\
Layout {\x0d\x0a      \
      Layout.fil\
lWidth: true; sp\
acing: 6\x0d\x0a      \
      Text { tex\
t: \x22\xc3\x84nderungen \
gelten sofort (r\
\xc3\xbcckg\xc3\xa4ngig: Str\
g+Z)\x22; font.pixe\
lSize: 10; color\
: \x22#7b8794\x22; Lay\
out.fillWidth: t\
rue; elide: Text\
.ElideRight }\x0d\x0a \
           Butto\
n {\x0d\x0a           \
     objectName:\
 \x22backCancel\x22\x0d\x0a \
               t\
ext: \x22\xc3\x84nderunge\
n verwerfen\x22; im\
plicitHeight: 26\
; font.pixelSize\
: 11\x0d\x0a          \
      enabled: d\
lg.depth > dlg.s\
tartDepth\x0d\x0a     \
           onCli\
cked: { columnEd\
itorController.u\
ndoTo(dlg.startD\
epth); dlg.refre\
sh() }\x0d\x0a        \
    }\x0d\x0a        }\
\x0d\x0a    }\x0d\x0a}\x0d\x0a\
"

qt_resource_name = b"\
\x00\x0d\
\x01|\x81B\
\x00c\
\x00o\x00l\x00u\x00m\x00n\x00_\x00e\x00d\x00i\x00t\x00o\x00r\
\x00\x14\
\x09\x9aH\x5c\
\x00C\
\x00h\x00a\x00n\x00g\x00e\x00T\x00y\x00p\x00e\x00D\x00i\x00a\x00l\x00o\x00g\x00.\
\x00q\x00m\x00l\
\x00\x0e\
\x010N\x9c\
\x00S\
\x00t\x00e\x00p\x00s\x00P\x00a\x00n\x00e\x00l\x00.\x00q\x00m\x00l\
\x00\x0e\
\x06g\xeb\x9c\
\x00G\
\x00r\x00o\x00u\x00p\x00P\x00a\x00n\x00e\x00l\x00.\x00q\x00m\x00l\
\x00\x0e\
\x0b\x93\x17\xfc\
\x00T\
\x00i\x00l\x00e\x00S\x00t\x00a\x00t\x00u\x00s\x00.\x00q\x00m\x00l\
\x00\x11\
\x02\xe13\xdc\
\x00F\
\x00u\x00n\x00c\x00t\x00i\x00o\x00n\x00S\x00t\x00a\x00c\x00k\x00.\x00q\x00m\x00l\
\
\x00\x0c\
\x0f{\x04\xfc\
\x00S\
\x00i\x00d\x00e\x00P\x00a\x00n\x00e\x00.\x00q\x00m\x00l\
\x00\x13\
\x00\x5co\xbc\
\x00T\
\x00r\x00a\x00n\x00s\x00f\x00o\x00r\x00m\x00D\x00i\x00a\x00l\x00o\x00g\x00.\x00q\
\x00m\x00l\
\x00\x0e\
\x04\x8f\xc3|\
\x00C\
\x00o\x00l\x00u\x00m\x00n\x00G\x00r\x00i\x00d\x00.\x00q\x00m\x00l\
\x00\x0f\
\x04h1\x9c\
\x00C\
\x00h\x00e\x00c\x00k\x00D\x00i\x00a\x00l\x00o\x00g\x00.\x00q\x00m\x00l\
\x00\x0e\
\x0d\x85\xb4\x5c\
\x00T\
\x00e\x00x\x00t\x00P\x00r\x00o\x00m\x00p\x00t\x00.\x00q\x00m\x00l\
\x00\x11\
\x0a\xb6\x8d\xfc\
\x00R\
\x00u\x00l\x00e\x00I\x00n\x00s\x00p\x00e\x00c\x00t\x00o\x00r\x00.\x00q\x00m\x00l\
\
\x00\x0f\
\x05Jc|\
\x00S\
\x00p\x00l\x00i\x00t\x00D\x00i\x00a\x00l\x00o\x00g\x00.\x00q\x00m\x00l\
\x00\x11\
\x0a\xde\xfe|\
\x00D\
\x00r\x00o\x00p\x00I\x00n\x00d\x00i\x00c\x00a\x00t\x00o\x00r\x00.\x00q\x00m\x00l\
\
\x00\x10\
\x06\xc7\xd3\xbc\
\x00L\
\x00o\x00o\x00k\x00u\x00p\x00D\x00i\x00a\x00l\x00o\x00g\x00.\x00q\x00m\x00l\
\x00\x0e\
\x04\xff\xc3\x9c\
\x00C\
\x00o\x00l\x00u\x00m\x00n\x00C\x00a\x00r\x00d\x00.\x00q\x00m\x00l\
\x00\x15\
\x09\x1b\xfc\x9c\
\x00C\
\x00o\x00n\x00d\x00i\x00t\x00i\x00o\x00n\x00a\x00l\x00D\x00i\x00a\x00l\x00o\x00g\
\x00.\x00q\x00m\x00l\
\x00\x12\
\x0a\xa9\xb1\x1c\
\x00T\
\x00i\x00l\x00e\x00B\x00a\x00c\x00k\x00D\x00i\x00a\x00l\x00o\x00g\x00.\x00q\x00m\
\x00l\
"

qt_resource_struct = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x11\x00\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\xfa\x00\x00\x00\x00\x00\x01\x00\x00z\xe4\
\x00\x00\x01\xa2\x0d\xfcV\x92\
\x00\x00\x00N\x00\x00\x00\x00\x00\x01\x00\x00$W\
\x00\x00\x01\xa2\x0d\xfcV\x15\
\x00\x00\x00\xb4\x00\x00\x00\x00\x00\x01\x00\x00q\xb8\
\x00\x00\x01\xa2\x0d\xfcV\x05\
\x00\x00\x01H\x00\x00\x00\x00\x00\x01\x00\x01[\x93\
\x00\x00\x01\xa2\x0d\xfcU\xfa\
\x00\x00\x01&\x00\x00\x00\x00\x00\x01\x00\x00\xa9\xbd\
\x00\x00\x01\xa2\x0d\xfcV\x92\
\x00\x00\x02(\x00\x00\x00\x00\x00\x01\x00\x01\xc8\x05\
\x00\x00\x01\xa2\x0d\xfcV\x92\
\x00\x00\x01\xb6\x00\x00\x00\x00\x00\x01\x00\x01\x8f\xce\
\x00\x00\x01\xa2\x0d\xfcV\x0d\
\x00\x00\x00p\x00\x00\x00\x00\x00\x01\x00\x008\x19\
\x00\x00\x01\xa2\x0d\xfcV\x05\
\x00\x00\x02\x02\x00\x00\x00\x00\x00\x01\x00\x01\xab=\
\x00\x00\x01\xa2\x0d\xfcV\x0d\
\x00\x00\x02J\x00\x00\x00\x00\x00\x01\x00\x01\xf2N\
\x00\x00\x01\xa2\x0d\xfcV\x05\
\x00\x00\x00 \x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\xa2\x0d\xfcU\xf7\
\x00\x00\x02z\x00\x00\x00\x00\x00\x01\x00\x02\x17O\
\x00\x00\x01\xa2\x0d\xfcV\x18\
\x00\x00\x01\x8e\x00\x00\x00\x00\x00\x01\x00\x01\x81\xc1\
\x00\x00\x01\xa2\x0d\xfcV\x0d\
\x00\x00\x01\xda\x00\x00\x00\x00\x00\x01\x00\x01\xaa\x5c\
\x00\x00\x01\xa2\x0d\xfcV\x05\
\x00\x00\x00\x92\x00\x00\x00\x00\x00\x01\x00\x00bE\
\x00\x00\x01\xa2\x0d\xfcV\x1a\
\x00\x00\x01l\x00\x00\x00\x00\x00\x01\x00\x01y\xb3\
\x00\x00\x01\xa2\x0d\xfcV\x15\
\x00\x00\x00\xdc\x00\x00\x00\x00\x00\x01\x00\x00t\x04\
\x00\x00\x01\xa2\x0d\xfcV\x0d\
"

def qInitResources():
    QtCore.qRegisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(0x03, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()
