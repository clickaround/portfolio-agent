# 선택적 pascal-agents 연동

`agents/pascal-agents`는 별도 저장소이며 이 저장소의 Git 추적이나 submodule에 포함되지 않는다. 기본 포트폴리오 엔진과 테스트에는 필요하지 않다. DiagramAgent, pptAgent 등 별도 도구가 필요할 때만 설치한다.

- 저장소: `https://github.com/akfldk1028/pascal-agents.git`
- 확인된 리비전: `a32be75b6c871923ddc682e75f027a06dc76f2f2` (2026-11-07에 원격 main 및 HEAD 확인)
- 해당 리비전의 `DiagramAgent/LICENSE`, `pptAgent/LICENSE`, `drawingbookAgent/LICENSE`는 각각 MIT. 포함된 외부 구성요소는 각자 별도 라이선스를 확인한다.

## 새 설치 (PowerShell, 작업공간 루트)

기존 디렉터리는 덮어쓰지 않는다. 명령 실패 시 중단하고 생성된 디렉터리와 오류를 확인한다.

```powershell
$target = Join-Path (Get-Location) 'agents/pascal-agents'
$revision = 'a32be75b6c871923ddc682e75f027a06dc76f2f2'
if (Test-Path -LiteralPath $target) { throw "Target already exists; preserve it: $target" }
git clone --no-checkout https://github.com/akfldk1028/pascal-agents.git $target
if ($LASTEXITCODE -ne 0) { throw 'Clone failed; inspect the target before retrying.' }
git -C $target checkout --detach $revision
if ($LASTEXITCODE -ne 0) { throw 'Pinned checkout failed; inspect the target before retrying.' }
$actual = (git -C $target rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actual -ne $revision) { throw 'Revision verification failed.' }
git -C $target status --short
if ($LASTEXITCODE -ne 0) { throw 'Status check failed.' }
```

고정 커밋의 소스만 받는다. 의존성 설치나 도구 실행은 각 에이전트의 안내와 라이선스 검토 후 별도로 수행한다. 작업 중인 기존 체크아웃이 있으면 위 명령을 실행하지 말고 아래의 읽기 전용 검사만 사용한다. 미커밋 변경이 있으면 커밋 해시가 같아도 고정 커밋과 실행 내용이 같다고 볼 수 없다.

## 기존 설치 확인 (변경 없음)

```powershell
git -C agents/pascal-agents remote -v
git -C agents/pascal-agents rev-parse HEAD
git -C agents/pascal-agents status --short
```

origin, 전체 커밋 ID와 작업 트리를 함께 확인한다. 로컬 수정 사항은 사용자의 자료이므로 자동 초기화·삭제·업데이트하지 않는다. 원격 main은 시간이 지나며 변경될 수 있다.
