"""Adapters between HTTP and the agents. Each function is a thin, synchronous call into one agent; routes decide whether it runs in a job.

    sourcePrepAgent  prepare / levels / knockout / cutout        portfolioAgent  ingest / planned author / pipeline / catalogue
    reviewAgent      review-context / record-review / finalize
"""
import json
import shutil
import time
from pathlib import Path

from . import _boot  # noqa: F401  (sys.path first)
from .errors import ApiError, unprocessable

from portfolio_agent.core import assets as core_assets  # noqa: E402
from portfolio_agent.core import paths as P  # noqa: E402


# ---- manifest ---------------------------------------------------------------------------------------------------
def manifest(project_dir: Path) -> dict:
    m, brief = core_assets.ingest(project_dir)
    return {"manifest": m, "brief": brief}


# ---- sourcePrepAgent --------------------------------------------------------------------------------------------
def prepare(project_dir: Path, req) -> dict:
    from portfolio_agent.engine import levels, prepare as prep
    rec = prep.prepare(project_dir, approve=req.approve)
    sheet = None
    if rec["proposals"]:
        sheet = project_dir / "out" / "prepare-proposals.png"
        sheet.parent.mkdir(parents=True, exist_ok=True)
        prep.proposal_sheet(project_dir, str(sheet))
    out = {"proposals": len(rec["proposals"]), "approved": rec["approved"], "derived": len(rec["derived"]), "sheet": "out/prepare-proposals.png" if sheet else None}
    if req.levels:
        out["levels"] = [d["file"] for d in levels.levels(project_dir)]
    if req.knockout or req.knockout_files:
        out["knockout"] = [d["file"] for d in levels.knockout(project_dir, kinds=("drawings",) if req.knockout else (), files=req.knockout_files)]
    return out


def cutout(project_dir: Path, req) -> dict:
    from portfolio_agent.engine import cutout as co
    done = co.cutout(project_dir, req.files, engine=req.engine)
    sheet = project_dir / "out" / "cutout-sheet.png"
    sheet.parent.mkdir(parents=True, exist_ok=True)
    co.cutout_sheet(project_dir, str(sheet))
    return {"cutouts": [{"file": d["file"], "opaque_fraction": d["opaque_fraction"], "engine": d["engine"]} for d in done], "sheet": "out/cutout-sheet.png"}


# ---- book plan --------------------------------------------------------------------------------------------------
def read_plan(project_dir: Path) -> dict:
    p = project_dir / "book-plan.json"
    if not p.is_file():
        raise ApiError(404, "no_plan", "this project has no book plan yet")
    return json.loads(p.read_text(encoding="utf-8"))


def validate_plan(project_dir: Path, plan: dict) -> dict:
    """Schema + asset rules of the planned author. Returns the manifest; raises 422 with the author's own message."""
    from portfolio_agent.authors import planned
    import jsonschema
    try:
        jsonschema.validate(plan, json.loads(P.BOOK_PLAN_SCHEMA.read_text(encoding="utf-8")))
    except jsonschema.ValidationError as e:
        raise unprocessable("plan_schema", f"book plan schema violation at {'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message[:300]}")
    m, _ = core_assets.ingest(project_dir)
    try:
        planned.check(plan, m)
    except planned.BookPlanError as e:
        raise unprocessable("plan_assets", str(e))
    return m


def write_plan(project_dir: Path, plan: dict) -> dict:
    validate_plan(project_dir, plan)
    (project_dir / "plans").mkdir(exist_ok=True)
    cur = project_dir / "book-plan.json"
    if cur.is_file():
        shutil.copy2(cur, project_dir / "plans" / f"book-plan-{time.strftime('%Y%m%d-%H%M%S')}.json")
    cur.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"pages": len(plan["pages"]), "versions": len(list((project_dir / "plans").glob("book-plan-*.json")))}


def plan_prompt(project_dir: Path, m: dict, brief_md: str, instructions: str, target: Path, error: str = "") -> str:
    skill = P.PLUGIN / "skills" / "portfolio-create" / "SKILL.md"
    craft = P.KNOWLEDGE_DIR / "editorial" / "layout-craft.md"
    assets = [{k: a[k] for k in ("id", "role", "kind", "aspect", "width", "height") if k in a} | ({"title": a["title"], "caption": a.get("caption", "")} if a.get("title") else {}) | ({"cutout": True} if a.get("cutout") else {}) for a in m["assets"]]
    return (
        "You are the HOST LLM of a portfolio book. Read the skill " + str(skill) + " (sections 'Book plan', 'Editorial devices', 'Grid systems') and the craft rules " + str(craft) + ".\n"
        "Write ONE JSON file: " + str(target) + " - a book plan valid against " + str(P.BOOK_PLAN_SCHEMA) + ". Never write coordinates. Use ONLY facts from project.md below; "
        "every asset id exactly once (unless allow_repeat_assets is justified); captions name what each image shows; headings are claims, not labels; "
        "use bleed/dark/strip/photoset sparingly (1 page in 3-4 at most); drawings are never cropped or bled; cut-out photos (cutout: true) go on white pages, never bleed.\n"
        "You may Read image files under " + str(project_dir) + " to see them. Do not run anything. Finish by writing the file, then reply 'done'.\n\n"
        "ASSETS (ids, roles, aspects):\n" + json.dumps(assets, ensure_ascii=False) + "\n\nproject.md:\n" + brief_md + "\n\n"
        + ("EXTRA DIRECTION FROM THE PERSON:\n" + instructions + "\n\n" if instructions else "")
        + ("YOUR PREVIOUS PLAN WAS REJECTED: " + error + "\nFix it and write the file again.\n" if error else ""))


