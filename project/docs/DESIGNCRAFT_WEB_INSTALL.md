# DesignCraft 웹 편집기 설치

저장소 루트에서 `python project/scripts/install_designcraft_web.py`를 실행한다. 공식 v0.17.0 웹 ZIP을 내려받아 고정 SHA-256을 확인하고 `.cache/bin/designcraft/web/dist/designcraft-web-0.17.0/`와 `frontend/public/designcraft-editor/`에 설치한다. 기존 ZIP과 설치 폴더는 덮어쓰지 않는다. 해시 불일치 또는 불완전한 기존 폴더는 보존하고 오류를 보고한다. 기존 폴더가 있으면 무결성을 검증하지 않고 보존하므로 교체는 사용자가 직접 결정한다.

정적 서버는 `.wasm`을 `application/wasm`으로 제공해야 한다. WebGPU는 HTTPS 또는 localhost가 필요하며, WebGL2/CPU 경로가 있다. iframe 저장과 내보내기는 브라우저 다운로드로 이뤄진다. 번들 안의 `HOSTING.md`와 라이선스 및 NOTICE를 유지한다.

웹 편집기는 원본 DesignCraft 화면이다. 로컬 앱과 글꼴 및 링크 자산 가용성이 달라 출력이 달라질 수 있다. 파일을 열고 저장한 뒤 자산, 글꼴, 레이아웃과 검토 상태를 다시 확인해야 한다.
