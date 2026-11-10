# GitHub 로그인 검증 — 2026-11-10

- REPRODUCED: GitHub 사용자 `akfldk1028`의 OAuth 앱 `Portfolio Agent`를 등록하고 Supabase 프로젝트 `lwescxtcempjhfxqlfyb`의 GitHub 제공자를 활성화했다. 콜백은 프로젝트의 `/auth/v1/callback`이다.
- REPRODUCED: 프로젝트 Auth 설정에서 GitHub 제공자 활성 상태를 확인했다. 로컬 `http://127.0.0.1:15178`에서 GitHub 버튼 → GitHub 권한 승인(이메일 읽기) → Supabase 콜백 → 프로젝트 목록 진입을 확인했다. GitHub로 로그인한 계정으로 격리된 로컬 API에서 `github-login-test` 프로젝트를 생성했다.
- 보안: 설정 중 출력된 초기 OAuth 비밀키는 GitHub에서 폐기했고, 새 비밀키로 교체하여 로그인 흐름을 확인했다. 비밀키는 저장소에 기록하지 않았다.
- 제한: OAuth 앱의 홈페이지와 테스트 리디렉션은 현재 로컬 개발 주소다. 공개 배포 전에 실제 도메인과 Supabase 허용 리디렉션을 설정하고 다시 검증해야 한다. Kakao 로그인은 설정하지 않았다. `github-login-test`는 테스트 데이터로 남아 있다.
