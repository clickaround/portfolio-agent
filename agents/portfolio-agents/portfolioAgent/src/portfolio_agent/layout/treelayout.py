"""Reading-order-preserving guillotine layout (binary-tree split) with content-aware cell areas.

Idea source: Paper2Poster `PosterAgent/tree_split_layout.py::panel_layout_generation` (MIT, (c) 2025 Paper2Poster):
recursively split an ORDERED panel list at every cut point, horizontally or vertically, with the first part's size proportional
to its share of content weight, and keep the arrangement with the lowest aspect-ratio loss. This is an independent
re-implementation (not a copy) with changes: gutters, images measured by wasted area under aspect-preserving fit
(so no stretching and little blank space), text cells with a minimum area derived from character count and font size.
"""
import math
from functools import lru_cache

MIN_CELL_MM = 14.0


def _img_waste(w, h, asp):
    """Fraction of the cell left empty when an image of aspect `asp` is fitted with `contain`."""
    ca = w / h
    fit = ca / asp if ca < asp else asp / ca
    return 1.0 - fit


def _leaf(item, w, h, A_tot):
    """Loss = empty area of this cell as a share of the page (x10) + hard penalties for unreadable text cells."""
    area = w * h
    if item["kind"] == "img" and (w < MIN_CELL_MM or h < MIN_CELL_MM):
        return 50.0
    if item["kind"] == "text" and (w < item.get("min_w_mm", 28.0) or h < item.get("min_h_mm", 10.0)):
        return 50.0
    if item["kind"] == "img":
        fit = (w / h) / item["aspect"] if (w / h) < item["aspect"] else item["aspect"] / (w / h)
        used = area * fit
        starve = max(0.0, 1.0 - used / (0.6 * item["weight"])) * item["weight"] / A_tot * 14.0  # image far smaller than its share of the page
        return (area * (1 - fit)) / A_tot * 10.0 + starve
    need = item.get("need_mm2", 0.0)
    pen = 0.0 if area >= need else 40.0 * (need - area) / max(need, 1)
    asp = w / h
    lo, hi = item.get("asp_range", (0.45, 2.6))
    if asp < lo:
        pen += (lo - asp) * 60
    if asp > hi:
        pen += (asp - hi) * 8
    used = min(area, need * 1.5)
    return pen + (area - used) / A_tot * 10.0


def solve(items, box, gap, first_horizontal=None):
    """items: ordered list of {kind:'img'|'text', weight, aspect?, need_mm2?}. box: (x, y, w, h). Returns (loss, [rects])."""
    n = len(items)
    A_tot = box[2] * box[3]
    weights = [it["weight"] for it in items]

    def rec(i, j, x, y, w, h):
        if j - i == 1:
            return _leaf(items[i], w, h, A_tot), [(x, y, w, h)]
        tot = sum(weights[i:j])
        best = (math.inf, None)
        for k in range(i + 1, j):
            r0 = sum(weights[i:k]) / tot
            for r in sorted({r0} | {q / 20 for q in range(4, 17)}):  # weight-proportional cut plus a grid of alternatives
                hw = (h - gap) * r
                if hw > 0 and h - gap - hw > 0:  # horizontal cut (stack)
                    l1, a1 = rec(i, k, x, y, w, hw)
                    l2, a2 = rec(k, j, x, y + hw + gap, w, h - gap - hw)
                    if l1 + l2 < best[0]:
                        best = (l1 + l2, a1 + a2)
                ww = (w - gap) * r
                if ww > 0 and w - gap - ww > 0:  # vertical cut (side by side)
                    l1, a1 = rec(i, k, x, y, ww, h)
                    l2, a2 = rec(k, j, x + ww + gap, y, w - gap - ww, h)
                    if l1 + l2 < best[0]:
                        best = (l1 + l2, a1 + a2)
        return best

    return rec(0, n, *box)


def fit_in(cell, aspect, anchor="lt"):
    x, y, w, h = cell
    if w / h > aspect:
        nw, nh = h * aspect, h
    else:
        nw, nh = w, w / aspect
    ox = x if "l" in anchor else x + (w - nw) / 2
    oy = y if "t" in anchor else y + (h - nh) / 2
    return [round(ox, 2), round(oy, 2), round(nw, 2), round(nh, 2)]


def text_need_mm2(text, font_pt, title_lines=0):
    """Approximate area a paragraph needs: chars * average glyph advance * line height (calibrated on Malgun/Segoe: 0.52em, 1.45 leading)."""
    fs = font_pt * 0.3528
    return max(1, len(text)) * (0.52 * fs) * (1.45 * fs) * 1.12 + title_lines * 2.2 * fs * 30
