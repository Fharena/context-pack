# Context Pack

<p align="center">
  <strong>Codex, Claude, Cursor 같은 코딩 에이전트를 위한 version-aware context pack generator.</strong>
</p>

<p align="center">
  <a href="https://github.com/Fharena/context-pack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Fharena/context-pack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/actions/workflows/release.yml"><img alt="Release workflow" src="https://github.com/Fharena/context-pack/actions/workflows/release.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/releases/tag/v0.2.17"><img alt="Release" src="https://img.shields.io/github/v/release/Fharena/context-pack?display_name=tag"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="#설치">설치</a> ·
  <a href="#터미널-데모">터미널 데모</a> ·
  <a href="#작동-방식">작동 방식</a> ·
  <a href="docs/RELEASE.ko.md">릴리즈 가이드</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Fharena/context-pack/main/assets/demo.gif" alt="Context Pack 터미널 데모" width="820">
</p>

Stop paying agents to rediscover your repo.

한국어로 풀면, 에이전트가 매번 repo를 다시 읽고 헤매는 비용을 줄이자는 뜻입니다.

Context Pack은 repo 안에 작은 프로젝트 도서관을 만들고, git 상태를 checkpoint하고, 작업별로 필요한 문서와 파일만 모은 compact `.context-pack/packs/CONTEXT_PACK.md`를 생성합니다. 핵심은 "AI memory"가 아니라 **지금 작업에 필요한 것만 먼저 읽게 하는 context router**입니다.

요즘 코딩 에이전트 작업은 로컬 IDE 한 곳에만 머물지 않습니다. Codex app/cloud worktree, Claude 원격 작업, Cursor, CLI, 다른 기기 사이를 오가게 됩니다. 작업 위치가 바뀌면, repo 자체가 최소한의 지도를 들고 있어야 합니다.

## 누구에게 맞는가

Context Pack은 이런 사람에게 맞습니다.

- Codex, Claude, Cursor, cloud worktree, 로컬 IDE, 원격 머신 사이를 오가며 작업하는 사람
- 코드 리뷰 때 에이전트가 repo 전체가 아니라 위험한 파일부터 보게 만들고 싶은 사람
- 미래의 AI contributor가 작은 최신 지도를 들고 시작하길 원하는 maintainer
- 한 벤더의 memory 기능이 아니라 git에 같이 실리는 markdown context를 원하는 사람

아주 작은 throwaway repo, 한 번짜리 프롬프트, 짧은 `AGENTS.md` 하나로 충분한 프로젝트에는 과합니다.

## 왜 필요한가

AI 코딩에서 비용이 많이 드는 순간은 코드 작성 자체보다, 작업 시작 전에 다음을 다시 찾는 과정입니다.

- 어떤 파일부터 읽어야 하는지
- 어떤 테스트가 관련 있는지
- 깨지면 안 되는 계약이나 불변조건이 무엇인지
- 이전 작업 메모가 지금 git 상태와 맞는지
- 코드 리뷰에서 어떤 위험을 먼저 봐야 하는지

Context Pack은 이 반복 탐색을 repo 안의 작은 도서관으로 바꿉니다.

- `.context-pack/INDEX.md`와 `.context-pack/AREAS/*.md`: 프로젝트 영역별 인덱스와 리뷰 라우터
- `.context-pack/CURRENT.md`: 현재 작업 상태와 다음 세션용 체크포인트
- `.context-pack/packs/CONTEXT_PACK.md`: 이번 작업에 필요한 파일, 계약, 테스트, 주의점만 모은 임시 컨텍스트 팩

## 여러 세션과 원격 작업을 위한 도구

한 작업이 꼭 한 세션에서 끝나지 않습니다. 로컬 IDE에서 시작했다가, Codex app에서 이어가고, cloud worktree에서 수정하고, 다른 기기에서 리뷰할 수 있습니다. 이때 매번 처음부터 repo를 다시 읽으면 비용도 들고 실수도 늘어납니다.

