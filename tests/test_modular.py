"""Modular layout (grid systems x slot compositions, both data): data validity, frame geometry, and that the catalogue
renders gate-clean for almost every combination on a real fixture."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runtime"))
from portfolio_agent.layout import modular  # noqa: E402
from portfolio_agent.engine.spec import default_spec  # noqa: E402


class DataTests(unittest.TestCase):
    def test_compositions_have_valid_non_overlapping_slots(self):
        for cid, comp in modular.compositions().items():
            slots = comp["slots"]
            self.assertTrue(slots, cid)
            for s in slots:
                for k in ("col", "row"):
                    a, b = s[k]
                    self.assertTrue(0 <= a < b <= 1, (cid, k, s))
                self.assertIn(s["kind"], ("image", "text", "rule"), cid)
            boxes = [s for s in slots if s["kind"] != "rule"]
            for i, s in enumerate(boxes):
                for t in boxes[i + 1:]:
                    ox = min(s["col"][1], t["col"][1]) - max(s["col"][0], t["col"][0])
                    oy = min(s["row"][1], t["row"][1]) - max(s["row"][0], t["row"][0])
                    self.assertFalse(ox > 0.01 and oy > 0.01, (cid, "slots overlap in fraction space", s, t))
            self.assertEqual(comp["images"], sum(1 for s in slots if s["kind"] == "image"), cid)
            if "rule" in {s["kind"] for s in slots}:
                for s in slots:
                    if s["kind"] == "rule":
                        self.assertLess(s["row"][0], s["row"][1], cid)

    def test_grid_systems_fill_the_type_area_exactly(self):
        spec = default_spec()
        for sid, sysm in modular.grid_systems().items():
            fr = modular.frame(sysm, spec, 1)
            g = fr["grid"]
            self.assertAlmostEqual(g["x"][-1] + g["col_w"], fr["right"], delta=0.05, msg=sid)
            self.assertAlmostEqual(g["x"][0], fr["left"], delta=0.01, msg=sid)
            self.assertLess(fr["top"], fr["bottom"], sid)

    def test_ninths_canon_margins(self):
        spec = default_spec(width_mm=210, height_mm=297)
        fr = modular.frame(modular.grid_systems()["book-6-ninths"], spec, 1)
        self.assertAlmostEqual(fr["left"], 210 / 9, delta=0.1)
        self.assertAlmostEqual(spec["width_mm"] - fr["right"], 2 * 210 / 9, delta=0.1)
        fr2 = modular.frame(modular.grid_systems()["book-6-ninths"], spec, 2)
        self.assertAlmostEqual(fr2["left"], 2 * 210 / 9, delta=0.1, msg="even page mirrors inner/outer")


class CatalogueTests(unittest.TestCase):
    def test_catalogue_renders_and_is_mostly_gate_clean(self):
        from portfolio_agent.engine import catalogue
        with tempfile.TemporaryDirectory() as t:
            r = catalogue.build(ROOT / "examples" / "synthetic_projects" / "arch_04", t, default_spec())
            self.assertGreaterEqual(r["pages"], 40)
            clean = sum(1 for x in r["rows"] if not x["blocking"])
            self.assertGreaterEqual(clean / r["pages"], 0.9, [x for x in r["rows"] if x["blocking"]])
            self.assertTrue(Path(r["sheet"]).is_file())


if __name__ == "__main__":
    unittest.main()
