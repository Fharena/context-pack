---
id: overview
last_reviewed_head: db336dcb7a22
status: active
paths:
  - README.md
  - AGENTS.md
  - .context-pack/**
tests: []
stale_if:
  - AGENTS.md changes
  - README.md changes
  - context manifest changes
---

# Overview

## Read When
- Starting a new session or code review.
- Unsure which area owns the task.
- Bootstrapping this repository's context library.

## Start With
- README.md
- AGENTS.md
- .context-pack/INDEX.md
- .context-pack/CURRENT.md

## Contracts
- Context docs are routing hints, not ground truth.
- If HEAD, dirty files, or diff hash differ from the pack, verify source code before acting.
- Generated packs are temporary and should not be committed.
- Public benchmark claims should distinguish deterministic orientation/token-budget comparisons from true independent-agent task success.
- Public benchmark docs should stay tied to reproducible `docs/benchmarks/latest.json` results and name weak spots found during dogfood.

## Common Failure Modes
- Trusting stale summaries after the code moved on.
- Reading append-only logs before the current source of truth.
- Editing a copied checkout or generated file instead of the canonical workspace.
- Presenting a routing/token reduction benchmark as if it proved final patch quality or wall-clock agent performance.
- Updating README benchmark claims without refreshing the generated benchmark artifacts and limitations.

## Expand Scope If
- Public API, CLI, schema, storage format, subprocess launch, or test helpers changed.
- The changed file does not match any known area.

## Do Not Start With
- .context-pack/packs/
- archived logs
- generated artifacts
