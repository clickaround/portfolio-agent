"""Levels for scanned drawings: faint grey scans read as "pale, barely legible" on the page (blind12 p8). `levels()` stretches
each drawing so its paper becomes white and its ink darker - a percentile stretch, no sharpening, no redrawing. Explicit and
reversible like `prepare`: the original stays in `sources/` (byte-identical), the working copy is replaced, and `derived.json`
records `transform: levels` with the percentiles used and both hashes. Photographs are never touched.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from portfolio_agent.core.assets import sha256

IMG = (".png", ".jpg", ".jpeg", ".tif", ".tiff")


def stretch(im: Image.Image, lo_pct=1.0, hi_pct=92.0):
    """Map the `lo_pct` percentile of luminance to black-ish and the `hi_pct` percentile (the paper) to white."""
    g = np.asarray(im.convert("L"), dtype=np.float32)
    lo, hi = np.percentile(g, lo_pct), np.percentile(g, hi_pct)
    if hi - lo < 10:
        return im, False
    out = np.clip((g - lo) / (hi - lo), 0, 1) * 255
    return Image.fromarray(out.astype(np.uint8)), True


def knockout_image(im: Image.Image, white=245, soft=20):
    """Make the scan's paper transparent so a drawing sits on any page colour: luminance >= `white` -> alpha 0, ramping to
    opaque over `soft` levels; colours are kept (overlays stay coloured). Reversible: the original is kept in sources/."""
    rgb = im.convert("RGB")
    g = np.asarray(rgb.convert("L"), dtype=np.float32)
    alpha = np.clip((white - g) / soft, 0, 1) * 255
    out = np.dstack([np.asarray(rgb), alpha.astype(np.uint8)])
    return Image.fromarray(out, "RGBA")


def knockout(project_dir, kinds=("drawings",), files=None):
    """Knock the paper out of scanned drawings (and named overlay PNGs) -> RGBA PNGs; recorded in derived.json as transform `knockout`."""
    root = Path(project_dir)
    src = root / "sources"
    src.mkdir(exist_ok=True)
    der_path = root / "derived.json"
    rec = json.loads(der_path.read_text(encoding="utf-8")) if der_path.is_file() else {"proposals": [], "approved": True, "derived": []}
    targets = [p for k in kinds for p in sorted((root / k).iterdir()) if p.suffix.lower() in IMG] + [root / f for f in (files or [])]
    done = []
    for p in targets:
        if not p.is_file():
            continue
        keep = src / p.name
        if not keep.exists():
            shutil.copy2(p, keep)
        with Image.open(p) as im:
            out = knockout_image(im)
        target = p.with_suffix(".png")
        if target != p:
            p.unlink()
        out.save(target)
        prev = next((d for d in rec["derived"] if d.get("file") == target.name), None)
        d = {"kind": target.parent.name, "file": target.name, "transform": "knockout", "engine": "paper->alpha (L>=245 transparent, 20-level ramp)", "source": f"sources/{p.name}",
             "source_sha256": sha256(keep), "derived_sha256": sha256(target), "after": prev.get("transform") if prev else None, "crop_px": prev.get("crop_px") if prev else None}
        rec["derived"] = [x for x in rec["derived"] if x.get("file") != target.name] + [d]
        done.append(d)
    der_path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return done


def levels(project_dir, kind="drawings", lo_pct=1.0, hi_pct=92.0):
    root = Path(project_dir)
    src = root / "sources"
    src.mkdir(exist_ok=True)
    der_path = root / "derived.json"
    rec = json.loads(der_path.read_text(encoding="utf-8")) if der_path.is_file() else {"proposals": [], "approved": True, "derived": []}
    done = []
    for p in sorted((root / kind).iterdir()):
        if p.suffix.lower() not in IMG:
            continue
        keep = src / p.name
        if not keep.exists():
            shutil.copy2(p, keep)
        with Image.open(p) as im:
            out, changed = stretch(im, lo_pct, hi_pct)
            if not changed:
                continue
            out.save(p)
        prev = next((d for d in rec["derived"] if d.get("file") == p.name), None)
        d = {"kind": kind, "file": p.name, "transform": "levels", "engine": f"percentile stretch {lo_pct}-{hi_pct}", "source": f"sources/{p.name}",
             "source_sha256": sha256(keep), "derived_sha256": sha256(p), "after": prev["transform"] if prev and prev.get("transform") else ("trim" if prev else None),
             "crop_px": prev.get("crop_px") if prev else None}
        rec["derived"] = [x for x in rec["derived"] if x.get("file") != p.name] + [d]
        done.append(d)
    der_path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return done
