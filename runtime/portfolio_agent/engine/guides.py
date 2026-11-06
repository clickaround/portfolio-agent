"""Guides overlay: draw margin box, columns, flowlines and element boxes over rendered pages (for LOOKING at grid discipline).
Shared by scripts/guides_overlay.py and the catalogue."""
import fitz

KIND_COLOR = {"image": (0.1, 0.5, 0.9), "pdf-region": (0.1, 0.5, 0.9), "text": (0.85, 0.3, 0.1), "shape": (0.4, 0.4, 0.4)}
MM = 72 / 25.4


def _frame_from_spec(spec):
    m, g, W, H = spec["margin_mm"], spec.get("gutter_mm", 6), spec["width_mm"], spec["height_mm"]
    n = 12
    cw = (W - 2 * m - g * (n - 1)) / n
    return {"left": m, "right": W - m, "top": m, "bottom": H - m, "grid": {"n": n, "col_w": cw, "gutter": g, "x": [m + i * (cw + g) for i in range(n)]}, "rows": 6}


def draw(page, scene, spec, fr=None, label=None):
    fr = fr or _frame_from_spec(spec)
    b = spec.get("bleed_mm", 0)
    ox = b * MM
    shp = page.new_shape()
    g = fr["grid"]
    for x in g["x"]:
        shp.draw_rect(fitz.Rect(ox + x * MM, ox + fr["top"] * MM, ox + (x + g["col_w"]) * MM, ox + fr["bottom"] * MM))
    shp.finish(color=(0.55, 0.75, 0.95), fill=(0.55, 0.75, 0.95), fill_opacity=0.10, width=0)
    rows = fr.get("rows", 6)
    for r in range(1, rows):
        y = fr["top"] + (fr["bottom"] - fr["top"]) * r / rows
        shp.draw_line(fitz.Point(ox + fr["left"] * MM, ox + y * MM), fitz.Point(ox + fr["right"] * MM, ox + y * MM))
    shp.finish(color=(0.6, 0.8, 0.95), width=0.3, dashes="[1 2] 0")
    shp.draw_rect(fitz.Rect(ox + fr["left"] * MM, ox + fr["top"] * MM, ox + fr["right"] * MM, ox + fr["bottom"] * MM))
    shp.finish(color=(0.45, 0.45, 0.45), width=0.6, dashes="[3 3] 0")
    for e in scene["elements"]:
        x, y, w, h = e["box_mm"]
        shp.draw_rect(fitz.Rect(ox + x * MM, ox + y * MM, ox + (x + w) * MM, ox + (y + h) * MM))
        shp.finish(color=KIND_COLOR.get(e["kind"], (0, 0, 0)), width=0.8)
        page.insert_text(fitz.Point(ox + x * MM + 1, ox + y * MM - 1.5), e["id"], fontsize=4.5, color=KIND_COLOR.get(e["kind"], (0, 0, 0)))
    shp.commit()
    if label:   # readable tile label on a white tab (top-left, above the margin box)
        tab = page.new_shape()
        tab.draw_rect(fitz.Rect(ox + 2, ox + 1, ox + 2 + min(len(label) * 5.2 + 8, page.rect.width - 4), ox + 15))
        tab.finish(color=None, fill=(1, 1, 1), fill_opacity=0.92)
        tab.commit()
        page.insert_text(fitz.Point(ox + 6, ox + 11), label, fontsize=9, color=(0.1, 0.1, 0.1))


def overlay_sheet(pdf_path, scenes, spec, sheet_path, dpi=60, cols=3, frames=None, labels=None):
    src = fitz.open(pdf_path)
    pix = []
    for i, (pg, sc) in enumerate(zip(src, scenes)):
        draw(pg, sc, spec, frames[i] if frames else None, labels[i] if labels else None)
        pix.append(pg.get_pixmap(dpi=dpi))
    w, h = pix[0].width, pix[0].height
    rows = (len(pix) + cols - 1) // cols
    g = 8
    sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, cols * (w + g) + g, rows * (h + g) + g), False)
    sheet.set_rect(sheet.irect, (120, 120, 120))
    for i, p in enumerate(pix):
        p.set_origin(g + (i % cols) * (w + g), g + (i // cols) * (h + g))
        sheet.copy(p, p.irect)
    sheet.save(sheet_path)
    src.close()
    return sheet_path
