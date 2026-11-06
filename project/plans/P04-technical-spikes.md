# P04 — Backend/PDF technical spikes

 Status: NOT_STARTED. **Canonical per-task specifications live in `tasks/cards/`**, not here; inspect only assigned task. `tasks/backlog.json` is the source of the dependency DAG.

 | Task ID | Scope | Prerequisites | Expected evidence |
 |---|---|---|---|
 | `T400` | A/B/C/D 아키텍처 비교 | T300, T209, T210 | `architecture/ALTERNATIVES_V2.md` |
| `T401` | Vector PDF preservation probe | T209, T302 | `evidence/P04-vector-pdf.md` |
| `T402` | Native layer edit probe | T206, T301 | `evidence/P04-openpencil-edit.md` |
| `T403` | Office layer edit probe | T207, T301 | `evidence/P04-genoffice-edit.md` |
| `T404` | Browser/HTML fallback probe | T301 | `evidence/P04-html-fallback.md` |
| `T405` | 국소 수정 원자성 | T301, T404 | `evidence/P04-local-edit.md` |
| `T406` | 출력 방식 내결함 결정 | T401, T404 | `architecture/OUTPUT_DECISION.md` |
| `T407` | 보안/권한 레드팀 | T301 | `evidence/P04-threat-tests.md` |

 ## Gate
 Every scoped task has observed output or explicit BLOCKED/SKIPPED evidence. Only true PASS is `done`; a failed implementation alternative is recorded as negative evidence and considered during ADR (not converted to successful implementation). When a task requires access to rights-controlled real cases or external tools and it is unavailable, continue independent tasks using synthetic fixtures; never forge permission.

 ## Execution protocol
 1. `python scripts/task_status.py --ready` and select a task whose prerequisites are met.
 2. Read `tasks/cards/Txxx.md`, then relevant sources only. State falsifiable acceptance and negative case.
 3. Implement or audit **only** the task-owned output. Run test/command and preserve exact evidence.
 4. Run full package validator and tests; update memory and task status with evidence through integration owner.
 5. If a substantial external effect requires permission, request it; otherwise execute autonomously within the workspace.

 ## Phase exit review
 Inspect `docs/V2_AUDIT_REPORT.md`, reference rights, baseline comparability, license/PII, true run logs, reversibility, and missing risks. An experiment's credible failure can justify a NO_GO architecture decision; it is never declared a quality PASS.
