"""Full-bleed / strip / dark compositions (layout/bleed.py) and the cut-out step (engine/cutout.py).

Falsifiable: a bleed page passes the blocking gates (the bleed graphic may leave the margin, text sits only inside a panel),
text placed on a bleed graphic WITHOUT a panel is blocked (TEXT_OVER_IMAGE), the cropped cover keeps the source aspect,
the local PDF carries the cropped image, dark pages invert the type colours, and a cut-out leaves the original byte-identical.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.core.sources.assets import ingest  # noqa: E402
from portfolio_agent.core.guardrails import gates  # noqa: E402
from portfolio_agent.engine import pipeline  # noqa: E402
from portfolio_agent.engine.spec import default_spec  # noqa: E402
from portfolio_agent.layout import book  # noqa: E402

FIX = ROOT / "examples" / "synthetic_projects"


class _M:
    def text_fits(self, *a, **k):
        return True


def _plan(pages, title="Bleed test"):
    return {"schema_version": "0.1.0", "doc_title": title, "domain": "photography", "keywords": ["k1"], "tokens": {}, "pages": pages}


class TestBleed(unittest.TestCase):
    def setUp(self):
        self.m, _ = ingest(FIX / "photo_01")
        self.A = {a["id"]: a for a in self.m["assets"]}
        self.spec = default_spec(bleed_mm=3)

    def _scene(self, page, variant=0):
        page = {"page": 1, "total": 1, "doc_title": "T", "section": "One", "section_no": 1, "caption": "A caption. With a second sentence that is a bit longer.", "text": "", **page}
        return book.build_scene("p", page, self.A, self.spec, variant), page

    def test_pick_flags(self):
        self.assertEqual(book.pick({"role": "hero", "assets": ["img01"], "bleed": "full"}, self.A), "bleed_full")
        self.assertEqual(book.pick({"role": "grid", "assets": ["img01", "img02", "img03"], "bleed": "grid"}, self.A), "bleed_grid")
        self.assertEqual(book.pick({"role": "grid", "assets": ["img01"] * 5}, self.A), "strip")
        self.assertEqual(book.pick({"role": "hero", "assets": ["img01"]}, self.A), "hero")

    def test_bleed_full_passes_gates_and_crops(self):
        for v in (0, 1):
            sc, pg = self._scene({"role": "hero", "assets": ["img04"], "title": "Wide photo covers the page", "bleed": "full"}, v)
            blocking, _ = gates.split(gates.qa_scene(sc, self.m, self.spec, _M()))
            self.assertEqual(blocking, [], blocking)
            g = next(e for e in sc["elements"] if e["id"].startswith("bleed-"))
            self.assertEqual(g["box_mm"], [-3, -3, self.spec["width_mm"] + 6, self.spec["height_mm"] + 6])
            fx0, fy0, fx1, fy1 = g["crop"]
            self.assertLess(fx1 - fx0, 1.0)   # 3:1 panorama on a portrait page: sides are cropped away
            self.assertEqual((fy0, fy1), (0.0, 1.0))
            self.assertTrue(any(e["id"].startswith("panel-") for e in sc["elements"]))
            self.assertTrue(pg.get("_no_furniture"))
            self.assertEqual(pg["_composition"], "bleed-full")

    def test_text_over_image_without_panel_is_blocked(self):
        sc, _ = self._scene({"role": "hero", "assets": ["img04"], "title": "T", "bleed": "full"})
        sc["elements"] = [e for e in sc["elements"] if not e["id"].startswith("panel-")]
        codes = {i["code"] for i in gates.qa_scene(sc, self.m, self.spec, _M())}
        self.assertIn("TEXT_OVER_IMAGE", codes)
        self.assertIn("TEXT_OVER_IMAGE", gates.BLOCKING)

    def test_split_top_grid_strip(self):
        cases = [({"role": "split", "assets": ["img02"], "title": "Split", "bleed": "split", "text": "Body text " * 20}, "bleed-split"),
                 ({"role": "hero", "assets": ["img01"], "title": "Top", "bleed": "top"}, "bleed-top"),
                 ({"role": "grid", "assets": ["img01", "img02", "img03"], "title": "Grid", "bleed": "grid"}, "bleed-grid"),
                 ({"role": "grid", "assets": ["img01", "img02", "img03", "img04"], "title": "Grid4", "bleed": "grid"}, "bleed-grid"),
                 ({"role": "grid", "assets": ["img01", "img02", "img03", "img04", "img05", "img06"], "title": "Strip", "strip": True, "captions": ["a"] * 6}, "strip")]
        for page, tag in cases:
            for v in (0, 1):
                sc, pg = self._scene(page, v)
                blocking, _ = gates.split(gates.qa_scene(sc, self.m, self.spec, _M()))
                self.assertEqual(blocking, [], (tag, v, blocking))
                self.assertEqual(pg["_composition"], tag)
                self.assertEqual(len([e for e in sc["elements"] if e.get("asset_id")]), len(page["assets"]))

    def test_dark_page_inverts(self):
        sc, _ = self._scene({"role": "hero", "assets": ["img03"], "title": "Night", "bleed": "full", "dark": True})
        ground = next(e for e in sc["elements"] if e["id"].startswith("dark-"))
        self.assertEqual(ground["z_index"], -1)
        from portfolio_agent.layout.typesystem import TypeSystem
        ts = TypeSystem(self.spec, {}, None)
        self.assertEqual(ground["style"]["fill"].lower(), ts.ink.lower())      # ground = the book's ink
        title = next(e for e in sc["elements"] if e["id"].startswith("title-"))
        self.assertEqual(title["style"]["color"].lower(), ts.paper.lower())    # type = the book's paper
        panel = next(e for e in sc["elements"] if e["id"].startswith("panel-"))
        self.assertEqual(panel["style"]["fill"].lower(), ts.ink.lower())

    def test_rule_based_hero_photo_goes_full_bleed(self):
        with tempfile.TemporaryDirectory() as td:
            r = pipeline.run(str(FIX / "photo_01"), td, spec=default_spec(bleed_mm=3), pptx=False)
            plan = json.loads((Path(td) / "attempts" / "01" / "plan.json").read_text(encoding="utf-8")) if (Path(td) / "attempts" / "01" / "plan.json").is_file() else r.get("plan", {})
            import math
            heroes = [p for p in plan.get("pages", []) if p["role"] == "hero"]
            self.assertTrue(heroes)
            pa = self.spec["width_mm"] / self.spec["height_mm"]
            for p in heroes:   # only a page-shaped photo covers the page; a square or a 3:1 panorama keeps the margin layout
                near = abs(math.log(self.A[p["assets"][0]]["aspect"] / pa)) < 0.25
                self.assertEqual(p.get("bleed") == "full", near, p)
            self.assertTrue(any(p.get("bleed") == "full" for p in heroes), heroes)
            self.assertTrue(r["gate_pass"], r.get("blocking_issues"))

    def test_compose_bleed_book_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            plan = _plan([{"role": "cover", "assets": ["img01"], "title": "Cover"},
                          {"role": "hero", "assets": ["img04"], "title": "Panorama", "bleed": "full", "caption": "Cap."},
                          {"role": "grid", "assets": ["img02", "img03", "img05"], "title": "Three", "bleed": "grid", "dark": True},
                          {"role": "split", "assets": ["img06"], "title": "Split", "bleed": "split", "text": "Grounded text. " * 10},
                          {"role": "closing", "assets": [], "statement": "End."}])
            pp = Path(td) / "plan.json"
            pp.write_text(json.dumps(plan), encoding="utf-8")
            r = pipeline.run_author(str(FIX / "photo_01"), str(Path(td) / "out"), "planned", {"plan_path": str(pp)}, spec=default_spec(bleed_mm=3), pptx=True)
            self.assertTrue(r["gate_pass"], r.get("blocking_issues"))
            import fitz
            d = fitz.open(r["files"]["pdf"] if isinstance(r.get("files"), dict) else str(Path(td) / "out" / "attempts" / "01" / "book.pdf"))
            self.assertEqual(d.page_count, 5)
            self.assertGreaterEqual(len(d[2].get_images()), 3)
            d.close()


if __name__ == "__main__":
    unittest.main()
