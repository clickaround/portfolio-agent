"""Scene Document v0.2 (element.style): schema, rendering and measuring. Each test can fail for a real reason."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.core.workspace import SCENE_SCHEMA  # noqa: E402
from portfolio_agent.engine import registry  # noqa: E402

SCHEMA = json.loads(SCENE_SCHEMA.read_text(encoding="utf-8"))
SERIF_ITALIC = r"C:\Windows\Fonts\georgiai.ttf"
HAVE_FONT = Path(SERIF_ITALIC).is_file()


def scene(elements, version="0.2.0"):
    base = {"z_index": 1, "locked": False, "allow_overlap": False}
    return {"schema_version": version, "project_id": "t", "page_id": "page-01", "size_mm": [200, 100], "elements": [{**base, **e} for e in elements]}


def txt(id_, text, style=None, box=(10, 10, 120, 30), pt=14):
    e = {"id": id_, "kind": "text", "text": text, "box_mm": list(box), "font_size_pt": pt}
    if style:
        e["style"] = style
    return e


class SchemaTests(unittest.TestCase):
    def test_v01_scene_without_style_still_valid(self):
        jsonschema.validate(scene([txt("body-01", "hello")], "0.1.0"), SCHEMA)

    def test_v02_style_accepted(self):
        jsonschema.validate(scene([txt("title-01", "Hi", {"font": "georgiai", "color": "#aa2200", "align": "right", "line_height": 1.4})]), SCHEMA)

    def test_bad_colour_unknown_key_and_line_height_rejected(self):
        for bad in ({"color": "red"}, {"colour": "#000000"}, {"line_height": 0.2}, {"align": "justify"}):
            with self.assertRaises(jsonschema.ValidationError, msg=bad):
                jsonschema.validate(scene([txt("body-01", "x", bad)]), SCHEMA)


class LocalRenderTests(unittest.TestCase):
    def render(self, elements):
        be = registry.get_backend("local")
        be.configure({})
        with tempfile.TemporaryDirectory() as t:
            ex = be.export([scene(elements)], {"assets": []}, t, Path(t) / "b", {}, ["pdf"])
            d = fitz.open(str(Path(t) / "b.pdf"))
            spans = [s for b in d[0].get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
            d.close()
        return ex, spans

    @unittest.skipUnless(HAVE_FONT, "georgiai.ttf not installed")
    def test_colour_font_and_alignment_reach_the_pdf(self):
        _, spans = self.render([txt("body-01", "Right aligned", {"font": SERIF_ITALIC, "color": "#cc0000", "align": "right"})])
        s = spans[0]
        self.assertEqual(s["color"], 0xCC0000)
        self.assertNotIn("Malgun", s["font"], "style.font must override the default body font")
        self.assertGreater(s["bbox"][0], (10 + 60) * 72 / 25.4, "right-aligned text must start in the right half of its 120mm box")

    def test_default_style_unchanged_black_left(self):
        _, spans = self.render([txt("body-01", "Plain")])
        self.assertEqual(spans[0]["color"], 0x1A1A1A)
        self.assertLess(spans[0]["bbox"][0], (10 + 5) * 72 / 25.4)

    def test_line_height_changes_fit_measurement(self):
        be = registry.get_backend("local")
        be.configure({})
        long = " ".join(["word"] * 40)
        self.assertTrue(be.text_fits(long, 60, 30, 10, False, {"line_height": 1.0}))
        self.assertFalse(be.text_fits(long, 60, 30, 10, False, {"line_height": 2.5}))

    def test_non_font_and_network_paths_are_refused(self):
        readme = str(ROOT.parent / "AGENTS.md")
        bs = chr(92)
        for bad in (readme, bs * 2 + "attacker" + bs + "share" + bs + "x.ttf", "//host/share/x.ttf"):
            with self.assertRaises(ValueError, msg=bad):
                self.render([txt("body-01", "x", {"font": bad})])

    def test_unknown_font_fails_loudly(self):
        with self.assertRaises(ValueError):
            self.render([txt("body-01", "x", {"font": "no-such-font-xyz"})])

    def test_shape_fill_tint_and_hairline(self):
        be = registry.get_backend("local")
        be.configure({})
        shp = {"id": "rule-01", "kind": "shape", "box_mm": [10, 50, 100, 0.3], "style": {"fill": "#e8e2d6"}}
        with tempfile.TemporaryDirectory() as t:
            be.export([scene([shp])], {"assets": []}, t, Path(t) / "b", {}, ["pdf"])
            d = fitz.open(str(Path(t) / "b.pdf"))
            fills = [dr["fill"] for dr in d[0].get_drawings() if dr.get("fill")]
            d.close()
        self.assertTrue(any(abs(f[0] - 0xE8 / 255) < 0.01 and abs(f[2] - 0xD6 / 255) < 0.01 for f in fills), fills)


class PreviewTests(unittest.TestCase):
    def test_png_previews_one_per_page_and_nonblank(self):
        be = registry.get_backend("local")
        sc1, sc2 = scene([txt("body-01", "page one")]), scene([txt("body-01", "page two")])
        sc2["page_id"] = "page-02"
        with tempfile.TemporaryDirectory() as t:
            ex = be.export([sc1, sc2], {"assets": []}, t, Path(t) / "out" / "book", {}, ["pdf", "png"])
            pngs = sorted(Path(ex["files"]["png"]).glob("page-*.png"))
            self.assertEqual([p.name for p in pngs], ["page-01.png", "page-02.png"])
            pm = fitz.Pixmap(str(pngs[0]))
            self.assertGreater(len(set(pm.samples[::97])), 1, "preview must contain ink, not a blank page")


class PptxParityTests(unittest.TestCase):
    def test_pptx_applies_colour_line_spacing_fill_and_skips_invisible(self):
        from pptx import Presentation
        be = registry.get_backend("local")
        els = [txt("body-01", "styled", {"color": "#cc0000", "line_height": 1.5}),
               txt("body-02", "default colour", box=(10, 50, 100, 20)),
               {"id": "rule-01", "kind": "shape", "box_mm": [10, 80, 100, 1], "style": {"fill": "#e8e2d6"}},
               {**txt("body-03", "hidden", box=(10, 90, 50, 10)), "visible": False}]
        with tempfile.TemporaryDirectory() as t:
            be.export([scene(els)], {"assets": []}, t, Path(t) / "b", {"style": {"text_color": "#112233"}}, ["pdf", "pptx"])
            prs = Presentation(str(Path(t) / "b.pptx"))
        shapes = {s.name: s for s in prs.slides[0].shapes}
        self.assertNotIn("body-03", shapes)
        run1 = shapes["body-01"].text_frame.paragraphs[0].runs[0]
        self.assertEqual(str(run1.font.color.rgb), "CC0000")
        self.assertEqual(shapes["body-01"].text_frame.paragraphs[0].line_spacing, 1.5)
        self.assertEqual(str(shapes["body-02"].text_frame.paragraphs[0].runs[0].font.color.rgb), "112233")
        self.assertEqual(str(shapes["rule-01"].fill.fore_color.rgb), "E8E2D6")
        be.configure({})


class GateUsesStyleTests(unittest.TestCase):
    def test_qa_scene_measures_with_element_style(self):
        from portfolio_agent.core.guardrails import gates
        be = registry.get_backend("local")
        be.configure({})
        long = " ".join(["word"] * 40)
        spec = {"width_mm": 200, "height_mm": 100, "margin_mm": 5, "gutter_mm": 4, "bleed_mm": 0}
        def codes(style):
            sc = scene([txt("body-01", long, style, box=(10, 10, 60, 30), pt=10)])
            return [i["code"] for i in gates.qa_scene(sc, {"assets": []}, spec, be)]
        self.assertNotIn("TEXT_OVERFLOW", codes({"line_height": 1.0}))
        self.assertIn("TEXT_OVERFLOW", codes({"line_height": 2.5}))


if __name__ == "__main__":
    unittest.main()
