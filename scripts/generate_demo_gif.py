#!/usr/bin/env python3
"""Generate the README terminal demo GIF.

This is an optional maintainer script. The project itself does not depend on
Pillow, but this script uses it to produce `assets/demo.gif`.
"""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - optional maintainer tooling
    raise SystemExit("Pillow is required for this script: python -m pip install pillow") from exc


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "demo.gif"

WIDTH = 980
HEIGHT = 560
BG = "#0f172a"
TERM = "#111827"
TERM_BORDER = "#334155"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
GREEN = "#22c55e"
BLUE = "#60a5fa"
YELLOW = "#facc15"
RED = "#fb7185"


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consolab.ttf" if bold else "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


TITLE_FONT = font(28, bold=True)
BODY_FONT = font(19)
SMALL_FONT = font(16)


def base_frame() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)

    d.rounded_rectangle((38, 32, WIDTH - 38, HEIGHT - 32), radius=16, fill=TERM, outline=TERM_BORDER, width=2)
    d.ellipse((64, 58, 78, 72), fill=RED)
    d.ellipse((88, 58, 102, 72), fill=YELLOW)
    d.ellipse((112, 58, 126, 72), fill=GREEN)
    d.text((148, 53), "context-pack demo", fill=MUTED, font=SMALL_FONT)
    d.text((64, 98), "Stop paying agents to rediscover your repo.", fill=TEXT, font=TITLE_FONT)
    return img


def draw_lines(img: Image.Image, lines: list[tuple[str, str]], *, start_y: int = 150) -> Image.Image:
    d = ImageDraw.Draw(img)
    y = start_y
    for line, color in lines:
        d.text((72, y), line, fill=color, font=BODY_FONT)
        y += 31
    return img


SCENES: list[list[tuple[str, str]]] = [
    [
        ("$ context-pack setup --dry-run", BLUE),
        ("Context Pack setup dry run for ./repo", MUTED),
        ("Setup plan:", TEXT),
        ("- create .context-pack/manifest.json", GREEN),
        ("- create AGENTS.md / CLAUDE.md / Cursor rules", GREEN),
        ("No files were written.", YELLOW),
    ],
    [
        ("$ context-pack setup", BLUE),
        ("Context Pack setup complete for ./repo", GREEN),
        ("Ready:", TEXT),
        ("- Context library: .context-pack", TEXT),
        ("- Handoff docs: .context-pack", TEXT),
        ("- Agent docs: AGENTS.md, CLAUDE.md, Cursor", TEXT),
    ],
    [
        ("$ context-pack start --task \"improve CLI onboarding\"", BLUE),
        ("Generated work pack: .context-pack/packs/CONTEXT_PACK.md", GREEN),
        ("Selected areas: installer-release, skill-plugin, engine", TEXT),
        ("Scope reduction: 3 areas instead of 82 repo files", YELLOW),
        ("Approx text budget: Read First ~8.2k tokens", YELLOW),
        ("Repo text: ~58.7k tokens from 77 text files", MUTED),
    ],
    [
        ("# Context Pack", YELLOW),
        ("Mode: work", TEXT),
        ("## Scope Reduction", TEXT),
        ("- Repo files considered: 82", TEXT),
        ("- Read First entries: 5 (~6% of repo files)", TEXT),
        ("- Approx Read First text: ~8.2k tokens", GREEN),
        ("- Token estimates use chars/4, not billing tokens", MUTED),
    ],
    [
        ("Read First:", TEXT),
        ("- .context-pack/AREAS/installer-release.md", BLUE),
        ("- .context-pack/AREAS/skill-plugin.md", BLUE),
        ("- .context-pack/AREAS/engine.md", BLUE),
        ("- README.md", BLUE),
        ("- src/context_pack/bundled/context_pack.py", BLUE),
    ],
    [
        ("$ context-pack checkpoint --pack", BLUE),
        ("Local checkpoint updated at .context-pack/local/LOCAL.md", GREEN),
        ("Context pack: .context-pack/packs/CONTEXT_PACK.md", TEXT),
        ("Tracked handoff stays clean unless --publish is used.", TEXT),
        ("Next agent prompt:", MUTED),
        ("\"Use $context-pack to continue from the current handoff.\"", TEXT),
    ],
]


def make_frames() -> list[Image.Image]:
    frames: list[Image.Image] = []
    for scene in SCENES:
        img = draw_lines(base_frame(), scene)
        frames.extend([img] * 9)
    return frames


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames = make_frames()
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=110,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
