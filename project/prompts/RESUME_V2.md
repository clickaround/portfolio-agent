# 세션 재개 (Codex 또는 Claude Code에 붙여넣기)

현재 프로젝트의 `AGENTS.md`, `memory/NOW.md`, `memory/HANDOFF.md`, `PLANS.md`와 `tasks/backlog.json`을 읽어라. 먼저 실제 파일 시스템과 마지막 실행 증거의 일치 여부를 확인한다. `python scripts/validate_package.py` 및 단위 테스트 실행 후 `python scripts/task_status.py --ready`를 본다. **증거 없는 완료**를 그대로 믿지 않는다.

선행 의존성이 충족된 가장 작은 작업을 한 개 선택하고 해당 `tasks/cards/Txxx.md`만 읽어라. 그 작업의 출력 파일 범위, 가설, 반증 조건, 최소 실행·검증 명령을 제시한 뒤 수행하라. 추가 자료가 필요할 때에만 해당 paper/repo/knowledge 파일을 읽어라. 완료 시 정확한 로그를 기록하고 HANDOFF를 갱신하라. 외부 API 결제/원본 전송/대량 다운로드/상용 배포는 권한 없이 수행하지 말라.

작업이 외부 허가/환경으로 막히면 해당 작업만 BLOCKED 처리하고, 합성 fixture 또는 다른 독립 작업으로 전환하라. 사용자가 승인한 범위를 넘지 않으면서 다음 ready task까지 이어가라.
