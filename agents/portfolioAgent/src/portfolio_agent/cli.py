"""Command line. Parses arguments and calls `engine` only (layering rule). Entry: `python scripts/portfolio.py <command>`.

run           rule-based author -> gates -> export
compose       host-authored BOOK PLAN (contracts/book-plan.schema.json) -> layout layer -> gates -> export  (LLM path, no coordinates)
check-scenes  host-authored scene JSON (B4) -> gates + bounded repair -> export
candidates    >= 3 blind rule-based candidates for an independent critic
edit          local text edit with preservation proof
backends      list discovered backends
grid          12-column grid + aspect-exact box sizes per asset (host authors)
catalogue     render one page's content under every grid system x slot composition, with guides (pick by eye)
prepare       trim scanned sheets to the drawing (originals kept byte-identical in sources/, crops recorded in derived.json)
cutout        remove the background of chosen photos (rembg; originals kept in sources/, recorded in derived.json) + before/after sheet
manifest      print assets (ids, role, aspect, size) + brief of a project, for host authors
review-context / record-review / finalize   fresh-review gate: bind frames -> independent reviewer -> promote to final/ (engine/review.py)
"""
import argparse
import json
import sys
from portfolio_agent.engine import pipeline, edit, registry
from portfolio_agent.engine.spec import default_spec, from_design_plan


def _style_from_args(a):
    st = json.loads(open(a.style_json, encoding="utf-8").read()) if getattr(a, "style_json", None) else {}
    if getattr(a, "design_md", None):
        from portfolio_agent.engine.spec import from_design_md
        st = {**from_design_md(a.design_md, getattr(a, "palette", None)), **st}
    if getattr(a, "band", None):
        side, color, width = (a.band.split(":") + ["#b44a2b", "6"])[:3]
        st["band"] = {"side": side, "color": color, "width_mm": float(width)}
    for k, v in (("footer", False if a.no_footer else None), ("header", False if getattr(a, "no_header", False) else None), ("footer_text", a.footer_text), ("font_body", a.font_body), ("font_title", a.font_title), ("body_pt", a.body_pt), ("title_scale", a.title_scale), ("text_color", a.text_color), ("paper_color", getattr(a, "paper_color", None)), ("accent_color", getattr(a, "accent_color", None))):
        if v is not None:
            st[k] = v
    return st


def _spec_from_args(a):
    dp = from_design_plan(json.loads(open(a.design_plan, encoding="utf-8").read())) if a.design_plan else {}
    kw = {k: v for k, v in dp.items() if k != "style"}
    kw.update({k: v for k, v in dict(width_mm=a.width_mm, height_mm=a.height_mm, margin_mm=a.margin_mm, bleed_mm=a.bleed_mm, page_count=a.pages).items() if v is not None})
    return default_spec(style={**dp.get("style", {}), **_style_from_args(a)}, **kw)


def _common(p):
    p.add_argument("--domain")
    for k in ("width-mm", "height-mm", "margin-mm", "bleed-mm"):
        p.add_argument("--" + k, type=float)
    p.add_argument("--pages", type=int)
    p.add_argument("--design-plan", help="design-plan.json from the DesignDirector")
    p.add_argument("--no-footer", action="store_true")
    p.add_argument("--footer-text")
    p.add_argument("--font-body")
    p.add_argument("--font-title")
    p.add_argument("--body-pt", type=float)
    p.add_argument("--title-scale", type=float)
    p.add_argument("--text-color")
    p.add_argument("--paper-color", help="page background, e.g. #ffffff (default white) or #f6f3ee")
    p.add_argument("--accent-color", help="section labels / rules, e.g. #b5461c")
    p.add_argument("--no-header", action="store_true")
    p.add_argument("--style-json", help="JSON file with the same keys as style")
    p.add_argument("--design-md", help="DESIGN.md (design.md format) or tokens.json from pptAgent/pascal: palette -> paper/text/accent")
    p.add_argument("--palette", help="palette name inside a tokens.json (e.g. neutral-accent, ink-dark, blueprint-mono)")
    p.add_argument("--band", help="background band 'left|top:#hex:width_mm' e.g. left:#b44a2b:6 (the cover spine B0 used)")
    p.add_argument("--also", action="append", default=[], help="extra exporter backend, e.g. designcraft")


