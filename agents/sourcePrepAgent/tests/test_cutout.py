"""Cut-out step (engine/cutout.py, sourcePrepAgent): the original stays byte-identical in sources/, the working copy is an RGBA png,
derived.json records the transform, the asset is flagged cutout, and the before/after sheet renders. Needs rembg + its cached model."""
import shutil
import tempfile
import unittest
from pathlib import Path

FIX = Path(__file__).resolve().parents[2] / "portfolioAgent" / "examples" / "synthetic_projects"


class TestCutout(unittest.TestCase):
    def test_cutout_keeps_original(self):
        try:
            import rembg  # noqa: F401
        except ImportError:
            self.skipTest("rembg not installed")
        if not (Path.home() / ".u2net" / "u2net.onnx").is_file():
            self.skipTest("u2net model not cached (offline)")
        from portfolio_agent.engine import cutout
        from portfolio_agent.core.sources.assets import ingest
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td) / "proj"
            shutil.copytree(FIX / "photo_01", proj)
            src = proj / "images" / "img01.png"
            with Image.open(src) as im:
                w0 = im.width
            before = src.read_bytes()
            done = cutout.cutout(proj, ["img01.png"], engine="rembg")
            self.assertEqual((proj / "sources" / "img01.png").read_bytes(), before)
            with Image.open(proj / "images" / "img01.png") as out:
                self.assertEqual(out.mode, "RGBA")
                self.assertLessEqual(out.width, w0)
            self.assertEqual(done[0]["transform"], "cutout")
            m, _ = ingest(proj)
            a = next(x for x in m["assets"] if x["id"] == "img01")
            self.assertTrue(a.get("cutout"))
            self.assertEqual(a["source_transform"]["tool"], "cutout")
            self.assertTrue(cutout.cutout_sheet(proj, str(Path(td) / "sheet.png")))



if __name__ == "__main__":
    unittest.main()