def generate_plan(project_dir: Path, runner, timeout_s: int, instructions: str, log) -> dict:
    m, brief = core_assets.ingest(project_dir)
    md = (project_dir / "project.md").read_text(encoding="utf-8")
    target = project_dir / "plans" / "_generated.json"
    target.parent.mkdir(exist_ok=True)
    err = ""
    for attempt in (1, 2):
        target.unlink(missing_ok=True)
        log(f"host LLM attempt {attempt}")
        code, text = runner(plan_prompt(project_dir, m, md, instructions, target, err), project_dir, timeout_s, "Read,Write")
        log(f"host LLM exit {code}: {text.strip()[-200:]}")
        if not target.is_file():
            err = "the file was not written"
            continue
        try:
            plan = json.loads(target.read_text(encoding="utf-8"))
            validate_plan(project_dir, plan)
        except (ValueError, ApiError) as e:
            err = getattr(e, "message", str(e))
            log(f"plan rejected: {err}")
            continue
        info = write_plan(project_dir, plan)
        target.unlink(missing_ok=True)
        return {"pages": info["pages"], "attempts": attempt}
    raise RuntimeError(f"the host LLM could not produce a valid book plan: {err}")


# ---- portfolioAgent: compose --------------------------------------------------------------------------------------
def build_spec(req):
    from portfolio_agent.engine.spec import default_spec
    style = {"paper_color": req.paper_color, "accent_color": req.accent_color, "text_color": req.text_color, "footer": req.footer,
             "header": False if req.header is False else None, "band": req.band}
    return default_spec(width_mm=req.width_mm, height_mm=req.height_mm, margin_mm=req.margin_mm, bleed_mm=req.bleed_mm, style={k: v for k, v in style.items() if v is not None})


def compose(project_dir: Path, req, log) -> dict:
    from portfolio_agent.engine import pipeline
    plan = project_dir / "book-plan.json"
    if not plan.is_file():
        raise RuntimeError("no book plan: PUT /projects/{id}/book-plan or POST /projects/{id}/book-plan/generate first")
    log("compose started")
    rep = pipeline.run_author(str(project_dir), str(project_dir / "out"), "planned", {"plan_path": str(plan)}, build_spec(req), req.domain, do_repair=True, label="B4_plan", also=tuple(req.also))
    return attempt_summary(rep)


def attempt_summary(rep: dict) -> dict:
    return {"attempt": rep.get("attempt"), "pages": rep.get("pages"), "gate_pass": rep.get("gate_pass"), "seconds": rep.get("seconds"),
            "blocking": [{"code": i["code"], "page": i.get("page"), "elements": i.get("elements"), "details": i.get("details")} for i in rep.get("blocking_issues", [])],
            "advisory": [{"code": i["code"], "page": i.get("page"), "elements": i.get("elements"), "details": i.get("details")} for i in rep.get("advisory_issues", [])]}


def attempt_detail(att: Path) -> dict:
    qa = json.loads((att / "qa.json").read_text(encoding="utf-8")) if (att / "qa.json").is_file() else {}
    pages = sorted(p.name for p in (att / "preview").glob("page-*.png")) if (att / "preview").is_dir() else []
    files = {n: (att / n).is_file() for n in ("book.pdf", "book.pptx", "plan.json", "qa.json", "episode.json", "review.json", "review-context.json")}
    return {"attempt": att.name, "gate_pass": qa.get("gate_pass"), "blocking": qa.get("blocking_issues", []), "advisory": qa.get("advisory_issues", []),
            "page_scores": qa.get("page_scores"), "pages": pages, "files": files, "reference_basis": qa.get("reference_basis")}


# ---- reviewAgent ------------------------------------------------------------------------------------------------
def review_context(project_dir: Path) -> dict:
    from portfolio_agent.engine import review
    try:
        return review.review_context(project_dir / "out")
    except review.ReviewError as e:
        raise unprocessable("review", str(e))


def record_review(project_dir: Path, body: dict) -> dict:
    from portfolio_agent.engine import review
    tmp = project_dir / "out" / "_review_in.json"
    tmp.write_text(json.dumps(body), encoding="utf-8")
    try:
        return review.record_review(project_dir / "out", tmp)
    except review.ReviewError as e:
        raise unprocessable("review", str(e))
    finally:
        tmp.unlink(missing_ok=True)


def finalize(project_dir: Path) -> dict:
    from portfolio_agent.engine import review
    try:
        return review.finalize(project_dir / "out")
    except review.ReviewError as e:
        raise unprocessable("review", str(e))


# ---- catalogue ----------------------------------------------------------------------------------------------------
def catalog() -> dict:
    from portfolio_agent.layout import modular, photoset
    return {
        "roles": ["cover", "split", "hero", "pair", "grid", "text", "closing"],
        "page_flags": {"bleed": ["full", "split", "top", "grid"], "dark": "boolean", "strip": "boolean", "photoset": "template id", "crop": ["cover"], "focus": "[fx, fy]", "index": "boolean"},
        "grid_systems": [{"id": g["id"], "columns": g.get("columns"), "description": g.get("description", "")} for g in modular.grid_systems().values()],
        "compositions": [{"id": c["id"], "images": c.get("images"), "tags": c.get("tags", [])} for c in modular.compositions().values()],
        "photosets": [{"id": t["id"], "images": t["k"], "tags": t.get("tags", [])} for t in photoset.templates().values()],
        "backends": sorted(p.parent.name for p in P.BACKENDS_DIR.glob("*/adapter.py")),
    }
