"""Before/after contact sheet for the in-game Sailor validation fixes.

Reads the two validation packs — the one built before the authored-geometry
fixes and the one built after — and lays the same seed's four Fashion Sense
frames side by side, so the same garment can be compared against the in-game
observation that prompted the change.

Read-only with respect to generation: it renders nothing, it only reads the
two packs' shirt.png sheets.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from v5.grammar import ATLAS_ORDER                                   # noqa: E402
from v5.pngio import (blank_image, blit, draw_rect, draw_text,       # noqa: E402
                      nearest_scale, read_rgba_png, write_rgba_png)

OUT = Path("output/v5_sailor_ingame_fix_01")
SHEET = "Shirts/{folder}/shirt.png"

# The in-game observations this pass was answering, by seed.
FINDINGS = {
    3:  "rear flap/back straps too far outward",
    4:  "white split line at sleeve/arm, worst from back",
    13: "rear flap reads as a flat horizontal band",
    14: "front collar collapses to a flat band; weak V",
    25: "strong candidate; rear flap too blocky/straight",
    40: "collar too wide/flat; back flap a straight bar",
    45: "back flap lines up as bars through the arms",
    83: "front insert is a box under the chin",
}

S = 9          # zoom
PAD = 6


def frames(sheet, height: int = 8):
    return [[row[:] for row in sheet[i * height:(i + 1) * height]]
            for i in range(len(ATLAS_ORDER))]


def strip(sheet, tint):
    """One garment's four frames in a row, zoomed."""
    fr = frames(sheet)
    w = len(fr[0][0]) * S
    out = blank_image(len(fr) * (w + 4) - 4, len(fr[0]) * S, tint)
    for i, f in enumerate(fr):
        blit(out, nearest_scale(f, S), i * (w + 4), 0)
    return out


def _wrap(text: str, width: int) -> list:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def build(before: Path, after: Path) -> Path:
    folders = sorted(p.name for p in (after / "Shirts").iterdir() if p.is_dir())
    rows = []
    for folder in folders:
        # "V5Sailor003Middy" -> 3.  Taking every digit picks up the "5" of "V5".
        seed = int(folder[len("V5Sailor"):][:3])
        b = read_rgba_png(before / SHEET.format(folder=folder))
        a = read_rgba_png(after / SHEET.format(folder=folder))
        rows.append((seed, folder, strip(b, (222, 214, 214, 255)),
                     strip(a, (214, 222, 214, 255))))

    sw, sh = len(rows[0][2][0]), len(rows[0][2])
    header, gutter, lane = 46, 26, 210
    width = lane + 2 * sw + 3 * gutter
    height = header + len(rows) * (sh + 20) + PAD
    out = blank_image(width, height, (243, 241, 237, 255))
    draw_text(out, "V5 SAILOR — IN-GAME VALIDATION FIXES", PAD, 6, scale=2)
    draw_text(out, "same seeds, same pack, same coverage axes."
                   "   frames: front / right / left / back", PAD, 24)
    draw_text(out, "BEFORE", lane + gutter, 34)
    draw_text(out, "AFTER", lane + 2 * gutter + sw, 34)
    for i, (seed, folder, b, a) in enumerate(rows):
        y = header + i * (sh + 20)
        draw_text(out, folder, PAD, y + 2)
        note = FINDINGS.get(seed)
        for j, line in enumerate(_wrap(note or "(not flagged in game)", 34)):
            draw_text(out, line, PAD, y + 12 + j * 10)
        blit(out, b, lane + gutter, y)
        blit(out, a, lane + 2 * gutter + sw, y)
        if note:
            draw_rect(out, PAD - 3, y - 2, 2, sh + 4, (176, 88, 72, 255))
        # a hard divider so the two lanes cannot be read as one eight-frame strip
        draw_rect(out, lane + 2 * gutter + sw - gutter // 2, y - 2, 1, sh + 4,
                  (150, 146, 140, 255))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "before_after.png"
    write_rgba_png(path, out)
    return path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: make_sailor_ingame_fix_comparison.py <before-pack> <after-pack>")
    print(build(Path(sys.argv[1]), Path(sys.argv[2])))
