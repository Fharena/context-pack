# Current Handoff

<!-- context-pack:fingerprint:start -->
- Repo root: D:\SJWORK\my_project_memory
- Git repo: yes
- Branch: main
- HEAD: 4f9fdbe5f8eb
- Dirty files: .context-pack/AREAS/engine.md, .context-pack/AREAS/installer-release.md, .context-pack/AREAS/tests.md
- Dirty diff hash: sha256:06bd8dd07bb2ea620bfa6709
- Updated at: 2026-06-28T22:00:47+09:00
<!-- context-pack:fingerprint:end -->
## Active Goal
- Product hardening for Context Pack. Latest work: `4f9fdbe feat: route failing test prompts to source` makes natural prompts like "why are tests failing" start from `source, tests` instead of tests alone, with packaged npm smoke coverage.

## Read First
1. `.context-pack/CURRENT.md`
2. `.context-pack/INDEX.md`
3. The relevant `.context-pack/AREAS/*.md` files

## Next Actions
1. Watch CI after pushing the latest handoff.
2. Next product iteration: test Context Pack on 3-5 external repos and collect before/after orientation examples.
3. Improve registry publishing readiness only after the lightweight skill UX stays stable.

## Watch Outs
- Treat stale context as a hint, not a fact.
- Check the source-of-truth checkout before editing.
- `context-pack setup --dry-run` now preserves this repo's curated manifest by default; use `--infer-areas` only when intentionally expanding area docs.
- Text-budget metrics are approximate (`chars/4`) and should be described as context-size guidance, not exact billing tokens.

## Last Verified
- `python -m unittest discover -s tests -v` (68 passed)
- `python scripts/validate_packaged_cli.py`
- `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
- `python -m json.tool .context-pack/manifest.json`
- `python -m json.tool .agents/plugins/marketplace.json`
- `python -m json.tool package.json`
- `git diff --check`
- packaged npm temp repo smoke: `context-pack start --task "why are tests failing"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "버그 고쳐줘"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "브랜치 리뷰해줘"` produces a review pack with only the changed source area
- `node bin/context-pack.js --help`
- `npm pack --dry-run`
- `python -m build`
- `python -m twine check dist/*`
