> **ARCHIVED V2; historical validation only.** Current v3 authoritative docs: GOALS.md, PLANS.md, architecture/ARCHITECTURE_MAP.md, formats/, research/repos.lock.json.

# VALIDATION_REPORT_V2 — 2026-11-04

This reports **actual scaffold-only checks executed in the construction container**. The user's Claude/Codex installation and external design engines were NOT tested.

| Test | Observed result | Scope |
|---|---|---|
| `python scripts/validate_package.py` | PASS, errors=0 | JSON readability, portable manifest fields, skill frontmatter, 65-task DAG and evidence-state policy, repository pins, no compiled bytecode |
| `python -m unittest discover -s tests -v` | PASS, 15 tests | synthetic geometry, NaN/boolean injection, source reference, global overlap bypass, local edit diff, file SHA, evidence gate negative tests |
| `python scripts/validate_contracts.py` | PASS, 5 fixtures validated | optional jsonschema package installed in author container; semantic contracts only for supplied synthetic examples |
| `python scripts/task_status.py --ready` | one task ready: T000 | no task silently marked done |
| `python scripts/check_layout.py examples/SYNTHETIC_scene.json --asset-manifest examples/SYNTHETIC_asset-manifest.json` | PASS (0 issues) | synthetic geometry/reference only; referenced PDF is intentionally fictitious |
| `python scripts/check_layout.py examples/SYNTHETIC_scene_invalid.json` | exit 1, expected invalid | bbox overflow + overlap negative control |

**NOT RUN:** Claude plugin validate/installation; Codex marketplace install; external GitHub clone/CLI samples; LLM generation; real-world portfolio expert ratings; vector PDF round-trip; controlled B0–B3; HarnessRouter/UHP. No corresponding quality or business success claims are made.

**Important:** `jsonschema` is optional, not part of the zero-dependency bootstrap; the additional contract check will return SKIPPED in environments where it is absent. It must never be reported as PASSED if skipped.
