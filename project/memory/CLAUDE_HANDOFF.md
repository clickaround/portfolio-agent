# Claude 인수인계: Portfolio Agent 개발

작성일: 2026-11-11. 이 문서는 이어서 개발하기 위한 인계이며 실행 결과 보증서가 아니다. 먼저 `project/AGENTS.md`, `project/memory/NOW.md`, `project/memory/HANDOFF.md`를 읽고 현재 Git 상태·코드와 대조한다. 오래된 기술·점수·인증 상태를 현재 사실로 단정하지 않는다.

## 사용자 목표와 성공 흐름

사람이 사진·도면·다이어그램·설명 등 자신의 작업 자료를 제공하고, AI 에이전트와 대화하면서 목적에 맞는 완성도 높은 포트폴리오를 제작·반복 수정한다. 건축 전용이 아니라 UX/제품, 그래픽, 사진, 산업디자인, 일러스트, 연구 등으로 확장한다. 인쇄물, 발표물, 디지털 결과의 규격은 사용자 목적에 따라 결정한다.

사용자는 웹에서 **왼쪽 대화와 오른쪽 DesignCraft 편집기**를 보고, 크기를 조절하며 직접 편집하거나 에이전트에 변경을 요청하고 싶어 한다. 에이전트는 실제 열린 문서를 관찰하고, 사용자 의도와 원본 자료에 근거한 변경을 제안·적용·검증해야 한다. 단순히 PDF를 생성하거나 채팅 텍스트만 표시하면 최종 목표가 아니다. 원본 보존·정확성과 사람에게 설득력 있는 시각적 품질이 함께 필요하다.

## 각 에이전트의 목적과 경계

| 구성 | 목적 | 입력 → 출력 | 현재 코드와 경계 |
|---|---|---|---|
| `sourcePrepAgent` | 사용자가 제공한 원본을 훼손하지 않으면서 사진·스캔·도면을 편집·배치에 적합하게 준비 | 원본 자료 → 준비된 파생 자료와 변환 이력 `derived.json` | `agents/sourcePrepAgent/`: 여백 정리 제안·승인, levels, 배경 제거·knockout. 원본과 해시·도구·설정을 보존한다. 임의의 재구성이나 허가 없는 고위험 크롭은 하지 않는다. |
| `portfolioAgent` | 자료의 의미와 사용자 목적을 살려 이야기 순서·페이지 구성·위계·편집 가능한 결과물을 만든다 | 자료 manifest + 사용자 브리프 + 호스트가 작성한 `book-plan.json` → scene·미리보기·PDF/PPTX 및 선택된 DesignCraft 결과 | `agents/portfolioAgent/`: 계획은 호스트 LLM, 좌표와 렌더는 레이아웃·백엔드가 담당한다. 내용·사실을 만들지 않는다. `knowledge/domains/` 등은 지식 데이터이며 독립 에이전트 실행을 뜻하지 않는다. |
| `reviewAgent` | 생성한 당사자와 분리해 사실·원본·레이아웃·출력을 검토하고, 정확한 결과물에 연결된 신선한 리뷰와 차단 조건을 관리 | 특정 시도와 해시·렌더 → review context, 리뷰 기록, 통과 조건에 맞는 최종화 | `agents/reviewAgent/src/portfolio_agent/engine/review.py`. 리뷰가 바뀐 결과에 계속 적용되는 것으로 간주하지 않는다. 객관적 하드 게이트와 시각적 취향·사람 리뷰를 분리한다. |
| 하네스/조정 | 대화와 작업의 단계·역할·도구 호출·취소·실패·승인·증거를 조율 | 사용자 요청 + 상태 → 준비/계획/생성/관찰/수정/검토 작업 | `project/architecture/agent-editor/PROTOCOL-HARNESS.md`는 목표 설계다. 완전한 자율 하네스, revision 기반 원자적 수정, 검증된 다중 에이전트 루프가 이미 구현된 것으로 오인하지 말 것. |
| 호스트 모델 어댑터 | 실제 모델/도구 호출과 오류를 공급자별로 격리 | 프롬프트·작업 문맥 → 결과·실패 | `backend/apps/api/src/pascal_api/gateways/llm.py`의 실사용 러너는 Claude CLI다. 주입 가능한 인터페이스가 있다는 것만으로 Codex/GPT 런타임이 완성된 것은 아니다. |

