#!/usr/bin/env python3
"""ArchPortfolioBench (design: benchmarks/SPEC.md + PROTO_V3.md) - engine-only tasks AP-03, AP-05, AP-06, AP-07, AP-08.

What this is: deterministic checks of creation/editing behaviour of ONE system (local compositor + optional DesignCraft export) on SYNTHETIC fixtures.
What this is NOT: the pre-registered B0-B5 host comparison (needs Claude/Codex host runs), AP-01/02/04/09/10, blind human preference, real cases.
Writes benchmarks/reports/<run-id>.json in the PROTO_V3 output shape; fields that were not measured are null, never guessed.
"""
import sys, json, time, shutil, datetime, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from portfolio_agent.engine import pipeline, edit, registry  # noqa: E402

FIX = ROOT.parent / "portfolioAgent/examples/synthetic_projects"
OUT = ROOT.parents[1] / ".cache/bench_ap"


def load_scenes(d):
    return [json.loads(f.read_text(encoding="utf-8")) for f in sorted((Path(d) / "scenes").glob("page-*.json"))]


def page_hash(pdf, i):
    import fitz, hashlib
    d = fitz.open(pdf); h = hashlib.sha256(d[i].get_pixmap(dpi=72).samples).hexdigest(); d.close(); return h


def ap03(proj):
    """A3 landscape book: page size exact, no clipping/overflow, source intact. (Design asks for 2 pages; we refuse silent asset drop -> natural page count reported.)"""
    d = OUT / proj / "ap03"; spec = pipeline.default_spec(width_mm=420, height_mm=297, margin_mm=15)
    rep = pipeline.run(FIX / proj, d, "B3_full", spec, pptx=False)
    import fitz
    doc = fitz.open(d / "book.pdf"); sizes = {(round(p.rect.width / 72 * 25.4), round(p.rect.height / 72 * 25.4)) for p in doc}; n = doc.page_count; doc.close()
    return dict(task="AP-03", project=proj, passed=rep["gate_pass"] and sizes == {(420, 297)}, pages=n, two_page_requirement_met=(n == 2), gate_codes=sorted({i["code"] for i in rep["gate_issues"]}))


def _base(proj, cond="B3_full"):
    d = OUT / proj / "base"; shutil.rmtree(d, ignore_errors=True)
    pipeline.run(FIX / proj, d, cond, pipeline.default_spec(), pptx=False); return d


def ap05(proj):
    """Enlarge one graphic by 20%: target must change; only listed reflow allowed; everything else stable. Refusal with a named reason is a SAFE outcome, reported separately."""
    d = _base(proj); res = []
    for sc in load_scenes(d):
        gs = [e for e in sc["elements"] if e["kind"] in ("image", "pdf-region")]
        if len(gs) >= 1:
            tgt = min(gs, key=lambda e: e["box_mm"][2] * e["box_mm"][3])  # smallest graphic has the most room
            r = edit.edit_element(d, sc["page_id"], tgt["id"], scale=1.2, auto_repair=True)
            res.append(dict(page=sc["page_id"], target=tgt["id"], committed=r["ok"], refused_reasons=sorted({i["code"] for i in r.get("qa_issues", [])} | {i["code"] for i in r.get("scene_diff", [])}), reflowed=r.get("reflowed"), px_outside=r.get("pixels_changed_outside_target")))
    return dict(task="AP-05", project=proj, attempts=res, committed=sum(x["committed"] for x in res), safely_refused=sum(not x["committed"] for x in res),
                unsafe_commits=sum(1 for x in res if x["committed"] and (x["px_outside"] or 0) > 0))


def ap06(proj):
    """Double a caption's length: overflow must trigger repair or controlled reflow; nothing else may change."""
    d = _base(proj); res = []
    for sc in load_scenes(d):
        for e in sc["elements"]:
            if e["kind"] == "text" and e["id"].startswith("caption") and e.get("text"):
                r = edit.edit_element(d, sc["page_id"], e["id"], text=(e["text"] + " ") * 2 + e["text"], auto_repair=True)  # 3x to force overflow in small boxes
                res.append(dict(page=sc["page_id"], target=e["id"], committed=r["ok"], reasons=sorted({i["code"] for i in r.get("qa_issues", [])}), reflowed=r.get("reflowed"), px_outside=r.get("pixels_changed_outside_target")))
    return dict(task="AP-06", project=proj, attempts=res, committed=sum(x["committed"] for x in res), safely_refused=sum(not x["committed"] for x in res))


