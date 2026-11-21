"""Seitenbilder fuer den Viewer (PyMuPDF, ohne Qt): normal farbig oder monochrom.

Monochrom wie ein Schwarz-Weiss-Plot: Helligkeit = dunkelster Farbkanal (min(R, G, B)), danach eine leichte
Kontrastkurve. Weiss bleibt weiss, jede kraeftige Farbe (auch Gelb oder Cyan) wird schwarz, Pastelltoene grau. Die
Kantenglaettung bleibt erhalten (keine harte Schwelle). Nur fuer die Anzeige - die PDF selbst wird nicht veraendert.
Nur Standardbibliothek (kein numpy): das Minimum wird mit Ganzzahl-Arithmetik ueber alle Pixel auf einmal gebildet."""
from __future__ import annotations

import pymupdf

MONO_GAMMA = 1.6        # > 1: Grautoene dunkler (Linien kraeftiger), Weiss bleibt weiss
_MONO_LUT = bytes(round(255 * (v / 255) ** MONO_GAMMA) for v in range(256))


def _lanes(data: bytes) -> int:
    """Bytes als Ganzzahl mit 16-Bit-Feldern (Wert im unteren Byte jedes Felds)."""
    wide = bytearray(2 * len(data))
    wide[0::2] = data
    return int.from_bytes(wide, "little")


def min_bytes(a: bytes, b: bytes) -> bytes:
    """Byteweises Minimum zweier gleich langer Byte-Folgen, ohne Python-Schleife je Pixel.

    Je 16-Bit-Feld: 256 + a - b liegt in 1..511 (kein Uebertrag ins Nachbarfeld); Bit 8 gesetzt <=> a >= b."""
    n = len(a)
    ia, ib = _lanes(a), _lanes(b)
    bit8 = int.from_bytes(b"\x00\x01" * n, "little")
    take_b = (((ia | bit8) - ib) & bit8) >> 8          # 1 in Feldern mit a >= b
    result = ia ^ ((ia ^ ib) & (take_b * 0xFF))
    return result.to_bytes(2 * n, "little")[0::2]


def monochrome_samples(rgb: bytes) -> bytes:
    """RGB-Pixel (3 Byte je Pixel) -> 1 Byte Grau je Pixel: dunkelster Kanal mit Kontrastkurve."""
    darkest = min_bytes(min_bytes(rgb[0::3], rgb[1::3]), rgb[2::3])
    return darkest.translate(_MONO_LUT)


def page_pixmap(page, matrix, clip=None, mono: bool = False):
    """Seitenbild ohne Alpha; ``mono`` = Graustufen-Pixmap (1 Kanal) im Monochrom-Stil, sonst RGB."""
    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False, colorspace=pymupdf.csRGB)
    if not mono:
        return pix
    samples = pix.samples
    if pix.stride != pix.width * 3:                     # Zeilen ohne Fuellbytes zusammensetzen
        samples = b"".join(samples[y * pix.stride:y * pix.stride + pix.width * 3] for y in range(pix.height))
    return pymupdf.Pixmap(pymupdf.csGRAY, pix.width, pix.height, monochrome_samples(samples), 0)
