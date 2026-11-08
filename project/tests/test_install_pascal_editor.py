import importlib.util
from pathlib import Path

import pytest


def load_installer():
    path = Path(__file__).resolve().parents[1] / "scripts" / "install_pascal_editor.py"
    spec = importlib.util.spec_from_file_location("install_pascal_editor", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_installer_publishes_and_updates_only_its_own_directory(tmp_path, monkeypatch):
    installer = load_installer()
    source = tmp_path / "build"
    target = tmp_path / "public" / "pascal-editor"
    source.mkdir()
    (source / "index.html").write_text("first")
    (source / "app.wasm").write_bytes(b"wasm")
    monkeypatch.setattr(installer, "SOURCE", source)
    monkeypatch.setattr(installer, "TARGET", target)
    target.mkdir(parents=True)
    (target / "user.txt").write_text("preserve")
    with pytest.raises(RuntimeError, match="unmanaged"):
        installer.main()
    assert (target / "user.txt").read_text() == "preserve"
    (target / "user.txt").unlink()
    target.rmdir()
    installer.main()
    assert (target / "LICENSE-MIT").is_file()
    assert (target / "NOTICE").is_file()
    assert list((target / "assets" / "fonts").glob("OFL-*.txt"))
    (source / "index.html").write_text("second")
    installer.main()
    assert (target / "index.html").read_text() == "second"
