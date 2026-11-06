"""End-to-end API tests on the synthetic fixtures (no real sources, no LLM): project -> upload -> manifest -> plan -> compose job -> pages/PDF -> review.
Also: path safety, upload limits, schema errors, the host-LLM runner (fake), and the OpenAPI contract file."""
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

API = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from pascal_api.config import Settings  # noqa: E402
from pascal_api.main import create_app  # noqa: E402

FIX = API.parents[1] / "agents" / "portfolioAgent" / "examples" / "synthetic_projects" / "photo_01" / "images"


def settings(td, **kw):
    d = dict(data_dir=Path(td), claude_bin="claude", max_upload_mb=100, llm_timeout_s=30, workers=2, cors_origins=())
    d.update(kw)
    return Settings(**d)


def wait(c, job, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        j = c.get(f"/jobs/{job['job']}").json()
        if j["status"] in ("succeeded", "failed"):
            return j
        time.sleep(0.3)
    raise AssertionError("job timed out")


def plan_for(ids):
    pages = [{"role": "cover", "assets": [ids[0]], "title": "Winter Harbour"}]
    rest = ids[1:]
    pages.append({"role": "grid", "assets": rest[:3], "title": "Three views", "captions": ["a", "b", "c"], "photoset": "lead-left-3"})
    pages.append({"role": "hero", "assets": [rest[3]], "title": "Wide light", "bleed": "full", "caption": "One photograph covers the page."})
    pages.append({"role": "hero", "assets": [rest[4]], "title": "Last frame", "caption": "The last photograph."})
    pages.append({"role": "closing", "assets": [], "statement": "Synthetic test series."})
    return {"schema_version": "0.1.0", "doc_title": "Winter Harbour Series", "domain": "photography", "keywords": ["series"], "tokens": {}, "pages": pages}


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.c = TestClient(create_app(settings(cls.td.name)))
        cls.c.post("/projects", json={"id": "harbour", "title": "Harbour", "brief": "# Winter Harbour Series\ndomain: photography\nkeywords: series, harbour\n\n## Statement\nSynthetic series for tests.\n"})
        for p in sorted(FIX.glob("*.png")):
            r = cls.c.post("/projects/harbour/assets/images", files={"file": (p.name, p.read_bytes(), "image/png")})
            assert r.status_code == 201, r.text

    @classmethod
    def tearDownClass(cls):
        cls.c.close()
        try:
            cls.td.cleanup()
        except Exception:
            pass

    def test_01_health_catalog_projects(self):
        h = self.c.get("/health").json()
        self.assertEqual(h["status"], "ok")
        self.assertIn("local", h["backends"])
        cat = self.c.get("/catalog").json()
        self.assertGreaterEqual(len(cat["photosets"]), 20)
        self.assertIn("lead-left-3", {t["id"] for t in cat["photosets"]})
        self.assertIn("swiss-12", {g["id"] for g in cat["grid_systems"]})
        self.assertEqual([p["id"] for p in self.c.get("/projects").json()], ["harbour"])
        self.assertEqual(self.c.get("/projects/harbour").json()["assets"]["images"], 6)
        self.assertEqual(self.c.post("/projects", json={"id": "harbour"}).status_code, 409)

    def test_02_manifest(self):
        m = self.c.get("/projects/harbour/manifest").json()
        ids = [a["id"] for a in m["manifest"]["assets"]]
        self.assertEqual(ids, ["img01", "img02", "img03", "img04", "img05", "img06"])
        self.assertEqual(m["brief"]["title"], "Winter Harbour Series")

    def test_03_plan_validation_errors_are_422_with_the_authors_message(self):
        bad = plan_for(["img01", "img02", "img03", "img04", "img05", "img06"])
        bad["pages"][1]["assets"] = ["img02", "img03", "nope"]
        r = self.c.put("/projects/harbour/book-plan", json=bad)
        self.assertEqual(r.status_code, 422, r.text)
        self.assertEqual(r.json()["error"]["code"], "plan_assets")
        self.assertIn("nope", r.json()["error"]["message"])
        r = self.c.put("/projects/harbour/book-plan", json={"pages": []})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json()["error"]["code"], "plan_schema")
        self.assertEqual(self.c.get("/projects/harbour/book-plan").status_code, 404)   # nothing was stored

    def test_04_full_flow_plan_compose_pages_pdf_review(self):
        ids = ["img01", "img02", "img03", "img04", "img05", "img06"]
        r = self.c.put("/projects/harbour/book-plan", json=plan_for(ids))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["pages"], 5)
        job = self.c.post("/projects/harbour/compose", json={"bleed_mm": 3, "paper_color": "#F4F2EE"})
        self.assertEqual(job.status_code, 202)
        j = wait(self.c, job.json())
        self.assertEqual(j["status"], "succeeded", j.get("error"))
        res = j["result"]
        self.assertTrue(res["gate_pass"], res["blocking"])
        self.assertEqual(res["pages"], 5)
        att = res["attempt"]
        att = att if isinstance(att, str) else f"{int(att):02d}"
        d = self.c.get(f"/projects/harbour/attempts/{att}").json()
        self.assertEqual(len(d["pages"]), 5)
        self.assertTrue(d["files"]["book.pdf"])
        png = self.c.get(f"/projects/harbour/attempts/{att}/pages/3.png")
        self.assertEqual(png.status_code, 200)
        self.assertTrue(png.content.startswith(b"\x89PNG"))
        pdf = self.c.get(f"/projects/harbour/attempts/{att}/book.pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        scene = self.c.get(f"/projects/harbour/attempts/{att}/scenes/3").json()
        self.assertTrue(any(e["id"].startswith("bleed-") for e in scene["elements"]))        # the bleed flag reached the layout
        self.assertEqual(self.c.get(f"/projects/harbour/attempts/{att}/pages/99.png").status_code, 404)
        # review: context binds hashes; a bad review is refused with 422, never a silent pass
        ctx = self.c.post("/projects/harbour/review/context").json()
        self.assertEqual(len(ctx["frames"]), 5)
        self.assertEqual(self.c.post("/projects/harbour/review/record", json={"review": {"reviewer_mode": "author"}}).status_code, 422)
        self.assertEqual(self.c.post("/projects/harbour/review/finalize").status_code, 422)   # no passing fresh review yet
        self.assertEqual(len(self.c.get("/projects/harbour/attempts").json()), 1)

    def test_05_prepare_and_cutout_job(self):
        self.c.post("/projects", json={"id": "prep"})
        p = sorted(FIX.glob("*.png"))[0]
        self.c.post("/projects/prep/assets/drawings", files={"file": ("sheet_a.png", p.read_bytes(), "image/png")})
        r = self.c.post("/projects/prep/prepare", json={"approve": False})
        self.assertEqual(r.status_code, 200, r.text)
        r = self.c.post("/projects/prep/prepare", json={"approve": False, "knockout": True})
        self.assertEqual(r.json()["knockout"], ["sheet_a.png"])
        m = self.c.get("/projects/prep/manifest").json()["manifest"]["assets"][0]
        self.assertEqual(m["source_transform"]["tool"], "knockout")
        self.assertEqual(self.c.get("/projects/prep/files/sources/sheet_a.png").status_code, 200)    # original kept
        r = self.c.post("/projects/prep/cutout", json={"files": ["missing.png"], "engine": "rembg"})
        self.assertEqual(r.status_code, 202)
        j = wait(self.c, r.json())
        self.assertEqual(j["status"], "failed")                                                       # a job error is data, not a crash
        self.assertIn("missing.png", j["error"])

    def test_06_safety(self):
        for bad in ("../x.png", "..%2Fx.png", "a/../../b.png"):
            r = self.c.get(f"/projects/harbour/files/images/{bad}")
            self.assertIn(r.status_code, (400, 404, 422))
        self.assertEqual(self.c.post("/projects/harbour/assets/images", files={"file": ("evil.exe", b"MZ", "application/octet-stream")}).status_code, 400)
        self.assertEqual(self.c.post("/projects/harbour/assets/secrets", files={"file": ("a.png", b"x", "image/png")}).status_code, 400)
        self.assertEqual(self.c.get("/projects/Bad%20Id").status_code, 400)
        self.assertEqual(self.c.get("/projects/ghost").status_code, 404)
        self.assertEqual(self.c.get("/projects/harbour/attempts/zz").status_code, 400)
        r = self.c.post("/projects", json={"id": "up"})
        small = TestClient(create_app(settings(self.td.name, max_upload_mb=0)))
        self.assertEqual(small.post("/projects/up/assets/images", files={"file": ("a.png", b"0123456789", "image/png")}).status_code, 413)
        small.close()
        self.assertEqual(self.c.get("/projects/up").json()["assets"]["images"], 0)                   # the partial file was removed

    def test_07_host_llm_generates_a_plan_with_a_fake_runner(self):
        calls = []

        def fake(prompt, cwd, timeout, tools):
            calls.append(prompt)
            target = Path(prompt.split("Write ONE JSON file: ")[1].split(" - a book plan")[0])
            ids = [a for a in ("img01", "img02", "img03", "img04", "img05", "img06")]
            if len(calls) == 1:                                   # first answer is wrong (unknown asset), the API must retry with the error
                p = plan_for(ids)
                p["pages"][1]["assets"][0] = "ghost"
            else:
                p = plan_for(ids)
            target.write_text(json.dumps(p), encoding="utf-8")
            return 0, "done"
        with tempfile.TemporaryDirectory() as td:
            c = TestClient(create_app(settings(td), llm_runner=fake))
            c.post("/projects", json={"id": "llm", "brief": "# T\ndomain: photography\n"})
            for p in sorted(FIX.glob("*.png")):
                c.post("/projects/llm/assets/images", files={"file": (p.name, p.read_bytes(), "image/png")})
            j = wait(c, c.post("/projects/llm/book-plan/generate", json={"instructions": "calm tone", "compose": {}}).json())
            self.assertEqual(j["status"], "succeeded", j.get("error"))
            self.assertEqual(j["result"]["attempts"], 2)
            self.assertIn("calm tone", calls[0])
            self.assertIn("ghost", calls[1])                      # the rejection reason went back to the host
            self.assertTrue(j["result"]["compose"]["gate_pass"])
            self.assertEqual(c.get("/projects/llm/book-plan").json()["doc_title"], "Winter Harbour Series")
            c.close()

    def test_08_job_history_survives_a_restart(self):
        with tempfile.TemporaryDirectory() as td:
            c = TestClient(create_app(settings(td)))
            c.post("/projects", json={"id": "z"})
            j = wait(c, c.post("/projects/z/compose", json={}).json())          # no plan -> failed, recorded
            self.assertEqual(j["status"], "failed")
            c.close()
            c2 = TestClient(create_app(settings(td)))
            self.assertEqual(c2.get("/jobs", params={"project": "z"}).json()[0]["id"], j["id"])
            c2.close()


class TestContract(unittest.TestCase):
    def test_openapi_json_is_current(self):
        p = subprocess.run([sys.executable, str(API / "scripts" / "export_openapi.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr or p.stdout)

    def test_only_the_gateway_imports_the_agents(self):
        bad = []
        for f in (API / "src" / "pascal_api").rglob("*.py"):
            if f.name in ("agents.py", "_boot.py"):
                continue
            if re.search(r"^\s*(from|import)\s+portfolio_agent", f.read_text(encoding="utf-8"), re.M):
                bad.append(str(f.relative_to(API)))
        self.assertEqual(bad, [], "gateways/agents.py is the ONLY module that imports portfolio_agent; everything else goes through it")

    def test_every_domain_package_has_router_and_no_cross_router_imports(self):
        src = API / "src" / "pascal_api"
        for dom in ("projects", "sources", "plans", "books", "reviews", "jobs", "catalog"):
            self.assertTrue((src / dom / "router.py").is_file(), dom)
            text = (src / dom / "router.py").read_text(encoding="utf-8")
            for other in ("projects", "sources", "plans", "books", "reviews", "jobs", "catalog"):
                if other != dom:
                    self.assertNotIn(f"from ..{other}.router", text, f"{dom} must not import {other}'s router")


if __name__ == "__main__":
    unittest.main()
