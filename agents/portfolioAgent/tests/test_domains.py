"""Domain generality: non-architecture synthetic projects must pass the SAME hard gates with no domain code.
Mechanical only (gates + pattern selection). Says nothing about design quality."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.engine import pipeline  # noqa: E402

FIX = ROOT / "examples" / "synthetic_projects"
EXPECT = {"ux_01": "ux-flow", "brand_01": "brand-system", "photo_01": "photo-series", "arch_01": "arch-drawing-led"}


class DomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (FIX / "photo_01").is_dir():
            import subprocess
            subprocess.check_call([sys.executable, str(ROOT / "examples" / "make_fixtures.py")])

    def test_each_domain_passes_gates_with_its_own_pattern(self):
        for name, pattern in EXPECT.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as t:
                r = pipeline.run(FIX / name, t, "B3_full", pptx=False)
                self.assertTrue(r["gate_pass"], r["gate_issues"])
                self.assertEqual(r["pattern"], pattern)

    def test_domain_override_changes_pattern_not_gates(self):
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "photo_01", t, "B3_full", domain="generic", pptx=False)
            self.assertTrue(r["gate_pass"], r["gate_issues"])
            self.assertNotEqual(r["pattern"], "photo-series")

    def test_every_asset_is_placed_in_every_domain(self):
        import json
        for name in ("ux_01", "brand_01", "photo_01"):
            with self.subTest(name), tempfile.TemporaryDirectory() as t:
                pipeline.run(FIX / name, t, "B3_full", pptx=False)
                man = json.loads((Path(t) / "manifest.json").read_text(encoding="utf-8"))
                used = {e.get("asset_id") for f in (Path(t) / "scenes").glob("*.json") for e in json.loads(f.read_text(encoding="utf-8"))["elements"]}
                self.assertEqual({a["id"] for a in man["assets"]} - used, set())


if __name__ == "__main__":
    unittest.main()
