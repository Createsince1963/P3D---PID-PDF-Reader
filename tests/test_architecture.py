"""Architekturregeln: Kern ohne Qt, Launcher ohne Kernlogik, keine festen A:-Pfade, Kit unveraendert eingebunden."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "p3d_pdfreader"


def _imports(path: Path) -> list[str]:
    return re.findall(r"^\s*(?:from|import)\s+([\w.]+)", path.read_text(encoding="utf-8"), re.M)


def test_core_without_qt():
    for py in (SRC / "core").glob("*.py"):
        assert not [m for m in _imports(py) if m.startswith("PySide6")], py.name


def test_launcher_without_core_logic():
    mods = _imports(ROOT / "Launcher" / "launcher_gui.py")
    assert not [m for m in mods if m.startswith("p3d_pdfreader.core")]


def test_no_fixed_subst_drive():
    for py in list(SRC.rglob("*.py")) + list((ROOT / "Launcher").glob("*.py")):
        assert not re.search(r"['\"]A:\\\\", py.read_text(encoding="utf-8")), py.name
