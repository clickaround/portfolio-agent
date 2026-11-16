# P10 — Conversation editing beside the DesignCraft canvas, and small models

Owner's direction (2026-11-14, 2026-11-15): a finished book in one shot is not the product. The user talks to the agent beside the canvas, marks a
spot, and the agent edits the open document at once. Weights come second: a small model for layout proposals or for editing is trained from what the
product records, not instead of it.

**Canonical per-task specifications live in `tasks/cards/`**; `tasks/backlog.json` is the source of the dependency DAG.

## Three tracks
- **A. Connect the editor** — T1003 -> T1004 -> T1005 -> T1012. The command bridge exists (`frontend/app/features/books/editor-command.ts`,
  `editor/designcraft/apps/designcraft-web/src/pascal_bridge.rs`) but allows five commands; the nine typed ops need more.
- **B. Edit quality** — T1000 (done), T1001 (done), T1006, T1007.
- **C. Layout model on our data** — T1002 (done), T1008 (general data), T1011 (portfolio data), T1009 (try existing weights as they are), T1013 (fine-tune).
  The missing piece is T1011: real portfolio pages. Two PDFs exist outside the repo today.
  Agreed recipe (2026-11-15): poster-trained weights -> fine-tune on portfolio layouts (T1011) + skeleton-swap synthetic pages (T1015) -> T1013 on a rented pod.
  No mass scraping of Issuu / Behance.
- **D. Small edit model** — T1010 (synthetic edit records), T1014.

| Task ID | Scope | Prerequisites | Expected evidence | State | Waiting on |
|---|---|---|---|---|---|
| `T1000` | 실시간 편집 첫 조각 (요소 키 + 명령 9개 + 게이트) | T212 | `evidence/P10-live-edit.md` | done | — |
| `T1001` | 판정 단계와 선호 기록 | T1000 | `evidence/P10-judge-record.md` | done | — |
| `T1002` | 논문·모델·데이터 조사 (가중치 학습 여부) | — | `evidence/P10-model-research.md` | done | — |
| `T1003` | 브라우저 에디터 명령 통로 넓히기 | T1000 | `editor/designcraft/apps/designcraft-web/src/pascal_bridge.rs` | pending | Rust + trunk 빌드 환경 확인 필요 |
| `T1004` | 편집 명령을 화면의 문서에 바로 적용 | T1003 | `frontend/app/features/books/editor-command.ts` | pending | — |
| `T1005` | 캔버스 표시(빨간 점) → 요소 | T1004 | `frontend/app/features/books/pages/book-page.tsx` | pending | — |
| `T1006` | 편집 → 판정 → 재시도 자동 반복 | T1001 | `agents/portfolioAgent/src/portfolio_agent/engine/live.py` | pending | — |
| `T1007` | 빠진 편집 명령: 자르기, 새 요소 | T1000 | `agents/portfolioAgent/backends/designcraft/live.py` | pending | — |
| `T1008` | LICA 데이터 받아 내용·라이선스 확인 | T1002 | `evidence/P10-lica-inspection.md` | pending | 주인 허락 필요: 내려받기 985 MB |
| `T1009` | PosterCopilot을 배치 제안기로 시험 | T1002 | `evidence/P10-postercopilot-proposer.md` | done (그대로는 못 씀) | 주인 허락 필요: 가중치 내려받기(약 16 GB), GPU(이 기기는 16 GB VRAM, 모델 카드는 약 20 GB) |
| `T1010` | 합성 편집 데이터 만들기 (Figma 방식) | T1006 | `evidence/P10-synthetic-edit-data.md` | pending | 구독 한도 안에서 며칠 걸림 |
| `T1011` | 포트폴리오 레이아웃 데이터 모으기 | T1002 | `evidence/P10-portfolio-layout-data.md` | pending | 실제 포트폴리오 PDF 필요: 지금 저장소 밖에 있는 것은 2개뿐. 분야당 수백 쪽이 목표(OmniDocLayout 기준 수백~2,000건) |
| `T1013` | 레이아웃 소형 모델 미세조정 (우리 데이터) | T1011, T1008 | `evidence/P10-layout-model.md` | pending | GPU 필요(이 기기 16 GB VRAM 또는 대여), T1011의 데이터 |
| `T1014` | 소형 편집 모델 미세조정 (LoRA) | T1010 | `evidence/P10-small-edit-model.md` | pending | GPU 필요 |
| `T1012` | Claude Design과 같은 원본으로 나란히 비교 | T1005 | `evidence/P10-vs-claude-design.md` | pending | 분야별 실제 원본 필요 |
| `T1015` | 합성 데이터: 실제 배치 틀 + 바꿔 끼운 내용 | T1011 | `evidence/P10-synthetic-layout-data.md` | pending | T1011의 추출 결과 |

## Gate
A user marks a spot on the canvas, says what to change, and sees that element change in the open document; an edit that does not do what was asked
is taken back with a reason. Model work passes only on rendered pages compared by eye with the rule layout or with Claude.
