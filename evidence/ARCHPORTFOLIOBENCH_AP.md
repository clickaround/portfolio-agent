# ArchPortfolioBench (designed) - engine-only subset, run 2026-11-04 (SYNTHETIC; report: benchmarks/reports/apbench-20261104-212821.json)
Source of truth: benchmarks/SPEC.md + PROTO_V3.md. This run covers ONLY AP-03, 05, 06, 07, 08 for the local compositor (+DesignCraft export). Not the B0-B5 host comparison, not AP-01/02/04/09/10, no blind human review, no real cases. The earlier `engine_regression_bench.py` (formerly misnamed ArchPortfolioBench v0) is a tuned regression test, not evidence of quality.
| Task | Result (3 synthetic projects) |
|---|---|
| AP-03 A3 landscape book | page size exact + gates pass 3/3; "2-page" requirement NOT met (3-5 pages: engine refuses silent asset drop) |
| AP-05 enlarge one graphic 20% | 2 / 10 attempts committed (only pages with free space, area x1.16-1.36, neighbours reflowed and declared); 8 refused safely (page already full); 0 unsafe commits |
| AP-06 triple a caption | 8 / 8 committed via bounded repair (font shrink); not checked: whether shrunk text is still comfortably readable |
| AP-07 revise page 2 only | 3 / 3: other pages byte-identical renders |
| AP-08 PDF + editable artifact | 3 / 3: PDF opens, PPTX opens in python-pptx with named, editable text boxes/pictures, scene JSON valid vs contracts schema, DesignCraft export exit 0 (.designcraft/PDF/IDML/PPTX exist); PowerPoint/InDesign opening and preview parity NOT checked |
Weaknesses of this evidence: fixtures synthetic and tiny (n=3), I wrote both engine and tests, no independent reviewer, AP-05 target choice (smallest graphic) favours success.
