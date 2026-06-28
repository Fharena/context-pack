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
    d.text((64, 98), "Agents get a map before repo-wide reading.", fill=TEXT, font=TITLE_FONT)
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
        ("User: Fix the login timeout.", BLUE),
        ("Agent: orient before broad repo reading.", TEXT),
        ("Runs quietly: context-pack start --task \"fix login timeout\"", MUTED),
        ("Selected areas: source, tests", GREEN),
        ("Why selected: starter code areas for this task", TEXT),
        ("Read first: pack, area docs, then real source", YELLOW),
    ],
    [
        ("First run is previewable.", BLUE),
        ("$ context-pack setup --dry-run", MUTED),
        ("No files written.", YELLOW),
        ("Plan:", TEXT),
        ("- create .context-pack/manifest.json", GREEN),
        ("- create source/tests area docs", GREEN),
        ("- install AGENTS.md / CLAUDE.md / Cursor rules", GREEN),
    ],
    [
        ("$ context-pack setup", BLUE),
        ("Context Pack setup complete for ./repo", GREEN),
        ("Ready:", TEXT),
        ("- Context library: .context-pack", TEXT),
        ("- Agent docs teach quiet orientation", TEXT),
        ("- Tiny obvious edits can skip Context Pack", YELLOW),
    ],
    [
        ("Generated work pack:", TEXT),
        (".context-pack/packs/CONTEXT_PACK.md", BLUE),
        ("Selected areas: source, tests", GREEN),
        ("Scope reduction: start from 2 areas, not the whole repo", YELLOW),
        ("Approx text budget shown with chars/4 caveat", MUTED),
        ("Agent now opens the listed files first.", TEXT),
    ],
    [
        ("# Context Pack", YELLOW),
        ("Mode: work", TEXT),
        ("## Read First", TEXT),
        ("- .context-pack/AREAS/source.md", BLUE),
        ("- .context-pack/AREAS/tests.md", BLUE),
        ("- src/", BLUE),
        ("- tests/", BLUE),
        ("- then verify against real code", MUTED),
    ],
    [
        ("Review branch against main.", BLUE),
        ("Agent runs: context-pack start --review --base main", MUTED),
        ("Pack includes:", TEXT),
        ("- changed files", GREEN),
        ("- relevant contracts and tests", GREEN),
        ("- stale warnings to verify in source", YELLOW),
    ],
    [
        ("User: leave this easy to resume later.", BLUE),
        ("Agent runs: context-pack checkpoint --pack", MUTED),
        ("Local checkpoint updated at .context-pack/local/LOCAL.md", GREEN),
        ("Context pack: .context-pack/packs/CONTEXT_PACK.md", TEXT),
        ("Tracked handoff stays clean unless --publish is used.", YELLOW),
        ("Next session starts from the same map.", TEXT),
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
