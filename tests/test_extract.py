"""Kern-Tests gegen echte Plant-3D-Plots (werden uebersprungen, wenn der Beispielordner fehlt)."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pytest

from p3d_pdfreader.core import export
from p3d_pdfreader.core.extract import find_pdfs, pdf_date, read_pdf
from p3d_pdfreader.paths import PathSettings

SAMPLES = Path(os.environ.get("P3D_PDFREADER_SAMPLES", Path.home() / "Downloads" / "PID Plots"))
SAMPLE = SAMPLES / "SGOPS-P-DL1-PID-00-EQPM-001.pdf"
needs_sample = pytest.mark.skipif(not SAMPLE.is_file(), reason="Beispiel-PDFs fehlen")


def test_pdf_date():
    assert pdf_date("D:20261019103250") == datetime(2026, 10, 19, 10, 32, 50)
    assert pdf_date("") is None


@needs_sample
def test_sample_metadata_and_title_block():
    r = read_pdf(SAMPLE)
    assert not r.error
    assert r.created == datetime(2026, 10, 19, 10, 32, 50)
    assert r.drawn == "K.VIDIC"
    assert r.author_display == "K.VIDIC"
    assert r.drawing_no == "SGOPS-P-DL1-PID-00-EQPM-001"
    assert (r.revision, r.revision_date, r.revision_by) == ("B", "03 AUG 2026", "KVI")
    assert r.plot_user


@needs_sample
def test_sample_tags():
    tags = {(t.type, t.tag) for t in read_pdf(SAMPLE).tags}
    for expected in [("Instrument", "TIT-130"), ("Instrument", "PDIT-410"), ("Equipment", "111PMP01"),
                     ("Armatur", "VH340"), ("Volltag", "203-17-111-TZIT-011")]:
        assert expected in tags
    assert not any(tag.startswith(("MIN", "HALF-", "SHORT-")) for _t, tag in tags)


@needs_sample
def test_export(tmp_path):
    results = [read_pdf(SAMPLE)]
    assert export.write_xlsx(tmp_path / "x.xlsx", results).is_file()
    export.write_csv(tmp_path / "x.csv", export.TAG_HEADERS, export.tag_rows(results))
    assert (tmp_path / "x.csv").read_text(encoding="utf-8-sig").startswith("PDF;")


def test_path_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    s = PathSettings.load()
    assert s.add_source(tmp_path)
    assert not s.add_source(str(tmp_path) + os.sep)
    s.save()
    assert PathSettings.load().sources == [str(tmp_path.resolve())]
    (tmp_path / "a.pdf").write_bytes(b"")
    assert find_pdfs([tmp_path]) == [tmp_path / "a.pdf"]


@needs_sample
def test_redline(tmp_path):
    import pymupdf
    from p3d_pdfreader.core.redline import write_redline
    r = read_pdf(SAMPLE)
    out = tmp_path / "r.pdf"
    n = write_redline(r, out)
    assert n == sum(len(t.hits) for t in r.tags)
    with pymupdf.open(out) as doc:
        annots = list(doc[0].annots())
        assert len(annots) == 2 * n + 1               # Rahmen + Pos.-Nr. je Fundstelle + Uebersicht
        assert any("Doppelter Tag" in a.info["content"] for a in annots)
    assert read_pdf(SAMPLE).tags                      # Original unveraendert lesbar


ROTATED = SAMPLES / "SGOPS-P-DL1-PID-00-EQPM-012.pdf"


@pytest.mark.skipif(not ROTATED.is_file(), reason="gedrehter Beispielplot fehlt")
def test_rotated_page(tmp_path):
    """/Rotate 270: Positionen in sichtbarer Lage, Schriftfeld erkannt, Redline-Rahmen umschliesst den Tag-Text."""
    import pymupdf
    from p3d_pdfreader.core.redline import write_redline
    r = read_pdf(ROTATED)
    assert r.drawn == "E.BUTSCH" and r.drawing_no.endswith("EQPM-012")
    tag = next(t for t in r.tags if t.tag == "631VES01")
    assert tag.rect[2] - tag.rect[0] > tag.rect[3] - tag.rect[1]      # waagerecht wie angezeigt
    out = tmp_path / "rot.pdf"
    write_redline(r, out, [tag])
    with pymupdf.open(out) as doc:
        page = doc[0]
        annot = next(a for a in page.annots() if a.type[1] == "Square")
        assert "631VES01" in page.get_textbox(annot.rect)


@needs_sample
def test_vertical_tags_and_no_single_letter_instruments():
    """Senkrechte Beschriftung (VH203, SGL010) wird erkannt; Revisionsdreiecke ("B" + Nummer) sind keine Instrumente."""
    r = read_pdf(SAMPLES / "SGOPS-P-DL1-PID-00-EQPM-002.pdf")
    tags = {t.tag for t in r.tags}
    assert {"VH203", "SGL010"} <= tags
    assert not [t for t in r.tags if t.type == "Instrument" and len(t.tag.split("-")[0]) < 2]


MULTI = SAMPLES / "SGOPS-P-DL1-PID-00-EQPM-003.pdf"


@pytest.mark.skipif(not MULTI.is_file(), reason="mehrseitiger Beispielplot fehlt")
def test_multipage_counts_per_page(tmp_path):
    """EQPM-003: Seite 2 = dieselbe Zeichnung mit Markups. Ein Tag auf beiden Seiten ist NICHT doppelt; Anzahl = je Seite."""
    import pymupdf
    from p3d_pdfreader.core.redline import write_redline
    from p3d_pdfreader.core.review import positions
    r = read_pdf(MULTI)
    sgl = next(t for t in r.tags if t.tag == "SGL010")
    assert sgl.pages == [0, 1] and sgl.count == 1 and not sgl.duplicate and sgl.pages_text == "1, 2"
    assert sum(t.duplicate for t in r.tags) < 0.2 * len(r.tags)          # vorher 162 von 171
    pos = positions([sgl])
    assert [(p.page, p.total) for p in pos] == [(0, 1), (1, 1)]
    out = tmp_path / "multi.pdf"
    write_redline(r, out, [sgl])
    with pymupdf.open(out) as doc:
        assert all(any(a.type[1] == "Square" for a in doc[i].annots()) for i in (0, 1))


def test_output_names_always_timestamped_and_originals_protected(tmp_path, monkeypatch):
    """Ausgaben: Zeitstempel wird ergaenzt, vorhandene Dateien nie ueberschrieben; Original-PDFs sind gesperrt.
    Review-Speichern legt je Speichern einen neuen Stand an, geladen wird der neueste."""
    monkeypatch.setenv("P3D_PDFREADER_HOME", str(tmp_path))
    from p3d_pdfreader import paths
    from p3d_pdfreader.core.review_store import ReviewStore
    plain = paths.ensure_timestamp(tmp_path / "Tags.xlsx")
    assert paths.has_timestamp(plain.stem) and plain.suffix == ".xlsx"
    stamped = tmp_path / "X_2026-11-20_10-00-00.pdf"
    stamped.write_bytes(b"")
    assert paths.ensure_timestamp(stamped) != stamped                  # vorhanden -> Zaehler, kein Ueberschreiben
    original = tmp_path / "orig.pdf"
    original.write_bytes(b"%PDF")
    paths.protect([original])
    assert paths.is_protected(str(original).upper()) or paths.is_protected(original)
    store = ReviewStore(original)
    store.set("Armatur", "VH1", "Review", "OK")
    first = store.save()
    store.set("Armatur", "VH1", "Review", "Klärung")
    second = store.save()
    assert first != second and first.exists() and second.exists()
    assert ReviewStore(original).values("Armatur", "VH1")[0] == "Klärung"
    assert original.read_bytes() == b"%PDF"                             # PDF unveraendert


def _pipe_pdf(path: Path) -> Path:
    """Kleine PDF: Rohrleitungsnummern waagerecht, senkrecht (90°), mit getrennter Nennweite und in zwei Teilen."""
    import pymupdf
    with pymupdf.open() as doc:
        page = doc.new_page(width=800, height=600)
        page.insert_text((50, 100), 'TFHR_SS01_001_1"', fontsize=9)
        page.insert_text((50, 150), 'TFHR_SS01_004_1 1/2"', fontsize=9)
        page.insert_text((50, 200), '201_07_092PS_ST03 _205_1 1/2"', fontsize=9)
        page.insert_text((50, 250), 'AV_TL02_XXX_2"', fontsize=9)            # Platzhalter: keine Nummer
        page.insert_text((50, 300), 'TFHR_SS01_001_1"', fontsize=9)          # zweites Label derselben Leitung
        page.insert_text((400, 400), 'PFC_ST10_006_1"', fontsize=9, rotate=90)
        doc.save(path)
    return path


def test_pipe_lines_optional_horizontal_and_vertical(tmp_path):
    pdf = _pipe_pdf(tmp_path / "pipes.pdf")
    assert not [t for t in read_pdf(pdf).tags if t.type == "Rohrleitung"]          # Standard: aus
    pipes = {t.tag: t for t in read_pdf(pdf, pipes=True).tags if t.type == "Rohrleitung"}
    assert set(pipes) == {'TFHR_SS01_001_1"', 'TFHR_SS01_004_1 1/2"', '201_07_092PS_ST03_205_1 1/2"',
                          'PFC_ST10_006_1"'}
    assert pipes['TFHR_SS01_001_1"'].count == 2
    vertical = pipes['PFC_ST10_006_1"'].rect
    assert vertical[3] - vertical[1] > vertical[2] - vertical[0]                    # senkrecht
    split = pipes['TFHR_SS01_004_1 1/2"'].rect
    assert split[2] - split[0] > 80                                                 # Rahmen ueber beide Woerter


@needs_sample
def test_sample_pipe_lines():
    pipes = {t.tag for t in read_pdf(SAMPLE, pipes=True).tags if t.type == "Rohrleitung"}
    assert {'TFHR_SS01_001_1"', 'TFHS_SS01_002_1"', 'PFC_ST10_006_1"', 'TFHR_SS01_004_1 1/2"',
            '203_17_112PFC_ST10_013_1"'} <= pipes
