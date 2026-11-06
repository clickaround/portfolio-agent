"""Host-authored Author (B4): the host agent (Claude Code / Codex) writes page specs as SceneDocument JSON (mm) from the brief, the asset
manifest and its own design plan. This author only LOADS and structurally validates them; geometry/provenance gates, repair, export and
critique happen in the engine exactly as for any other author.

options: {"scenes_dir": path to page-*.json}
"""
import json
from pathlib import Path
import jsonschema
from portfolio_agent.core.workspace import SCENE_SCHEMA

HERO_FLOOR = 0.35  # same floor as the rule-based author so conditions are comparable


class HostScenesError(ValueError):
    pass


class HostAuthor:
    name = "host"
    can_relayout = False

    def propose(self, brief, manifest, spec, measurer, options):
        d = Path(options["scenes_dir"])
        files = sorted(d.glob("page-*.json"))
        if not files:
            raise HostScenesError(f"no page-*.json in {d}")
        schema = json.loads(SCENE_SCHEMA.read_text(encoding="utf-8"))
        scenes, pages = [], []
        for i, f in enumerate(files, 1):
            sc = json.loads(f.read_text(encoding="utf-8"))
            try:
                jsonschema.validate(sc, schema)
            except jsonschema.ValidationError as e:
                raise HostScenesError(f"{f.name}: schema violation: {e.message[:160]}") from e
            if sc["size_mm"] != [spec["width_mm"], spec["height_mm"]]:
                raise HostScenesError(f"{f.name}: size_mm {sc['size_mm']} != spec {[spec['width_mm'], spec['height_mm']]}")
            sc["project_id"] = manifest["project_id"]
            scenes.append(sc)
            pages.append({"page": i, "role": "host", "assets": [e["asset_id"] for e in sc["elements"] if e.get("asset_id")], "title": "", "text": "", "caption": "", "variant": 0})
        plan = {"doc_title": brief["title"], "pages": pages, "hero_min_ratio": HERO_FLOOR, "meta": {"author": self.name, "pattern": "host-authored", "retrieval": "n/a", "notes": []}}
        return plan, scenes

    def relayout(self, page_plan, scene_before, manifest, spec, weight_mult):
        raise NotImplementedError("host-authored pages cannot be re-laid-out by the engine; ask the host to revise the page spec")


AUTHOR = HostAuthor()