선택적 `agents/pascal-agents/`는 별도 Git 저장소다. `DiagramAgent`는 다이어그램/도면 오버레이, `pptAgent`는 발표·팔레트·보드 자산 관련 기능의 후보이며, `drawingbookAgent`는 별도 제품 영역이다. 기본 세 에이전트의 작업과 분리하고 실제 연동 여부를 코드로 확인한다. 이 체크아웃에는 미커밋 변경이 있으므로 초기화·덮어쓰기·자동 업데이트하지 않는다. 설치와 고정 리비전은 `project/docs/PASCAL_AGENTS_SETUP.md` 참고.

`agents/portfolio-plugin/`은 에이전트 엔진 자체가 아니라 Claude/Codex용 스킬과 CLI 진입점이다. `backend/packages/portfolio-core/`는 공유 계약·검증, `backend/apps/api/`는 API, `frontend/`는 웹, `editor/designcraft/`는 Rust/WASM 편집기다. 역할을 하나의 거대한 에이전트 파일로 합치지 않는다.

## 현재 증거와 한계

- **CODE_INSPECTED:** `books/router.py`, `books/suggestions.py`, `frontend/app/features/books/editor-chat-panel.tsx`에는 생성·가져오기·대화 및 명시적 라이브 구조 포함 경로가 있다. 이미지·실제 화면을 모델이 본다고 단정하지 않는다.
- **DOC_REPORTED:** 합성 자료·가짜 모델 계획과 실제 DesignCraft/WASM을 이용한 첫 생성 및 편집 열기 흐름이 이전에 검증됐다. `project/evidence/2026-11-09_AGENT_WORKSPACE_E2E.md`, `project/evidence/2026-11-09_FULL_FLOW_CHECK.md`를 확인한다. 이는 실제 모델의 최종 품질을 증명하지 않는다.
- **DOC_REPORTED:** 과거 실제 Claude를 이용한 제한된 텍스트 제안·삽입과 PDF 왕복 기록이 있다. 시점·범위·당시 환경은 `project/memory/HANDOFF.md`와 해당 evidence를 확인한다. 현재 Claude 할당량/로그인 상태는 다시 확인해야 한다.
- **CODE_INSPECTED:** 현재 대화창은 저장된 PDF 텍스트와 사용자가 선택적으로 허용한 제한된 라이브 구조를 전송한다. 이미지 인식, 임의 객체 자율 변경, 수정 전후 시각적 검증 및 완전한 agent-editor 피드백 루프는 입증되지 않았다.
- **CODE_INSPECTED:** Supabase 대화 SQL은 `supabase/drafts/`에 있고 로컬 초안 검사·저장소 어댑터가 있다. 앱 라우트 연결, assistant 영속화, worker/outbox, 클라우드 마이그레이션·Storage는 미완이다. `supabase/README.md`가 현재 범위를 설명한다. 기존 계정·자료·프로젝트를 삭제하거나 자동 이전하지 않는다.
- **DOC_REPORTED:** 로그인은 전용 Supabase 프로젝트에서 이메일과 GitHub 로컬 흐름 및 일부 계정 간 차단을 확인한 기록이 있다. Kakao·실제 운영 도메인과 배포는 별도 검증이 필요하다. 이 문서에 자격 증명을 복사하지 않는다.

## 벤치마크의 위치와 해석

`agents/reviewAgent/benchmarks/`는 별도 GitHub 저장소가 아닌 리뷰 에이전트 하위 폴더다. `SPEC.md`, `PROTO_V3.md`, `HUMAN_REVIEW.md`, `THREATS_TO_VALIDITY.md`, `archportfoliobench_ap.py`, `engine_regression_bench.py`, `cases/`, `metrics/`, `reports/`, `results/`를 보존한다. SPEC에는 제안만 된 작업도 있으므로 개별 실행 증거와 구별한다.

