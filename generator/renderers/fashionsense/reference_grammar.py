"""Controlled reference-derived garment renderer.

This bounded renderer implements only the twelve grammars authorized for the
first grammar/palette proof. It emits direct 16x16 logical Shirt frames and
uses the proven native Farmer sleeve contract. It is intentionally separate
from production generation and contains no rarity behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from generator.controlled_test.engine import validate_controlled_test_recipes
from generator.png_utils import RGBA, TRANSPARENT, blank_image


DIRECTIONS = ("front", "right", "left", "back")
SYSTEMS = ("silhouette", "collar", "opening", "layering", "hem", "panels", "pockets", "trim", "highlight")
FINAL_ART_ELIGIBLE = False
RENDER_STATUS = "STRUCTURE_DEBUG_ONLY"


@dataclass(frozen=True)
class ControlledGarmentRender:
    recipe: dict[str, Any]
    role_frames: dict[str, list[list[str | None]]]
    frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    signal_cells: dict[str, dict[str, frozenset[tuple[int, int]]]]
    active_roles: tuple[str, ...]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    material_behavior_id: str


def _empty_roles() -> dict[str, list[list[str | None]]]:
    return {direction: [[None for _ in range(16)] for _ in range(16)] for direction in DIRECTIONS}


def _signals() -> dict[str, dict[str, set[tuple[int, int]]]]:
    return {system: {direction: set() for direction in DIRECTIONS} for system in SYSTEMS}


def _row_range(direction: str, silhouette: str, y: int) -> tuple[int, int] | None:
    if direction == "front":
        top = {0: (2, 13), 1: (0, 15), 2: (0, 15)}
    elif direction == "back":
        top = {0: (2, 13), 1: (0, 15), 2: (0, 15)}
    elif direction == "right":
        top = {0: (2, 11), 1: (0, 11), 2: (0, 13)}
    else:
        top = {0: (4, 13), 1: (4, 15), 2: (2, 15)}
    if y in top:
        return top[y]
    models: dict[str, list[tuple[int, int] | None]] = {
        "fitted": [(1, 14)] * 7 + [(2, 13)] * 4 + [(3, 12), None, None],
        "regular": [(1, 14)] * 10 + [(2, 13)] * 2 + [None, None],
        "soft": [(0, 15)] * 8 + [(1, 14)] * 2 + [(2, 13), (2, 13), None, None],
        "boxy": [(0, 15)] * 10 + [(1, 14), (1, 14), None, None],
        "vest": [(2, 13)] * 8 + [(3, 12)] * 3 + [(4, 11), None, None],
        "waistcoat": [(2, 13)] * 8 + [(3, 12)] * 3 + [(4, 11), (5, 10), None],
        "cropped_round": [(0, 15)] * 7 + [(1, 14), (1, 14), (2, 13), None, None, None, None],
        "tunic": [(1, 14)] * 8 + [(0, 15)] * 2 + [(1, 14), (1, 14), (2, 13)],
    }
    index = y - 3
    if not 0 <= index < len(models[silhouette]):
        return None
    bounds = models[silhouette][index]
    if bounds is None:
        return None
    left, right = bounds
    if direction == "right":
        return max(0, left - 1), max(0, right - 1)
    if direction == "left":
        return min(15, left + 1), min(15, right + 1)
    return bounds


def _base_shape(roles, signals, silhouette: str) -> None:
    for direction in DIRECTIONS:
        for y in range(16):
            bounds = _row_range(direction, silhouette, y)
            if bounds is None:
                continue
            for x in range(bounds[0], bounds[1] + 1):
                roles[direction][y][x] = "PrimaryFabric"
                signals["silhouette"][direction].add((x, y))


def _put(roles, signals, direction: str, x: int, y: int, role: str, system: str) -> None:
    if 0 <= x < 16 and 0 <= y < 16 and roles[direction][y][x] is not None:
        roles[direction][y][x] = role
        signals[system][direction].add((x, y))


def _line(roles, signals, direction: str, coords, role: str, system: str) -> None:
    for x, y in coords:
        _put(roles, signals, direction, x, y, role, system)


def _fill(roles, signals, direction: str, x0: int, x1: int, y0: int, y1: int, role: str, system: str) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            _put(roles, signals, direction, x, y, role, system)


def _side_pair(roles, signals, coords, role: str, system: str) -> None:
    _line(roles, signals, "right", coords, role, system)
    _line(roles, signals, "left", ((15 - x, y) for x, y in coords), role, system)


def _row_bounds(frame: list[list[str | None]], y: int) -> tuple[int, int] | None:
    xs = [x for x, role in enumerate(frame[y]) if role is not None]
    return None if not xs else (min(xs), max(xs))


def _selective_finish(recipe, roles, signals) -> None:
    material = recipe["materialId"]
    soft = material in {"KNIT", "SWEATSHIRT", "CARDIGAN"}
    crisp = material in {"WOVEN_SHIRT", "DENIM_WORKWEAR", "BOMBER_OUTERWEAR", "BLAZER_FORMAL"}
    for direction in DIRECTIONS:
        frame = roles[direction]
        occupied_rows = [y for y in range(16) if any(frame[y])]
        if not occupied_rows:
            continue
        bottom = max(occupied_rows)
        anchor_rows = (1, 3, 11, bottom) if soft else (1, 3, 7, 11, bottom)
        for y in anchor_rows:
            bounds = _row_bounds(frame, y)
            if not bounds:
                continue
            left, right = bounds
            if y in ({3, 11} if soft else {3, 7, 11}):
                _put(roles, signals, direction, right, y, "StructuralDark", "silhouette")
            if y in {1, bottom}:
                _put(roles, signals, direction, left, y, "StructuralDark", "silhouette")
                _put(roles, signals, direction, right, y, "DeepShadow", "silhouette")
        bounds = _row_bounds(frame, 0)
        if bounds:
            highlight_span = 2 if soft else 3 if crisp else 2
            for x in range(bounds[0] + 1, min(bounds[0] + 1 + highlight_span, bounds[1] + 1)):
                _put(roles, signals, direction, x, 0, "PrimaryFabricLight", "highlight")


def _fitted_tee(roles, signals) -> None:
    _base_shape(roles, signals, "fitted")
    _line(roles, signals, "front", ((6, 0), (7, 1), (8, 1), (9, 0)), "StructuralDark", "collar")
    _line(roles, signals, "back", ((6, 0), (7, 1), (8, 1), (9, 0)), "StructuralDark", "collar")
    _side_pair(roles, signals, ((6, 0), (7, 1), (8, 1)), "StructuralDark", "collar")
    _line(roles, signals, "front", ((4, 4), (5, 4), (4, 5), (5, 5)), "Accent", "panels")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 14)
        if bounds:
            _line(roles, signals, direction, ((bounds[0], 14), (bounds[1], 14)), "StructuralDark", "hem")


def _open_casual_shirt(roles, signals) -> None:
    _base_shape(roles, signals, "regular")
    _fill(roles, signals, "front", 6, 9, 2, 12, "SecondaryFabric", "layering")
    _line(roles, signals, "front", ((5, y) for y in range(3, 13)), "StructuralDark", "opening")
    _line(roles, signals, "front", ((10, y) for y in range(3, 13)), "StructuralDark", "opening")
    _line(roles, signals, "front", ((3, 0), (4, 1), (5, 2), (12, 0), (11, 1), (10, 2)), "PrimaryFabricLight", "collar")
    _line(roles, signals, "front", ((3, 7), (4, 7), (5, 7), (3, 8), (5, 8)), "StructuralDark", "pockets")
    _line(roles, signals, "back", ((3, 3), (4, 3), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 3), (12, 3)), "StructuralDark", "panels")
    _side_pair(roles, signals, ((7, 1), (8, 2), (9, 3), (9, 4)), "PrimaryFabricLight", "collar")
    _side_pair(roles, signals, ((8, y) for y in range(5, 12)), "SecondaryFabric", "layering")
    _side_pair(roles, signals, ((9, y) for y in range(5, 12)), "StructuralDark", "opening")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 14)
        if bounds:
            _line(roles, signals, direction, ((bounds[0], 14), (bounds[1], 14)), "StructuralDark", "hem")


def _open_cardigan(roles, signals) -> None:
    _base_shape(roles, signals, "soft")
    # The soft neckline is still a structural carrier: it is deliberately
    # shallower than a shirt collar, but must survive the front composite.
    _line(roles, signals, "front", ((5, 0), (6, 1), (7, 2), (8, 2), (9, 1), (10, 0)), "Trim", "collar")
    for y in range(2, 13):
        spread = 2 if y >= 5 else 1
        _fill(roles, signals, "front", 8 - spread, 7 + spread, y, y, "SecondaryFabric", "layering")
        _put(roles, signals, "front", 7 - spread, y, "Trim", "opening")
        _put(roles, signals, "front", 8 + spread, y, "Trim", "opening")
    _fill(roles, signals, "front", 3, 5, 10, 12, "PrimaryFabricLight", "pockets")
    _fill(roles, signals, "front", 10, 12, 10, 12, "PrimaryFabricLight", "pockets")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 14)
        if bounds:
            _line(roles, signals, direction, ((x, 14) for x in range(bounds[0], bounds[1] + 1)), "Trim", "hem")
    _line(roles, signals, "back", ((5, 1), (6, 1), (7, 2), (8, 2), (9, 1), (10, 1)), "Trim", "collar")
    _side_pair(roles, signals, ((8, 2), (9, 3), (9, 4), (9, 5), (9, 6), (9, 7), (9, 8), (9, 9), (9, 10), (9, 11)), "Trim", "opening")


def _sweater_vest(roles, signals) -> None:
    _base_shape(roles, signals, "vest")
    for direction in DIRECTIONS:
        for y in range(0, 8):
            bounds = _row_bounds(roles[direction], y)
            if not bounds:
                continue
            for x in range(bounds[0], min(bounds[0] + 3, bounds[1] + 1)):
                _put(roles, signals, direction, x, y, "SecondaryFabric", "layering")
            for x in range(max(bounds[1] - 2, bounds[0]), bounds[1] + 1):
                _put(roles, signals, direction, x, y, "SecondaryFabric", "layering")
    _line(roles, signals, "front", ((5, 0), (6, 1), (7, 2), (8, 3), (9, 2), (10, 1), (11, 0)), "Trim", "collar")
    _fill(roles, signals, "front", 7, 8, 0, 2, "SecondaryFabric", "layering")
    _line(roles, signals, "back", ((5, 0), (6, 1), (7, 1), (8, 1), (9, 1), (10, 0)), "Trim", "collar")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 13)
        if bounds:
            _line(roles, signals, direction, ((x, 13) for x in range(bounds[0], bounds[1] + 1)), "Trim", "hem")
    _side_pair(roles, signals, ((3, 3), (3, 4), (4, 5), (4, 6)), "StructuralDark", "panels")


def _formal_waistcoat(roles, signals) -> None:
    _base_shape(roles, signals, "waistcoat")
    for direction in DIRECTIONS:
        for y in range(0, 7):
            bounds = _row_bounds(roles[direction], y)
            if bounds:
                _fill(roles, signals, direction, bounds[0], min(bounds[0] + 2, bounds[1]), y, y, "SecondaryFabric", "layering")
                _fill(roles, signals, direction, max(bounds[1] - 2, bounds[0]), bounds[1], y, y, "SecondaryFabric", "layering")
    _line(roles, signals, "front", ((4, 0), (5, 1), (6, 2), (7, 3), (8, 3), (9, 2), (10, 1), (11, 0)), "DeepShadow", "collar")
    _fill(roles, signals, "front", 6, 9, 0, 2, "SecondaryFabric", "layering")
    _line(roles, signals, "front", ((7, y) for y in range(4, 12)), "StructuralDark", "opening")
    _line(roles, signals, "front", ((8, 6), (8, 8), (8, 10)), "OptionalMetal", "trim")
    _line(roles, signals, "front", ((3, 10), (4, 10), (5, 10), (10, 10), (11, 10), (12, 10)), "StructuralDark", "pockets")
    _line(roles, signals, "front", ((4, 14), (5, 14), (6, 15), (9, 15), (10, 14), (11, 14)), "StructuralDark", "hem")
    _line(roles, signals, "back", ((4, 7), (5, 7), (6, 7), (7, 8), (8, 8), (9, 7), (10, 7), (11, 7)), "Trim", "panels")
    _side_pair(roles, signals, ((4, 4), (4, 6), (5, 8), (5, 10), (6, 12)), "StructuralDark", "panels")


def _crewneck_sweatshirt(roles, signals) -> None:
    _base_shape(roles, signals, "boxy")
    for direction in DIRECTIONS:
        _line(roles, signals, direction, ((6, 0), (7, 1), (8, 1), (9, 0)), "Trim", "collar")
        bounds = _row_bounds(roles[direction], 14)
        if bounds:
            _line(roles, signals, direction, ((x, 14) for x in range(bounds[0], bounds[1] + 1)), "Trim", "hem")
    _line(roles, signals, "front", ((4, 4), (5, 3), (6, 3), (7, 4), (8, 4), (9, 3), (10, 3), (11, 4)), "PrimaryFabricLight", "panels")


def _cropped_bomber(roles, signals) -> None:
    _base_shape(roles, signals, "cropped_round")
    for direction in DIRECTIONS:
        _line(roles, signals, direction, ((6, 0), (7, 1), (8, 1), (9, 0)), "Trim", "collar")
        bounds = _row_bounds(roles[direction], 12)
        if bounds:
            _line(roles, signals, direction, ((x, 12) for x in range(bounds[0], bounds[1] + 1)), "Trim", "hem")
    _fill(roles, signals, "front", 1, 4, 2, 6, "SecondaryFabric", "panels")
    _fill(roles, signals, "front", 11, 14, 2, 6, "SecondaryFabric", "panels")
    _line(roles, signals, "front", ((7, y) for y in range(2, 12)), "StructuralDark", "opening")
    _line(roles, signals, "front", ((8, 4),), "Accent", "trim")
    _line(roles, signals, "front", ((3, 8), (4, 7), (11, 7), (12, 8)), "StructuralDark", "pockets")
    _line(roles, signals, "back", ((3, 4), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 3), (12, 4)), "SecondaryFabric", "panels")
    _side_pair(roles, signals, ((3, 2), (4, 2), (5, 3), (6, 3), (7, 3)), "SecondaryFabric", "panels")
    _side_pair(roles, signals, ((8, 7), (9, 8), (10, 8)), "StructuralDark", "pockets")


def _work_jacket(roles, signals) -> None:
    _base_shape(roles, signals, "boxy")
    _line(roles, signals, "front", ((3, 0), (4, 1), (5, 2), (12, 0), (11, 1), (10, 2)), "SecondaryFabric", "collar")
    _line(roles, signals, "front", ((7, y) for y in range(2, 14)), "StructuralDark", "opening")
    _line(roles, signals, "front", ((8, 5), (8, 8), (8, 11)), "Accent", "trim")
    _fill(roles, signals, "front", 2, 5, 7, 11, "SecondaryFabric", "pockets")
    _fill(roles, signals, "front", 10, 13, 7, 11, "SecondaryFabric", "pockets")
    _line(roles, signals, "front", ((2, 7), (3, 7), (4, 7), (5, 7), (10, 7), (11, 7), (12, 7), (13, 7)), "StructuralDark", "pockets")
    _line(roles, signals, "back", ((2, 3), (3, 3), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 4), (12, 3), (13, 3)), "StructuralDark", "panels")
    _side_pair(roles, signals, ((3, 1), (4, 2), (5, 3)), "StructuralDark", "panels")
    _side_pair(roles, signals, ((6, 7), (7, 7), (8, 7), (9, 7)), "StructuralDark", "pockets")
    _side_pair(roles, signals, ((6, 8), (7, 8), (8, 8), (9, 8), (6, 9), (7, 9), (8, 9), (9, 9)), "SecondaryFabric", "pockets")
    _side_pair(roles, signals, ((9, 10), (9, 11), (9, 12)), "StructuralDark", "panels")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 14)
        if bounds:
            _line(roles, signals, direction, ((x, 14) for x in range(bounds[0], bounds[1] + 1)), "StructuralDark", "hem")


def _fitted_blazer(roles, signals) -> None:
    _base_shape(roles, signals, "fitted")
    _fill(roles, signals, "front", 6, 9, 1, 8, "SecondaryFabric", "layering")
    _line(roles, signals, "front", ((3, 0), (4, 1), (5, 2), (6, 3), (7, 4), (12, 0), (11, 1), (10, 2), (9, 3), (8, 4)), "PrimaryFabricLight", "collar")
    _line(roles, signals, "front", ((5, 3), (6, 4), (7, 5), (10, 3), (9, 4), (8, 5)), "StructuralDark", "opening")
    _line(roles, signals, "front", ((7, 8), (8, 10)), "OptionalMetal", "trim")
    _line(roles, signals, "front", ((3, 10), (4, 10), (5, 10), (10, 10), (11, 10), (12, 10)), "StructuralDark", "pockets")
    _line(roles, signals, "back", ((5, 0), (6, 1), (7, 2), (8, 2), (9, 1), (10, 0)), "PrimaryFabricLight", "collar")
    _line(roles, signals, "back", ((7, y) for y in range(3, 13)), "StructuralDark", "panels")
    _line(roles, signals, "back", ((7, 13), (8, 13), (7, 14), (8, 14)), "DeepShadow", "hem")
    _side_pair(roles, signals, ((5, 0), (6, 1), (7, 2), (8, 3), (8, 4)), "PrimaryFabricLight", "collar")
    _side_pair(roles, signals, ((8, 4), (9, 5), (9, 6)), "StructuralDark", "opening")
    _side_pair(roles, signals, ((5, 10), (6, 10), (7, 10)), "StructuralDark", "pockets")
    _side_pair(roles, signals, ((8, 12), (9, 12), (9, 13)), "PrimaryFabricLight", "panels")
    _line(roles, signals, "front", ((3, 14), (4, 14), (5, 14), (10, 14), (11, 14), (12, 14)), "StructuralDark", "hem")


def _wrap_top(roles, signals) -> None:
    _base_shape(roles, signals, "fitted")
    for y in range(1, 11):
        start = max(3, 11 - y // 2)
        _fill(roles, signals, "front", start, 12, y, y, "SecondaryFabric", "layering")
        _put(roles, signals, "front", start, y, "StructuralDark", "opening")
    _line(roles, signals, "front", ((4, 0), (5, 1), (6, 2), (7, 3), (8, 3), (9, 2), (10, 1), (11, 0)), "DeepShadow", "collar")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 11)
        if bounds:
            _line(roles, signals, direction, ((x, 11) for x in range(bounds[0], bounds[1] + 1)), "Trim", "hem")
    _line(roles, signals, "right", ((5, 2), (6, 3), (7, 4), (8, 5), (9, 6), (9, 7)), "StructuralDark", "opening")
    _fill(roles, signals, "right", 8, 11, 4, 8, "SecondaryFabric", "layering")
    _line(roles, signals, "left", ((5, 2), (6, 3), (6, 4)), "Trim", "panels")
    _line(roles, signals, "back", ((3, 3), (4, 3), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 3), (12, 3)), "PrimaryFabricLight", "panels")


def _sailor_top(roles, signals) -> None:
    _base_shape(roles, signals, "regular")
    _line(roles, signals, "front", ((2, 0), (3, 1), (4, 2), (5, 3), (6, 4), (7, 5), (8, 5), (9, 4), (10, 3), (11, 2), (12, 1), (13, 0)), "SecondaryFabric", "collar")
    _fill(roles, signals, "front", 7, 8, 1, 4, "SecondaryFabric", "layering")
    _line(roles, signals, "front", ((7, 5), (8, 5), (7, 6), (8, 6)), "Accent", "trim")
    _fill(roles, signals, "back", 3, 12, 1, 5, "SecondaryFabric", "collar")
    _line(roles, signals, "back", ((3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5)), "Trim", "collar")
    _side_pair(roles, signals, ((3, 0), (4, 1), (5, 2), (6, 3), (7, 4), (8, 4)), "SecondaryFabric", "collar")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 14)
        if bounds:
            _line(roles, signals, direction, ((x, 14) for x in range(bounds[0] + 1, bounds[1])), "Trim", "hem")


def _belted_tunic(roles, signals) -> None:
    _base_shape(roles, signals, "tunic")
    _line(roles, signals, "front", ((6, 0), (7, 1), (7, 2), (8, 2), (8, 1), (9, 0)), "DeepShadow", "collar")
    for direction in DIRECTIONS:
        bounds = _row_bounds(roles[direction], 10)
        if bounds:
            _line(roles, signals, direction, ((x, 10) for x in range(bounds[0], bounds[1] + 1)), "SecondaryFabric", "hem")
            _line(roles, signals, direction, ((x, 11) for x in range(bounds[0] + 1, bounds[1])), "Trim", "hem")
    _line(roles, signals, "front", ((7, 12), (8, 12), (7, 13), (8, 13), (7, 14), (8, 14), (7, 15), (8, 15)), "StructuralDark", "hem")
    _line(roles, signals, "back", ((3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 4), (12, 4)), "PrimaryFabricLight", "panels")
    # Side waist break and cloth fall are the side-view carriers; this is not
    # a front belt pasted sideways.
    _side_pair(roles, signals, ((4, 9), (5, 9), (6, 9), (7, 9), (8, 9), (9, 9)), "SecondaryFabric", "panels")
    _side_pair(roles, signals, ((3, 12), (3, 13), (3, 14)), "StructuralDark", "hem")


AUTHORS: dict[str, Callable[[dict, dict], None]] = {
    "FITTED_TEE": _fitted_tee,
    "OPEN_CASUAL_SHIRT": _open_casual_shirt,
    "OPEN_CARDIGAN": _open_cardigan,
    "SWEATER_VEST": _sweater_vest,
    "FORMAL_WAISTCOAT": _formal_waistcoat,
    "CREWNECK_SWEATSHIRT": _crewneck_sweatshirt,
    "CROPPED_BOMBER": _cropped_bomber,
    "WORK_JACKET": _work_jacket,
    "FITTED_BLAZER": _fitted_blazer,
    "WRAP_TOP": _wrap_top,
    "SAILOR_TOP": _sailor_top,
    "BELTED_TUNIC": _belted_tunic,
}


def _rgba(value: str) -> RGBA:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255


def _resolve_role(story: dict[str, Any], role: str) -> str:
    available = story["roles"]
    fallbacks = {
        "OptionalMetal": ("Accent", "Trim", "StructuralDark"),
        "OptionalMotif": ("Accent", "Trim", "PrimaryFabricLight"),
        "SecondaryFabricLight": ("SecondaryFabric", "PrimaryFabricLight"),
        "Trim": ("StructuralDark",),
        "Accent": ("Trim", "PrimaryFabricLight"),
    }
    if role in available:
        return role
    for candidate in fallbacks.get(role, ("PrimaryFabric",)):
        if candidate in available:
            return candidate
    raise ValueError(f"palette story {story['id']} cannot resolve role {role}")


def _stack(frames: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    texture = blank_image(16, 64)
    for index, direction in enumerate(("front", "right", "left", "back")):
        for y, row in enumerate(frames[direction]):
            texture[index * 16 + y] = list(row)
    return texture


def _sleeve_ramp(recipe: dict[str, Any]) -> tuple[tuple[int, int, int], ...]:
    story = recipe["paletteStory"]
    fabric = recipe["nativeSleeveFabric"]
    light_role = "SecondaryFabricLight" if fabric == "SecondaryFabric" else "PrimaryFabricLight"
    choices = ("StructuralDark", fabric, _resolve_role(story, light_role))
    colors = [_rgba(story["roles"][_resolve_role(story, role)])[:3] for role in choices]
    # Fashion Sense expects a stable three-stop native sleeve ramp. Preserve
    # order while ensuring duplicate optional-role fallbacks remain distinct.
    if len(set(colors)) < 3:
        colors[-1] = _rgba(story["roles"][_resolve_role(story, "PrimaryFabricLight")])[:3]
    return tuple(colors)


def render_controlled_garment(recipe: dict[str, Any]) -> ControlledGarmentRender:
    errors = validate_controlled_test_recipes([recipe])
    # Single-recipe validation intentionally reports the collection-count and
    # allowlist-order checks. Filter those; all content checks remain binding.
    errors = tuple(error for error in errors if not error.startswith("expected exactly") and not error.startswith("grammar selection/order"))
    if errors:
        raise ValueError("invalid controlled recipe: " + "; ".join(errors))
    if recipe["grammarId"] not in AUTHORS:
        raise ValueError(f"unsupported controlled grammar {recipe['grammarId']}")
    roles = _empty_roles()
    signals = _signals()
    AUTHORS[recipe["grammarId"]](roles, signals)
    _selective_finish(recipe, roles, signals)
    story = recipe["paletteStory"]
    frames: dict[str, list[list[RGBA]]] = {}
    active: set[str] = set()
    for direction in DIRECTIONS:
        frame = blank_image(16, 16)
        for y in range(16):
            for x in range(16):
                role = roles[direction][y][x]
                if role is None:
                    continue
                resolved = _resolve_role(story, role)
                active.add(resolved)
                frame[y][x] = _rgba(story["roles"][resolved])
        frames[direction] = frame
    return ControlledGarmentRender(
        recipe=recipe,
        role_frames=roles,
        frames=frames,
        texture=_stack(frames),
        signal_cells={system: {direction: frozenset(cells) for direction, cells in views.items()} for system, views in signals.items()},
        active_roles=tuple(sorted(active)),
        sleeve_colors=_sleeve_ramp(recipe),
        material_behavior_id=recipe["materialId"],
    )
