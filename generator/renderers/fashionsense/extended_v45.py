"""Logical-pixel renderers for bounded V4.5 extended-garment prototypes.

These are capability fixtures, not a production outfit engine. Every visible
cell is authored directly at the target Fashion Sense logical resolution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA, TRANSPARENT, blank_image
from generator.v45.engine import load_v45_data, validate_v45_recipe


ROOT = Path(__file__).resolve().parents[3]
GRAMMAR = ROOT / "generator" / "data" / "fashionsense" / "v45_extended_grammar.json"
DIRECTIONS = ("front", "back", "right", "left")


@dataclass(frozen=True)
class FSV45PrototypeRender:
    recipe: dict[str, Any]
    contract: dict[str, Any]
    frames: dict[str, tuple[list[list[RGBA]], ...]]
    texture: list[list[RGBA]]
    occupied_cells: dict[str, tuple[int, ...]]
    alpha_binary: bool
    static_contract_passes: bool
    static_errors: tuple[str, ...]


def load_v45_fs_grammar() -> dict[str, Any]:
    return json.loads(GRAMMAR.read_text(encoding="utf-8"))


def _palette():
    return load_v45_data()["designConcept"]["paletteRoles"]


def _rgba(rgb) -> RGBA:
    return tuple(rgb) + (255,)


def _set(mask, x, y, region):
    if 0 <= y < len(mask) and 0 <= x < len(mask[0]): mask[y][x] = region


def _fill(mask, x0, x1, y0, y1, region):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): _set(mask, x, y, region)


def _render_regions(mask, colors):
    h = len(mask); w = len(mask[0]); frame = blank_image(w, h)
    occupied = {(x, y) for y in range(h) for x in range(w) if mask[y][x] is not None}
    for x, y in occupied:
        region = mask[y][x]
        exterior = any((x + dx, y + dy) not in occupied for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        frame[y][x] = colors["outline"] if exterior else colors.get(region, colors["base"])
    return frame


def _pants_mask(direction, phase, rare=False):
    mask = [[None for _ in range(16)] for _ in range(12)]
    if direction in {"front", "back"}:
        _fill(mask, 4, 11, 0, 5, "base")
        left_shift = -1 if phase == 1 else 0; right_shift = 1 if phase == 2 else 0
        if phase == 3: left_shift, right_shift = -1, 1
        _fill(mask, 4 + left_shift, 7 + left_shift, 5, 11, "base")
        _fill(mask, 8 + right_shift, 11 + right_shift, 5, 11, "base")
        for y in range(5, 11): _set(mask, 7, y, "crease")
        for x in range(5, 11): _set(mask, x, 1, "waist")
        if rare:
            for x in (4 + left_shift, 5 + left_shift, 10 + right_shift, 11 + right_shift):
                for y in (6, 7): _set(mask, x, y, "panel")
            if direction == "front":
                for x, y in ((5, 2), (6, 3), (7, 4)): _set(mask, x, y, "leather")
    else:
        shift = -1 if (direction == "left" and phase in {1, 3}) else 1 if (direction == "right" and phase in {2, 3}) else 0
        _fill(mask, 5, 10, 0, 5, "base")
        _fill(mask, 6 + shift, 10 + shift, 5, 11, "base")
        for y in range(2, 10): _set(mask, 6 if direction == "left" else 9, y, "panel" if rare else "crease")
    return mask


def _skirt_mask(direction, phase):
    mask = [[None for _ in range(16)] for _ in range(10)]
    sway = -1 if phase == 1 else 1 if phase == 2 else 0
    if direction in {"front", "back"}:
        _fill(mask, 5, 10, 0, 1, "waist")
        for y in range(2, 9):
            inset = max(0, 2 - y // 3)
            _fill(mask, 3 + inset + (sway if y > 5 else 0), 12 - inset + (sway if y > 5 else 0), y, y, "base")
        _fill(mask, 3 + sway, 12 + sway, 9, 9, "hem")
        for x in (6, 9):
            for y in range(2, 9): _set(mask, x + (sway if y > 5 else 0), y, "pleat")
    else:
        _fill(mask, 6, 10, 0, 1, "waist")
        for y in range(2, 9): _fill(mask, 5 + (sway if y > 5 else 0), 11 + (sway if y > 5 else 0), y, y, "base")
        _fill(mask, 5 + sway, 11 + sway, 9, 9, "hem")
        for y in range(3, 9): _set(mask, 7 + sway, y, "pleat")
    return mask


def _shoes_mask(direction, phase, tall):
    mask = [[None for _ in range(16)] for _ in range(12)]
    top = 3 if tall else 7
    if direction in {"front", "back"}:
        ls = -1 if phase in {1, 3} else 0; rs = 1 if phase in {2, 3} else 0
        _fill(mask, 4 + ls, 7 + ls, top, 10, "base"); _fill(mask, 8 + rs, 11 + rs, top, 10, "base")
        _fill(mask, 3 + ls, 7 + ls, 10, 11, "sole"); _fill(mask, 8 + rs, 12 + rs, 10, 11, "sole")
        if tall:
            for x in range(4 + ls, 8 + ls): _set(mask, x, 4, "cuff")
            for x in range(8 + rs, 12 + rs): _set(mask, x, 4, "cuff")
            for x, y in ((5 + ls, 7), (6 + ls, 7), (9 + rs, 7), (10 + rs, 7)): _set(mask, x, y, "strap")
    else:
        shift = -1 if direction == "left" and phase in {1, 3} else 1 if direction == "right" and phase in {2, 3} else 0
        _fill(mask, 6 + shift, 10 + shift, top, 10, "base"); _fill(mask, 5 + shift, 12 + shift, 10, 11, "sole")
        if tall:
            _fill(mask, 6 + shift, 10 + shift, 4, 4, "cuff"); _fill(mask, 6 + shift, 10 + shift, 7, 7, "strap")
    return mask


def _mantle_mask(direction, phase, tail_only=False):
    height = 24 if tail_only else 32; mask = [[None for _ in range(24)] for _ in range(height)]
    sway = -1 if phase == 1 else 1 if phase == 2 else 0
    if tail_only:
        _fill(mask, 7, 16, 1, 4, "anchor")
        for y in range(5, 22):
            spread = min(3, (y - 4) // 5)
            _fill(mask, 7 - spread + sway, 11 + sway, y, y, "base")
            _fill(mask, 12 + sway, 16 + spread + sway, y, y, "base")
        for x in range(5 + sway, 19 + sway): _set(mask, x, 22, "border")
        return mask
    if direction == "front":
        _fill(mask, 7, 16, 5, 8, "anchor")
        _fill(mask, 7, 9, 8, 13, "base"); _fill(mask, 14, 16, 8, 13, "base")
        _set(mask, 11, 8, "clasp"); _set(mask, 12, 8, "clasp")
    elif direction == "back":
        for y in range(5, 29):
            spread = min(4, (y - 4) // 5)
            _fill(mask, 8 - spread + sway, 15 + spread + sway, y, y, "base")
        for x in range(4 + sway, 20 + sway): _set(mask, x, 29, "border")
        # Original split-feather crest: paired angular planes, not a copied logo.
        for x, y in ((8, 13), (9, 14), (10, 15), (11, 16), (15, 13), (14, 14), (13, 15), (12, 16), (9, 17), (14, 17)):
            _set(mask, x + sway, y, "emblem")
    else:
        lean = 1 if direction == "right" else -1
        _fill(mask, 8, 14, 5, 9, "anchor")
        for y in range(9, 29):
            edge = min(5, (y - 8) // 4)
            x0 = 7 + min(0, lean * edge) + sway; x1 = 15 + max(0, lean * edge) + sway
            _fill(mask, x0, x1, y, y, "base")
        for x in range(4 + sway, 19 + sway): _set(mask, x, 29, "border")
    return mask


def _colors(recipe):
    p = _palette(); subtype = recipe["articleSubtype"]
    colors = {"outline": _rgba(p["outline"]), "crease": _rgba(p["fieldDark"]), "leather": _rgba(p["leather"]),
              "waist": _rgba(p["leather"]), "panel": _rgba(p["fieldDark"]), "cuff": _rgba(p["fieldMid"]),
              "strap": _rgba(p["leather"]), "sole": _rgba(p["outline"]), "hem": _rgba(p["leather"]),
              "pleat": _rgba(p["fieldDark"]), "border": _rgba(p["fieldLight"]), "anchor": _rgba(p["fieldDark"]),
              "clasp": _rgba(p["light"]), "emblem": _rgba(p["cream"])}
    if subtype == "FITTED_FIELD_TROUSERS": colors["base"] = _rgba(p["cream"])
    elif subtype in {"PANEL_FIELD_TROUSERS", "BACK_FIELD_MANTLE"}: colors["base"] = _rgba(p["fieldMid"])
    elif subtype == "SHORT_PLEATED_SKIRT": colors["base"] = _rgba(p["fieldLight"])
    else: colors["base"] = _rgba(p["fieldDark"])
    return colors


def _stack(frames, width, height, count):
    texture = blank_image(width * count, height * 4)
    for row, direction in enumerate(DIRECTIONS):
        for index, frame in enumerate(frames[direction]):
            for y, pixels in enumerate(frame):
                texture[row * height + y][index * width:index * width + width] = list(pixels)
    return texture


def render_v45_prototype(recipe: dict[str, Any]) -> FSV45PrototypeRender:
    errors = list(validate_v45_recipe(recipe))
    grammar = load_v45_fs_grammar(); key = recipe["articleSubtype"]
    if recipe["articleType"] == "PANTS": key = "PANTS"
    elif recipe["articleType"] == "SKIRT": key = "SKIRT"
    elif recipe["articleType"] == "MANTLE": key = "MANTLE"
    elif recipe["articleType"] == "COAT_TAIL_COMPANION": key = "COAT_TAIL_COMPANION"
    contract = grammar["contracts"][key]; width, height = contract["frameSize"]; count = contract["frameCount"]
    colors = _colors(recipe); frames = {}
    for direction in DIRECTIONS:
        built = []
        for phase in range(count):
            article = recipe["articleType"]
            if article == "PANTS": mask = _pants_mask(direction, phase, rare=recipe["rarity"] == "Rare")
            elif article == "SKIRT": mask = _skirt_mask(direction, phase)
            elif article == "FOOTWEAR": mask = _shoes_mask(direction, phase, recipe["articleSubtype"] == "TALL_BOOTS")
            else: mask = _mantle_mask(direction, phase, tail_only=article == "COAT_TAIL_COMPANION")
            built.append(_render_regions(mask, colors))
        frames[direction] = tuple(built)
    texture = _stack(frames, width, height, count)
    occupied = {d: tuple(sum(pixel[3] > 0 for row in f for pixel in row) for f in frames[d]) for d in DIRECTIONS}
    alpha = {pixel[3] for row in texture for pixel in row}
    if alpha - {0, 255}: errors.append("alpha is not binary")
    if any(min(values) == 0 for values in occupied.values()): errors.append("one or more direction frames are empty")
    return FSV45PrototypeRender(recipe, contract, frames, texture, occupied, not bool(alpha - {0, 255}), not errors, tuple(errors))

