"""Preview rendering: role/region template -> RGBA, contact sheet, offline worn preview.

Palettes here are PREVIEW-ONLY ramps used to look at the template; the frozen
generator owns real material/palette remixing.

The worn preview is an offline approximation of FarmerRenderer placement
(vanilla farmer_base + hairstyle 0, hat at -2,-2 of the 16x32 body frame, hair
+1) — the same convention as tools/preview_trucker_neutral_template.py.  It is
NOT a QC Bridge capture.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from v5.pngio import blank_image, blit, draw_text, flip_h, nearest_scale, read_rgba_png  # noqa: E402

from engine import SIZE, VIEWS  # noqa: E402

CONTENT = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)")
FARMER = CONTENT / "Characters/Farmer"
MAS = ROOT / "generator content/[FS] More Accessories and Stuff Pack/Hats"
COTTAGE = ROOT / "generator content/[FS] Cottagecore Set/Hats"
CAST = (33, 9, 19, 255)          # vanilla's under-brim cast colour (hats.png)

# ramps: O, S, M, L, H — hue-shifted dark->light, outline darkest
RAMPS = {
    "olive":  [(36, 44, 21), (57, 63, 35), (76, 84, 51), (106, 123, 72), (161, 166, 97)],
    "khaki":  [(66, 48, 30), (122, 96, 62), (158, 130, 86), (196, 170, 118), (228, 208, 160)],
    "denim":  [(24, 30, 58), (44, 62, 108), (62, 92, 150), (92, 128, 186), (150, 182, 222)],
    "straw":  [(81, 44, 12), (173, 91, 24), (206, 132, 53), (255, 182, 72), (255, 225, 104)],
    "cream":  [(74, 60, 52), (176, 158, 136), (214, 200, 176), (238, 228, 206), (252, 248, 236)],
    "rust":   [(58, 20, 22), (120, 40, 34), (160, 62, 44), (196, 98, 62), (228, 148, 98)],
    "charcoal": [(26, 25, 28), (46, 45, 49), (69, 67, 72), (105, 102, 109), (140, 137, 146)],
    "navy":   [(20, 22, 44), (34, 40, 80), (52, 60, 112), (78, 90, 150), (120, 132, 190)],
}
# preview palettes: region -> ramp
PALETTES = {
    "olive":  {"crown": "olive", "brim_top": "olive", "brim_under": "olive", "band": "khaki"},
    "denim":  {"crown": "denim", "brim_top": "denim", "brim_under": "denim", "band": "cream"},
    "straw":  {"crown": "straw", "brim_top": "straw", "brim_under": "straw", "band": "rust"},
    "charcoal": {"crown": "charcoal", "brim_top": "charcoal", "brim_under": "charcoal", "band": "navy"},
}
ROLE_INDEX = {"O": 0, "S": 1, "M": 2, "L": 3, "H": 4}
# role-map debug colours
ROLE_DEBUG = {"O": (20, 20, 24, 255), "S": (90, 90, 110, 255), "M": (150, 150, 165, 255),
              "L": (205, 205, 215, 255), "H": (250, 250, 255, 255), "C": (120, 30, 60, 255)}
REGION_DEBUG = {"crown": (214, 120, 70, 255), "band": (240, 210, 70, 255), "brim_top": (90, 160, 210, 255),
                "brim_under": (40, 80, 150, 255), "cast": (120, 30, 60, 255)}


def render_view(grid, palette="olive", mode="colour"):
    out = blank_image(SIZE, SIZE)
    for y in range(SIZE):
        for x in range(SIZE):
            c = grid.cells[y][x]
            if not c:
                continue
            region, role = c
            if mode == "roles":
                out[y][x] = ROLE_DEBUG[role]
            elif mode == "regions":
                out[y][x] = REGION_DEBUG[region]
            elif role == "C":
                out[y][x] = CAST
            else:
                ramp = RAMPS[PALETTES[palette][region]]
                out[y][x] = tuple(ramp[ROLE_INDEX[role]]) + (255,)
    return out


def render_strip(tpl, palette="olive", mode="colour"):
    """20x80, vanilla hats.png order front/right/left/back."""
    strip = []
    for v in VIEWS:
        strip += render_view(tpl["views"][v], palette, mode)
    return strip


# --------------------------------------------------------------------------- references

def vanilla_names():
    data = json.loads((CONTENT / "Data/hats.json").read_text())
    names = {}
    for k, v in data.items():
        parts = v.split("/")
        idx = int(parts[-1]) if parts[-1].isdigit() else (int(k) if k.isdigit() else None)
        if idx is not None:
            names[idx] = parts[0]
    return names


def vanilla_strip(idx, sheet=None):
    sheet = sheet or read_rgba_png(FARMER / "hats.png")
    x, y = (idx % 12) * 20, (idx // 12) * 80
    return [row[x:x + 20] for row in sheet[y:y + 80]]


def vanilla_bank():
    sheet = read_rgba_png(FARMER / "hats.png")
    n = (len(sheet[0]) // 20) * (len(sheet) // 80)
    names = vanilla_names()
    return {f"vanilla:{names.get(i, i)} ({i})": vanilla_strip(i, sheet) for i in range(n)}


def fs_strip(png):
    """plurffle 20x60 front/side/back -> 20x80 with left = mirrored side (FS flips Left)."""
    p = read_rgba_png(png)
    side = p[20:40]
    return p[0:20] + side + flip_h(side) + p[40:60]


def mod_bank():
    out = {}
    for label, path in (("plurffle:Sun Hat", MAS / "SunHat/hat.png"),
                        ("plurffle:Straw Hat", MAS / "StrawHat/hat.png"),
                        ("plurffle:Boater Hat", COTTAGE / "BoaterHat/hat.png")):
        if path.exists():
            out[label] = fs_strip(path)
    return out


# --------------------------------------------------------------------------- worn

_BODY = None


def _farmer():
    global _BODY
    if _BODY is None:
        body = read_rgba_png(FARMER / "farmer_base.png")
        hair = read_rgba_png(FARMER / "hairstyles.png")
        hair = [[(r * 120 // 255, g * 80 // 255, b * 55 // 255, a) if a else (r, g, b, a)
                 for (r, g, b, a) in row] for row in hair]
        _BODY = (body, hair)
    return _BODY


# (body frame, flip, hair row) per view
_WORN = {"front": (0, False, 0), "right": (6, False, 1), "left": (6, True, 1), "back": (12, False, 2)}


def worn_tile(strip, view, bg=(126, 150, 110, 255)):
    """24x40 tile: farmer + hat for one view."""
    body, hair = _farmer()
    f, flip, hrow = _WORN[view]
    out = blank_image(24, 40, bg)
    s = [row[(f % 6) * 16:(f % 6) * 16 + 16] for row in body[(f // 6) * 32:(f // 6) * 32 + 32]]
    hh = [row[0:16] for row in hair[hrow * 32:hrow * 32 + 32]]
    if flip:
        s, hh = flip_h(s), flip_h(hh)
    ox, oy = 4, 6
    blit(out, s, ox, oy)
    blit(out, hh, ox, oy + 1)
    vi = VIEWS.index(view)
    blit(out, strip[vi * 20:vi * 20 + 20], ox - 2, oy - 2)
    return out


def worn_row(strip, bg=(126, 150, 110, 255)):
    row = blank_image(96, 40, bg)
    for i, v in enumerate(VIEWS):
        blit(row, worn_tile(strip, v, bg), i * 24, 0)
    return row
