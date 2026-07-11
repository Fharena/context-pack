---
id: skill-plugin
status: active
paths:
  - plugins/context-pack/.codex-plugin/plugin.json
  - plugins/context-pack/skills/context-pack/SKILL.md
  - plugins/context-pack/skills/context-pack/agents/openai.yaml
tests:
  - tests/test_context_pack.py
verify:
  - python scripts/sync_packaged_assets.py --check
  - python -m unittest discover -s tests -v
last_reviewed_head: c18bd9bcc69b
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
- The CLI receives explicit operations rather than maintaining a phrase classifier.
- Configured repositories may route automatically before broad reading.
- Unconfigured repositories use normal targeted search unless the user explicitly requests a transient preview or evaluation.
- Persistent setup and Git hooks require explicit requests.
- The skill stays concise and skips obvious or already-localized work.

## Common Failure Modes
- Every trivial edit turns into Context Pack ceremony.
- Inferred transient routing finds a related file but distracts from the defect.
- Plugin copy promises lifecycle automation the skill cannot guarantee.
- Canonical and packaged skill resources drift.
