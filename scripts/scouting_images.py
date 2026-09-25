"""Make the web images for one scouting report from its PDF.

    python3 scripts/scouting_images.py scouting/<player>/<Report>.pdf

Writes report.jpg (full width, for the report page) and thumb.jpg (small, for
the Scouting grid) next to the PDF. The page is cropped to the form's edges, so
a form exported on a letter page with wide margins still fills its card.
Needs PyMuPDF: pip install pymupdf
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF

FULL_WIDTH = 1800   # px, sharp enough to read the handwriting-size text
THUMB_WIDTH = 720   # px, a grid card is at most ~560 px wide on desktop


def content_box(page):
    """The page's non-white area, found on a coarse grayscale render."""
    dpi = 36
    pm = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
    w, h, s = pm.width, pm.height, pm.samples
    xs, ys = [], []
    for y in range(h):
        row = s[y * w:(y + 1) * w]
        for x, v in enumerate(row):
            if v < 200:
                xs.append(x)
                ys.append(y)
    if not xs:
        return page.rect
    k, pad = 72 / dpi, 4
    box = fitz.Rect(min(xs) * k - pad, min(ys) * k - pad,
                    (max(xs) + 1) * k + pad, (max(ys) + 1) * k + pad)
    return box & page.rect


def render(page, clip, width, out):
    zoom = width / clip.width
    pm = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
    pm.save(out, jpg_quality=82)
    print(f"{out}  {pm.width}x{pm.height}  {out.stat().st_size // 1024} KB")


def main(pdf_path):
    pdf = Path(pdf_path)
    page = fitz.open(pdf)[0]
    clip = content_box(page)
    render(page, clip, FULL_WIDTH, pdf.parent / "report.jpg")
    render(page, clip, THUMB_WIDTH, pdf.parent / "thumb.jpg")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
