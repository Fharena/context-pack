# Contributing

Thanks for helping improve Context Pack.

## Development Setup

Context Pack is intentionally stdlib-only. No package install is required for the core engine.

Run tests:

```bash
python -m unittest discover -s tests -v
```

Run the repo doctor:

```bash
python plugins/context-pack/scripts/context_pack.py doctor
```

## Project Layout

- `plugins/context-pack/skills/context-pack/scripts/context_pack.py`: deterministic engine
- `plugins/context-pack/skills/context-pack/SKILL.md`: Codex skill instructions
- `plugins/context-pack/.codex-plugin/plugin.json`: Codex plugin metadata
- `.codex/context/`: project context library
- `tests/`: unit tests

## Pull Requests

Keep changes focused. If you change command behavior, update:

- tests
- `README.md` and `README.ko.md` when user-facing commands change
- `.codex/context/manifest.json` or `AREAS/*.md` when routing changes
- `CHANGELOG.md` for release-visible changes

## Design Rules

- Prefer deterministic script logic for factual repo state.
- Use agent judgment only for semantic summaries, contracts, failure modes, and decisions.
- Keep generated files under `.codex/packs/` and out of git.
- Treat context docs as routing hints, not source of truth.
