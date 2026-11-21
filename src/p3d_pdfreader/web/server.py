r"""Web-Server des P3D PDF Readers (nur Standardbibliothek + PyMuPDF/openpyxl aus ``core``).

Jeder Browser bekommt eine Sitzung (Cookie) mit eigenen Scan-Ergebnissen. PDFs kommen aus den Quellordnern des
Servers (``config\paths.json`` oder ``--source``, z. B. UNC-Freigaben) oder werden hochgeladen. Der Browser sieht nie
Serverpfade als Eingabe - nur IDs der eingelesenen PDFs; gelesen wird nur, was unter einem Quellordner liegt oder
hochgeladen wurde. PDFs werden nur gelesen; Ausgaben (Redline, Excel, CSV, ZIP) entstehen in einem Temp-Ordner und
gehen als Download an den Browser.

PyMuPDF ist nicht threadsicher - alle Zugriffe laufen ueber ``PDF_LOCK``."""
from __future__ import annotations

import argparse
import io
import json
import logging
import mimetypes
import re
import secrets
import shutil
import socket
import sys
import tempfile
import threading
import time
import zipfile
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from ..constants import APP_NAME
from ..paths import PathSettings, file_timestamp, logs_dir, patterns_file, tool_root

STATIC = Path(__file__).resolve().parents[1] / "assets" / "web"
PDF_LOCK = threading.RLock()
SESSION_TTL = 12 * 3600            # Sekunden ohne Zugriff, dann wird die Sitzung (inkl. Uploads) verworfen
MAX_UPLOAD = 300 * 1024 * 1024     # Byte je Datei
MAX_RENDER_PIXELS = 16_000_000
COOKIE = "p3d_pdfreader_sid"
log = logging.getLogger("p3d_pdfreader.web")


