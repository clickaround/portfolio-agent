"""Page-level visual metrics on rendered previews (advisory, score L).

Ported from the user's own pptAgent (agents/pascal-agents/pptAgent/engine/src/deckforge/critique/metrics/{whitespace,imbalance}.py),
which implements the AeSlides (arXiv 2604.22840) formulas:
- whitespace: local standard deviation over an H x W box, F = min(sigma, T_clip)/T_clip, empty where F < tau; ratio inside the margin frame
- imbalance: ink-weighted centroid distance from the page centre, d = sqrt(((x-0.5)/x_tol)^2 + ((y-0.5)/y_tol)^2)
pptAgent thresholds (docs/principles.md): whitespace <= 45 % required, imbalance d <= 2.0 advisory. Here BOTH are advisory.
"""
import numpy as np
from PIL import Image


def _box_mean(a, win_h, win_w):
    ph, pw = win_h // 2, win_w // 2
    p = np.pad(a, ((ph + 1, ph), (pw + 1, pw)), mode="edge").astype(np.float64)
    s = p.cumsum(0).cumsum(1)
    h, w = a.shape
    total = s[win_h:win_h + h, win_w:win_w + w] - s[:h, win_w:win_w + w] - s[win_h:win_h + h, :w] + s[:h, :w]
    return total / (win_h * win_w)


def local_std(gray, win_h, win_w):
    mean = _box_mean(gray, win_h, win_w)
    var = _box_mean(gray * gray, win_h, win_w) - mean * mean
    return np.sqrt(np.clip(var, 0, None))


def whitespace_ratio(png, frame_frac=0.05, win=(101, 76), t_clip=12.0, tau=0.05):
    gray = np.asarray(Image.open(png).convert("L"), dtype=np.float64)
    f = np.minimum(local_std(gray, *win), t_clip) / t_clip
    empty = f < tau
    fh, fw = int(empty.shape[0] * frame_frac), int(empty.shape[1] * frame_frac)
    inner = empty[fh:empty.shape[0] - fh, fw:empty.shape[1] - fw]
    return float(inner.mean())


def ink_centroid(png):
    gray = np.asarray(Image.open(png).convert("L"), dtype=np.float64)
    border = np.concatenate([gray[0], gray[-1], gray[:, 0], gray[:, -1]])
    ink = np.abs(gray - np.median(border))
    total = ink.sum()
    if total == 0:
        return None
    h, w = gray.shape
    ys, xs = np.mgrid[0:h, 0:w]
    return float((ink * xs).sum() / total / w), float((ink * ys).sum() / total / h)


def imbalance(png, x_tol=0.05, y_tol=0.15):
    c = ink_centroid(png)
    if c is None:
        return None, None
    return float(np.hypot((c[0] - 0.5) / x_tol, (c[1] - 0.5) / y_tol)), c


def page_issues(png, page_id, max_whitespace=0.45, max_imbalance=2.0):
    """Advisory issues for one rendered page."""
    out = []
    ws = whitespace_ratio(png)
    if ws > max_whitespace:
        out.append({"code": "WHITESPACE_EXCESS", "elements": [], "page": page_id, "details": f"{ws:.0%} of the page is empty (limit {max_whitespace:.0%})"})
    d, c = imbalance(png)
    if d is not None and d > max_imbalance:
        out.append({"code": "IMBALANCE", "elements": [], "page": page_id, "details": f"visual centroid ({c[0]:.2f}, {c[1]:.2f}), d={d:.2f} > {max_imbalance}"})
    return out, {"whitespace": round(ws, 3), "imbalance": None if d is None else round(d, 2)}
