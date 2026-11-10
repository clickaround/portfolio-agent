# 인증 및 사용자별 프로젝트 접근 조사 — 2026-11-10

## 확인한 현재 상태

- REPRODUCED: 전용 Supabase MCP가 `lwescxtcempjhfxqlfyb` 프로젝트에 접근한다. public 스키마는 비어 있다. 브라우저 공개 키와 URL을 git에 포함되지 않는 `frontend/.env.local`에 설정했다.
- REPRODUCED: Supabase Auth 설정 API는 이메일 인증 사용, 회원가입 허용, GitHub 및 Kakao 비활성 상태를 반환했다. 로그인 페이지의 버튼이 활성화된 것은 확인했으나 실제 계정의 로그인 성공이나 이메일 확인은 시험하지 않았다.
- CODE_INSPECTED: FastAPI는 요청자의 액세스 토큰을 검증하지 않고 하나의 `ProjectStore`와 `JobStore`를 공유한다. 로그인하지 않아도 프로젝트, 원본, PDF, 페이지 및 작업 정보에 접근할 수 있다. 프론트의 API 클라이언트에도 인증 헤더가 없다.
- CODE_INSPECTED: 이미지와 PDF는 `img.src`와 `a.href`로 API에 직접 접근하며, 편집기와 제안 화면에는 별도 `fetch`도 있다. JSON API에만 토큰을 추가하면 이 경로들이 깨지거나 보호되지 않는다.
- CODE_INSPECTED: 프로젝트 메타데이터 및 파일은 로컬 디스크에 있고, Supabase에 저장되거나 사용자별로 분리되지 않는다. 기존 로컬 데이터의 소유자를 추측해서 이전해서는 안 된다.

## 공식 문서 근거와 구현 방향

- DOC_REPORTED: [Supabase JWT 검증](https://supabase.com/docs/guides/auth/jwts)은 검증 라이브러리와 프로젝트 JWKS를 사용하며, 비대칭 키가 아닌 프로젝트에서는 JWKS가 비어 있을 수 있다고 명시한다. 서버는 서명뿐 아니라 발급자, 대상, 만료 및 사용자 ID도 검증해야 한다.
- DOC_REPORTED: [리디렉션 URL 설정](https://supabase.com/docs/guides/auth/redirect-urls)은 회원가입 확인과 OAuth 콜백 주소를 허용 목록과 맞추도록 요구한다. 운영 주소와 개발 주소를 구분해야 한다.
- HYPOTHESIS: 사용자별 파일 디렉터리 분리 또는 사용자 소유권 데이터와 서버 검사 중 하나를 일관되게 적용한다. 파일, 작업, 생성물까지 동일한 주체 검사를 적용하고 로그인 없는 접근과 다른 사용자의 접근을 모두 차단해야 한다.
- HYPOTHESIS: 이미지/PDF 표시와 다운로드는 인증된 fetch 후 제한된 수명의 Blob URL을 쓰거나, 안전한 서버 세션을 적용한다. URL 쿼리에 장기 JWT를 넣지 않는다.
- HYPOTHESIS: 인증 실패 또는 Auth 서버 장애 시 보호 데이터 접근은 실패 처리한다. 기존 로컬 데이터 이전은 명시적 소유자 지정 및 충돌 검증을 거쳐 별도 수행한다.

## 다음 검증

두 계정으로 프로젝트, 원본, 생성물, 작업 목록 및 직접 URL에 대한 교차 접근 거부를 검증한다. 가입 확인, 로그인, 새로고침, 로그아웃, 만료 세션과 허용된 콜백을 실제 브라우저에서 시험한다. 실제 사용자 계정이나 이메일 확인 없이 이를 성공했다고 보고하지 않는다.
