# Context Pack

[한국어 README](README.ko.md)

Context Pack is a repo-local context library and context-pack generator for coding agents.

It helps Codex, Claude, Cursor, and humans avoid paying the agent to rediscover the same project structure every session or review. The deterministic engine records git state, maps changed files to project areas, detects stale context, and writes a small `.codex/packs/CONTEXT_PACK.md` that tells the agent what to read first.

## Why

Most AI coding waste starts before coding: the agent has to rediscover which files matter, which tests cover the change, what contracts must not break, and whether old notes are stale.

Context Pack turns that into a lightweight project library:

- `.codex/context/` is the project index.
- `.codex/handoff/` is the current work state.
- `.codex/packs/CONTEXT_PACK.md` is the generated desk for the current task.

## Korean Summary

Context Pack은 Codex, Claude, Cursor 같은 코딩 에이전트가 매번 repo 전체를 다시 읽지 않도록, 프로젝트 안에 작은 컨텍스트 도서관을 만드는 도구입니다.

- `.codex/context/`: 프로젝트 영역별 인덱스와 리뷰 라우터
- `.codex/handoff/`: 현재 작업 상태와 다음 세션용 체크포인트
- `.codex/packs/CONTEXT_PACK.md`: 이번 작업에 필요한 파일, 계약, 테스트, 주의점만 모은 임시 컨텍스트 팩

핵심은 "AI memory"가 아니라, **지금 작업에 필요한 문서와 파일만 먼저 읽게 하는 version-aware context router**입니다. 자세한 한국어 설명은 [README.ko.md](README.ko.md)를 보세요.

## What It Does

- Initializes a repo-local context library.
- Checkpoints branch, HEAD, dirty files, and diff hash.
- Generates task or review context packs.
- Maps changed files to context areas from `manifest.json`.
- Surfaces contracts, failure modes, tests, and stale warnings.
- Keeps generated/local files out of git by default.

## Install As A Codex Skill

From this repository:

```powershell
python scripts/install_skill.py
```

This copies `plugins/context-pack/skills/context-pack` to your Codex skills directory.

## Use From The Plugin Source

```powershell
python plugins/context-pack/scripts/context_pack.py init
python plugins/context-pack/scripts/context_pack.py checkpoint --pack
python plugins/context-pack/scripts/context_pack.py pack --task "startup bug"
python plugins/context-pack/scripts/context_pack.py review-pack
python plugins/context-pack/scripts/context_pack.py review-pack --base main
python plugins/context-pack/scripts/context_pack.py doctor
```

Optional git automation:

```powershell
python plugins/context-pack/scripts/context_pack.py install-git-hooks --mode safe
```

Safe mode installs repo-local hooks for pre-commit validation and post-checkout/post-merge checkpoints. Aggressive mode also checkpoints after commits.

## Install As A Local Codex Plugin

For Codex plugin development/testing:

```powershell
python scripts/install_plugin.py
```

This copies `plugins/context-pack` into `~/plugins/context-pack` and updates the personal marketplace at `~/.agents/plugins/marketplace.json`.

For repo-scoped marketplace installs, this repository also includes:

```text
.agents/plugins/marketplace.json
```

After cloning, add this repository as a Codex plugin marketplace if you want Codex to discover the bundled plugin from the repo.

## Agent UX

Tell the agent:

```text
Initialize context-pack in this repo.
Build a review context pack for my changes.
Checkpoint this work for the next session.
```

After initialization, agents should read:

1. `.codex/handoff/CURRENT.md`
2. `.codex/context/INDEX.md`
3. `.codex/packs/CONTEXT_PACK.md` when generated
4. Relevant `.codex/context/AREAS/*.md`

## Git Policy

Track:

- `.codex/context/manifest.json`
- `.codex/context/INDEX.md`
- `.codex/context/REVIEW.md`
- `.codex/context/CONTRACTS.md`
- `.codex/context/AREAS/*.md`
- `.codex/handoff/CURRENT.md`
- `.codex/handoff/LOG.md`
- `.codex/handoff/DECISIONS.md`

Ignore:

- `.codex/packs/`
- `.codex/context/tmp/`
- `.codex/handoff/LOCAL.md`

## Design

Context Pack is markdown-first and RAG-later. The core product is not vector search; it is a version-aware routing index that produces the smallest useful reading set for the current task.

The script handles deterministic work. The agent handles semantic work:

- Write area summaries.
- Identify project contracts.
- Record durable decisions.
- Improve failure-mode checklists.

## Release Check

```powershell
python -m unittest discover -s tests -v
python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack
python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack
```

## Development

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Validate the plugin:

```powershell
python C:/Users/99yoo/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/context-pack
python C:/Users/99yoo/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/context-pack/skills/context-pack
```

GitHub Actions runs the stdlib unit tests on Windows and Ubuntu for Python 3.11 and 3.12.
