"""Preview sheets: isolated contact, gameplay-size Farmer composites, controlled
pairs, and an anatomy sheet that visualises the architecture classification.

The Farmer compositor mirrors the installed FarmerRenderer layout: the Farmer at
4x, a 16x16 shirt blitted at 2x at (16, 56 + featureY*4).
"""

from __future__ import annotations

import os
from pathlib import Path

from .body import W
from .pngio import (RGBA, blank_image, blit, draw_rect, draw_text, flip_h,
                    nearest_scale, read_rgba_png)

CONTENT = Path(os.environ.get(
    "STARDEW_CONTENT",
    "/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)"))
DIRECTIONS = ("front", "right", "back", "left")
BODY_FRAME = {"front": 0, "right": 6, "back": 12, "left": 6}
FEATURE_Y = {0: 1, 6: 1, 12: 0}
HAIR_TINT: RGBA = (112, 76, 52, 255)
BG: RGBA = (231, 226, 218, 255); PANEL: RGBA = (204, 197, 187, 255)
INK: RGBA = (38, 36, 35, 255); ACC: RGBA = (44, 112, 122, 255); WARN: RGBA = (162, 72, 52, 255)


class Farmer:
    def __init__(self, content: Path = CONTENT):
        self.available = (content / "Characters/Farmer/farmer_base.png").exists()
        if self.available:
            self.body = read_rgba_png(content / "Characters/Farmer/farmer_base.png")
            self.hair = read_rgba_png(content / "Characters/Farmer/hairstyles.png")

    def _crop(self, px, x, y, w, h): return [list(r[x:x + w]) for r in px[y:y + h]]

    def _body(self, d):
        i = BODY_FRAME[d]; f = self._crop(self.body, i % 6 * 16, i // 6 * 32, 16, 32)
        return flip_h(f) if d == "left" else f

    def _hair(self, d):
        y = 32 if d in ("right", "left") else 64 if d == "back" else 0
        f = self._crop(self.hair, 0, y, 16, 32)
        f = flip_h(f) if d == "left" else f
        return [[(p[0] * HAIR_TINT[0] // 255, p[1] * HAIR_TINT[1] // 255,
                  p[2] * HAIR_TINT[2] // 255, p[3]) for p in r] for r in f]

    def composite(self, shirt, d) -> list[list[RGBA]]:
        canvas = blank_image(64, 128, PANEL)
        fy = FEATURE_Y[BODY_FRAME[d]]
        if self.available:
            blit(canvas, nearest_scale(self._body(d), 4), 0, 0)
        blit(canvas, nearest_scale(shirt, 2), 16, 56 + fy * 4)
        if self.available:
            blit(canvas, nearest_scale(self._hair(d), 4), 0, fy * 4 + (4 if d == "back" else 0))
        return canvas


def _tile(canvas, img, x, y, border=ACC):
    draw_rect(canvas, x - 2, y - 2, len(img[0]) + 4, len(img) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(img[0]) + 2, len(img) + 2, PANEL)
    blit(canvas, img, x, y)


def contact_sheet(items, title) -> list[list[RGBA]]:
    """12 variants, four isolated directions each, 5x."""
    scale = 5; cell = W * scale; gap = 8; label = 168
    row_h = cell + 26
    canvas = blank_image(label + 4 * (cell + gap) + 12, 40 + len(items) * row_h, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for c, d in enumerate(DIRECTIONS):
        draw_text(canvas, d.upper(), label + c * (cell + gap), 24, color=ACC)
    for r, it in enumerate(items):
        y = 40 + r * row_h
        s = it["spec"]
        draw_text(canvas, it["label"][:26], 6, y + 4, color=INK)
        draw_text(canvas, f"{s.collar_width[:4]}/{s.rear_flap_depth[:4]}/{s.trim_style[:3]}", 6, y + 16, color=ACC)
        draw_text(canvas, f"{s.center_detail[:4]} {s.fit[:4]} {s.material[:5]}", 6, y + 28, color=ACC)
        for c, d in enumerate(DIRECTIONS):
            _tile(canvas, nearest_scale(it["images"][d], scale), label + c * (cell + gap), y)
    return canvas


def gameplay_sheet(items, farmer: Farmer, title) -> list[list[RGBA]]:
    """Gameplay-size read: the Farmer wearing each variant, four directions."""
    cols = 4
    cell_w = 4 * 68 + 14
    rows = (len(items) + cols // 4 - 1)
    canvas = blank_image(cell_w * 2 + 200, 44 + ((len(items) + 1) // 2) * 148, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for i, it in enumerate(items):
        col = i % 2; row = i // 2
        x0 = 8 + col * (cell_w + 92); y0 = 34 + row * 148
        draw_text(canvas, it["label"][:24], x0, y0, color=INK)
        for c, d in enumerate(DIRECTIONS):
            _tile(canvas, farmer.composite(it["images"][d], d), x0 + 92 + c * 68 - 84, y0 + 12, ACC)
    return canvas


def pair_sheet(a, b, variable, farmer: Farmer) -> list[list[RGBA]]:
    """Controlled comparison: one variable changes, everything else pinned."""
    canvas = blank_image(4 * 68 + 4 * 88 + 240, 260, BG)
    draw_text(canvas, f"CONTROLLED PAIR - ONLY {variable.upper()} CHANGES", 8, 8, color=INK)
    for r, it in enumerate((a, b)):
        y = 34 + r * 112
        draw_text(canvas, f"{getattr(it['spec'], variable)}", 8, y + 6, color=WARN)
        draw_text(canvas, it["label"][:22], 8, y + 20, color=ACC)
        for c, d in enumerate(DIRECTIONS):
            _tile(canvas, nearest_scale(it["images"][d], 5), 150 + c * 88, y)
            _tile(canvas, farmer.composite(it["images"][d], d), 150 + 4 * 88 + 16 + c * 68, y - 12, WARN)
    return canvas


ANATOMY_COLORS = {
    "silhouette":  (176, 170, 160, 255),
    "occlusion":   (196, 84, 62, 255),
    "light_field": (108, 156, 186, 255),
    "free_edge":   (240, 196, 74, 255),
    "trim":        (108, 178, 122, 255),
    "detail":      (168, 112, 190, 255),
}


def _anatomy_class(system: str | None) -> str | None:
    if system is None:
        return None
    if system == "silhouette":
        return "silhouette"
    if system.startswith("occlusion"):
        return "occlusion"
    if "free_edge" in system:
        return "free_edge"
    if system.startswith("trim"):
        return "trim"
    if system.startswith("center_detail"):
        return "detail"
    if "light_field" in system:
        return "light_field"
    return "silhouette"


def anatomy_sheet(items, title) -> list[list[RGBA]]:
    """Colour-codes which construction system owns each cell.

    Yellow marks FREE edges, red marks OCCLUSION cast onto the body. Where the
    flap meets the shoulder there is deliberately no yellow: that edge is
    ATTACHED, which is what stops the panel reading as a pasted square.
    """
    scale = 6; cell = W * scale; gap = 8; label = 168
    show = ("front", "right", "back")
    canvas = blank_image(label + 3 * (cell + gap) + 260, 60 + len(items) * (cell + 16), BG)
    draw_text(canvas, title, 8, 8, color=INK)
    lx = label + 3 * (cell + gap) + 10
    for i, (name, col) in enumerate(ANATOMY_COLORS.items()):
        draw_rect(canvas, lx, 26 + i * 14, 10, 10, col)
        draw_text(canvas, name.replace("_", " "), lx + 16, 27 + i * 14, color=INK)
    for c, d in enumerate(show):
        draw_text(canvas, d.upper(), label + c * (cell + gap), 24, color=ACC)
    for r, it in enumerate(items):
        y = 40 + r * (cell + 16)
        draw_text(canvas, it["label"][:26], 6, y + 4, color=INK)
        for c, d in enumerate(show):
            frame = it["frames"][d]
            img = blank_image(W, W)
            for yy in range(W):
                for xx in range(W):
                    k = _anatomy_class(frame.system[yy][xx])
                    if k:
                        img[yy][xx] = ANATOMY_COLORS[k]
            _tile(canvas, nearest_scale(img, scale), label + c * (cell + gap), y)
    return canvas
