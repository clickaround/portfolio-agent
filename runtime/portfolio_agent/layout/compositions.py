"""Page compositions on a column grid (knowledge/editorial/layout-craft.md §1-3, §5).

Every composition: elements hang from ONE flowline (`c.hang`), snap to column edges, keep captions/labels in the same marker
positions page after page, and leave white space that is bounded by the grid (a short text column, a top-hung hero) rather than
leftover after a fit. Variant 1 mirrors or swaps the band order so adjacent pages never repeat.

Ids keep the shared conventions (core/conventions.py): title-NN, body-NN, caption-NN(-k), label-NN, header-NN-*, photo/drawing-NN-k, hairline-NN(-k).
"""
from portfolio_agent.core.geometry import fit
from . import treelayout as TL

PT = 0.3528


def split_lead(txt):
    """'Third floor plan. The rest...' -> ('Third floor plan.', 'The rest...') when the lead is short; else ('', txt)."""
    import re
    m = re.match(r"^(.{3,48}?[.:])\s+(.{8,})$", txt.strip(), re.S)
    return (m.group(1), m.group(2)) if m else ("", txt)


class Ctx:
    """Everything a composition needs for one page (plain data, no I/O)."""

    def __init__(self, page, assets, spec, grid, ts, variant):
        self.page, self.A, self.spec, self.grid, self.ts, self.variant = page, assets, spec, grid, ts, variant
        s = ts.scale_factor
        W, H, m = spec["width_mm"], spec["height_mm"], spec["margin_mm"]
        self.W, self.H, self.m, self.s = W, H, m, s
        self.left, self.right = m, W - m
        self.cw = W - 2 * m
        self.gap = spec.get("gutter_mm", 6)
        self.header_h = ts.line_mm("label") + 3.0 * s if ts.header else 0.0
        self.footer_h = ts.line_mm("folio") + 3.5 * s if ts.footer else 0.0
        self.hang = m + self.header_h                       # the flowline content hangs from
        self.bottom = H - m - self.footer_h                 # content stops here
        self.els = []
        self.pn = page["page"]
        self.b = float(spec.get("bleed_mm", 0) or 0)        # bleed_* compositions extend graphics to -b .. W+b (layout/bleed.py)
        self.dark = bool(page.get("dark"))                  # dark page: ts is already inverted by book.build_scene

    # ---- grid helpers ----
    def x(self, col):
        return self.grid["x"][col]

    def span_w(self, span):
        return round(span * self.grid["col_w"] + (span - 1) * self.grid["gutter"], 2)

    def cols_for(self, width_mm):
        """Smallest span whose width >= width_mm (capped at n)."""
        for s in range(1, self.grid["n"] + 1):
            if self.span_w(s) >= width_mm - 0.01:
                return s
        return self.grid["n"]

    def col_box(self, start, span, y, h):
        return [self.x(start), y, self.span_w(span), h]

    # ---- element helpers ----
    def tag(self, name):
        """Record which composition branch produced this page (plan.json audit + tests)."""
        self.page["_composition"] = name

    def el(self, i, kind, box, z=0, asset=None, text=None, role=None, locked=False, style=None):
        e = {"id": i, "kind": kind, "asset_id": asset, "box_mm": [round(v, 2) for v in box], "z_index": z, "locked": locked, "allow_overlap": False}
        if kind in ("image", "pdf-region", "svg"):
            e["allow_crop"] = False
        if text is not None:
            e["text"] = text
        if role:
            e["font_size_pt"] = round(self.ts.pt(role), 1)
            e["style"] = style or self.ts.style(role, text or "")
        elif style:
            e["style"] = style
        self.els.append(e)
        return e

    def graphic(self, idx, box, align="lt", z=0):
        a = self.A[self.page["assets"][idx]]
        r = fit(a["aspect"], box, align)
        self.el(f"{ {'drawing': 'drawing', 'diagram': 'diagram'}.get(a['role'], 'photo') }-{self.pn:02d}-{idx + 1}", a["kind"], r, z, asset=a["id"], locked=True)
        return r

    def cover(self, idx, box, eid=None):
        """A graphic that COVERS `box`. Raster images are cropped centred (element `crop` = visible fraction of the source);
        vector assets (pdf-region/svg) are never cropped (legacy gate) and are contain-fitted inside the box instead."""
        a = self.A[self.page["assets"][idx]]
        eid = eid or f"{ {'drawing': 'drawing', 'diagram': 'diagram'}.get(a['role'], 'photo') }-{self.pn:02d}-{idx + 1}"
        x, y, w, h = box
        if a["kind"] == "image":
            ba, aa = w / h, a["aspect"]
            fx, fy = (self.page.get("focus") or [0.5, 0.5])[:2]   # host-chosen focal point (fractions of the source); default centred
            if aa > ba:                      # source wider than the box: crop the sides around the focal x
                fw = ba / aa
                x0 = min(max(fx - fw / 2, 0.0), 1 - fw)
                crop = [round(x0, 4), 0.0, round(x0 + fw, 4), 1.0]
            else:
                fh = aa / ba
                y0 = min(max(fy - fh / 2, 0.0), 1 - fh)
                crop = [0.0, round(y0, 4), 1.0, round(y0 + fh, 4)]
            e = self.el(eid, "image", box, 0, asset=a["id"], locked=True)
            e["crop"] = crop
            return [round(v, 2) for v in box]
        r = fit(a["aspect"], box, "c")
        self.el(eid, a["kind"], r, 0, asset=a["id"], locked=True)
        return r

    def bleed_graphic(self, idx, box, k=1):
        """`cover` with a `bleed-NN-k` id: may run past the trim into the bleed, exempt from the margin gate, may sit under a panel."""
        return self.cover(idx, box, f"bleed-{self.pn:02d}-{k}")

    def panel(self, box, name="", opacity=0.9):
        """Solid panel under text that sits on a bleed graphic (text over an image is only allowed inside a panel: gates)."""
        return self.el(f"panel-{self.pn:02d}{name}", "shape", box, 1, style={"fill": self.ts.paper, "opacity": opacity})

    def text(self, name, box, txt, role, style=None):
        if not txt:
            return None
        if role == "caption" and style is None:
            lead, rest = split_lead(txt)
            lh = self.ts.line_mm("caption")
            if lead and box[3] >= self.ts.line_mm("caption", 3) and TL.text_need_mm2(rest, self.ts.pt("caption")) * 1.2 <= box[2] * (box[3] - lh):   # bold lead on its own line only when the rest still fits below
                self.el(f"{name}-{self.pn:02d}", "text", [box[0], box[1], box[2], lh], 2, text=lead, role="caption", style={**self.ts.style("caption", lead), "color": self.ts.ink, "font": self.ts.heading_font or self.ts.body_font} if (self.ts.heading_font or self.ts.body_font) else {**self.ts.style("caption", lead), "color": self.ts.ink})
                return self.el(f"{name}-lead-{self.pn:02d}", "text", [box[0], box[1] + lh, box[2], max(lh, box[3] - lh)], 2, text=rest, role="caption")
        return self.el(f"{name}-{self.pn:02d}", "text", box, 2, text=txt, role=role, style=style)

    def hairline(self, name, x, y, w):
        return self.el(f"hairline-{self.pn:02d}{name}", "shape", [x, y, w, 0.25], 1, style={"fill": self.ts.hairline})

    def label(self, box, name="label"):
        pg = self.page
        txt = f"{pg.get('section_no', 0):02d} / {pg.get('section', '')}" if pg.get("section") else ""
        return self.text(name, box, self.ts.label_text(txt), "label")

    def aspect(self, idx):
        return self.A[self.page["assets"][idx]]["aspect"]

    def heading_block(self, start, span, y, with_body=True, body_key="text"):
        """label / heading / body stacked in one column from y. Returns y after the block."""
        ts, pg = self.ts, self.page
        w = self.span_w(span)
        lab = self.label(self.col_box(start, span, y, ts.line_mm("label")))
        y2 = y + (ts.line_mm("label") + 2.0 * self.s if lab else 0)
        hh = ts.line_mm("heading", 2 if len(pg["title"]) * (1 / ts.chars_per_mm("heading", pg["title"])) > w else 1)
        self.text("title", self.col_box(start, span, y2, hh), pg["title"], "heading")
        y3 = y2 + hh + 2.5 * self.s
        body = pg.get(body_key, "") if with_body else ""
        if body and len(body) <= 160 and not pg.get("_plain"):   # a short text is a pull quote, not a paragraph (critic: "orphaned one-line body")
            need = TL.text_need_mm2(body, ts.pt("pull")) / w * 1.3 + ts.line_mm("pull")
            h = min(max(need, ts.line_mm("pull", 2)), self.bottom - y3)
            self.text("body", self.col_box(start, span, y3, h), body, "pull")
            y3 += h
        elif body:
            need = TL.text_need_mm2(body, ts.pt("body")) / w * 1.25 + ts.line_mm("body")
            h = min(max(need, ts.line_mm("body", 2)), self.bottom - y3)
            self.text("body", self.col_box(start, span, y3, h), body, "body")
            y3 += h
        return y3


