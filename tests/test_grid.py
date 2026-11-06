"""Host-author grid helper: numbers must be exact, or hosts would copy wrong geometry."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runtime"))
from portfolio_agent.engine import grid  # noqa: E402
from portfolio_agent.engine.spec import default_spec  # noqa: E402


class GridTests(unittest.TestCase):
    def test_last_column_ends_exactly_at_right_margin(self):
        for spec in (default_spec(), default_spec(width_mm=210, height_mm=297, margin_mm=15, gutter_mm=4)):
            g = grid.columns(spec)
            right = g["x"][-1] + g["col_w"]
            self.assertAlmostEqual(right, spec["width_mm"] - spec["margin_mm"], delta=0.1)
            self.assertAlmostEqual(g["x"][0], spec["margin_mm"])

    def test_full_span_equals_inner_width(self):
        spec = default_spec()
        g = grid.columns(spec)
        self.assertAlmostEqual(grid.span_width(g, 12), spec["width_mm"] - 2 * spec["margin_mm"], delta=0.05)

    def test_box_aspect_is_exact_and_fits_height(self):
        g = grid.columns(default_spec())
        for aspect in (0.5, 1.0, 1.6, 3.0):
            boxes = grid.asset_boxes(g, aspect, g["margin_box"][3])
            self.assertTrue(boxes)
            for b in boxes:
                self.assertAlmostEqual(b["w"] / b["h"], aspect, delta=0.01 * aspect)
                self.assertLessEqual(b["h"], g["margin_box"][3])

    def test_too_tall_spans_are_dropped(self):
        g = grid.columns(default_spec())
        spans = [b["span"] for b in grid.asset_boxes(g, 0.4, g["margin_box"][3])]
        self.assertNotIn(12, spans)

    def test_view_lists_every_asset(self):
        v = grid.view(ROOT / "examples" / "synthetic_projects" / "arch_01", default_spec())
        self.assertGreaterEqual(len(v["assets"]), 3)
        self.assertTrue(all(a["boxes_by_span"] for a in v["assets"]))


if __name__ == "__main__":
    unittest.main()
