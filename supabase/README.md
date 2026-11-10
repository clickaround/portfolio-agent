# Supabase 데이터 계층 (구현 중)

`drafts/portfolio_conversation_foundation.sql`은 프로젝트·대화·메시지와 텍스트 part, run/attempt/outbox의 기반과 사용자 메시지 전용 트랜잭션 함수를 포함한다. 미완성 파일의 자동 배포를 막기 위해 migrations 폴더 밖에 둔다. assistant 저장, outbox worker, 로컬 프로젝트 이관, 모델 호출 이력과 API/UI 연결은 아직 없다. 기존 앱은 이 스키마를 사용하지 않는다. 실행 가능한 최종 마이그레이션으로 취급하거나 배포하지 않는다.

`python supabase/tests/run_draft_checks.py`는 로컬 Supabase DB에서 합성 계정 두 개를 트랜잭션 안에 만들고 소유자 읽기, 타 사용자 접근·위조 쓰기·작성자 불일치 거부와 순차 멱등성을 시험한 후 롤백한다. `python supabase/tests/run_concurrency_checks.py`는 별도 임시 로컬 DB와 두 독립 연결로 중복 요청, 상충 요청 및 대화별 활성 실행 하나의 제약을 시험한다. 동시성 시험의 `auth.uid()`는 실제 JWT 검증이 아닌 테스트용 대체 함수다. 이 검증은 실제 API/JWT 통합, 모든 CRUD, 성능, Storage, 에이전트 또는 마이그레이션 재실행 안전성을 증명하지 않는다.

다음 구현에는 신뢰 가능한 서버 전용 assistant 쓰기와 outbox worker, 로컬 프로젝트 ID·소유권의 명시적 매핑, 모델 호출 이력, API·UI 연결 및 전체 RLS 테스트가 필요하다. `backend/apps/api/src/pascal_api/conversations/`의 user-JWT 저장소 어댑터는 아직 라우트에 연결되지 않았다. 사용자 프로젝트는 자동으로 이전하거나 삭제하지 않는다.
