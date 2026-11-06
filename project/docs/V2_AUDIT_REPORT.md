> **ARCHIVED V2; historical validation only.** Current v3 authoritative docs: GOALS.md, PLANS.md, architecture/ARCHITECTURE_MAP.md, formats/, research/repos.lock.json.

# v1 → v2 독립 설계 감사 (2026-11-04)

범위: 전달된 v1 ZIP 100개 파일의 정적 점검과 핵심 코드/메모리/태스크/스키마 수동 검토. **실제 Claude/Codex 호스트 플러그인, 외부 레포 실행, 미적 품질 검증은 하지 않음.**

## 주요 발견 및 조치
| ID | 심각도 | v1 문제 | v2 조치 | 재검증 |
|---|---|---|---|---|
| F01 | Critical | 33개 중 27개 태스크 합격조건이 추상적 | 60+ 원자 카드에 산출물·검사·반증 정의 | backlog 검사 |
| F02 | Critical | 사용자 허가 사례 최소 5개가 없으면 생성 PoC까지 정지 | 합성 사례로 파이프라인 독립 검증, 실사례 평가는 rights gate | 데이터/태스크 분리 |
| F03 | High | 편집 백엔드 둘 모두 성공을 요구해 전체 아키텍처 동결 | 대안 별 probe 결과 실패도 근거로 기록하고 fallback 경로 유지 | P04 gate review |
| F04 | High | B1→B2에서 reference와 backend 동시 변경 | case/no-case, domain/no-domain, QA off/on을 각각 통제 | ABLATIONS_V2 |
| F05 | High | 증거 없는 `done/not_needed` 전환이 가능 | evidence path/finished_at/pass_state 필수 + waiver | negative unit tests |
| F06 | High | bbox 검사는 NaN·bool·통합 provenance를 검출하지 못함 | finite / explicit-overlap / asset refs 검사 보강 | negative tests |
| F07 | High | ZIP에 __pycache__ .pyc가 포함됨 | 해당 파일 제외, 텍스트 소스만 패킹 | zip manifest |
| F08 | High | 이미지/포폴 사례가 link_only인데 '고품질 사례' 혼동 가능 | 후보는 품질/권한 미확인, 승인 사례와 split 구분 | RIGHTS_PROTOCOL |
| F09 | High | 단순 플러그인 스키마 검사를 호스트 설치로 오해 가능 | host discovery 별 실행/blocked, manifest vs host 구분 | P00 host log |
| F10 | High | OpenPencil vs GenOffice에 대한 기술적 tradeoff 불명확 | fallback 포함 비교 매트릭스 + PDF 벡터 probe 명시 | ALTERNATIVES_V2 |
| F11 | High | 국소 수정·출력 체크가 추상적 | Scoped edit diff 및 source hash+export visual gate | tests / P04 |
| F12 | High | C4/ADD/ATAM을 이름만 기재하고 실제 평가 시나리오 부족 | 품질 시나리오·데이터 흐름·ADR 후보 추가 | architecture docs |
| F13 | High | UI/세션이 바뀌면 메모리와 실행 결과 불일치 가능 | evidence-based task update + handoff 회복 절차 | RUNBOOK |
| F14 | Medium | 범용 도메인 확장과 건축 PoC 범위 혼재 | 건축 1도메인 구현, 나머지는 차이 연구만 | SCOPE_MATRIX |
| F15 | High | PDF 원본 SHA 유지와 실제 vector fidelity 혼동 | content, rendering, vector identity 별 검사 | PDF_TEST_PROTOCOL |
| F16 | High | 보안·데이터 권리·원격 모델 전송 가드레일 약함 | 개인정보/악성 prompt-injection/외부도구 격리 | SECURITY_TESTS |
| F17 | Medium | 장기 제품 유료 파일럿/운영비 결정 누락 | P08 별도 사업·권리 게이트 | BUSINESS_GATE |
| F18 | Medium | HarnessRouter UHP와 Slides Kit 상용권 혼동 | core/kit 라이선스와 no-copy gate 구분 | LICENSE_RISKS |
| F19 | Medium | 부분 평가 코드를 실제 벤치마크 재현처럼 읽힐 수 있음 | 재현 상태 4단계와 실행 증거 규약 명시 | REPRO_PROTOCOL |
| F20 | Medium | 작은 작업 병렬 실행이 모두 같은 memory를 수정할 수 있음 | 단일 integration owner / worktree file ownership | TASK_RUNBOOK |

## 즉시 중단 조건
원본 무단 변형, 사례 권한 없는 다운로드/학습, 사용자 비밀 외부 전송, 라이선스 불명확 코드 상용 배포, 하드게이트 FAIL인데 PASS 보고, 동일 heldout을 반복 튜닝에 사용.

## 미해결·반증해야 할 위험
1. 실제 고품질 건축 포트폴리오 사례 권한 확보 (blocker for human quality evidence, not synthetic engineering).
2. PDF 벡터/텍스트/해치/치수 표시 충실도 (tool-specific spike pending).
3. 3개 시안이 실제로 3개 다른 디자인인지 (human validation pending).
4. 외부 편집 엔진의 파일/폰트/PDF export 실제 성능 (not executed).
5. Codex/Claude 버전별 plugin discovery (not executed).
6. Benchmark 지표의 건축 분야 타당성과 인간 선호 상관 (not measured).

## 적합 판정
v2는 **더 상세한 실행 계획·스캐폴드**, 제품·외부 레포 재현 완료가 아니다. 실행 증거 없는 성공 주장 금지.
