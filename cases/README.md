# Case Library — 반드시 필요하지만, 이 ZIP에는 저작권 미확인 실제 이미지가 없음

**CASE COLLECTION STATUS: 0 approved cases.** 이 폴더에는 가짜 '우수 포트폴리오 사례'를 넣지 않았습니다. `examples/SYNTHETIC_*`는 스키마 테스트용 합성 파일이며 절대 평가/학습 사례로 세지 않는다.

## Collection stages
1. 목적/분야/독자(취업/대학원/제안서) 기준으로 후보 탐색. 출처 링크·저작권자·포트폴리오 전체 페이지 수와 페이지 흐름 메타데이터만 초기 기록.
2. 원본 PDF/이미지 저장, 분석, 임베딩, 모델 입력, 재배포 중 **허용된 사용 범위** 확인. 공개 웹 링크만으로 저장/학습 허가를 추정하지 않는다.
3. 허가된 전체 포트폴리오의 project sequence를 보고 1~4개의 유의미한 spread를 선정. 파일별 SHA256, page number, rights 기록.
4. 페이지·spread와 콘텐츠별 주석: 페이지 역할, 핵심 시각증거, 그리드, 여백, 타이포그래피, 정보 밀도, 리듬, 반복/생략, 선정 이유.
5. 2인의 독립 주석자 불일치 기록. 선택한 좋은 이유와 위험(복제 금지) 함께 보관.
6. 공개 `reference`와 검증용 `heldout`은 **제작자/프로젝트 단위로 분리**. 참조원본을 평가 입력으로 재사용 금지.
7. 개인 식별 정보·무단 저작물은 저장하지 않거나 별도 암호화 저장소. Git에 원본 금지.

### Collection targets (start small, proposed)
- Architecture 5–10 full multi-page portfolios / 20–40 selected pages; independently held-out additional portfolios for evaluation.
- UX / branding / photography: each 2–3 exploratory cases for **cross-domain taxonomy only**. Production support deferred.
- Collect 10–20 *negative examples* or author-approved synthetic failures to teach anti-report rubric, not as training data at first.

### Rights status
`link_only` (URL metadata only), `permission_pending`, `permission_granted_reference`, `permission_granted_eval`, `permission_granted_training`, `restricted`, `withdrawn`. Separate scopes; never infer one from another.

### Workflow
Use `skills/portfolio-research/SKILL.md` and `prompts/CASE_AUDIT.md`. Each case gets one JSON manifest conforming to `cases/case.schema.json`. The actual images live in ignored `cases/private/` or external managed storage, not this ZIP.
