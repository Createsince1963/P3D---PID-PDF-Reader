r"""Variante 1 "nur HTML": Offline-HTML-Bericht = **eine** HTML-Datei ohne Server und ohne Internet.

Enthaelt die Oberflaeche der Web-Version (``assets\web``: app.css, app.js inline), die Scan-Ergebnisse (dieselben
JSON-Daten wie der Web-Server, ``server.file_json``/``tag_json``) und je Seite ein JPEG-Bild. Im Browser gehen Tabellen,
Filter, Nur doppelte, Fundstellen-Navigation, Viewer (Zoom bis zur Bildaufloesung, Drehen, Seiten, Schwarz-Weiss).
Nicht im Bericht: Einlesen, Redline-PDF, Review-Excel, Export (brauchen den Server bzw. die Desktop-App).

Die Datei laesst sich per Mail oder Freigabe weitergeben. Groesse ca. 0,3-1 MB je Seite (``max_px``)."""
from __future__ import annotations

import base64
import html
import json
import re
from datetime import datetime
from pathlib import Path

from ..constants import APP_NAME
from .server import STATIC, file_json, review_lists, review_store, tag_json, version

DEFAULT_MAX_PX = 3000          # laengste Bildseite in Pixeln (Zoom bis etwa 1:1 eines A1-Plots am Bildschirm)
DEFAULT_QUALITY = 80           # JPEG-Qualitaet
EST_BYTES_PER_PAGE = 700_000   # grobe Schaetzung fuer die Warnung vor sehr grossen Dateien


def estimate_mb(results: list) -> float:
    return sum(max(r.pages, 1) for r in results) * EST_BYTES_PER_PAGE / 1e6


def _page_images(path: Path, max_px: int, quality: int) -> tuple[list, list]:
    import pymupdf
    sizes, images = [], []
    with pymupdf.open(path) as doc:
        for page in doc:
            w, h = page.rect.width, page.rect.height
            sizes.append([round(w, 2), round(h, 2)])
            zoom = max_px / max(w, h)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False, colorspace=pymupdf.csRGB)
            images.append("data:image/jpeg;base64," + base64.b64encode(pix.tobytes("jpg", jpg_quality=quality)).decode())
    return sizes, images


def _blob(name_data: tuple[str, bytes]) -> dict:
    name, data = name_data
    mime = "application/pdf" if name.lower().endswith(".pdf") else \
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return {"name": name, "uri": f"data:{mime};base64," + base64.b64encode(data).decode()}


def report_data(results: list, max_px: int = DEFAULT_MAX_PX, quality: int = DEFAULT_QUALITY, progress=None,
                title: str = "", redline: bool = True, review: bool = True) -> dict:
    """Daten fuer ``window.P3D_OFFLINE``. ``progress(i, n, name)`` meldet den Fortschritt (Abbruch: True zurueckgeben).

    ``redline``/``review``: Redline-PDF bzw. Review-Excel je PDF (alle Tags) mit einbetten - im Bericht als Download.
    Export-Excel und Review-Excel gesamt sind immer dabei (klein)."""
    from .server import build_export_xlsx, build_redline, build_review
    files, tags, pages, images, all_tags = [], {}, {}, {}, []
    per_file: dict[int, dict] = {}
    done: list = []
    for i, r in enumerate(results, start=1):
        if progress and progress(i, len(results), r.name):
            break
        fid = i
        files.append(file_json(fid, r, "bericht"))
        store = review_store(r)                        # gespeicherte Audit-Eintraege mit in den Bericht
        tags[fid] = [tag_json(t, store) for t in r.tags]
        all_tags.extend({"file": fid, "pdf": r.name, "drawing_no": r.drawing_no, **tag_json(t, store)} for t in r.tags)
        if r.error:
            pages[fid], images[fid] = [], []
            continue
        done.append((fid, r))
        try:
            pages[fid], images[fid] = _page_images(r.path, max_px, quality)
            extra = {}
            if redline:
                extra["redline"] = _blob(build_redline(r))
            if review:
                extra["review"] = _blob(build_review([(fid, r)]))
            per_file[fid] = extra
        except Exception as exc:  # noqa: BLE001 - eine defekte PDF bricht den Bericht nicht ab
            files[-1]["error"] = files[-1]["error"] or f"Bild/Ausgabe fehlt: {type(exc).__name__}: {exc}"
            pages.setdefault(fid, [])
            images.setdefault(fid, [])
    downloads = {"per_file": per_file}
    if done:
        downloads["export"] = _blob(build_export_xlsx([r for _i, r in done]))
        downloads["review_total"] = _blob(build_review(done, None, "Review_gesamt"))
    return {"info": {"app": APP_NAME, "version": version(), "offline": True, "sources": [], **review_lists(),
                     "created": datetime.now().strftime("%Y-%m-%d %H:%M"), "title": title or "Offline-Bericht",
                     "max_px": max_px},
            "files": files, "tags": tags, "pages": pages, "images": images, "all_tags": all_tags,
            "downloads": downloads}