def version() -> str:
    try:
        return (tool_root() / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


# ---- Daten -> JSON ---------------------------------------------------------------------------------------------
def _hits(tag) -> list:
    """Fundstellen in Navigationsreihenfolge: Seite, dann von oben nach unten, links nach rechts."""
    hits = tag.hits or ([(0, tag.rect)] if tag.rect else [])
    return [[p, [round(v, 1) for v in r]] for p, r in sorted(hits, key=lambda h: (h[0], round(h[1][1]), h[1][0]))]


def file_json(fid: int, r, origin: str) -> dict:
    return {"id": fid, "name": r.name, "origin": origin, "drawing_no": r.drawing_no,
            "created": r.created.strftime("%Y-%m-%d %H:%M") if r.created else "", "author": r.author_display,
            "checked": r.checked, "revision": r.revision, "revision_date": r.revision_date,
            "revision_text": r.revision_text, "plot_user": r.plot_user, "pages": r.pages, "size_kb": r.size_kb,
            "tags": len(r.tags), "duplicates": sum(1 for t in r.tags if t.duplicate), "error": r.error}


def tag_json(t) -> dict:
    return {"type": t.type, "tag": t.tag, "count": t.count, "pages": t.pages_text, "page": t.page,
            "duplicate": t.duplicate, "hits": _hits(t)}


# ---- Sitzungen ---------------------------------------------------------------------------------------------------
class ScanJob:
    def __init__(self) -> None:
        self.total = 0
        self.done = 0
        self.current = ""
        self.finished = False
        self.cancelled = False
        self.error = ""


class Session:
    def __init__(self, sid: str) -> None:
        self.id = sid
        self.lock = threading.Lock()
        self.results: dict[int, tuple] = {}         # id -> (PdfResult, Herkunft "server"/"upload")
        self.next_id = 1
        self.job: ScanJob | None = None
        self.upload_dir: Path | None = None
        self.seen = time.time()

    def add(self, result, origin: str) -> int:
        with self.lock:
            # gleiche Datei erneut eingelesen -> alten Eintrag ersetzen (Pfadvergleich nach resolve())
            key = str(result.path.resolve()).casefold()
            for fid, (old, _o) in list(self.results.items()):
                if str(old.path.resolve()).casefold() == key:
                    del self.results[fid]
            fid = self.next_id
            self.next_id += 1
            self.results[fid] = (result, origin)
            return fid

    def get(self, fid: int):
        with self.lock:
            item = self.results.get(fid)
        if item is None:
            raise KeyError(f"PDF {fid} ist nicht eingelesen")
        return item[0]

    def files(self) -> list[dict]:
        with self.lock:
            items = list(self.results.items())
        return [file_json(fid, r, origin) for fid, (r, origin) in items]

    def uploads(self) -> Path:
        if self.upload_dir is None:
            self.upload_dir = Path(tempfile.mkdtemp(prefix="p3d_pdfreader_upload_"))
        return self.upload_dir

    def close(self) -> None:
        if self.job and not self.job.finished:
            self.job.cancelled = True
        if self.upload_dir:
            shutil.rmtree(self.upload_dir, ignore_errors=True)


class App:
    """Zustand des Servers: Quellordner und Sitzungen."""

    def __init__(self, extra_sources: list[str] | None = None) -> None:
        self.extra_sources = [str(Path(s).resolve()) for s in (extra_sources or [])]
        self.sessions: dict[str, Session] = {}
        self.lock = threading.Lock()

    def sources(self) -> list[Path]:
        seen, out = set(), []
        for s in PathSettings.load().sources + self.extra_sources:
            p = Path(s).resolve()
            if str(p).casefold() not in seen:
                seen.add(str(p).casefold())
                out.append(p)
        return out

    def session(self, sid: str | None) -> Session:
        now = time.time()
        with self.lock:
            for key, s in list(self.sessions.items()):
                if now - s.seen > SESSION_TTL and (s.job is None or s.job.finished):
                    s.close()
                    del self.sessions[key]
            s = self.sessions.get(sid or "")
            if s is None:
                s = Session(secrets.token_urlsafe(24))
                self.sessions[s.id] = s
            s.seen = now
            return s

    def start_scan(self, session: Session, indices: list[int] | None, pipes: bool = False) -> ScanJob:
        from ..core.extract import find_pdfs, read_pdf
        from ..core.patterns import load

        sources = self.sources()
        chosen = [p for i, p in enumerate(sources) if (indices is None or i in indices) and p.exists()]
        job = ScanJob()
        session.job = job

        def run() -> None:
            try:
                pat = load(patterns_file())
                files = find_pdfs(chosen)
                job.total = len(files)
                for path in files:
                    if job.cancelled:
                        break
                    job.current = path.name
                    with PDF_LOCK:
                        result = read_pdf(path, pat, pipes)
                    session.add(result, "server")
                    job.done += 1
            except Exception as exc:  # noqa: BLE001 - Fehler an den Browser melden statt den Server zu stoppen
                job.error = f"{type(exc).__name__}: {exc}"
                log.exception("Scan")
            finally:
                job.finished = True

        threading.Thread(target=run, daemon=True, name=f"scan-{session.id[:6]}").start()
        return job


# ---- Ausgaben ----------------------------------------------------------------------------------------------------
def _select_tags(result, keys) -> list:
    """``keys`` = [[Typ, Tag], ...] (z. B. gefilterte Tabelle) oder None = alle Tags."""
    if keys is None:
        return result.tags
    wanted = {(str(k[0]), str(k[1])) for k in keys if isinstance(k, (list, tuple)) and len(k) == 2}
    return [t for t in result.tags if (t.type, t.tag) in wanted]


def _stem(result) -> str:
    return re.sub(r"[^\w.\- ]", "_", result.path.stem)


def build_redline(result, keys=None) -> tuple[str, bytes]:
    from ..core.redline import write_redline
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "redline.pdf"
        with PDF_LOCK:
            write_redline(result, out, _select_tags(result, keys))
        return f"{_stem(result)}_Redline_{file_timestamp()}.pdf", out.read_bytes()


def build_review(results: list, keys_by_id: dict | None = None, name: str = "") -> tuple[str, bytes]:
    from ..core.review import write_review_xlsx
    tags_by_pdf = {r.path: _select_tags(r, keys_by_id[i]) for i, r in results if keys_by_id and i in keys_by_id}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "review.xlsx"
        write_review_xlsx(out, [r for _i, r in results], tags_by_pdf)
        stem = name or (_stem(results[0][1]) if len(results) == 1 else "Review_gesamt")
        return f"{stem}_Review_{file_timestamp()}.xlsx", out.read_bytes()


def build_export_xlsx(results: list) -> tuple[str, bytes]:
    from ..core.export import write_xlsx
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "export.xlsx"
        write_xlsx(out, results)
        return f"PDF_Reader_Export_{file_timestamp()}.xlsx", out.read_bytes()


def build_export_csv(results: list) -> tuple[str, bytes]:
    """ZIP mit Tags-CSV und ``_Dateien.csv`` (``;``, UTF-8 mit BOM) wie in der Desktop-App."""
    from ..core.export import FILE_HEADERS, TAG_HEADERS, file_rows, tag_rows, write_csv
    stamp = file_timestamp()
    buf = io.BytesIO()
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, headers, rows in ((f"PDF_Reader_Tags_{stamp}.csv", TAG_HEADERS, tag_rows(results)),
                                    (f"PDF_Reader_Tags_{stamp}_Dateien.csv", FILE_HEADERS, file_rows(results))):
            zf.write(write_csv(Path(tmp) / name, headers, rows), name)
    return f"PDF_Reader_CSV_{stamp}.zip", buf.getvalue()


def build_bulk(results: list, options: dict, keys_by_id: dict | None = None) -> tuple[str, bytes]:
    """Review Auswahl/Bulk als ZIP: Redline-PDF je PDF, Review-Excel je PDF, Review-Excel gesamt."""
    stamp = file_timestamp()
    folder = f"Review_{stamp}/"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fid, r in results:
            keys = (keys_by_id or {}).get(fid)
            if options.get("redline"):
                name, data = build_redline(r, keys)
                zf.writestr(folder + name, data)
            if options.get("review_each"):
                name, data = build_review([(fid, r)], keys_by_id)
                zf.writestr(folder + name, data)
        if options.get("review_total") and results:
            name, data = build_review(results, keys_by_id, "Review_gesamt")
            zf.writestr(folder + name, data)
    return f"Review_{stamp}.zip", buf.getvalue()


def render_png(result, page: int, zoom: float, clip: tuple | None, mono: bool = False) -> bytes:
    """Seite (sichtbare Lage) als PNG; ``zoom`` = Pixel je PDF-Punkt, ``clip`` = Ausschnitt in Seitenkoordinaten,
    ``mono`` = monochrom (schwarz auf weiss, nur Ansicht)."""
    import pymupdf

    from ..core.render import page_pixmap
    with PDF_LOCK, pymupdf.open(result.path) as doc:
        if not 0 <= page < doc.page_count:
            raise KeyError(f"Seite {page + 1} gibt es nicht")
        pg = doc[page]
        rect = pg.rect if clip is None else pymupdf.Rect(clip) & pg.rect
        if rect.is_empty:
            raise ValueError("Ausschnitt liegt ausserhalb der Seite")
        zoom = max(0.05, min(zoom, 40.0))
        if rect.width * rect.height * zoom * zoom > MAX_RENDER_PIXELS:
            zoom = (MAX_RENDER_PIXELS / (rect.width * rect.height)) ** 0.5
        pix = page_pixmap(pg, pymupdf.Matrix(zoom, zoom), clip=rect, mono=mono)
        return pix.tobytes("png")


def page_sizes(result) -> list:
    import pymupdf
    with PDF_LOCK, pymupdf.open(result.path) as doc:
        return [[round(p.rect.width, 2), round(p.rect.height, 2)] for p in doc]


def lan_addresses(port: int) -> list[str]:
    """Adressen, unter denen Kollegen den Server erreichen (Rechnername und IPv4-Adressen)."""
    host = socket.gethostname()
    out = [f"http://{host}:{port}/"]
    try:
        for info in socket.getaddrinfo(host, None, socket.AF_INET):
            url = f"http://{info[4][0]}:{port}/"
            if url not in out and not info[4][0].startswith("127."):
                out.append(url)
    except OSError:
        pass
    return out


# ---- HTTP --------------------------------------------------------------------------------------------------------
class HttpError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


class Handler(BaseHTTPRequestHandler):
    server_version = "P3DPDFReader"
    app: App = None  # type: ignore[assignment]   # wird in make_server gesetzt

    def log_message(self, fmt: str, *args) -> None:
        log.info("%s %s", self.address_string(), fmt % args)

    # -- Hilfen --
    def _session(self) -> Session:
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        sid = jar[COOKIE].value if COOKIE in jar else None
        s = self.app.session(sid)
        self._new_sid = s.id if s.id != sid else None
        return s

    def _send(self, status: int, body: bytes, ctype: str, headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        if getattr(self, "_new_sid", None):
            self.send_header("Set-Cookie", f"{COOKIE}={self._new_sid}; Path=/; HttpOnly; SameSite=Strict")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _download(self, name: str, data: bytes, inline: bool = False) -> None:
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        if name.endswith(".xlsx"):
            ctype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ascii_name = name.encode("ascii", "replace").decode().replace("?", "_").replace('"', "_")
        disposition = f"{'inline' if inline else 'attachment'}; filename=\"{ascii_name}\"; " \
                      f"filename*=UTF-8''{_quote(name)}"
        self._send(200, data, ctype, {"Content-Disposition": disposition})

    def _body(self, limit: int = 2 * 1024 * 1024) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length > limit:
            raise HttpError(413, "Datei zu gross")
        return self.rfile.read(length) if length else b""

    def _payload(self) -> dict:
        try:
            data = json.loads(self._body() or b"{}")
        except ValueError:
            raise HttpError(400, "Ungueltige Anfrage") from None
        return data if isinstance(data, dict) else {}

    def _results(self, s: Session, ids) -> list:
        if ids is None:
            with s.lock:
                return [(fid, r) for fid, (r, _o) in s.results.items()]
        return [(int(i), s.get(int(i))) for i in ids]

    # -- Routing --
    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_HEAD(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        self._new_sid = None
        try:
            url = urlparse(self.path)
            parts = [unquote(p) for p in url.path.split("/") if p]
            if not parts or parts[0] != "api":
                return self._static(url.path)
            s = self._session()
            q = {k: v[-1] for k, v in parse_qs(url.query).items()}
            self._api(method, parts[1:], q, s)
        except HttpError as exc:
            self._json({"error": str(exc)}, exc.status)
        except KeyError as exc:
            self._json({"error": str(exc.args[0] if exc.args else exc)}, 404)
        except (ValueError, TypeError) as exc:
            self._json({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:  # noqa: BLE001
            log.exception("Anfrage %s", self.path)
            self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

    def _static(self, path: str) -> None:
        rel = path.lstrip("/") or "index.html"
        target = (STATIC / rel).resolve()
        if not target.is_file() or STATIC not in target.parents:
            raise HttpError(404, "Nicht gefunden")
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or target.suffix in (".js", ".json", ".svg"):
            ctype = {".js": "text/javascript", ".svg": "image/svg+xml"}.get(target.suffix, ctype) + "; charset=utf-8"
        self._session()                                    # Cookie schon mit der Seite setzen
        self._send(200, target.read_bytes(), ctype)

    def _api(self, method: str, parts: list[str], q: dict, s: Session) -> None:
        route = (method, parts[0] if parts else "")
        if route == ("GET", "info"):
            sources = self.app.sources()
            return self._json({"app": APP_NAME, "version": version(),
                               "sources": [{"index": i, "path": str(p), "exists": p.exists()}
                                           for i, p in enumerate(sources)]})
        if route == ("POST", "scan"):
            if s.job and not s.job.finished:
                raise HttpError(409, "Es laeuft bereits ein Scan")
            d = self._payload()
            idx = d.get("sources")
            self.app.start_scan(s, None if idx is None else [int(i) for i in idx], bool(d.get("pipes")))
            return self._json({"started": True})
        if route == ("GET", "scan"):
            j = s.job
            return self._json({"running": bool(j and not j.finished), "total": j.total if j else 0,
                               "done": j.done if j else 0, "current": j.current if j else "",
                               "error": j.error if j else "", "finished": bool(j and j.finished)})
        if route == ("POST", "cancel"):
            if s.job:
                s.job.cancelled = True
            return self._json({"cancelled": True})
        if route == ("POST", "clear"):
            with s.lock:
                s.results.clear()
            return self._json({"cleared": True})
        if route == ("POST", "upload"):
            return self._upload(s)
        if route == ("GET", "files"):
            if len(parts) == 1:
                return self._json(s.files())
            return self._file_api(s, int(parts[1]), parts[2] if len(parts) > 2 else "", q)
        if route == ("GET", "tags"):                       # Blatt "Alle Tags"
            rows = []
            for fid, r in self._results(s, None):
                rows.extend({"file": fid, "pdf": r.name, "drawing_no": r.drawing_no, **tag_json(t)} for t in r.tags)
            return self._json(rows)
        if route == ("POST", "redline"):
            d = self._payload()
            return self._download(*build_redline(s.get(int(d["id"])), d.get("tags")))
        if route == ("POST", "review"):
            d = self._payload()
            keys = {int(k): v for k, v in (d.get("tags") or {}).items()}
            return self._download(*build_review(self._results(s, d.get("ids")), keys or None))
        if route == ("POST", "bulk"):
            d = self._payload()
            keys = {int(k): v for k, v in (d.get("tags") or {}).items()}
            return self._download(*build_bulk(self._results(s, d.get("ids")), d.get("options") or {}, keys or None))
        if route == ("POST", "export"):
            d = self._payload()
            results = [r for _i, r in self._results(s, d.get("ids"))]
            build = build_export_csv if d.get("format") == "csv" else build_export_xlsx
            return self._download(*build(results))
        raise HttpError(404, "Unbekannte Funktion")

    def _file_api(self, s: Session, fid: int, what: str, q: dict) -> None:
        r = s.get(fid)
        if what == "tags":
            return self._json([tag_json(t) for t in r.tags])
        if what == "pages":
            return self._json(page_sizes(r))
        if what == "render":
            clip = tuple(float(q[k]) for k in ("x0", "y0", "x1", "y1")) if "x0" in q else None
            png = render_png(r, int(q.get("page", 0)), float(q.get("zoom", 1)), clip, q.get("mono") == "1")
            return self._send(200, png, "image/png", {"Cache-Control": "private, max-age=600"})
        if what == "pdf":                                   # Original zum Ansehen im Browser (nur lesen)
            return self._download(r.name, r.path.read_bytes(), inline=True)
        raise HttpError(404, "Unbekannte Funktion")

    def _upload(self, s: Session) -> None:
        name = Path(unquote(self.headers.get("X-File-Name", "upload.pdf"))).name
        if not name.lower().endswith(".pdf"):
            raise HttpError(400, "Nur PDF-Dateien")
        data = self._body(MAX_UPLOAD)
        if not data.startswith(b"%PDF"):
            raise HttpError(400, f"{name} ist keine PDF")
        folder = s.uploads() / secrets.token_hex(4)          # Unterordner: gleichnamige Uploads bleiben getrennt
        folder.mkdir()
        path = folder / name
        path.write_bytes(data)
        from ..core.extract import read_pdf
        from ..core.patterns import load
        with PDF_LOCK:
            result = read_pdf(path, load(patterns_file()), self.headers.get("X-Pipes") == "1")
        fid = s.add(result, "upload")
        return self._json(file_json(fid, result, "upload"))


def _quote(text: str) -> str:
    from urllib.parse import quote
    return quote(text, safe="")


def make_server(host: str, port: int, sources: list[str] | None = None) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"app": App(sources)})
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m p3d_pdfreader.web", description=f"{APP_NAME} – Web-Server")
    parser.add_argument("--host", default="127.0.0.1",
                        help="0.0.0.0 = im Netzwerk erreichbar, 127.0.0.1 = nur dieser PC (Standard)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--source", action="append", default=[],
                        help="zusaetzlicher Quellordner (mehrfach moeglich), ergaenzt config\\paths.json")
    parser.add_argument("--version", action="store_true")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):        # Windows-Konsole (cp1252/cp850): Umlaute nie als Absturzgrund
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    if args.version:
        print(f"{APP_NAME} Web {version()}")
        return 0
    from ..core.patterns import write_defaults
    write_defaults(patterns_file())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(logs_dir() / "p3d_pdfreader_web.log", encoding="utf-8")])
    server = make_server(args.host, args.port, args.source)
    app = server.RequestHandlerClass.app
    print(f"{APP_NAME} Web {version()} läuft auf Port {args.port}.", flush=True)
    if args.host in ("0.0.0.0", ""):
        print("Adressen für Kollegen im Firmennetz:", flush=True)
        for url in lan_addresses(args.port):
            print(f"  {url}", flush=True)
    else:
        print(f"  http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}/  (nur dieser PC)",
              flush=True)
    print("Quellordner:", flush=True)
    for p in app.sources() or []:
        print(f"  [{'OK' if p.exists() else 'fehlt'}] {p}", flush=True)
    if not app.sources():
        print("  (keine – im Desktop-Tool unter Einstellungen › Pfade eintragen oder --source angeben;"
              " Hochladen geht immer)", flush=True)
    print("Beenden mit Strg+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for sess in list(app.sessions.values()):
            sess.close()
    return 0