Context Pack은 repo가 다음 정보를 들고 다니게 합니다.

- 마지막 checkpoint의 checkout과 git 상태
- 변경 파일이 속한 프로젝트 영역
- 리뷰 때 확인해야 할 계약과 테스트
- stale 가능성이 있는 문서와 검증 필요 지점
- commit하면 안 되는 generated/local 파일

## 설치

Codex에서 가장 짧은 GitHub 직접 실행 경로입니다.

```bash
npx github:Fharena/context-pack install-codex --activate
```

이 경로는 `PATH`에 Node와 Python 3.11+가 필요합니다. Codex CLI가 `PATH`에 없다면 `--activate`를 빼고, 출력되는 `codex plugin add ...` 명령을 나중에 실행하면 됩니다.

그 다음 사람은 명령어를 외울 필요 없이 에이전트에게 이렇게 말하면 됩니다.

```text
Use $context-pack to set up this repo.
Use $context-pack to start work on this bug.
Use $context-pack to checkpoint this work.
```

에이전트가 내부 엔진을 실행하고, 생성된 pack을 읽고, 필요한 파일부터 이어서 봅니다. Context Pack이 설정된 repo에서는 에이전트가 도구 이름을 듣지 않아도, 큰 작업 시작 전 / 코드 리뷰 전 / 낯선 디버깅 전 / handoff 전에 `context-pack start`를 스스로 실행하는 흐름을 목표로 합니다.

이미 CLI를 설치했다면 Codex plugin은 이렇게 설치하거나 갱신할 수 있습니다.

```bash
context-pack install-codex --activate
```

Codex가 아니거나 터미널에서 직접 repo를 설정하고 싶다면:

```bash
npx github:Fharena/context-pack measure --task "fix login timeout"
npx github:Fharena/context-pack setup --dry-run
npx github:Fharena/context-pack setup
npx github:Fharena/context-pack start
npx github:Fharena/context-pack start --task "fix login timeout"
npx github:Fharena/context-pack start --review --base main
```

Python tooling을 선호하거나 CLI를 영구 설치하고 싶다면:

```bash
pipx install git+https://github.com/Fharena/context-pack.git
context-pack setup
```

CLI를 영구 설치하지 않고 한 번 시험해보고 싶다면:

```bash
pipx run --spec git+https://github.com/Fharena/context-pack.git context-pack setup
```

`npx` 경로는 같은 Python engine을 얇게 감싸는 방식입니다. Node 중심 사용자에게 Python 패키지를 먼저 설치하라고 요구하지 않기 위한 진입점입니다.

아래 예시는 읽기 쉽게 `context-pack`으로 적습니다. GitHub `npx` 경로를 계속 쓴다면 `context-pack` 자리에 `npx github:Fharena/context-pack`를 붙이면 됩니다.

다음에 뭘 실행할지 모르겠다면 인자 없이 `context-pack`만 실행해 quickstart를 볼 수 있습니다. 설치 버전은 `context-pack --version`으로 확인합니다.

`measure`는 setup 전에 실행할 수 있습니다. `.context-pack/`가 없으면 source/test/docs/automation 영역을 메모리에서만 추론하고 아무 파일도 쓰지 않으므로, repo를 바꾸기 전에 예상 context 절감을 먼저 볼 수 있습니다. `fix login timeout`처럼 아직 특정 영역과 매칭되지 않는 일반 코드 작업은 overview만 보지 않고 첫 실행부터 `source`와 `tests`에서 시작합니다.
`setup`은 repo context library, handoff 문서, `.gitignore` 항목, `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/context-pack.mdc` 공통 agent rule을 한 번에 만듭니다.
먼저 무엇을 건드리는지 확인하고 싶다면 `setup --dry-run`을 실행하세요. 실제 파일이나 hook을 쓰지 않고 create/update/append/refresh/leave unchanged 계획을 구분해서 보여주며, 선택한 옵션을 보존한 적용 명령도 함께 출력합니다.
첫 setup에서는 `source`, `tests`, `docs`, `automation` 같은 일반 경로가 있으면 초기 area를 추론합니다. 이후 setup 재실행은 기존 `.context-pack/manifest.json`을 기본적으로 보존합니다. 새로 생긴 경로를 area로 추가하고 싶을 때만 `setup --infer-areas`를 쓰고, 첫 설치도 overview만 만들고 싶다면 `setup --no-infer-areas`를 쓰세요.

