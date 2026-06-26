---
id: skill-plugin
last_reviewed_head: 4cd7e6c6caf4
status: active
paths:
  - plugins/context-pack/.codex-plugin/plugin.json
  - plugins/context-pack/skills/context-pack/SKILL.md
  - plugins/context-pack/skills/context-pack/agents/openai.yaml
tests:
  - plugin validation
  - skill validation
stale_if:
  - engine command set changes
  - plugin metadata changes
---

# Skill Plugin

## Read When
- Changing how agents are instructed to use Context Pack.
- Updating Codex plugin metadata or skill triggers.
- Aligning README, SKILL.md, and engine command behavior.

## Start With
- `plugins/context-pack/skills/context-pack/SKILL.md`
- `plugins/context-pack/.codex-plugin/plugin.json`
- `plugins/context-pack/skills/context-pack/agents/openai.yaml`

## Contracts
- The skill must route factual work to the deterministic engine first.
- The skill should tell agents to use `context-pack start` proactively before broad reading, review, unfamiliar debugging, and handoff.
- The manifest must remain validation-ready.
- Do not promise automatic lifecycle hooks unless the plugin manifest or installer actually provides them.
- Trigger language must cover start routing, initialization, context packs, review packs, checkpoints, status, stale checks, mark-reviewed, and token-saving orientation.

## Common Failure Modes
- Skill docs drift from engine commands.
- Manifest includes unsupported fields.
- Product copy narrows the value to session handoff only.
- Default prompt makes Context Pack feel manual-only instead of agent-first.
- Skill guidance teaches lower-level commands before the one-command start path.

## Expand Scope If
- New commands are added.
- Codex plugin manifest schema changes.
- Hook installation moves from opt-in script to plugin-native lifecycle hooks.

## Do Not Start With
- generated context packs
