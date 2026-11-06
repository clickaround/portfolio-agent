# P03 — Benchmark & negative fixtures

 Status: NOT_STARTED. **Canonical per-task specifications live in `tasks/cards/`**, not here; inspect only assigned task. `tasks/backlog.json` is the source of the dependency DAG.

 | Task ID | Scope | Prerequisites | Expected evidence |
 |---|---|---|---|
 | `T300` | 평가 목적·평가 단위 선언 | T100, T200 | `benchmarks/EVAL_UNITS.md` |
| `T301` | 합성 fixture와 악성 사례 | T104, T300 | `benchmarks/cases/negative-cases.json` |
| `T302` | Geometry/Source hard gates | T301 | `benchmarks/HARD_GATES.md` |
| `T303` | Human blinded A/B 프로토콜 | T300, T106 | `benchmarks/HUMAN_REVIEW_V2.md` |
| `T304` | Benchmark split 동결 | T109, T301 | `benchmarks/DATA_SPLIT.md` |
| `T305` | 비교군 분해·통제 | T302, T303 | `benchmarks/ABLATIONS_V2.md` |
| `T306` | 메트릭과 결과 형식 잠금 | T302 | `contracts/eval-protocol.schema.json` |
| `T307` | 분포 변화/정책 점검 | T305 | `benchmarks/THREATS_TO_VALIDITY.md` |

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
