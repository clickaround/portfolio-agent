# 에이전트 폴더 표준: gitagent + Harness² (2026-11-13)

상태: 적용함(gitagent 깃헙 스펙 대조 포함). 기준 폴더는 `agents/baseAgent/`이고 sourcePrepAgent, portfolioAgent, reviewAgent가 따른다. `agents/baseAgent/scripts/check_base.py`와 아키텍처 테스트가 강제한다.

## 출처

- **Harness²**: "Harness²: Recursive Agent Harnessing for an Open World", arXiv 2610.14224 (2026-10, Google Cloud AI Research와 Northwestern).
  - DOC_REPORTED: 2.1절, 2.3절, 부록 D.1, D.2 끝부분, D.3 표 5, 편집기 프롬프트의 규칙. arXiv HTML을 도구로 읽었고 D.2 중간 일부는 잘려서 못 읽었다.
  - CODE_INSPECTED: google-research/harness2 @ 6868817 (Apache-2.0, `.cache/vendor/harness2`). `harness2/core/tree.py`, `core/library.py`, `core/context.py`, `substrate/opencode.py`, `substrate/codex.py`, 기준 하네스 `third_party/jb_runner/harness_baseline_oc/`. 코드는 실행하지 않았다.
- **gitagent**: github.com/open-gitagent/opengap @ d7a8e2e (MIT, `.cache/vendor/opengap`). 2026-11-13에 읽었다.
  - DOC_REPORTED: `spec/SPECIFICATION.md` v0.1.0의 2~13절, 15~19절.
  - CODE_INSPECTED: `spec/schemas/*.schema.json`, `src/commands/validate.ts`, `src/adapters/system-prompt.ts`, `examples/`. 코드는 실행하지 않았다.
- **gitagent 런타임**: github.com/open-gitagent/gitagent @ f4a309c (gitagent 3, Rust, `.cache/vendor/gitagent`). `pascal-agents`가 쓰는 쪽이다.
  - DOC_REPORTED: `README.md`의 Architecture, agent manifest, Coming from the TypeScript gitagent, `docs/HOW-IT-WORKS.md` 1, 9, 13절.
  - CODE_INSPECTED: `crates/loader/src/{manifest,declared,subagents,v1,validate}.rs`, `crates/tools/src/declared.rs`. 실행하지 않았다.
  - 스펙 저장소와 런타임이 다르면 런타임을 따랐다.
- **gitagent 2.2.0** (Node, `agents/pascal-agents/pptAgent/src`, 소유자가 윈도우에서 쓰는 판). CODE_INSPECTED: `loader.ts`, `tool-loader.ts`, `hooks.ts`, `agents.ts`. gitagent 3은 npm에 리눅스와 맥 바이너리만 있어서(REPRODUCED: `npm view @open-gitagent/gitagent`) 윈도우에서는 이 판이 기준이다.
- AHE(arXiv 2604.25850)는 다른 논문이다. Harness²는 AHE의 파일 단위 분해에 미들웨어 플러그인을 더했다.

## baseAgent는 gitagent 3 저장소다

`agents/baseAgent/`는 gitagent 3 저장소(open-gitagent/gitagent @ f4a309c, MIT, 193개 파일)를 `git archive`로 통째로 옮기고 그 위에 Harness² 파일을 얹은 폴더다. gitagent 파일 목록은 `UPSTREAM_FILES.txt`, 얹은 것은 `UPSTREAM.md`에 있다. 겹친 이름은 `README.md` 하나였고, 우리 안내는 `MODULE.md`로 옮겼다. gitagent의 예시 에이전트는 `agent/`에 그대로 있고, 모듈의 에이전트 파일은 폴더 루트에 있다.

세 에이전트(sourcePrepAgent, portfolioAgent, reviewAgent)에는 런타임 소스를 넣지 않았다. 얹은 파일만 같은 구조로 갖는다.

gitagent 3은 리눅스와 맥 바이너리만 배포하고 이 PC에는 Rust가 없어서, 옮긴 소스는 빌드하지도 실행하지도 않았다.

## Harness²의 8가지 구성요소 (표 5)

