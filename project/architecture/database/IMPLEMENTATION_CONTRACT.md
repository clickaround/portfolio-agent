# 프로젝트·대화 영속화 구현 계약

상태: **구현 전 설계안, 미검증**. 2026-11-10. 이 문서는 [전체 모델](README.md), [LLM 대화](LLM_CONVERSATION_DESIGN.md)의 현재 코드 적용 경계와 모호했던 결정들을 보완한다. 구체적인 SQL·API 작성 및 다중 사용자 테스트가 끝나기 전에는 완성된 시스템으로 취급하지 않는다.

## 1. 현재와 목표

현재 프로젝트는 인증된 사용자 UUID 아래 서버 파일 시스템에 있고 URL은 소유자별 `slug`다. 대화는 React 상태이며 저장하지 않는다. 사용자 메시지는 `editor-chat`에 최근 20개가 전달되고 비동기 job 결과를 클라이언트가 읽는다. Supabase Auth는 작동하지만 DB에는 이 앱의 public 테이블이 없다. 기존 SQL은 `supabase/drafts/`의 실험 초안으로 배포 대상이 아니다.

목표는 사용자가 로그인 → 자신의 프로젝트 → 대화 → 메시지 → 에이전트 응답을 새로고침과 재로그인 후에도 복구하는 것이다. 생성 전의 작업공간 대화와 생성 후 편집기 대화 모두 다룬다. 이메일/GitHub 사용자는 동일 `auth.users.id`인 경우에만 같은 소유자로 본다. 이메일 문자열이 같다는 이유로 자동 병합하지 않는다.

## 2. 권위와 ID

- **DB가 권위**: 프로젝트 메타데이터, 대화, 메시지, 실행 상태 및 파일 메타데이터. **객체 저장소가 권위**: 검증된 이미지·원본·native 문서·PDF 바이트. **실행 중인 편집기만의 임시 상태**: 아직 저장되지 않은 DOM/WASM 문서. 이 임시 상태가 DB 문서 버전이라고 표시하지 않는다.
- `projects.id`는 UUID, `(owner_id, slug)`는 유일. API는 기존 slug를 받은 뒤 검증된 사용자 UUID와 함께 정확히 하나의 DB project UUID로 해석한다. 권한이 없는 프로젝트와 없는 프로젝트는 모두 404로 응답한다. 클라이언트가 제공한 owner_id를 신뢰하지 않는다.
- 생성 전에도 대화를 만들 수 있다. `conversations.project_id`는 필수, `context_attempt_id`는 선택이다. attempt/문서 버전이 생기면 새로운 상태 참조 또는 불변 메시지 입력으로 남긴다. 대화방 전체를 하나의 특정 시도에 영구 고정하지 않는다.
- 현재 파일 기반 시도 번호 `01`과 미래의 `document_versions.id` UUID는 다르다. `legacy_attempt_refs(project_id, legacy_attempt, document_version_id)` 이행 매핑을 사용하고 `(project_id,legacy_attempt)`를 유일하게 한다. 임의의 동일 번호를 다른 프로젝트와 연결할 수 없도록 복합 FK를 둔다.
- 이전은 소유자가 확인된 각 `(auth_user_uuid, local_slug)` 단위로 수행한다. dry-run은 원본 경로·충돌·개수·해시만 보고하고 쓰지 않는다. 이후 재실행 가능한 이행 작업이 DB 매핑을 기록하고 객체 업로드와 해시 검증을 따로 진행한다. 기존 로컬 원본을 삭제하지 않는다. 중복 slug, 미확인 소유자, 해시 충돌 시 중단하고 보고한다. 단일 DB 트랜잭션으로 파일/객체까지 원자적으로 이전할 수 없으며 부분 이력과 재개 지점이 필요하다.

## 3. 초기 스키마와 쓰기 주체

1차로 적용할 것은 `projects`, `conversations`, `messages`, `message_parts`, `agent_runs`, `run_attempts`다. 파일/문서 버전 및 도구 호출은 해당 기능을 실제로 연결할 때 후속 마이그레이션으로 추가한다. 첨부·문서 이력과 자율 편집은 초기 대화 저장의 완료 조건에 포함하지 않으며 UI에서 구현됐다고 표시하지 않는다.