def _summary(rep):
    print(json.dumps({k: rep[k] for k in ("condition", "author", "pattern", "pages", "gate_pass", "seconds", "attempt")}
                     | {"blocking": [i["code"] for i in rep["blocking_issues"]], "advisory": [i["code"] for i in rep["advisory_issues"]]}, ensure_ascii=False))
    return 0 if rep["gate_pass"] else 1


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="portfolio_agent")
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("project")
    r.add_argument("out")
    r.add_argument("--condition", default="B3_full", choices=list(pipeline.CONDITIONS))
    _common(r)
    cp = sp.add_parser("compose")
    cp.add_argument("project")
    cp.add_argument("plan")
    cp.add_argument("out")
    _common(cp)
    h = sp.add_parser("check-scenes")
    h.add_argument("project")
    h.add_argument("scenes_dir")
    h.add_argument("out")
    _common(h)
    c = sp.add_parser("candidates")
    c.add_argument("project")
    c.add_argument("out")
    c.add_argument("-n", type=int, default=3)
    c.add_argument("--design-plan")
    e = sp.add_parser("edit")
    e.add_argument("out")
    e.add_argument("page")
    e.add_argument("element")
    e.add_argument("text")
    rc = sp.add_parser("review-context")
    rc.add_argument("out")
    rr = sp.add_parser("record-review")
    rr.add_argument("out")
    rr.add_argument("review_json")
    fz = sp.add_parser("finalize")
    fz.add_argument("out")
    sp.add_parser("backends")
    gr = sp.add_parser("grid")
    gr.add_argument("project")
    gr.add_argument("--design-plan")
    gr.add_argument("--columns", type=int, default=12)
    for k in ("width-mm", "height-mm", "margin-mm", "gutter-mm"):
        gr.add_argument("--" + k, type=float)
    ct = sp.add_parser("catalogue")
    ct.add_argument("project")
    ct.add_argument("out")
    ct.add_argument("--systems", help="comma-separated grid system ids")
    ct.add_argument("--photosets", action="store_true", help="instead: every 2-6 photo-set template with the project's photos (photosets_guides.png)")
    ct.add_argument("--cover", action="store_true", help="with --photosets: cover (crop) the cells instead of fitting")
    _common(ct)
    pp = sp.add_parser("prepare")
    pp.add_argument("project")
    pp.add_argument("--approve", action="store_true", help="write the trimmed derivatives (originals kept in sources/); without it only the proposal + sheet are written")
    pp.add_argument("--sheet", help="png path for the crop-proposal contact sheet")
    pp.add_argument("--levels", action="store_true", help="also stretch the levels of the drawings (paper -> white, ink darker); recorded in derived.json, originals kept")
    pp.add_argument("--knockout", action="store_true", help="also make the drawings' paper transparent (RGBA) so they sit on a coloured page; recorded in derived.json")
    pp.add_argument("--knockout-files", help="comma-separated extra files (relative to the project) to knock out, e.g. diagrams/overlay_plan.png")
    co = sp.add_parser("cutout")
    co.add_argument("project")
    co.add_argument("--files", required=True, help="comma-separated file names under images/ chosen by the host (never all photos blindly)")
    co.add_argument("--engine", default="rembg", choices=["rembg", "photocraft"])
    co.add_argument("--sheet", help="png path for the before/after sheet")
    m = sp.add_parser("manifest")
    m.add_argument("project")
    a = ap.parse_args(argv)
    if a.cmd in ("review-context", "record-review", "finalize"):
        from portfolio_agent.engine import review
        try:
            res = review.review_context(a.out) if a.cmd == "review-context" else review.record_review(a.out, a.review_json) if a.cmd == "record-review" else review.finalize(a.out)
        except review.ReviewError as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            return 1
        print(json.dumps({"ok": True, **res}, ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "backends":
        print(json.dumps({"backends": registry.list_backends()}))
        return 0
    if a.cmd == "manifest":
        from portfolio_agent.engine import ingest_view
        print(json.dumps(ingest_view.view(a.project), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "prepare":
        from portfolio_agent.engine import prepare
        rec = prepare.prepare(a.project, approve=a.approve)
        sheet = prepare.proposal_sheet(a.project, a.sheet) if a.sheet else None
        lv = ko = None
        if a.levels:
            from portfolio_agent.engine import levels
            lv = [d["file"] for d in levels.levels(a.project)]
        if a.knockout or a.knockout_files:
            from portfolio_agent.engine import levels
            ko = [d["file"] for d in levels.knockout(a.project, kinds=("drawings",) if a.knockout else (), files=[f.strip() for f in (a.knockout_files or "").split(",") if f.strip()])]
        print(json.dumps({"proposals": len(rec["proposals"]), "approved": rec["approved"], "derived": len(rec["derived"]), "sheet": sheet, "levels": lv, "knockout": ko}, ensure_ascii=False))
        return 0
    if a.cmd == "cutout":
        from portfolio_agent.engine import cutout
        done = cutout.cutout(a.project, [f.strip() for f in a.files.split(",") if f.strip()], engine=a.engine)
        sheet = cutout.cutout_sheet(a.project, a.sheet) if a.sheet else None
        print(json.dumps({"cutouts": [{"file": d["file"], "opaque_fraction": d["opaque_fraction"], "engine": d["engine"]} for d in done], "sheet": sheet}, ensure_ascii=False))
        return 0
    if a.cmd == "catalogue":
        from portfolio_agent.engine import catalogue
        if a.photosets:
            res = catalogue.build_photosets(a.project, a.out, _spec_from_args(a), crop="cover" if a.cover else None)
        else:
            res = catalogue.build(a.project, a.out, _spec_from_args(a), systems=a.systems.split(",") if a.systems else None)
        print(json.dumps({k: res[k] for k in ("pages", "sheet", "pdf", "blocking_total")}, ensure_ascii=False))
        return 0
    if a.cmd == "grid":
        from portfolio_agent.engine import grid
        dp = from_design_plan(json.loads(open(a.design_plan, encoding="utf-8").read())) if a.design_plan else {}
        kw = {k: v for k, v in dp.items() if k != "style"}
        kw.update({k: v for k, v in dict(width_mm=a.width_mm, height_mm=a.height_mm, margin_mm=a.margin_mm, gutter_mm=a.gutter_mm).items() if v is not None})
        print(json.dumps(grid.view(a.project, default_spec(**kw), a.columns), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "run":
        return _summary(pipeline.run(a.project, a.out, a.condition, _spec_from_args(a), a.domain, also=a.also))
    if a.cmd == "compose":
        return _summary(pipeline.run_author(a.project, a.out, "planned", {"plan_path": a.plan}, _spec_from_args(a), a.domain, do_repair=True, label="B4_plan", also=a.also))
    if a.cmd == "check-scenes":
        return _summary(pipeline.run_host(a.project, a.scenes_dir, a.out, _spec_from_args(a), a.domain, also=a.also))
    if a.cmd == "candidates":
        from portfolio_agent.engine import candidates
        base = from_design_plan(json.loads(open(a.design_plan, encoding="utf-8").read())) if a.design_plan else None
        print(json.dumps(candidates.run(a.project, a.out, base, a.n), ensure_ascii=False, indent=1))
        return 0
    res = edit.edit_text(a.out, a.page, a.element, a.text)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
