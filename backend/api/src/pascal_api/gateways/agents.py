"""Gateway to the agents: the ONLY module that imports `portfolio_agent` (hexagonal "driven adapter"; tested in tests/test_architecture_api.py).
Domain services call these functions; they never import an agent. Each function is a thin, synchronous call into one agent.

    sourcePrepAgent  prepare / levels / knockout / cutout          portfolioAgent  ingest / planned author / pipeline / catalogue
    reviewAgent      review-context / record-review / finalize
"""
import json
from pathlib import Path

from .. import _boot  # noqa: F401  (sys.path first)
from ..exceptions import unprocessable

from portfolio_agent.core import assets as core_assets  # noqa: E402
from portfolio_agent.core import paths as P  # noqa: E402


# ---- portfolioAgent: ingest / catalogue ---------------------------------------------------------------------------
def ingest(project_dir: Path):
    return core_assets.ingest(project_dir)


def backends() -> list:
    return sorted(p.parent.name for p in P.BACKENDS_DIR.glob("*/adapter.py"))


def catalog() -> dict:
    from portfolio_agent.layout import modular, photoset
    return {
        "roles": ["cover", "split", "hero", "pair", "grid", "text", "closing"],
        "page_flags": {"bleed": ["full", "split", "top", "grid"], "dark": "boolean", "strip": "boolean", "photoset": "template id", "crop": ["cover"], "focus": "[fx, fy]", "index": "boolean"},
        "grid_systems": [{"id": g["id"], "columns": g.get("columns"), "description": g.get("description", "")} for g in modular.grid_systems().values()],
        "compositions": [{"id": c["id"], "images": c.get("images"), "tags": c.get("tags", [])} for c in modular.compositions().values()],
        "photosets": [{"id": t["id"], "images": t["k"], "tags": t.get("tags", [])} for t in photoset.templates().values()],
        "backends": backends(),
    }


# ---- portfolioAgent: book plan --------------------------------------------------------------------------------------
def plan_resources() -> dict:
    return {"skill": P.PLUGIN / "skills" / "portfolio-create" / "SKILL.md", "craft": P.KNOWLEDGE_DIR / "editorial" / "layout-craft.md", "schema": P.BOOK_PLAN_SCHEMA}


def validate_plan(project_dir: Path, plan: dict) -> dict:
    """Schema + the planned author's asset rules. Returns the manifest; raises 422 carrying the author's own message."""
    import jsonschema
    from portfolio_agent.authors import planned
    try:
        jsonschema.validate(plan, json.loads(P.BOOK_PLAN_SCHEMA.read_text(encoding="utf-8")))
    except jsonschema.ValidationError as e:
        raise unprocessable("plan_schema", f"book plan schema violation at {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:300]}")
    manifest, _ = core_assets.ingest(project_dir)
    try:
        planned.check(plan, manifest)
    except planned.BookPlanError as e:
        raise unprocessable("plan_assets", str(e))
    return manifest


def compose(project_dir: Path, plan_path: Path, spec_args: dict, domain, also) -> dict:
    from portfolio_agent.engine import pipeline
    from portfolio_agent.engine.spec import default_spec
    style = {k: v for k, v in spec_args.get("style", {}).items() if v is not None}
    spec = default_spec(width_mm=spec_args["width_mm"], height_mm=spec_args["height_mm"], margin_mm=spec_args["margin_mm"], bleed_mm=spec_args["bleed_mm"], style=style)
    rep = pipeline.run_author(str(project_dir), str(project_dir / "out"), "planned", {"plan_path": str(plan_path)}, spec, domain, do_repair=True, label="B4_plan", also=tuple(also))
    return {"attempt": rep.get("attempt"), "pages": rep.get("pages"), "gate_pass": rep.get("gate_pass"), "seconds": rep.get("seconds"),
            "blocking": [_issue(i) for i in rep.get("blocking_issues", [])], "advisory": [_issue(i) for i in rep.get("advisory_issues", [])]}


def _issue(i: dict) -> dict:
    return {"code": i["code"], "page": i.get("page"), "elements": i.get("elements"), "details": i.get("details")}


# ---- sourcePrepAgent ------------------------------------------------------------------------------------------------
def prepare(project_dir: Path, approve: bool, levels: bool, knockout: bool, knockout_files: list) -> dict:
    from portfolio_agent.engine import levels as lv, prepare as prep
    rec = prep.prepare(project_dir, approve=approve)
    sheet = None
    if rec["proposals"]:
        sheet = project_dir / "out" / "prepare-proposals.png"
        sheet.parent.mkdir(parents=True, exist_ok=True)
        prep.proposal_sheet(project_dir, str(sheet))
    out = {"proposals": len(rec["proposals"]), "approved": rec["approved"], "derived": len(rec["derived"]), "sheet": "out/prepare-proposals.png" if sheet else None}
    if levels:
        out["levels"] = [d["file"] for d in lv.levels(project_dir)]
    if knockout or knockout_files:
        out["knockout"] = [d["file"] for d in lv.knockout(project_dir, kinds=("drawings",) if knockout else (), files=knockout_files)]
    return out


def cutout(project_dir: Path, files: list, engine: str) -> dict:
    from portfolio_agent.engine import cutout as co
    done = co.cutout(project_dir, files, engine=engine)
    sheet = project_dir / "out" / "cutout-sheet.png"
    sheet.parent.mkdir(parents=True, exist_ok=True)
    co.cutout_sheet(project_dir, str(sheet))
    return {"cutouts": [{"file": d["file"], "opaque_fraction": d["opaque_fraction"], "engine": d["engine"]} for d in done], "sheet": "out/cutout-sheet.png"}


# ---- reviewAgent ------------------------------------------------------------------------------------------------------
def _review(fn_name: str, out_dir: Path, *args):
    from portfolio_agent.engine import review
    try:
        return getattr(review, fn_name)(out_dir, *args)
    except review.ReviewError as e:
        raise unprocessable("review", str(e))


def review_context(out_dir: Path) -> dict:
    return _review("review_context", out_dir)


def record_review(out_dir: Path, review_json_path: Path) -> dict:
    return _review("record_review", out_dir, review_json_path)


def finalize(out_dir: Path) -> dict:
    return _review("finalize", out_dir)
