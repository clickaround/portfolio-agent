"""Full-bleed and strip compositions, derived from the user's reference portfolios (private annotations kept outside the repo (C:/DK/real_sources/cases_private/user_cases_annotations.json)).

Real portfolios cover whole pages with one photograph, bleed a render off three edges beside a text column, tile 2x2 photos to
the trim with thin gutters, and run process thumbnails as one strip. These compositions produce exactly those devices; the
guardrails (core/guardrails/gates.py) allow a `bleed-NN-k` graphic to leave the margin box and let text sit on it ONLY inside a
`panel-NN` shape, so legibility never depends on the photograph.

Page flags read from the plan (host decides, never coordinates): `bleed: full|split|top|grid`, `dark: true`, `strip: true`.
Running header/footer are suppressed on bleed pages (`_no_furniture`), as in the cases (a small running label at most).
"""
import math

from . import treelayout as TL


def _trim(c):
    """Bleed pages carry no running furniture: content hangs from the margin, not from a header line."""
    c.page["_no_furniture"] = True
    c.hang, c.bottom = c.m, c.H - c.m


def _panel_block(c, x, w, y_top=None, y_bottom=None, caption_key="caption"):
    """label / heading / caption inside a solid panel, hung from y_top or standing on y_bottom. Returns the panel box."""
    ts, pg = c.ts, c.page
    pad = 4.0 * c.s
    cap = pg.get(caption_key, "")
    title = pg["title"]
    hl = 2 if len(title) / ts.chars_per_mm("heading", title) > w - 2 * pad else 1
    cap_lines = min(5, max(1, math.ceil(TL.text_need_mm2(cap, ts.pt("body")) * 1.25 / ((w - 2 * pad) * ts.line_mm("body"))))) if cap else 0
    h = 2 * pad + ts.line_mm("label") + 1.5 * c.s + ts.line_mm("heading", hl) + (2.0 * c.s + ts.line_mm("body", cap_lines) if cap else 0)
    y = y_top if y_top is not None else y_bottom - h
    c.panel([x, y, w, h])
    yy = y + pad
    c.label([x + pad, yy, w - 2 * pad, ts.line_mm("label")])
    yy += ts.line_mm("label") + 1.5 * c.s
    c.text("title", [x + pad, yy, w - 2 * pad, ts.line_mm("heading", hl)], title, "heading")
    yy += ts.line_mm("heading", hl) + 2.0 * c.s
    if cap:   # on a panel the caption is set at body size in ink (blind11/12: "subtitle tiny and low-contrast")
        c.text("caption", [x + pad, yy, w - 2 * pad, ts.line_mm("body", cap_lines)], cap, "body")
    return [x, y, w, h]


