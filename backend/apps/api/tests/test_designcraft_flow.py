from unittest.mock import patch

from fastapi.testclient import TestClient
from pascal_api.config import Settings
from pascal_api.main import create_app
from portfolio_agent.engine.pipeline import _record_attempt


def test_native_export_is_preserved_per_attempt_and_downloadable(tmp_path):
    settings = Settings(tmp_path, "claude", 100, 30, 1, ())
    app = create_app(settings)
    project = app.state.store.create("demo")
    out = project / "out"
    (out / "scenes").mkdir(parents=True)
    (out / "designcraft").mkdir()
    (out / "designcraft" / "book.designcraft").write_bytes(b"native-first")
    (out / "plan.json").write_text("{}")
    report = {"author": "planned", "condition": None, "project": "demo", "gate_pass": True, "blocking_issues": [], "advisory_issues": [], "pages": 1, "repairs": [], "backend": "local", "extra_exporters": {"designcraft": {"exit": 0, "files": {"native": str(out / "designcraft" / "book.designcraft")}}}}
    first = _record_attempt(out, report, {})
    (out / "designcraft" / "book.designcraft").write_bytes(b"native-second")
    second = _record_attempt(out, report, {})
    with TestClient(app) as client:
        assert client.get(f"/projects/demo/attempts/{first}").json()["files"]["book.designcraft"]
        assert client.get(f"/projects/demo/attempts/{first}/book.designcraft").content == b"native-first"
        assert client.get(f"/projects/demo/attempts/{second}/book.designcraft").content == b"native-second"
        assert client.get(f"/projects/demo/attempts/{first}/book.exe").status_code == 404


def test_open_editor_requires_trusted_local_origin(tmp_path):
    settings = Settings(tmp_path, "claude", 100, 30, 1, ("http://localhost:5173",))
    app = create_app(settings)
    project = app.state.store.create("demo")
    att = project / "out" / "attempts" / "01"
    att.mkdir(parents=True)
    (att / "book.designcraft").write_bytes(b"native")
    with TestClient(app, client=("127.0.0.1", 1234)) as client, patch("pascal_api.books.router.agents.open_designcraft", return_value={"opened": True, "edit_path": "local", "message": "saved separately"}) as launch:
        assert client.post("/projects/demo/attempts/01/open-designcraft", headers={"origin": "https://evil.example"}, json={}).status_code == 403
        assert client.post("/projects/demo/attempts/01/open-designcraft", headers={"origin": "http://localhost:5173"}, json={}).status_code == 200
        launch.assert_called_once()