이미 context library가 있고 공통 agent rule만 갱신하고 싶다면:

```bash
context-pack install-agent-docs
```

두 명령 모두 Context Pack 관리 블록 밖의 기존 문서는 보존합니다. `.context-pack/` 도서관만 만들고 싶다면 `setup --agent-docs none`을 쓰고, 특정 agent doc만 원하면 `install-agent-docs --target claude` 또는 `--target cursor`를 쓰면 됩니다.

예전 `.codex/context` 도서관을 이미 쓰고 있다면:

```bash
context-pack migrate
```

`.context-pack/`가 없을 때는 기존 layout도 계속 읽지만, 새 setup은 벤더 중립 경로인 `.context-pack/`를 기본으로 씁니다.

## 로컬 설치 옵션

clone한 repo에서 Codex plugin으로 설치:

```powershell
python plugins/context-pack/scripts/context_pack.py install-codex --force --activate
```

Codex skill만 설치:

```powershell
python scripts/install_skill.py
```

아무것도 설치하지 않고 source에서 직접 실행:

```powershell
python plugins/context-pack/scripts/context_pack.py setup
python plugins/context-pack/scripts/context_pack.py start --review --base main
```

repo-scoped Codex marketplace도 포함되어 있습니다.

```text
.agents/plugins/marketplace.json
```

clone한 repo 자체를 local Codex plugin marketplace로 추가하면, 이 repo 안의 plugin을 바로 발견할 수 있습니다.

```bash
codex plugin marketplace add .
codex plugin add context-pack@context-pack
```

## 터미널 데모

```text
$ context-pack measure --task "improve agent CLI onboarding" --max-areas 3 --max-read-first 8
Context Pack Measure for /work/context-pack
Git: yes; branch: main; HEAD: 67f7355488c
Context library: ok
Mode: work
Task: improve agent CLI onboarding
No files written.

Selected areas: installer-release, engine, skill-plugin
Why selected:
- installer-release: task matched keywords: cli, onboarding
- engine: task matched keywords: agent
- skill-plugin: task matched keywords: agent
Related areas: overview
Why related:
- overview: task matched keywords: onboarding
Scope reduction: start from 3 area(s) instead of scanning 50 repo file(s)
Read First entries: 8 (~16% of repo files)
Approx text budget: Read First ~17.0k tokens from 8 file(s) (~14% of repo text); repo ~117.8k tokens from 49 text file(s)

Run next:
- context-pack start --task "improve agent CLI onboarding"

$ context-pack start --task "improve agent CLI onboarding" --max-areas 3 --max-read-first 8
Context Pack Start for /work/context-pack
Git: yes; branch: main; HEAD: 67f7355488c0
Context library: ok
Dirty files: 0; diff hash: clean

Generated work pack for task: .context-pack/packs/CONTEXT_PACK.md
Selected areas: installer-release, engine, skill-plugin
Why selected:
- installer-release: task matched keywords: cli, onboarding
- engine: task matched keywords: agent
- skill-plugin: task matched keywords: agent
Scope reduction: start from 3 area(s) instead of scanning 50 repo file(s)
Approx text budget: Read First ~17.0k tokens from 8 file(s) (~14% of repo text); repo ~117.8k tokens from 49 text file(s)

Read next:
- .context-pack/packs/CONTEXT_PACK.md
- .context-pack/AREAS/installer-release.md
- .context-pack/AREAS/engine.md
- .context-pack/AREAS/skill-plugin.md

$ Get-Content .context-pack/packs/CONTEXT_PACK.md -TotalCount 40
# Context Pack

Mode: work

## Scope Reduction
- Repo files considered: 50
- Primary areas selected: 3 of 5
- Read First entries: 8 (~16% of repo files)
- Changed files in scope: 0
- Approx Read First text: ~17.0k tokens from 8 file(s) (~14% of repo text)
- Approx repo text: ~117.8k tokens from 49 text file(s)
- Token estimates use chars/4 and skip binary, unreadable, ignored, and >1 MB files.

## Selected Areas
- installer-release (score 12): task matched keywords: cli, onboarding
- engine (score 6): task matched keywords: agent
- skill-plugin (score 6): task matched keywords: agent

## Related Areas
- overview (score 3): task matched keywords: onboarding

## Read First
- .context-pack/AREAS/installer-release.md
- README.md
- README.ko.md
- CHANGELOG.md
- pyproject.toml

## Read Later
- .context-pack/AREAS/skill-plugin.md
- plugins/context-pack/skills/context-pack/SKILL.md
- .context-pack/AREAS/engine.md

## Contracts To Check
- The engine must remain stdlib-only so it can run from a skill, plugin, or copied checkout.
- ... more contract(s) omitted; inspect area docs if needed
```

