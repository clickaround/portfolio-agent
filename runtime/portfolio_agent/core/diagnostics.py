"""Computational DIAGNOSTICS in the style of SlidesGen-Bench (arXiv 2601.09487): contrast (usability), colorfulness (engagement),
entropy + RMSSD (rhythm proxy). Re-implemented from the paper's description, not from its code (no license file in that repo).
These are NOT quality gates and NOT validated for portfolios (paper reports Spearman 0.71 vs humans on slides); report as diagnostics only.
"""
import math
import fitz
import numpy as np


def _page(pdf, i, dpi=72):
    d = fitz.open(pdf)
    pm = d[i].get_pixmap(dpi=dpi)
    a = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[:, :, :3].astype(float)
    d.close()
    return a


def _lum(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def colorfulness(a):
    """Hasler & Suesstrunk 2003: sigma_rgyb + 0.3 * mu_rgyb on opponent channels."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    rg, yb = r - g, 0.5 * (r + g) - b
    return float(math.hypot(rg.std(), yb.std()) + 0.3 * math.hypot(rg.mean(), yb.mean()))


def entropy(a):
    g = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]).astype(np.uint8)
    h = np.bincount(g.ravel(), minlength=256).astype(float)
    p = h[h > 0] / h.sum()
    return float(-(p * np.log2(p)).sum())


def usability(a, boxes_px):
    """Mean of ln(contrast)/ln(21) over text boxes; contrast between background (median luminance) and the most distant pixel."""
    L = _lum(a)
    vals = []
    for x0, y0, x1, y1 in boxes_px:
        r = L[max(0, y0):y1, max(0, x0):x1]
        if r.size < 20:
            continue
        bg = float(np.median(r))
        fg = float(r.flat[np.argmax(np.abs(r - bg))])
        hi, lo = max(bg, fg), min(bg, fg)
        vals.append(math.log((hi + 0.05) / (lo + 0.05)) / math.log(21))
    return float(np.mean(vals)) if vals else None


def analyse(pdf, scenes, dpi=72):
    s = dpi / 25.4
    per = []
    for i, sc in enumerate(scenes):
        a = _page(pdf, i, dpi)
        boxes = [(int(e["box_mm"][0] * s), int(e["box_mm"][1] * s), int((e["box_mm"][0] + e["box_mm"][2]) * s), int((e["box_mm"][1] + e["box_mm"][3]) * s)) for e in sc["elements"] if e["kind"] == "text" and e.get("text")]
        per.append(dict(page=sc["page_id"], colorfulness=round(colorfulness(a), 2), entropy=round(entropy(a), 3), usability=None if not boxes else (None if usability(a, boxes) is None else round(usability(a, boxes), 3))))
    ent = [p["entropy"] for p in per]
    rmssd = float(np.sqrt(np.mean(np.diff(ent) ** 2))) if len(ent) >= 5 else None  # paper requires >= 5 slides
    use = [p["usability"] for p in per if p["usability"] is not None]
    return dict(per_page=per, usability_mean=round(float(np.mean(use)), 3) if use else None, colorfulness_mean=round(float(np.mean([p["colorfulness"] for p in per])), 2),
                entropy_rmssd=None if rmssd is None else round(rmssd, 3), note="diagnostic only; entropy here is plain grayscale Shannon entropy (proxy for the paper's subband entropy)")


def pei_estimate(pptx_path=None, has_vector_in_native=False, has_masters_or_styles=False):
    """Rough PEI level (SlidesGen-Bench knockout scale) from observable structure. ESTIMATE, not the official evaluator."""
    level, why = 0, []
    if pptx_path:
        from pptx import Presentation
        prs = Presentation(str(pptx_path))
        shapes = [s for sl in prs.slides for s in sl.shapes]
        if any(s.has_text_frame and s.text_frame.text.strip() for s in shapes):
            level = 1
            why.append("L1: editable text boxes")
    if level >= 1 and has_vector_in_native:
        level = 2
        why.append("L2: vector graphics retained in the native file")
    if level >= 2 and has_masters_or_styles:
        level = 3
        why.append("L3: styles/masters present")
    return dict(level=level, reasons=why or ["no editable text structure found"], note="estimate; L4 (native charts) and L5 (animation) not applicable/not assessed")
