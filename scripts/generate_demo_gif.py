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
        ("$ python plugins/context-pack/scripts/context_pack.py init", BLUE),
        ("Initialized context-pack in ./repo", GREEN),
        ("- Context index: .codex/context/INDEX.md", TEXT),
        ("- Handoff: .codex/handoff/CURRENT.md", TEXT),
        ("- Manifest: .codex/context/manifest.json", TEXT),
    ],
    [
        ("$ python plugins/context-pack/scripts/context_pack.py review-pack --base main", BLUE),
        ("Context pack written to .codex/packs/CONTEXT_PACK.md", GREEN),
        ("Selected areas: engine, installer-release, tests", TEXT),
        ("", TEXT),
        ("No repo-wide scan needed yet.", MUTED),
    ],
    [
        ("# Context Pack", YELLOW),
        ("Mode: review", TEXT),
        ("Selected Areas:", TEXT),
        ("- engine", GREEN),
        ("- installer-release", GREEN),
        ("- tests", GREEN),
    ],
    [
        ("Read First:", TEXT),
        ("- .codex/context/AREAS/engine.md", BLUE),
        ("- plugins/context-pack/.../context_pack.py", BLUE),
        ("- tests/test_context_pack.py", BLUE),
        ("", TEXT),
        ("Contracts To Check:", TEXT),
        ("- Engine stays stdlib-only.", GREEN),
    ],
    [
        ("$ python plugins/context-pack/scripts/context_pack.py checkpoint --pack", BLUE),
        ("Checkpoint updated at .codex/handoff/CURRENT.md", GREEN),
        ("HEAD: cc20bba; dirty: 0 file(s); hash: clean", TEXT),
        ("", TEXT),
        ("Next agent starts from the right shelf.", YELLOW),
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