목표는 source code를 대체하는 것이 아닙니다. 에이전트가 올바른 서가에서 시작하게 만드는 것입니다.

## 기본 사용 흐름

터미널에서 직접 쓸 때의 흐름입니다. Codex plugin으로 설치했다면 보통 명령어를 직접 치지 않고 `Use $context-pack ...`라고 말하면 됩니다.

작업 시작 전:

```powershell
context-pack measure --task "고치려는 버그나 작업 설명"
context-pack start --task "고치려는 버그나 작업 설명"
```

`measure`는 read-only입니다. `.context-pack/packs/CONTEXT_PACK.md`를 쓰지 않고 selected area, Read First 항목, 대략적인 text budget만 먼저 보여줍니다.

코드 리뷰 전:

```powershell
context-pack start --review --base main
```

작업 후:

```powershell
context-pack checkpoint --pack
```

상태 검증:

```powershell
context-pack doctor
```

source 확인 후 stale warning을 닫을 때:

```powershell
context-pack mark-reviewed runtime tests
```

## 핵심 기능

| 기능 | 줄여주는 것 |
| --- | --- |
| `setup` | context library, handoff 문서, `.gitignore`, 공통 agent rule, doctor check까지 한 번에 처리. `setup --dry-run`으로 계획을 미리 보고, `--infer-areas`로 새 추론 area를 명시적으로 추가하거나 `--no-infer-areas`로 overview-only 설치 가능 |
| `measure` | read-only proof: generated pack을 쓰지 않고 selected area, scope reduction, 대략적인 text budget을 미리 보여줌 |
| `start` | 처음 진입 명령 하나로 자동 init, task pack, review pack, changed-files pack 선택 |
| `install-codex` | package나 clone에서 Codex plugin과 personal marketplace entry 설치 |
| `install-agent-docs` | `AGENTS.md`, `CLAUDE.md`, Cursor project rules에 공통 Context Pack 규칙 작성 |
| `init` | repo-local context library, handoff 문서, source/test/docs 영역 자동 생성 |
| `migrate` | 기존 `.codex/context`, `.codex/handoff` 문서를 `.context-pack/`로 복사 |
| `status` | context health, 예상 영역, stale warning, 다음 행동 표시 |
| `checkpoint` | branch, HEAD, dirty files, diff hash를 기본적으로 ignored local state에 기록 |
| `pack` / `pack --changed` | selected/related 영역으로 나뉜 compact 작업별 또는 changed-files reading pack 생성 |
| `review-pack` | dirty files 또는 `--base` 기준 compact 코드 리뷰 팩 생성 |
| `mark-reviewed` | 확인한 area doc을 현재 HEAD 기준 reviewed로 표시 |
| `doctor` | context library가 정상인지 검증하고, `doctor --fix`로 누락된 setup 파일 복구 |
| `install-git-hooks` | 선택적 repo-local checkpoint 자동화 |