| 묶음 | # | 구성요소 | Harness² 파일 | 활성 시점 | 역할 |
|---|---|---|---|---|---|
| 컨텍스트 구성 | C1 | 시스템 프롬프트 | `systemprompt.md` | 매 호출 | 모든 과제에 쓰는 페르소나와 최상위 절차 |
| 컨텍스트 구성 | C2 | 가드레일 | `guardrails.md` | 매 호출 | 과제와 도구에 상관없이 지키는 강한 제약 |
| 컨텍스트 구성 | C3 | 기억 | `LongTermMEMORY.md` | 매 호출 | 한 도메인의 과제들이 공유하는 오래가는 사실 |
| 도구 인터페이스 | C4 | 도구 안내 | `tool_descriptions/tool_guidance.md` | 매 호출 | 이미 있는 도구를 언제 어떻게 쓰는가 |
| 오케스트레이션 | C5 | 하위 에이전트 | `sub_agents/<name>/AGENT.md` | task 도구 | 자기 컨텍스트를 가진 위임 작업자, 결과만 돌려준다 |
| 컨텍스트 구성 | C6 | 스킬 | `skills/<name>/SKILL.md`, `skills/<name>/scripts/*` | skill 도구 | 호출될 때만 올라오는 전문 절차 |
| 도구 인터페이스 | C7 | 스크립트 | `scripts/<name>.py` | bash 실행 | 추론하지 않고 실행하는 결정적 기능 |
| 미들웨어 제어 | C8 | 플러그인 | `plugin/<name>.ts` | 도구 루프 안 | 도구 호출과 턴 경계에서 행동을 강제하는 훅 |

C1~C4는 상시(always-on) 파일이고, C5~C8은 필요할 때만 쓰인다. 기준 하네스에서 상시 파일은 비어 있고, 필요할 때 쓰는 폴더에는 그 구성요소가 있다는 것을 알리는 안내 파일이 하나씩 있다.

## Harness²가 검증하는 규칙 (저장소 코드)

1. 상시 파일 4개의 합은 24,000자 이하다. 여기 쓴 글자는 에이전트의 출력 예산과 경쟁한다.
2. 상시 글에는 `{{ }}`나 `{% %}`를 쓰지 않는다(템플릿으로 렌더되어 검증에 실패한다).
3. 스킬은 프런트매터 `name:`이 폴더 이름과 같아야 하고 `description:`이 있어야 한다.
4. 스킬 이름은 상시 글에 한 번은 나와야 한다. 안 나오면 에이전트가 그 스킬을 열지 않는다.
5. 하위 에이전트는 프런트매터 `mode: subagent`와 `description:`이 있어야 한다.
6. 스크립트 이름은 소문자 스네이크케이스이고 컴파일되어야 한다. 스킬이나 상시 글이 부르는 스크립트는 반드시 있어야 한다.
7. 채점 결과, 루브릭, 점수가 든 파일은 하네스나 작업 폴더에 넣지 않는다.
8. 하네스 트리가 원본이고, 호스트가 읽는 자리로는 렌더한다(OpenCode는 `.opencode/`, Codex는 `AGENTS.md` 하나와 `.agents/skills/`).
9. 검증에 실패한 하네스는 통째로 버린다.

`check_base.py`는 1~4, 6의 이름과 컴파일, 7을 검사한다. 5는 gitagent 형식(`agents/<name>/agent.yaml`의 `metadata.mode: subagent`)으로 검사한다. gitagent 쪽은 스펙의 JSON 스키마(`agents/baseAgent/schemas/gitagent/`, MIT 사본)와 위 2~6번을 검사한다. "부르는 스크립트가 있는가"(6의 뒷부분)는 검사하지 않는다. 스킬 본문의 경로가 플러그인 폴더 기준이라서다.

## gitagent 스펙에서 확인한 것

1. 필수는 `agent.yaml`(`name`, `version`, `description`)과 문단이 하나 이상 있는 `SOUL.md`다.
2. `agent.yaml`의 `skills`, `tools`, `agents`에 적은 이름은 `skills/<name>/`, `tools/<name>.yaml`, `agents/<name>/`에 실제로 있어야 한다. `tools`에는 내장 도구 이름(`cli`, `read`, `write`, `edit`, `memory`)도 적는다(런타임). 그래서 선언 도구는 내장 이름을 쓸 수 없고, CLI의 `edit`는 `edit-element`로 선언했다.
3. 도구는 `tools/<name>.yaml`이고 `input_schema.type: object`, `implementation: {type: script, path, runtime: python3}` 형식이다. 스키마에 없는 키는 허용하지 않는다. 런타임은 스크립트를 `tools/`에서 실행하고 인자를 stdin의 JSON 객체 하나로 준다. 그래서 도구마다 `tools/<name>.sh` 실행기가 있고, 실행기가 자기 폴더의 `scripts/tool_entry.py`로 JSON을 `portfolio <명령>` 인자로 바꾼다.
4. 하위 에이전트는 `agents/<name>/agent.yaml` + `SOUL.md`이거나 `agents/<name>.md` 한 파일이다.
5. 훅 이벤트는 `on_session_start`, `on_session_end`, `pre_tool_use`, `post_tool_use`, `on_error`, `pre_response`, `post_response`다. 스크립트는 `hooks/scripts/`에 둔다.
6. `memory/MEMORY.md`는 200줄 이하이고 설정은 `memory/memory.yaml`에 둔다. `knowledge/`에는 `index.yaml`을 둔다.
7. gitagent가 프롬프트에 넣는 것은 순서대로 `SOUL.md`·`RULES.md`·`DUTIES.md`, 내장 작업 지침, 스킬(본문까지), 하위 에이전트, 워크플로, `always_load` 지식, 예시, 컴플라이언스, `memory/MEMORY.md`, `hooks/bootstrap.md`다. **`guardrails/`와 도구 안내는 읽지 않는다.**
8. 하위 에이전트 폴더는 그 자체로 온전한 에이전트이고, 자기 컨텍스트로 돌고 마지막 요약만 돌려준다. Harness² C5와 같은 뜻이다.

