#!/usr/bin/env python3
"""Install the Context Pack skill into the local Codex skills directory."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins" / "context-pack" / "skills" / "context-pack"


def default_target() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "skills" / "context-pack"
    return Path.home() / ".codex" / "skills" / "context-pack"


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the context-pack Codex skill.")
    parser.add_argument("--target", type=Path, default=default_target(), help="Skill target directory")
    parser.add_argument("--force", action="store_true", help="Replace an existing installed skill")
    args = parser.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"Source skill not found: {SOURCE}")
    if args.target.exists():
        if not args.force:
            raise SystemExit(f"Target already exists: {args.target}. Use --force to replace it.")
        shutil.rmtree(args.target)
    args.target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, args.target)
    print(f"Installed context-pack skill to {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
