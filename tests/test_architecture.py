"""Enforces the layering in runtime/ARCHITECTURE.md (the Python analogue of DesignCraft's `cargo xtask layers`).

    core  <-  layout  <-  authors/*, backends/*  <-  engine  <-  cli
"""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "runtime" / "portfolio_agent"
TOP_LEVEL_ALLOWED = {
    # design package
    "agents", "architecture", "backends", "benchmarks", "cases", "contracts", "core", "docs", "examples", "formats", "integrations", "knowledge", "memory", "plans",
    "prompts", "research", "runtime", "scripts", "skills", "tasks", "tests",
    # added during implementation (documented in architecture/ARCHITECTURE_MAP.md)
    "evidence", "preview", ".pytest_cache", ".git",   # (.pytest_cache: tool cache, ignored; .git: version control)
    # host/tooling dot-folders
    ".agents", ".claude-plugin", ".codex-plugin", ".cache", ".remember",
}


def imports_of(path, module_name):
    """All absolute module names imported by `path` (relative imports resolved against module_name)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    pkg_parts = module_name.split(".")[:-1] if path.name != "__init__.py" else module_name.split(".")
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg_parts[: len(pkg_parts) - (n.level - 1)]
                mod = ".".join(base + ([n.module] if n.module else []))
                out.append(mod)
                out += [mod + "." + a.name for a in n.names]
            elif n.module:
                out.append(n.module)
                out += [n.module + "." + a.name for a in n.names]
    return out


def package_modules():
    for p in sorted(PKG.rglob("*.py")):
        rel = p.relative_to(PKG.parent).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        yield p, ".".join(parts)


def layer_of(mod):
    if mod.startswith("portfolio_agent.core"):
        return "core"
    if mod.startswith("portfolio_agent.layout"):
        return "layout"
    if mod.startswith("portfolio_agent.authors"):
        return "authors"
    if mod.startswith("portfolio_agent.engine"):
        return "engine"
    if mod == "portfolio_agent.cli":
        return "cli"
    return None


class LayeringTests(unittest.TestCase):
    def violations(self, layer, forbidden, extra=None):
        bad = []
        for p, mod in package_modules():
            if layer_of(mod) != layer:
                continue
            for imp in imports_of(p, mod):
                tgt = layer_of(imp)
                if tgt in forbidden or (extra and extra(mod, imp)):
                    bad.append(f"{mod} imports {imp}")
        return bad

    def test_core_imports_no_other_layer(self):
        self.assertEqual(self.violations("core", {"layout", "authors", "engine", "cli"}), [])

    def test_layout_imports_only_core(self):
        self.assertEqual(self.violations("layout", {"authors", "engine", "cli"}), [])

    def test_authors_import_only_core_and_never_each_other(self):
        def cross_author(mod, imp):
            a, b = mod.split(".")[2:3], imp.split(".")[2:3]
            return imp.startswith("portfolio_agent.authors.") and mod.startswith("portfolio_agent.authors.") and a and b and a != b and a[0] not in ("knowledge",) and b[0] not in ("knowledge",)
        self.assertEqual(self.violations("authors", {"engine", "cli"}, cross_author), [])

    def test_engine_does_not_import_cli_and_only_registry_imports_authors(self):
        def authors_outside_registry(mod, imp):
            return imp.startswith("portfolio_agent.authors") and not mod.endswith("engine.registry")
        self.assertEqual(self.violations("engine", {"cli"}, authors_outside_registry), [])

    def test_cli_talks_to_engine_only(self):
        self.assertEqual(self.violations("cli", {"core", "authors"}), [])

    def test_backends_import_only_core_of_the_package(self):
        bad = []
        for adapter in sorted((ROOT / "backends").glob("*/adapter.py")):
            for imp in imports_of(adapter, f"pa_backend_{adapter.parent.name}"):
                if imp.startswith("portfolio_agent") and layer_of(imp) not in ("core",) and imp != "portfolio_agent":
                    bad.append(f"{adapter.parent.name} imports {imp}")
                if imp.startswith("pa_backend_"):
                    bad.append(f"{adapter.parent.name} imports another backend {imp}")
        self.assertEqual(bad, [])

    def test_every_backend_exposes_BACKEND_with_declared_capabilities(self):
        from importlib import util
        for adapter in sorted((ROOT / "backends").glob("*/adapter.py")):
            src = adapter.read_text(encoding="utf-8")
            self.assertIn("BACKEND =", src, adapter)
            self.assertIn("capabilities", src, adapter)


class FolderTests(unittest.TestCase):
    def test_top_level_folders_are_documented(self):
        actual = {p.name for p in ROOT.iterdir() if p.is_dir()}
        self.assertEqual(sorted(actual - TOP_LEVEL_ALLOWED), [], "new top-level folder: document it in architecture/ARCHITECTURE_MAP.md and add it to TOP_LEVEL_ALLOWED")

    def test_every_package_dir_has_init(self):
        missing = [str(d.relative_to(ROOT)) for d in PKG.rglob("*") if d.is_dir() and d.name != "__pycache__" and any(d.glob("*.py")) and not (d / "__init__.py").exists()]
        self.assertEqual(missing, [])

    def test_no_runtime_data_files_inside_the_package(self):
        data = [str(p.relative_to(ROOT)) for p in PKG.rglob("*") if p.is_file() and p.suffix in (".json", ".csv", ".txt")]
        self.assertEqual(data, [], "data belongs in knowledge/, contracts/, formats/ - not inside code")


class DetectorSelfTest(unittest.TestCase):
    """The layering check must actually fail on a violation (negative test)."""

    def test_detects_core_importing_engine_and_relative_imports(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "bad.py"
            f.write_text(chr(10).join(["from portfolio_agent.engine import pipeline", "from ..engine import registry", "import os", ""]), encoding="utf-8")
            imps = imports_of(f, "portfolio_agent.core.bad")
            self.assertIn("portfolio_agent.engine", imps)
            self.assertIn("portfolio_agent.engine.registry", imps)
            self.assertEqual({layer_of(i) for i in imps if layer_of(i)}, {"engine"})


if __name__ == "__main__":
    unittest.main()
