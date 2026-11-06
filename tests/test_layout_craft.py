"""Layout craft invariants (knowledge/editorial/layout-craft.md). These are falsifiable geometry checks on real engine output:
graphics snap to the column grid, text columns respect the measure, furniture is switchable, credits never become headings,
pair rows align their tops, CJK titles never get a Latin-only serif."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runtime"))
from portfolio_agent.engine import pipeline  # noqa: E402
from portfolio_agent.engine.spec import default_spec  # noqa: E402
from portfolio_agent.core.geometry import columns  # noqa: E402
from portfolio_agent.layout.typesystem import TypeSystem  # noqa: E402

FIX = ROOT / "examples" / "synthetic_projects"


def run(project, **style):
    t = tempfile.mkdtemp()
    r = pipeline.run(FIX / project, t, "B3_full", default_spec(style=style), pptx=False)
    scenes = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((Path(t) / "scenes").glob("*.json"))]
    plan = json.loads((Path(t) / "plan.json").read_text(encoding="utf-8"))
    return r, scenes, plan


def graphics(sc):
    return [e for e in sc["elements"] if e["kind"] in ("image", "pdf-region")]


class CraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = {p: run(p) for p in ("arch_01", "ux_01", "photo_01", "brand_01")}
        cls.grid = columns(default_spec(), 12)

    def test_graphics_snap_to_grid_columns(self):
        g = self.grid
        right = default_spec()["width_mm"] - default_spec()["margin_mm"]
        for p, (r, scenes, _) in self.out.items():
            self.assertTrue(r["gate_pass"], (p, r["gate_issues"]))
            for sc in scenes:
                gs = sorted((e for e in graphics(sc) if not e["id"].startswith("bleed-")), key=lambda e: e["box_mm"][0])   # bleed graphics leave the grid on purpose (gates: bleed box)
                prev_right = None
                for e in gs:
                    x, y, w, h = e["box_mm"]
                    on_col = any(abs(x - cx) < 0.06 for cx in g["x"])
                    on_right = abs(x + w - right) < 0.06
                    adjacent = prev_right is not None and abs(x - (prev_right + g["gutter"])) < 0.06
                    self.assertTrue(on_col or on_right or adjacent, (p, sc["page_id"], e["id"], x, w))
                    prev_right = x + w

    def test_text_columns_respect_the_measure(self):
        ts = TypeSystem(default_spec(), {}, None, "x")
        cpm = ts.chars_per_mm("body")
        for p, (_, scenes, _) in self.out.items():
            for sc in scenes:
                for e in sc["elements"]:
                    if e["id"].startswith("body-") and len(e.get("text", "")) > 150:   # the measure is a paragraph rule
                        chars = e["box_mm"][2] * cpm
                        self.assertTrue(40 <= chars <= 80, (p, sc["page_id"], e["id"], round(chars)))

    def test_header_and_footer_are_switchable(self):
        _, scenes, _ = run("arch_01", header=False, footer=True)
        ids = {e["id"].split("-")[0] for sc in scenes for e in sc["elements"]}
        self.assertNotIn("header", ids)
        self.assertIn("folio", ids)
        _, scenes, _ = run("arch_01", header=True, footer=False)
        ids = {e["id"].split("-")[0] for sc in scenes for e in sc["elements"]}
        self.assertIn("header", ids)
        self.assertNotIn("folio", ids)

    def test_credits_sections_never_become_page_headings(self):
        _, scenes, plan = self.out["arch_01"]
        heads = [pg["title"] for pg in plan["pages"] if pg["role"] not in ("cover", "closing")]
        self.assertNotIn("Role", heads)
        self.assertEqual(plan["pages"][-1]["role"], "closing")
        self.assertIn("14 weeks", plan["pages"][-1]["statement"])

    def test_pair_rows_align_tops_and_share_height(self):
        seen = 0
        for p, (_, scenes, plan) in self.out.items():
            for sc, pg in zip(scenes, plan["pages"]):
                gs = graphics(sc)
                if pg.get("_composition") == "pair-row":
                    self.assertAlmostEqual(gs[0]["box_mm"][1], gs[1]["box_mm"][1], delta=0.06, msg=(p, sc["page_id"]))
                    self.assertAlmostEqual(gs[0]["box_mm"][3], gs[1]["box_mm"][3], delta=0.06, msg=(p, sc["page_id"]))
                    seen += 1
        self.assertGreater(seen, 0, "no pair row found in fixtures")

    def test_every_page_carries_content(self):
        for p, (_, scenes, plan) in self.out.items():
            for sc in scenes:
                has = bool(graphics(sc)) or any(e["id"].startswith("title-") and e.get("font_size_pt", 0) > 20 for e in sc["elements"])
                self.assertTrue(has, (p, sc["page_id"]))

    def test_cjk_title_never_gets_latin_only_serif(self):
        ts = TypeSystem(default_spec(), {"display": "serif"}, type("M", (), {"font_available": staticmethod(lambda n: True)})(), "한글 제목")
        self.assertIsNone(ts.heading_font)
        ts2 = TypeSystem(default_spec(), {"display": "serif"}, type("M", (), {"font_available": staticmethod(lambda n: True)})(), "Latin Title")
        self.assertEqual(ts2.heading_font, "georgia")
        self.assertNotIn("font", ts2.style("display", "한글"))  # per-element fallback too

    def test_user_fonts_and_colours_override_domain_tokens(self):
        _, scenes, plan = run("arch_01", font_title="malgunbd", text_color="#102030", paper_color="#ffffff")
        title = next(e for sc in scenes for e in sc["elements"] if e["id"] == "title-01")
        self.assertEqual(title["style"]["font"], "malgunbd")
        self.assertEqual(title["style"]["color"], "#102030")


if __name__ == "__main__":
    unittest.main()