7번 때문에 `RULES.md`를 가드레일과 도구 안내에서 생성한다. 전에는 `RULES.md`가 `guardrails/`를 가리키기만 해서 gitagent로 돌리면 가드레일이 빠졌다.

쓰지 않은 gitagent 항목: `DUTIES.md`, `workflows/`, `schedules/`, `examples/`, `plugins/`, `compliance/`, `config/`, `hooks/bootstrap.md`, `hooks/teardown.md`. 모두 선택 사항이다.

주의: gitagent 런타임은 스킬 본문을 모두 프롬프트에 넣는다. Harness²의 24,000자 상한은 C1~C4에만 적용했으므로, gitagent로 돌릴 때 실제 프롬프트는 그보다 길다.

## 합친 구조

gitagent 스펙의 폴더가 바탕이다. Harness²의 8가지는 gitagent에 같은 자리가 있으면 그 자리에 넣고, 없으면(가드레일 폴더, 도구 안내, 스크립트, 매니페스트) Harness²에서 가져와 더한다.

```
agents/<agentName>/
  agent.yaml                 # gitagent 매니페스트 (skills, tools, agents를 이름으로 나열)
  harness.yaml               # Harness² 매니페스트: 8가지 구성요소의 위치
  AGENTS.md                  # gitagent: 다른 도구용 안내. 사람과 코딩 에이전트가 읽는다
  SOUL.md                    # gitagent 정체성 = Harness² C1 시스템 프롬프트 + 스킬 호출 조건
  RULES.md                   # gitagent 제약. guardrails/와 tools/TOOL_GUIDANCE.md에서 생성한다 (직접 고치지 않는다)
  guardrails/
    GUARDRAILS.md            # Harness² C2 가드레일 (원본)
    ENFORCEMENT.md           #    규칙별로 강제하는 코드 위치, 없으면 prose only
  memory/
    MEMORY.md                # gitagent 기억 = Harness² C3 (200줄 이하)
    memory.yaml              # gitagent 기억 설정
  tools/
    TOOL_GUIDANCE.md         # Harness² C4 도구 안내 (원본)
    <tool>.yaml              # gitagent 도구 선언 (CLI 명령 하나당 하나)
    <tool>.sh                #    실행기: stdin JSON -> portfolio CLI
  agents/<name>/             # gitagent 하위 에이전트 = Harness² C5
    agent.yaml               #    metadata.mode: subagent
    SOUL.md
  skills/<name>/SKILL.md     # gitagent 스킬(Agent Skills 표준) = Harness² C6. 여기가 원본
  scripts/<name>.py          # Harness² C7 스크립트 (portfolio.py, tool_entry.py는 사본)
  hooks/
    hooks.yaml               # gitagent 훅 = Harness² C8 플러그인
    guard.json               #    금지 규칙 (에이전트마다 다르다)
    scripts/guard.sh         #    훅 실행기 (gitagent 2.x는 훅을 sh로 시작한다). 사본
    scripts/guard.py         #    훅 본체 (stdin JSON -> allow | block). 사본
  knowledge/index.yaml       # gitagent 지식 목록 (knowledge/가 있을 때)
  src/ tests/                # 엔진 코드. 두 표준 어디에도 속하지 않는다
```

