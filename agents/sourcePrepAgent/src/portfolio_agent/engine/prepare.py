"""Prepare real sources: people hand over scanned SHEETS (drawing + border + title block). A portfolio shows the drawing.

`prepare(project_dir)` moves nothing and rewrites nothing: originals stay byte-identical in `sources/`; trimmed copies are
written to `drawings/` (or `images/`) with `derived.json` recording source sha256, crop rectangle (px) and the derived sha256,
so every crop is explicit, reversible and auditable (AGENTS.md: transforms explicit and reversible). A contact sheet of the
proposed crops is written for the person to approve before anything is laid out.

Trim heuristic (deterministic, no ML): threshold ink, find the sheet's inner frame (largest ink bounding box), drop the title
block band at the bottom when a long horizontal rule separates it, then shrink to the ink bbox inside with a small margin.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from portfolio_agent.core.sources.assets import sha256

INK = 200          # grey level below which a pixel counts as ink
PAD_FRAC = 0.012   # breathing room around the ink bbox


def _ink_bbox(mask, min_frac=0.002):
    rows = np.where(mask.mean(axis=1) > min_frac)[0]
    cols = np.where(mask.mean(axis=0) > min_frac)[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def propose_crop(path):
    """-> (x, y, w, h) in source pixels, or None when nothing to trim (ink fills the frame already)."""
    im = Image.open(path).convert("L")
    a = np.asarray(im)
    H, W = a.shape
    mask = a < INK
    if mask.mean() > 0.25:           # a photograph or a dark scan: never auto-trim (only line drawings on white qualify)
        return None
    # 1. inner frame: the strongest full-width horizontal rules and full-height vertical rules (relative threshold)
    row_density = mask.mean(axis=1)
    col_density = mask.mean(axis=0)
    strong_rows = np.where(row_density > max(0.3, 0.6 * row_density.max()))[0]
    strong_cols = np.where(col_density > max(0.3, 0.6 * col_density.max()))[0]
    top = int(strong_rows[strong_rows < H * 0.25].max()) + 2 if (strong_rows < H * 0.25).any() else 0
    left = int(strong_cols[strong_cols < W * 0.25].max()) + 2 if (strong_cols < W * 0.25).any() else 0
    right = int(strong_cols[strong_cols > W * 0.75].min()) - 2 if (strong_cols > W * 0.75).any() else W
    # 2. title block: the lowest strong rule above the bottom 25 % that has mostly-text rows under it
    cand = strong_rows[(strong_rows > H * 0.75)]
    bottom = int(cand.min()) - 2 if len(cand) else H
    inner = mask[top:bottom, left:right]
    bb = _ink_bbox(inner)
    if bb is None:
        return None
    x0, y0, x1, y1 = bb
    px, py = int((x1 - x0) * PAD_FRAC), int((y1 - y0) * PAD_FRAC)
    x0, y0 = max(0, x0 - px) + left, max(0, y0 - py) + top
    x1, y1 = min(right - left, x1 + px) + left, min(bottom - top, y1 + py) + top
    if (x1 - x0) * (y1 - y0) > 0.93 * W * H:
        return None
    return [x0, y0, x1 - x0, y1 - y0]


def prepare(project_dir, kinds=("drawings", "images"), approve=False):
    """Write trimmed derivatives + derived.json + a proposal contact sheet. With approve=False only the proposal is written."""
    root = Path(project_dir)
    src = root / "sources"
    src.mkdir(exist_ok=True)
    proposals = []
    for kind in kinds:
        d = root / kind
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
                continue
            crop = propose_crop(p)
            if crop is None:
                continue
            proposals.append({"kind": kind, "file": p.name, "crop_px": crop, "source_sha256": sha256(p)})
    der_path = root / "derived.json"
    old = json.loads(der_path.read_text(encoding="utf-8")) if der_path.is_file() else {}
    rec = {"proposals": proposals, "approved": approve, "derived": list(old.get("derived", []))}   # never drop earlier records (cut-outs, levels, past trims)
    if approve:
        for pr in proposals:
            p = root / pr["kind"] / pr["file"]
            keep = src / p.name
            if not keep.exists():
                shutil.copy2(p, keep)                      # original preserved, byte-identical
            im = Image.open(keep)
            x, y, w, h = pr["crop_px"]
            out = im.crop((x, y, x + w, y + h))
            out.save(p)                                    # derived replaces the working copy under its own name
            pr["derived_sha256"] = sha256(p)
            pr["source"] = f"sources/{p.name}"
            rec["derived"].append(pr)
    (root / "derived.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec


def proposal_sheet(project_dir, out_png, max_w=700):
    """Side-by-side: original with the proposed crop outlined in red, for approval."""
    from PIL import ImageDraw
    root = Path(project_dir)
    rec = json.loads((root / "derived.json").read_text(encoding="utf-8"))
    tiles = []
    for pr in rec["proposals"]:
        p = root / "sources" / pr["file"] if (root / "sources" / pr["file"]).exists() else root / pr["kind"] / pr["file"]
        im = Image.open(p).convert("RGB")
        dr = ImageDraw.Draw(im)
        x, y, w, h = pr["crop_px"]
        dr.rectangle([x, y, x + w, y + h], outline=(220, 30, 30), width=max(3, im.width // 300))
        s = max_w / im.width
        tiles.append(im.resize((max_w, int(im.height * s))))
    if not tiles:
        return None
    cols = 3
    th = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (max_w + 10) + 10, rows * (th + 10) + 10), (120, 120, 120))
    for i, t in enumerate(tiles):
        sheet.paste(t, (10 + (i % cols) * (max_w + 10), 10 + (i // cols) * (th + 10)))
    sheet.save(out_png)
    return out_png
