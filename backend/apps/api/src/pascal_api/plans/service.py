"""The book plan: editorial decisions and flags (never coordinates). Stored as book-plan.json with every earlier version kept under plans/."""
import json
import shutil
import time
import uuid
from pathlib import Path

from ..exceptions import ApiError
from ..gateways import agents


def read(d: Path) -> dict:
    p = d / "book-plan.json"
    if not p.is_file():
        raise ApiError(404, "no_plan", "this project has no book plan yet")
    return json.loads(p.read_text(encoding="utf-8"))


def write(d: Path, plan: dict) -> dict:
    agents.validate_plan(d, plan)
    (d / "plans").mkdir(exist_ok=True)
    cur = d / "book-plan.json"
    if cur.is_file():
        shutil.copy2(cur, d / "plans" / f"book-plan-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex}.json")
    cur.write_text(json.dumps(plan, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"pages": len(plan["pages"]), "versions": len(list((d / "plans").glob("book-plan-*.json")))}


def prompt(d: Path, manifest: dict, brief_md: str, instructions: str, target: Path, error: str = "") -> str:
    r = agents.plan_resources()
    assets = []
    for a in manifest["assets"]:
        row = {k: a[k] for k in ("id", "role", "kind", "aspect", "width", "height") if k in a}
        if a.get("title"):
            row |= {"title": a["title"], "caption": a.get("caption", "")}
        if a.get("cutout"):
            row["cutout"] = True
        assets.append(row)
    return (
        "You are the HOST LLM of a portfolio book. Read the skill " + str(r["skill"]) + " (sections 'Book plan', 'Editorial devices', 'Grid systems') and the craft rules " + str(r["craft"]) + ".\n"
        "Write ONE JSON file: " + str(target) + " - a book plan valid against " + str(r["schema"]) + ". Never write coordinates. Use ONLY facts from project.md below; "
        "every asset id exactly once (unless allow_repeat_assets is justified); captions name what each image shows; headings are claims, not labels; "
        "use bleed/dark/strip/photoset sparingly (1 page in 3-4 at most); drawings are never cropped or bled; cut-out photos (cutout: true) go on white pages, never bleed.\n"
        "You may Read image files under " + str(d) + " to see them. Do not run anything. Finish by writing the file, then reply 'done'.\n\n"
        "ASSETS (ids, roles, aspects):\n" + json.dumps(assets, ensure_ascii=False) + "\n\nproject.md:\n" + brief_md + "\n\n"
        + ("EXTRA DIRECTION FROM THE PERSON:\n" + instructions + "\n\n" if instructions else "")
        + ("YOUR PREVIOUS PLAN WAS REJECTED: " + error + "\nFix it and write the file again.\n" if error else ""))


def generate(d: Path, runner, timeout_s: int, instructions: str, log) -> dict:
    """The host LLM (Claude Code CLI on the subscription) writes the plan; a rejected plan goes back once with the author's own message."""
    manifest, _ = agents.ingest(d)
    brief_md = (d / "project.md").read_text(encoding="utf-8")
    target = d / "plans" / "_generated.json"
    target.parent.mkdir(exist_ok=True)
    err = ""
    for attempt in (1, 2):
        target.unlink(missing_ok=True)
        log(f"host LLM attempt {attempt}")
        code, text = runner(prompt(d, manifest, brief_md, instructions, target, err), d, timeout_s, "Read,Write")
        log(f"host LLM exit {code}: {text.strip()[-200:]}")
        if not target.is_file():
            err = "the file was not written"
            continue
        try:
            plan = json.loads(target.read_text(encoding="utf-8"))
            info = write(d, plan)
        except (ValueError, ApiError) as e:
            err = getattr(e, "message", str(e))
            log(f"plan rejected: {err}")
            continue
        target.unlink(missing_ok=True)
        return {"pages": info["pages"], "attempts": attempt}
    raise RuntimeError(f"the host LLM could not produce a valid book plan: {err}")