| # | Harness² 파일 | gitagent 자리 | 우리 위치 |
|---|---|---|---|
| C1 | `systemprompt.md` | `SOUL.md` | `SOUL.md` |
| C2 | `guardrails.md` | `RULES.md` | 원본 `guardrails/GUARDRAILS.md`, `RULES.md`로 생성 |
| C3 | `LongTermMEMORY.md` | `memory/MEMORY.md` | `memory/MEMORY.md` |
| C4 | `tool_descriptions/tool_guidance.md` | 없음 | 원본 `tools/TOOL_GUIDANCE.md`, `RULES.md`로 생성 |
| C5 | `sub_agents/<name>/AGENT.md` | `agents/<name>/agent.yaml` + `SOUL.md` | gitagent 형식 + `metadata.mode: subagent` |
| C6 | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | 같음 |
| C7 | `scripts/<name>.py` | 없음 | `scripts/<name>.py` |
| C8 | `plugin/<name>.ts` | `hooks/hooks.yaml`, `hooks/scripts/` | gitagent 형식 |

## 호스트로 렌더

렌더는 두 가지다. 첫째, `RULES.md`는 `guardrails/GUARDRAILS.md`와 `tools/TOOL_GUIDANCE.md`를 이어 붙여 만든다(gitagent가 읽는 자리). 둘째, 스킬의 원본은 소유 에이전트의 `skills/`다. Claude Code와 Codex는 플러그인 폴더에서 스킬을 찾으므로 `agents/baseAgent/scripts/render_host.py`가 `agents/portfolio-plugin/skills/`로 복사한다. 스킬을 고친 뒤에는 이 스크립트를 돌린다. `--check`와 아키텍처 테스트가 두 곳이 같은지 검사한다.

| 소유 | 스킬 |
|---|---|
| sourcePrepAgent | `portfolio-cutout` |
| portfolioAgent | `portfolio-plan`, `portfolio-design-direction`, `portfolio-create`, `portfolio-edit`, `portfolio-format`, `portfolio-diagrams` |
| reviewAgent | `portfolio-review`, `portfolio-experiment` |
| 플러그인 공용 (렌더 대상 아님) | `portfolio-orchestrate`, `portfolio-research`, `portfolio-case-curator`, `diagram-design`(외부 MIT 사본) |

스킬 본문의 상대 경로는 플러그인 폴더 기준으로 쓰여 있다. 실행되는 곳이 플러그인 폴더이기 때문이다.

## 가드레일은 세 군데에 둔다

1. **글 (C2, `guardrails/GUARDRAILS.md`).** 매 호출에 들어간다.
2. **코드 (C8 `hooks/`, 엔진, 공유 코어 `core/guardrails/`).** 실행 경로에서 막는다. 위치는 `guardrails/ENFORCEMENT.md`에 적는다.
3. **권한 (`project/AGENTS.md`).** 배포, 구매, 비밀 접근, 대량 수집 금지와 라이선스 게이트.

글로만 있는 규칙은 지켜진다는 보장이 없다. 코드로 검사할 수 있는 것은 2번으로 옮긴다.

## 경험 라이브러리

자리는 `project/harness/library/`이고 구조는 그 폴더의 README에 있다. Harness²는 과제마다 제안, 탐침, 합성으로 하네스를 고치고, 채택한 트리와 `EXPERIENCE.md`를 도메인별로 쌓는다. 우리는 아직 이 루프를 돌리지 않으며 항목도 없다.

## 에이전트 폴더는 독립 모듈이다

gitagent 런타임은 에이전트 폴더 밖을 가리키는 도구·훅 스크립트를 거부한다. 그래서 공용 파일은 경로로 공유하지 않고 각 폴더에 사본을 둔다. `render_host.py`가 사본을 만들고 `--check`가 같은지 검사한다.

| 사본 | 원본 |
|---|---|
| `scripts/portfolio.py` (CLI 진입점) | `agents/portfolio-plugin/scripts/portfolio.py` (`agents/module.json`의 `extra_copies`) |
| `scripts/tool_entry.py` (stdin JSON -> CLI 인자) | `agents/baseAgent/scripts/tool_entry.py` |
| `hooks/scripts/guard.sh`, `guard.py` (훅 가드) | `agents/baseAgent/hooks/scripts/` |
| `RULES.md` | 그 에이전트의 `guardrails/GUARDRAILS.md` + `tools/TOOL_GUIDANCE.md` |

baseAgent는 포트폴리오를 모른다. 이 프로젝트의 설정은 `agents/module.json`(스킬을 복사할 호스트 폴더, 추가 사본)과 각 에이전트의 `tools/cli.json`(도구가 부르는 CLI)에 있다. baseAgent는 별도 저장소(github.com/akfldk1028/base-agent, 비공개)이고 이 저장소에는 git 서브모듈로 들어온다. 받을 때 `git clone --recurse-submodules`를 쓰거나 받은 뒤 `git submodule update --init`을 한다. baseAgent를 고치면 그 저장소에 커밋하고, 이 저장소에서 `git add agents/baseAgent`로 가리키는 커밋을 올린다.

