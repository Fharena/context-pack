# Context Pack

<p align="center">
  <strong>Codex, Claude, Cursor 같은 코딩 에이전트를 위한 version-aware context pack generator.</strong>
</p>

<p align="center">
  <a href="https://github.com/Fharena/context-pack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/Fharena/context-pack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://github.com/Fharena/context-pack/releases/tag/v0.1.0"><img alt="Release" src="https://img.shields.io/github/v/release/Fharena/context-pack?display_name=tag"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="#빠른-시작">빠른 시작</a> ·
  <a href="#터미널-데모">터미널 데모</a> ·
  <a href="#작동-방식">작동 방식</a>
</p>

<p align="center">
  <img src="assets/demo.gif" alt="Context Pack 터미널 데모" width="820">
</p>

Stop paying agents to rediscover your repo.

한국어로 풀면, 에이전트가 매번 repo를 다시 읽고 헤매는 비용을 줄이자는 뜻입니다.

Context Pack은 repo 안에 작은 프로젝트 도서관을 만들고, git 상태를 checkpoint하고, 작업별로 필요한 문서와 파일만 모은 `.codex/packs/CONTEXT_PACK.md`를 생성합니다. 핵심은 "AI memory"가 아니라 **지금 작업에 필요한 것만 먼저 읽게 하는 context router**입니다.

요즘 코딩 에이전트 작업은 로컬 IDE 한 곳에만 머물지 않습니다. Codex app/cloud worktree, Claude 원격 작업, Cursor, CLI, 다른 기기 사이를 오가게 됩니다. 작업 위치가 바뀌면, repo 자체가 최소한의 지도를 들고 있어야 합니다.

## 왜 필요한가

AI 코딩에서 비용이 많이 드는 순간은 코드 작성 자체보다, 작업 시작 전에 다음을 다시 찾는 과정입니다.

- 어떤 파일부터 읽어야 하는지
- 어떤 테스트가 관련 있는지
- 깨지면 안 되는 계약이나 불변조건이 무엇인지
- 이전 작업 메모가 지금 git 상태와 맞는지
- 코드 리뷰에서 어떤 위험을 먼저 봐야 하는지

Context Pack은 이 반복 탐색을 repo 안의 작은 도서관으로 바꿉니다.

- `.codex/context/`: 프로젝트 영역별 인덱스와 리뷰 라우터
- `.codex/handoff/`: 현재 작업 상태와 다음 세션용 체크포인트
- `.codex/packs/CONTEXT_PACK.md`: 이번 작업에 필요한 파일, 계약, 테스트, 주의점만 모은 임시 컨텍스트 팩

## 여러 세션과 원격 작업을 위한 도구

한 작업이 꼭 한 세션에서 끝나지 않습니다. 로컬 IDE에서 시작했다가, Codex app에서 이어가고, cloud worktree에서 수정하고, 다른 기기에서 리뷰할 수 있습니다. 이때 매번 처음부터 repo를 다시 읽으면 비용도 들고 실수도 늘어납니다.

Context Pack은 repo가 다음 정보를 들고 다니게 합니다.

- 마지막 checkpoint의 checkout과 git 상태
- 변경 파일이 속한 프로젝트 영역
- 리뷰 때 확인해야 할 계약과 테스트
- stale 가능성이 있는 문서와 검증 필요 지점
- commit하면 안 되는 generated/local 파일

## 빠른 시작

이 repo에서 바로 실행:

```powershell
python plugins/context-pack/scripts/context_pack.py init
python plugins/context-pack/scripts/context_pack.py pack --task "startup bug"
python plugins/context-pack/scripts/context_pack.py review-pack --base main
python plugins/context-pack/scripts/context_pack.py checkpoint --pack
python plugins/context-pack/scripts/context_pack.py doctor
```

Codex skill만 설치:

```powershell
python scripts/install_skill.py
```

Codex plugin으로 설치:

```powershell
python scripts/install_plugin.py
codex plugin add context-pack@personal
```

repo-scoped Codex marketplace도 포함되어 있습니다.

```text
.agents/plugins/marketplace.json
```

clone한 repo 자체를 Codex plugin marketplace로 추가하면, 이 repo 안의 plugin을 바로 발견할 수 있습니다.

## 터미널 데모

