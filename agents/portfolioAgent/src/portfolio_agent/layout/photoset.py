"""Photo sets: 2-6 photographs on one page (knowledge/patterns/photosets.json).

A template is a list of cells as fractions of the content band under the heading. The engine snaps cell columns to the
column grid, keeps a gutter between cells, fits each photograph inside its cell without cropping (or covers the cell when the
host sets `crop: "cover"` - raster photos are then cropped centred, as on bleed pages), and chooses the template whose cells
waste the least area for these photographs' aspects. The host may name a template (`photoset: "lead-left-3"`) instead; the
first asset is the lead. Captions: one under each cell when `captions` are given, else the page caption under the set.

Templates are data: a new arrangement is one JSON entry, never code (tests check cells never overlap).
"""
import json

from portfolio_agent.core.geometry import fit
from portfolio_agent.core.workspace import PATTERNS_DIR

FILE = PATTERNS_DIR / "photosets.json"


def templates():
    return {t["id"]: t for t in json.loads(FILE.read_text(encoding="utf-8"))["templates"]}


def _mirror(cells):
    return [[round(1 - f1, 4), round(1 - f0, 4), r0, r1] for f0, f1, r0, r1 in cells]


def _box(c, cell, top, avail_h):
    """fraction cell -> mm box: columns snapped to the grid, rows exact with half a gutter between neighbours."""
    f0, f1, r0, r1 = cell
    n = c.grid["n"]
    c0 = min(round(f0 * n), n - 1)
    c1 = min(max(c0 + 1, round(f1 * n)), n)
    x = c.x(c0)
    w = c.x(c1 - 1) + c.grid["col_w"] - x
    y = top + r0 * avail_h + (c.gap / 2 if r0 > 0 else 0)
    y1 = top + r1 * avail_h - (c.gap / 2 if r1 < 1 else 0)
    return [round(x, 2), round(y, 2), round(w, 2), round(y1 - y, 2)]


def fill_score(c, cells, aspects, top, avail_h, cap_h):
    """Mean share of each cell that its photograph fills when fitted without cropping (1.0 = the cells match the photos)."""
    tot = 0.0
    for cell, a in zip(cells, aspects):
        x, y, w, h = _box(c, cell, top, avail_h)
        h = max(1.0, h - cap_h)
        r = fit(a, [x, y, w, h], "lt")
        tot += (r[2] * r[3]) / (w * h)
    return tot / len(cells)


def choose(c, k, aspects, top, avail_h, cap_h, forced=None):
    tpl = templates()
    if forced:
        if forced not in tpl:
            raise KeyError(f"unknown photoset {forced!r}; known: {sorted(tpl)}")
        return tpl[forced]
    cands = [t for t in tpl.values() if t["k"] == k]
    if not cands:
        raise KeyError(f"no photoset template for {k} photographs (2-6)")
    return max(cands, key=lambda t: fill_score(c, t["cells"], aspects, top, avail_h, cap_h))


def photoset(c):
    ts, n, pg = c.ts, c.grid["n"], c.page
    k = len(pg["assets"])
    caps = pg.get("captions") or []
    band = ts.line_mm("label") + ts.line_mm("heading") + 4 * c.s
    if c.variant == 0:
        c.label(c.col_box(0, 3, c.hang, ts.line_mm("label")))
        c.text("title", c.col_box(0, n // 2, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), pg["title"], "heading")
    else:
        c.label(c.col_box(n // 2, 3, c.hang, ts.line_mm("label")))
        c.text("title", c.col_box(n // 2, n - n // 2, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), pg["title"], "heading")
    top = c.hang + band + c.gap
    page_cap = "" if caps else pg.get("caption", "")
    foot_h = ts.line_mm("caption", 2) + 1.5 * c.s if page_cap else 0
    avail_h = c.bottom - top - foot_h
    cap_h = ts.line_mm("caption", 2) + 1.5 * c.s if caps else 0
    aspects = [c.aspect(i) for i in range(k)]
    t = choose(c, k, aspects, top, avail_h, cap_h, pg.get("photoset"))
    cells = _mirror(t["cells"]) if c.variant == 1 else t["cells"]
    cover = pg.get("crop") == "cover"
    c.tag(f"photoset-{t['id']}")
    for i, cell in enumerate(cells[:k]):
        x, y, w, h = _box(c, cell, top, avail_h)
        img_h = h - cap_h
        if cover:
            r = c.cover(i, [x, y, w, img_h])
        else:
            r = c.graphic(i, [x, y, w, img_h], "lt")
        if caps:
            c.text("caption" if i == 0 else f"caption-{i + 1}", [r[0], r[1] + r[3] + 1.0 * c.s, r[2], ts.line_mm("caption", 2)], caps[i] if i < len(caps) else "", "caption")
    if page_cap:
        c.text("caption", c.col_box(0, n // 2, c.bottom - ts.line_mm("caption", 2), ts.line_mm("caption", 2)), page_cap, "caption")


COMPOSITIONS = {"photoset": photoset}
