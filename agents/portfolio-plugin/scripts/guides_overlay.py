#!/usr/bin/env python3
"""Render each page of a run with its construction lines: margin box, 12 column grid, hang line, footer flowline and every element box
(colour by kind). For LOOKING at grid discipline. Usage: guides_overlay.py <out_dir> <sheet.png> [dpi] [cols]
Reads <out_dir>/book.pdf + <out_dir>/scenes/*.json + <out_dir>/run.json (spec)."""
import json
import sys
from pathlib import Path

import fitz

KIND_COLOR = {"image": (0.1, 0.5, 0.9), "pdf-region": (0.1, 0.5, 0.9), "text": (0.85, 0.3, 0.1), "shape": (0.4, 0.4, 0.4)}


def columns(spec, n=12):
    m, g, W = spec["margin_mm"], spec.get("gutter_mm", 6), spec["width_mm"]
    cw = (W - 2 * m - g * (n - 1)) / n
    return [(m + i * (cw + g), cw) for i in range(n)]


def main(out_dir, sheet, dpi=60, cols=3):
    out = Path(out_dir)
    spec = json.loads((out / "run.json").read_text(encoding="utf-8"))["spec"]
    scenes = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((out / "scenes").glob("page-*.json"))]
    src = fitz.open(str(out / "book.pdf"))
    MM = 72 / 25.4
    b = spec.get("bleed_mm", 0)
    m = spec["margin_mm"]
    pages = []
    for pg, sc in zip(src, scenes):
        W, H = sc["size_mm"]
        shp = pg.new_shape()
        ox = b * MM
        # columns (light blue), margin box (grey), hang line approx = top margin + header band (dashed red)
        for x, cw in columns(spec):
            shp.draw_rect(fitz.Rect(ox + x * MM, ox + m * MM, ox + (x + cw) * MM, ox + (H - m) * MM))
        shp.finish(color=(0.55, 0.75, 0.95), fill=(0.55, 0.75, 0.95), fill_opacity=0.10, width=0)
        shp.draw_rect(fitz.Rect(ox + m * MM, ox + m * MM, ox + (W - m) * MM, ox + (H - m) * MM))
        shp.finish(color=(0.45, 0.45, 0.45), width=0.6, dashes="[3 3] 0")
        for e in sc["elements"]:
            x, y, w, h = e["box_mm"]
            shp.draw_rect(fitz.Rect(ox + x * MM, ox + y * MM, ox + (x + w) * MM, ox + (y + h) * MM))
            shp.finish(color=KIND_COLOR.get(e["kind"], (0, 0, 0)), width=0.8)
            pg.insert_text(fitz.Point(ox + x * MM + 1, ox + y * MM - 1.5), e["id"], fontsize=4.5, color=KIND_COLOR.get(e["kind"], (0, 0, 0)))
        shp.commit()
        pages.append(pg.get_pixmap(dpi=dpi))
    w, h = pages[0].width, pages[0].height
    rows = (len(pages) + cols - 1) // cols
    g = 8
    sheetpm = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + g) + g, rows * (h + g) + g), False)
    sheetpm.set_rect(sheetpm.irect, (120, 120, 120))
    for i, p in enumerate(pages):
        p.set_origin(g + (i % cols) * (w + g), g + (i // cols) * (h + g))
        sheetpm.copy(p, p.irect)
    sheetpm.save(sheet)
    print(sheet)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], int(a[3]) if len(a) > 3 else 60, int(a[4]) if len(a) > 4 else 3)
