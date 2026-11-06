#!/usr/bin/env python3
"""Engine regression bench (NOT the designed ArchPortfolioBench; see archportfoliobench_ap.py). 2x2 factorial: case-retrieval {off,on} x review/repair {off,on}, over projects x output specs.
Measures objective hard gates, local-edit preservation, runtime, cost. Does NOT measure aesthetic quality (needs blinded human review).
NOT RUN here: general-LLM baseline, editing-backend comparison (OpenPencil/GenOffice), human review."""
import sys, json, time, shutil, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parents[2] / "backend" / "common" / "src")); import pascal_bootstrap; pascal_bootstrap.setup(); sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from portfolio_agent.engine import pipeline, edit

PROJECTS = ["arch_01", "arch_02", "arch_03"]
SPECS = {"A4-landscape": dict(width_mm=297, height_mm=210), "A4-portrait": dict(width_mm=210, height_mm=297), "square210-bleed3": dict(width_mm=210, height_mm=210, bleed_mm=3)}

def main():
    out = ROOT.parents[2] / ".cache/bench"; shutil.rmtree(out, ignore_errors=True); rows = []
    for p in PROJECTS:
        for sn, sv in SPECS.items():
            for cond in pipeline.CONDITIONS:
                d = out / p / sn / cond; spec = pipeline.default_spec(**sv)
                try: rep = pipeline.run(ROOT.parent / "portfolioAgent/examples/synthetic_projects" / p, d, cond, spec, pptx=False)
                except Exception as e: rows.append(dict(project=p, spec=sn, condition=cond, crashed=repr(e)[:200])); continue
                codes = sorted({i["code"] for i in rep["gate_issues"]}); row = dict(project=p, spec=sn, condition=cond, pages=rep["pages"], gate_pass=rep["gate_pass"], issue_count=len(rep["gate_issues"]), issue_codes=codes, seconds=rep["seconds"], cost_usd=0.0)
                t0 = time.perf_counter(); cand = None
                for sc in sorted((d / "scenes").glob("page-*.json")):
                    for e in json.loads(sc.read_text(encoding="utf-8"))["elements"]:
                        if e["kind"] == "text" and e["id"].startswith("caption") and e.get("text") and not e["locked"]: cand = (sc.stem, e["id"]); break
                    if cand: break
                if cand: res = edit.edit_text(d, cand[0], cand[1], "Edited caption text."); row["local_edit"] = dict(target=cand, preserved=res["ok"], reason=res.get("reason") or [i["code"] for i in res.get("qa_issues", [])] or None, px_outside=res.get("pixels_changed_outside_target"))
                else: row["local_edit"] = dict(target=None, preserved=None, reason="no editable caption")
                rows.append(row)
    agg = {}
    for r in rows:
        if "crashed" in r: continue
        a = agg.setdefault(r["condition"], dict(runs=0, gate_pass=0, issues=0, secs=0.0, edit_ok=0, edit_n=0)); a["runs"] += 1; a["gate_pass"] += r["gate_pass"]; a["issues"] += r["issue_count"]; a["secs"] += r["seconds"]
        if r["local_edit"]["preserved"] is not None: a["edit_n"] += 1; a["edit_ok"] += bool(r["local_edit"]["preserved"])
    res = dict(bench="engine-regression (not ArchPortfolioBench)", date=str(datetime.date.today()), fixtures="SYNTHETIC", aggregate={k: dict(v, secs=round(v["secs"], 1)) for k, v in agg.items()}, rows=rows,
               not_run=["general-LLM vs skill baseline (needs paid API; BLOCKED)", "editing-backend comparison (OpenPencil/GenOffice not executed)", "blinded human aesthetic review", "real-portfolio cases (no rights-cleared set)"])
    (ROOT / "benchmarks/results").mkdir(exist_ok=True); (ROOT / "benchmarks/results/engine-regression.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res["aggregate"], indent=1)); crashed = [r for r in rows if "crashed" in r]; print("crashed:", len(crashed), [c["crashed"] for c in crashed][:3])

if __name__ == "__main__": main()
