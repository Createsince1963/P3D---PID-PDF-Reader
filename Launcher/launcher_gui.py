"""Launcher GUI for P3D PDF Reader (source: P3D InstrumentationList launcher, names and paths adapted only).

Rebuild of the launcher of P3D XCHANGE (itself a rebuild of the "P3D - Tag Compliance" launcher), adapted to this tool:
one workspace, start of the application (``python -m p3d_pdfreader``), start of the built EXE, checks (environment, tests), EXE build (``build_exe.bat``),
folders, portable copy (USB / company laptop) and the Windows mobile hotspot.

Standalone: imports only ``main_gui_kit`` (theme, buttons) and ``hotspot`` from this folder - no core logic, so the
launcher starts even when the application has a problem. No own colours: every colour is a token of the kit palette.
Launcher texts are English (owner 2026-11-16), like the launcher it is rebuilt from.
"""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QProcess, QProcessEnvironment, QRectF, QSettings, QSize, Qt, QThread, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                    # workspace of the module (resolve(): subst drive -> C:)
for _p in (ROOT, ROOT / "src", HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
from main_gui_kit.buttons import ButtonKind, action_button  # noqa: E402  (ROOT must be on sys.path first)
from main_gui_kit.theme import ThemeManager  # noqa: E402
from main_gui_kit.widgets import page_title  # noqa: E402
import hotspot as HS  # noqa: E402  (Windows mobile hotspot via PowerShell, standard library only)

ORG, APP = "TBK", "P3D PDF Reader Launcher"
PRODUCT = "P3D PDF Reader"
LAUNCHER_TITLE = f"{PRODUCT} - Launcher"
PACKAGE = "p3d_pdfreader"                             # started like start_pdf_reader.bat: python -m p3d_pdfreader
ENV_PYTHON = "P3D_PDFREADER_PYTHON"                     # optional: another python.exe for the launcher and its jobs
COMPANY_PYTHON = Path(r"C:\Program Files\Python314\python.exe")   # company PC default; used when the central Python is absent
COMPANY_FILE = HERE / "python_company.txt"           # company-PC python.exe set in the launcher; START_LAUNCHER.bat reads it too
CENTRAL_PYTHON = ROOT.parent.parent / "Tools_Central" / "Python" / "python" / "python.exe"   # development PC
ENV_HOME = "P3D_PDFREADER_HOME"                      # data folder of the EXE (see p3d_pdfreader/paths.py)
EXE_NAME = "P3D_PDF_Reader.exe"
EXE_FOLDER = "P3D_PDF_Reader"             # onedir build: dist\P3D_PDF_Reader\
WEB_PACKAGE = f"{PACKAGE}.web"                       # web server: python -m p3d_pdfreader.web --host ... --port ...
WEB_PORT = "8765"
# Portable copy = only the files needed to RUN the program, plus this launcher: the .py files of src and main_gui_kit,
# the runtime data the program loads (src\p3d_pdfreader\assets: icons), the launcher folder (.py + .bat +
# python_company.txt), requirements.txt, start_pdf_reader.bat, README.md (manual) and VERSION. Everything else stays out:
# data (sources, reviews, exports, logs of this PC), tests, build files (build_exe, run_p3d_pdfreader.py), tools.
PORTABLE_INCLUDE = ("src", "main_gui_kit", HERE.name, "requirements.txt", "start_pdf_reader.bat", "start_web_server.bat",
                    "README.md", "VERSION")
PORTABLE_SKIP_DIRS = {"__pycache__", ".pytest_cache", ".pytest_tmp"}


def _portable_file(rel: Path) -> bool:
    """True if the file `rel` (relative to the workspace) belongs into the portable copy."""
    if len(rel.parts) == 1:
        return True
    top = rel.parts[0]
    if top == HERE.name:
        return rel.suffix.lower() in (".py", ".bat") or rel.name == COMPANY_FILE.name
    if "assets" in rel.parts:
        return rel.name != "README.md"
    return rel.suffix.lower() == ".py"                # src, main_gui_kit


REQUIRED_PACKAGES = ("PySide6", "openpyxl", "PyMuPDF")   # same as requirements.txt
MIN_PYTHON = "3.10"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
PAL = ThemeManager._PALETTES["LIGHT"]                 # kit palette + accent of the application: the only colour sources
ACCENT = "#0F5EA8"                                    # primary buttons / icons: same blue as the P3D XCHANGE launcher

ENV_CHECK = f"""
import sys, importlib.metadata as m
ok = sys.version_info >= tuple(int(x) for x in "{MIN_PYTHON}".split("."))
print("Python", sys.version.split()[0], "-", sys.executable, "" if ok else "  [ERROR] at least {MIN_PYTHON} needed")
for p in sys.argv[1:]:
    optional = p.startswith("?")
    p = p.lstrip("?")
    try:
        print("  [OK]     ", p, m.version(p))
    except Exception:
        print("  [missing]" if optional else "  [ERROR]  ", p, "(only needed for the tests)" if optional else "not installed")
        ok = ok and optional
print("Environment is fine." if ok else "Environment is NOT fine - see requirements.txt.")
raise SystemExit(0 if ok else 1)
"""


def _company_python() -> Path:
    """Python of the company PC: the path saved by the launcher (python_company.txt), else the standard installation."""
    try:
        text = COMPANY_FILE.read_text(encoding="utf-8").strip().strip('"')
    except OSError:
        text = ""
    return Path(text) if text else COMPANY_PYTHON


def _default_python() -> Path:
    """Like start_pdf_reader.bat: the central Python next to the workspace; else the Python the launcher runs with."""
    override = os.environ.get(ENV_PYTHON, "").strip()
    if override and Path(override).is_file():
        return Path(override)
    if CENTRAL_PYTHON.is_file():
        return CENTRAL_PYTHON
    if _company_python().is_file():                   # copy on the company PC / USB stick: no Tools_Central there
        return _company_python()
    return Path(sys.executable)


def _decode(data: bytes) -> str:
    """Output of a job: Python writes UTF-8 (PYTHONUTF8), cmd.exe itself the console code page."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("oem" if sys.platform == "win32" else "latin-1", errors="replace")
    return text.rstrip()


def _version_of(root: Path) -> str:
    """Version of a source tree: DISPLAY_VERSION from the source (no import), else the VERSION file."""
    try:
        match = re.search(r'^DISPLAY_VERSION\s*=\s*"([^"]+)"', (root / "src" / PACKAGE / "__init__.py").read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    except OSError:
        pass
    try:
        return (root / "VERSION").read_text(encoding="utf-8").strip() or "?"
    except OSError:
        return "?"


# ---- versions from the git history: every DISPLAY_VERSION a commit set ------------------------------------------------
GIT_MARK = "\x01"                                     # marks a commit line in the git log output


def _version_key(text: str) -> tuple[int, ...]:
    """Sort key of a version or a folder name like v0.7.0 / v0.703: its numbers (0.710 > 0.703 > 0.7.0 > 0.6.0)."""
    return tuple(int(n) for n in re.findall(r"\d+", text))


def _git_versions(root: Path = ROOT) -> dict[str, tuple[str, str]]:
    """{version: (commit, date)} for every DISPLAY_VERSION in the git history, the newest commit per version.
    Empty without git or repository (portable copy, company PC) - the launcher then shows the folders only."""
    init = f"src/{PACKAGE}/__init__.py"
    try:
        out = subprocess.run(["git", "log", "-p", "-G", "^DISPLAY_VERSION", f"--format={GIT_MARK}%h %cs", "--", init],
                             cwd=str(root), capture_output=True, timeout=30, creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return {}
    if out.returncode != 0:
        return {}
    found: dict[str, tuple[str, str]] = {}
    commit = date = ""
    for line in out.stdout.decode("utf-8", errors="replace").splitlines():
        if line.startswith(GIT_MARK):
            commit, _, date = line[1:].partition(" ")
        elif commit:
            match = re.match(r'\+DISPLAY_VERSION\s*=\s*"([^"]+)"', line)
            if match:
                found.setdefault(match.group(1), (commit, date))   # log runs newest first
    return found


def _extract_git_version(commit: str, dest: Path, root: Path = ROOT) -> None:
    """Writes the files of `commit` to `dest` (versions\\v<version>\\source) with git archive. Extracted into
    <dest>.part first and renamed at the end, so an aborted extraction never looks like a complete version."""
    out = subprocess.run(["git", "archive", "--format=tar", commit], cwd=str(root), capture_output=True, timeout=300,
                         creationflags=NO_WINDOW)
    if out.returncode != 0:
        raise RuntimeError(_decode(out.stderr) or f"git archive exit code {out.returncode}")
    part = dest.with_name(dest.name + ".part")
    if part.exists():
        shutil.rmtree(part)
    part.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(out.stdout)) as tar:
        try:
            tar.extractall(part, filter="data")         # Python 3.12+: no paths outside the target
        except TypeError:
            tar.extractall(part)
    part.rename(dest)


# ---- small line icons for the buttons (as in the Tag Compliance launcher), drawn in a palette colour ----------------
def _draw_icon(p: QPainter, name: str) -> None:           # coordinates in a 14 x 14 box
    if name == "run":
        p.drawPolygon(QPolygonF([QPointF(4, 2.5), QPointF(11.5, 7), QPointF(4, 11.5)]))
    elif name == "ok":
        p.drawPolyline(QPolygonF([QPointF(2.5, 7.5), QPointF(5.5, 10.5), QPointF(11.5, 3.5)]))
    elif name == "folder":
        p.drawPolyline(QPolygonF([QPointF(1.5, 11.5), QPointF(1.5, 3), QPointF(5.5, 3), QPointF(7, 4.5), QPointF(12.5, 4.5),
                                  QPointF(12.5, 11.5), QPointF(1.5, 11.5)]))
    elif name == "refresh":
        p.drawArc(QRectF(2.5, 2.5, 9, 9), 60 * 16, 270 * 16)
        p.drawPolyline(QPolygonF([QPointF(8.5, 1), QPointF(9.6, 3.3), QPointF(7.2, 4.2)]))
    elif name == "copy":
        p.drawRect(QRectF(4.5, 4.5, 8, 8))
        p.drawPolyline(QPolygonF([QPointF(2, 9.5), QPointF(2, 1.5), QPointF(9.5, 1.5)]))
    elif name == "new":
        p.drawLine(QPointF(7, 2.5), QPointF(7, 11.5))
        p.drawLine(QPointF(2.5, 7), QPointF(11.5, 7))


def _icon(name: str, on_colour: bool) -> QIcon:
    scale = 3
    pixmap = QPixmap(14 * scale, 14 * scale)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(scale, scale)
    pen = QPen(QColor(Qt.white) if on_colour else QColor(ACCENT), 1.3)
    pen.setJoinStyle(Qt.RoundJoin)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    _draw_icon(painter, name)
    painter.end()
    return QIcon(pixmap)


def _button(text: str, kind: ButtonKind = ButtonKind.NEUTRAL, tip: str = "", icon: str = "", expand: bool = True) -> QPushButton:
    button = action_button(text, kind)
    button.setSizePolicy(QSizePolicy.Expanding if expand else QSizePolicy.Fixed, QSizePolicy.Fixed)
    if icon:
        button.setIcon(_icon(icon, kind is not ButtonKind.NEUTRAL))
        button.setIconSize(QSize(14, 14))
    if tip:
        button.setToolTip(tip)
    return button


def _muted(text: str = "", wrap: bool = False) -> QLabel:
    label = QLabel(text)
    label.setProperty("role", "muted")
    label.setWordWrap(wrap)
    return label


class SidePanel(QWidget):
    """Content of the scrolling side panel. Its minimum height follows the real height of the cards at the current width
    (word-wrapped status texts change it), so the scroll area scrolls instead of squeezing cards into each other."""

    def _fit(self) -> None:
        lay = self.layout()
        if lay is not None:
            need = lay.totalHeightForWidth(self.width()) if lay.hasHeightForWidth() else lay.totalMinimumSize().height()
            if need != self.minimumHeight():
                self.setMinimumHeight(need)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit()

    def event(self, e) -> bool:
        if e.type() == e.Type.LayoutRequest:
            self._fit()
        return super().event(e)


class FuncWorker(QObject):
    """Runs one blocking call (e.g. a PowerShell hotspot command, several seconds) in a background thread."""
    finished = Signal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self) -> None:
        try:
            result = self.fn()
        except Exception as e:  # noqa: BLE001 - reported in the log, the launcher keeps running
            result = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        self.finished.emit(result)


class CopyWorker(QObject):
    """Portable copy in a background thread. A file that already exists on the target is only replaced when the workspace
    file is NEWER; same age or a newer file on the target is kept. Copying again therefore only writes what changed."""
    progress = Signal(int, int, int, int)     # bytes done, bytes total, files done, files total
    fileCopied = Signal(str)
    finished = Signal(dict)

    def __init__(self, src: Path, dest: Path, python: Path | None = None, company: str = ""):
        super().__init__()
        self.src, self.dest, self.python = src, dest, python
        self.company = company.strip().strip('"')         # Firmen-PC-Python -> Ziel\Launcher\python_company.txt
        self._cancel = False

    def _write_company(self) -> str:
        """Firmen-PC-Pfad immer in die Kopie schreiben: START_LAUNCHER.bat und start_pdf_reader.bat der Kopie nutzen ihn,
        wenn dort kein Tools_Central existiert (Firmen-PC / USB)."""
        if not self.company:
            return ""
        target = self.dest / HERE.name / COMPANY_FILE.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.company + "\n", encoding="utf-8")
        return str(target)

    def cancel(self) -> None:
        self._cancel = True

    def _files(self) -> list[tuple[Path, int]]:
        out = []
        for name in PORTABLE_INCLUDE:
            top = self.src / name
            if top.is_file():
                out.append((top, top.stat().st_size))
                continue
            for folder, dirs, names in os.walk(top):
                dirs[:] = [d for d in dirs if d not in PORTABLE_SKIP_DIRS]
                for n in names:
                    p = Path(folder) / n
                    if not _portable_file(p.relative_to(self.src)):
                        continue
                    try:
                        out.append((p, p.stat().st_size))
                    except OSError:
                        continue
        return out

    def run(self) -> None:
        summary = {"copied": 0, "skipped": 0, "target_newer": [], "failed": [], "bytes": 0, "cancelled": False, "error": ""}
        try:
            files = self._files()
            total_b, total_n = sum(s for _, s in files) or 1, len(files)
            done_b = 0
            self.progress.emit(0, total_b, 0, total_n)
            for i, (p, size) in enumerate(files, start=1):
                if self._cancel:
                    summary["cancelled"] = True
                    break
                rel = p.relative_to(self.src)
                target = self.dest / rel
                try:
                    st = p.stat()
                    if target.is_file():
                        tt = target.stat()
                        if st.st_mtime <= tt.st_mtime + 2:      # same age or older (2 s = FAT / USB time steps): keep it
                            summary["skipped"] += 1
                            if st.st_mtime < tt.st_mtime - 2:
                                summary["target_newer"].append(str(rel))
                            done_b += size
                            self.progress.emit(done_b, total_b, i, total_n)
                            continue
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, target)
                    summary["copied"] += 1
                    summary["bytes"] += size
                    self.fileCopied.emit(str(rel))
                except OSError as error:
                    summary["failed"].append((str(rel), str(error)))
                done_b += size
                self.progress.emit(done_b, total_b, i, total_n)
        except Exception as error:  # noqa: BLE001 - reported to the user, the launcher keeps running
            summary["error"] = f"{type(error).__name__}: {error}"
        if not summary["cancelled"] and not summary["error"]:
            try:
                summary["install"] = self._write_install()
            except OSError as error:
                summary["failed"].append(("INSTALL.txt", str(error)))
            try:
                written = self._write_company()
                if written:
                    self.fileCopied.emit(f"{HERE.name}\\{COMPANY_FILE.name}  (Firmen-PC-Python: {self.company})")
            except OSError as error:
                summary["failed"].append((COMPANY_FILE.name, str(error)))
        self.finished.emit(summary)

    def _python_version(self) -> str:
        if self.python is None or not self.python.is_file():
            return ""
        try:
            return subprocess.run([str(self.python), "-c", "import sys; print(sys.version.split()[0])"], capture_output=True,
                                  text=True, timeout=60, creationflags=NO_WINDOW).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    def _write_install(self) -> str:
        """INSTALL.txt in the copy (text only, no install script). requirements.txt is copied from the project."""
        self.dest.mkdir(parents=True, exist_ok=True)
        py = self._python_version()
        version = _version_of(self.src)
        text = f"""{PRODUCT} {version} - running this copy on another computer
=====================================================================

What is needed
  * Python {py or MIN_PYTHON + ' or newer'} (64-bit; minimum {MIN_PYTHON}) - an installed Python or a portable WinPython.
  * The packages in requirements.txt: {", ".join(REQUIRED_PACKAGES)}.

Install the packages (once) - in a command prompt in THIS folder:
  "<path to>\\python.exe" -m pip install -r requirements.txt

Without internet (company network): download the packages on a computer with internet
  python -m pip download -r requirements.txt -d wheels
copy the "wheels" folder here and install from it:
  "<path to>\\python.exe" -m pip install --no-index --find-links wheels -r requirements.txt

Start the app (command prompt in THIS folder):
  set PYTHONPATH=src;.
  "<path to>\\python.exe" -m {PACKAGE}
  start_pdf_reader.bat uses the central Python (..\\..\\Tools_Central\\Python\\python\\python.exe) if present,
  else the company-PC Python from {HERE.name}\\python_company.txt (set in the launcher, copied with the project).

Launcher of this copy (start, environment check, folders, hotspot):
  "<path to>\\python.exe" {HERE.name}\\launcher_gui.py
  ({HERE.name}\\START_LAUNCHER.bat does the same. Without Tools_Central it and the launcher use
   {COMPANY_PYTHON}; any other python.exe: set P3D_PDFREADER_PYTHON.)
  Tests and the EXE build are not part of this copy - those launcher buttons only work in the full workspace.

Settings, mapping, licence/access and logs are created by the app in the subfolders "config" and "logs" of this copy.
Licence/access (security.sqlite) is not copied: set it up on the new computer in the Administrator area.

Not in this copy on purpose: project data (Input, Export List, Output), tests, tools, build files.
"""
        (self.dest / "INSTALL.txt").write_text(text, encoding="utf-8")
        return f"Python {py or '?'}"


class LauncherWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(LAUNCHER_TITLE)
        self.setMinimumSize(1000, 640)
        self.resize(1180, 760)
        # Additions to the kit stylesheet, palette tokens only: white cards, muted captions, transparent labels on cards,
        # dark "secondary" button (Start EXE) as in the Tag Compliance launcher, thin progress line.
        self.setStyleSheet(
            f"QFrame#Card {{ background: {PAL.card}; border: 1px solid {PAL.border}; border-radius: 6px; }} "
            "QLabel, QCheckBox { background: transparent; } "
            f'QLabel[role="muted"] {{ color: {PAL.txt_muted}; }} '
            "QScrollArea, QWidget#Side { background: transparent; } "
            f'QPushButton[kind="primary"] {{ background: {ACCENT}; }} '
            f'QPushButton[kind="primary"]:hover {{ background: {QColor(ACCENT).darker(115).name()}; }} '
            f'QPushButton[kind="secondary"] {{ background: {PAL.secondary}; }} '
            f'QPushButton[kind="secondary"]:hover {{ background: {QColor(PAL.secondary).lighter(130).name()}; }} '
            f"QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }} "
            f"QCheckBox::indicator:unchecked {{ width: 13px; height: 13px; border: 1px solid {PAL.txt_muted}; "
            f"border-radius: 3px; background: {PAL.card}; }} "
            f"QProgressBar {{ background: {PAL.border}; border: none; border-radius: 1px; }} "
            f"QProgressBar::chunk {{ background: {ACCENT}; border-radius: 1px; }}")
        self.process: QProcess | None = None            # checks / build: one job at a time, captured into the log
        self.gui_process: QProcess | None = None        # the application started from this launcher
        self.portable_process: QProcess | None = None   # the application started from a portable copy
        self.web_process: QProcess | None = None        # web server (python -m p3d_pdfreader.web), output in the log
        self.copy_thread: QThread | None = None
        self.copy_worker: CopyWorker | None = None
        self._copy_dest: Path | None = None
        self._hs_thread: QThread | None = None
        self._hs_worker: FuncWorker | None = None
        self._hs_label = ""
        self._build()
        self._load_settings()
        self._log(f"{LAUNCHER_TITLE} ready. Workspace: {ROOT}")

    # ---- UI ---------------------------------------------------------------------------------------
    def _build(self) -> None:
        outer = QHBoxLayout(self)
        left = SidePanel()
        left.setObjectName("Side")
        side = QVBoxLayout(left)
        left_scroll = QScrollArea()                      # the side panel scrolls instead of squeezing its cards
        left_scroll.setWidget(left)
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setMinimumWidth(420)
        left_scroll.setMaximumWidth(460)
        side.addWidget(page_title(PRODUCT))
        side.addWidget(_muted("Launcher: start, checks, build, folders, portable copy, hotspot"))

        self.python = QLineEdit(str(CENTRAL_PYTHON))
        self.python.setToolTip("Development PC: python.exe with PySide6, openpyxl and PyMuPDF (Tools_Central). Used for Start GUI, the "
                               "checks and the portable copy while it exists. The EXE build uses its own environment (.venv_build).")
        browse = _button("Browse ...", tip="Choose another python.exe (development PC)", icon="folder", expand=False)
        browse.clicked.connect(lambda: self._browse_python(self.python))
        self.python_company = QLineEdit(str(_company_python()))
        self.python_company.setToolTip("Company PC: python.exe used when the development Python above does not exist on this PC. "
                                       "Saved to Launcher\\python_company.txt - START_LAUNCHER.bat uses it as well.")
        self.python_company.editingFinished.connect(self._save_settings)
        browse_company = _button("Browse ...", tip="Choose the python.exe of the company PC", icon="folder", expand=False)
        browse_company.clicked.connect(lambda: self._browse_python(self.python_company))
        python_grid = QGridLayout()
        python_grid.setHorizontalSpacing(6)
        python_grid.setVerticalSpacing(4)
        python_grid.addWidget(QLabel("Development"), 0, 0)
        python_grid.addWidget(self.python, 0, 1)
        python_grid.addWidget(browse, 0, 2)
        python_grid.addWidget(QLabel("Company PC"), 1, 0)
        python_grid.addWidget(self.python_company, 1, 1)
        python_grid.addWidget(browse_company, 1, 2)
        python_grid.setColumnStretch(1, 1)
        python_row = QVBoxLayout()
        python_row.addLayout(python_grid)
        side.addWidget(self._card("Python runtime (start, checks, copy)", python_row))

        self.version_combo = QComboBox()
        self.version_combo.setToolTip("Version used by Start GUI. 'Current workspace' = this folder as it is. Versions "
                                      "marked 'git' come from the git history and are extracted to "
                                      "versions\\v<version>\\source on their first start. A version from "
                                      "versions\\ is started from its own folder and keeps its own config in "
                                      "its folder - the config of the workspace is not touched.")
        b_refresh = _button("Refresh", tip="Read the version list again (workspace, folder versions\\, git history)", icon="refresh", expand=False)
        b_refresh.clicked.connect(self._refresh_versions)
        version_row = QHBoxLayout()
        version_row.addWidget(self.version_combo, 1)
        version_row.addWidget(b_refresh)
        side.addWidget(self._card("App version (for Start GUI)", version_row))
        self._refresh_versions()

        start = QVBoxLayout()
        b_start = _button("Start GUI ...", ButtonKind.PRIMARY,
                          f"python -m {PACKAGE} (like start_pdf_reader.bat); its console output streams into the log", "run")
        b_start.clicked.connect(self._start_gui)
        b_exe = _button("Start EXE", ButtonKind.SECONDARY, f"build_exe\\dist\\{EXE_NAME}, if it was built", "run")
        b_exe.clicked.connect(self._start_exe)
        start.addWidget(b_start)
        start.addWidget(b_exe)
        side.addWidget(self._card("Start", start))
        side.addWidget(self._card("Web server (browser access, company network)", self._web_card()))

        side.addWidget(self._card("Quality gate", self._grid((
            ("Check environment", self._check_env, "ok"),
            ("Show version (--version)", lambda: self._run_python(["-m", PACKAGE, "--version"], "Version"), ""),
            ("Tests (fast, without GUI)", lambda: self._run_tests(["tests/test_architecture.py", "tests/test_extract.py"], "Tests (fast)"), ""),
            ("Tests (full)", lambda: self._run_tests(["tests"], "Tests (full)"), ""),
        ))))

        side.addWidget(self._card("Build", self._grid((
            ("Build Onefile EXE ...", lambda: self._run_build([], "Build Onefile EXE"), ""),
            ("Build Onedir EXE ...", lambda: self._run_build(["onedir"], "Build Onedir EXE"), ""),
        ))))

        side.addWidget(self._card("Folders", self._grid((
            ("Open workspace", lambda: self._open(ROOT), "folder"),
            ("Open data", lambda: self._open(self._data_dir()), "folder"),
            ("Open logs", lambda: self._open(ROOT / "logs"), "folder"),
            ("Open dist", lambda: self._open(ROOT / "build_exe" / "dist"), "folder"),
            ("Open EXE data", lambda: self._open(self._exe_data_dir()), "folder"),
        ))))

        self.portable_target = QLineEdit()
        self.portable_target.setToolTip(f"A USB stick or any folder. The project is copied into a subfolder named "
                                        f"'{ROOT.name}' there (python source, no EXE build).")
        portable_browse = _button("Browse ...", tip="Choose the USB / target folder", icon="folder", expand=False)
        portable_browse.clicked.connect(self._browse_portable_target)
        portable_row = QHBoxLayout()
        portable_row.addWidget(self.portable_target, 1)
        portable_row.addWidget(portable_browse)
        portable_body = QVBoxLayout()
        portable_body.addLayout(portable_row)
        self.b_copy = _button("Copy project here ...", icon="copy", tip=(
            "Copies only the files needed to run the program: the .py files of src and main_gui_kit, the program's runtime "
            "data (assets, help, config\\p3d_mapping.json), this launcher, requirements.txt and "
            "start_pdf_reader.bat; writes INSTALL.txt. "
            "Not copied: project data (Input, Export List, Output), settings and licence of this PC, logs, tests, tools, build files. "
            "Runs in the background; an existing file is only replaced by a newer one. Click again to cancel."))
        self.b_copy.clicked.connect(self._copy_portable)
        self.copy_bar = QProgressBar()
        self.copy_bar.setRange(0, 1000)
        self.copy_bar.setFixedHeight(3)
        self.copy_bar.setTextVisible(False)
        self.copy_bar.hide()
        self.copy_status = _muted(wrap=True)
        self.copy_status.hide()
        b_start_portable = _button(f"Start copy (python -m {PACKAGE}, no .bat) ...", ButtonKind.PRIMARY,
                                   "Runs the Python runtime above directly on the copy - no .bat file needed", "copy")
        b_start_portable.clicked.connect(self._start_portable)
        portable_body.addWidget(self.b_copy)
        portable_body.addWidget(self.copy_bar)
        portable_body.addWidget(self.copy_status)
        portable_body.addWidget(b_start_portable)
        side.addWidget(self._card("Portable copy (USB / company laptop)", portable_body))
        side.addWidget(self._card("Hotspot (own Wi-Fi, office area)", self._hotspot_card()))
        side.addStretch(1)

        right = QVBoxLayout()
        log_header = QHBoxLayout()
        log_header.addWidget(page_title("Output / Log"))
        log_header.addStretch(1)
        copy_btn = _button("Copy log", expand=False)
        clear_btn = _button("Clear log", expand=False)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.output.toPlainText()))
        clear_btn.clicked.connect(self.output.clear)
        log_header.addWidget(copy_btn)
        log_header.addWidget(clear_btn)
        right.addLayout(log_header)
        right.addWidget(self.output, 1)

        outer.addWidget(left_scroll)
        outer.addLayout(right, 1)

    def _card(self, title: str, inner) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)   # a card never grows taller than its content
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(6)
        lay.addWidget(_muted(title))
        inner.setContentsMargins(0, 0, 0, 0)
        if not isinstance(inner, QGridLayout):
            inner.setSpacing(6)
        lay.addLayout(inner)
        return frame

    @staticmethod
    def _grid(actions) -> QGridLayout:
        grid = QGridLayout()
        grid.setVerticalSpacing(6)
        for row, (text, callback, icon) in enumerate(actions):
            button = _button(text, icon=icon)
            button.clicked.connect(lambda _=False, f=callback: f())
            grid.addWidget(button, row, 0)
        return grid

    # ---- settings ---------------------------------------------------------------------------------
    def _load_settings(self) -> None:
        s = QSettings(ORG, APP)
        python = s.value("python", "")
        if python and Path(str(python)).is_file():       # a saved path that does not exist on this PC is dropped:
            self.python.setText(str(python))             # the field keeps the development default (Tools_Central)
        company = s.value("pythonCompany", "")
        if company and Path(str(company)).is_file():
            self.python_company.setText(str(company))
        self.portable_target.setText(str(s.value("portableTarget", "") or ""))
        self.version_combo.setCurrentIndex(max(0, self.version_combo.findData(str(s.value("appVersion", "") or ""))))
        if s.value("hsSsid"):
            self.hs_ssid.setText(str(s.value("hsSsid")))
        if s.value("hsPassword"):
            self.hs_pass.setText(str(s.value("hsPassword")))
        self.hs_band.setCurrentIndex(max(0, self.hs_band.findData(s.value("hsBand", "2.4"))))
        self.hs_keep.setChecked(s.value("hsKeepOn", True, type=bool))
        self.web_port.setText(str(s.value("webPort", WEB_PORT) or WEB_PORT))
        self.web_network.setChecked(s.value("webNetwork", True, type=bool))
        geometry = s.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def _save_settings(self) -> None:
        s = QSettings(ORG, APP)
        s.setValue("python", self.python.text())
        s.setValue("pythonCompany", self.python_company.text())
        self._write_company_file()
        s.setValue("portableTarget", self.portable_target.text())
        s.setValue("appVersion", self._selected_version())
        s.setValue("hsSsid", self.hs_ssid.text().strip())
        s.setValue("hsPassword", self.hs_pass.text().strip())
        s.setValue("hsBand", self.hs_band.currentData())
        s.setValue("hsKeepOn", self.hs_keep.isChecked())
        s.setValue("webPort", self.web_port.text().strip())
        s.setValue("webNetwork", self.web_network.isChecked())
        s.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event) -> None:
        if self.copy_thread is not None:
            answer = QMessageBox.question(self, "Close launcher", "The portable copy is still running.\n\n"
                                          "Cancel it and close the launcher? (files copied so far stay there)",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            self.copy_worker.cancel()
            self.copy_thread.quit()
            self.copy_thread.wait(10000)
        if self._hs_thread is not None:                  # a hotspot command is still talking to Windows
            self._hs_thread.wait(90000)                  # (the hotspot itself stays as it is after closing)
        running = [p for p in (self.gui_process, self.portable_process, self.process, self.web_process)
                   if p is not None and p.state() != QProcess.NotRunning]
        if running:
            answer = QMessageBox.question(
                self, "Close launcher",
                f"{PRODUCT} or a job started from this launcher is still running.\n\n"
                "Its console runs inside this launcher window (no separate console), so closing the launcher "
                "ends it too - any unsaved work in it would be lost.\n\nClose the launcher and end it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return
        self._save_settings()
        super().closeEvent(event)

    # ---- helpers ----------------------------------------------------------------------------------
    def _log(self, text: str) -> None:
        self.output.appendPlainText(text)

    def _write_company_file(self) -> None:
        """Company-PC path -> Launcher\\python_company.txt (read by START_LAUNCHER.bat). Written only when it changed."""
        text = self.python_company.text().strip()
        if not text or text == str(_company_python()):
            return
        try:
            COMPANY_FILE.write_text(text + "\n", encoding="utf-8")
        except OSError as error:
            self._log(f"Could not save {COMPANY_FILE}: {error}")

    def _python_path(self) -> Path | None:
        """Development Python if it exists on this PC, else the company-PC Python."""
        dev = Path(self.python.text().strip().strip('"')).expanduser()
        if dev.is_file():
            return dev
        company = Path(self.python_company.text().strip().strip('"')).expanduser()
        if company.is_file():
            return company
        self._log(f"Python runtime not found: {dev} (development) / {company} (company PC)")
        return None

    def _browse_python(self, field: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Python runtime", field.text(), "Python executable (python.exe)")
        if path:
            field.setText(path.replace("/", "\\"))
            self._save_settings()

    @staticmethod
    def _data_dir() -> Path:
        """Data folder of the app when run from source (paths.TOOL_ROOT = workspace): settings, mapping, licence in config\\."""
        return ROOT / "config"

    @staticmethod
    def _exe_data_dir() -> Path:
        env = os.environ.get(ENV_HOME, "").strip()
        if env:
            return Path(env)
        base = os.environ.get("LOCALAPPDATA", "").strip() or str(Path.home() / "AppData" / "Local")
        return Path(base) / "P3D_PDFREADER"

    def _open(self, folder: Path) -> None:
        if not folder.is_dir():                          # nothing is created here - the app / the build creates the folder
            self._log(f"Folder does not exist yet: {folder}")
            return
        subprocess.Popen(["explorer", str(folder)])

    # ---- app version list: current workspace + source trees in versions\ + versions from the git history ---------
    def _refresh_versions(self) -> None:
        previous = self.version_combo.currentData()
        self.version_combo.clear()
        self.version_combo.addItem(f"Current workspace ({_version_of(ROOT)})", "")
        entries: dict[str, str] = {}                    # folder name in versions\ -> text in the list
        versions = ROOT / "versions"
        if versions.is_dir():
            for folder in versions.iterdir():
                if (folder / "source" / "src" / PACKAGE).is_dir():
                    entries[folder.name] = f"Version {folder.name}"
        self._git_commits: dict[str, str] = {}          # folder name -> commit, only for versions not extracted yet
        for version, (commit, date) in _git_versions().items():
            name = f"v{version}"
            if name not in entries:
                entries[name] = f"Version {name}  (git {commit}, {date})"
                self._git_commits[name] = commit
        for name in sorted(entries, key=_version_key, reverse=True):
            self.version_combo.addItem(entries[name], name)
        self.version_combo.setCurrentIndex(max(0, self.version_combo.findData(previous if previous is not None else "")))

    def _extract_version(self, name: str, dest: Path) -> bool:
        """Extracts a version from the git history once to versions\\<name>\\source; later starts use that folder."""
        commit = self._git_commits[name]
        self._log(f"Extracting version {name} from git commit {commit} to {dest} ...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            _extract_git_version(commit, dest)
        except Exception as e:  # noqa: BLE001 - reported in the log, the launcher keeps running
            self._log(f"[ERROR] Extracting {name} failed: {type(e).__name__}: {e}")
            return False
        finally:
            QApplication.restoreOverrideCursor()
        self._log(f"Version {name} extracted.")
        self._refresh_versions()
        return True

    def _selected_version(self) -> str:
        return str(self.version_combo.currentData() or "")

    # ---- start ------------------------------------------------------------------------------------
    @staticmethod
    def _app_env(root: Path) -> dict[str, str]:
        return {"PYTHONPATH": f"{root / 'src'};{root}"}   # like start_pdf_reader.bat

    def _start_gui(self) -> None:
        if self.gui_process is not None and self.gui_process.state() != QProcess.NotRunning:
            self._log("The GUI is already running (started from this launcher).")
            return
        python = self._python_path()
        if python is None:
            return
        version = self._selected_version()
        root = ROOT / "versions" / version / "source" if version else ROOT
        if version and not root.exists() and version in self._git_commits and not self._extract_version(version, root):
            return
        if not (root / "src" / PACKAGE).is_dir():
            self._log(f"Not found: {root / 'src' / PACKAGE}")
            return
        label = f"Start GUI ({version})" if version else "Start GUI"
        if version:
            self._log(f"Note: version {version} uses its own config folder: {root / 'config'}")
        proc = self._spawn(str(python), ["-m", PACKAGE], label, cwd=root, env=self._app_env(root))
        proc.finished.connect(lambda code, _status: self._job_finished(code, label))
        self.gui_process = proc

    def _start_exe(self) -> None:
        dist = ROOT / "build_exe" / "dist"
        exe = dist / EXE_NAME
        if not exe.is_file():
            exe = dist / EXE_FOLDER / EXE_NAME
        if not exe.is_file():
            self._log("EXE not found. Build it first (Build Onefile EXE / Build Onedir EXE).")
            return
        proc = subprocess.Popen([str(exe)], cwd=str(exe.parent))
        self._log(f"EXE started (PID {proc.pid}): {exe}")

    # ---- jobs: captured in this window's own log, no second console -------------------------------
    def _spawn(self, program: str, arguments: list[str], label: str, cwd: Path | None = None,
               env: dict[str, str] | None = None) -> QProcess:
        self._log("=" * 72)
        self._log(f"Job: {label}")
        self._log(f"Command: {program} {' '.join('<script>' if chr(10) in a else a for a in arguments)}")
        proc = QProcess(self)
        proc.setWorkingDirectory(str(cwd or ROOT))
        environment = QProcessEnvironment.systemEnvironment()
        environment.insert("PYTHONUTF8", "1")
        environment.insert("PYTHONUNBUFFERED", "1")
        for key, value in (env or {}).items():
            environment.insert(key, value)
        proc.setProcessEnvironment(environment)
        proc.readyReadStandardOutput.connect(lambda: self._log(_decode(bytes(proc.readAllStandardOutput()))))
        proc.readyReadStandardError.connect(lambda: self._log(_decode(bytes(proc.readAllStandardError()))))
        proc.errorOccurred.connect(lambda _e: self._log(f"[ERROR] {label}: {proc.errorString()}"))
        proc.start(program, arguments)
        return proc

    def _run_captured(self, program: str, arguments: list[str], label: str, env: dict[str, str] | None = None) -> bool:
        if self.process is not None and self.process.state() != QProcess.NotRunning:
            self._log("A launcher job is already running - wait for it to finish.")
            return False
        proc = self._spawn(program, arguments, label, env=env)
        proc.finished.connect(lambda code, _status: self._job_finished(code, label))
        self.process = proc
        return True

    def _run_python(self, arguments: list[str], label: str, env: dict[str, str] | None = None) -> None:
        python = self._python_path()
        if python is not None:
            self._run_captured(str(python), arguments, label, env={**self._app_env(ROOT), **(env or {})})

    def _check_env(self) -> None:
        self._run_python(["-c", ENV_CHECK, *REQUIRED_PACKAGES, "?pytest"], "Environment check")

    def _run_tests(self, targets: list[str], label: str) -> None:
        # project rule: tests run with QT_QPA_PLATFORM=offscreen and PYTHONPATH=src
        # own basetemp: %TEMP%\pytest-of-<user> can be unreadable (WinError 5) on company PCs
        basetemp = str(ROOT / ".pytest_tmp")
        self._run_python(["-m", "pytest", "-q", "--basetemp", basetemp, *targets], label,
                         env={"QT_QPA_PLATFORM": "offscreen"})

    def _run_build(self, args: list[str], label: str) -> None:
        bat = ROOT / "build_exe.bat"
        if not bat.is_file():
            self._log(f"Not found: {bat}")
            return
        answer = QMessageBox.question(self, label, "build_exe.bat deletes the folder build_exe and builds the EXE again "
                                      "(takes several minutes; the first time it creates .venv_build).\n\nBuild now?",
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self._run_captured("cmd.exe", ["/c", str(bat), *args], label)

    def _job_finished(self, code: int, label: str) -> None:
        self._log(f"Result: {label} | exit code {code}")
        self._log("=" * 72)

    # ---- web server: browser access for colleagues (python -m p3d_pdfreader.web) ------------------
    def _web_card(self) -> QVBoxLayout:
        body = QVBoxLayout()
        row = QHBoxLayout()
        row.addWidget(QLabel("Port"))
        self.web_port = QLineEdit(WEB_PORT)
        self.web_port.setMaximumWidth(70)
        row.addWidget(self.web_port)
        self.web_network = QCheckBox("Reachable in the network")
        self.web_network.setToolTip("On: host 0.0.0.0 - colleagues open http://<this PC>:<port>/ in their browser "
                                    "(Windows may ask once to allow Python in the firewall).\n"
                                    "Off: 127.0.0.1 - only this PC.")
        self.web_network.setChecked(True)
        row.addWidget(self.web_network, 1)
        body.addLayout(row)
        buttons = QHBoxLayout()
        b_start = _button("Start web server", ButtonKind.PRIMARY,
                          f"python -m {WEB_PACKAGE}; the addresses for colleagues appear in the log", "run")
        b_start.clicked.connect(self._start_web)
        b_stop = _button("Stop", tip="End the web server", expand=False)
        b_stop.clicked.connect(self._stop_web)
        b_open = _button("Open in browser", tip="Open the web version on this PC", expand=False)
        b_open.clicked.connect(self._open_web)
        buttons.addWidget(b_start, 1)
        buttons.addWidget(b_stop)
        buttons.addWidget(b_open)
        body.addLayout(buttons)
        body.addWidget(_muted("Source folders: config\\paths.json of this PC (set in the app under Settings › Paths). "
                              "Colleagues can also upload PDFs.", wrap=True))
        return body

    def _web_port(self) -> str:
        port = self.web_port.text().strip()
        return port if port.isdigit() and 0 < int(port) < 65536 else WEB_PORT

    def _start_web(self) -> None:
        if self.web_process is not None and self.web_process.state() != QProcess.NotRunning:
            self._log("The web server is already running (started from this launcher).")
            return
        python = self._python_path()
        if python is None:
            return
        host = "0.0.0.0" if self.web_network.isChecked() else "127.0.0.1"
        label = "Web server"
        proc = self._spawn(str(python), ["-m", WEB_PACKAGE, "--host", host, "--port", self._web_port()], label,
                           cwd=ROOT, env=self._app_env(ROOT))
        proc.finished.connect(lambda code, _status: self._job_finished(code, label))
        self.web_process = proc

    def _stop_web(self) -> None:
        if self.web_process is None or self.web_process.state() == QProcess.NotRunning:
            self._log("The web server is not running.")
            return
        self.web_process.kill()
        self.web_process.waitForFinished(5000)
        self._log("Web server stopped.")

    def _open_web(self) -> None:
        import webbrowser
        webbrowser.open(f"http://localhost:{self._web_port()}/")

    # ---- hotspot: this laptop's own Wi-Fi (Windows mobile hotspot, hotspot.py) --------------------
    def _hotspot_card(self) -> QVBoxLayout:
        body = QVBoxLayout()
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(6)
        form.setVerticalSpacing(4)
        self.hs_ssid = QLineEdit(HS.DEFAULT_SSID)
        self.hs_ssid.setToolTip("Wi-Fi name the devices see. A NEW name avoids an old saved entry with another password on "
                                "the phones / laptops (a common reason for 'wrong password').")
        self.hs_pass = QLineEdit(HS.new_password())
        self.hs_pass.setToolTip("WPA2 password, at least 8 characters. Letters and digits only = easy to type on a phone.")
        b_newpw = _button("New", tip="New easy-to-type password (no l / 1 / o / 0)", icon="new", expand=False)
        b_newpw.clicked.connect(lambda: self.hs_pass.setText(HS.new_password()))
        self.hs_band = QComboBox()
        for text, val in (("2.4 GHz (most compatible)", "2.4"), ("Auto", "auto"), ("5 GHz (faster, not every device)", "5")):
            self.hs_band.addItem(text, val)
        self.hs_keep = QCheckBox("Stay on without connected devices")
        self.hs_keep.setChecked(True)
        self.hs_keep.setToolTip("Windows switches its hotspot off after about 5 minutes without a connected device. While the "
                                "launcher hotspot runs this is switched off; 'Stop hotspot' switches it on again.")
        form.addWidget(QLabel("Wi-Fi name"), 0, 0)
        form.addWidget(self.hs_ssid, 0, 1, 1, 2)
        form.addWidget(QLabel("Password"), 1, 0)
        form.addWidget(self.hs_pass, 1, 1)
        form.addWidget(b_newpw, 1, 2)
        form.addWidget(QLabel("Band"), 2, 0)
        form.addWidget(self.hs_band, 2, 1, 1, 2)
        form.addWidget(self.hs_keep, 3, 0, 1, 3)
        form.setColumnStretch(1, 1)
        body.addLayout(form)
        row = QHBoxLayout()
        self.hs_buttons = []
        for text, icon, tip, slot in (
                ("Check", "ok", "Read-only: Wi-Fi hardware, Wi-Fi Direct, group policies, current hotspot state",
                 lambda: self._hotspot_job(HS.check, "Hotspot check")),
                ("Start hotspot", "run", "Sets the Wi-Fi name / password above (WPA2, chosen band) and switches the Windows "
                 "mobile hotspot on. Windows SHARES the current WLAN / LAN connection with it - on a company laptop only "
                 "with IT approval.", self._hotspot_start),
                ("Stop hotspot", "", "Switches the Windows mobile hotspot off (and Windows' automatic turn-off on again)",
                 self._hotspot_stop)):
            b = _button(text, tip=tip, icon=icon)
            b.setMinimumWidth(0)
            b.clicked.connect(lambda _=False, f=slot: f())
            row.addWidget(b)
            self.hs_buttons.append(b)
        self.hs_status = QLabel("Not checked yet.")
        self.hs_status.setWordWrap(True)
        self.hs_status.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body.addLayout(row)
        body.addWidget(self.hs_status)
        return body

    def _hotspot_start(self) -> None:
        ssid, pw = self.hs_ssid.text().strip(), self.hs_pass.text().strip()
        err = HS.validate(ssid, pw)
        if err:
            QMessageBox.warning(self, "Start hotspot", err)
            return
        answer = QMessageBox.question(
            self, "Start hotspot",
            f"Windows will open its own Wi-Fi '{ssid}' (password {pw}, WPA2, {self.hs_band.currentText()}) on this laptop "
            "and SHARE the current connection with it - devices in the hotspot can also reach that network.\n\n"
            "On a company laptop: only with the IT's approval.\n\nStart it?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        self._save_settings()
        band, keep = self.hs_band.currentData(), self.hs_keep.isChecked()
        self._hotspot_job(lambda: HS.start(ssid, pw, band, keep), "Start hotspot")

    def _hotspot_stop(self) -> None:
        restore = QSettings(ORG, APP).value("hsRestoreAutoOff", False, type=bool)
        self._hotspot_job(lambda: HS.stop(restore), "Stop hotspot")

    def _hotspot_job(self, fn, label: str) -> None:
        if self._hs_thread is not None:
            self._log("A hotspot command is still running - wait for it to finish.")
            return
        self._log("=" * 72)
        self._log(f"Job: {label} (Windows PowerShell, takes a few seconds) ...")
        self.hs_status.setText(f"{label} ...")
        for b in self.hs_buttons:
            b.setEnabled(False)
        worker = FuncWorker(fn)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._hotspot_done)      # bound method: runs in the GUI thread
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._hs_thread, self._hs_worker, self._hs_label = thread, worker, label
        thread.start()

    def _hotspot_done(self, r: dict) -> None:
        label = self._hs_label
        self._hs_thread = self._hs_worker = None
        for b in self.hs_buttons:
            b.setEnabled(True)
        lines = HS.summary(r)
        for ln in lines:
            self._log(ln)
        s = QSettings(ORG, APP)                          # restore Windows' auto turn-off on Stop only if WE switched it off
        if label == "Start hotspot" and r.get("auto_off_before") is True:
            s.setValue("hsRestoreAutoOff", True)
        elif label == "Stop hotspot" and r.get("ok"):
            s.setValue("hsRestoreAutoOff", False)
        if r.get("state") == "On":
            self._log(f"Hotspot is ON - devices join Wi-Fi \"{r.get('ssid')}\" (password {r.get('password')}); "
                      f"address of this laptop in the hotspot: {r.get('ip') or HS.HOTSPOT_DEFAULT_IP}.")
        self.hs_status.setText("\n".join(lines) if lines else "-")
        self._log(f"Result: {label} | {'OK' if r.get('ok') else 'FAILED'}")
        self._log("=" * 72)

    # ---- portable copy (USB / company laptop) ------------------------------------------------------
    def _browse_portable_target(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select USB stick / target folder", self.portable_target.text())
        if path:
            self.portable_target.setText(path.replace("/", "\\"))
            self._save_settings()

    def _portable_dest(self) -> Path | None:
        text = self.portable_target.text().strip()
        if not text:
            self._log("Choose a USB stick / target folder first (Browse ...).")
            return None
        return Path(text).expanduser() / ROOT.name

    def _copy_portable(self) -> None:
        if self.copy_thread is not None:                 # the button is "Cancel copy" while a copy runs
            self.copy_worker.cancel()
            self.b_copy.setEnabled(False)
            self.copy_status.setText("Cancelling ...")
            return
        dest = self._portable_dest()
        if dest is None:
            return
        if not dest.parent.is_dir():
            self._log(f"Target folder does not exist: {dest.parent}")
            return
        if dest.resolve() == ROOT or ROOT in dest.resolve().parents:      # compared after resolve() (subst drive)
            self._log(f"Target is inside the workspace itself - choose another folder: {dest}")
            return
        self._save_settings()
        self._log("=" * 72)
        self._log(f"Job: Portable copy -> {dest}")
        self._log("Counting files ... (existing files are only replaced by newer ones; every copied file is listed below)")
        self.copy_bar.setValue(0)
        self.copy_bar.show()
        self.copy_status.setText("Counting files ...")
        self.copy_status.show()
        self.b_copy.setText("Cancel copy")
        worker = CopyWorker(ROOT, dest, self._python_path(), self.python_company.text())
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._copy_progress)
        worker.fileCopied.connect(self._copy_file)
        worker.finished.connect(self._copy_done)
        self._copy_dest = dest
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.copy_thread, self.copy_worker = thread, worker
        thread.start()

    def _copy_progress(self, done_b: int, total_b: int, done_n: int, total_n: int) -> None:
        self.copy_bar.setValue(int(1000 * done_b / max(1, total_b)))
        self.copy_status.setText(f"{done_n:,} of {total_n:,} files  ·  {done_b / 1048576:,.1f} of {total_b / 1048576:,.1f} MB")

    def _copy_file(self, rel: str) -> None:
        self._log(f"  copied  {rel}")

    def _copy_done(self, summary: dict) -> None:
        dest = self._copy_dest
        self.copy_thread = self.copy_worker = None
        self.b_copy.setText("Copy project here ...")
        self.b_copy.setEnabled(True)
        failed = summary["failed"]
        for rel, err in failed[:50]:
            self._log(f"  FAILED  {rel}: {err}")
        if len(failed) > 50:
            self._log(f"  ... and {len(failed) - 50} more failed files")
        newer = summary["target_newer"]
        for rel in newer[:50]:
            self._log(f"  kept    {rel}  (the file on the target is newer - not overwritten)")
        if len(newer) > 50:
            self._log(f"  ... and {len(newer) - 50} more files that are newer on the target")
        counts = (f"{summary['copied']:,} file(s) copied ({summary['bytes'] / 1048576:,.1f} MB), "
                  f"{summary['skipped']:,} kept (already up to date"
                  + (f", {len(newer):,} newer on the target" if newer else "") + f"), {len(failed):,} failed")
        if summary["error"]:
            state, title, text = "ERROR", "Portable copy failed", f"The copy stopped with an error:\n{summary['error']}\n\n{counts}"
        elif summary["cancelled"]:
            state, title, text = "CANCELLED", "Portable copy cancelled", f"Cancelled.\n\n{counts}\n\nTarget: {dest}"
        elif failed:
            state, title, text = "WARNING", "Portable copy finished with errors", f"{counts}\n\nTarget: {dest}\nSee the log for the failed files."
        else:
            state, title, text = "OK", "Portable copy finished", f"{counts}\n\nTarget: {dest}\n\nStart it there with \"Start copy ...\"."
            self.copy_bar.setValue(1000)
        self.copy_status.setText(f"{state}: {counts}")
        if summary.get("install"):
            self._log(f"  written INSTALL.txt  ({summary['install']})")
        self._log(f"Result: Portable copy | {state} | {counts}")
        self._log("=" * 72)
        QApplication.alert(self)                         # taskbar flashes if the launcher is in the background
        box = QMessageBox.warning if state in ("ERROR", "WARNING") else QMessageBox.information
        box(self, title, text)

    def _start_portable(self) -> None:
        dest = self._portable_dest()
        if dest is None:
            return
        if not (dest / "src" / PACKAGE).is_dir():
            self._log(f"Not copied yet (or moved): {dest}. Use \"Copy project here ...\" first.")
            return
        python = self._python_path()
        if python is None:
            return
        if self.portable_process is not None and self.portable_process.state() != QProcess.NotRunning:
            self._log("A copy started from this launcher is already running.")
            return
        proc = self._spawn(str(python), ["-m", PACKAGE], "Start portable copy", cwd=dest, env=self._app_env(dest))
        proc.finished.connect(lambda code, _status: self._job_finished(code, "Start portable copy"))
        self.portable_process = proc


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(LAUNCHER_TITLE)
    app.setStyle("Fusion")                               # same widget style as the Tag Compliance launcher
    theme = ThemeManager(app, start="LIGHT")             # kit theme, as in the main window of the application
    window = LauncherWindow()
    window._theme = theme
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
