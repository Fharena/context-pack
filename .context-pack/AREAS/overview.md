---
id: overview
status: active
paths:
  - .context-pack/**
  - AGENTS.md
  - CLAUDE.md
  - .cursor/rules/**
tests: []
last_reviewed_head: 8e8138f9a1b8
---

# Overview

## Read When
- Starting or resuming work without a specific task.
- Verifying the source-of-truth checkout, current handoff, or area ownership.

## Start With
- `.context-pack/CURRENT.md`
- `.context-pack/INDEX.md`
- `README.md`

## Contracts
- Context docs are routing hints, not ground truth.
- A handoff names the repository path, branch, HEAD, dirty fingerprint, and next action.
- Generated packs remain ignored and shared logs stay bounded.
- Benchmark evidence is reproducible and never substitutes for source or patch verification.

## Common Failure Modes
- A session edits a copied or stale checkout.
- Overview context dominates a task with a clear source or test route.
- Old checkpoint detail is read before current source and `CURRENT.md`.
- Orientation ratios are described as exact provider tokens or task-quality gains.

## Do Not Start With
- `.context-pack/packs/`
- old Git history unless the current handoff points there
