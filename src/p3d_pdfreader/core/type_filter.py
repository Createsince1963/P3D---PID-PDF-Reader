"""Prueftypen (1.0.58): Vorfilter fuer die gesamte Pruefung - nicht gewaehlte Tag-Typen erscheinen in keiner Tabelle,
Markierung und Ausgabe. Gemerkt werden die **abgewaehlten** Typen (``state.json``), damit neue Typen (eigene Muster)
mitgeprueft werden. Wirkt nur in dem Prozess, der ``activate`` aufruft (Desktop-App; der Web-Server prueft alles).
Ohne Qt."""
from __future__ import annotations

STATE_KEY = "check_types_excluded"      # config/state.json
_excluded: frozenset[str] = frozenset()


def activate(excluded) -> None:
    global _excluded
    _excluded = frozenset(str(t) for t in (excluded or []))


def excluded() -> frozenset[str]:
    return _excluded


def apply(tags) -> list:
    """Nur die Tags der gewaehlten Prueftypen."""
    return [t for t in tags if t.type not in _excluded] if _excluded else list(tags)


def dropped(tags) -> list:
    """Die abgewaehlten Tags (z. B. damit ihre Importzeilen nicht als „fehlt im PDF“ gelten)."""
    return [t for t in tags if t.type in _excluded] if _excluded else []
