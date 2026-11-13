# START HERE — Portfolio Agent v0.4.0 (설계/실행 패키지)

**이 압축파일은 완성된 디자인 생성기가 아닙니다.** Claude Code / Codex가 실제 프로젝트를 연구하고 작은 단계로 구현하기 위한 실행 가능한 설계 스캐폴드입니다. 사례 품질·실제 플러그인 설치·백엔드 실행은 아직 검증 전입니다.

## Windows PowerShell / macOS / Linux
1. ZIP을 압축 해제해 `portfolio-agent/` 디렉터리로 이동합니다.
2. `python scripts/validate_package.py` → `python -m unittest discover -s tests -v` → `python scripts/task_status.py --ready`.
3. `prompts/START_HERE_KO.md`를 Codex 또는 Claude Code에 입력합니다. 첫 실행 시 P00 검증부터 처리합니다.
4. P02의 해당 작업을 시작하면 에이전트가 `python scripts/clone_repos.py --group layout --apply`처럼 **자동으로 공개 GitHub 저장소를 고정 SHA로 복제**하도록 지침이 포함돼 있습니다. 설치/실행은 별도 라이선스·안전 검사 후 단계적으로 수행합니다.
5. `docs/ARCHITECTURE_MAP.md`는 전체 폴더 구조를 설명합니다. `project/agent-roles/WORKSHARE.md`는 다중 에이전트 협업 규칙입니다.

## 작업을 무조건 나누는 이유
다중 에이전트를 사용할 때에도 원본 파일 변경과 최종 문서 합성은 단일 작업자만 허용합니다. '모든 에이전트가 각자 디자인하고 한 파일에 쓰기'는 충돌과 회귀를 초래하므로 금지합니다.

## 의사결정
- **실제 사례 = 필수** (품질 검증); **대량 크롤링 = 필수 아님** (선택). **모델 학습 = 후순위**.
- DesignCraft = 인쇄 책자/DTP 주요 후보. OpenPencil = 자유형 비주얼 캔버스 후보. GenOffice = PPTX/Office 출력 후보. PhotoCraft/VectorCraft = 사진/벡터 보정 모듈 후보. 확정은 재현 실험 후.
- 페이지 크기는 A3 고정이 아니라 사용자 정의를 포함한 `formats/page-presets.json` 및 계약 기반.
- HarnessRouter/UHP는 선택적 호스트 실행·비교, 디자인 모델/품질 평가를 대체하지 않습니다.
