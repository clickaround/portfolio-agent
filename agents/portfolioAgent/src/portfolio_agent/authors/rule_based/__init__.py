"""Rule-based Author: pattern retrieval -> page plan -> guillotine layout (+ optional content-preserving pagination and hero search).

Candidate D / fallback author (ADR-0007). Options (all booleans, ablation switches used by the benchmarks):
    cases  : retrieve a layout pattern from knowledge/patterns (off = naive all-grid plan)
    review : paginate overflowing text to new pages and search layout variants to reach the hero-size floor
"""
from portfolio_agent.core.model.contracts import Plan, Scene
from portfolio_agent.authors import knowledge
from portfolio_agent.layout import search
from portfolio_agent import layout
from portfolio_agent.layout.typesystem import TypeSystem
from . import plan as planmod


def _paginate_text(plan, manifest, spec, project_id, measurer):
    """Content-preserving: if a body overflows its box at minimum font, push the remainder to a following text page."""
    A = {a["id"]: a for a in manifest["assets"]}
    i, changed = 0, False
    while i < len(plan["pages"]):
        pg = plan["pages"][i]
        if pg["role"] in ("split", "text", "closing") and pg.get("text"):
            sc = layout.build_scene(project_id, pg, A, spec, pg.get("variant", 0))
            body = next(e for e in sc["elements"] if e["id"].startswith("body"))
            minfs = 8 * min(spec["width_mm"], spec["height_mm"]) / 210.0
            _, _, w, h = body["box_mm"]
            if not measurer.text_fits(pg["text"], w, h, minfs):
                words = pg["text"].split()
                lo, hi = 1, len(words)
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if measurer.text_fits(" ".join(words[:mid]), w, h, minfs):
                        lo = mid
                    else:
                        hi = mid - 1
                pg["text"], rest = " ".join(words[:lo]), " ".join(words[lo:])
                plan["pages"].insert(i + 1, {"role": "text", "assets": [], "page": i + 2, "title": pg["title"] + " (cont.)", "text": rest, "caption": "", "variant": 0,
                                             "section": pg.get("section", ""), "section_no": pg.get("section_no", 0), "keywords": pg.get("keywords", [])})
                changed = True
        i += 1
    for n, pg in enumerate(plan["pages"]):
        pg["page"] = n + 1
    return changed


def _hero_ratio(scenes, spec):
    ca = (spec["width_mm"] - 2 * spec["margin_mm"]) * (spec["height_mm"] - 2 * spec["margin_mm"])
    return max((e["box_mm"][2] * e["box_mm"][3] / ca for s in scenes for e in s["elements"] if e["kind"] != "text"), default=0)


class RuleBasedAuthor:
    name = "rule_based"
    can_relayout = True

    def propose(self, brief, manifest, spec, measurer, options) -> tuple[Plan, list[Scene]]:
        cases, review = options.get("cases", True), options.get("review", True)
        pid = manifest["project_id"]
        retrieved = knowledge.retrieve(brief, manifest)[0] if cases else {"pattern": knowledge.baseline_pattern(), "score": 0, "rationale": "retrieval disabled"}
        plan = planmod.make_plan(brief, manifest, retrieved["pattern"], spec.get("page_count"))
        for pg in plan["pages"]:
            pg["variant"] = 0
        ts = TypeSystem(spec, plan.get("tokens", {}), measurer, brief["title"])
        scenes = layout.build_book(pid, plan, manifest, spec, alternate=cases or review, ts=ts)
        notes = []
        if review:
            if _paginate_text(plan, manifest, spec, pid, measurer):
                for pg in plan["pages"]:
                    pg.setdefault("variant", 0)
                scenes = layout.build_book(pid, plan, manifest, spec, alternate=True, ts=ts)
            if _hero_ratio(scenes, spec) < plan["hero_min_ratio"]:
                best, forced = _hero_ratio(scenes, spec), {}
                for pg in plan["pages"]:
                    if not pg["assets"]:
                        continue
                    flip = {**forced, pg["page"]: 1 - pg.get("variant", 0)}
                    trial = layout.build_book(pid, plan, manifest, spec, True, flip, ts=ts)
                    if _hero_ratio(trial, spec) > best:
                        best, forced, scenes = _hero_ratio(trial, spec), flip, trial
                    if best >= plan["hero_min_ratio"]:
                        break
                notes.append(f"layout variant search forced={forced} hero={best:.2f}")
        searched = None
        if options.get("search"):
            scenes, searched = search.search_book(pid, plan, manifest, spec, measurer, ts, scenes)
            notes.append(f"layout search: {sum(len(r['candidates']) for r in searched)} candidates over {len(searched)} pages")
        notes.append(f"type: display={ts.heading_font or 'body-bold'} italic={ts.italic_font} body={ts.body_font or 'default'} body_pt={ts.body_pt} paper={ts.paper} accent={ts.accent}")
        plan["meta"] = {"author": self.name, "pattern": retrieved["pattern"]["id"], "retrieval": retrieved["rationale"], "notes": notes,
                        **({"search": searched} if searched else {}), "style_defaults": {"paper_color": ts.paper}}  # author-chosen defaults; user spec.style always wins (merged by the engine)
        return plan, scenes

    def relayout(self, page_plan, scene_before, manifest, spec, weight_mult):
        A = {a["id"]: a for a in manifest["assets"]}
        pg = {**page_plan, "weight_mult": weight_mult}
        return layout.build_scene(scene_before["project_id"], pg, A, spec, pg.get("variant", 0), None, pg.get("total"))


AUTHOR = RuleBasedAuthor()
