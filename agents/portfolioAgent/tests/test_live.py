"""Live editing of the DesignCraft document (engine/live.py + backends/designcraft/live.py). Needs the pinned binary; skipped without it."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.engine import pipeline, live, registry  # noqa: E402

FIX = ROOT / "examples/synthetic_projects"


def _scenes(out):
    return {s["page_id"]: s for s in (json.loads(f.read_text(encoding="utf-8")) for f in sorted((Path(out) / "scenes").glob("page-*.json")))}


def _el(out, key):
    page, eid = key.split("/")
    return next(e for e in _scenes(out)[page]["elements"] if e["id"] == eid)


class LiveEditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.get_backend("designcraft")
        if sys.modules["pa_backend_designcraft"].CLI is None:
            raise unittest.SkipTest("designcraft-cli not installed under .cache/bin/designcraft")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        pipeline.run(FIX / "arch_01", cls.out, "B3_full", pptx=False)
        r = live.start(cls.out)
        assert r["ok"], r
        cls.dc = live._dc()
        page = _scenes(cls.out)["page-02"]
        cls.title = "page-02/" + next(e["id"] for e in page["elements"] if e["id"].startswith("title"))
        cls.body = "page-02/" + next(e["id"] for e in page["elements"] if e["id"].startswith("body"))
        cls.image = "page-02/" + next(e["id"] for e in page["elements"] if e["kind"] == "image")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_1_mark_finds_the_element_and_context_is_one_page(self):
        x, y, w, h = _el(self.out, self.image)["box_mm"]
        c = live.context(self.out, "page-02", x + w / 2, y + h / 2)
        self.assertEqual(c["marked"][0], self.image)
        self.assertTrue(all(e["key"].startswith("page-02/") for e in c["elements"]))
        self.assertIn("set_box", c["tools"])

    def test_2_text_edit_changes_only_its_target(self):
        r = live.edit(self.out, [{"op": "set_text", "target": self.title, "text": "Courtyard"}])
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["changed"], {self.title: ["text"]})
        self.assertEqual(_el(self.out, self.title)["text"], "Courtyard")
        self.assertEqual(_el(self.out, self.title)["edited_by"], "agent")
        self.assertTrue(Path(r["document"]).is_file() and Path(r["pdf"]).is_file())

    def test_3_edit_that_breaks_a_gate_is_not_kept_and_says_why(self):
        before = live._state(self.out)["step"]
        box = _el(self.out, self.image)["box_mm"]
        r = live.edit(self.out, [{"op": "move", "target": self.image, "dx_mm": -200, "dy_mm": 0}])
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "GATE")
        self.assertTrue(any("OUTSIDE_MARGIN" in c for c in r["critique"]), r["critique"])
        self.assertEqual(live._state(self.out)["step"], before)
        self.assertEqual(_el(self.out, self.image)["box_mm"], box)

    def test_4_one_bad_op_does_not_cancel_the_good_one(self):
        r = live.edit(self.out, [{"op": "explode", "target": self.title}, {"op": "set_text", "target": "page-02/nope", "text": "x"},
                                 {"op": "move", "target": self.title, "dx_mm": 0, "dy_mm": 1}])
        self.assertTrue(r["ok"], r)
        self.assertEqual([x["ok"] for x in r["results"]], [False, False, True])
        self.assertEqual(r["changed"], {self.title: ["box"]})

    def test_5_user_changes_are_taken_in_and_protected(self):
        st = live._state(self.out)
        mine = self.out / "saved-by-user.designcraft"   # what the editor would save after the user drags the body text
        self.dc.apply(live._file(self.out, st["step"], "designcraft"), [{"op": "move", "target": self.body, "dx_mm": 0, "dy_mm": 3}], mine)
        r = live.sync(self.out, mine)
        self.assertEqual(r["changed"], {self.body: ["box"]})
        self.assertEqual(_el(self.out, self.body)["edited_by"], "user")
        r = live.edit(self.out, [{"op": "move", "target": self.body, "dx_mm": 0, "dy_mm": -3}])
        self.assertFalse(r["ok"])
        self.assertIn("USER_EDITED", r["results"][0]["error"])
        r = live.edit(self.out, [{"op": "move", "target": self.body, "dx_mm": 0, "dy_mm": -1}], marked=[self.body])
        self.assertTrue(r["ok"], r)

    def test_7_type_size_reaches_the_scene_and_text_that_no_longer_fits_is_refused(self):
        r = live.edit(self.out, [{"op": "text_style", "target": self.title, "size": 24}])
        self.assertTrue(r["ok"], r)
        self.assertEqual(_el(self.out, self.title)["font_size_pt"], 24)
        self.assertEqual(r["changed"], {self.title: ["style"]})
        r = live.edit(self.out, [{"op": "set_text", "target": self.body, "text": "word " * 900}], marked=[self.body])
        self.assertFalse(r["ok"])
        self.assertEqual(r["reason"], "GATE")

    def test_6_picture_keeps_its_shape_and_undo_goes_back(self):
        x, y, w, h = _el(self.out, self.image)["box_mm"]
        r = live.edit(self.out, [{"op": "set_box", "target": self.image, "box_mm": [x, y, w * 0.8, h]}])
        self.assertTrue(r["ok"], r)
        nx, ny, nw, nh = _el(self.out, self.image)["box_mm"]
        self.assertAlmostEqual(nw / nh, w / h, delta=0.01)
        self.assertLess(nw, w)
        r = live.undo(self.out)
        self.assertTrue(r["ok"])
        self.assertEqual(_el(self.out, self.image)["box_mm"], [x, y, w, h])

    def test_8_judge_sees_the_request_and_a_low_score_takes_the_edit_back(self):
        said = "move the title down a little"
        step, box = live._state(self.out)["step"], _el(self.out, self.title)["box_mm"]
        r = live.edit(self.out, [{"op": "move", "target": self.title, "dx_mm": 0, "dy_mm": 1}], instruction=said)
        self.assertTrue(r["ok"], r)
        j = live.judge_context(self.out)
        self.assertEqual(j["instruction"], said)
        self.assertAlmostEqual(j["changed"][self.title]["after"]["box_mm"][1] - j["changed"][self.title]["before"]["box_mm"][1], 1, delta=0.05)
        self.assertEqual(len(j["pages"][0]["empty_band_after_mm"]), 2)
        v = live.verdict(self.out, 2, "the title barely moved")
        self.assertEqual((v["kept"], v["retry"], v["tries"]), (False, True, 1))
        self.assertEqual(live._state(self.out)["step"], step)
        self.assertEqual(_el(self.out, self.title)["box_mm"], box)
        self.assertFalse(live.judge_context(self.out)["ok"])   # nothing left to judge
        r = live.edit(self.out, [{"op": "move", "target": self.title, "dx_mm": 0, "dy_mm": 2}], instruction=said)
        self.assertTrue(r["ok"], r)
        self.assertTrue(live.verdict(self.out, 5)["kept"])
        h = [x for x in live._state(self.out)["history"] if x.get("instruction") == said]
        self.assertEqual([(x["judge"]["score"], x.get("undone_by")) for x in h], [(2, "judge"), (5, None)])

    def test_9_user_undo_is_recorded_against_the_agent_edit(self):
        r = live.edit(self.out, [{"op": "move", "target": self.title, "dx_mm": 0, "dy_mm": -1}], instruction="up a bit")
        self.assertTrue(r["ok"], r)
        live.undo(self.out)
        h = live._state(self.out)["history"]
        self.assertEqual(h[-2]["undone_by"], "user")
        self.assertEqual((h[-1]["by"], h[-1]["undid"]), ("undo", r["step"]))


if __name__ == "__main__":
    unittest.main()
