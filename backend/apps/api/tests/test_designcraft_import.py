import hashlib
import io
import json
import time
import zipfile
from types import SimpleNamespace
from unittest.mock import patch

import fitz
import pytest
from fastapi.testclient import TestClient
from pascal_api.books import native_import
from pascal_api.books.native_import import _validate_native_archive
from pascal_api.config import Settings
from pascal_api.main import create_app


def native_zip(name="document.json", body=b"{}", *, symlink=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if symlink:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            archive.writestr(info, body)
        else:
            archive.writestr(name, body)
    return buf.getvalue()


def fake_render(native, pdf):
    assert zipfile.is_zipfile(native)
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Edited page")
    doc.save(pdf)
    doc.close()


def wait(client, job):
    for _ in range(100):
        result = client.get(f"/jobs/{job}").json()
        if result["status"] in ("succeeded", "failed"):
            return result
        time.sleep(.05)
    raise AssertionError("job timed out")


def parent_manifest(project, attempt, path="images/original.png", expected=None):
    asset = project / "images" / "original.png"
    asset.write_bytes(b"original source")
    digest = expected or hashlib.sha256(b"original source").hexdigest()
    (attempt / "manifest.json").write_text(json.dumps({"assets": [{"relative_path": path, "sha256": digest}]}), encoding="utf-8")


def test_import_renders_new_attempt_but_blocks_unverified_finalization(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        edited = native_zip()
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edited.designcraft", edited, "application/octet-stream")})
        assert response.status_code == 202, response.text
        result = wait(client, response.json()["job"])
        assert result["status"] == "succeeded", result
        assert result["result"]["attempt"] == "02"
        imported = project / "out" / "attempts" / "02"
        meta = json.loads((imported / "import.json").read_text(encoding="utf-8"))
        assert meta["parent_relation"] == "comparison_only" and meta["derivation_verified"] is False
        assert meta["source_evidence"]["status"] == "verified"
        ledger = [json.loads(line) for line in (old.parent / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        assert ledger[-1]["attempt"] == "02" and ledger[-1]["plan_sha256"] is None
        assert ledger[-1]["blocking"] == ["NATIVE_EDIT_UNVERIFIED"]
        assert not (imported / "ledger-pending.json").exists()
        assert (old / "book.designcraft").read_bytes() == b"original"
        item = client.get("/projects/demo/attempts/02").json()
        assert item["gate_pass"] is False
        assert any(i["code"] == "NATIVE_EDIT_UNVERIFIED" for i in item["blocking"])
        assert not any(i["code"] == "SOURCE_PROVENANCE_UNVERIFIED" for i in item["blocking"])
        assert client.get("/projects/demo/attempts/02/book.pdf").content.startswith(b"%PDF")
        assert client.get("/projects/demo/attempts/02/pages/1.png").content.startswith(b"\x89PNG")
        ctx = client.post("/projects/demo/review/context").json()
        assert ctx["attempt"] == "02" and "book.designcraft" in ctx["outputs"] and "book.pdf" in ctx["outputs"]
        assert client.post("/projects/demo/review/finalize").status_code == 422
        # Synthetic test attestations exercise the authorization path; they are not a real human review.
        review = {"review_context_sha256": ctx["review_context_sha256"], "frame_hashes": ctx["frames"],
                  "reviewed_frames": list(ctx["frames"]), "reviewer_mode": "human", "blockers": [],
                  "dimension_scores": {name: 0.9 for name in ("hierarchy", "composition_balance", "whitespace_intent", "typography", "sequence_narrative", "asset_fidelity", "domain_fit", "anti_template")},
                  "native_edit_confirmation": {"reviewed_exported_pages": True, "content_and_source_fidelity_confirmed": True, "page_geometry_and_clipping_confirmed": True}}
        assert client.post("/projects/demo/review/record", json={"review": review}).status_code == 200
        finalized = client.post("/projects/demo/review/finalize")
        assert finalized.status_code == 200, finalized.text
        assert finalized.json()["native_edit_human_attested"] is True
        assert (project / "out" / "final" / "book.designcraft").read_bytes() == edited


def test_ledger_failure_preserves_attempt_and_recoverable_entry(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render), \
         patch("pascal_api.books.native_import._append_ledger", side_effect=OSError("disk full")):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edited.designcraft", native_zip(), "application/octet-stream")})
        result = wait(client, response.json()["job"])
        assert result["status"] == "failed" and "ledger pending" in result["error"]
        attempt = old.parent / "02"
        assert (attempt / "book.designcraft").read_bytes() == native_zip()
        assert json.loads((attempt / "ledger-pending.json").read_text(encoding="utf-8"))["attempt"] == "02"
        assert (old / "book.designcraft").read_bytes() == b"original"
        assert client.get("/projects/demo/attempts/02").json()["ledger_pending"] is True


def test_recover_pending_ledger_is_idempotent_and_preserves_existing_records(tmp_path):
    attempts = tmp_path / "out" / "attempts"
    attempt = attempts / "02"
    attempt.mkdir(parents=True)
    entry = {"attempt": "02", "author": "native_import", "condition": "edited_designcraft", "gate_pass": False,
             "blocking": ["NATIVE_EDIT_UNVERIFIED"], "advisory": [], "plan_sha256": None, "pages": 1, "time": "test"}
    pending = attempt / "ledger-pending.json"
    pending.write_text(json.dumps(entry), encoding="utf-8")
    ledger = attempts / "ledger.jsonl"
    ledger.write_text(json.dumps(entry) + "\n", encoding="utf-8")  # append succeeded before marker cleanup failed
    assert native_import.recover_pending_ledger(tmp_path, "02") == "already_recorded"
    assert not pending.exists()
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1
    assert native_import.recover_pending_ledger(tmp_path, "02") == "already_recorded"


def test_recover_pending_ledger_refuses_conflict_and_partial_line(tmp_path):
    attempts = tmp_path / "out" / "attempts"
    attempt = attempts / "02"
    attempt.mkdir(parents=True)
    pending = attempt / "ledger-pending.json"
    pending.write_text(json.dumps({"attempt": "02", "author": "native_import"}), encoding="utf-8")
    ledger = attempts / "ledger.jsonl"
    for contents in ('{"attempt":"02","author":"other"}\n', '{"attempt":'):
        ledger.write_text(contents, encoding="utf-8")
        with pytest.raises(ValueError):
            native_import.recover_pending_ledger(tmp_path, "02")
        assert pending.exists() and ledger.read_text(encoding="utf-8") == contents


def test_recover_pending_ledger_appends_missing_entry(tmp_path):
    attempt = tmp_path / "out" / "attempts" / "02"
    attempt.mkdir(parents=True)
    entry = {"attempt": "02", "author": "native_import"}
    (attempt / "ledger-pending.json").write_text(json.dumps(entry), encoding="utf-8")
    assert native_import.recover_pending_ledger(tmp_path, "02") == "appended"
    assert json.loads((attempt.parent / "ledger.jsonl").read_text(encoding="utf-8")) == entry


@pytest.mark.parametrize("link_name", ["ledger-pending.json", "ledger.jsonl"])
def test_recovery_rejects_dangling_symlinks_even_when_entry_exists(tmp_path, link_name):
    attempts = tmp_path / "out" / "attempts"
    attempt = attempts / "02"
    attempt.mkdir(parents=True)
    entry = {"attempt": "02", "author": "native_import"}
    target = attempt / link_name if link_name == "ledger-pending.json" else attempts / link_name
    if link_name == "ledger-pending.json":
        (attempts / "ledger.jsonl").write_text(json.dumps(entry) + "\n", encoding="utf-8")
    else:
        (attempt / "ledger-pending.json").write_text(json.dumps(entry), encoding="utf-8")
    try:
        target.symlink_to(tmp_path / "does-not-exist")
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    with pytest.raises(ValueError, match="Linked"):
        native_import.recover_pending_ledger(tmp_path, "02")
    assert target.is_symlink()


def test_recover_ledger_api_is_serialized_origin_checked_and_idempotent(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ("http://localhost:5173",)))
    project = app.state.store.create("demo")
    attempt = project / "out" / "attempts" / "02"
    attempt.mkdir(parents=True)
    entry = {"attempt": "02", "author": "native_import"}
    (attempt / "ledger-pending.json").write_text(json.dumps(entry), encoding="utf-8")
    url = "/projects/demo/attempts/02/recover-ledger"
    with TestClient(app) as client:
        assert client.post(url, headers={"origin": "https://evil.example"}).status_code == 403
        for expected in ("appended", "already_recorded"):
            response = client.post(url, headers={"origin": "http://localhost:5173"})
            assert response.status_code == 202
            result = wait(client, response.json()["job"])
            assert result["status"] == "succeeded" and result["result"]["status"] == expected
        assert client.get("/projects/demo/attempts/02").json()["ledger_pending"] is False
        assert len((attempt.parent / "ledger.jsonl").read_text(encoding="utf-8").splitlines()) == 1


@pytest.mark.parametrize("condition", ["missing_manifest", "changed", "missing_file", "traversal", "transformed_original_changed"])
def test_import_retains_attempt_but_blocks_unverifiable_source(tmp_path, condition):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    if condition != "missing_manifest":
        parent_manifest(project, old, path="../outside.png" if condition == "traversal" else "images/original.png")
    if condition == "changed":
        (project / "images" / "original.png").write_bytes(b"changed")
    if condition == "missing_file":
        (project / "images" / "original.png").unlink()
    if condition == "transformed_original_changed":
        source = project / "sources" / "original.png"
        source.write_bytes(b"different")
        manifest_path = old / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["assets"][0]["source_transform"] = {"source": "sources/original.png", "source_sha256": hashlib.sha256(b"expected").hexdigest()}
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        result = wait(client, response.json()["job"])
        assert result["status"] == "succeeded", result
        assert {i["code"] for i in result["result"]["blocking"]} == {"NATIVE_EDIT_UNVERIFIED", "SOURCE_PROVENANCE_UNVERIFIED"}
        assert (project / "out" / "attempts" / "02" / "book.designcraft").exists()
        assert (old / "book.designcraft").read_bytes() == b"original"
        assert client.post("/projects/demo/review/context").status_code == 422


def test_transformed_original_is_included_in_verified_source_evidence(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    (project / "sources" / "original.png").write_bytes(b"source")
    manifest = json.loads((old / "manifest.json").read_text(encoding="utf-8"))
    manifest["assets"][0]["source_transform"] = {"source": "sources/original.png", "source_sha256": hashlib.sha256(b"source").hexdigest()}
    (old / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        assert wait(client, response.json()["job"])["status"] == "succeeded"
        context = client.post("/projects/demo/review/context")
        assert context.status_code == 200, context.text
        evidence = context.json()["native_edit"]["source_evidence"]
        assert {a["path"] for a in evidence["assets"]} == {"images/original.png", "sources/original.png"}


def test_import_render_failure_does_not_create_attempt(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=RuntimeError("invalid document")):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("bad.designcraft", native_zip(), "application/octet-stream")})
        assert response.status_code == 202
        assert wait(client, response.json()["job"])["status"] == "failed"
        assert not (old.parent / "02").exists()
        assert (old / "book.designcraft").read_bytes() == b"original"


def test_import_rejects_unsafe_archives_before_cli(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf") as render:
        for payload in (b"not zip", native_zip("../document.json"), native_zip("document.json", symlink=True), native_zip("elsewhere.json")):
            response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("bad.designcraft", payload, "application/octet-stream")})
            if response.status_code == 202:
                assert wait(client, response.json()["job"])["status"] == "failed"
            else:
                assert response.status_code in (400, 422)
        render.assert_not_called()
        assert not (old.parent / "02").exists()


def test_archive_limits_and_duplicate_entries(tmp_path):
    path = tmp_path / "input.designcraft"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("document.json", "{}")
        archive.writestr("large.bin", b"0" * (2 * 1024 * 1024))
    with pytest.raises(ValueError, match="decompression limits"):
        _validate_native_archive(path)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("document.json", "{}")
        archive.writestr("DOCUMENT.JSON", "{}")
    with pytest.raises(ValueError, match="Unsafe archive entry"):
        _validate_native_archive(path)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("document.json", "{}")
        archive.writestr("../outside.txt", "bad")
    with pytest.raises(ValueError, match="Unsafe archive entry"):
        _validate_native_archive(path)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("document.json", "{}")
        with archive.open("oversized.bin", "w") as stream:
            for _ in range(129):
                stream.write(b"x" * (1024 * 1024))
    with pytest.raises(ValueError, match="decompression limits"):
        _validate_native_archive(path)


def test_nonfinite_page_dimensions_are_rejected():
    for width, height in ((float("nan"), 20), (20, float("inf")), (-1, 20), (0, 20)):
        with pytest.raises(ValueError):
            native_import._validate_page_size(width, height, 1)


def test_windows_reparse_point_is_treated_as_link():
    path = SimpleNamespace(is_symlink=lambda: False, lstat=lambda: SimpleNamespace(st_file_attributes=0x400))
    assert native_import._is_link_or_reparse(path)


def test_total_page_pixel_budget_blocks_before_attempt_creation(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")

    def oversized(_, pdf):
        document = fitz.open()
        for _ in range(3):
            document.new_page(width=4500, height=4500)
        document.save(pdf)
        document.close()

    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=oversized):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("large.designcraft", native_zip(), "application/octet-stream")})
        result = wait(client, response.json()["job"])
        assert result["status"] == "failed"
        assert "total pixel" in result["error"].lower()
        assert not (old.parent / "02").exists()
        assert (old / "book.designcraft").read_bytes() == b"original"


