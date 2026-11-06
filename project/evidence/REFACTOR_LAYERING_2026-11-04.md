# Refactor to layered modules (2026-11-04) - evidence
Why: flat `runtime/portfolio_agent/*.py` mixed layout, rendering, gates, domain data and orchestration (render.py held global style state; qa.py imported render; patterns.json lived in code; adapters imported by ad-hoc sys.path). Multiple backends/authors/domains would have made it unmaintainable.
Before -> after:
- ingest.py -> core/assets.py | qa.py -> core/gates.py (measurer injected) | repair.py -> core/repair.py | diagnostics.py -> core/diagnostics.py | new core/{contracts,geometry,conventions,paths,legacy_checks}.py
- plan.py, layout.py, treelayout.py -> authors/rule_based/ (+ RuleBasedAuthor: pattern retrieval, pagination, hero search, relayout) | cases.py -> authors/knowledge.py | new authors/host/ (B4 loader)
- pipeline.py (slimmed to orchestration), edit.py (author.relayout instead of layout import), candidates.py, new engine/{registry,spec,ingest_view}.py
- render.py -> backends/local/adapter.py (LocalBackend: measurer + exporter, state on the instance) | designcraft adapter wrapped as DesignCraftBackend | patterns.json -> knowledge/patterns/layout-patterns.json
- cli.py talks to engine only; new commands `check-scenes`, `manifest`, `backends`; `--also <backend>` for extra exporters.
Verification: `python -m unittest discover -s tests` = 40 tests OK, 0 skipped (incl. 9 architecture tests: dependency direction, closed top-level folder list, package __init__, no data files inside code, backend shape, detector self-test); package validator PASS; ArchPortfolioBench AP-05..08 rerun with identical outcomes as before the refactor (AP-05 2/10, AP-06 8/8, AP-07 3/3, AP-08 3/3).
Not verified: behaviour on non-architecture domains beyond pattern selection; Codex host; the layering test only checks imports (not runtime coupling through dict conventions).