| 작업 | 유일한 쓰기 주체 | 원자적 경계 |
|---|---|---|
| 프로젝트·대화 생성/수정 | 사용자 JWT를 검증한 API. DB는 사용자 JWT를 전달받거나 최소 권한 전용 함수를 이용 | 서버가 생성자/소유자를 JWT subject로 설정. DB가 권한과 프로젝트 관계를 다시 확인 |
| 사용자 메시지 접수 | 인증 API → 제한된 DB 함수 | 대화 행 잠금 → 중복 키와 정규화된 요청 해시 비교 → 메시지·part·run·첫 attempt·dispatch 레코드 삽입 → commit. 트랜잭션 실패 시 아무것도 접수하지 않음 |
| 작업 claim·결과 | 외부에서 접근 불가능한 worker 전용 DB 역할/연결 | claim과 lease 확인 후 비교 갱신. assistant 메시지·part 및 run 상태를 한 트랜잭션에 확정 |
| 대화 목록·메시지 조회 | 사용자 JWT 기반 읽기 | DB RLS + API 소유자 검사. 메시지는 `(conversation_id, sequence)` 오름차순 커서 |

브라우저와 일반 authenticated 역할은 assistant/system/tool 메시지, run 성공, 비용, review, 파일 해시·확정 상태를 직접 쓰지 못한다. 프로젝트·대화 ID 변경과 owner 변경도 금지한다. worker 자격은 서버 환경에서만 사용하며 RLS 우회 역할이면 **API/worker에서 별도로 사용자·프로젝트·대화·run 소속을 검증**한다. 어떤 최소 권한 역할/연결을 쓸지는 배포 환경에서 실제 지원 여부와 RLS 테스트로 확정하고, 브라우저에 `service_role` 키를 전달하지 않는다.