def test_total_preview_size_budget_blocks_before_attempt_creation(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render), \
         patch("pascal_api.books.native_import.MAX_PREVIEW_BYTES", 1):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        result = wait(client, response.json()["job"])
        assert result["status"] == "failed" and "preview file size" in result["error"]
        assert not (old.parent / "02").exists()
        assert (old / "book.designcraft").read_bytes() == b"original"


def test_import_rejects_wrong_extension_and_oversize_before_job(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 0, 30, 1, ()))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    with TestClient(app) as client:
        url = "/projects/demo/attempts/01/import-designcraft"
        assert client.post(url, files={"file": ("a.pdf", b"x", "application/pdf")}).status_code == 400
        assert client.post(url, files={"file": ("a.designcraft", b"x", "application/octet-stream")}).status_code == 413
        assert not list((project / "out" / ".native-imports").iterdir())
        assert (old / "book.designcraft").read_bytes() == b"original"


def test_suggestions_are_source_bound_read_only_and_become_stale(tmp_path):
    from pathlib import Path
    calls = []
    def analysis_runner(prompt, cwd, timeout, tools):
        calls.append((prompt, Path(cwd), tools))
        assert tools == "" and Path(cwd).is_dir()
        return 0, json.dumps({"summary": "Improve legibility", "pages": [{"page": 1, "suggestions": [{"issue": "Text is small", "recommendation": "Increase type", "evidence": "Page 1 heading"}]}]})
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()), analysis_runner=analysis_runner)
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        assert wait(client, response.json()["job"])["status"] == "succeeded"
        assert client.get("/projects/demo/attempts/02").json()["native_edit"] is True
        request = client.post("/projects/demo/attempts/02/suggestions", json={"instructions": "Check type", "source_kind": "synthetic"})
        assert request.status_code == 202, request.text
        result = wait(client, request.json()["job"])
        assert result["status"] == "succeeded", result
        suggestion_id = result["result"]["suggestion_id"]
        url = f"/projects/demo/attempts/02/suggestions/{suggestion_id}"
        doc = client.get(url).json()
        assert doc["source_kind"] == "synthetic" and doc["output"]["pages"][0]["page"] == 1
        assert client.get("/projects/demo/attempts/02/suggestions").json()[0]["status"] == "fresh"
        assert not calls[0][1].exists()  # isolated inputs removed after execution
        (project / "images" / "original.png").write_bytes(b"changed")
        assert client.get(url).status_code == 409
        assert client.get("/projects/demo/attempts/02/suggestions").json()[0]["status"] == "stale"


