"""Composition catalogue: render ONE page's content under every suitable composition x chosen grid systems, gate each,
and write a guides contact sheet so a person (or a host) can pick by eye. Also the data source for `compose` with
page.composition / plan.grid_system."""
import json
from pathlib import Path

from portfolio_agent.core.sources import assets
from portfolio_agent.core.guardrails import gates
from portfolio_agent.layout import modular
from portfolio_agent.layout.typesystem import TypeSystem
from . import registry
from .guides import overlay_sheet


def build_photosets(project_dir, out_dir, spec, domain_tokens=None, crop=None):
    """Every photo-set template (knowledge/patterns/photosets.json) rendered with this project's own photographs (first k), gated,
    on one guides sheet - so the host (or the person) picks a 2-6 photo arrangement by eye. `crop="cover"` shows the covered variant."""
    from portfolio_agent.layout import book, photoset
    domain_tokens = domain_tokens or {"paper": "#ffffff", "ink": "#1c1c1c", "accent": "#b5461c", "display": "serif"}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    be = registry.get_backend("local")
    manifest, brief = assets.ingest(project_dir)
    A = {a["id"]: a for a in manifest["assets"]}
    photos = [a["id"] for a in manifest["assets"] if a["role"] == "photo"]
    ts = TypeSystem(spec, domain_tokens, be, brief["title"])
    be.configure({**{"paper_color": ts.paper}, **(spec.get("style") or {})})
    scenes, rows = [], []
    for tid, t in photoset.templates().items():
        k = t["k"]
        if k > len(photos):
            continue
        for variant in (0, 1):
            pg = {"role": "grid", "assets": photos[:k], "title": f"{k} photographs", "captions": [f"View {i + 1:02d}" for i in range(k)], "section": "Studies", "section_no": 1,
                  "photoset": tid, "keywords": brief.get("keywords", []), "doc_title": brief["title"], "page": 1, "total": 1, **({"crop": crop} if crop else {})}
            sc = book.build_scene(manifest["project_id"], pg, A, spec, variant, ts, 1)
            sc["page_id"] = f"{tid}__v{variant}" + ("__cover" if crop else "")
            issues = gates.qa_scene(sc, manifest, spec, be)
            blocking = [i for i in issues if i["code"] in gates.BLOCKING]
            rows.append({"template": tid, "variant": variant, "k": k, "blocking": [i["code"] for i in blocking], "composition": pg.get("_composition")})
            scenes.append(sc)
    (out / "scenes").mkdir(exist_ok=True)
    for sc in scenes:
        (out / "scenes" / f"{sc['page_id']}.json").write_text(json.dumps(sc, indent=1), encoding="utf-8")
    ex = be.export(scenes, manifest, project_dir, out / "photosets", spec, ["pdf"])
    (out / "run.json").write_text(json.dumps({"spec": spec}, indent=1), encoding="utf-8")
    (out / "photosets.json").write_text(json.dumps({"rows": rows}, indent=1), encoding="utf-8")
    fr = {"left": spec["margin_mm"], "right": spec["width_mm"] - spec["margin_mm"], "top": spec["margin_mm"], "bottom": spec["height_mm"] - spec["margin_mm"],
          "grid": __import__("portfolio_agent.core.geometry", fromlist=["columns"]).columns(spec, book.GRID_COLUMNS), "rows": 6}
    sheet = overlay_sheet(str(out / "photosets.pdf"), scenes, spec, str(out / "photosets_guides.png"), dpi=55, cols=4, frames=[fr] * len(scenes), labels=[sc["page_id"].replace("__", "  ·  ") for sc in scenes])
    return {"pages": len(scenes), "sheet": sheet, "rows": rows, "pdf": ex["files"].get("pdf"), "blocking_total": sum(len(r["blocking"]) for r in rows)}