에이전트마다 다른 것은 데이터다: `hooks/guard.json`(금지 규칙), `tools/<name>.yaml`과 실행기, 가드레일, 스킬.

## 윈도우에서 도는 조건

모듈 자체는 파일이라 운영체제를 가리지 않는다. 걸리는 것은 gitagent가 스크립트를 시작하는 방식이었고, 2.2.0 코드를 읽고 고쳤다.

| gitagent 2.2.0이 하는 일 | 우리 쪽 대응 |
|---|---|
| 훅을 무조건 `sh <스크립트>`로 시작한다 | 훅은 `guard.sh`이고 이것이 `guard.py`를 부른다 |
| 도구는 `implementation.script`만 읽는다 | 도구 선언에 `path`(스펙)와 `script`(2.x)를 둘 다 적는다 |
| 도구를 `runtime` 값 그대로 실행한다 | `runtime: sh`. 윈도우 프로그램이 `bash`를 실행하면 Git의 bash가 아니라 `System32\bash.exe`(WSL)가 잡힌다(REPRODUCED) |
| 파이썬 이름을 정하지 않는다 | 실행기가 `python3`, `python` 순으로 실제로 도는 것을 고른다. 윈도우의 `python3`는 스토어 바로가기라 돌지 않는다(REPRODUCED) |

조건: `sh`가 PATH에 있어야 한다(Git for Windows). 이것은 gitagent 2.x의 훅이 원래 요구하는 조건이다.

## 훅 가드 (C8)

`hooks/hooks.yaml`이 `pre_tool_use`에 `scripts/guard.py`를 등록한다(`fail_open: false`). 규칙은 `hooks/guard.json`에 있다.

| 에이전트 | 막는 것 |
|---|---|
| sourcePrepAgent, portfolioAgent | `sources/`에 쓰기·지우기·옮기기, `_unblind_key` 파일에 접근 |
| reviewAgent | `finalize` 도구 말고 `final/`에 쓰기·복사 |
| reviewAgent의 `fresh-reviewer` | `_unblind_key` 파일에 접근 |

한계: gitagent 런타임에서만 돈다(Claude Code 플러그인 경로에서는 돌지 않는다). 셸 명령은 패턴으로 잡으므로 우회할 수 있다. 엔진 안의 검사(게이트, 해시 결합)가 여전히 주된 강제다.

## 지금 비어 있는 것

- 하위 에이전트는 reviewAgent의 `fresh-reviewer` 하나다. 지금 실행 방식(새 `claude -p`, Read만)을 적은 것이며 이 폴더로 실제 실행해 보지는 않았다.
- baseAgent의 `guard.json`은 규칙이 없다(복사한 뒤 채운다).
- `guardrails/ENFORCEMENT.md`의 엔진 쪽 행은 코드를 읽어서 적었다. 훅 가드 행은 테스트로 실행해 확인했다.

## 확인한 것과 못 한 것

- REPRODUCED: `check_base.py` 네 폴더 PASS, `render_host.py --check` PASS, 전체 테스트 182 passed 1 skipped (2026-11-13). 도구 실행기를 gitagent 2.x 방식(에이전트 폴더에서 `sh tools/<name>.sh`)과 3 방식(`tools/`에서)으로 stdin JSON을 넣어 실행. `portfolio_agent`가 없는 파이썬에서 `uv run`으로 넘어가는 경로. 훅 가드를 `sh hooks/scripts/guard.sh`에 이벤트 JSON을 넣어 실행. 모두 윈도우 11에서 했다. `claude plugin validate agents/portfolio-plugin` 통과(아이콘 없음 경고만).
- Harness² 부록 D.2는 두 번에 나눠 끝까지 읽었다. 추가로 반영한 규칙: 스킬이나 상시 글이 부르는 스크립트는 반드시 있어야 한다(`check_base.py`가 검사).
- 못 한 것: gitagent 프로그램 자체로 이 폴더를 띄워 보는 것. gitagent 3은 윈도우 바이너리가 없고, 2.2.0(`pascal-agents/pptAgent`)은 빌드와 의존성 설치가 안 된 상태다(`dist/`, `node_modules/` 없음). 대신 2.2.0이 도구와 훅을 시작하는 명령을 그대로 재현해 실행했다.
- Codex에서 플러그인을 다시 설치해 보지 않았다. Claude Code는 검증 명령만 돌렸고 세션에서 스킬을 불러 보지는 않았다.
- `pascal-agents`(별도 저장소)에는 적용하지 않았다.
