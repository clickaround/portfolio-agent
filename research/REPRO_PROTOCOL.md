# Reproduction protocol — install first only when approved

1. `repos.lock.json`에서 SHA를 가져온다. user workspace 밖의 `.cache/vendor/<repo>`에 clone/fetch하고 detached SHA 체크아웃. Git 추적에서 제외.
2. 실제 `README`, `LICENSE`, scripts, package manifests, test configs를 읽는다. 모델 다운로드/유료 API/추가 계정은 별도 승인.
3. 최소 테스트를 **독립 환경**에서 실행하고 환경(OS, Python, Node, commit SHA, package lock, model ID)을 기록한다.
4. 각 비교마다 입력 fixture SHA256, 명령, 종료 코드, 생성 파일 SHA256, 렌더 PNG/PDF, 실제 비용/시간을 남긴다.
5. 참조 사례와 같은 디자인을 베끼는 것이 아니라, 동일 **사용자 콘텐츠**에 대한 **서로 다른 정당한 구성**을 평가한다.
6. 저장소에 없는 CLI 명령이나 데이터셋 경로를 추측하지 않는다. 설치 성공 전까지 `NOT_RUN`.

## Candidate smoke-test entrypoints (README와 버전 확인 후 실행)
- GDB: `pip install -e .` (환경 격리 후) → `gdb verify` (공개 README 예제; 실행 전 종속성 확인).
- Diagram Design: `npx skills add cathrynlavery/diagram-design` 또는 클론 후 해당 레포의 self-check (사용자 환경에 대한 설치 승인 필요).
- GenOffice / OpenPencil: 각 README의 CLI/MCP 최소 `help`, `version`, `export` (여기에는 확정 명령을 기입하지 않음).
- HarnessRouter: Docker image 별도 약 4 GB 용량·provider API key 필요. P08 전 설치 금지.

## Report template
```yaml
repo: owner/name
sha: exact commit
platform: OS/Python/Node/Browser
model: exact id or none
fixture_hash: sha256
command: exact text
exit_code: 0 | nonzero
artifacts: [path + sha256]
observed_result: short statement
unverified_claims: []
cost_usd: measured | not_measured
status: SMOKE_PASSED | FAILED | BLOCKED
```