하드 게이트는 원본 및 출처, 사실성, 잘림·범위·의도하지 않은 겹침, 내보내기·편집 가능성 등을 우선 판정한다. 미적 품질은 동일 조건의 기준선, 권리가 확인된 실제 자료, 독립적인 사람의 블라인드 비교와 별도 기록이 필요하다. 과거 Robie 사례의 약 0.67 및 기준선 범위는 작은 표본과 판정 변동이 큰 탐색 결과로, 실사용 품질 합격이나 일반화를 뜻하지 않는다. 합성 fixtures/가짜 LLM은 엔지니어링 회귀용이다.

## 다음 개발 순서

1. `git status -sb`와 `uv run python project/scripts/task_status.py --ready`로 실제 상태와 작업 카드 확인. 기존 변경과 ignored 데이터는 보존한다.
2. `project/architecture/agent-editor/PROTOCOL-HARNESS.md`를 목표로 현재 웹 → API → 작업 → 생성 파일 → WASM 편집기 경계를 추적하고, 한 번에 검증 가능한 다음 수직 기능을 선택한다. 실제 capability를 관찰하기 전 미지원 편집 도구를 선언하지 않는다.
3. 대화·작업의 사용자/프로젝트 경계, 원본·문서 버전, 승인·충돌·중단·멱등성을 설계하고 로컬 합성 환경에서 먼저 검증한다. 기존 DesignCraft 수정본이나 사용자 계정을 덮어쓰지 않는다.
4. 단일 대상에 대한 관찰 → 제안 → 명시적 승인 → 예상 revision에 맞는 적용 → 재조회·검증을 구현하고, 실패·오래된 revision·중복·undo·다른 객체 불변을 테스트한다. 기존 기능과 모델 공급자 경계를 함께 유지한다.
5. 벤치마크를 각 에이전트와 전체 흐름에 연결한다: 자료 변형/출처, 생성 계약·레이아웃·내보내기, 편집 성공 및 범위 밖 변경, 독립 리뷰·사람 선호, 비용과 지연. 실패와 측정 불가를 기록하고 합성 테스트를 실제 디자인 평가로 승격하지 않는다.

## Claude가 읽을 메모리와 시작점

- **공유 프로젝트 메모리:** `project/memory/NOW.md`, `HANDOFF.md`, `PROJECT.md`, `LESSONS.md`, 이 문서. 저장소에 있는 파일이므로 Claude와 Codex가 같은 내용을 읽고 갱신할 수 있다. 결론을 낼 때 최신 코드·증거와 대조한다.
- **사용자 PC의 Codex 전용 메모리(선택):** `C:/Users/User/AppData/Roaming/orca/codex-runtime-home/home/memories/MEMORY.md`. 현재 기기와 파일 접근 권한이 있을 때 Portfolio Agent 항목만 검색해 참고한다. Claude의 자동 메모리에 복제되거나 다른 기기에서 접근 가능하다고 가정하지 말고, 관련 없는 다른 프로젝트·민감 정보는 읽거나 옮기지 않는다.
- **명령:** 저장소 루트에서 `uv run python project/scripts/task_status.py --ready`, `uv run pytest agents/sourcePrepAgent/tests agents/portfolioAgent/tests agents/reviewAgent/tests`, `uv run lint-imports`, `uv run ruff check .`; 웹은 `cd frontend` 후 `npm run typecheck`, `npm test`, `npm run build`. 실제로 실행하지 않은 명령은 통과로 보고하지 않는다.
- **DUI:** 공통 UI는 별도 비공개 `akfldk1028/dui`, 로컬 `C:/DK/DUI`; Portfolio와 MARK는 커밋 고정 참조다. 새 환경/CI는 읽기 권한이 필요하다. `packages/dui`는 과거 로컬 사본이며 새 DUI 원본이 아니다.
- **안전과 사용자 의도:** 한국어로 간결하게 진행 상황을 알리고, 근거 없는 완료·자율 편집·디자인 품질을 주장하지 않는다. 원본·자료·Git 변경을 보존한다. 커밋·푸시·배포는 사용자의 해당 작업 지시와 프로젝트 정책을 따른다.
