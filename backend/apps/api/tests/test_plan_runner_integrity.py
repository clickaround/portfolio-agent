import json
from pathlib import Path

import pytest
from pascal_api.plans import service


def test_failed_runner_cannot_promote_a_file_it_wrote(tmp_path, monkeypatch):
    (tmp_path / "project.md").write_text("Synthetic brief", encoding="utf-8")
    monkeypatch.setattr(service.agents, "ingest", lambda _project: ({"assets": []}, None))
    monkeypatch.setattr(service.agents, "plan_resources", lambda: {"skill": Path("skill"), "craft": Path("craft"), "schema": Path("schema")})
    monkeypatch.setattr(service.agents, "validate_plan", lambda _project, _plan: None)
    calls = []

    def failed_runner(_prompt, project, _timeout, _tools):
        calls.append(1)
        (project / "plans" / "_generated.json").write_text(json.dumps({"pages": [{"role": "cover"}]}), encoding="utf-8")
        return 1, "CLAUDE_USAGE_LIMIT"

    with pytest.raises(RuntimeError, match="사용 한도"):
        service.generate(tmp_path, failed_runner, 30, "Synthetic", lambda _message: None)
    assert len(calls) == 1
    assert not (tmp_path / "book-plan.json").exists()
    assert not (tmp_path / "plans" / "_generated.json").exists()
