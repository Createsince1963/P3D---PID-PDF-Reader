"""Viewer-Anzeige: Monochrom-Darstellung und gruen/rote Umrandung nach Review-Status."""
from __future__ import annotations

import os
import time
from types import SimpleNamespace

import pymupdf
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication  # noqa: E402

from test_extract import SAMPLE, needs_sample  # noqa: E402

from p3d_pdfreader.core.render import page_pixmap  # noqa: E402
from p3d_pdfreader.core.review_store import status_hits  # noqa: E402


def _color_pdf(path):
    doc = pymupdf.open()
    page = doc.new_page(width=200, height=100)
    page.draw_rect(pymupdf.Rect(10, 10, 90, 90), color=(1, 1, 0), fill=(1, 1, 0))    # Gelb
    page.draw_rect(pymupdf.Rect(110, 10, 190, 90), color=(0, 0, 1), fill=(0, 0, 1))  # Blau
    doc.save(path)
    doc.close()
    return path


def test_monochrome_pixmap(tmp_path):
    with pymupdf.open(_color_pdf(tmp_path / "c.pdf")) as doc:
        page = doc[0]
        color = page_pixmap(page, pymupdf.Matrix(1, 1))
        mono = page_pixmap(page, pymupdf.Matrix(1, 1), mono=True)
        assert color.n == 3 and mono.n == 1
        assert (mono.width, mono.height) == (color.width, color.height)
        assert mono.pixel(150, 50)[0] < 10        # Blau -> schwarz
        assert mono.pixel(50, 50)[0] < 10         # Gelb -> schwarz (nicht fast weiss wie bei Graustufen)
        assert mono.pixel(100, 5)[0] == 255       # Weiss bleibt weiss
        assert mono.tobytes("png")[:4] == b"\x89PNG"


def test_status_hits_all_tags_framed():
    tags = [SimpleNamespace(type="Armatur", tag="A1", hits=[(0, (1, 1, 2, 2))]),
            SimpleNamespace(type="Armatur", tag="A2", hits=[(0, (3, 3, 4, 4))]),
            SimpleNamespace(type="Armatur", tag="A3", hits=[(0, (5, 5, 6, 6))])]
    store = SimpleNamespace(entries={"Armatur|A2": {"Review": "Korrektur erforderlich"},
                                     "Armatur|A3": {"Review": "OK"}})
    ok, faulty = status_hits(tags, store)
    assert len(ok) == 2 and faulty == [[(0, (3, 3, 4, 4))]]
    ok, faulty = status_hits(tags, None)           # ohne Review: alle gruen
    assert len(ok) == 3 and faulty == []


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@needs_sample
def test_viewer_monochrome_and_status_frames(app, tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader.gui.main_window import MainWindow
    w = MainWindow(app, "test")
    w.scan([SAMPLE])
    start = time.time()
    while w._thread is not None and time.time() - start < 30:
        app.processEvents()
    page = w.page
    page.files.table.selectRow(0)
    preview = page.preview
    result = page._store_result
    on_page = sum(1 for t in result.tags for p, _r in t.hits if p == preview.page)
    assert len(preview._status_items) == on_page > 0
    ok_pen = preview._status_items[0].pen().color().name()
    first = result.tags[0]
    page.store.set(first.type, first.tag, "Review", "Korrektur erforderlich")
    page._store_changed()
    colors = {i.pen().color().name() for i in preview._status_items}
    assert len(colors) == 2 and ok_pen in colors
    page.viewer.mono_button.setChecked(True)
    assert preview.monochrome and preview._base.pixmap().toImage().isGrayscale()
    page.viewer.mono_button.setChecked(False)
    assert not preview.monochrome
    page.store.dirty = False
    w.close()


def test_no_tag_is_not_marked(tmp_path):
    """Review "No Tag": kein Rahmen im Viewer und im Redline-PDF, Pos.-Nr. der uebrigen wie in der Review-Excel."""
    import pymupdf
    from p3d_pdfreader.core.extract import PdfResult, Tag
    from p3d_pdfreader.core.redline import write_redline
    from p3d_pdfreader.core.review import positions
    from p3d_pdfreader.core.review_store import REVIEW_VALUES, key

    assert "No Tag" in REVIEW_VALUES
    pdf = tmp_path / "p.pdf"
    with pymupdf.open() as doc:
        doc.new_page(width=600, height=400)
        doc.save(pdf)
    no = Tag(tag="MARCH-2025", type="Instrument", hits=[(0, (50, 50, 100, 60)), (0, (50, 90, 100, 100))])
    yes = Tag(tag="VH328", type="Armatur", hits=[(0, (200, 200, 240, 210))])

    class Store:
        entries = {key(no.type, no.tag): {"Review": "No Tag"}}

    ok, faulty = status_hits([no, yes], Store())
    assert ok == [yes.hits] and faulty == []
    tags = [no, yes]
    out = tmp_path / "r.pdf"
    assert write_redline(PdfResult(path=pdf, tags=tags), out, store=Store(), layer=False) == 1
    pos = next(p.pos for p in positions(tags) if p.tag is yes)
    with pymupdf.open(out) as doc:
        page = doc[0]                                             # Seite halten, sonst sind die Annotationen ungueltig
        annots = list(page.annots())
        assert len(annots) == 3                                   # Rahmen + Pos.-Nr. von VH328 + Uebersicht
        assert [a.info["subject"] for a in annots if a.type[1] == "Square"] == [f"Pos. {pos} – VH328"]
        assert any("nicht markiert): 1" in a.info["content"] for a in annots)
