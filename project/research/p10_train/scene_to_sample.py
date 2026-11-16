"""One page of a run -> one training sample in the layout-model format (PosterCopilot card and paper arXiv 2512.04082, read 2026-11-15):
layers/<n>_<type|image>.png (one PNG per element, text on a transparent ground) + target.json (canvas_size + per-layer box, order, category)
+ target.dsl, the same layout as a compact line format (owner's decision 2026-11-15, after FLOORA arXiv 2609.36064: a DSL of 642 characters
against more than 10,000 for the verbose form; fewer tokens, fewer digits to get wrong):

  page W H            page size in whole mm
  <id> <kind> x y w h one line per layer, back to front; id = layer number, kind = image | drawing | title | body | caption | label | text; whole mm

target.json stays for weights that were trained to emit JSON (PosterCopilot); target.dsl is what a model we train ourselves should emit.

  scene_to_sample.py RUN_DIR OUT_DIR [--px 8] [--pages page-01 ...] [--source LABEL]

What goes in: visible pictures, drawings and text. Running header, page number and hairlines stay out: the rules place that furniture.
`source` is written into meta.json so a training set can be filtered by where the layout came from (real | claude | engine). Pages laid out
by our own engine must not be trained on: they only teach the rules back.
"""
import argparse
import json
from pathlib import Path
import fitz
from PIL import Image


def text_layer(img):
    """Ink on a transparent ground: alpha from darkness, colour kept (the paper rasterises text into image layers)."""
    rgb = img.convert("RGB")
    alpha = rgb.convert("L").point(lambda v: 255 - v)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def page_sample(page, sc, out, px, source):
    layers = out / "layers"
    layers.mkdir(parents=True, exist_ok=True)
    for f in layers.glob("*.png"):
        f.unlink()
    els = [e for e in sc["elements"] if e.get("visible") is not False and e["kind"] != "shape" and not e["id"].startswith("header")
           and (e["kind"] != "text" or e.get("text"))]
    els.sort(key=lambda e: (e["kind"] == "text", e["id"]))
    stack = {e["id"]: i for i, e in enumerate(sc["elements"])}   # later in the scene = nearer the viewer
    top = max(stack.values())
    target, meta = [], []
    for n, e in enumerate(els):
        x, y, w, h = e["box_mm"]
        pm = page.get_pixmap(dpi=round(px * 25.4), clip=fitz.Rect(x, y, x + w, y + h) * (72 / 25.4))
        img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
        cat = "type" if e["kind"] == "text" else "image"
        (text_layer(img) if cat == "type" else img).save(layers / f"{n}_{cat}.png")
        target.append({"image_id": n, "category": cat, "x": round(x * px), "y": round(y * px), "w": round(w * px), "h": round(h * px), "order": top - stack[e["id"]]})
        meta.append({"image_id": n, "element": e["id"], "kind": e["kind"], "role": e.get("role"), "asset_id": e.get("asset_id"), "font_size_pt": e.get("font_size_pt")})
    W, H = round(sc["size_mm"][0] * px), round(sc["size_mm"][1] * px)
    kind = {e["id"]: ("drawing" if e["kind"] == "pdf-region" else "image" if e["kind"] != "text" else
                      next((k for k in ("title", "body", "caption", "label") if e["id"].startswith(k)), "text")) for e in els}
    lines = [f"page {round(sc['size_mm'][0])} {round(sc['size_mm'][1])}"]
    for n, e in sorted(enumerate(els), key=lambda ne: stack[ne[1]["id"]]):
        lines.append(f"{n} {kind[e['id']]} " + " ".join(str(round(v)) for v in e["box_mm"]))
    (out / "target.dsl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "target.json").write_text(json.dumps({"canvas_size": {"width": W, "height": H}, "layers": sorted(target, key=lambda t: t["order"])}, indent=1), encoding="utf-8")
    (out / "meta.json").write_text(json.dumps({"page_id": sc["page_id"], "px_per_mm": px, "source": source, "layers": meta}, indent=1, ensure_ascii=False), encoding="utf-8")
    return len(target)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("out")
    ap.add_argument("--px", type=int, default=8)
    ap.add_argument("--pages", nargs="*")
    ap.add_argument("--source", default="engine", choices=["real", "claude", "engine"])
    a = ap.parse_args()
    run, out = Path(a.run), Path(a.out)
    doc = fitz.open(run / "book.pdf")
    for i, f in enumerate(sorted((run / "scenes").glob("page-*.json"))):
        sc = json.loads(f.read_text(encoding="utf-8"))
        if a.pages and sc["page_id"] not in a.pages:
            continue
        print(sc["page_id"], page_sample(doc[i], sc, out / sc["page_id"], a.px, a.source), "layers")


if __name__ == "__main__":
    main()
