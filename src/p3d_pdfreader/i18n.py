"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). Mehrsprachige Oberflaeche: Standard Deutsch, optional Englisch/Franzoesisch.

* Der Katalog liegt strukturiert in ``assets/i18n/catalog.json`` (Schluessel = deutscher Originaltext, je Eintrag ``en``/``fr``).
* Statt jeden Text im Code zu umhuellen, uebersetzt ein Event-Filter die Widgets beim Anzeigen (Beschriftungen, Knoepfe,
  Reiter, Tabellenkoepfe, Menues, Tooltips, Fenstertitel). Combo-Eintraege und Listeninhalte bleiben unveraendert (sie sind Daten).
* Der Wechsel wirkt sofort auf alle offenen Fenster; die Wahl wird je Benutzer in ``config/state.json`` gemerkt.
* Nicht im Katalog stehende Texte bleiben deutsch (Katalog laesst sich ohne Codeaenderung erweitern)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from PySide6.QtCore import QEvent, QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractButton, QApplication, QComboBox, QGroupBox, QLabel, QLineEdit, QMenu, QPushButton, QTabBar, QTableWidget,
    QToolButton, QWidget,
)

from .paths import config_dir

LANGUAGES = {"de": "Deutsch", "en": "English", "fr": "Français"}
DEFAULT = "de"
_DIR = Path(__file__).parent / "assets" / "i18n"
_GLOSSARY = _DIR / "glossary.json"

_entries: dict[str, dict[str, str]] = {}          # deutscher Text -> {"en": ..., "fr": ...}
_templates: list[tuple[str, dict[str, str]]] = []  # Texte mit {0}, {1} ... : (deutsche Vorlage, Uebersetzungen)
_reverse: dict[str, str] = {}                     # uebersetzter Text -> deutscher Text
_state = {"lang": DEFAULT, "loaded": False}
_missed: set[str] = set()                         # nicht uebersetzte Texte (nur Diagnose)
_PLACEHOLDER = re.compile(r"\{(\d+)\}")
_AFFIX = re.compile(r"^([\s›▾•·+−\-…]*)(.*?)([\s›▾•·+−…]*)$", re.S)   # Kernwort ohne Pfeile/Aufzaehlungszeichen
_rx_cache: dict[str, re.Pattern] = {}


def _compile(template: str) -> re.Pattern:
    """Vorlage mit {0}, {1} ... in einen Regex mit benannten Gruppen umwandeln."""
    cached = _rx_cache.get(template)
    if cached is None:
        parts, last = [], 0
        for m in _PLACEHOLDER.finditer(template):
            parts.append(re.escape(template[last:m.start()]))
            parts.append(f"(?P<g{m.group(1)}>.*?)")
            last = m.end()
        parts.append(re.escape(template[last:]))
        cached = _rx_cache[template] = re.compile("^" + "".join(parts) + "$", re.S)
    return cached


def _fill(template: str, match: re.Match, lang: str = DEFAULT) -> str:
    """Vorlage fuellen; eingesetzte Werte, die selbst im Katalog stehen (z. B. Bereichs- oder Seitennamen), mit uebersetzen."""
    groups = {k: _exact(v, lang) if v else v for k, v in match.groupdict().items()}
    return _PLACEHOLDER.sub(lambda m: groups.get(f"g{m.group(1)}", m.group(0)), template)


def _exact(text: str, lang: str) -> str:
    """Nur exakte Katalogtreffer (keine Vorlagen) - fuer eingesetzte Werte; Unbekanntes (Daten) bleibt unveraendert."""
    german = text if text in _entries else _reverse.get(text)
    if german is None:
        return text
    return german if lang == DEFAULT else (_entries.get(german, {}).get(lang) or german)


def _user_glossary_file() -> Path:
    return config_dir() / "glossary_user.json"


