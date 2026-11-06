"""Cut-outs ("누끼"): remove the background of a photograph so a product, model or object can sit on the book's paper.

Who decides: the host LLM (skills/portfolio-cutout/SKILL.md) names WHICH images get a cut-out (objects / models / people on a
background that adds nothing). This module only executes, deterministically and reversibly: the original stays byte-identical in
`sources/`, the working copy in `images/` becomes an RGBA PNG trimmed to the subject, and `derived.json` records the transform
(engine, hashes, alpha bbox) so `core/assets.py` can show it as `source_transform` on the asset.

Engines (plug-in functions `bytes -> RGBA PIL.Image`):
  rembg       MIT, danielgatis/rembg, u2net ONNX model, local CPU, offline once the model is cached (default)
  photocraft  Apache-2.0, storytold/photocraft `layer.removeBackground` (crates/algo/src/segment/subject.rs, graph-cut subject
              selection, no ML model) through `photocraft-cli run`; signed release binary in .cache/bin/photocraft (never vendored).
"""
import io
import json
import shutil
from pathlib import Path

from PIL import Image

from portfolio_agent.core.sources.assets import sha256
from portfolio_agent.core.workspace import CACHE_DIR

PAD_FRAC = 0.04     # breathing room around the subject's alpha bbox
IMG = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")


def _engine_rembg(data: bytes) -> Image.Image:
    from rembg import remove  # imported lazily: optional dependency
    return Image.open(io.BytesIO(remove(data))).convert("RGBA")


PHOTOCRAFT_CLI = CACHE_DIR / "bin" / "photocraft" / "photocraft-cli.exe"   # v0.20.2, sha256 + Authenticode verified 2026-11-05 (evidence/BLEED_AND_CUTOUT_2026-11-05.md)


def _engine_photocraft(data: bytes) -> Image.Image:
    """storytold/photocraft headless: `photocraft-cli run in.jpg --cmd layer.removeBackground --out out.png` (0.3 s per photo, no model download)."""
    import subprocess
    import tempfile
    if not PHOTOCRAFT_CLI.is_file():
        raise RuntimeError(f"photocraft engine unavailable: {PHOTOCRAFT_CLI} missing (download the signed release zip into .cache/bin/photocraft and verify its SHA256SUMS first)")
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.png"
        Image.open(io.BytesIO(data)).convert("RGB").save(src)
        out = Path(td) / "out.png"
        p = subprocess.run([str(PHOTOCRAFT_CLI), "run", str(src), "--cmd", "layer.removeBackground", "--out", str(out)], capture_output=True, text=True, timeout=300)
        if p.returncode != 0 or not out.is_file():
            raise RuntimeError(f"photocraft-cli failed ({p.returncode}): {p.stderr[-400:]}")
        return Image.open(out).convert("RGBA").copy()


ENGINES = {"rembg": (_engine_rembg, "rembg/u2net (MIT)"), "photocraft": (_engine_photocraft, "photocraft select-subject (Apache-2.0)")}


def _trim(im: Image.Image, pad_frac=PAD_FRAC):
    """Crop an RGBA image to its alpha bbox plus padding. Returns (image, bbox_px) or (im, None) when nothing is opaque."""
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        return im, None
    x0, y0, x1, y1 = bbox
    px, py = int((x1 - x0) * pad_frac), int((y1 - y0) * pad_frac)
    box = (max(0, x0 - px), max(0, y0 - py), min(im.width, x1 + px), min(im.height, y1 + py))
    return im.crop(box), [box[0], box[1], box[2] - box[0], box[3] - box[1]]


def cutout(project_dir, files, engine="rembg", pad_frac=PAD_FRAC):
    """Cut out `files` (names under images/). Writes images/<stem>.png (RGBA), keeps originals in sources/, appends to derived.json."""
    root = Path(project_dir)
    src = root / "sources"
    src.mkdir(exist_ok=True)
    fn, label = ENGINES[engine]
    der_path = root / "derived.json"
    rec = json.loads(der_path.read_text(encoding="utf-8")) if der_path.is_file() else {"proposals": [], "approved": True, "derived": []}
    done = []
    for name in files:
        p = root / "images" / name
        if not p.is_file() or p.suffix.lower() not in IMG:
            raise FileNotFoundError(f"not an image under images/: {name}")
        keep = src / p.name
        if not keep.exists():
            shutil.copy2(p, keep)                      # original preserved, byte-identical
        data = keep.read_bytes()
        im = fn(data)
        im, bbox = _trim(im, pad_frac)
        if bbox is None:
            raise RuntimeError(f"{name}: the engine found no subject (fully transparent result); leave this photo as it is")
        out = p.with_suffix(".png")
        if out != p:
            p.unlink()                                 # the working copy is replaced by the RGBA png; the original is in sources/
        im.save(out)
        import numpy as np
        frac = float((np.asarray(im.getchannel("A")) > 8).mean())
        d = {"kind": "images", "file": out.name, "transform": "cutout", "engine": label, "crop_px": bbox,
             "source": f"sources/{p.name}", "source_sha256": sha256(keep), "derived_sha256": sha256(out), "opaque_fraction": round(frac, 3)}
        rec["derived"] = [x for x in rec["derived"] if x.get("file") != out.name] + [d]
        done.append(d)
    der_path.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return done


def cutout_sheet(project_dir, out_png, max_w=520):
    """Before / after (on a checkerboard) for every recorded cut-out, for the person to approve by eye."""
    root = Path(project_dir)
    rec = json.loads((root / "derived.json").read_text(encoding="utf-8"))
    rows = []
    for d in rec.get("derived", []):
        if d.get("transform") != "cutout":
            continue
        before = Image.open(root / d["source"]).convert("RGB")
        after = Image.open(root / "images" / d["file"]).convert("RGBA")
        cb = _checker(after.size)
        cb.alpha_composite(after)
        tiles = []
        for im in (before, cb.convert("RGB")):
            s = max_w / im.width
            tiles.append(im.resize((max_w, max(1, int(im.height * s)))))
        rows.append(tiles)
    if not rows:
        return None
    th = [max(t.height for t in r) for r in rows]
    sheet = Image.new("RGB", (2 * (max_w + 10) + 10, sum(th) + 10 * (len(rows) + 1)), (120, 120, 120))
    y = 10
    for r, h in zip(rows, th):
        for i, t in enumerate(r):
            sheet.paste(t, (10 + i * (max_w + 10), y))
        y += h + 10
    sheet.save(out_png)
    return out_png


def _checker(size, cell=24):
    w, h = size
    im = Image.new("RGBA", size, (255, 255, 255, 255))
    px = im.load()
    for yy in range(0, h, cell):
        for xx in range(0, w, cell):
            if (xx // cell + yy // cell) % 2:
                for j in range(yy, min(h, yy + cell)):
                    for i in range(xx, min(w, xx + cell)):
                        px[i, j] = (210, 210, 210, 255)
    return im