def _inline_script(text: str) -> str:
    return text.replace("</script", "<\\/script")


def build_html(data: dict) -> str:
    """index.html der Web-Version mit app.css, Daten und app.js inline (keine externen Dateien)."""
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    css = (STATIC / "app.css").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    payload = _inline_script(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    title = html.escape(f"{data['info']['title']} – {APP_NAME}")
    page = re.sub(r"<title>.*?</title>", lambda _m: f"<title>{title}</title>", page, count=1, flags=re.S)
    page = page.replace('<link rel="stylesheet" href="app.css">', f"<style>\n{css}\n</style>")
    page = page.replace('<script src="app.js"></script>',
                        f"<script>window.P3D_OFFLINE = {payload};</script>\n<script>\n{_inline_script(js)}\n</script>")
    if "window.P3D_OFFLINE" not in page or "<style>" not in page:
        raise RuntimeError("index.html der Web-Version hat nicht den erwarteten Aufbau (app.css/app.js)")
    return page


def write_report(results: list, out_path: str | Path, max_px: int = DEFAULT_MAX_PX, quality: int = DEFAULT_QUALITY,
                 progress=None, title: str = "", redline: bool = True, review: bool = True) -> Path:
    out_path = Path(out_path)
    data = report_data(results, max_px, quality, progress, title, redline, review)
    out_path.write_text(build_html(data), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    """Kommandozeile (Launcher): ``python -m p3d_pdfreader --report --source <Ordner> [--source ...] --out <Datei.html>``."""
    import argparse

    from ..core.extract import find_pdfs, read_pdf
    from ..core.patterns import load
    from ..paths import ensure_timestamp, exports_dir, patterns_file
    p = argparse.ArgumentParser(prog="python -m p3d_pdfreader --report", description=f"{APP_NAME} – Offline-HTML-Bericht")
    p.add_argument("--source", action="append", required=True, help="Ordner oder PDF (mehrfach möglich)")
    p.add_argument("--out", default="", help="Ziel-HTML (Standard: Exportordner, mit Zeitstempel)")
    p.add_argument("--max-px", type=int, default=DEFAULT_MAX_PX)
    p.add_argument("--pipes", action="store_true", help="Rohrleitungsnummern mit einlesen")
    p.add_argument("--no-redline", action="store_true", help="keine Redline-PDFs einbetten (kleinere Datei)")
    p.add_argument("--no-review", action="store_true", help="keine Review-Excel je PDF einbetten")
    args = p.parse_args(argv)
    files = find_pdfs([Path(s) for s in args.source])
    if not files:
        print("Keine PDFs gefunden.", flush=True)
        return 1
    pat = load(patterns_file())
    print(f"{len(files)} PDF(s) einlesen …", flush=True)
    results = []
    for i, f in enumerate(files, start=1):
        print(f"  {i}/{len(files)} {f.name}", flush=True)
        results.append(read_pdf(f, pat, args.pipes))
    out = Path(args.out) if args.out else exports_dir() / "PDF_Reader_Bericht.html"
    out = ensure_timestamp(out)

    def progress(i: int, n: int, name: str) -> bool:
        print(f"  Bericht {i}/{n} {name}", flush=True)
        return False

    write_report(results, out, args.max_px, progress=progress, redline=not args.no_redline,
                 review=not args.no_review, title=Path(args.source[0]).name)
    print(f"Bericht gespeichert: {out} ({out.stat().st_size / 1e6:.1f} MB)", flush=True)
    return 0
