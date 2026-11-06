"""Generate >=3 genuinely different layout candidates + objective metrics + a blind review packet for an INDEPENDENT critic.
No candidate is auto-declared winner."""
import json
import random
from pathlib import Path
import fitz
import numpy as np
from PIL import Image
from portfolio_agent.core import assets
from . import pipeline

STYLES = {  # composition constraints, not coordinates
    "c1": dict(spec=dict(margin_mm=18, gutter_mm=9), style=dict(title_scale=1.0, body_pt=11)),
    "c2": dict(spec=dict(margin_mm=10, gutter_mm=4), style=dict(title_scale=1.25, body_pt=10.5)),
    "c3": dict(spec=dict(margin_mm=14, gutter_mm=6), style=dict(title_scale=1.1, body_pt=12, mirror=True)),
}


def _ink(pdf):
    d = fitz.open(pdf)
    out = []
    for p in d:
        a = np.frombuffer(p.get_pixmap(dpi=30).samples, np.uint8).reshape(-1, 3)
        out.append(float((a.min(axis=1) < 245).mean()))
    return out


def run(project, out_dir, base_spec=None, n=3, condition="B3_full"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    names = list(STYLES)[:n]
    random.Random(7).shuffle(names)  # blind labels A, B, C
    cands = []
    for label, key in zip("ABC", names):
        cfg = STYLES[key]
        b = base_spec or {}
        spec = pipeline.default_spec(**{**b, **cfg["spec"], "style": {**b.get("style", {}), **cfg["style"]}})
        d = out / f"cand_{label}"
        rep = pipeline.run(project, d, condition, spec, pptx=False)
        ink = _ink(d / "book.pdf")
        sheet = []
        for p in fitz.open(d / "book.pdf"):
            pm = p.get_pixmap(dpi=45)
            sheet.append(Image.frombytes("RGB", (pm.width, pm.height), pm.samples))
        w, h = sheet[0].size
        cols = min(3, len(sheet))
        rows = (len(sheet) + cols - 1) // cols
        S = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 8) + 8), (110, 110, 110))
        for k, im in enumerate(sheet):
            S.paste(im, (8 + (k % cols) * (w + 8), 8 + (k // cols) * (h + 8)))
        S.save(d / "sheet.png")
        cands.append(dict(label=label, _style_key=key, gate_pass=rep["gate_pass"], gate_codes=sorted({i["code"] for i in rep["gate_issues"]}), pages=rep["pages"],
                          ink_mean=round(float(np.mean(ink)), 3), ink_min=round(min(ink), 3), ink_max=round(max(ink), 3), sheet=f"cand_{label}/sheet.png", pdf=f"cand_{label}/book.pdf"))
    (out / "_unblind_key.json").write_text(json.dumps({c["label"]: c["_style_key"] for c in cands}), encoding="utf-8")
    public = [{k: v for k, v in c.items() if k != "_style_key"} for c in cands]
    manifest, brief = assets.ingest(project)
    ctx = dict(domain=brief["domain"], title=brief["title"], audience=brief["audience"], asset_roles=sorted({a["role"] for a in manifest["assets"]}), candidates=public,
               rubric="knowledge/editorial/critic-rubric.md",
               instruction="Fresh reviewer only. Score each candidate per rubric, list issues, rank, or reject all. Do not read _unblind_key.json.")
    (out / "review_context.json").write_text(json.dumps(ctx, indent=1, ensure_ascii=False), encoding="utf-8")
    return ctx
