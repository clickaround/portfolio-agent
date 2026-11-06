# P08 — Training, HarnessRouter and commercial decisions

 Status: NOT_STARTED. **Canonical per-task specifications live in `tasks/cards/`**, not here; inspect only assigned task. `tasks/backlog.json` is the source of the dependency DAG.

 | Task ID | Scope | Prerequisites | Expected evidence |
 |---|---|---|---|
 | `T800` | HarnessRouter 필요성 결정 | T704, T211 | `architecture/adr/0007-harnessrouter.md` |
| `T801` | UHP 격리 smoke [optional] | T800 | `evidence/P08-uhp-smoke.md` |
| `T802` | 학습 필요성 판단 | T701, T702, T704 | `research/TRAINING_DECISION_V2.md` |
| `T803` | 유료 파일럿/사업성 검증 | T703, T704 | `research/BUSINESS_GATE.md` |
| `T804` | 상용 배포 라이선스 검토 | T210 | `research/COMMERCIAL_LICENSE_RELEASE.md` |

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
