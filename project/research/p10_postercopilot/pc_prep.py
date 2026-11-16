"""Turn pages of one of our runs into PosterCopilot layer folders: each visible element cropped from the rendered page (text keeps its
real type, pictures their real pixels). Running header and hairlines are left out: they are furniture the rules place.

  pc_prep.py RUN_DIR OUT_DIR VENDOR MODEL page-01 page-02 ...   -> OUT_DIR/<page>/layers/*.png, OUT_DIR/<page>/map.json, OUT_DIR/jobs.json
"""
import json
import sys
from pathlib import Path
import fitz

run, out = Path(sys.argv[1]), Path(sys.argv[2])
pages = sys.argv[3:]
PX = 8   # px per mm: A4 landscape -> 2376 x 1680
doc = fitz.open(run / "book.pdf")
scenes = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((run / "scenes").glob("page-*.json"))]
jobs = []
for i, sc in enumerate(scenes):
    if sc["page_id"] not in pages:
        continue
    pix = doc[i].get_pixmap(dpi=round(PX * 25.4))
    d = out / sc["page_id"] / "layers"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("*.png"):
        f.unlink()
    els = [e for e in sc["elements"] if e.get("visible") is not False and e["kind"] != "shape" and not e["id"].startswith("header")
           and (e["kind"] != "text" or e.get("text"))]
    els.sort(key=lambda e: (e["kind"] == "text", e["id"]))   # pictures first, like the reference examples
    mapping = []
    for n, e in enumerate(els):
        x, y, w, h = e["box_mm"]
        clip = fitz.IRect(round(x * PX), round(y * PX), round((x + w) * PX), round((y + h) * PX)) & pix.irect
        name = f"{n}_{'type' if e['kind'] == 'text' else 'image'}.png"
        fitz.Pixmap(pix, pix.width, pix.height, clip).save(d / name) if False else fitz.Pixmap(doc[i].get_pixmap(dpi=round(PX * 25.4), clip=fitz.Rect(x, y, x + w, y + h) * (72 / 25.4))).save(d / name)
        mapping.append({"image_id": n, "file": name, "element": e["id"], "kind": e["kind"], "box_mm": e["box_mm"]})
    W, H = round(sc["size_mm"][0] * PX), round(sc["size_mm"][1] * PX)
    (out / sc["page_id"] / "map.json").write_text(json.dumps({"page_id": sc["page_id"], "px_per_mm": PX, "canvas": [W, H], "layers": mapping}, indent=1), encoding="utf-8")
    jobs.append({"assets": str(d), "width": W, "height": H, "out": str(out / sc["page_id"] / "layout.json")})
    print(sc["page_id"], len(mapping), "layers", W, H)
(out / "jobs.json").write_text(json.dumps(jobs, indent=1), encoding="utf-8")
