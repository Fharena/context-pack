# Current Handoff

<!-- context-pack:fingerprint:start -->
- Repo root: D:\SJWORK\my_project_memory
- Git repo: yes
- Branch: main
- HEAD: 6ea29a3485d6
- Dirty files: none
- Dirty diff hash: clean
- Updated at: 2026-06-28T23:16:32+09:00
<!-- context-pack:fingerprint:end -->
## Active Goal
- Product hardening for Context Pack. Latest product work: `62d40a8 feat: route ci build failure prompts` lets `start --task` route "CI is red", "build failed", and similar CI/build failure phrases to automation/source/tests without treating "red build badge docs" as code failure work. Context areas reviewed at `6ea29a3`.

## Read First
1. `.context-pack/CURRENT.md`
2. `.context-pack/INDEX.md`
3. The relevant `.context-pack/AREAS/*.md` files

## Next Actions
1. Watch CI after pushing the latest handoff.
2. Next product iteration: dogfood on 3-5 external repos and collect before/after orientation examples.
3. Keep improving natural agent triggers only when they reduce manual tool use without making the skill feel heavy.

## Watch Outs
- Treat stale context as a hint, not a fact.
- Check the source-of-truth checkout before editing.
- `context-pack setup --dry-run` now preserves this repo's curated manifest by default; use `--infer-areas` only when intentionally expanding area docs.
- Text-budget metrics are approximate (`chars/4`) and should be described as context-size guidance, not exact billing tokens.

## Last Verified
- `python -m unittest discover -s tests -v` (77 passed)
- `python scripts/validate_packaged_cli.py`
- `python -m json.tool plugins/context-pack/.codex-plugin/plugin.json`
- `python -m json.tool .context-pack/manifest.json`
- `python -m json.tool .agents/plugins/marketplace.json`
- `python -m json.tool package.json`
- `git diff --check`
- packaged npm temp repo smoke: `context-pack start --task "why are tests failing"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "ci is red"` selects automation/source/tests
- packaged npm temp repo smoke: `context-pack start --task "login is broken"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "버그 고쳐줘"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "버그 잡아줘"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "문제 해결해줘"` selects source/tests
- packaged npm temp repo smoke: `context-pack start --task "review this branch"` on a clean feature branch infers `main` and selects source
- packaged npm temp repo smoke: `context-pack start --task "look over my changes"` routes to review mode and selects source
- packaged npm temp repo smoke: `context-pack start --task "변경사항 봐줘"` routes to review mode and selects source
- packaged npm temp repo smoke: `context-pack start --task "브랜치 리뷰해줘"` produces a review pack with only the changed source area
- packaged npm temp repo smoke: `context-pack start --task "나중에 이어가게 정리해줘"` points to checkpoint and packaged `checkpoint --pack` keeps tracked status unchanged
- packaged npm temp repo smoke: `context-pack start --task "I'm done for now"` points to checkpoint
- packaged npm temp repo smoke: `context-pack start --task "작업 끝났어"` points to checkpoint
- `node bin/context-pack.js --help`
- `npm pack --dry-run`
- `python -m build`
- `python -m twine check dist/*`
