"""Enforces the layering (backend/common/ARCHITECTURE.md; the Python analogue of DesignCraft's `cargo xtask layers`) across ALL source roots
of the portfolio_agent namespace package, and the workspace folder rules (agents / backend / frontend / project).

    core (backend/common)  <-  layout  <-  authors/*, backends/*  <-  engine (portfolioAgent + sourcePrepAgent + reviewAgent)  <-  cli
"""
import ast
import unittest
from pathlib import Path

import pascal_bootstrap

WORKSPACE = pascal_bootstrap.setup()
SOURCE_ROOTS = pascal_bootstrap.SOURCE_ROOTS
HUB = WORKSPACE / "agents" / "portfolio-agents"
BACKENDS = HUB / "portfolioAgent" / "backends"
TOP_LEVEL_ALLOWED = {
    "agents", "backend", "frontend", "project",          # the four product folders (SPLIT_PLAN.md)
    "_bmad", "_bmad-output",                              # BMAD planning tool output
    ".agents", ".cache", ".git", ".remember", ".pytest_cache", ".claude", ".vscode", ".idea",
}
NAMESPACE_DIRS = {"portfolio_agent", "engine"}            # PEP 420: spread over several agents, so no __init__.py


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
    for root in SOURCE_ROOTS:
        pkg = root / "portfolio_agent"
        if not pkg.is_dir():
            continue
        for p in sorted(pkg.rglob("*.py")):
            rel = p.relative_to(root).with_suffix("")
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
        for adapter in sorted(BACKENDS.glob("*/adapter.py")):
            for imp in imports_of(adapter, f"pa_backend_{adapter.parent.name}"):
                if imp.startswith("portfolio_agent") and layer_of(imp) not in ("core",) and imp != "portfolio_agent":
                    bad.append(f"{adapter.parent.name} imports {imp}")
                if imp.startswith("pa_backend_"):
                    bad.append(f"{adapter.parent.name} imports another backend {imp}")
        self.assertEqual(bad, [])

    def test_every_backend_exposes_BACKEND_with_declared_capabilities(self):
        from importlib import util
        for adapter in sorted(BACKENDS.glob("*/adapter.py")):
            src = adapter.read_text(encoding="utf-8")
            self.assertIn("BACKEND =", src, adapter)
            self.assertIn("capabilities", src, adapter)


class AgentFolderTests(unittest.TestCase):
    def test_source_prep_and_review_agents_import_only_core(self):
        bad = []
        for agent in ("sourcePrepAgent", "reviewAgent"):
            for p in sorted((HUB / agent / "src").rglob("*.py")):
                mod = ".".join(p.relative_to(HUB / agent / "src").with_suffix("").parts)
                for imp in imports_of(p, mod):
                    if imp.startswith("portfolio_agent") and layer_of(imp) not in ("core", None):
                        bad.append(f"{agent}: {mod} imports {imp}")
        self.assertEqual(bad, [], "sourcePrepAgent / reviewAgent depend on backend/common (core) only, never on portfolioAgent")

    def test_agent_folders_are_self_describing(self):
        for agent in ("portfolioAgent", "sourcePrepAgent", "reviewAgent"):
            self.assertTrue((HUB / agent / "AGENTS.md").is_file(), f"{agent}/AGENTS.md (identity, contract, how to test) is required")
            self.assertTrue((HUB / agent / "tests").is_dir(), f"{agent}/tests")


class FolderTests(unittest.TestCase):
    def test_top_level_folders_are_documented(self):
        actual = {p.name for p in WORKSPACE.iterdir() if p.is_dir() and any(p.iterdir())}   # an empty leftover dir (locked by an editor on Windows) is harmless
        self.assertEqual(sorted(actual - TOP_LEVEL_ALLOWED), [], "new top-level folder: it must be one of agents/backend/frontend/project (see SPLIT_PLAN.md)")

    def test_every_package_dir_has_init_except_namespace_dirs(self):
        missing = []
        for root in SOURCE_ROOTS:
            pkg = root / "portfolio_agent"
            if not pkg.is_dir():
                continue
            for d in [pkg, *pkg.rglob("*")]:
                if d.is_dir() and d.name != "__pycache__" and any(d.glob("*.py")) and not (d / "__init__.py").exists() and d.name not in NAMESPACE_DIRS:
                    missing.append(str(d.relative_to(WORKSPACE)))
        self.assertEqual(missing, [])

    def test_no_namespace_dir_has_init(self):
        bad = [str(root / "portfolio_agent" / n) for root in SOURCE_ROOTS for n in ("", "engine") if (root / "portfolio_agent" / n / "__init__.py").exists()]
        self.assertEqual(bad, [], "portfolio_agent and portfolio_agent.engine are PEP 420 namespaces: an __init__.py would hide the other agents' modules")

    def test_no_data_files_inside_source_roots(self):
        data = [str(p.relative_to(WORKSPACE)) for root in SOURCE_ROOTS for p in root.rglob("*") if p.is_file() and p.suffix in (".json", ".csv", ".txt") and "__pycache__" not in p.parts]
        self.assertEqual(data, [], "data belongs in knowledge/, contracts/ - not inside code")


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
