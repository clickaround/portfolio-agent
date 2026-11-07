"""Input -> asset manifest (immutable hashes) + project brief."""
import hashlib, re
import json
from pathlib import Path
from PIL import Image
import fitz

IMG = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

def parse_brief(path):
    t = Path(path).read_text(encoding="utf-8"); lines = t.splitlines()
    brief = {"title": "Untitled", "domain": "generic", "audience": "", "keywords": [], "sections": {}}
    cur = None
    for ln in lines:
        if ln.startswith("# ") and brief["title"] == "Untitled": brief["title"] = ln[2:].strip(); continue
        if ln.startswith("## "): cur = ln[3:].strip(); brief["sections"][cur] = []; continue
        m = re.match(r"(domain|audience|keywords):\s*(.*)", ln)
        if m and cur is None:
            brief[m.group(1)] = [k.strip() for k in m.group(2).split(",")] if m.group(1) == "keywords" else m.group(2).strip(); continue
        if cur is not None: brief["sections"][cur].append(ln)
    brief["sections"] = {k: " ".join(x.strip() for x in v if x.strip()) for k, v in brief["sections"].items()}
    return brief

def ingest(project_dir):
    root = Path(project_dir); assets = []
    for sub, role in (("images", "photo"), ("drawings", "drawing"), ("diagrams", "diagram")):
        d = root / sub
        if not d.is_dir(): continue
        for p in sorted(d.iterdir()):
            rel = p.relative_to(root).as_posix(); a = {"id": p.stem, "relative_path": rel, "sha256": sha256(p), "role": role, "rights": "owned", "original_immutable": True}
            if p.suffix.lower() in IMG:
                with Image.open(p) as im: w, h = im.size
                a.update(kind="image", width=w, height=h, crop_allowed=False)
            elif p.suffix.lower() == ".pdf":
                with fitz.open(p) as d_: r = d_[0].rect; w, h = r.width, r.height
                a.update(kind="pdf-region", width=w, height=h, crop_allowed=False, source_page=1)
            elif p.suffix.lower() == ".svg":
                with fitz.open(p) as d_: r = d_[0].rect; w, h = r.width, r.height
                a.update(kind="svg", width=w, height=h, crop_allowed=False)
            else: continue
            a["aspect"] = a["width"] / a["height"]; assets.append(a)
    ds = root / "diagrams" / "diagram-set.json"
    if ds.is_file():   # DiagramAgent (pascal-agents) delivery, contract diagram-set/v1: titles/captions travel with the SVGs
        rec = json.loads(ds.read_text(encoding="utf-8"))
        by_file = {Path(x["svg"]).name: x for x in rec.get("diagrams", [])}
        for a in assets:
            x = by_file.get(Path(a["relative_path"]).name)
            if x:
                a["title"] = x.get("title"); a["caption"] = x.get("caption", ""); a["diagram_type"] = x.get("type")
    der = root / "derived.json"
    if der.is_file():   # explicit, reversible transforms (engine/prepare.py): record them on the asset, never hide them
        rec = json.loads(der.read_text(encoding="utf-8"))
        by_file = {d["file"]: d for d in rec.get("derived", [])}
        for a in assets:
            d = by_file.get(Path(a["relative_path"]).name)
            if d:
                a["source_transform"] = {"crop_px": d.get("crop_px"), "source": d["source"], "source_sha256": d["source_sha256"],
                                         "tool": d.get("transform", "trim"), "engine": d.get("engine", "prepare")}
                if d.get("transform") == "cutout":
                    a["cutout"] = True   # RGBA subject on transparent ground: sits on the paper, never bleeds
    return {"schema_version": "0.1.0", "project_id": root.name, "assets": assets}, parse_brief(root / "project.md")
