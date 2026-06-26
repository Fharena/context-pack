# Context Pack

Context Pack is a repo-local context library and context-pack generator for coding agents.

It helps Codex, Claude, Cursor, and humans avoid paying the agent to rediscover the same project structure every session or review. The deterministic engine records git state, maps changed files to project areas, detects stale context, and writes a small `.codex/packs/CONTEXT_PACK.md` that tells the agent what to read first.

## Why

Most AI coding waste starts before coding: the agent has to rediscover which files matter, which tests cover the change, what contracts must not break, and whether old notes are stale.

Context Pack turns that into a lightweight project library:

- `.codex/context/` is the project index.
- `.codex/handoff/` is the current work state.
- `.codex/packs/CONTEXT_PACK.md` is the generated desk for the current task.

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
