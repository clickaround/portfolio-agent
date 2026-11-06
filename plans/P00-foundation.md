# P00 — Agent bootstrap

 Status: NOT_STARTED. **Canonical per-task specifications live in `tasks/cards/`**, not here; inspect only assigned task. `tasks/backlog.json` is the source of the dependency DAG.

 | Task ID | Scope | Prerequisites | Expected evidence |
 |---|---|---|---|
 | `T000` | 기존 구조 보존·정적 검사 | – | `evidence/P00-static.md` |
| `T001` | Claude 플러그인 인식 | T000 | `evidence/P00-claude.md` |
| `T002` | Codex 플러그인 인식 | T000 | `evidence/P00-codex.md` |
| `T003` | 기억/인계 재개 실험 | T000 | `evidence/P00-handoff.md` |
| `T004` | 태스크 상태 도구 검증 | T000 | `evidence/P00-task-runner.md` |

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
