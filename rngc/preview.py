"""Farmer composites and contact sheets.

The Farmer compositor is moved here from the legacy tool
``tools/generate_controlled_grammar_hd_adapter_repair.py`` (offsets confirmed
against the installed FarmerRenderer: shirt at (16, 56 + featureY*4) over the
Farmer drawn at 4x). A 16x16 frame is blitted at 2x, an 8x8 frame at 4x, so
both occupy the same 32x32 display box.
"""

from __future__ import annotations

import os
from pathlib import Path

from .pngio import RGBA, blank_image, blit, draw_rect, draw_text, flip_h, nearest_scale, read_rgba_png

DEFAULT_CONTENT = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)")
CONTENT = Path(os.environ.get("STARDEW_CONTENT", DEFAULT_CONTENT))
BODY_FRAME = {"front": 0, "right": 6, "back": 12, "left": 6}
FEATURE_Y = {0: 1, 6: 1, 12: 0}
HAIR_TINT: RGBA = (112, 76, 52, 255)
BG: RGBA = (232, 226, 217, 255); PANEL: RGBA = (205, 197, 186, 255)
INK: RGBA = (39, 37, 36, 255); ACC: RGBA = (46, 116, 125, 255); WARN: RGBA = (160, 70, 50, 255)
DIRECTIONS = ("front", "right", "back", "left")


