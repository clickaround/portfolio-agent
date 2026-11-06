"""Photo-set templates (layout/photoset.py, knowledge/patterns/photosets.json): cells never overlap, every template renders
gate-clean with real photo aspects in both variants, the best template is chosen by fill, a named template is honoured,
and `crop: cover` crops raster photos while keeping the source aspect."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.core.assets import ingest  # noqa: E402
from portfolio_agent.core.guardrails import gates  # noqa: E402
from portfolio_agent.engine.spec import default_spec  # noqa: E402
from portfolio_agent.layout import book, photoset  # noqa: E402

FIX = ROOT / "examples" / "synthetic_projects"


class _M:
    def text_fits(self, *a, **k):
        return True


class TestPhotoset(unittest.TestCase):
    def setUp(self):
        self.m, _ = ingest(FIX / "photo_01")
        self.A = {a["id"]: a for a in self.m["assets"]}
        self.photos = [a["id"] for a in self.m["assets"] if a["role"] == "photo"]
        self.spec = default_spec()

    def _scene(self, k, variant=0, **flags):
        page = {"page": 1, "total": 1, "doc_title": "T", "section": "S", "section_no": 1, "role": "grid", "assets": self.photos[:k], "title": "Photos",
                "captions": [f"c{i}" for i in range(k)], **flags}
        return book.build_scene("p", page, self.A, self.spec, variant), page

    def test_templates_cells_do_not_overlap(self):
        tpl = photoset.templates()
        self.assertGreaterEqual(len(tpl), 20)
        for tid, t in tpl.items():
            self.assertEqual(len(t["cells"]), t["k"], tid)
            for cell in t["cells"]:
                f0, f1, r0, r1 = cell
                self.assertTrue(0 <= f0 < f1 <= 1 and 0 <= r0 < r1 <= 1, (tid, cell))
            for i, a in enumerate(t["cells"]):
                for b in t["cells"][i + 1:]:
                    ox = min(a[1], b[1]) - max(a[0], b[0])
                    oy = min(a[3], b[3]) - max(a[2], b[2])
                    self.assertFalse(ox > 0.01 and oy > 0.01, (tid, a, b))

    def test_every_template_renders_gate_clean(self):
        for tid, t in photoset.templates().items():
            for v in (0, 1):
                sc, pg = self._scene(t["k"], v, photoset=tid)
                blocking, _ = gates.split(gates.qa_scene(sc, self.m, self.spec, _M()))
                self.assertEqual(blocking, [], (tid, v, blocking))
                self.assertEqual(pg["_composition"], f"photoset-{tid}")
                self.assertEqual(len([e for e in sc["elements"] if e.get("asset_id")]), t["k"])

    def test_auto_choice_and_routing(self):
        sc, pg = self._scene(3)
        self.assertTrue(pg["_composition"].startswith("photoset-"))
        self.assertEqual(book.pick({"role": "grid", "assets": self.photos[:4]}, self.A), "photoset")
        self.assertEqual(book.pick({"role": "grid", "assets": self.photos[:2]}, self.A), "pair")
        self.assertEqual(book.pick({"role": "grid", "assets": self.photos[:2], "photoset": "lead-left-2"}, self.A), "photoset")
        with self.assertRaises(KeyError):
            self._scene(3, photoset="no-such-template")

    def test_cover_crops_but_keeps_aspect(self):
        sc, _ = self._scene(4, photoset="quad-4", crop="cover")
        imgs = [e for e in sc["elements"] if e.get("asset_id")]
        self.assertTrue(all(e.get("crop") for e in imgs))
        blocking, _ = gates.split(gates.qa_scene(sc, self.m, self.spec, _M()))
        self.assertEqual(blocking, [], blocking)
        # a 3:1 panorama (img04) in a near-square cell loses its sides, never its height
        e = next(e for e in imgs if e["asset_id"] == "img04")
        self.assertEqual((e["crop"][1], e["crop"][3]), (0.0, 1.0))
        self.assertLess(e["crop"][2] - e["crop"][0], 0.7)


if __name__ == "__main__":
    unittest.main()
