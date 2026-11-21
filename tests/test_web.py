"""Web-Server (python -m p3d_pdfreader.web): API gegen echte Plots, Ergebnisse identisch mit core.read_pdf."""
from __future__ import annotations

import io
import json
import shutil
import threading
import time
import urllib.error
import urllib.request
import zipfile
from http.cookiejar import CookieJar
from urllib.parse import quote

import pytest

from p3d_pdfreader.core.extract import read_pdf
from p3d_pdfreader.web.server import make_server
from test_extract import SAMPLES, SAMPLE, needs_sample

ROTATED = SAMPLES / "SGOPS-P-DL1-PID-00-EQPM-012.pdf"


class Client:
    def __init__(self, base: str) -> None:
        self.base = base
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def req(self, path: str, data: bytes | None = None, headers: dict | None = None):
        r = urllib.request.Request(self.base + path, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
        with self.opener.open(r, timeout=120) as res:
            return res.status, dict(res.headers), res.read()

    def json(self, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        return json.loads(self.req(path, data, {"Content-Type": "application/json"})[2])

    def upload(self, path):
        return json.loads(self.req("/api/upload", path.read_bytes(), {"X-File-Name": quote(path.name)})[2])


@pytest.fixture()
def server(tmp_path):
    src = tmp_path / "quelle"
    src.mkdir()
    if SAMPLE.is_file():
        shutil.copy(SAMPLE, src)
    srv = make_server("127.0.0.1", 0, [str(src)])
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", src
    srv.shutdown()
    srv.server_close()


def test_static_and_info(server):
    base, src = server
    c = Client(base)
    status, headers, body = c.req("/")
    assert status == 200 and b"P3D PDF Reader" in body
    assert "p3d_pdfreader_sid" in headers.get("Set-Cookie", "")
    for asset in ("/app.js", "/app.css"):
        assert c.req(asset)[0] == 200
    info = c.json("/api/info")
    assert any(s["path"] == str(src.resolve()) and s["exists"] for s in info["sources"])
    assert info["version"]


def test_no_path_traversal_and_unknown_ids(server):
    c = Client(server[0])
    for path in ("/../VERSION", "/%2e%2e/%2e%2e/VERSION", "/api/files/999/tags"):
        with pytest.raises(urllib.error.HTTPError) as err:
            c.req(path)
        assert err.value.code == 404


def test_upload_rejects_non_pdf(server):
    c = Client(server[0])
    with pytest.raises(urllib.error.HTTPError) as err:
        c.req("/api/upload", b"kein pdf", {"X-File-Name": "x.pdf"})
    assert err.value.code == 400


@needs_sample
def test_scan_matches_core(server):
    c = Client(server[0])
    c.json("/api/scan", {"sources": [len(c.json("/api/info")["sources"]) - 1]})
    for _ in range(600):
        st = c.json("/api/scan")
        if st["finished"]:
            break
        time.sleep(0.1)
    assert st["finished"] and st["done"] == 1 and not st["error"]
    files = c.json("/api/files")
    assert len(files) == 1
    f = files[0]
    expected = read_pdf(SAMPLE)
    assert f["drawing_no"] == expected.drawing_no == "SGOPS-P-DL1-PID-00-EQPM-001"
    assert f["author"] == expected.author_display and f["revision"] == expected.revision
    tags = c.json(f"/api/files/{f['id']}/tags")
    assert {(t["type"], t["tag"], t["count"]) for t in tags} == {(t.type, t.tag, t.count) for t in expected.tags}
    assert len(c.json("/api/tags")) == len(expected.tags)


@needs_sample
def test_sessions_are_separate(server):
    a, b = Client(server[0]), Client(server[0])
    a.upload(SAMPLE)
    assert len(a.json("/api/files")) == 1
    assert b.json("/api/files") == []


@needs_sample
@pytest.mark.skipif(not ROTATED.is_file(), reason="gedrehter Beispiel-Plot fehlt")
def test_rotated_plot_pages_and_hits():
    """Fundstellen in sichtbarer Lage - innerhalb der vom Server gemeldeten Seitengroesse."""
    srv = make_server("127.0.0.1", 0, [])
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        c = Client(f"http://127.0.0.1:{srv.server_address[1]}")
        f = c.upload(ROTATED)
        w, h = c.json(f"/api/files/{f['id']}/pages")[0]
        for t in c.json(f"/api/files/{f['id']}/tags"):
            for page, r in t["hits"]:
                assert page == 0 and -1 <= r[0] < r[2] <= w + 1 and -1 <= r[1] < r[3] <= h + 1
    finally:
        srv.shutdown()
        srv.server_close()


@needs_sample
def test_render_and_downloads(server):
    c = Client(server[0])
    f = c.upload(SAMPLE)
    fid = f["id"]
    status, headers, png = c.req(f"/api/files/{fid}/render?page=0&zoom=0.3")
    assert headers["Content-Type"] == "image/png" and png[:8] == b"\x89PNG\r\n\x1a\n"
    status, headers, png = c.req(f"/api/files/{fid}/render?page=0&zoom=4&x0=100&y0=100&x1=300&y1=200")
    assert png[:4] == b"\x89PNG"
    pdf = c.req(f"/api/files/{fid}/pdf")[2]
    assert pdf == SAMPLE.read_bytes()                                      # Original unveraendert ausgeliefert

    tags = c.json(f"/api/files/{fid}/tags")
    dups = [[t["type"], t["tag"]] for t in tags if t["duplicate"]] or [[tags[0]["type"], tags[0]["tag"]]]
    _s, h, red = c.req("/api/redline", json.dumps({"id": fid, "tags": dups}).encode(), {"Content-Type": "application/json"})
    assert red[:4] == b"%PDF" and "_Redline_" in h["Content-Disposition"]
    import pymupdf
    with pymupdf.open(stream=red, filetype="pdf") as doc:
        annots = [a for p in doc for a in p.annots()]
    assert len(annots) >= 2 * sum(len(t["hits"]) for t in tags if [t["type"], t["tag"]] in dups)

    _s, h, xlsx = c.req("/api/review", json.dumps({"ids": [fid]}).encode(), {"Content-Type": "application/json"})
    assert xlsx[:2] == b"PK" and "_Review_" in h["Content-Disposition"]
    _s, _h, xlsx = c.req("/api/export", json.dumps({"format": "xlsx"}).encode(), {"Content-Type": "application/json"})
    assert xlsx[:2] == b"PK"
    _s, _h, z = c.req("/api/export", json.dumps({"format": "csv"}).encode(), {"Content-Type": "application/json"})
    names = zipfile.ZipFile(io.BytesIO(z)).namelist()
    assert any(n.endswith("_Dateien.csv") for n in names) and len(names) == 2

    payload = {"ids": [fid], "options": {"redline": True, "review_each": True, "review_total": True}}
    _s, _h, z = c.req("/api/bulk", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    names = zipfile.ZipFile(io.BytesIO(z)).namelist()
    assert len(names) == 3 and all(n.startswith("Review_") for n in names)
    assert SAMPLE.read_bytes() == pdf                                      # Quelle nie veraendert
