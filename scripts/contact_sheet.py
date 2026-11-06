#!/usr/bin/env python3
"""Contact sheet PNG of a PDF's pages (for LOOKING at output). Usage: contact_sheet.py in.pdf out.png [dpi] [cols]"""
import sys
import fitz


def main(pdf, out, dpi=60, cols=3):
    d = fitz.open(pdf)
    pix = [p.get_pixmap(dpi=dpi) for p in d]
    w, h = pix[0].width, pix[0].height
    rows = (len(pix) + cols - 1) // cols
    g = 8
    sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + g) + g, rows * (h + g) + g), False)
    sheet.set_rect(sheet.irect, (120, 120, 120))
    for i, p in enumerate(pix):
        p.set_origin(g + (i % cols) * (w + g), g + (i // cols) * (h + g))
        sheet.copy(p, p.irect)
    sheet.save(out)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], int(a[3]) if len(a) > 3 else 60, int(a[4]) if len(a) > 4 else 3)