```text
$ python plugins/context-pack/scripts/context_pack.py review-pack --base main
Context pack written to .codex/packs/CONTEXT_PACK.md
Selected areas: engine, installer-release, tests

$ Get-Content .codex/packs/CONTEXT_PACK.md -TotalCount 40
# Context Pack

Mode: review

## Selected Areas
- engine
- installer-release
- tests

## Read First
- .codex/context/AREAS/engine.md
- plugins/context-pack/skills/context-pack/scripts/context_pack.py
- tests/test_context_pack.py

## Contracts To Check
- The engine must remain stdlib-only.
- Generated packs must stay under .codex/packs/.
- Hook install must preserve unrelated hook contents.

## Tests
- tests/test_context_pack.py
```

목표는 source code를 대체하는 것이 아닙니다. 에이전트가 올바른 서가에서 시작하게 만드는 것입니다.

## 기본 사용 흐름

처음 한 번:

```powershell
python plugins/context-pack/scripts/context_pack.py init
```

작업 시작 전:

```powershell
python plugins/context-pack/scripts/context_pack.py pack --task "고치려는 버그나 작업 설명"
```

코드 리뷰 전:

```powershell
python plugins/context-pack/scripts/context_pack.py review-pack --base main
```

작업 후:

```powershell
python plugins/context-pack/scripts/context_pack.py checkpoint --pack
```

상태 검증:

```powershell
python plugins/context-pack/scripts/context_pack.py doctor
```

## 핵심 기능

| 기능 | 줄여주는 것 |
| --- | --- |
| `init` | repo-local context library와 handoff 문서 생성 |
| `checkpoint` | branch, HEAD, dirty files, diff hash 기록 |
| `pack` | 작업별 reading pack 생성 |
| `review-pack` | dirty files 또는 `--base` 기준 코드 리뷰 팩 생성 |
| `doctor` | context library가 정상인지 검증 |
| `install-git-hooks` | 선택적 repo-local checkpoint 자동화 |

## 에이전트에게 이렇게 말하면 됩니다

```text
Initialize context-pack in this repo.
Build a review context pack for my changes.
Checkpoint this work for the next session.
이 버그 고치기 전에 context pack 만들어.
작업 끝났으니 checkpoint 해줘.
```

에이전트는 보통 다음 순서로 읽으면 됩니다.

1. `.codex/handoff/CURRENT.md`
2. `.codex/context/INDEX.md`
3. `.codex/packs/CONTEXT_PACK.md`
4. 관련 `.codex/context/AREAS/*.md`
5. 실제 코드 파일

## 작동 방식

Context Pack은 vector DB나 일반적인 memory bank가 아닙니다. git 상태를 기준으로 stale 여부를 의심하고, 지금 작업에 필요한 파일과 문서만 고르는 라우팅 레이어입니다.

Python script가 맡는 일:

- git 상태 수집
- dirty file 목록
- diff hash
- area matching
- pack 생성
- stale warning
- hook 설치
- doctor 검증

AI가 맡는 일:

- area 요약 개선
- 프로젝트 계약 정리
- common failure modes 작성
- 중요한 결정 기록

## Git 정책

기본적으로 추적할 파일:

```text
.codex/context/manifest.json
.codex/context/INDEX.md
.codex/context/REVIEW.md
.codex/context/CONTRACTS.md
.codex/context/AREAS/*.md
.codex/handoff/CURRENT.md
.codex/handoff/LOG.md
.codex/handoff/DECISIONS.md
```

기본적으로 ignore할 파일:

```text
.codex/packs/
.codex/context/tmp/
.codex/handoff/LOCAL.md
```

컨텍스트 도서관과 handoff는 다음 사람/에이전트에게 전달되어야 하지만, 생성된 임시 pack과 로컬 경로 정보는 repo에 남기지 않는 편이 안전합니다.

## 자동화

repo-local git hook을 설치할 수 있습니다.

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode safe
```

safe mode:

- `pre-commit`: `doctor` 실행
- `post-checkout`: branch 변경 후 checkpoint
- `post-merge`: pull/merge 후 checkpoint

aggressive mode는 commit 이후 checkpoint도 추가합니다.

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode aggressive
```

제거:

```powershell
python plugins/context-pack/scripts/context_pack.py uninstall-git-hooks
```

## 검증

```powershell
python -m unittest discover -s tests -v
python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack
python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack
```

GitHub Actions에서는 Windows/Ubuntu, Python 3.11/3.12 조합으로 stdlib unit test와 JSON validation을 실행합니다.

## 릴리즈

변경 기록은 [CHANGELOG.md](CHANGELOG.md)를 보세요. 현재 릴리즈: [v0.1.0](https://github.com/Fharena/context-pack/releases/tag/v0.1.0).