## Agent-first UX

```text
Use $context-pack to set up Context Pack in this repo.
Use $context-pack to make a context pack for this bug.
Use $context-pack to review this branch against main.
Use $context-pack to checkpoint this work.
Initialize context-pack in this repo.
Build a review context pack for my changes.
Checkpoint this work for the next session.
이 버그 고치기 전에 context pack 만들어.
작업 끝났으니 checkpoint 해줘.
```

더 중요한 흐름은 암묵적 사용입니다.

- repo를 넓게 읽기 전: `context-pack start --task "..."`
- Context Pack이 없을 때: `context-pack setup`
- setup이 깨진 것 같을 때: `context-pack doctor --fix`
- 리뷰 전: base를 알면 `context-pack start --review --base <base-ref>`
- 낯선 디버깅 전: 여러 파일을 열기 전에 task pack 생성
- 의미 있는 수정/리뷰 후: git을 더럽히지 않게 `checkpoint --pack`으로 local checkpoint
- handoff 자체를 git으로 공유해야 할 때: `checkpoint --publish --pack`
- source 확인 후: `mark-reviewed <area>`로 stale warning 닫기

Codex, Claude, Cursor 사이를 오가는 개인/팀 repo라면 `context-pack install-agent-docs`를 한 번 실행해 각 에이전트가 같은 proactive rule을 보게 만드는 것이 좋습니다.

에이전트는 보통 다음 순서로 읽으면 됩니다.

1. `.context-pack/CURRENT.md`
2. `.context-pack/INDEX.md`
3. `.context-pack/packs/CONTEXT_PACK.md`
4. 관련 `.context-pack/AREAS/*.md`
5. 실제 코드 파일

## AGENTS.md나 CLAUDE.md만 쓰면 안 되나?

써야 합니다. Context Pack은 그것들을 대체하지 않습니다.

`AGENTS.md`, `CLAUDE.md`, `.cursor/rules` 같은 파일은 오래 유지되는 instruction layer입니다. 코딩 스타일, 명령어, 정책, 프로젝트 규칙을 담기 좋습니다. Context Pack은 그 옆의 routing layer입니다.

- branch, HEAD, dirty files, diff hash를 기록합니다.
- 변경 파일이나 작업 설명을 관련 영역 문서로 매핑합니다.
- 이번 작업/리뷰에 필요한 임시 read-first pack을 만듭니다.
- 요약 문서가 stale일 수 있으면 경고합니다.
- durable context는 git에 남기고 generated/local context는 ignore합니다.

즉 에이전트는 rule file에서 “어떻게 행동할지”를 읽고, Context Pack에서 “어디부터 볼지”를 읽습니다.

`context-pack install-agent-docs`는 이 두 레이어를 연결합니다. 에이전트가 원래 읽는 파일에 행동 규칙을 넣고, `.context-pack/`와 generated pack은 특정 벤더 memory에 묶이지 않는 동적 routing state로 둡니다.

## Context Pack은 무엇이 다른가?

Context Pack은 몇 가지 익숙한 아이디어와 겹치지만, 일부러 범위를 좁게 잡습니다.

| 대안 | 잘하는 것 | Context Pack이 더하는 것 |
| --- | --- | --- |
| `AGENTS.md`, `CLAUDE.md`, editor rules | 오래 유지되는 행동 지침 | branch, HEAD, dirty files, stale area docs, task/review pack을 기준으로 한 version-aware routing |
| vendor memory / project knowledge | 특정 에이전트 안의 recall | Codex, Claude, Cursor, cloud worktree, 로컬 머신 사이를 git과 함께 이동하는 Markdown context |
| RAG / vector DB | 큰 corpus의 semantic retrieval | 서비스, index server, embedding, 숨은 ranking state 없이 검토 가능한 deterministic routing |
| context dumper | 파일 묶음을 빠르게 전달 | area ownership, Read First / Read Later, contracts, failure modes, stale warning |

