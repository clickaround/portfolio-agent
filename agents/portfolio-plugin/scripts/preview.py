#!/usr/bin/env python3
"""Render every project/condition to PNG pages + one index.html viewer (side-by-side B0 naive vs B3 full). Usage: python scripts/preview.py [outdir]"""
import sys, os, html
from pathlib import Path
os.environ.setdefault("PYTHONUTF8", "1"); sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT.parents[1] / "backend" / "common" / "src")); import pascal_bootstrap; pascal_bootstrap.setup()
import fitz
from portfolio_agent.engine import pipeline
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parents[1] / ".cache" / "preview"; out.mkdir(parents=True, exist_ok=True); sections = []
for pr in ("arch_01", "arch_02", "arch_03"):
    row = []
    for cond in ("B0_naive", "B3_full"):
        d = out / pr / cond; rep = pipeline.run(ROOT.parent / "portfolioAgent/examples/synthetic_projects" / pr, d, cond, pipeline.default_spec(), pptx=False); pages = []
        doc = fitz.open(d / "book.pdf")
        for i, pg in enumerate(doc): f = d / f"p{i+1:02d}.png"; pg.get_pixmap(dpi=80).save(f); pages.append(f.relative_to(out).as_posix())
        codes = sorted({i["code"] for i in rep["gate_issues"]}) or ["none"]
        row.append(f"<div class='col'><h3>{cond} — gates: {'PASS' if rep['gate_pass'] else 'FAIL'} <small>{html.escape(', '.join(codes))}</small></h3><div class='pages'>" + "".join(f"<img src='{p}'>" for p in pages) + f"</div><a href='{(d/'book.pdf').relative_to(out).as_posix()}'>book.pdf</a></div>")
    sections.append(f"<h2>{pr}</h2><div class='cols'>{''.join(row)}</div>")
(out / "index.html").write_text("<!doctype html><meta charset=utf-8><title>Portfolio preview</title><style>body{font-family:Segoe UI,sans-serif;background:#eee;margin:20px}.cols{display:flex;gap:24px;align-items:flex-start}.col{flex:1;background:#fff;padding:12px}.pages{display:flex;flex-wrap:wrap;gap:8px}img{width:48%;border:1px solid #bbb}small{color:#a00;font-weight:400}h3{margin:0 0 8px}</style><h1>Synthetic fixtures — NOT real design quality evidence</h1>" + "".join(sections), encoding="utf-8")
print(out / "index.html")
