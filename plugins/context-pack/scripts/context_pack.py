#!/usr/bin/env python3
"""Wrapper for the bundled context-pack engine."""

from __future__ import annotations

import runpy
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[1] / "skills" / "context-pack" / "scripts" / "context_pack.py"


if __name__ == "__main__":
    runpy.run_path(str(ENGINE), run_name="__main__")
