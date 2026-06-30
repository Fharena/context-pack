---
id: skill-plugin
last_reviewed_head: 53d3b3cf60d4
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
- Teaching Claude, Cursor, or mixed-agent repos how to pick up Context Pack automatically.
- Updating Codex plugin metadata or skill triggers.
- Aligning README, SKILL.md, and engine command behavior.
- Making first-time repo onboarding feel like one agent action instead of several manual CLI steps.

## Start With
- `plugins/context-pack/skills/context-pack/SKILL.md`
- `plugins/context-pack/.codex-plugin/plugin.json`
- `plugins/context-pack/skills/context-pack/agents/openai.yaml`

## Contracts
- The skill must route factual work to the deterministic engine first.
- The skill should tell agents to use `context-pack start` proactively before broad reading, review, unfamiliar debugging, and handoff.
- For normal bug/debug/review/handoff work, `start` is the first move even when `.context-pack/` is missing; reserve `setup` for explicit install or configuration requests.
- The skill should use `context-pack setup` when the user asks to configure project memory and `context-pack doctor --fix` when setup is present but broken or incomplete.
- The manifest must remain validation-ready.
- Do not promise automatic lifecycle hooks unless the plugin manifest or installer actually provides them.
- Trigger language must cover install/update requests, start routing, initialization, context packs, review packs, checkpoints, status, stale checks, mark-reviewed, and token-saving orientation.
- Shared agent-doc guidance should make Context Pack feel proactive, not like a manual CLI chore.
- Skill and generated agent-doc examples should stay aligned with the router's natural-language surface, including softer review wording such as "look over my changes" and short handoff wording such as "I'm done for now".
- Skill trigger language should mention CI/build failure debugging when the deterministic router supports "CI is red" / "build failed".

## Common Failure Modes
- Skill docs drift from engine commands.
- Manifest includes unsupported fields.
- Product copy narrows the value to session handoff only.
- Default prompt makes Context Pack feel manual-only instead of agent-first.
- Skill guidance teaches lower-level commands before the one-command start path.
- Skill guidance teaches `init` plus `install-agent-docs` before the one-command `setup` path.
- Skill guidance treats doctor as read-only even when repair is available.
- Install/update requests are routed to old local scripts instead of `install-codex`.
- Claude/Cursor guidance drifts from the generated `AGENTS.md` rule block.
- Skill examples promise natural review handling that the deterministic `start --task` intent guard does not recognize.
- Skill examples promise short handoff handling that the deterministic `start --task` intent guard does not recognize.
- Skill metadata omits CI/build failure debugging after README and engine advertise it.

## Expand Scope If
- New commands are added.
- Codex plugin manifest schema changes.
- Hook installation moves from opt-in script to plugin-native lifecycle hooks.

## Do Not Start With
- generated context packs
