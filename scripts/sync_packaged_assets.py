#!/usr/bin/env python3
"""Sync canonical plugin assets into the installable Python package."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAIRS = (
    (
        ROOT / "plugins/context-pack/skills/context-pack/scripts/context_pack.py",
        ROOT / "src/context_pack/bundled/context_pack.py",
    ),
    (
        ROOT / "plugins/context-pack/skills/context-pack/SKILL.md",
        ROOT / "src/context_pack/bundled/SKILL.md",
    ),
    (
        ROOT / "plugins/context-pack/skills/context-pack/agents/openai.yaml",
        ROOT / "src/context_pack/bundled/openai.yaml",
    ),
    (
        ROOT / "plugins/context-pack/.codex-plugin/plugin.json",
        ROOT / "src/context_pack/bundled/plugin.json",
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail when packaged copies are stale")
    args = parser.parse_args()

    stale: list[str] = []
    for source, target in PAIRS:
        if target.exists() and source.read_bytes() == target.read_bytes():
            continue
        if args.check:
            stale.append(str(target.relative_to(ROOT)))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    if stale:
        print("Stale packaged assets: " + ", ".join(stale))
        print("Run: python scripts/sync_packaged_assets.py")
        return 1
    if not args.check:
        print(f"Synced {len(PAIRS)} packaged assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