def glossary_rows() -> list[dict]:
    """Sprachtabelle der Fachbegriffe: ``de, en, fr, status, hinweis`` (Benutzeraenderungen ueberlagern die Auslieferung)."""
    try:
        rows = json.loads(_GLOSSARY.read_text(encoding="utf-8")).get("Begriffe", [])
    except (OSError, ValueError):
        rows = []
    try:
        user = json.loads(_user_glossary_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        user = {}
    merged = []
    for row in rows:
        row = dict(row)
        row.update(user.get(row["de"], {}))
        merged.append(row)
    return merged


def set_term(german: str, en: str, fr: str, status: str = "geklärt", note: str = "") -> None:
    """Begriff in der Benutzer-Sprachtabelle ablegen (wirkt sofort, bleibt ueber Updates erhalten)."""
    try:
        user = json.loads(_user_glossary_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        user = {}
    entry = {"en": en, "fr": fr, "status": status}
    if note:
        entry["hinweis"] = note
    user[german] = entry
    try:
        _user_glossary_file().write_text(json.dumps(user, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    reload()


def reload() -> None:
    _state["loaded"] = False
    _entries.clear()
    _templates.clear()
    _reverse.clear()
    _load()


def _add(german: str, translations: dict[str, str]) -> None:
    translations = {k: v for k, v in translations.items() if v}
    if _PLACEHOLDER.search(german):
        _templates.append((german, translations))
    else:
        _entries.setdefault(german, {}).update(translations)


def _load() -> None:
    if _state["loaded"]:
        return
    _state["loaded"] = True
    for path in sorted(_DIR.glob("catalog*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for section, items in data.items():
            if section.startswith("_") or not isinstance(items, dict):
                continue
            for german, translations in items.items():
                _add(german, translations)
    for row in glossary_rows():                       # Fachbegriffe gelten vor dem allgemeinen Katalog
        _add(row["de"], {"en": row.get("en", ""), "fr": row.get("fr", "")})
    for german, translations in _entries.items():
        for text in translations.values():
            _reverse.setdefault(text, german)


def language() -> str:
    return _state["lang"]


def _translate_line(text: str, lang: str) -> str:
    if text in _entries:
        german = text
    elif text in _reverse:
        german = _reverse[text]
    else:
        german = None
    if german is not None:
        return german if lang == DEFAULT else (_entries.get(german, {}).get(lang) or german)
    for source, translations in _templates:             # Vorlage in Deutsch oder einer Zielsprache erkennen
        for candidate in (source, *translations.values()):
            m = _compile(candidate).match(text)
            if m:
                target = source if lang == DEFAULT else (translations.get(lang) or source)
                return _fill(target, m, lang)
    m = _AFFIX.match(text)                               # Zeichen davor/dahinter (z. B. "›   Hilfstabellen", "Verwaltung  ▾")
    if m and (m.group(1) or m.group(3)) and m.group(2):
        core = _exact(m.group(2), lang)
        if core != m.group(2) or m.group(2) in _entries:
            return m.group(1) + core + m.group(3)
    return text


def tr(text: str, lang: str | None = None) -> str:
    """Uebersetzt einen (deutschen oder bereits uebersetzten) Text; unbekannte Texte bleiben unveraendert.

    Texte mit Platzhaltern ({0}) werden ueber Vorlagen gefunden, mehrzeilige Texte zeilenweise uebersetzt."""
    _load()
    if not text or not any(c.isalpha() for c in text):
        return text
    lang = lang or _state["lang"]
    escaped = "&&" in text
    key = text.replace("&&", "&")
    result = _translate_line(key, lang)
    if result == key and "\n" in key:
        result = "\n".join(_translate_line(line, lang) if line.strip() else line for line in key.split("\n"))
    if lang != DEFAULT and result == key:
        if key not in _entries and key not in _reverse and not any(_compile(s).match(key) for s, _t in _templates)                 and not _covered_by_affix(key):
            _missed.add(key)
    return result.replace("&", "&&") if escaped else result


def _covered_by_affix(text: str) -> bool:
    m = _AFFIX.match(text)
    return bool(m and (m.group(1) or m.group(3)) and m.group(2) and (m.group(2) in _entries or m.group(2) in _reverse))


def untranslated() -> list[str]:
    """Texte, die zur Laufzeit ohne Uebersetzung geblieben sind (Diagnose fuer die Sprachtabelle)."""
    return sorted(_missed)


# ---------------------------------------------------------------- Persistenz
def _state_file() -> Path:
    return config_dir() / "state.json"


def saved_language() -> str:
    try:
        lang = json.loads(_state_file().read_text(encoding="utf-8")).get("language", DEFAULT)
    except (OSError, ValueError):
        return DEFAULT
    return lang if lang in LANGUAGES else DEFAULT


def _save_language(lang: str) -> None:
    try:
        try:
            data = json.loads(_state_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        data["language"] = lang
        _state_file().write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------- Widgets
def _set(widget, getter: str, setter: str, lang: str) -> None:
    text = getattr(widget, getter)()
    if isinstance(text, str) and text and not text.lstrip().startswith("<"):
        new = tr(text, lang)
        if new != text:
            getattr(widget, setter)(new)


def translate_widget(widget: QWidget, lang: str | None = None) -> None:
    """Uebersetzt ein Widget und alle darunter liegenden Widgets."""
    lang = lang or _state["lang"]
    try:
        widgets = [widget, *widget.findChildren(QWidget)]
    except RuntimeError:
        return
    for w in widgets:
        try:
            _translate_one(w, lang)
        except RuntimeError:
            continue


def _translate_one(w: QWidget, lang: str) -> None:
    if True:
        if isinstance(w, QComboBox):
            return                                      # Eintraege sind Daten (Code vergleicht sie mit deutschen Konstanten)
        if isinstance(w, QLabel):
            _set(w, "text", "setText", lang)
        elif isinstance(w, QAbstractButton):
            _set(w, "text", "setText", lang)
        elif isinstance(w, QGroupBox):
            _set(w, "title", "setTitle", lang)
        elif isinstance(w, QLineEdit):
            _set(w, "placeholderText", "setPlaceholderText", lang)
        elif isinstance(w, QTabBar):
            for i in range(w.count()):
                new = tr(w.tabText(i), lang)
                if new != w.tabText(i):
                    w.setTabText(i, new)
        elif isinstance(w, QTableWidget):
            for c in range(w.columnCount()):
                item = w.horizontalHeaderItem(c)
                if item is not None:
                    new = tr(item.text(), lang)
                    if new != item.text():
                        item.setText(new)
        if w.toolTip():
            new = tr(w.toolTip(), lang)
            if new != w.toolTip():
                w.setToolTip(new)
        if w.isWindow() and w.windowTitle():
            new = tr(w.windowTitle(), lang)
            if new != w.windowTitle():
                w.setWindowTitle(new)
        for action in w.actions():
            _translate_action(action, lang)
        if isinstance(w, (QToolButton, QPushButton)) and w.menu() is not None:
            _translate_menu(w.menu(), lang)             # Menues ohne Eltern-Widget werden von findChildren nicht erfasst
        elif isinstance(w, QMenu):
            _translate_menu(w, lang)


def _translate_menu(menu: QMenu, lang: str) -> None:
    """Eintraege eines Menues samt Untermenues (Untermenues sind Kinder des Menues, siehe ``QMenu.addMenu``)."""
    try:
        for action in menu.actions():
            _translate_action(action, lang)
        for sub in menu.findChildren(QMenu):
            for action in sub.actions():
                _translate_action(action, lang)
    except RuntimeError:
        pass


def _translate_action(action: QAction, lang: str) -> None:
    try:
        _translate_action_unsafe(action, lang)
    except RuntimeError:                                # C++-Objekt schon geloescht (Fenster im Abbau)
        pass


def _translate_action_unsafe(action: QAction, lang: str) -> None:
    # Kein ``action.menu()``: unter PySide6 6.11 loescht das Freigeben des Action-Wrappers danach das Menue samt Eintraegen
    # (Export-Menue war nach dem Sprachwechsel weg). Untermenues uebersetzt ``_translate_menu``.
    if action.property("i18n_skip"):                    # z. B. Sprachnamen im Sprachmenue bleiben in ihrer eigenen Sprache
        return
    new = tr(action.text(), lang)
    if new != action.text():
        action.setText(new)


class _Filter(QObject):
    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() == QEvent.Show and isinstance(obj, QWidget):
            current, previous = _state["lang"], obj.property("_i18n_lang")
            if previous != current and (current != DEFAULT or previous is not None):
                obj.setProperty("_i18n_lang", current)
                translate_widget(obj)
        return False


_filter: _Filter | None = None


def install(app: QApplication, lang: str | None = None) -> None:
    """Sprache setzen (Standard: gespeicherte Wahl) und den Uebersetzungsfilter installieren."""
    global _filter
    _load()
    _state["lang"] = lang if lang in LANGUAGES else saved_language()
    if _filter is None:
        _filter = _Filter(app)
        app.installEventFilter(_filter)


def set_language(lang: str, app: QApplication | None = None) -> None:
    """Sprache sofort fuer alle offenen Fenster wechseln und merken."""
    if lang not in LANGUAGES:
        return
    _load()
    _state["lang"] = lang
    _save_language(lang)
    app = app or QApplication.instance()
    if app is None:
        return
    if _filter is None:
        install(app, lang)
    for top in app.topLevelWidgets():
        top.setProperty("_i18n_lang", lang)
        translate_widget(top, lang)
        for child in top.findChildren(QWidget):
            child.setProperty("_i18n_lang", lang)
