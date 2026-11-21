"""Einstiegspunkt fuer die EXE (PyInstaller) - startet den P3D PDF Reader wie ``python -m p3d_pdfreader``."""
from p3d_pdfreader.app import main

if __name__ == "__main__":
    raise SystemExit(main())
