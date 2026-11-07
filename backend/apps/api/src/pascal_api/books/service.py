import json
from pathlib import Path

from ..exceptions import ApiError
from ..gateways import agents
from .schemas import ComposeRequest


def compose(d: Path, req: ComposeRequest, log) -> dict:
    plan = d / "book-plan.json"
    if not plan.is_file():
        raise RuntimeError("no book plan: PUT /projects/{id}/book-plan or POST /projects/{id}/book-plan/generate first")
    log("compose started")
    style = {"paper_color": req.paper_color, "accent_color": req.accent_color, "text_color": req.text_color, "footer": req.footer,
             "header": False if req.header is False else None, "band": req.band}
    return agents.compose(d, plan, {"width_mm": req.width_mm, "height_mm": req.height_mm, "margin_mm": req.margin_mm, "bleed_mm": req.bleed_mm, "style": style}, req.domain, req.also)


def attempt_info(att: Path) -> dict:
    qa = json.loads((att / "qa.json").read_text(encoding="utf-8")) if (att / "qa.json").is_file() else {}
    pages = sorted(p.name for p in (att / "preview").glob("page-*.png")) if (att / "preview").is_dir() else []
    files = {n: (att / n).is_file() for n in ("book.pdf", "book.pptx", "book.designcraft", "plan.json", "qa.json", "episode.json", "review.json", "review-context.json")}
    dc = qa.get("extra_exporters", {}).get("designcraft", {}) or {}
    designcraft = {"status": "unverified", "notes": dc.get("notes") or []} if files["book.designcraft"] else None
    pending = att / "ledger-pending.json"
    return {"attempt": att.name, "native_edit": isinstance(qa.get("native_edit"), dict), "ledger_pending": pending.exists() or pending.is_symlink(), "gate_pass": qa.get("gate_pass"), "blocking": qa.get("blocking_issues", []), "advisory": qa.get("advisory_issues", []),
            "page_scores": qa.get("page_scores"), "pages": pages, "files": files, "reference_basis": qa.get("reference_basis"), "designcraft": designcraft}


def scene(att: Path, page: int) -> dict:
    p = att / "scenes" / f"page-{page:02d}.json"
    if not p.is_file():
        raise ApiError(404, "not_found", f"scene {page} not found")
    return json.loads(p.read_text(encoding="utf-8"))
