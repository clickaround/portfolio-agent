import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_installed_resources_and_user_data_are_separate(tmp_path):
    import portfolio_agent.core.workspace as workspace

    module = tmp_path / "isolated_workspace.py"
    shutil.copyfile(workspace.__file__, module)
    data = tmp_path / "portfolio_runtime_data"
    data.mkdir()
    (data / "__init__.py").write_text("", encoding="utf-8")
    user = tmp_path / "user-data"
    env = os.environ.copy()
    env.pop("PASCAL_WORKSPACE", None)
    env["PASCAL_DATA_DIR"] = str(user)
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]); import isolated_workspace as w; "
        "print(w.WORKSPACE); print(w.CACHE_DIR); print(w.CASES_APPROVED_DIR)"
    )
    result = subprocess.run([sys.executable, "-I", "-c", code, str(tmp_path)], env=env, text=True, capture_output=True, check=True)
    lines = result.stdout.splitlines()
    assert Path(lines[0]) == data
    assert Path(lines[1]) == user / "cache"
    assert Path(lines[2]) == user / "cases" / "approved"
