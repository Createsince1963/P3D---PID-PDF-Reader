"""Dictionary-based i18n ({key: {"DE":..., "EN":...}}, T(key), set_lang()).

Carried over into main_gui_kit unchanged. GUI strings are English by default
(GUI-Vorgabe); the translation table stays available for later use.
"""
from __future__ import annotations

from typing import Dict

_STRINGS: Dict[str, Dict[str, str]] = {}
_LANG: str = "EN"


def register(entries: Dict[str, Dict[str, str]]) -> None:
    _STRINGS.update(entries)


def set_lang(code: str) -> None:
    global _LANG
    _LANG = code.upper()


def get_lang() -> str:
    return _LANG


def T(key: str) -> str:
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_LANG) or entry.get("EN") or key