@pytest.mark.parametrize("target", ["source", "preview", "native"])
def test_suggestions_fail_closed_if_sources_change_during_runner(tmp_path, target):
    def changing_runner(prompt, cwd, timeout, tools):
        project_dir = tmp_path / "projects" / "demo"
        path = {"source": project_dir / "images" / "original.png", "preview": project_dir / "out" / "attempts" / "02" / "preview" / "page-01.png", "native": project_dir / "out" / "attempts" / "02" / "book.designcraft"}[target]
        path.write_bytes(b"changed")
        return 0, json.dumps({"summary": "x", "pages": [{"page": 1, "suggestions": []}]})
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()), analysis_runner=changing_runner)
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        response = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        assert wait(client, response.json()["job"])["status"] == "succeeded"
        response = client.post("/projects/demo/attempts/02/suggestions", json={"source_kind": "synthetic"})
        assert wait(client, response.json()["job"])["status"] == "failed"
        assert not list((project / "out" / "suggestions").rglob("*.json")) if (project / "out" / "suggestions").exists() else True


def test_text_analysis_runner_disables_all_tools(tmp_path):
    from types import SimpleNamespace

    from pascal_api.gateways.llm import make_read_only_claude_runner
    with patch("pascal_api.gateways.llm.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="{}", stderr="")) as run:
        prompt = "가" * 120_000
        assert make_read_only_claude_runner("claude")(prompt, tmp_path, 5, "") == (0, "{}")
        command = run.call_args.args[0]
        assert prompt not in command and run.call_args.kwargs["input"] == prompt
        assert command[command.index("--tools") + 1] == ""
        assert "--restricted" in command and command[command.index("--permission-prompts") + 1] == "none"
        with pytest.raises(ValueError):
            make_read_only_claude_runner("claude")("prompt", tmp_path, 5, "Read")


def test_suggestion_rejects_tampered_output(tmp_path):
    def runner(prompt, cwd, timeout, tools):
        return 0, json.dumps({"summary": "Original", "pages": [{"page": 1, "suggestions": []}]})
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ()), analysis_runner=runner)
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        imported = client.post("/projects/demo/attempts/01/import-designcraft", files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        assert wait(client, imported.json()["job"])["status"] == "succeeded"
        job = client.post("/projects/demo/attempts/02/suggestions", json={})
        record_id = wait(client, job.json()["job"])["result"]["suggestion_id"]
        path = project / "out" / "suggestions" / "02" / f"{record_id}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["output"]["summary"] = "Tampered"
        path.write_text(json.dumps(record), encoding="utf-8")
        assert client.get(f"/projects/demo/attempts/02/suggestions/{record_id}").status_code == 409
        assert client.get("/projects/demo/attempts/02/suggestions").json()[0]["status"] == "stale"


def test_import_rejects_untrusted_browser_origin_but_allows_configured_and_cli(tmp_path):
    app = create_app(Settings(tmp_path, "claude", 1, 30, 1, ("http://localhost:5173",)))
    project = app.state.store.create("demo")
    old = project / "out" / "attempts" / "01"
    old.mkdir(parents=True)
    (old / "book.designcraft").write_bytes(b"original")
    parent_manifest(project, old)
    with TestClient(app) as client, patch("pascal_api.gateways.agents.render_designcraft_pdf", side_effect=fake_render):
        url = "/projects/demo/attempts/01/import-designcraft"
        def send(origin):
            headers = {"origin": origin} if origin else {}
            return client.post(url, headers=headers, files={"file": ("edit.designcraft", native_zip(), "application/octet-stream")})
        assert send("https://evil.example").status_code == 403
        assert wait(client, send("http://localhost:5173").json()["job"])["status"] == "succeeded"
        assert wait(client, send(None).json()["job"])["status"] == "succeeded"