def build(project_dir, out_dir, spec, page_index=1, systems=None, domain_tokens=None):
    """domain_tokens default: the architecture pattern tokens (serif display, warm paper) so the catalogue shows the editorial voice."""
    domain_tokens = domain_tokens or {"paper": "#ffffff", "ink": "#1c1c1c", "accent": "#b5461c", "display": "serif"}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    be = registry.get_backend("local")
    manifest, brief = assets.ingest(project_dir)
    A = {a["id"]: a for a in manifest["assets"]}
    # one representative page: the lead photo + first long section, or two assets for pair compositions
    photos = [a["id"] for a in manifest["assets"] if a["role"] == "photo"]
    draws = [a["id"] for a in manifest["assets"] if a["role"] == "drawing"]
    secs = list(brief["sections"].items())
    pages = {
        "one": {"role": "split", "assets": photos[:1], "title": secs[0][0] if secs else brief["title"], "text": secs[0][1] if secs else "", "caption": secs[1][1] if len(secs) > 1 else "", "section": secs[0][0] if secs else "", "section_no": 1},
        "drawing": {"role": "hero", "assets": draws[:1] or photos[1:2], "title": "Plan", "caption": secs[1][1] if len(secs) > 1 else "", "section": "Plan", "section_no": 2},
        "two": {"role": "grid", "assets": photos[1:3] if len(photos) >= 3 else photos[:2], "title": "Studies", "captions": ["View 01", "View 02"], "section": "Studies", "section_no": 3},
        "cover": {"role": "cover", "assets": photos[:1], "title": brief["title"], "tagline": "Architecture portfolio", "section": ""},
        "closing": {"role": "closing", "assets": [], "title": brief["title"], "statement": secs[-1][1] if secs else brief["title"], "section": secs[-1][0] if secs else "", "section_no": 4},
    }
    for p in pages.values():
        p.update({"keywords": brief.get("keywords", []), "doc_title": brief["title"], "page": page_index, "total": 5})
    ts = TypeSystem(spec, domain_tokens or {}, be, brief["title"])
    be.configure({**{"paper_color": ts.paper}, **(spec.get("style") or {})})
    systems = [modular.grid_systems()[s] for s in (systems or ["swiss-12", "editorial-8", "book-6-ninths", "poster-4"])]
    scenes, rows = [], []
    for sysm in systems:
        for comp in modular.compositions().values():
            for key, pg in pages.items():
                if not modular.suitable(comp, pg, A, spec):
                    continue
                pg2 = dict(pg)
                els = modular.render(pg2, A, spec, sysm, comp, ts)
                sc = {"schema_version": "0.2.0", "project_id": manifest["project_id"], "page_id": f"{sysm['id']}__{comp['id']}__{key}", "size_mm": [spec["width_mm"], spec["height_mm"]], "elements": els}
                issues = gates.qa_scene(sc, manifest, {**spec, "margin_mm": min(modular.frame(sysm, spec)["left"], modular.frame(sysm, spec)["top"])}, be)
                blocking = [i for i in issues if i["code"] in gates.BLOCKING]
                rows.append({"grid": sysm["id"], "composition": comp["id"], "page": key, "blocking": [i["code"] for i in blocking], "elements": len(els)})
                scenes.append(sc)
                break  # one representative page per composition per grid
    (out / "scenes").mkdir(exist_ok=True)
    for sc in scenes:
        (out / "scenes" / f"{sc['page_id']}.json").write_text(json.dumps(sc, indent=1), encoding="utf-8")
    ex = be.export(scenes, manifest, project_dir, out / "catalogue", spec, ["pdf"])
    (out / "run.json").write_text(json.dumps({"spec": spec}, indent=1), encoding="utf-8")
    (out / "catalogue.json").write_text(json.dumps({"rows": rows, "systems": [s["id"] for s in systems]}, indent=1), encoding="utf-8")
    sheet = overlay_sheet(str(out / "catalogue.pdf"), scenes, spec, str(out / "catalogue_guides.png"), dpi=55, cols=4, frames=[modular.frame(modular.grid_systems()[sc["page_id"].split("__")[0]], spec) for sc in scenes],
                          labels=[sc["page_id"].replace("__", "  ·  ") for sc in scenes])
    return {"pages": len(scenes), "sheet": sheet, "rows": rows, "pdf": ex["files"].get("pdf"), "blocking_total": sum(len(r["blocking"]) for r in rows)}