def bleed_full(c):
    """One graphic covers the page to the bleed; label + heading + caption on a solid panel (top-left, variant 1 bottom-left)."""
    _trim(c)
    c.tag("bleed-full")
    n = c.grid["n"]
    c.bleed_graphic(0, [-c.b, -c.b, c.W + 2 * c.b, c.H + 2 * c.b])
    w = c.span_w(max(3, n // 3))
    if c.variant == 0:
        _panel_block(c, c.m, w, y_top=c.m)
    else:
        _panel_block(c, c.m, w, y_bottom=c.H - c.m)


def bleed_split(c):
    """Graphic bleeds off three edges on ~2/3 of the width; label / heading / body in the remaining columns (variant 1 mirrored)."""
    _trim(c)
    c.tag("bleed-split")
    n = c.grid["n"]
    icols = max(n // 2, (n * 2) // 3)
    tcols = n - icols
    g = c.grid["gutter"]
    if c.variant == 0:
        c.bleed_graphic(0, [-c.b, -c.b, c.x(icols) - g + c.b, c.H + 2 * c.b])
        start = icols
    else:
        x0 = c.x(tcols)
        c.bleed_graphic(0, [x0, -c.b, c.W + c.b - x0, c.H + 2 * c.b])
        start = 0
    y = c.heading_block(start, tcols, c.m)
    cap = c.page.get("caption", "")
    if cap:   # the caption stands on the bottom margin so the column reads as a bracket, not as a half-empty column (blind11 p2)
        h = ts_lines(c, "caption", cap, c.span_w(tcols))
        if y + c.gap + h <= c.bottom:
            c.text("caption", c.col_box(start, tcols, c.bottom - h, h), cap, "caption")


def ts_lines(c, role, txt, w, lo=1, hi=6):
    lines = max(lo, min(hi, math.ceil(TL.text_need_mm2(txt, c.ts.pt(role)) * 1.25 / (w * c.ts.line_mm(role)))))
    return c.ts.line_mm(role, lines)


def bleed_top(c):
    """Graphic bleeds off the top and both sides down to ~62 % of the page; label + heading left, caption / body right below it
    (variant 1: text band on top, graphic bleeds off the bottom)."""
    _trim(c)
    c.tag("bleed-top")
    ts, n = c.ts, c.grid["n"]
    split = 0.62 * c.H
    body = c.page.get("text", "") or c.page.get("caption", "")
    if c.variant == 0:
        c.bleed_graphic(0, [-c.b, -c.b, c.W + 2 * c.b, split + c.b])
        y = split + c.gap
    else:
        c.bleed_graphic(0, [-c.b, c.H - split, c.W + 2 * c.b, split + c.b])
        y = c.m
    hcols = n // 3
    c.heading_block(0, hcols, y, with_body=False)
    if body:
        bcols = ts.measure_cols(c.grid, body)
        role = "pull" if len(body) <= 160 else "body"
        h = min(ts_lines(c, role, body, c.span_w(bcols), hi=12), (c.H - c.m - y) if c.variant == 0 else (c.H - split - c.gap - y))
        c.text("body", c.col_box(n - bcols, bcols, y, h), body, role)


def bleed_grid(c):
    """2-4 photographs tiled to the trim with thin gutters (case_B p9/p44): 2 side by side, 3 = one tall + two stacked, 4 = 2 x 2.
    Title as a small panel in the first cell's corner."""
    _trim(c)
    c.tag("bleed-grid")
    k = len(c.page["assets"])
    g, b, W, H = c.gap, c.b, c.W, c.H
    cells = []
    if k == 2:
        cw = (W - g) / 2
        cells = [[-b, -b, cw + b, H + 2 * b], [cw + g, -b, cw + b, H + 2 * b]]
    elif k == 3:
        cw = (W - g) / 2
        ch = (H - g) / 2
        tall = [-b, -b, cw + b, H + 2 * b]
        stack = [[cw + g, -b, cw + b, ch + b], [cw + g, ch + g, cw + b, ch + b]]
        cells = [tall] + stack if c.variant == 0 else [stack[0], stack[1], tall]
        if c.variant == 1:   # tall cell on the right
            cells = [[-b, -b, cw + b, ch + b], [-b, ch + g, cw + b, ch + b], [cw + g, -b, cw + b, H + 2 * b]]
    else:
        cw, ch = (W - g) / 2, (H - g) / 2
        cells = [[-b, -b, cw + b, ch + b], [cw + g, -b, cw + b, ch + b], [-b, ch + g, cw + b, ch + b], [cw + g, ch + g, cw + b, ch + b]]
    for i, box in enumerate(cells[:k]):
        c.bleed_graphic(i, box, k=i + 1)
    n = c.grid["n"]
    _panel_block(c, c.m, c.span_w(max(3, n // 4)), y_top=c.m if c.variant == 0 else None, y_bottom=None if c.variant == 0 else c.H - c.m)


def strip(c):
    """Title block on the hang line, then ONE row (two rows above 6) of equal thumbnails with numbered captions (case_A p7)."""
    ts, n = c.ts, c.grid["n"]
    c.tag("strip")
    k = len(c.page["assets"])
    caps = c.page.get("captions", [""] * k)
    body = c.page.get("text", "")
    band = ts.line_mm("label") + ts.line_mm("heading") + 3 * c.s
    if body:
        bcols = ts.measure_cols(c.grid, body)
        bh = min(ts_lines(c, "body", body, c.span_w(bcols), hi=10), (c.bottom - c.hang) * 0.3)
        c.text("body", c.col_box(n - bcols, bcols, c.hang, bh), body, "body")
        band = max(band, bh)
    c.label(c.col_box(0, n // 3, c.hang, ts.line_mm("label")))
    c.text("title", c.col_box(0, n // 2, c.hang + ts.line_mm("label") + 1.5 * c.s, ts.line_mm("heading")), c.page["title"], "heading")
    top = c.hang + band + c.gap
    cap_h = ts.line_mm("caption", 2) + 1.0 * c.s
    amax = max(c.aspect(i) for i in range(k))

    def _row(rows):   # cells for `rows` rows: column-snapped when the grid divides, else equal free cells
        per_row = math.ceil(k / rows)
        if n % per_row == 0:
            span = n // per_row
            xs, cell_w = [c.x(i * span) for i in range(per_row)], c.span_w(span)
        else:
            cell_w = (c.cw - (per_row - 1) * c.gap) / per_row
            xs = [c.left + i * (cell_w + c.gap) for i in range(per_row)]
        avail = c.bottom - top - rows * cap_h - (rows - 1) * c.gap
        row_h = min(cell_w / amax, avail / rows)
        return per_row, xs, cell_w, row_h

    # one row is the device, but never at the price of unreadable thumbnails over a half-empty page (blind11 p8):
    # take the row count (1-3) that gives the largest cells
    per_row, xs, cell_w, row_h = max((_row(r) for r in (1, 2, 3) if r <= k), key=lambda t: t[3])
    rows = math.ceil(k / per_row)
    for i in range(k):
        r, col = divmod(i, per_row)
        y = top + r * (row_h + cap_h + c.gap)
        c.graphic(i, [xs[col], y, cell_w, row_h], "lt")
        cap = caps[i] if i < len(caps) else ""
        c.text("caption" if i == 0 else f"caption-{i + 1}", [xs[col], y + row_h + 1.0 * c.s, cell_w, ts.line_mm("caption", 2)], f"{i + 1:02d}  {cap}".strip(), "caption")


COMPOSITIONS = {"bleed_full": bleed_full, "bleed_split": bleed_split, "bleed_top": bleed_top, "bleed_grid": bleed_grid, "strip": strip}