# ---------------------------------------------------------------- compositions
def cover(c):
    ts, pg, n = c.ts, c.page, c.grid["n"]
    title = pg["title"]
    words = title.split()
    l1, l2 = (" ".join(words[:(len(words) + 1) // 2]), " ".join(words[(len(words) + 1) // 2:])) if len(words) >= 2 and len(title) > 12 else (title, "")
    kw = " / ".join(pg.get("keywords", [])[:5])
    tag = pg.get("tagline", "")
    if not pg["assets"]:
        y = c.hang + (c.bottom - c.hang) * 0.3
        c.text("title", c.col_box(0, n - 2, y, ts.line_mm("display")), l1, "display")
        if l2:
            c.text("title-2", c.col_box(0, n - 2, y + ts.line_mm("display"), ts.line_mm("display")), l2, "display_italic")
        c.text("caption", c.col_box(0, n // 2, y + ts.line_mm("display", 2) + 6 * c.s, ts.line_mm("caption")), kw, "caption")
        return
    landscape = c.aspect(0) >= 1.15
    c.tag("cover-landscape" if landscape else "cover-portrait")
    if landscape:
        # title on the hang line, hero below; when the hero is height-limited the leftover becomes a deliberate side column
        one_line = len(title) / ts.chars_per_mm("display", title) <= c.span_w(n // 2 + 1)
        if one_line and not (ts.display_serif and ts.italic_font and l2):   # a serif display keeps its two-line roman/italic form (editorial voice)
            l1, l2 = title, ""
        th = ts.line_mm("display", 2 if l2 else 1)
        block_h = th + 2 * c.s
        if c.variant == 0:
            y = c.hang
            c.text("title", c.col_box(0, n // 2 + 1, y, ts.line_mm("display")), l1, "display")
            if l2:
                c.text("title-2", c.col_box(0, n // 2 + 1, y + ts.line_mm("display"), ts.line_mm("display")), l2, "display_italic")
            img_y = y + block_h + c.gap
            short = c.cw / c.aspect(0) < 0.6 * (c.bottom - img_y)     # width-limited hero (portrait page): hang it from the bottom flowline
            r = c.graphic(0, [c.left, img_y, c.cw, c.bottom - img_y], "lb" if short else "lt")
        else:
            img_h = c.bottom - c.hang - block_h - c.gap
            r = c.graphic(0, [c.left, c.hang, c.cw, img_h], "lt")
            y = r[1] + r[3] + c.gap
            c.text("title", c.col_box(0, n // 2 + 1, y, ts.line_mm("display")), l1, "display")
            if l2:
                c.text("title-2", c.col_box(0, n // 2 + 1, y + ts.line_mm("display"), ts.line_mm("display")), l2, "display_italic")
        side_x = r[0] + r[2] + c.gap
        if c.right - side_x >= c.span_w(2):      # side column beside the hero: tagline + keywords, hanging from the image top
            sy = r[1]
            c.text("caption-2", [side_x, sy, c.right - side_x, ts.line_mm("caption", 2)], tag, "caption")
            c.text("caption", [side_x, sy + ts.line_mm("caption", 2) + 2 * c.s, c.right - side_x, ts.line_mm("caption_italic", 3)], kw, "caption_italic")
        else:                                     # full-width hero: keywords right of the title, tagline under the image
            ky = (c.hang if c.variant == 0 else y)
            c.text("caption", c.col_box(n // 2 + 2, n // 2 - 2, ky + th - ts.line_mm("caption", 2), ts.line_mm("caption", 2)), kw, "caption")
            if tag and c.variant == 1:
                c.text("caption-2", c.col_box(n // 2 + 2, n // 2 - 2, ky, ts.line_mm("caption")), tag, "caption")
    else:
        # portrait hero: image fills the right 7/12, title column left (variant 1 mirrored)
        tcols = n - (n * 7) // 12
        tstart, istart = (0, tcols) if c.variant == 0 else (n - tcols, 0)
        c.graphic(0, c.col_box(istart, n - tcols, c.hang, c.bottom - c.hang), "lt" if c.variant == 0 else "rt")
        y = c.hang
        c.text("title", c.col_box(tstart, tcols, y, ts.line_mm("display_small")), l1, "display_small")
        if l2:
            c.text("title-2", c.col_box(tstart, tcols, y + ts.line_mm("display_small"), ts.line_mm("display_small")), l2, "display_italic")
        y += ts.line_mm("display_small", 2 if l2 else 1) + 6 * c.s
        c.hairline("", c.x(tstart), y, c.span_w(2))
        c.text("caption", c.col_box(tstart, tcols, y + 3 * c.s, ts.line_mm("caption", 2)), kw, "caption_italic")
        if tag:
            c.text("caption-2", c.col_box(tstart, tcols, c.bottom - ts.line_mm("caption"), ts.line_mm("caption")), tag, "caption")


def feature(c):
    """One image + text column (role `split`). Image and text hang from the same line; the text column is sized to the measure.
    A wide image (would fill < 60 % of the column height) becomes a banner across all columns with the text block below."""
    ts, n = c.ts, c.grid["n"]
    body = c.page.get("text", "")
    tcols = ts.measure_cols(c.grid, body)
    icols = n - tcols
    avail_h = c.bottom - c.hang
    a = c.aspect(0)
    if c.span_w(icols) / a < 0.6 * avail_h:
        c.tag("feature-banner")
        # text band on the hang line (label + heading left, body in a measure-wide column right); the banner hangs from the bottom flowline
        hcols = n - tcols if c.variant == 0 else tcols
        hstart, bstart = (0, n - tcols) if c.variant == 0 else (n - hcols, 0)
        y = c.hang
        c.label(c.col_box(hstart, hcols, y, ts.line_mm("label")))
        c.text("title", c.col_box(hstart, hcols, y + ts.line_mm("label") + 2.0 * c.s, ts.line_mm("heading", 2)), c.page["title"], "heading")
        band = ts.line_mm("label") + ts.line_mm("heading", 2) + 2.0 * c.s
        if body:
            need = TL.text_need_mm2(body, ts.pt("body")) / c.span_w(tcols) * 1.25 + ts.line_mm("body")
            bh = min(max(need, ts.line_mm("body", 2)), avail_h * 0.45)
            c.text("body", c.col_box(bstart, tcols, y, bh), body, "body")
            band = max(band, bh)
        top = y + band + c.gap
        c.graphic(0, [c.left, top, c.cw, c.bottom - top], "lb")
        return
    c.tag("feature-column")
    need_w = a * avail_h                                   # width the image takes at full column height
    icols = min(icols, max(2, c.cols_for(need_w)))          # height-limited image: give it only the columns it needs
    if c.variant == 0:
        c.graphic(0, c.col_box(0, icols, c.hang, avail_h), "lt")
        c.heading_block(icols, tcols, c.hang)
    else:
        c.heading_block(0, tcols, c.hang)
        c.graphic(0, c.col_box(n - icols, icols, c.hang, avail_h), "rt")


def hero(c):
    """One photo. Landscape: across all columns with a caption band (bottom for variant 0, top for variant 1).
    Portrait: full column height at the left (right for variant 1), label + statement in the adjacent column."""
    ts, n = c.ts, c.grid["n"]
    cap = c.page.get("caption", "")
    avail_h = c.bottom - c.hang
    a = c.aspect(0)
    if a < 1.2 and n - max(3, c.cols_for(a * avail_h)) >= 3:    # column form only when a real text column (>= 3 columns) remains
        c.tag("hero-column")
        icols = max(3, c.cols_for(a * avail_h))
        tcols = min(ts.measure_cols(c.grid, cap), n - icols)
        if c.variant == 0:
            c.graphic(0, c.col_box(0, icols, c.hang, avail_h), "lt")
            tx = icols
        else:   # image right, type stays on the left margin (an indented column reads as an error)
            c.graphic(0, c.col_box(n - icols, icols, c.hang, avail_h), "rt")
            tx = 0
        c.label(c.col_box(tx, tcols, c.hang, ts.line_mm("label")))
        c.text("title", c.col_box(tx, tcols, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
        c.text("caption", c.col_box(tx, tcols, c.hang + ts.line_mm("label") + ts.line_mm("heading") + 3 * c.s, ts.line_mm("caption_italic", 4)), cap, "caption_italic")
        return
    c.tag("hero-full")
    band = max(ts.line_mm("caption_italic", 2), ts.line_mm("label")) + 2 * c.s
    if c.variant == 0:
        r = c.graphic(0, [c.left, c.hang, c.cw, avail_h - band - c.gap], "lt")
        y = r[1] + r[3] + c.gap
    else:
        y = c.hang
        img_y = c.hang + band + c.gap
        c.graphic(0, [c.left, img_y, c.cw, c.bottom - img_y], "lt")
    c.label(c.col_box(0, 2, y + 1.0, ts.line_mm("label")))
    c.text("caption", c.col_box(2, n - 4, y, ts.line_mm("caption_italic", 2)), cap, "caption_italic")


def plate(c):
    """One drawing as a plate. Column form: drawing across 9/12 columns with a title column beside it. If the drawing cannot fill
    >= 85 % of the band height that way, band form: label/heading/caption in a band on the hang line, the plate full width below it."""
    ts, n = c.ts, c.grid["n"]
    cap = c.page.get("caption", "")
    tcols = n - (n * 9) // 12
    if len(cap) > 150:                         # a paragraph beside the plate must still respect the measure
        tcols = max(tcols, ts.measure_cols(c.grid, cap))
    dcols = n - tcols
    avail_h = c.bottom - c.hang
    a = c.aspect(0)
    if c.span_w(dcols) / a >= 0.75 * avail_h:     # critics prefer "the drawing leads" (column form) unless it would be clearly short
        c.tag("plate-column")
        vert = "t" if c.span_w(dcols) / a >= 0.85 * avail_h else "b"   # a width-limited plate stands on the bottom margin (no leftover strip under it)
        if c.variant == 0:
            c.graphic(0, c.col_box(0, dcols, c.hang, avail_h), "l" + vert)
            c.heading_block(dcols, tcols, c.hang, body_key="caption")
        else:
            c.heading_block(0, tcols, c.hang, body_key="caption")
            c.graphic(0, c.col_box(n - dcols, dcols, c.hang, avail_h), "r" + vert)
        return
    c.tag("plate-band")
    y = c.hang
    hcols = n // 2
    c.label(c.col_box(0, 3, y, ts.line_mm("label")))
    c.text("title", c.col_box(0, hcols, y + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
    band = ts.line_mm("label") + ts.line_mm("heading") + 4 * c.s
    if cap:   # caption sits under the heading, in the same column (never orphaned on the far side)
        cy = y + band
        ch = min(ts.line_mm("body", 3), avail_h * 0.2)
        c.text("body", c.col_box(0, min(hcols, ts.measure_cols(c.grid, cap)), cy, ch), cap, "body")
        band += ch + 1.5 * c.s
    top = y + band + c.gap
    r = fit(a, [c.left, top, c.cw, c.bottom - top], "t")      # centred plate ...
    x = min(c.grid["x"], key=lambda gx: abs(gx - r[0]))        # ... with its left edge snapped to the nearest column (grid discipline)
    if x + r[2] > c.right + 0.01:
        x = max(gx for gx in c.grid["x"] if gx + r[2] <= c.right + 0.01)
    c.graphic(0, [x, top, r[2], r[3]], "lt")


def pair(c):
    """Two graphics. Row: equal height, tops aligned, outer edges on the grid. If that row would be short (< 55 % of the band)
    the pair stacks instead: two full-width rows sharing the left edge. Heading band above (variant 0) or below."""
    ts, n = c.ts, c.grid["n"]
    band = ts.line_mm("label") + ts.line_mm("heading") + 4 * c.s
    caps = c.page.get("captions", ["", ""])
    cap_lines = 3 if any(len(x) > 90 or split_lead(x)[0] for x in caps) else (2 if any(len(x) > 45 for x in caps) else 1)
    cap_h = ts.line_mm("caption", cap_lines) + 1.5 * c.s
    a1, a2 = c.aspect(0), c.aspect(1)
    if c.variant == 0:
        c.label(c.col_box(0, 3, c.hang, ts.line_mm("label")))
        c.text("title", c.col_box(0, n // 2, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
        top = c.hang + band + c.gap
        avail_h = c.bottom - top
    else:   # band stays on top but moves to the right half, so facing pages do not repeat the same top-left skeleton
        c.label(c.col_box(n // 2, 3, c.hang, ts.line_mm("label")))
        c.text("title", c.col_box(n // 2, n - n // 2, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
        top = c.hang + band + c.gap
        avail_h = c.bottom - top
    tall, wide = (0, 1) if a1 < a2 else (1, 0)
    if c.aspect(tall) < 1.0 < 1.4 < c.aspect(wide) and c.aspect(tall) * (avail_h - cap_h) <= 0.55 * c.cw:   # portrait at full height leaves room for the wide one
        c.tag("pair-side")
        at, aw = c.aspect(tall), c.aspect(wide)
        ht = avail_h - cap_h
        wt = at * ht
        ww = c.cw - wt - c.gap
        hw = min(ht, ww / aw)
        if c.variant == 0:
            rw = c.graphic(wide, [c.left, top, ww, hw], "lt")
            rt = c.graphic(tall, [c.right - wt, top, wt, ht], "rt")
        else:
            rt = c.graphic(tall, [c.left, top, wt, ht], "lt")
            rw = c.graphic(wide, [c.right - ww, top, ww, hw], "rt")
        c.text("caption", [rw[0], rw[1] + rw[3] + 1.0, rw[2], ts.line_mm("caption")], caps[wide] if len(caps) > wide else "", "caption")
        c.text("caption-2", [rt[0], rt[1] + rt[3] + 1.0, rt[2], ts.line_mm("caption")], caps[tall] if len(caps) > tall else "", "caption")
        return
    row_h = min(avail_h - cap_h, (c.cw - c.gap) / (a1 + a2))
    h1s, h2s = c.cw / a1, c.cw / a2
    k = min(1.0, (avail_h - 2 * cap_h - c.gap) / (h1s + h2s))
    stack_ok = k >= 0.45 and min(h1s, h2s) * k >= 0.18 * avail_h   # a stack is fine when both rows stay readable
    if row_h < 0.7 * (avail_h - cap_h) and not stack_ok:   # neither a row nor a stack fills the band: let the guillotine solver place them
        return grid(c)
    if row_h >= 0.7 * (avail_h - cap_h):
        c.tag("pair-row")
        w1, w2 = row_h * a1, row_h * a2
        if avail_h - cap_h - row_h > 0.15 * avail_h:   # width-limited pair: stand it on the bottom margin so the air sits under the heading, not under the captions (blind15)
            top = c.bottom - cap_h - row_h
        c.graphic(0, [c.left, top, w1, row_h], "lt")
        adjacent = w1 + w2 + c.gap < 0.8 * c.cw          # narrow pair: sit together on the left, void stays on the outer edge
        x2 = c.left + w1 + c.gap if adjacent else c.right - w2
        c.graphic(1, [x2, top, w2, row_h], "lt")
        cy = top + row_h + 1.5 * c.s
        c.text("caption", [c.left, cy, w1, ts.line_mm("caption", cap_lines)], caps[0] or c.page.get("caption", ""), "caption")
        c.text("caption-2", [x2, cy, w2, ts.line_mm("caption", cap_lines)], caps[1] or "", "caption")
        end = cy + cap_h
    else:  # stacked rows, both hanging from the left edge, heights scaled to share the band
        c.tag("pair-stack")
        h1, h2 = h1s * k, h2s * k
        r1 = c.graphic(0, [c.left, top, c.cw, h1], "lt")
        c.text("caption", [c.left, r1[1] + r1[3] + 1.0, r1[2], ts.line_mm("caption")], caps[0] or c.page.get("caption", ""), "caption")
        y2 = r1[1] + r1[3] + cap_h + c.gap
        r2 = c.graphic(1, [c.left, y2, c.cw, h2], "lt")
        c.text("caption-2", [c.left, r2[1] + r2[3] + 1.0, r2[2], ts.line_mm("caption")], caps[1] or "", "caption")
        end = r2[1] + r2[3] + cap_h


def grid(c):
    """Three or more graphics (or a pair that fits neither row nor stack): reading-order guillotine under a heading band."""
    ts, n = c.ts, c.grid["n"]
    c.tag("grid-guillotine")
    band = ts.line_mm("label") + ts.line_mm("heading") + 4 * c.s
    if not any(e["id"].startswith("title-") for e in c.els):
        c.label(c.col_box(0, 3, c.hang, ts.line_mm("label")))
        c.text("title", c.col_box(0, n // 2, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
    top = c.hang + band + c.gap
    cap = c.page.get("caption", "")
    items = [{"kind": "img", "weight": (1.5 if k == 0 else 1.0) * c.page.get("weight_mult", {}).get(aid, 1.0), "aspect": c.A[aid]["aspect"], "name": f"img{k}"} for k, aid in enumerate(c.page["assets"])]
    if cap:
        need = TL.text_need_mm2(cap, ts.pt("caption"))
        items.append({"kind": "text", "weight": max(need * 1.3, c.cw * (c.bottom - top) * 0.07), "min_h_mm": 9.0, "need_mm2": need, "name": "caption", "asp_range": (1.8, 14), "min_w_mm": 40.0})
    loss, cells = TL.solve(items, (c.left, top, c.cw, c.bottom - top), c.gap)
    if c.variant == 1:
        cells = [(c.left + c.cw - (x - c.left) - w, y, w, h) for (x, y, w, h) in cells]
    ii = 0
    for it, cell in zip(items, cells):
        if it["kind"] == "img":
            c.graphic(ii, list(cell), "lt" if c.variant == 0 else "rt")
            ii += 1
        else:
            c.text("caption", list(cell), cap, "caption")
    c.page["_layout_loss"] = round(loss, 3)


def text(c):
    c.tag("text-column")
    n = c.grid["n"]
    tcols = c.ts.measure_cols(c.grid, c.page.get("text", ""))
    start = 0 if c.variant == 0 else n - tcols
    c.heading_block(start, tcols, c.hang)


def closing(c):
    """Typographic close: a statement in display type, a hairline and a numbered keyword row; credits in a side column."""
    ts, n = c.ts, c.grid["n"]
    c.tag("closing-statement")
    stmt = c.page.get("statement", "") or c.page["title"]
    words = stmt.split()
    l1, l2 = (" ".join(words[:(len(words) + 1) // 2]), " ".join(words[(len(words) + 1) // 2:])) if len(words) >= 3 else (stmt, "")
    y = c.hang + (c.bottom - c.hang) * 0.22
    c.label(c.col_box(0, 3, c.hang, ts.line_mm("label")))
    c.text("title", c.col_box(0, n - 3, y, ts.line_mm("display")), l1, "display")
    if l2:
        c.text("title-2", c.col_box(0, n - 3, y + ts.line_mm("display"), ts.line_mm("display")), l2, "display_italic")
    notes = c.page.get("text", "")
    if notes:
        c.text("body", c.col_box(n - 3, 3, c.hang, min(ts.line_mm("body", 6), (c.bottom - c.hang) * 0.4)), notes, "body")
    kws = c.page.get("keywords", [])[:4]
    if kws:
        row_h = ts.line_mm("label") + ts.line_mm("subhead") + 2 * c.s
        ry = c.bottom - row_h
        c.hairline("", c.left, ry - 3 * c.s, c.cw)
        span = n // len(kws)
        for k, kw in enumerate(kws):
            c.text(f"label-{k + 1}" if False else f"caption-{k + 1}", c.col_box(k * span, span, ry, ts.line_mm("label")), f"{k + 1:02d}", "label")
            c.text(f"subhead-{k + 1}" if False else f"caption-{k + 10}", c.col_box(k * span, span, ry + ts.line_mm("label") + 1.0, ts.line_mm("subhead")), kw, "subhead")


def diagram_row(c):
    """2-4 diagrams on column-snapped cells (equal spans), tops on one flowline, a caption under each; label + heading + body above
    (variant 1: below). Four diagrams with no body text become a 2 x 2 block so they stay legible."""
    ts, n = c.ts, c.grid["n"]
    k = len(c.page["assets"])
    caps = c.page.get("captions", [""] * k)
    body = c.page.get("text", "") or c.page.get("caption", "")
    bcols = ts.measure_cols(c.grid, body) if body else 0
    body_h = min(TL.text_need_mm2(body, ts.pt("body")) / c.span_w(bcols) * 1.3 + ts.line_mm("body"), (c.bottom - c.hang) * 0.35) if body else 0
    band = max(ts.line_mm("label") + ts.line_mm("heading") + 3 * c.s, body_h)
    cap_h = ts.line_mm("caption", 2) + 1.5 * c.s
    top = c.hang + band + c.gap          # heading always on top (blind11: a headline at the page bottom reads as an error); variant 1 swaps the columns
    avail_h = c.bottom - top
    per_row = k
    span = n // k
    row_h = min(c.span_w(span) / max(c.aspect(i) for i in range(k)), avail_h - cap_h)
    if k == 4 and row_h < 0.35 * avail_h:      # 2 x 2 block whenever one row would make them thumbnails (the body shares the heading band)
        per_row, span = 2, n // 2
        row_h = min(c.span_w(span) / max(c.aspect(i) for i in range(k)), (avail_h - 2 * cap_h - c.gap) / 2)
    c.tag("diagram-row" if per_row == k else "diagram-block")
    end = top
    for i in range(k):
        r, col = divmod(i, per_row)
        y = top + r * (row_h + cap_h + c.gap)
        x, w = c.x(col * span), c.span_w(span)
        c.graphic(i, [x, y, w, row_h], "lt")
        c.text("caption" if i == 0 else f"caption-{i + 1}", [x, y + row_h + 1.5 * c.s, w, ts.line_mm("caption", 2)], caps[i] if i < len(caps) else "", "caption")
        end = max(end, y + row_h + cap_h)
    y = c.hang
    hstart, bstart = (0, n - bcols) if c.variant == 0 else (n - n // 2, 0)
    c.label(c.col_box(hstart, 3, y, ts.line_mm("label")))
    c.text("title", c.col_box(hstart, n // 2, y + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
    if body:
        c.text("body", c.col_box(bstart, bcols, y, body_h), body, "body")


def index_grid(c):
    """Index of sheets: every drawing as a thumbnail on column-snapped cells (4 per row), numbered caption under each;
    label + heading (+ text) in the left columns."""
    ts, n = c.ts, c.grid["n"]
    c.tag("index-grid")
    k = len(c.page["assets"])
    tcols = 4 if n >= 12 else max(2, n // 3)
    c.label(c.col_box(0, tcols, c.hang, ts.line_mm("label")))
    c.text("title", c.col_box(0, tcols, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading", 2)), c.page["title"], "heading")
    body = c.page.get("text", "")
    if body:
        c.text("body", c.col_box(0, tcols, c.hang + ts.line_mm("label") + ts.line_mm("heading", 2) + 4 * c.s, ts.line_mm("body", 8)), body, "body")
    gcols = n - tcols
    cap_h = ts.line_mm("caption", 2) + 1.0
    amax = max(c.aspect(i) for i in range(k))

    def _cells(per_row):
        span = gcols // per_row
        rows = (k + per_row - 1) // per_row
        cell_w = c.span_w(span)
        cell_h = min((c.bottom - c.hang - (rows - 1) * c.gap) / rows - cap_h, cell_w / 0.8)
        return per_row, span, rows, cell_w, cell_h, min(cell_w / amax, cell_h)   # last = visible drawing height

    # 2-4 per row: whichever fills the page with the largest thumbnails (blind11: "index thumbnails unreadable, bottom empty")
    per_row, span, rows, cell_w, cell_h, _ = max((_cells(p) for p in range(2, min(4, gcols) + 1)), key=lambda t: t[5])
    caps = c.page.get("captions", [""] * k)
    for i in range(k):
        r, col = divmod(i, per_row)
        x = c.x(tcols + col * span)
        y = c.hang + r * (cell_h + cap_h + c.gap)
        c.graphic(i, [x, y, cell_w, cell_h], "lt")
        c.text("caption" if i == 0 else f"caption-{i + 1}", [x, y + cell_h + 1.0, cell_w, ts.line_mm("caption", 2)], caps[i] if i < len(caps) else "", "caption")


COMPOSITIONS = {"cover": cover, "diagram_row": diagram_row, "index_grid": index_grid, "split": feature, "hero": hero, "plate": plate, "pair": pair, "grid": grid, "text": text, "closing": closing}


def furniture(c, total):
    """Running header + footer markers (user-switchable) and the optional background band (style.band)."""
    ts, pg, n = c.ts, c.page, c.grid["n"]
    band = (c.spec.get("style") or {}).get("band")
    if band and band.get("side") in ("left", "top") and (pg["role"] == "cover" or band.get("every_page")):
        wmm = float(band.get("width_mm", 6))
        box = [0, 0, wmm, c.H] if band["side"] == "left" else [0, 0, c.W, wmm]
        c.el(f"band-{c.pn:02d}", "shape", box, 0, style={"fill": band.get("color", ts.accent)})
    if ts.header:
        c.el(f"hairline-{c.pn:02d}-head", "shape", [c.left, c.m + ts.line_mm("label") + 0.8 * c.s, c.cw, 0.25], 1, style={"fill": ts.hairline})   # one rule under the running head on every page: the system the critic reads as "designed"
        c.text("header", c.col_box(0, n // 2, c.m, ts.line_mm("label")), ts.label_text(pg.get("doc_title", "")), "label", style=ts.style("folio"))
        right = f"{c.pn:02d} / {total:02d}" + (f"   {ts.label_text(pg['section'])}" if pg.get("section") else "")
        c.text("header-r", c.col_box(n // 2, n - n // 2, c.m, ts.line_mm("label")), right, "label", style={**ts.style("folio"), "align": "right"})
    if ts.footer:
        y = c.bottom + 1.5 * c.s
        c.el(f"rule-{c.pn:02d}", "shape", [c.left, y, c.cw, 0.3], 1, style={"fill": ts.hairline})
        ft = (c.spec.get("style", {}) or {}).get("footer_text", "{title}   {page:02d} / {total:02d}").format(title=pg.get("doc_title", ""), page=c.pn, total=total)
        c.text("folio", [c.left, y + 2.0 * c.s, c.cw, ts.line_mm("folio")], ft, "folio")
