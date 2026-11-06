# P02 — Repository + paper code verification

 Status: NOT_STARTED. **Canonical per-task specifications live in `tasks/cards/`**, not here; inspect only assigned task. `tasks/backlog.json` is the source of the dependency DAG.

 | Task ID | Scope | Prerequisites | Expected evidence |
 |---|---|---|---|
 | `T200` | GitHub 코드 고정 및 범위 감사 | T000 | `research/REPO_AUDIT_V2.md` |
| `T201` | GDB 실제 실행 검사 | T200 | `evidence/P02-gdb.md` |
| `T202` | SlidesGen-Bench 검사 | T200 | `evidence/P02-slidesgen.md` |
| `T203` | DECKBench/PosterBench 검사 | T200 | `evidence/P02-deck-poster.md` |
| `T204` | DeepSlides와 학습 코드 검토 | T200 | `evidence/P02-deepslides.md` |
| `T205` | AutoDesign 하네스 실행 | T200 | `evidence/P02-autodesign.md` |
| `T206` | OpenPencil 독립 프로브 | T200 | `evidence/P02-openpencil.md` |
| `T207` | GenOffice 독립 프로브 | T200 | `evidence/P02-genoffice.md` |
| `T208` | Diagram Design 격리 시험 | T200 | `evidence/P02-diagram.md` |
| `T209` | PDF 보존 라이브러리 타당성 | T200 | `research/PDF_ENGINE_OPTIONS.md` |
| `T210` | 서드파티 라이선스 게이트 | T200 | `research/THIRD_PARTY_AUDIT.md` |
| `T211` | HarnessRouter/UHP 인터페이스 조사 | T200 | `research/UHP_INTEGRATION_REVIEW.md` |

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
