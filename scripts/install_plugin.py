#!/usr/bin/env python3
"""Install the Context Pack plugin into the personal Codex marketplace."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins" / "context-pack"


def default_target() -> Path:
    return Path.home() / "plugins" / "context-pack"


def default_marketplace() -> Path:
    return Path.home() / ".agents" / "plugins" / "marketplace.json"


def load_marketplace(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": "personal",
            "interface": {"displayName": "Personal"},
            "plugins": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def update_marketplace(path: Path, plugin_name: str) -> None:
    data = load_marketplace(path)
    data.setdefault("name", "personal")
    data.setdefault("interface", {"displayName": "Personal"})
    data.setdefault("plugins", [])
    entry = {
        "name": plugin_name,
        "source": {
            "source": "local",
            "path": f"./plugins/{plugin_name}",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Productivity",
    }
    for idx, existing in enumerate(data["plugins"]):
        if existing.get("name") == plugin_name:
            data["plugins"][idx] = entry
            break
    else:
        data["plugins"].append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Context Pack as a local Codex plugin.")
    parser.add_argument("--target", type=Path, default=default_target(), help="Plugin target directory")
    parser.add_argument("--marketplace", type=Path, default=default_marketplace(), help="Personal marketplace.json path")
    parser.add_argument("--force", action="store_true", help="Replace an existing plugin target")
    args = parser.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"Plugin source not found: {SOURCE}")
    if args.target.exists():
        if not args.force:
            raise SystemExit(f"Target already exists: {args.target}. Use --force to replace it.")
        shutil.rmtree(args.target)
    args.target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, args.target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    update_marketplace(args.marketplace, "context-pack")
    print(f"Installed plugin to {args.target}")
    print(f"Updated marketplace {args.marketplace}")
    print("Install in Codex with: codex plugin add context-pack@personal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
