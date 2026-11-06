"""Unit conversion and aspect-preserving fit. Pure functions, no I/O."""
PT_PER_MM = 72 / 25.4


def fit(aspect, box, align="c"):
    """Largest rect of `aspect` inside `box` (x,y,w,h). align: any of 'l','r','t','b' ('c' = centred)."""
    x, y, w, h = box
    if w / h > aspect:
        nw, nh = h * aspect, h
    else:
        nw, nh = w, w / aspect
    ox = x if "l" in align else (x + w - nw if "r" in align else x + (w - nw) / 2)
    oy = y if "t" in align else (y + h - nh if "b" in align else y + (h - nh) / 2)
    return [round(ox, 2), round(oy, 2), round(nw, 2), round(nh, 2)]


def columns(spec, n=12):
    """n equal columns inside the margin box (knowledge/editorial/layout-craft.md). -> {n, col_w, gutter, x[], margin_box}."""
    m, g = spec["margin_mm"], spec.get("gutter_mm", 6)
    W, H = spec["width_mm"], spec["height_mm"]
    inner = W - 2 * m
    cw = (inner - g * (n - 1)) / n
    return {"n": n, "col_w": round(cw, 2), "gutter": g, "x": [round(m + i * (cw + g), 2) for i in range(n)], "margin_box": [m, m, round(inner, 2), round(H - 2 * m, 2)]}
