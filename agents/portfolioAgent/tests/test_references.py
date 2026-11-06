"""Rights gate for reference cases (cases/RIGHTS_PROTOCOL.md): falsifying tests."""
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.core.guardrails import references  # noqa: E402


def _dir(cases):
    d = tempfile.TemporaryDirectory()
    for i, c in enumerate(cases):
        (Path(d.name) / f"{i}.json").write_text(json.dumps(c), encoding="utf-8")
    return d


OK = {"case_id": "A", "rights_status": "approved", "use_scope": ["view", "extract_metadata"], "rights_evidence": "written consent from owner 2026-11-04"}


class ReferenceGateTests(unittest.TestCase):
    def test_empty_library_is_tagged_no_external_reference(self):
        with _dir([]) as d:
            b = references.reference_basis(Path(d))
        self.assertEqual(b["tag"], "NO_EXTERNAL_REFERENCE")
        self.assertEqual(b["approved_cases"], 0)

    def test_link_only_pending_and_heldout_are_refused_with_reasons(self):
        bad = [{**OK, "case_id": "L", "rights_status": "link_only"},
               {**OK, "case_id": "P", "rights_status": "permission_pending"},
               {**OK, "case_id": "H", "split": "heldout"},
               {**OK, "case_id": "S", "use_scope": ["view"]}]
        with _dir(bad) as d:
            b = references.reference_basis(Path(d))
        self.assertEqual(b["tag"], "NO_EXTERNAL_REFERENCE")
        self.assertEqual(sorted(r["case_id"] for r in b["refused"]), ["H", "L", "P", "S"])
        self.assertTrue(all(r["reason"] for r in b["refused"]))

    def test_approved_case_is_accepted_but_quality_not_claimed(self):
        with _dir([OK]) as d:
            b = references.reference_basis(Path(d))
        self.assertEqual((b["tag"], b["case_ids"]), ("APPROVED_CASES_AVAILABLE_NOT_USED", ["A"]))
        self.assertFalse(b["used_in_generation"])
        self.assertIn("unverified", b["claim"])

    def test_malformed_and_bypass_attempts_are_refused_not_crashing(self):
        bad = [{**OK, "case_id": "str-scope", "use_scope": "no_extract_metadata"},
               {**OK, "case_id": "null-scope", "use_scope": None},
               {**OK, "case_id": "no-evidence", "rights_evidence": ""},
               {**OK, "case_id": "held_out-typo", "split": "held_out"},
               {**OK, "case_id": "Heldout-caps", "split": "Heldout"},
               {**OK, "case_id": "flag", "heldout": True},
               {k: v for k, v in OK.items() if k != "case_id"},
               [1, 2, 3], "just a string"]
        with _dir(bad) as d:
            b = references.reference_basis(Path(d))
        self.assertEqual(b["tag"], "NO_EXTERNAL_REFERENCE", b)
        self.assertEqual(len(b["refused"]), len(bad))

    def test_non_json_entries_are_refused_not_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "case.JSON").write_text(json.dumps(OK), encoding="utf-8")
            (Path(d) / "notes.txt").write_text("x", encoding="utf-8")
            b = references.reference_basis(Path(d))
        self.assertEqual(b["tag"], "NO_EXTERNAL_REFERENCE")
        self.assertEqual(len(b["refused"]), 2)

    def test_unreadable_file_is_refused_not_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "x.json").write_text("{not json", encoding="utf-8")
            b = references.reference_basis(Path(d))
        self.assertEqual(len(b["refused"]), 1)

    def test_pipeline_output_carries_the_tag(self):
        from portfolio_agent.engine import pipeline
        from portfolio_agent.engine.spec import default_spec
        with tempfile.TemporaryDirectory() as out:
            rep = pipeline.run(str(ROOT / "examples" / "synthetic_projects" / "arch_01"), out, "B3_full", default_spec())
            qa = json.loads((Path(out) / "qa.json").read_text(encoding="utf-8"))
            plan = json.loads((Path(out) / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["reference_basis"]["tag"], "NO_EXTERNAL_REFERENCE")
        self.assertEqual(qa["reference_basis"]["tag"], "NO_EXTERNAL_REFERENCE")
        self.assertEqual(plan["meta"]["reference_basis"]["tag"], "NO_EXTERNAL_REFERENCE")


if __name__ == "__main__":
    unittest.main()
