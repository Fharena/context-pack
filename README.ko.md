# Context Pack

[English README](README.md)

Context Pack은 Codex, Claude, Cursor 같은 코딩 에이전트가 매번 프로젝트 구조를 다시 탐색하지 않도록, repo 안에 작은 컨텍스트 도서관과 작업별 컨텍스트 팩을 만드는 도구입니다.

핵심 메시지:

> Stop paying agents to rediscover your repo.

한국어로 풀면:

> 에이전트가 매번 repo를 다시 읽고 헤매는 비용을 줄이자.

## 왜 필요한가

AI 코딩에서 비용이 많이 드는 순간은 코드 작성 자체보다, 작업 시작 전에 다음을 다시 찾는 과정입니다.

- 어떤 파일부터 읽어야 하는지
- 어떤 테스트가 관련 있는지
- 깨지면 안 되는 계약이나 불변조건이 무엇인지
- 이전 작업 메모가 지금 git 상태와 맞는지
- 코드 리뷰에서 어떤 위험을 먼저 봐야 하는지

Context Pack은 이 정보를 repo 안에 관리하고, 작업이나 리뷰마다 작은 `.codex/packs/CONTEXT_PACK.md`를 생성합니다. 에이전트는 전체 repo를 훑기 전에 이 팩을 먼저 읽습니다.

## 파일 구조

```text
.codex/
  context/
    manifest.json
    INDEX.md
    REVIEW.md
    CONTRACTS.md
    AREAS/
      overview.md
      engine.md
      ...
  handoff/
    CURRENT.md
    LOG.md
    DECISIONS.md
    LOCAL.md
  packs/
    CONTEXT_PACK.md
```

역할:

- `.codex/context/`: 프로젝트 도서관. 영역별 시작 파일, 테스트, 계약, 실패 패턴을 담습니다.
- `.codex/handoff/`: 현재 작업 상태. branch, HEAD, dirty files, diff hash, 다음 액션을 담습니다.
- `.codex/packs/`: 생성된 임시 팩. git에 올리지 않는 것이 기본입니다.

## 빠른 시작

이 repo에서 바로 실행:

```powershell
python plugins/context-pack/scripts/context_pack.py init
python plugins/context-pack/scripts/context_pack.py checkpoint --pack
python plugins/context-pack/scripts/context_pack.py pack --task "startup bug"
python plugins/context-pack/scripts/context_pack.py review-pack
python plugins/context-pack/scripts/context_pack.py review-pack --base main
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

## 핵심 기능

- repo-local context library 초기화
- branch, HEAD, dirty files, diff hash 체크포인트
- 작업/리뷰별 `CONTEXT_PACK.md` 생성
- changed files를 `manifest.json`의 area와 매칭
- 관련 contracts, failure modes, tests, stale warning 표시
- git hook 기반 자동 checkpoint 옵션
- Codex skill/plugin 배포 지원

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

이유는 간단합니다. 컨텍스트 도서관과 handoff는 다음 사람/에이전트에게 전달되어야 하지만, 생성된 임시 pack과 로컬 경로 정보는 repo에 남기지 않는 편이 안전합니다.

## 자동화

repo-local git hook을 설치할 수 있습니다.

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode safe
```

safe mode:

- `pre-commit`: `doctor` 실행
- `post-checkout`: branch 변경 후 checkpoint
- `post-merge`: pull/merge 후 checkpoint

공격적인 모드:

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode aggressive
```

aggressive mode는 commit 이후 checkpoint도 추가합니다.

제거:

```powershell
python plugins/context-pack/scripts/context_pack.py uninstall-git-hooks
```

## 설계 방향

Context Pack은 RAG나 vector DB를 먼저 도입하지 않습니다.

MVP 방향은:

- Markdown-first
- git-aware
- stale-aware
- review-aware
- deterministic engine first
- semantic summary second

즉, 반복 가능한 일은 Python script가 처리합니다.

- git 상태 수집
- dirty file 목록
- diff hash
- area matching
- pack 생성
- hook 설치
- doctor 검증

AI가 맡는 일은 의미 판단입니다.

- area 요약 개선
- 프로젝트 계약 정리
- common failure modes 작성
- 중요한 결정 기록

## 검증

```powershell
python -m unittest discover -s tests -v
python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack
python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack
```

GitHub Actions에서는 Windows/Ubuntu, Python 3.11/3.12 조합으로 stdlib unit test를 실행합니다.

## 한 줄 포지셔닝

Context Pack은 AI 코딩 에이전트를 위한 **version-aware context pack generator**입니다.

Memory Bank처럼 기억을 쌓는 것에서 멈추지 않고, 매 작업마다 “지금 책상 위에 올릴 최소 컨텍스트”를 만들어 줍니다.