class Farmer:
    def __init__(self, content: Path = CONTENT):
        self.available = (content / "Characters/Farmer/farmer_base.png").exists()
        if self.available:
            self.body = read_rgba_png(content / "Characters/Farmer/farmer_base.png")
            self.hair = read_rgba_png(content / "Characters/Farmer/hairstyles.png")

    def _crop(self, px, x, y, w, h): return [list(r[x:x + w]) for r in px[y:y + h]]

    def body_frame(self, d):
        i = BODY_FRAME[d]; f = self._crop(self.body, i % 6 * 16, i // 6 * 32, 16, 32)
        return flip_h(f) if d == "left" else f

    def hair_frame(self, d):
        y = 32 if d in ("right", "left") else 64 if d == "back" else 0
        f = self._crop(self.hair, 0, y, 16, 32)
        f = flip_h(f) if d == "left" else f
        return [[(p[0] * HAIR_TINT[0] // 255, p[1] * HAIR_TINT[1] // 255, p[2] * HAIR_TINT[2] // 255, p[3]) for p in r] for r in f]

    def composite(self, shirt, d, *, shirt_scale: int) -> list[list[RGBA]]:
        """Farmer at 4x with the shirt at `shirt_scale` (2 for 16x16, 4 for 8x8)."""
        canvas = blank_image(64, 128, PANEL)
        fy = FEATURE_Y[BODY_FRAME[d]]
        if self.available:
            blit(canvas, nearest_scale(self.body_frame(d), 4), 0, 0)
        blit(canvas, nearest_scale(shirt, shirt_scale), 16, 56 + fy * 4)
        if self.available:
            blit(canvas, nearest_scale(self.hair_frame(d), 4), 0, fy * 4 + (4 if d == "back" else 0))
        return canvas


def tile(canvas, img, x, y, border=ACC):
    draw_rect(canvas, x - 2, y - 2, len(img[0]) + 4, len(img) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(img[0]) + 2, len(img) + 2, PANEL)
    blit(canvas, img, x, y)


def row_of_frames(canvas, frames: dict, x0, y, scale, label, *, border=ACC, gap=12):
    """Draw four direction frames (dict keyed by DIRECTIONS) in a row; return width used."""
    draw_text(canvas, label, x0, y - 10, color=INK)
    x = x0
    for d in DIRECTIONS:
        img = nearest_scale(frames[d], scale) if scale != 1 else frames[d]
        draw_text(canvas, d.upper(), x, y + len(img) + 4, color=border)
        tile(canvas, img, x, y, border); x += len(img[0]) + gap
    return x - x0


def garment_sheet(title, v5_frames, farmer: Farmer, *, vanilla=None, vanilla_name="", reduced=None) -> list[list[RGBA]]:
    """Per-garment sheet: isolated 16x16 @8x, Farmer composites, vanilla counterpart, 8x8 diagnostic."""
    rows = 2 + (2 if vanilla else 0) + (1 if reduced else 0)
    canvas = blank_image(4 * 140 + 40, 40 + rows * 168, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    y = 40
    row_of_frames(canvas, v5_frames, 12, y, 8, "V5 16X16 LOGICAL AT 8X"); y += 168
    row_of_frames(canvas, {d: farmer.composite(v5_frames[d], d, shirt_scale=2) for d in DIRECTIONS}, 12, y, 1, "V5 ON FARMER (SCALE 2)"); y += 168
    if vanilla:
        row_of_frames(canvas, {d: farmer.composite(vanilla[d], d, shirt_scale=4) for d in DIRECTIONS}, 12, y, 1, f"VANILLA {vanilla_name} ON FARMER (SCALE 4)", border=WARN); y += 168
        row_of_frames(canvas, vanilla, 12, y, 16, f"VANILLA {vanilla_name} 8X8 AT 16X", border=WARN); y += 168
    if reduced:
        row_of_frames(canvas, reduced, 12, y, 16, "DIAGNOSTIC ONLY: 2X2 MAJORITY REDUCTION OF V5 AT 16X (NOT A GATE)", border=(120, 110, 100, 255)); y += 168
    return canvas


def collection_sheet(title, items, farmer: Farmer, *, vanilla_col=True) -> list[list[RGBA]]:
    """items: list of dicts {label, frames, vanilla(optional), vanilla_name}. One row per garment."""
    w = 150 + 4 * 76 + (4 * 76 + 30 if vanilla_col else 0)
    canvas = blank_image(w, 44 + len(items) * 156, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    draw_text(canvas, "V5 (SCALE 2)", 150, 24, color=ACC)
    if vanilla_col: draw_text(canvas, "VANILLA COUNTERPART (SCALE 4)", 150 + 4 * 76 + 30, 24, color=WARN)
    for r, it in enumerate(items):
        y = 44 + r * 156
        draw_text(canvas, it["label"][:22], 8, y + 4, color=INK)
        if it.get("sub"): draw_text(canvas, it["sub"][:22], 8, y + 16, color=ACC)
        for c, d in enumerate(DIRECTIONS):
            tile(canvas, farmer.composite(it["frames"][d], d, shirt_scale=2), 150 + c * 76, y + 12, ACC)
            if vanilla_col and it.get("vanilla"):
                tile(canvas, farmer.composite(it["vanilla"][d], d, shirt_scale=4), 150 + 4 * 76 + 30 + c * 76, y + 12, WARN)
    return canvas


def resolution_sheet(title, entries, farmer: Farmer) -> list[list[RGBA]]:
    """entries: list of {label, a16, b8, vanilla}. Columns A/B/C on the Farmer at equal display size."""
    canvas = blank_image(3 * (4 * 76 + 20) + 160, 60 + len(entries) * 156, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    heads = ("A: V5 16X16 LOGICAL / SCALE 2", "B: 8X8 LOGICAL / SCALE 4 (2X2 MAJORITY REDUCTION OF A)", "C: VANILLA 8X8 / SCALE 4")
    for c, h in enumerate(heads): draw_text(canvas, h, 160 + c * (4 * 76 + 20), 30, color=(INK, INK, WARN)[c])
    for r, e in enumerate(entries):
        y = 60 + r * 156; draw_text(canvas, e["label"][:24], 8, y + 4, color=INK)
        for c, (key, scale) in enumerate((("a16", 2), ("b8", 4), ("vanilla", 4))):
            if not e.get(key): continue
            for k, d in enumerate(DIRECTIONS):
                tile(canvas, farmer.composite(e[key][d], d, shirt_scale=scale), 160 + c * (4 * 76 + 20) + k * 76, y + 12, WARN if key == "vanilla" else ACC)
    draw_text(canvas, "AWAITING HUMAN DECISION - DO NOT SELF-DECLARE A WINNER", 8, len(canvas) - 12, color=WARN)
    return canvas
