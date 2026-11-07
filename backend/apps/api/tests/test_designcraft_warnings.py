import json

from fastapi.testclient import TestClient
from pascal_api.config import Settings
from pascal_api.main import create_app


def test_attempt_exposes_designcraft_notes_and_unverified_status(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 100, 30, 1, ()))
    project = app.state.store.create("demo")
    attempt = project / "out" / "attempts" / "01"
    attempt.mkdir(parents=True)
    (attempt / "book.designcraft").write_bytes(b"native")
    (attempt / "qa.json").write_text(json.dumps({"gate_pass": True, "extra_exporters": {"designcraft": {"exit": 0, "notes": ["crop not applied"]}}}), encoding="utf-8")
    with TestClient(app) as client:
        data = client.get("/projects/demo/attempts/01").json()
        assert data["gate_pass"] is True
        assert data["designcraft"]["status"] == "unverified"
        assert data["designcraft"]["notes"] == ["crop not applied"]
        assert client.get("/projects/demo/attempts").json()[0]["designcraft"] == data["designcraft"]


def test_attempt_without_designcraft_has_no_native_status(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 100, 30, 1, ()))
    project = app.state.store.create("demo")
    (project / "out" / "attempts" / "01").mkdir(parents=True)
    with TestClient(app) as client:
        assert client.get("/projects/demo/attempts/01").json()["designcraft"] is None