def ap07(proj):
    """Revise page 2 only: page 1 (and all other pages) must render identically."""
    d = _base(proj)
    sc = load_scenes(d)[1]; tgt = next((e for e in sc["elements"] if e["kind"] == "text" and e["id"].startswith(("body", "caption", "title"))), None)
    if tgt is None: return dict(task="AP-07", project=proj, passed=None, note="no editable text on page 2")
    hashes = [page_hash(d / "book.pdf", i) for i in range(len(load_scenes(d)))]
    r = edit.edit_element(d, sc["page_id"], tgt["id"], text="Revised page two text.", auto_repair=True)
    after = [page_hash(d / "book.pdf", i) for i in range(len(hashes))]
    return dict(task="AP-07", project=proj, committed=r["ok"], other_pages_identical=all(h == a for i, (h, a) in enumerate(zip(hashes, after)) if i != 1), page2_changed=hashes[1] != after[1] if r["ok"] else None, reasons=sorted({i["code"] for i in r.get("qa_issues", [])}))


def ap08(proj):
    """Export PDF + editable artifact: files open, PPTX objects are editable (text boxes/pictures, named by element id), scene JSON validates against contracts/scene-document.schema.json."""
    d = OUT / proj / "ap08"; shutil.rmtree(d, ignore_errors=True)
    rep = pipeline.run(FIX / proj, d, "B3_full", pipeline.default_spec(), pptx=True)
    import fitz, jsonschema
    from pptx import Presentation
    pdf_ok = fitz.open(d / "book.pdf").page_count == rep["pages"]
    prs = Presentation(str(d / "book.pptx")); shapes = [s for sl in prs.slides for s in sl.shapes]
    named = sum(1 for s in shapes if s.name and not s.name.startswith(("Picture", "TextBox", "Rectangle")))
    texts = sum(1 for s in shapes if s.has_text_frame and s.text_frame.text.strip())
    schema = json.loads((ROOT.parents[1] / "backend/common/contracts/scene-document.schema.json").read_text(encoding="utf-8"))
    valid = True
    try:
        for sc in load_scenes(d): jsonschema.validate(sc, schema)
    except jsonschema.ValidationError as e:
        valid = f"INVALID: {e.message[:120]}"
    dc = None
    try:
        be = registry.get_backend("designcraft")
        r = be.export(load_scenes(d), json.loads((d / "manifest.json").read_text(encoding="utf-8")), FIX / proj, d / "dc" / "book", pipeline.default_spec(), ["pdf", "pptx", "native", "idml"])
        dc = dict(exit=r["exit"], files={k: bool(v) for k, v in r["files"].items()})
    except Exception as ex:  # adapter optional
        dc = dict(error=repr(ex)[:160])
    from portfolio_agent.core.quality import diagnostics
    diag = diagnostics.analyse(d / "book.pdf", load_scenes(d))
    pei_pptx = diagnostics.pei_estimate(d / "book.pptx")
    pei_dc = diagnostics.pei_estimate(d / "dc" / "book.pptx", has_vector_in_native=True, has_masters_or_styles=True) if dc and dc.get("files", {}).get("pptx") else None
    return dict(task="AP-08", project=proj, diagnostics=diag, pei_local_pptx=pei_pptx, pei_designcraft_native_estimate=pei_dc, pdf_opens=pdf_ok, pptx_slides=len(prs.slides), pptx_shapes=len(shapes), pptx_text_boxes_nonempty=texts, pptx_named_objects=named, scene_json_schema_valid=valid, designcraft_export=dc,
                note="PPTX opened with python-pptx only; PowerPoint/Keynote opening and preview parity NOT checked")


def main():
    shutil.rmtree(OUT, ignore_errors=True); t0 = time.time(); results = []
    for proj in ("arch_01", "arch_02", "arch_03"):
        for fn in (ap03, ap05, ap06, ap07, ap08):
            try: results.append(fn(proj))
            except Exception as e: results.append(dict(task=fn.__name__.upper(), project=proj, crashed=repr(e)[:300]))
    run_id = datetime.datetime.now().strftime("apbench-%Y%m%d-%H%M%S")
    try: sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or None
    except Exception: sha = None
    report = dict(run_id=run_id, bench="ArchPortfolioBench (engine-only subset)", source_case_ids=[], fixtures="SYNTHETIC", output_format="A4/A3 landscape PDF + PPTX + scene JSON (+DesignCraft if installed)", renderer="portfolio_agent local compositor (PyMuPDF)",
                  host=None, model=None, sha=sha, prompt_version=None, hard_gates={"checked": ["G1 source hash", "G3 clip/overflow/overlap (via qa)"], "not_checked": ["G2 human zoom review", "G4 fact links", "G5 recipient policy"]},
                  scores=None, human_preferences=None, cost_usd=0.0, latency_s=round(time.time() - t0, 1), evidence_paths=[], blinded=False,
                  status="PARTIAL - engine tasks only; B0-B5 host conditions, AP-01/02/04/09/10, blind human review NOT RUN", results=results)
    (ROOT / "benchmarks/reports").mkdir(exist_ok=True); p = ROOT / f"benchmarks/reports/{run_id}.json"; p.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in results: print(json.dumps({k: v for k, v in r.items() if k != "attempts"}, ensure_ascii=False)[:260])
    print("report:", p)


if __name__ == "__main__":
    main()