`SECURITY DEFINER`가 꼭 필요하면 빈 `search_path`, 스키마 지정, 입력 검증, `auth.uid()` 소유자 확인, PUBLIC/anon 실행 취소, 목적별 최소 GRANT를 하나의 마이그레이션에 넣는다. 초안의 `append_user_message`는 사용자 메시지만 저장하므로 **아래 접수 트랜잭션을 충족하지 않는다**. 그대로 배포하거나 기존 API에 연결하지 않는다. [Supabase 함수 보안](https://supabase.com/docs/guides/database/functions)

## 4. 전송·실행·동시성 계약

- `POST /projects/{slug}/conversations/{id}/messages` 입력: `client_request_id` UUID, `text`(1~4000자), 선택한 context 참조와 동의 범위. 최초 지원은 텍스트만. 로그인 JWT와 route 소유자를 서버가 검증한다.
- 동일 대화/요청 ID·동일 정규화 payload의 재전송은 기존 `message_id/run_id`를 돌려준다. 동일 키에 다른 본문·첨부·문서 revision·동의 범위가 있으면 `409 idempotency_conflict`. 해시는 버전이 명시된 canonical JSON(UTF-8, 필드 정렬, 빠진 필드/NULL 규칙과 문자열 정규화 규칙 포함)으로 계산하며 그 정확한 구현은 테스트 벡터와 함께 확정한다. 해시 하나만 저장해 원문 복원 가능하다고 주장하지 않는다.
- 1차는 대화당 동시에 활성 run 하나. 다른 새 요청은 `409 run_in_progress`; 이전 요청 ID의 재전송은 해당 run을 조회한다. 부분 유일 인덱스와 트랜잭션 잠금으로 경쟁 요청을 차단한다. 대화에 속한 메시지 순서는 같은 대화 행 잠금으로 배정하며 두 브라우저 탭에서 중복되지 않아야 한다.
- 접수 성공은 `202 {message_id,run_id,status}`. DB commit 전 실패는 요청 미접수; commit 뒤 응답 단절은 같은 키로 조회·재시도. API는 모델 호출에 브라우저가 보낸 과거 메시지 배열을 그대로 신뢰하지 않고 DB에서 허용된 대화 이력을 선택한다.
- `agent_runs`: queued → running → succeeded/failed/cancelled/unknown_outcome. 실패 시 error code와 공개 가능한 메시지만 보관. `run_attempts`는 재시도마다 새 행이며 제약·권한·실제 실행 결과를 검사한다. 저장 성공과 실행 성공을 혼동하지 않는다.
- DB commit과 큐 전달 사이는 **transactional outbox**로 처리: 메시지/run/outbox를 한 트랜잭션에 쓰고 dispatcher가 재시도하며 worker claim은 조건부 갱신 또는 행 잠금을 사용한다. 중복 전달은 허용하되 외부 모델·도구의 실제 부작용은 별도의 멱등 키가 없으면 정확히 한 번 실행을 보장할 수 없다. 전송 결과가 불명확하면 `unknown_outcome`으로 두고 자동 재실행하지 않는다.
- 1차 응답은 완료된 텍스트만 저장한다. 스트리밍 조각 저장·SSE 복구는 후속 범위. 제안 문구는 별도 message part로 보존하되 문서에 자동 반영하지 않는다. API가 반환한 제안과 편집기에서 실제 적용한 작업은 별도다.

## 5. 파일과 프라이버시

초기 대화 영속화는 텍스트 범위다. 기존 로컬 업로드·PDF 경로는 현재대로 유지하며 클라우드 접근이라고 표시하지 않는다. 다음 단계는 개인용 비공개 Storage + `assets/asset_versions`·`documents/document_versions/version_artifacts`를 도입해 바이트 검증, 해시, 메타데이터와 삭제 상태를 연결한다. 객체 키에 임의의 사용자 제공 경로를 사용하지 않는다. DB와 Storage 사이의 실패는 상태와 정리 작업으로 복구한다.

모델에 전달한 메시지 ID와 버전·추출 범위는 실행 입력 기록으로 남기되, 실제 전송하지 않은 이미지를 전송했다고 기록하지 않는다. 선택한 라이브 편집 상태는 동의 받은 경우만 제한해 사용한다. 사용자 삭제/보존 정책, 공급자에 이미 보낸 정보와 백업 보존기간은 제품·운영 결정이 필요하며 미결 상태다. 자격 증명·토큰·내부 추론은 기록하지 않는다.

## 6. 모듈·계약

```text
supabase/migrations/               검증 후 생성한 순서 있는 배포 SQL
supabase/tests/                    RLS·FK·RPC·경쟁 테스트
backend/apps/api/src/pascal_api/
  projects/                       사용자별 project ID/slug 해석
  conversations/{router,schemas,service,repository}.py
  runs/{service,repository,worker}.py
  storage/                        DB와 객체 저장 포트·어댑터
frontend/app/features/conversations/
  queries.ts  mutations.ts  schema.ts  components/
```

frontend는 별도 API 모듈만 사용하고 편집기 컴포넌트는 대화 UI와 저장 API를 직접 합치지 않는다. 현재 `editor-chat`은 임시 API로 명시하고, 새 경로는 기능 플래그로 도입한다. 구조화된 OpenAPI 타입을 갱신하고 이전 경로의 제거 시점은 새 경로의 회귀 검증 후 정한다. 다중 worker 운영 전 지금의 프로세스 내부 JobStore를 durable queue로 간주하지 않는다.

## 7. 배포·검증 게이트

1. **로컬/격리 DB**: 마이그레이션 빈 DB 적용과 재생성, 구조/제약, 명시된 GRANT/RLS, 함수 search_path, 익명/A/B/worker 역할 검증. 서로 다른 프로젝트·대화 참조 삽입과 권한 상승, owner 변경, 가짜 assistant/result 쓰기 거부. 실제 토큰을 쓴 API 테스트 별도 수행.
2. **동시성/장애**: 두 독립 DB 연결로 중복 키·다른 payload 충돌·같은 대화 동시 접수·중복 dispatcher·lease 만료·DB commit 직후 worker 중단·결과 불명 테스트. 트랜잭션 하나의 순차 테스트를 동시성 검증으로 부르지 않는다.
3. **브라우저**: 실제 계정 A/B로 프로젝트·대화 생성, 메시지/응답 저장, 새로고침·로그아웃·재로그인 복구, B의 직접 ID 접근 거부, 오류와 재시도 표시. 테스트 더블과 실제 LLM 호출을 명시적으로 구분한다.
4. **전환**: 로컬 프로젝트 이행 dry-run·중단 재개·해시 대조·수동 점검. DB/Storage 적용 전 백업·롤백·관측 계획을 마련한다. 기능 플래그 활성화 후 검증 전에는 이전 로컬 경로를 삭제하지 않는다.

위 게이트와 Storage·운영 설정이 통과하기 전에는 완벽, 운영 가능, 클라우드 저장 완료라고 보고하지 않는다. 실제 마이그레이션은 아직 생성·적용하지 않았다.
