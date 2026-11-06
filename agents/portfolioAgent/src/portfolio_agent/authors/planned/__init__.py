"""Planned Author (LLM path, B4'): the host writes a Book Plan (contracts/book-plan.schema.json) - sequence, roles, asset
assignment, words, variants, tokens - and this author turns it into scenes with the deterministic `layout` layer.

The host never writes coordinates. Hard rules enforced here (not in the host): every asset id must exist and be used at least once;
role/asset-count compatibility; CJK-safe fonts via the type system. Everything after (gates, repair, export, edit proof) is the engine's.
"""
import json
from pathlib import Path

import jsonschema

from portfolio_agent import layout
from portfolio_agent.layout import modular
from portfolio_agent.core.contracts import Plan, Scene
from portfolio_agent.core.paths import BOOK_PLAN_SCHEMA
from portfolio_agent.layout.typesystem import TypeSystem

SCHEMA = BOOK_PLAN_SCHEMA
ROLE_ASSETS = {"cover": (0, 1), "split": (1, 1), "hero": (1, 1), "pair": (2, 2), "grid": (2, 6), "text": (0, 0), "closing": (0, 0)}


class BookPlanError(ValueError):
    pass


def load_plan(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        jsonschema.validate(plan, json.loads(SCHEMA.read_text(encoding="utf-8")))
    except jsonschema.ValidationError as e:
        raise BookPlanError(f"book plan schema violation: {e.message[:200]}") from e
    return plan


def check(plan, manifest):
    ids = {a["id"] for a in manifest["assets"]}
    used = [aid for pg in plan["pages"] for aid in pg["assets"]]
    unknown = sorted(set(used) - ids)
    if unknown:
        raise BookPlanError(f"unknown asset ids {unknown}; known: {sorted(ids)}")
    repeat_ok = plan.get("allow_repeat_assets") or any(pg.get("role") == "grid" and pg.get("index") for pg in plan["pages"])
    dup = sorted({a for a in used if used.count(a) > 1})
    if dup and not repeat_ok:
        raise BookPlanError(f"assets used more than once {dup}: repeating an asset reads as padding; set allow_repeat_assets: true only with a reason")
    missing = sorted(ids - set(used))
    if missing:
        raise BookPlanError(f"assets never placed {missing}: every asset must appear at least once (or remove it from the project)")
    for i, pg in enumerate(plan["pages"], 1):
        lo, hi = ROLE_ASSETS[pg["role"]]
        if pg.get("strip"):
            hi = 10   # a process strip takes up to ten thumbnails (layout/bleed.py strip)
        if pg.get("bleed") == "grid":
            lo, hi = 2, 4
        if not lo <= len(pg["assets"]) <= hi:
            raise BookPlanError(f"page {i}: role {pg['role']!r} takes {lo}-{hi} assets, got {len(pg['assets'])}")


class PlannedAuthor:
    name = "planned"
    can_relayout = True

    def propose(self, brief, manifest, spec, measurer, options) -> tuple[Plan, list[Scene]]:
        bp = load_plan(options["plan_path"])
        check(bp, manifest)
        pages = []
        sec_no = 0
        for i, pg in enumerate(bp["pages"], 1):
            p = {"role": "grid" if pg["role"] == "pair" else pg["role"], "assets": list(pg["assets"]), "page": i, "_index": bool(pg.get("index")),
                 "title": pg.get("title") or pg.get("section") or bp["doc_title"], "section": pg.get("section", ""),
                 "text": pg.get("text", ""), "caption": pg.get("caption", ""), "captions": pg.get("captions", []),
                 "statement": pg.get("statement", ""), "tagline": pg.get("tagline", ""), "keywords": bp.get("keywords", brief.get("keywords", [])),
                 **{k: pg[k] for k in ("bleed", "dark", "strip", "photoset", "crop", "focus") if k in pg}}   # editorial devices (layout/bleed.py); the host decides, never coordinates
            if p["role"] not in ("cover",):
                sec_no += 1
                p["section_no"] = sec_no
            pages.append(p)
        plan = {"doc_title": bp["doc_title"], "pattern_id": "host-plan", "tokens": bp.get("tokens", {}), "pages": pages,
                "hero_min_ratio": bp.get("hero_min_ratio", 0.35), "asset_count": len(manifest["assets"])}
        if bp.get("band") and not (spec.get("style") or {}).get("band"):
            spec.setdefault("style", {})["band"] = bp["band"]
        ts = TypeSystem(spec, plan["tokens"], measurer, bp["doc_title"])
        force = {i: pg["variant"] for i, pg in enumerate(bp["pages"], 1) if "variant" in pg}
        scenes = layout.build_book(manifest["project_id"], plan, manifest, spec, alternate=True, force=force, ts=ts)
        # pages that name a composition (and the book's grid system) are re-rendered through the modular layer
        system = modular.grid_systems().get(bp.get("grid_system", "swiss-12"))
        comps = modular.compositions()
        A = {a["id"]: a for a in manifest["assets"]}
        for i, (pg_in, pg) in enumerate(zip(bp["pages"], plan["pages"])):
            cid = pg_in.get("composition")
            if cid:
                if cid not in comps:
                    raise BookPlanError(f"page {i + 1}: unknown composition {cid!r}; known: {sorted(comps)}")
                pg["total"] = len(plan["pages"]); pg["doc_title"] = bp["doc_title"]
                scenes[i]["elements"] = modular.render(pg, A, spec, system, comps[cid], ts, pg_in.get("variant", 0))
        plan["meta"] = {"author": self.name, "pattern": "host-plan", "retrieval": "n/a (host decided)", "notes": [f"plan={options['plan_path']}"],
                        "style_defaults": {"paper_color": ts.paper, **({"band": bp["band"]} if bp.get("band") else {})}}
        return plan, scenes

    def relayout(self, page_plan, scene_before, manifest, spec, weight_mult):
        A = {a["id"]: a for a in manifest["assets"]}
        pg = {**page_plan, "weight_mult": weight_mult}
        return layout.build_scene(scene_before["project_id"], pg, A, spec, pg.get("variant", 0), None, pg.get("total"))


AUTHOR = PlannedAuthor()
