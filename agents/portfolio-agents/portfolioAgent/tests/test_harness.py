"""Harness guardrails (research/PAPER_NOTES_AUTODESIGN_HARNESS.md): blocking vs advisory gates, minimum type size, text grounding,
immutable attempts ledger, fresh-review binding, finalize refusal. Every test can fail for a real reason."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.engine import pipeline, registry, review  # noqa: E402
from portfolio_agent.engine.spec import default_spec  # noqa: E402
from portfolio_agent.core.guardrails import gates  # noqa: E402

FIX = ROOT / "examples" / "synthetic_projects"


def scene(elements):
    base = {"z_index": 1, "locked": False, "allow_overlap": False}
    return {"schema_version": "0.2.0", "project_id": "t", "page_id": "page-01", "size_mm": [297, 210], "elements": [{**base, **e} for e in elements]}


class GateSplitTests(unittest.TestCase):
    def test_naive_layout_passes_blocking_gates_but_carries_advisories(self):
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "arch_01", t, "B0_naive", pptx=False)
        self.assertTrue(r["gate_pass"], r["blocking_issues"])
        self.assertTrue({i["code"] for i in r["advisory_issues"]} & {"REPEATED_LAYOUT", "HERO_TOO_SMALL"}, r["advisory_issues"])

    def test_full_condition_has_no_advisories_on_fixture(self):
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "arch_01", t, "B3_full", pptx=False)
        self.assertEqual([i["code"] for i in r["advisory_issues"] if i["code"] not in ("TEXT_UNGROUNDED", "WHITESPACE_EXCESS", "IMBALANCE")], [])

    def test_type_too_small_is_blocking(self):
        be = registry.get_backend("local")
        be.configure({})
        sc = scene([{"id": "body-01", "kind": "text", "text": "tiny", "box_mm": [20, 20, 100, 20], "font_size_pt": 5}])
        codes = [i["code"] for i in gates.qa_scene(sc, {"assets": []}, default_spec(), be)]
        self.assertIn("TYPE_TOO_SMALL", codes)
        self.assertIn("TYPE_TOO_SMALL", gates.BLOCKING)

    def test_invented_sentence_is_flagged_as_ungrounded_advisory(self):
        with tempfile.TemporaryDirectory() as t:
            pipeline.run(FIX / "arch_01", t, "B3_full", pptx=False)
            scenes_dir = Path(t) / "scenes"
            f = sorted(scenes_dir.glob("*.json"))[1]
            sc = json.loads(f.read_text(encoding="utf-8"))
            body = next(e for e in sc["elements"] if e["id"].startswith("body-"))
            body["text"] = "The tower is 48 storeys tall and won the Pritzker Prize in 2031."
            issues = gates.grounding_issues([sc], FIX / "arch_01")
        self.assertEqual([i["code"] for i in issues], ["TEXT_UNGROUNDED"])
        self.assertIn("TEXT_UNGROUNDED", gates.ADVISORY)


class AttemptsAndReviewTests(unittest.TestCase):
    def test_attempts_are_numbered_and_final_only_after_fresh_review(self):
        with tempfile.TemporaryDirectory() as t:
            pipeline.run(FIX / "arch_01", t, "B3_full", pptx=False)
            pipeline.run(FIX / "arch_01", t, "B3_full", pptx=False)
            att = sorted(p.name for p in (Path(t) / "attempts").iterdir() if p.is_dir())
            self.assertEqual(att, ["01", "02"])
            ledger = [json.loads(l) for l in (Path(t) / "attempts" / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([l["attempt"] for l in ledger], ["01", "02"])
            self.assertFalse((Path(t) / "final" / "FINAL.json").exists(), "final must not exist before a fresh review")
            with self.assertRaises(review.ReviewError):
                review.finalize(t)
            ctx = review.review_context(t)
            good = {"review_context_sha256": ctx["review_context_sha256"], "frame_hashes": ctx["frames"], "reviewer_mode": "fresh_subagent",
                    "reviewed_frames": list(ctx["frames"]), "dimension_scores": {d: 0.8 for d in review.DIMENSIONS}, "blockers": [], "issues": []}
            rp = Path(t) / "rv.json"
            # self-authored review is refused
            rp.write_text(json.dumps({**good, "reviewer_mode": "author"}), encoding="utf-8")
            with self.assertRaises(review.ReviewError):
                review.record_review(t, rp)
            # tampered frame hash is refused
            bad = {**good, "frame_hashes": {k: "0" * 64 for k in ctx["frames"]}}
            rp.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaises(review.ReviewError):
                review.record_review(t, rp)
            # low mean cannot be declared a pass
            low = {**good, "dimension_scores": {d: 0.5 for d in review.DIMENSIONS}, "verdict": "pass"}
            rp.write_text(json.dumps(low), encoding="utf-8")
            with self.assertRaises(review.ReviewError):
                review.record_review(t, rp)
            rp.write_text(json.dumps(good), encoding="utf-8")
            stored = review.record_review(t, rp)
            self.assertEqual(stored["verdict"], "pass")
            rec = review.finalize(t)
            self.assertEqual(rec["attempt"], "02")
            self.assertTrue((Path(t) / "final" / "book.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