핵심은 "더 많은 memory"가 아닙니다. repo가 에이전트에게 어디부터 봐야 하는지, 어떤 문서가 stale일 수 있는지, 어떤 체크가 중요한지를 먼저 알려주는 것입니다.

## Area 선택과 모노레포

Context Pack의 첫 번째 선택 로직은 일부러 단순하고 확인 가능하게 둡니다.

- `setup` / `init`은 첫 설치 때 일반적인 source, test, docs, automation 경로를 보고 초기 area를 추론합니다. 이후 재실행은 `--infer-areas`를 명시하지 않으면 사용자가 정리한 manifest를 보존합니다.
- 변경 파일은 area path glob과 매칭됩니다.
- 작업 설명의 keyword가 area score를 올릴 수 있습니다. 단, 흔한 stop word는 무시해서 일반적인 문장이 관련 없는 area를 선택하지 않게 합니다.
- pack은 selected areas, related areas, Read First, Read Later로 context를 나눕니다.
- stale warning은 area doc이 검토된 git 상태와 현재 git 상태를 비교합니다.

그래서 예측 가능하지만 마법은 아닙니다. 복잡한 모노레포에서는 `.context-pack/manifest.json`과 `.context-pack/AREAS/*.md`를 실제 ownership 경계에 맞게 손보는 편이 좋습니다. area가 너무 넓으면 쪼개고, pack이 시끄러우면 `--max-areas` / `--max-read-first`를 낮추거나 path glob을 조정하고, source 확인 후 `mark-reviewed`로 stale warning을 닫습니다.

현재 scoring은 semantic understanding engine이 아니라 routing heuristic입니다. 이건 의도입니다. 에이전트가 소스 코드를 읽기 전에, 어떤 파일과 경고가 왜 선택됐는지 Markdown만 봐도 설명 가능해야 합니다.

## 현재 범위

Context Pack은 hosted platform이 아니라 작은 repo-local 도구입니다. 지금은 small-to-medium 프로젝트, 에이전트 사용이 많은 개인 repo, AI contributor가 들어오는 오픈소스 repo, 로컬/클라우드 에이전트 세션을 오가는 팀에 가장 잘 맞습니다.

공개 설치 경로는 현재 GitHub를 통한 `pipx` 또는 `npx` 실행입니다. Registry 배포는 opt-in이지만, release workflow는 이미 Python wheel/sdist와 npm tarball을 빌드/검증하고 GitHub Release assets로 업로드합니다. CI는 Windows/Ubuntu, Python 3.11/3.12, package, Codex plugin, Node wrapper, npm tarball smoke path를 확인합니다.

## 작동 방식

Context Pack은 vector DB나 일반적인 memory bank가 아닙니다. git 상태를 기준으로 stale 여부를 의심하고, 지금 작업에 필요한 파일과 문서만 고르는 라우팅 레이어입니다.

Python script가 맡는 일:

- git 상태 수집
- dirty file 목록
- diff hash
- repo onboarding과 공통 agent rule을 위한 원커맨드 `setup`
- 설치된 package나 source checkout에서 Codex plugin 설치
- Python tooling에서 시작하지 않는 개발자를 위한 GitHub `npx` wrapper
- `AGENTS.md`, `CLAUDE.md`, Cursor project rules에 공통 repo rule 설치
- 첫 진입용 `start`: 필요한 경우 init하고 task/review/changed-files pack 선택
- 첫 init 시 source/test/docs/automation 영역 자동 추론
- changed-file path matching과 task keyword 기반 area scoring
- selected/related 영역을 나누는 compact pack 생성
- 얼마나 읽기를 줄였는지 보여주는 scope-reduction과 대략적인 text-budget metrics
- Read First / Read Later 분리
- contract와 failure mode 중복 제거
- stale warning
- context health status와 reviewed-state 업데이트
- 누락된 setup 파일을 복구하는 `doctor --fix`
- hook 설치
- doctor 검증

