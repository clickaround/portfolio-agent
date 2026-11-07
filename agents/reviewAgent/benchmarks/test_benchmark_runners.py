import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load(name):
    path = Path(__file__).parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BenchmarkRunnersTest(unittest.TestCase):
    def test_ap03_requires_exactly_two_pages(self):
        ap = load("archportfoliobench_ap")
        self.assertFalse(ap.ap03_pass(True, {(420, 297)}, 5))
        self.assertTrue(ap.ap03_pass(True, {(420, 297)}, 2))
        self.assertFalse(ap.ap03_pass(False, {(420, 297)}, 2))

    def test_schema_exists_and_fixture_hash_changes(self):
        ap = load("archportfoliobench_ap")
        self.assertTrue(ap.SCENE_SCHEMA.is_file())
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "file.txt"
            p.write_text("first", encoding="utf-8")
            first = ap.fixture_hashes(Path(td))
            p.write_text("second", encoding="utf-8")
            self.assertNotEqual(first, ap.fixture_hashes(Path(td)))

    def test_run_folders_preserve_prior_output(self):
        ap = load("archportfoliobench_ap")
        reg = load("engine_regression_bench")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for module in (ap, reg):
                one = module.create_run_dir(root)
                (one / "saved.txt").write_text("keep", encoding="utf-8")
                two = module.create_run_dir(root)
                self.assertNotEqual(one, two)
                self.assertEqual((one / "saved.txt").read_text(encoding="utf-8"), "keep")

    def test_crashes_and_failed_task_require_nonzero_exit(self):
        ap = load("archportfoliobench_ap")
        reg = load("engine_regression_bench")
        self.assertNotEqual(ap.result_exit_code([{"crashed": "error"}]), 0)
        self.assertNotEqual(ap.result_exit_code([{"task": "AP-03", "passed": False}]), 0)
        self.assertNotEqual(ap.result_exit_code([{"task": "AP-08", "scene_json_schema_valid": "invalid"}]), 0)
        self.assertNotEqual(ap.result_exit_code([{"task": "AP-07", "other_pages_identical": False}]), 0)
        self.assertEqual(ap.result_exit_code([{"task": "AP-03", "passed": True}]), 0)
        self.assertNotEqual(reg.result_exit_code([{"crashed": "error"}]), 0)

    def test_ap_runner_reports_crashes_and_fails_without_touching_prior_runs(self):
        ap = load("archportfoliobench_ap")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "reviewAgent"
            root.mkdir()
            fixtures = Path(td) / "fixtures"
            fixtures.mkdir()
            (fixtures / "input.txt").write_text("fixture", encoding="utf-8")
            previous = Path(td) / "output" / "previous"
            previous.mkdir(parents=True)
            (previous / "saved.txt").write_text("keep", encoding="utf-8")
            def broken(_):
                raise RuntimeError("synthetic error")
            with patch.object(ap, "ROOT", root), patch.object(ap, "OUT", previous.parent), patch.object(ap, "FIX", fixtures), \
                 patch.object(ap, "ap03", broken), patch.object(ap, "ap05", broken), patch.object(ap, "ap06", broken), \
                 patch.object(ap, "ap07", broken), patch.object(ap, "ap08", broken):
                self.assertEqual(ap.main(), 1)
            reports = list((root / "benchmarks" / "reports").glob("*.json"))
            self.assertEqual(len(reports), 1)
            self.assertEqual((previous / "saved.txt").read_text(encoding="utf-8"), "keep")
            self.assertIn('"crashed"', reports[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
