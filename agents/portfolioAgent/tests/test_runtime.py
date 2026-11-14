import sys, json, tempfile, shutil, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
from portfolio_agent.engine import pipeline, edit, registry  # noqa: E402
from portfolio_agent.core.sources import assets
from portfolio_agent.core.guardrails import gates  # noqa: E402

FIX = ROOT / "examples/synthetic_projects"


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (FIX / "arch_01").is_dir():
            import subprocess
            subprocess.check_call([sys.executable, str(ROOT / "examples/make_fixtures.py")])

    def test_full_pipeline_passes_gates_and_outputs_exist(self):
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "arch_01", t, "B3_full")
            self.assertTrue(r["gate_pass"], r["gate_issues"])
            for f in ("book.pdf", "book.pptx", "qa.json", "manifest.json"):
                self.assertTrue((Path(t) / f).is_file(), f)
            self.assertEqual(r["pattern"], "arch-drawing-led")

    def test_naive_baseline_is_flagged_by_advisory_diagnostics(self):
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "arch_01", t, "B0_naive", pptx=False)
            self.assertTrue(r["advisory_issues"], "naive all-grid plan must trigger composition diagnostics")

    def test_long_text_is_paginated_not_truncated(self):
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "arch_02", t, "B3_full", pptx=False)
            self.assertTrue(r["gate_pass"], r["gate_issues"])
            _, brief = assets.ingest(FIX / "arch_02")
            want = brief["sections"]["Concept"].split()
            got = []
            for f in sorted((Path(t) / "scenes").glob("*.json")):
                for e in json.loads(f.read_text(encoding="utf-8"))["elements"]:
                    if e["id"].startswith("body") and e["text"].startswith("The scheme"):
                        got += e["text"].split()
            self.assertEqual(want, got)

    def test_refuses_silent_asset_drop(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                pipeline.run(FIX / "arch_01", t, "B3_full", pipeline.default_spec(page_count=2))

    def test_local_edit_preserves_everything_else(self):
        with tempfile.TemporaryDirectory() as t:
            pipeline.run(FIX / "arch_01", t, "B3_full", pptx=False)
            ok = edit.edit_text(t, "page-02", "body-02", "Short revised text.")
            self.assertTrue(ok["ok"], ok)
            self.assertEqual(ok["pixels_changed_outside_target"], 0)
            self.assertEqual(edit.edit_text(t, "page-01", "photo-01-1", "x")["reason"], "LOCKED_TARGET")
            bad = edit.edit_text(t, "page-02", "body-02", "overflow " * 500)
            self.assertFalse(bad["ok"])
            self.assertIn("TEXT_OVERFLOW", [i["code"] for i in bad["qa_issues"]])

    def test_an_accepted_edit_becomes_a_new_attempt(self):
        """Review and finalize read the latest attempt; an edit that stays outside the attempts is never reviewed or promoted."""
        with tempfile.TemporaryDirectory() as t:
            pipeline.run(FIX / "arch_01", t, "B3_full", pptx=False)
            out = Path(t)
            before_frame = (out / "attempts/01/preview/page-02.png").read_bytes()
            ok = edit.edit_text(t, "page-02", "body-02", "Short revised text.")
            self.assertTrue(ok["ok"], ok)
            self.assertEqual(ok["attempt"], "02")
            self.assertEqual(sorted(p.name for p in (out / "attempts").iterdir() if p.is_dir()), ["01", "02"])
            self.assertIn("Short revised text.", (out / "attempts/02/scenes/page-02.json").read_text(encoding="utf-8"))
            self.assertNotIn("Short revised text.", (out / "attempts/01/scenes/page-02.json").read_text(encoding="utf-8"), "an attempt is immutable")
            self.assertNotEqual((out / "attempts/02/preview/page-02.png").read_bytes(), before_frame, "the reviewer must see the edited page")
            self.assertEqual((out / "attempts/02/preview/page-01.png").read_bytes(), (out / "attempts/01/preview/page-01.png").read_bytes())
            self.assertEqual((out / "preview/page-02.png").read_bytes(), (out / "attempts/02/preview/page-02.png").read_bytes())
            self.assertTrue(json.loads((out / "attempts/02/qa.json").read_text(encoding="utf-8"))["gate_pass"])
            rejected = edit.edit_text(t, "page-02", "body-02", "overflow " * 500)
            self.assertFalse(rejected["ok"])
            self.assertEqual(len([p for p in (out / "attempts").iterdir() if p.is_dir()]), 2, "a rejected edit leaves no attempt")

    def test_layout_search_keeps_only_candidates_the_gates_pass(self):
        """Every page records what was tried and why it was rejected; nothing is cropped unless the asset allows it; no content is lost."""
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run_author(FIX / "arch_01", t, "rule_based", {"cases": True, "review": True, "search": True}, pptx=False)
            self.assertTrue(r["gate_pass"], r["gate_issues"])
            plan = json.loads((Path(t) / "plan.json").read_text(encoding="utf-8"))
            records = plan["meta"]["search"]
            self.assertEqual(len(records), r["pages"])
            self.assertTrue(any(c["ok"] is False and c["why"] for rec in records for c in rec["candidates"]), "rejections carry their reason")
            self.assertTrue(any(len(rec["candidates"]) > 20 for rec in records), "a page with assets gets a real search")
            self.assertFalse(any(rec["chosen"] and rec["chosen"].startswith("bleed") for rec in records), "fixture assets are not marked crop_allowed")
            scenes = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((Path(t) / "scenes").glob("page-*.json"))]
            self.assertFalse(any(e.get("crop") for sc in scenes for e in sc["elements"]))
            for pg, sc in zip(plan["pages"], scenes):
                self.assertTrue(set(pg["assets"]) <= {e.get("asset_id") for e in sc["elements"]})
            ok = edit.edit_text(t, "page-02", "body-02", "Short revised text.") if any(e["id"] == "body-02" for e in scenes[1]["elements"]) else {"ok": True}
            self.assertTrue(ok["ok"], ok)

    def test_tampered_source_is_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            proj = Path(t) / "p"
            shutil.copytree(FIX / "arch_03", proj)
            manifest, brief = assets.ingest(proj)
            (proj / "images/img01.png").write_bytes(b"tampered")
            codes = [i["code"] for i in gates.qa_book([], manifest, {"pages": [], "hero_min_ratio": 0}, pipeline.default_spec(), proj, registry.get_backend("local"))]
            self.assertIn("SOURCE_MODIFIED", codes)

    def test_non_architecture_domain_uses_its_own_pattern(self):
        from portfolio_agent.authors import knowledge as cases
        m, b = assets.ingest(FIX / "arch_03")
        b["domain"], b["keywords"] = "photography", ["series"]
        self.assertEqual(cases.retrieve(b, m)[0]["pattern"]["id"], "photo-series")

    def test_style_footer_off_and_custom_fonts(self):
        import fitz
        st = {"footer": False, "font_title": "malgunbd", "font_body": r"C:\Windows\Fonts\segoeui.ttf", "body_pt": 12}
        with tempfile.TemporaryDirectory() as t:
            r = pipeline.run(FIX / "arch_01", t, "B3_full", pipeline.default_spec(style=st), pptx=False)
            self.assertTrue(r["gate_pass"], r["gate_issues"])
            ids = [e["id"] for f in (Path(t) / "scenes").glob("*.json") for e in json.loads(f.read_text(encoding="utf-8"))["elements"]]
            self.assertFalse(any(i.startswith(("folio", "rule")) for i in ids))
            fonts = {f[3] for pg in fitz.open(Path(t) / "book.pdf") for f in pg.get_fonts()}
            self.assertIn("Segoe UI Regular", fonts)
            self.assertIn("Malgun Gothic Bold", fonts)
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                pipeline.run(FIX / "arch_01", t, "B3_full", pipeline.default_spec(style={"font_body": "NoSuchFont"}), pptx=False)

    def test_designcraft_backend_if_installed(self):
        import fitz
        be = registry.get_backend("designcraft")
        from portfolio_agent.core.model import contracts
        self.assertIsInstance(be, contracts.Exporter)
        try:
            import importlib
            cli = sys.modules[be.__class__.__module__].CLI
        except Exception:
            cli = None
        if cli is None:
            self.skipTest("designcraft-cli not installed under .cache/bin/designcraft")
        with tempfile.TemporaryDirectory() as t:
            pipeline.run(FIX / "arch_03", t, "B3_full", pptx=False)
            scenes = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((Path(t) / "scenes").glob("page-*.json"))]
            manifest = json.loads((Path(t) / "manifest.json").read_text(encoding="utf-8"))
            r = be.export(scenes, manifest, FIX / "arch_03", Path(t) / "dc" / "book", pipeline.default_spec(), ["pdf", "pptx", "native", "idml"])
            self.assertEqual(r["exit"], 0, r)
            self.assertTrue(all(r["files"].values()), r["files"])
            d = fitz.open(Path(t) / "dc" / "book.pdf")
            n, w = d.page_count, d[0].rect.width / 72 * 25.4
            d.close()
            self.assertEqual(n, len(scenes))
            self.assertAlmostEqual(w, 297, delta=0.5)


if __name__ == "__main__":
    unittest.main()
