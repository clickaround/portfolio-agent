"""Orchestration only: ingest -> author.propose -> (repair) -> export -> gates. No layout, rendering or domain logic lives here."""
import json
import shutil
import time
from pathlib import Path
from portfolio_agent.core.sources import assets
from portfolio_agent.core.guardrails import gates, repair, references
from . import registry
from .spec import default_spec, from_design_plan  # noqa: F401  (re-exported: engine's public API)

# Ablation conditions for the rule-based author (see benchmarks/): switches only, no behaviour of their own.
CONDITIONS = {
    "B0_naive": dict(cases=False, review=False),
    "B1_cases": dict(cases=True, review=False),
    "B2_review": dict(cases=False, review=True),
    "B3_full": dict(cases=True, review=True),
}


def run_author(project_dir, out_dir, author, options, spec=None, domain=None, pptx=True, do_repair=True, backend="local", also=(), label=None):
    """Generic run: any Author, any measurer/exporter backend (default local), optional extra exporters (e.g. 'designcraft')."""
    t0 = time.perf_counter()
    spec = spec or default_spec()
    be = registry.get_backend(backend)
    be.configure(spec.get("style"))
    out = Path(out_dir)
    (out / "scenes").mkdir(parents=True, exist_ok=True)
    manifest, brief = assets.ingest(project_dir)
    if domain:
        brief["domain"] = domain
    au = registry.get_author(author)
    plan, scenes = au.propose(brief, manifest, spec, be, options)
    spec["style"] = {**plan.get("meta", {}).get("style_defaults", {}), **(spec.get("style") or {})}  # author defaults under user choices
    be.configure(spec["style"])
    repairs = []
    if do_repair:
        for sc in scenes:
            r = repair.repair_scene(sc, manifest, spec, be)
            repairs.append({"page": sc["page_id"], "touched": r["touched"], "log": r["log"], "unexpected_edits": r["unexpected_edits"]})
    for sc in scenes:
        (out / "scenes" / f"{sc['page_id']}.json").write_text(json.dumps(sc, indent=1), encoding="utf-8")
    formats = ["pdf"] + (["pptx"] if pptx and "pptx" in be.capabilities else []) + (["png"] if "png" in be.capabilities else [])
    ex = be.export(scenes, manifest, project_dir, out / "book", spec, formats)
    extra = {}
    for name in also:
        extra[name] = registry.get_backend(name).export(scenes, manifest, project_dir, out / name / "book", spec, sorted(registry.get_backend(name).capabilities))
    issues = gates.qa_book(scenes, manifest, plan, spec, project_dir, be) + gates.qa_pdf(str(out / "book.pdf"), scenes, spec) + gates.grounding_issues(scenes, project_dir)
    page_scores = {}
    if ex.get("files", {}).get("png"):   # advisory visual metrics on the rendered previews (AeSlides via pptAgent)
        from portfolio_agent.core.quality import page_metrics
        for sc, png in zip(scenes, sorted(Path(ex["files"]["png"]).glob("page-*.png"))):
            pi, sc_scores = page_metrics.page_issues(str(png), sc["page_id"])
            issues += pi
            page_scores[sc["page_id"]] = sc_scores
    blocking, advisory = gates.split(issues)
    meta = plan.setdefault("meta", {})
    meta["reference_basis"] = references.reference_basis()
    report = {"reference_basis": meta["reference_basis"],"condition": label, "author": author, "backend": backend, "project": manifest["project_id"], "pattern": meta.get("pattern"), "retrieval": meta.get("retrieval"), "pages": len(scenes),
              "gate_issues": issues, "blocking_issues": blocking, "advisory_issues": advisory, "gate_pass": not blocking, "repairs": repairs, "page_scores": page_scores, "pdf_overflow": ex["overflow"], "pptx": ex["notes"], "extra_exporters": extra,
              "seconds": round(time.perf_counter() - t0, 3), "cost_usd": 0.0, "note": "hard-gate result only; says nothing about aesthetic quality"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    (out / "plan.json").write_text(json.dumps(plan, indent=1), encoding="utf-8")
    (out / "run.json").write_text(json.dumps({"project_dir": str(Path(project_dir).resolve()), "spec": spec, "author": author, "backend": backend, "options": options, "condition": label}, indent=1), encoding="utf-8")
    (out / "qa.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    report["attempt"] = _record_attempt(out, report, ex.get("files", {}))
    return report


def _record_attempt(out, report, files):
    """Immutable, numbered attempts (AutoDesign guardrail 2): every run of the same out dir is kept; `final/` is written only by review.finalize."""
    adir = out / "attempts"
    adir.mkdir(exist_ok=True)
    n = len([p for p in adir.iterdir() if p.is_dir()]) + 1
    att = adir / f"{n:02d}"
    att.mkdir()
    shutil.copytree(out / "scenes", att / "scenes")
    for name in ("plan.json", "qa.json", "manifest.json", "run.json", "book.pdf", "book.pptx"):
        if (out / name).is_file():
            shutil.copy2(out / name, att / name)
    if files.get("png") and Path(files["png"]).is_dir():
        shutil.copytree(files["png"], att / "preview")
    entry = {"attempt": att.name, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "author": report["author"], "condition": report["condition"],
             "gate_pass": report["gate_pass"], "blocking": [i["code"] for i in report["blocking_issues"]], "advisory": [i["code"] for i in report["advisory_issues"]],
             "plan_sha256": assets.sha256(att / "plan.json"), "pages": report["pages"]}
    with (adir / "ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + chr(10))
    # episode package (AI Harness Engineering, arXiv 2605.13357: one auditable record per run) - entropy = advisory churn across attempts
    hist = [json.loads(l) for l in (adir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    prev = hist[-2] if len(hist) > 1 else None
    churn = (len(set(prev["advisory"]) ^ set(entry["advisory"])) if prev else 0)
    import os as _os
    episode = {"attempt": att.name, "task": {"author": report["author"], "condition": report["condition"], "project": report["project"], "plan_sha256": entry["plan_sha256"]},
               "context": {"spec": {k: report.get(k) for k in ("pages",)}, "reference_basis": report.get("reference_basis", {}).get("tag")},
               "tools": {"backend": report["backend"], "extra_exporters": sorted(report.get("extra_exporters", {}))},
               "host": {k: _os.environ.get(v) for k, v in (("name", "PORTFOLIO_HOST"), ("model", "PORTFOLIO_MODEL"), ("session", "PORTFOLIO_SESSION"))},
               "state": {"gate_pass": report["gate_pass"], "blocking": entry["blocking"], "advisory": entry["advisory"], "page_scores": report.get("page_scores", {})},
               "failure_attribution": [{"code": i["code"], "elements": i.get("elements", []), "page": i.get("page")} for i in report["blocking_issues"]],
               "verification": {"repairs": [r["log"] for r in report["repairs"] if r["log"]], "fresh_review": None},
               "entropy": {"advisory_churn_vs_previous": churn, "plan_changed_vs_previous": bool(prev and prev["plan_sha256"] != entry["plan_sha256"])},
               "interventions": [], "recorded": entry["time"]}
    (att / "episode.json").write_text(json.dumps(episode, indent=1, ensure_ascii=False), encoding="utf-8")
    return att.name


def run(project_dir, out_dir, condition="B3_full", spec=None, domain=None, pptx=True, **kw):
    """Rule-based author with a named ablation condition (benchmark convenience)."""
    cond = CONDITIONS[condition]
    return run_author(project_dir, out_dir, "rule_based", cond, spec, domain, pptx, do_repair=cond["review"], label=condition, **kw)


def run_host(project_dir, scenes_dir, out_dir, spec=None, domain=None, pptx=True, **kw):
    """B4: host-authored scenes -> gates + bounded repair + export."""
    return run_author(project_dir, out_dir, "host", {"scenes_dir": str(scenes_dir)}, spec, domain, pptx, do_repair=True, label="B4_host", **kw)