AI가 시간이 지나며 개선할 수 있는 일:

- area 요약 개선
- 프로젝트 계약 정리
- common failure modes 작성
- 중요한 결정 기록

처음부터 사람이 taxonomy를 다 손으로 만들 필요는 없습니다. `init`은 repo 안의 파일 구조를 보고 쓸만한 기본 영역을 만들고, 의미 있는 refinement는 실제 작업을 하면서 쌓는 구조입니다.

## Git 정책

기본적으로 추적할 파일:

```text
.context-pack/manifest.json
.context-pack/INDEX.md
.context-pack/REVIEW.md
.context-pack/CONTRACTS.md
.context-pack/AREAS/*.md
.context-pack/CURRENT.md
.context-pack/LOG.md
.context-pack/DECISIONS.md
```

기본적으로 ignore할 파일:

```text
.context-pack/packs/
.context-pack/tmp/
.context-pack/local/LOCAL.md
```

자동 에이전트 checkpoint는 기본적으로 `.context-pack/local/LOCAL.md`와 `.context-pack/packs/`에 기록되므로, 일반적인 작업 종료 checkpoint는 tracked 파일을 더럽히지 않습니다. handoff 자체를 git에 남겨야 할 때만 `context-pack checkpoint --publish --pack`을 사용합니다.

컨텍스트 도서관과 durable handoff는 다음 사람/에이전트에게 전달될 수 있지만, 생성된 임시 pack과 로컬 경로 정보는 repo에 남기지 않는 편이 안전합니다.

## 자동화

선택 기능입니다. Context Pack을 쓰기 위해 꼭 필요하지는 않습니다.

기본 자동화 모델은 에이전트 행동입니다. skill과 repo `AGENTS.md`, `CLAUDE.md`, Cursor rules가 에이전트에게 작업 시작, 리뷰, 디버깅, handoff 경계에서 Context Pack을 스스로 쓰라고 알려줍니다. `checkpoint`는 기본적으로 ignored local state에 쓰기 때문에 에이전트가 작업단위 끝마다 실행해도 tracked handoff 문서를 더럽히지 않습니다. git hook은 checkout, merge, commit 같은 git 경계에서만 작동하는 보조 안전망입니다.

repo-local git hook을 설치하면 git 작업 경계에서 checkpoint를 조금 더 자동화할 수 있습니다.

```powershell
context-pack install-git-hooks --mode safe
```

safe mode:

- `pre-commit`: `doctor` 실행
- `post-checkout`: branch 변경 후 checkpoint
- `post-merge`: pull/merge 후 checkpoint

aggressive mode는 commit 이후 checkpoint도 추가합니다.

```powershell
context-pack install-git-hooks --mode aggressive
```

제거:

```powershell
context-pack uninstall-git-hooks
```

## 검증

```powershell
python -m unittest discover -s tests -v
python -m json.tool plugins/context-pack/.codex-plugin/plugin.json
python -m json.tool .agents/plugins/marketplace.json
python -m pip install -e .
context-pack --help
context-pack doctor --fix --help
node bin/context-pack.js --help
python -m pip install build twine
python -m build
python -m twine check dist/*
npm pack --dry-run
python scripts/validate_packaged_cli.py
```

GitHub Actions에서는 Windows/Ubuntu, Python 3.11/3.12 조합으로 stdlib unit test, JSON validation, packaged CLI check, Python wheel/sdist check, Node/npm wrapper check를 실행합니다. Release workflow는 tag에서 GitHub Release assets를 빌드하고, Trusted Publishing 설정 후에는 PyPI/npm publish까지 선택적으로 실행할 수 있습니다.

## 릴리즈

변경 기록은 [CHANGELOG.md](CHANGELOG.md)와 [docs/RELEASE.ko.md](docs/RELEASE.ko.md)를 보세요. 현재 릴리즈: [v0.2.17](https://github.com/Fharena/context-pack/releases/tag/v0.2.17).
