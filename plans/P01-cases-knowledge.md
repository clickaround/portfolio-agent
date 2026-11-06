# P01 — Portfolio expertise & rights

 Status: NOT_STARTED. **Canonical per-task specifications live in `tasks/cards/`**, not here; inspect only assigned task. `tasks/backlog.json` is the source of the dependency DAG.

 | Task ID | Scope | Prerequisites | Expected evidence |
 |---|---|---|---|
 | `T100` | 포트폴리오 JTBD 정의 | T000 | `research/domain/architecture-jtbd.md` |
| `T101` | 크로스 도메인 차이 조사 | T000 | `research/domain/cross-domain-taxonomy.md` |
| `T102` | 링크 후보 사실 확인 | T100 | `cases/catalog-audit.jsonl` |
| `T103` | 사례 권리 프로토콜 | T100 | `cases/RIGHTS_PROTOCOL.md` |
| `T104` | 합성 사례 구성 | T103 | `cases/fixtures/synthetic-case.json` |
| `T105` | 권리 승인 실제 사례 1건 상세 주석 | T102, T103 | `cases/annotations/approved-case-01.json` |
| `T106` | 사례 품질 선정 기준 | T100 | `cases/SELECTION_RUBRIC.md` |
| `T107` | 레퍼런스 주석 신뢰성 | T106 | `cases/ANNOTATION_QA.md` |
| `T108` | 사례 검색 계약 | T104, T103 | `contracts/reference-retrieval.md` |
| `T109` | 데이터 분할/누출 검사 | T103 | `benchmarks/DATA_SPLIT.md` |

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
