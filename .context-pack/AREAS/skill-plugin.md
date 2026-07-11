---
id: skill-plugin
status: active
paths:
  - plugins/context-pack/.codex-plugin/plugin.json
  - plugins/context-pack/skills/context-pack/SKILL.md
  - plugins/context-pack/skills/context-pack/agents/openai.yaml
tests:
  - python scripts/sync_packaged_assets.py --check
---

# Skill And Plugin

## Read When
- Changing when agents invoke Context Pack or how the Codex plugin describes itself.

## Start With
- `plugins/context-pack/skills/context-pack/SKILL.md`
- `plugins/context-pack/skills/context-pack/agents/openai.yaml`
- `plugins/context-pack/.codex-plugin/plugin.json`

## Contracts
- The agent interprets natural-language task, review, continuation, and handoff intent.
- The CLI receives explicit operations rather than maintaining a second phrase classifier.
- Normal orientation may be transient; persistent setup requires an explicit request.
- The skill remains concise background guidance and skips tiny obvious work.

## Common Failure Modes
- Every trivial edit turns into Context Pack ceremony.
- Plugin copy promises lifecycle automation that the skill cannot guarantee.
- Canonical and packaged skill resources drift.
