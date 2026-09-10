"""V5D benchmark-informed masculine upper-garment renderer.

This is a bounded grammar layer over the proven V5B runtime backend. It never
loads benchmark or vanilla art. All cells below implement reusable construction
programs chosen by coordinate-free V5D semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from generator.png_utils import RGBA, TRANSPARENT
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import FSV5BUpperRender, _coverage_missing, _idle_frames, _stack, render_fs_v5b
from generator.renderers.fashionsense.upper_v5c2 import (
    _bounds,
    _clear,
    _fixed,
    _put_fixed,
    _put_mask,
    _reset_v3_surface,
    _ribbed_hem,
)
from generator.v5d.engine import validate_v5d_recipe


SYSTEMS = ("silhouette", "collar", "opening", "layering", "pockets", "panels", "trim", "pattern", "motif", "hem")


@dataclass(frozen=True)
class FSV5DRender:
    recipe: dict[str, Any]
    base: FSV5BUpperRender
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    signal_cells: dict[str, dict[str, frozenset[tuple[int, int]]]]
    removed_cells: dict[str, frozenset[tuple[int, int]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    hide_native_sleeves: bool
    companion_required: bool
    sleeves_texture: list[list[RGBA]] | None
    sleeves_json: dict[str, Any] | None
    sleeve_idle_frames: dict[str, list[list[RGBA]]] | None
    sleeve_metrics: dict[str, Any]


def _signals():
    return {name: {direction: set() for direction in DIRECTION_ORDER} for name in SYSTEMS}


def _freeze(signals):
    return {name: {direction: frozenset(cells) for direction, cells in views.items()} for name, views in signals.items()}


def _shape(recipe, frames, defaults, signals, removed) -> None:
    role = recipe["articleRole"]
    fitted = role in {"CASUAL_SHIRT", "FORMAL_WAISTCOAT", "FORMAL_BLAZER", "PERIOD_TOP", "ALT_STREET_TOP"}
    for direction in DIRECTION_ORDER:
        if fitted:
            for y in range(10, 16):
                bounds = _bounds(frames[direction], y)
                if bounds and bounds[1] - bounds[0] >= 10:
                    _clear(frames, defaults, signals, removed, direction, bounds[0], y)
                    _clear(frames, defaults, signals, removed, direction, bounds[1], y)
        if role == "CROPPED_FIELD_JACKET":
            for y in range(13, 16):
                for x in range(16):
                    _clear(frames, defaults, signals, removed, direction, x, y)


def _wrap_band(render, frames, defaults, signals, system, y: int, role: str = "secondary", thickness: int = 1) -> None:
    for direction in DIRECTION_ORDER:
        for yy in range(y, min(16, y + thickness)):
            bounds = _bounds(frames[direction], yy)
            if not bounds:
                continue
            for x in range(bounds[0] + 1, bounds[1]):
                _put_fixed(render, frames, defaults, signals, system, direction, x, yy, role)


def _back_yoke(render, frames, defaults, signals, *, role: str = "STRUCTURAL_EDGE") -> None:
    for x in range(3, 13):
        y = 3 if 5 <= x <= 10 else 2
        _put_mask(render, frames, defaults, signals, "panels", "back", x, y, role)
    for direction in ("right", "left"):
        for x in range(5, 11):
            xx = x if direction == "right" else 15 - x
            _put_mask(render, frames, defaults, signals, "panels", direction, xx, 3, role)


def _pair_pockets(render, frames, defaults, signals, *, y: int, width: int = 3, role: str = "secondary") -> None:
    starts = (3, 13 - width)
    for start in starts:
        for x in range(start, start + width):
            _put_mask(render, frames, defaults, signals, "pockets", "front", x, y, "STRUCTURAL_EDGE")
            _put_fixed(render, frames, defaults, signals, "pockets", "front", x, y + 1, role)


def _tailored_corners(render, frames, defaults, signals) -> None:
    for direction in DIRECTION_ORDER:
        rows = [y for y in range(16) if any(pixel[3] for pixel in frames[direction][y])]
        if not rows:
            continue
        bottom = max(rows)
        bounds = _bounds(frames[direction], bottom)
        if bounds:
            for x in (bounds[0], min(bounds[0] + 1, bounds[1]), max(bounds[1] - 1, bounds[0]), bounds[1]):
                _put_mask(render, frames, defaults, signals, "hem", direction, x, bottom, "DEEP_CREASE")


def _casual(render, frames, defaults, signals) -> None:
    # The frozen BUTTON_SHIRT foundation owns a full-height four-cell placket.
    # A henley does not: replace that inherited region with neighboring body
    # cloth, then author only the short semantic opening below. This is an
    # article rule, not a Tideglass-specific coordinate patch.
    regions = render.base.design.base.regions
    for direction in DIRECTION_ORDER:
        for y in range(16):
            body = [x for x in range(16) if regions[direction][y][x] == "BODY" and frames[direction][y][x][3]]
            if not body:
                continue
            body_frame_values = [frames[direction][y][x] for x in body]
            body_default_values = [defaults[direction][y][x] for x in body]
            # A row's dominant cloth value preserves the existing light bias
            # while avoiding a nearby structural crease becoming a new stripe.
            frame_value = max(set(body_frame_values), key=body_frame_values.count)
            default_value = max(set(body_default_values), key=body_default_values.count)
            for x in range(16):
                if regions[direction][y][x] != "PLACKET" or not frames[direction][y][x][3]:
                    continue
                frames[direction][y][x] = frame_value
                defaults[direction][y][x] = default_value
    for x, y in ((6, 1), (7, 1), (8, 1), (9, 1), (5, 2), (10, 2)):
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, y, "secondary")
    for y in range(3, 7):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "STRUCTURAL_EDGE")
    for x, y in ((8, 4), (8, 6)):
        _put_fixed(render, frames, defaults, signals, "trim", "front", x, y, "accent")
    # A narrow chest rhythm wraps but leaves the center placket readable.
    for direction in DIRECTION_ORDER:
        bounds = _bounds(frames[direction], 8)
        if bounds:
            for x in range(bounds[0] + 2, bounds[1] - 1):
                if direction == "front" and x in {7, 8}:
                    continue
                _put_fixed(render, frames, defaults, signals, "pattern", direction, x, 8, "secondary")


def _workshirt(render, frames, defaults, signals) -> None:
    for x, y in ((4, 1), (5, 1), (10, 1), (11, 1), (5, 2), (6, 2), (9, 2), (10, 2)):
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, y, "light_accent")
    for y in range(3, 15):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "STRUCTURAL_EDGE")
    for y in (5, 8, 11, 14):
        _put_fixed(render, frames, defaults, signals, "trim", "front", 8, y, "accent")
    _pair_pockets(render, frames, defaults, signals, y=7)
    _back_yoke(render, frames, defaults, signals)
    _tailored_corners(render, frames, defaults, signals)


def _knit(render, frames, defaults, signals) -> None:
    for direction in DIRECTION_ORDER:
        for x, y in ((6, 1), (7, 1), (8, 1), (9, 1), (5, 2), (10, 2)):
            _put_fixed(render, frames, defaults, signals, "collar", direction, x, y, "secondary")
    for direction in DIRECTION_ORDER:
        for y in (4, 5, 6):
            bounds = _bounds(frames[direction], y)
            if bounds:
                for x in range(bounds[0] + 1, bounds[1]):
                    role = "light_accent" if (x + y) % 5 in {0, 1} else "secondary"
                    _put_fixed(render, frames, defaults, signals, "pattern", direction, x, y, role)
    _ribbed_hem(render, frames, defaults, signals)


def _hoodie(render, frames, defaults, signals) -> None:
    front_outer = ((4, 0), (11, 0), (3, 1), (12, 1), (4, 2), (11, 2), (5, 3), (10, 3))
    front_inner = ((5, 0), (6, 0), (9, 0), (10, 0), (4, 1), (5, 1), (10, 1), (11, 1), (5, 2), (6, 2), (9, 2), (10, 2))
    for x, y in front_outer:
        _put_mask(render, frames, defaults, signals, "collar", "front", x, y, "DEEP_CREASE")
    for x, y in front_inner:
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, y, "secondary")
    for direction in ("back", "right", "left"):
        for y, half in ((0, 3), (1, 4), (2, 4), (3, 3), (4, 2)):
            lo, hi = 8 - half, 8 + half
            for x in range(lo, hi):
                boundary = x in {lo, hi - 1} or y == 0
                if boundary:
                    _put_mask(render, frames, defaults, signals, "collar", direction, x, y, "DEEP_CREASE")
                else:
                    _put_fixed(render, frames, defaults, signals, "collar", direction, x, y, "secondary")
    # Connected pouch with intentional side termination.
    for x in range(5, 11):
        _put_mask(render, frames, defaults, signals, "pockets", "front", x, 9, "STRUCTURAL_EDGE")
        _put_fixed(render, frames, defaults, signals, "pockets", "front", x, 12, "secondary")
    for y in (10, 11):
        for x in range(4, 12):
            role = "dark_accent" if x in {4, 11} else "secondary"
            _put_fixed(render, frames, defaults, signals, "pockets", "front", x, y, role)
    _ribbed_hem(render, frames, defaults, signals)


def _cardigan(render, frames, defaults, signals) -> None:
    # Broad inner shirt and two knitted edges distinguish this from a jacket.
    for y in range(2, 14):
        spread = 1 if y < 5 else 2
        for x in range(8 - spread, 8 + spread):
            _put_fixed(render, frames, defaults, signals, "layering", "front", x, y, "light_accent")
        for x in (8 - spread - 1, 8 + spread):
            _put_fixed(render, frames, defaults, signals, "opening", "front", x, y, "secondary")
    for x in range(4, 7):
        _put_mask(render, frames, defaults, signals, "pockets", "front", x, 10, "STRUCTURAL_EDGE")
        _put_fixed(render, frames, defaults, signals, "pockets", "front", x, 11, "secondary")
    for x in range(9, 12):
        _put_mask(render, frames, defaults, signals, "pockets", "front", x, 10, "STRUCTURAL_EDGE")
        _put_fixed(render, frames, defaults, signals, "pockets", "front", x, 11, "secondary")
    for x in range(5, 11):
        _put_fixed(render, frames, defaults, signals, "collar", "back", x, 1 if x in {6, 7, 8, 9} else 2, "secondary")
    for direction, x in (("right", 10), ("left", 5)):
        for y in range(3, 13):
            _put_fixed(render, frames, defaults, signals, "opening", direction, x, y, "secondary")
    _ribbed_hem(render, frames, defaults, signals)


def _waistcoat(render, frames, defaults, signals) -> None:
    for x, y in ((5, 1), (10, 1), (6, 2), (9, 2), (7, 3), (8, 3), (7, 4), (8, 4)):
        _put_fixed(render, frames, defaults, signals, "layering", "front", x, y, "light_accent")
    for x, y in ((4, 1), (11, 1), (5, 2), (10, 2), (6, 3), (9, 3), (6, 4), (9, 4)):
        _put_mask(render, frames, defaults, signals, "opening", "front", x, y, "DEEP_CREASE")
    for y in range(5, 14):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "STRUCTURAL_EDGE")
    for y in (7, 10, 13):
        _put_fixed(render, frames, defaults, signals, "trim", "front", 8, y, "accent")
    for start in (3, 10):
        for x in range(start, start + 3):
            _put_mask(render, frames, defaults, signals, "pockets", "front", x, 10, "STRUCTURAL_EDGE")
    for x in range(5, 11):
        _put_fixed(render, frames, defaults, signals, "panels", "back", x, 2, "secondary")
    _tailored_corners(render, frames, defaults, signals)


def _utility_vest(render, frames, defaults, signals) -> None:
    for x in range(5, 11):
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, 1, "light_accent")
    for y in range(2, 15):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "DEEP_CREASE")
    for start in (2, 10):
        for y in range(6, 10):
            for x in range(start, start + 4):
                role = "dark_accent" if y in {6, 9} or x in {start, start + 3} else "secondary"
                _put_fixed(render, frames, defaults, signals, "pockets", "front", x, y, role)
    for x in (3, 4, 11, 12):
        _put_fixed(render, frames, defaults, signals, "panels", "front", x, 2, "secondary")
    _wrap_band(render, frames, defaults, signals, "hem", 12, "dark_accent", 1)
    _back_yoke(render, frames, defaults, signals)


def _field_jacket(render, frames, defaults, signals) -> None:
    for x, y in ((5, 1), (10, 1), (6, 2), (9, 2), (6, 3), (9, 3), (7, 4), (8, 4)):
        _put_mask(render, frames, defaults, signals, "opening", "front", x, y, "DEEP_CREASE")
    for y in range(3, 12):
        for x in (7, 8):
            _put_fixed(render, frames, defaults, signals, "layering", "front", x, y, "secondary")
    _pair_pockets(render, frames, defaults, signals, y=7, role="light_accent")
    _back_yoke(render, frames, defaults, signals)
    for direction, cells in (("right", ((7, 1), (8, 2), (9, 3), (9, 4))), ("left", ((8, 1), (7, 2), (6, 3), (6, 4)))):
        for x, y in cells:
            _put_mask(render, frames, defaults, signals, "opening", direction, x, y, "DEEP_CREASE")
    _tailored_corners(render, frames, defaults, signals)


def _blazer(render, frames, defaults, signals) -> None:
    for x, y in ((4, 1), (11, 1), (5, 2), (10, 2), (6, 3), (9, 3), (7, 4), (8, 4), (6, 5), (9, 5)):
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, y, "secondary")
    for y, span in ((2, range(6, 10)), (3, range(7, 9)), (4, range(7, 9))):
        for x in span:
            _put_fixed(render, frames, defaults, signals, "layering", "front", x, y, "light_accent")
    for y in range(4, 10):
        _put_fixed(render, frames, defaults, signals, "opening", "front", 7, y, "accent")
        _put_mask(render, frames, defaults, signals, "opening", "front", 8, y, "STRUCTURAL_EDGE")
    _put_fixed(render, frames, defaults, signals, "motif", "front", 11, 7, "light_accent")
    _put_fixed(render, frames, defaults, signals, "motif", "front", 12, 7, "accent")
    for x in range(5, 11):
        _put_mask(render, frames, defaults, signals, "panels", "back", x, 2, "STRUCTURAL_EDGE")
    for y in range(3, 8):
        _put_mask(render, frames, defaults, signals, "panels", "back", 7, y, "STRUCTURAL_EDGE")
    # Reconstruct the lapel on the visible side plane instead of flattening
    # the formal hierarchy into a front-only triangle.
    for direction, cells in (
        ("right", ((7, 1), (8, 2), (9, 3), (9, 4))),
        ("left", ((8, 1), (7, 2), (6, 3), (6, 4))),
    ):
        for x, y in cells:
            _put_fixed(render, frames, defaults, signals, "collar", direction, x, y, "secondary")
    _tailored_corners(render, frames, defaults, signals)


def _period(render, frames, defaults, signals) -> None:
    # High collar and connected cravat are the dominant gesture.
    for x in range(5, 11):
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, 1, "secondary")
    for x, y in ((6, 2), (7, 2), (8, 2), (9, 2), (7, 3), (8, 3), (6, 4), (7, 4), (8, 4), (9, 4), (7, 5), (8, 5)):
        _put_fixed(render, frames, defaults, signals, "motif", "front", x, y, "light_accent")
    for x, y in ((5, 6), (9, 7), (5, 9), (9, 10), (5, 12), (9, 13)):
        _put_fixed(render, frames, defaults, signals, "opening", "front", x, y, "accent")
    for x, y in ((4, 8), (5, 9), (6, 10), (7, 11)):
        _put_fixed(render, frames, defaults, signals, "trim", "front", x, y, "light_accent")
    for direction in DIRECTION_ORDER:
        bounds = _bounds(frames[direction], 7)
        if bounds:
            for x in (bounds[0] + 1, bounds[1] - 1):
                _put_fixed(render, frames, defaults, signals, "pattern", direction, x, 7, "secondary")
    for x in range(5, 11):
        _put_fixed(render, frames, defaults, signals, "collar", "back", x, 1, "secondary")
    # The high collar remains visible in profile, while a quiet back coat seam
    # replaces the front cravat as the subordinate period construction cue.
    for direction in ("right", "left"):
        for x in range(6, 10):
            _put_fixed(render, frames, defaults, signals, "collar", direction, x, 1, "secondary")
    for y in range(3, 11):
        _put_mask(render, frames, defaults, signals, "opening", "back", 7, y, "STRUCTURAL_EDGE")
    _tailored_corners(render, frames, defaults, signals)


def _military(render, frames, defaults, signals) -> None:
    for direction in DIRECTION_ORDER:
        for x in range(5, 11):
            _put_fixed(render, frames, defaults, signals, "collar", direction, x, 1, "secondary")
    for x in (3, 4, 11, 12):
        _put_fixed(render, frames, defaults, signals, "panels", "front", x, 2, "light_accent")
    for y in range(3, 13):
        _put_mask(render, frames, defaults, signals, "opening", "front", 7, y, "DEEP_CREASE")
    for y in (4, 7, 10):
        _put_fixed(render, frames, defaults, signals, "trim", "front", 8, y, "accent")
    _pair_pockets(render, frames, defaults, signals, y=6)
    _wrap_band(render, frames, defaults, signals, "hem", 12, "dark_accent")
    _back_yoke(render, frames, defaults, signals)


def _tunic(render, frames, defaults, signals) -> None:
    for x, y in ((5, 1), (10, 1), (6, 2), (9, 2), (7, 3), (8, 3)):
        _put_fixed(render, frames, defaults, signals, "layering", "front", x, y, "light_accent")
    for x, y in ((3, 2), (4, 2), (4, 3), (5, 3), (5, 4), (6, 4)):
        _put_fixed(render, frames, defaults, signals, "panels", "front", x, y, "secondary")
    for step in range(9):
        x, y = 4 + step, 4 + step
        if x < 14 and y < 13:
            _put_fixed(render, frames, defaults, signals, "trim", "front", x, y, "dark_accent")
            if x + 1 < 16:
                _put_fixed(render, frames, defaults, signals, "trim", "front", x + 1, y, "accent")
    _wrap_band(render, frames, defaults, signals, "hem", 12, "dark_accent")
    for y in (13, 14):
        for x in range(6, 10):
            _put_fixed(render, frames, defaults, signals, "panels", "front", x, y, "secondary")
    for x, y in ((10, 5), (11, 5), (10, 6), (11, 6)):
        _put_fixed(render, frames, defaults, signals, "motif", "front", x, y, "light_accent")
    # Sash resolves on right side; back retains only belt and shoulder echo.
    for x, y in ((7, 5), (8, 6), (9, 7), (10, 8)):
        _put_fixed(render, frames, defaults, signals, "trim", "right", x, y, "accent")
    _wrap_band(render, frames, defaults, signals, "hem", 12, "dark_accent")


def _armor(render, frames, defaults, signals) -> None:
    for direction in DIRECTION_ORDER:
        for x in range(5, 11):
            _put_mask(render, frames, defaults, signals, "collar", direction, x, 1, "DEEP_CREASE")
    # Plate caps and chest segments are connected masses.
    for start in (2, 10):
        for y in range(2, 6):
            for x in range(start, start + 4):
                role = "light_accent" if y == 2 else "secondary"
                _put_fixed(render, frames, defaults, signals, "panels", "front", x, y, role)
    for y in range(4, 14):
        for x in range(6, 10):
            _put_fixed(render, frames, defaults, signals, "layering", "front", x, y, "accent")
    for x, y in ((7, 6), (8, 6), (6, 7), (9, 7), (7, 8), (8, 8)):
        _put_fixed(render, frames, defaults, signals, "motif", "front", x, y, "light_accent")
    _wrap_band(render, frames, defaults, signals, "hem", 11, "dark_accent", 1)
    for direction in ("right", "left"):
        for x in range(4, 12):
            _put_fixed(render, frames, defaults, signals, "panels", direction, x, 3, "secondary")
    for x in range(4, 12):
        _put_fixed(render, frames, defaults, signals, "panels", "back", x, 3, "secondary")
    for y in range(5, 13):
        for x in range(6, 10):
            _put_fixed(render, frames, defaults, signals, "layering", "back", x, y, "accent")


def _alt(render, frames, defaults, signals) -> None:
    for x in range(5, 11):
        _put_fixed(render, frames, defaults, signals, "collar", "front", x, 1, "secondary")
    for x, y in ((3, 2), (4, 2), (5, 2), (3, 3), (4, 3), (5, 3), (4, 4), (5, 4)):
        _put_fixed(render, frames, defaults, signals, "panels", "front", x, y, "secondary")
    for step in range(10):
        x, y = 4 + step, 3 + step
        if x < 14 and y < 14:
            _put_mask(render, frames, defaults, signals, "opening", "front", x, y, "DEEP_CREASE")
            if x + 1 < 16:
                _put_fixed(render, frames, defaults, signals, "opening", "front", x + 1, y, "light_accent")
    for x, y in ((9, 6), (10, 7), (9, 8), (8, 7)):
        _put_fixed(render, frames, defaults, signals, "motif", "front", x, y, "accent")
    for x in range(4, 12):
        _put_fixed(render, frames, defaults, signals, "panels", "back", x, 3 if x < 8 else 4, "secondary")
    for x, y in ((7, 4), (8, 5), (9, 6), (10, 7)):
        _put_fixed(render, frames, defaults, signals, "opening", "right", x, y, "light_accent")
    # Asymmetry resolves differently on the far side: a short shoulder panel,
    # not a mirrored second zip. This keeps the article authored in profile.
    for x, y in ((5, 3), (6, 3), (6, 4), (7, 4)):
        _put_fixed(render, frames, defaults, signals, "panels", "left", x, y, "secondary")
    for x, y in ((5, 3), (6, 3), (7, 4), (8, 4), (9, 5), (10, 5)):
        _put_fixed(render, frames, defaults, signals, "panels", "back", x, y, "secondary")
    _tailored_corners(render, frames, defaults, signals)


ROLE_RENDERERS = {
    "CASUAL_SHIRT": _casual,
    "WORK_SHIRT": _workshirt,
    "KNIT_SWEATER": _knit,
    "STREET_HOODIE": _hoodie,
    "CARDIGAN": _cardigan,
    "FORMAL_WAISTCOAT": _waistcoat,
    "UTILITY_VEST": _utility_vest,
    "CROPPED_FIELD_JACKET": _field_jacket,
    "FORMAL_BLAZER": _blazer,
    "PERIOD_TOP": _period,
    "MILITARY_TOP": _military,
    "ADVENTURER_TUNIC": _tunic,
    "ARMOR_TABARD": _armor,
    "ALT_STREET_TOP": _alt,
}


def _decorate_sleeves(base: FSV5BUpperRender, recipe: dict[str, Any]):
    if base.sleeves_texture is None:
        return None, base.sleeve_metrics
    atlas = [[pixel for pixel in row] for row in base.sleeves_texture]
    mode = "none"
    if recipe["articleRole"] in {"STREET_HOODIE", "ALT_STREET_TOP"}:
        mode = "single_stripe"
    elif recipe["articleRole"] in {"MILITARY_TOP", "ARMOR_TABARD"}:
        mode = "reinforced_cuff"
    changed = 0
    if mode != "none":
        accent = _fixed(base, "accent" if mode == "single_stripe" else "dark_accent")
        tile_w, tile_h = 32, 64
        for tile_y in range(len(atlas) // tile_h):
            for tile_x in range(len(atlas[0]) // tile_w):
                ox, oy = tile_x * tile_w, tile_y * tile_h
                opaque = [(x, y) for y in range(tile_h) for x in range(tile_w) if atlas[oy + y][ox + x][3]]
                if not opaque:
                    continue
                ys = [y for _, y in opaque]
                ymin, ymax = min(ys), max(ys)
                target = round(ymin + (0.58 if mode == "single_stripe" else 0.80) * (ymax - ymin))
                for x, y in opaque:
                    if abs(y - target) <= (0 if mode == "single_stripe" else 1):
                        atlas[oy + y][ox + x] = accent
                        changed += 1
    metrics = dict(base.sleeve_metrics)
    metrics.update({"v5dDecoration": mode, "v5dDecoratedCells": changed})
    return atlas, metrics


def render_fs_v5d(recipe: dict[str, Any]) -> FSV5DRender:
    result = validate_v5d_recipe(recipe)
    if not result.valid:
        raise ValueError("invalid V5D recipe: " + "; ".join(result.errors))
    base = render_fs_v5b(recipe["baseUpperRecipe"])
    frames = {direction: [list(row) for row in base.frames[direction]] for direction in DIRECTION_ORDER}
    defaults = {direction: [list(row) for row in base.default_frames[direction]] for direction in DIRECTION_ORDER}
    signals = _signals()
    removed = {direction: set() for direction in DIRECTION_ORDER}
    _reset_v3_surface(base, frames, defaults)
    _shape(recipe, frames, defaults, signals, removed)
    ROLE_RENDERERS[recipe["articleRole"]](base, frames, defaults, signals)
    coverage = _coverage_missing(base, frames, allow_sleeve_exposure=False)
    if any(coverage.values()):
        raise ValueError(f"V5D body coverage failed: {coverage}")
    sleeves, sleeve_metrics = _decorate_sleeves(base, recipe)
    idle = _idle_frames(sleeves, base.sleeves_json) if sleeves is not None else None
    return FSV5DRender(
        recipe=recipe,
        base=base,
        frames=frames,
        default_frames=defaults,
        texture=_stack(frames),
        signal_cells=_freeze(signals),
        removed_cells={direction: frozenset(cells) for direction, cells in removed.items()},
        coverage_missing=coverage,
        sleeve_colors=base.sleeve_colors,
        hide_native_sleeves=False,
        companion_required=base.companion_required,
        sleeves_texture=sleeves,
        sleeves_json=base.sleeves_json,
        sleeve_idle_frames=idle,
        sleeve_metrics=sleeve_metrics,
    )
