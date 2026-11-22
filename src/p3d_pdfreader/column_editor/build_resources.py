"""Compile qml.qrc into qml_resources.py (decision D7: the QML files live inside the program, not next to it).

Part of the column_editor package, so any application that embeds the tile editor can rebuild the resources itself:
    python -m column_editor.build_resources
P3D - Tag Compliance keeps `build_qml_resources.py` in the project root; it only calls `main()` of this module
(qa_release.bat runs it before the quality gate). Uses the rcc of the installed PySide6, so the resource module always
matches the Qt version that runs it.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
QRC = HERE / "qml.qrc"
OUT = HERE / "qml_resources.py"


def main(qrc: Path | None = None, out: Path | None = None) -> int:
    qrc, out = Path(qrc or QRC), Path(out or OUT)
    from PySide6.scripts.pyside_tool import rcc
    if not qrc.is_file():
        print(f"[ERROR] {qrc} not found")
        return 1
    # --no-compress: the QML files are tiny, and a compressed resource (rcc 6.12 uses zstd by default, 6.11 used zlib) can be
    # found by QFile.exists() but fail with "Input/output error" when the running Qt build cannot decompress it.
    sys.argv = ["pyside6-rcc", "--no-compress", str(qrc), "-o", str(out)]
    try:
        rcc()                                  # the PySide6 wrapper ends with sys.exit(<rcc exit code>)
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"[ERROR] rcc failed (exit code {e.code})")
            return int(e.code) if isinstance(e.code, int) else 1
    if not out.is_file() or out.stat().st_size == 0:
        print("[ERROR] rcc produced no output")
        return 1
    print(f"OK: {out.name} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
