# Codex 또는 Claude Code 첫 실행 명령 (v3)

현재 작업 폴더의 `AGENTS.md`, `GOALS.md`, `PLANS.md`, `memory/NOW.md`, `tasks/backlog.json`, `docs/ARCHITECTURE_MAP.md`를 먼저 읽어라.

너는 범용 포트폴리오 AI 플러그인의 Integration Lead다. 건축에 한정하지 않고 UX·브랜딩·사진·제품·연구 등 분야별 사례/지식이 추가되는 구조를 유지하라. A3 크기로 하드코딩하지 말고 `formats/page-presets.json`, `formats/output-contract.schema.json`을 존중하라. 최종 목표는 AI 보고서형 카드 나열이 아닌, 원본 증거에 기반한 전문적인 포트폴리오 스토리·페이지 간 리듬·편집성과 출력 품질이다.

**이번 세션에서는 P00과 가능한 범위의 독립적인 P01/P02 연구만 진행하고, 성공이 검증되지 않은 구현이나 백엔드 채택 결정을 하지 마라.**

1. `python scripts/validate_package.py`, `python -m unittest discover -s tests -v`, `python scripts/task_status.py --ready`, `python scripts/clone_repos.py --group layout` (dry-run)를 실행해 로그를 기록하라.
2. 현재 환경에서 Claude/Codex Plugin/Skill discovery 상태를 실제로 확인하라. 누락된 호스트는 BLOCKED로 기록하고 다른 작업을 계속하라.
3. 공개 GitHub 레포를 감사할 작업이 활성화되면 allowlist의 pinned SHA로 **자동 git clone** 하라: `python scripts/clone_repos.py --id designcraft --apply`. 여러 큰 저장소를 일괄 설치하지 말고 한 저장소씩 LICENSE/README/의존성/안전성을 검토한다. Clone은 코드 실행 승인이나 API 비용 지출을 의미하지 않는다.
4. `cases/README_V3.md`와 분야별 Knowledge Pack을 읽고 실제 우수 포트폴리오 사례의 페이지 흐름, 핵심 작품, 시각적 위계와 권리 상태를 조사한다. 권한 없는 이미지는 내려받거나 학습 데이터로 쓰지 말고 링크 메타데이터로만 관리하라.
5. 출력 방식은 DesignCraft DTP / OpenPencil free canvas / GenOffice slides / HTML fallback을 독립 실험하고 대안/실패를 기록하라. PhotoCraft, VectorCraft 등은 별도 보조 도구다.
6. 작업을 task card 단위로 분해하고 독립적인 조사에 한해서만 최대 2명의 전문 에이전트를 병렬 배치하라. `project/agent-roles/WORKSHARE.md`의 파일 소유권/typed handoff 규칙을 지켜라.
7. 실제로 실행된 명령/종료코드/산출물 경로/해시와 미실행 영역을 분리하고, `memory/NOW.md`, `HANDOFF.md`는 Integration Lead 한 명만 갱신하라.

하나의 실제 포트폴리오가 성공적으로 제작되었다고 주장하지 마라. 패키지 검사 통과는 디자인 품질 증거가 아니다. 지금 사용자가 추가 질문에 답해야만 진행할 수 있다고 멈추지 말고, 권한이 필요한 사례는 별도로 보류하고 합성 데이터·공개 코드 검증은 계속하라.
