import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from pascal_api.config import Settings
from pascal_api.exceptions import ApiError
from pascal_api.main import create_app
from pascal_api.plans import service as plans
from pascal_api.storage.projects import ProjectStore
from PIL import Image


class StorageRegressions(unittest.TestCase):
    def test_duplicate_upload_preserves_original_even_when_too_large(self):
        with tempfile.TemporaryDirectory() as td:
            store = ProjectStore(Path(td))
            store.create("sample")
            original = store.add_asset("sample", "images", "a.png", io.BytesIO(b"original"), 100)
            with self.assertRaises(ApiError) as caught:
                store.add_asset("sample", "images", "a.png", io.BytesIO(b"x" * 11), 10)
            self.assertEqual(caught.exception.status, 409)
            self.assertEqual(original.read_bytes(), b"original")
            with self.assertRaises(ApiError) as caught:
                store.add_asset("sample", "images", "b.png", io.BytesIO(b"x" * 11), 10)
            self.assertEqual(caught.exception.status, 413)
            self.assertFalse((original.parent / "b.png").exists())

    def test_tiff_uploads_are_included_in_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Settings(Path(td), "claude", 100, 30, 1, ())
            with TestClient(create_app(settings)) as client:
                client.post("/projects", json={"id": "sample"})
                for ext in ("tif", "tiff"):
                    buf = io.BytesIO()
                    Image.new("RGB", (13, 7), "white").save(buf, "TIFF")
                    response = client.post("/projects/sample/assets/images", files={"file": (f"image-{ext}.{ext}", buf.getvalue(), "image/tiff")})
                    self.assertEqual(response.status_code, 201)
                assets = client.get("/projects/sample/manifest").json()["manifest"]["assets"]
                self.assertEqual({a["id"] for a in assets}, {"image-tif", "image-tiff"})
                self.assertTrue(all((a["width"], a["height"]) == (13, 7) for a in assets))

    def test_rapid_plan_saves_preserve_each_prior_version(self):
        with tempfile.TemporaryDirectory() as td, patch.object(plans.agents, "validate_plan"):
            root = Path(td)
            with patch.object(plans.time, "strftime", return_value="fixed"):
                for n in range(3):
                    plans.write(root, {"pages": [n]})
            previous = [json.loads(p.read_text(encoding="utf-8"))["pages"][0] for p in (root / "plans").glob("book-plan-*.json")]
            self.assertCountEqual(previous, [0, 1])


if __name__ == "__main__":
    unittest.main()
