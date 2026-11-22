"""Web-Version aus der Desktop-App starten/stoppen (Menueband-Gruppe "Web").

Der Server laeuft als **eigener Prozess** (``python -m p3d_pdfreader --web`` bzw. ``<EXE> --web``), nicht als Thread:
PyMuPDF ist nicht threadsicher, und die App rendert selbst mit PyMuPDF. Laeuft auf dem Port schon ein Server (Launcher,
``start_web_server.bat``), wird er genutzt statt ein zweiter gestartet."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser

from .. import paths

WEB_PORT = 8765
WEB_TIP = ("Web-Version für Kollegen im Firmennetz: startet den Web-Server auf diesem PC (Port 8765). "
           "Die Kollegen öffnen die angezeigte Adresse im Browser – ohne Python oder EXE. "
           "Quellordner = Einstellungen › Pfade dieses PCs; Kollegen können auch PDFs hochladen.")


def port_open(port: int = WEB_PORT) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def addresses(port: int = WEB_PORT) -> list[str]:
    from ..web.server import lan_addresses
    return lan_addresses(port)


class WebServerControl:
    def __init__(self, port: int = WEB_PORT) -> None:
        self.port = port
        self.proc: subprocess.Popen | None = None

    @property
    def own_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start(self, timeout: float = 8.0) -> str:
        """Server starten. Rueckgabe: "started", "external" (lief schon) oder Fehlertext."""
        if self.own_running:
            return "started"
        if port_open(self.port):
            return "external"
        frozen = getattr(sys, "frozen", False)
        cmd = [sys.executable] + ([] if frozen else ["-m", "p3d_pdfreader"]) + \
              ["--web", "--host", "0.0.0.0", "--port", str(self.port)]
        env = dict(os.environ)
        if not frozen:
            root = paths.tool_root()
            env["PYTHONPATH"] = f"{root / 'src'};{root}"
        env["PYTHONUTF8"] = "1"
        try:
            self.proc = subprocess.Popen(cmd, cwd=str(paths.tool_root()), env=env, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as exc:
            return f"Start fehlgeschlagen: {exc}"
        end = time.time() + timeout
        while time.time() < end:
            if port_open(self.port):
                return "started"
            if self.proc.poll() is not None:
                break
            time.sleep(0.15)
        self.stop()
        return f"Der Web-Server ist nicht gestartet. Details: {paths.logs_dir() / 'p3d_pdfreader_web.log'}"

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None

    def open_browser(self) -> None:
        webbrowser.open(f"http://localhost:{self.port}/")
