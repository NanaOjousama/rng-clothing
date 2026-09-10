"""Bounded unified-garment Fashion Sense renderer for Generator V5A.

The frozen V3 renderer supplies upper construction, palette, surface design,
coverage, and shading. This adapter reconstructs the waist and bounded lower
silhouette on a taller logical Shirt frame. The extended hem remains attached
to the torso layer; no leg articulation is claimed.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA, TRANSPARENT, blank_image
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.surface_v3 import FSV3SurfaceRender, render_fs_v3
from generator.v2_recipe_engine import load_v2_data
from generator.v3.engine import load_v3_data
from generator.v5a.engine import load_v5a_data, validate_v5a_recipe


ROOT = Path(__file__).resolve().parents[3]
GRAMMAR = ROOT / "generator" / "data" / "fashionsense" / "v5a_unified_grammar.json"


@dataclass(frozen=True)
class FSV5AUnifiedRender:
    recipe: dict[str, Any]
    design: FSV3SurfaceRender
    frame_height: int
    transition_y: int
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    regions: dict[str, list[list[str | None]]]
    texture: list[list[RGBA]]
    article_cells: dict[str, frozenset[tuple[int, int]]]
    extension_cells: dict[str, frozenset[tuple[int, int]]]
    surface_cells: dict[str, dict[str, frozenset[tuple[int, int]]]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    hide_sleeves: bool
    active_mask_values: tuple[int, ...]


def load_v5a_fs_grammar() -> dict[str, Any]:
    return json.loads(GRAMMAR.read_text(encoding="utf-8"))


def _stack(frames: dict[str, list[list[RGBA]]], height: int) -> list[list[RGBA]]:
    texture = blank_image(16, height * 4)
    for index, direction in enumerate(DIRECTION_ORDER):
        for y, row in enumerate(frames[direction]):
            texture[index * height + y] = list(row)
    return texture


def _mirror_cells(cells: dict[tuple[int, int], str]) -> dict[tuple[int, int], str]:
    swaps = {"OUTER_PANEL_LEFT": "OUTER_PANEL_RIGHT", "OUTER_PANEL_RIGHT": "OUTER_PANEL_LEFT"}
    return {(15 - x, y): swaps.get(region, region) for (x, y), region in cells.items()}


def _fill(cells: dict[tuple[int, int], str], left: int, right: int, y: int, region: str) -> None:
    for x in range(max(0, left), min(15, right) + 1):
        cells[(x, y)] = region


def _dress_cells(direction: str, intent: dict[str, str], height: int, start: int) -> dict[tuple[int, int], str]:
    if direction == "left":
        return _mirror_cells(_dress_cells("right", intent, height, start))
    cells: dict[tuple[int, int], str] = {}
    silhouette = intent["silhouette"]
    for y in range(start, height):
        i = y - start
        if direction == "right":
            expansion = min(2, max(0, (i - 1) // 4))
            left, right = 6 - expansion, 10 + expansion
        else:
            if silhouette in {"fitted", "straight"}:
                expansion = 0
            elif silhouette in {"a_line", "pinafore", "structured"}:
                expansion = min(2, max(0, (i - 1) // 3))
            else:
                expansion = min(3, max(0, (i - 1) // 2))
            left, right = 4 - expansion, 11 + expansion
        region = "WAIST" if i <= (1 if intent["waist"] in {"high", "belted"} else 0) else "DRESS_LOWER"
        if y >= height - (2 if intent["hem"] == "layered" else 1):
            region = "HEM"
        _fill(cells, left, right, y, region)
        if region == "DRESS_LOWER" and direction in {"front", "back"} and silhouette in {"soft_flare", "pinafore"}:
            cells[(7, y)] = "FOLD"
            if silhouette == "soft_flare" and i % 2 == 0:
                cells[(10, y)] = "FOLD"
    return cells


def _one_piece_cells(direction: str, intent: dict[str, str], height: int, start: int) -> dict[tuple[int, int], str]:
    if direction == "left":
        return _mirror_cells(_one_piece_cells("right", intent, height, start))
    cells: dict[tuple[int, int], str] = {}
    form = intent["lowerForm"]
    for y in range(start, height):
        i = y - start
        if direction == "right":
            expansion = 1 if i >= 5 else 0
            if form == "work_apron":
                left, right = 5, 11
            elif form == "uniform_panel":
                left, right = 6 - expansion, 10 + expansion
            else:
                left, right = 5 - expansion, 11 + expansion
        elif form == "work_apron":
            left, right = (3, 12) if i <= 1 else (4, 11)
        elif form == "uniform_panel":
            expansion = 1 if i >= 5 else 0
            left, right = 4 - expansion, 11 + expansion
        else:
            expansion = min(2, max(0, (i - 1) // 4))
            left, right = 4 - expansion, 11 + expansion
        belt_depth = 1 if intent["waist"] == "sashed" else 0
        region = "BELT" if i <= belt_depth else "LOWER_PANEL"
        if y >= height - (2 if intent["hem"] == "layered" else 1):
            region = "HEM"
        _fill(cells, left, right, y, region)
        if direction in {"front", "back"} and i >= 2:
            cells[(7, y)] = "CENTER_SEAM"
            if form == "split_tabard":
                cells[(8, y)] = "CENTER_SEAM"
        if form == "split_tabard" and y >= height - 2 and direction in {"front", "back"}:
            cells.pop((7, y), None)
            cells.pop((8, y), None)
        if form == "uniform_panel" and y == height - 1 and direction in {"front", "back"}:
            cells.pop((7, y), None)
            cells.pop((8, y), None)
        if form == "work_apron" and y == height - 1 and direction == "front":
            cells.pop((7, y), None)
            cells.pop((8, y), None)
    return cells


def _outerwear_cells(direction: str, intent: dict[str, str], height: int, start: int) -> dict[tuple[int, int], str]:
    if direction == "left":
        return _mirror_cells(_outerwear_cells("right", intent, height, start))
    cells: dict[tuple[int, int], str] = {}
    for y in range(start, height):
        expansion = 1 if y >= height - 3 and intent["construction"] != "cardigan" else 0
        if direction == "front":
            _fill(cells, 3 - expansion, 6, y, "OUTER_PANEL_LEFT")
            _fill(cells, 9, 12 + expansion, y, "OUTER_PANEL_RIGHT")
            if intent["front"] == "partially_open" and y < height - 2:
                _fill(cells, 7, 8, y, "INNER_LAYER")
        elif direction == "back":
            _fill(cells, 3 - expansion, 12 + expansion, y, "BACK_PANEL")
            if intent["hem"] in {"split", "layered"} and y >= height - 3:
                cells.pop((7, y), None)
                cells.pop((8, y), None)
        else:
            _fill(cells, 5 - expansion, 12 + expansion, y, "OUTER_PANEL_RIGHT")
            if intent["front"] != "closed" and y < height - 2:
                cells[(11, y)] = "INNER_LAYER"
        if y >= height - (2 if intent["hem"] == "layered" else 1):
            for point in [point for point in cells if point[1] == y and cells[point] != "INNER_LAYER"]:
                cells[point] = "EXTENDED_HEM"
        if intent["hem"] == "rounded" and y == height - 1:
            xs = sorted(x for x, py in cells if py == y)
            if len(xs) >= 4:
                cells.pop((xs[0], y), None)
                cells.pop((xs[-1], y), None)
    return cells


def _article_cells(recipe: dict[str, Any], height: int, start: int) -> dict[str, dict[tuple[int, int], str]]:
    builder = {"DRESS": _dress_cells, "ONE_PIECE": _one_piece_cells, "BOUNDED_LONG_OUTERWEAR": _outerwear_cells}[recipe["articleType"]]
    return {direction: builder(direction, recipe["articleIntent"], height, start) for direction in DIRECTION_ORDER}


def _role_for_cell(cells: dict[tuple[int, int], str], x: int, y: int, start: int, height: int) -> str:
    region = cells[(x, y)]
    exterior = any(point not in cells for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    if region == "CENTER_SEAM":
        return "DEEP_CREASE"
    if region == "FOLD":
        return "STRUCTURAL_EDGE"
    if exterior:
        if y == height - 1 or x >= 11:
            return "EXTERIOR_CONTOUR"
        if x <= 4 and y < height - 1:
            return "LIGHT"
        return "SHADOW"
    if y == start:
        return "LIGHT"
    if x >= 9:
        return "SHADOW"
    return "BASE"


def _mask_color(role: str, grammar: dict[str, Any]) -> RGBA:
    value = grammar["roleRamp"][role]
    return value, value, value, 255


def _default_color(role: str, design: FSV3SurfaceRender, grammar: dict[str, Any]) -> RGBA:
    value = grammar["roleRamp"][role]
    dye = load_v2_data()["palettes"]["families"][design.base.recipe["paletteFamily"]]["defaultDye"]
    return tuple(value * dye[index] // 255 for index in range(3)) + (255,)


def _story_color(design: FSV3SurfaceRender, key: str) -> RGBA:
    rgb = load_v3_data()["palettes"]["stories"][design.recipe["paletteStory"]][key]
    return rgb[0], rgb[1], rgb[2], 255


def _surface_candidates(target: str, regions: list[list[str | None]], start: int, height: int) -> list[tuple[int, int]]:
    named = {
        "waist": {"WAIST", "BELT"}, "hem": {"HEM"}, "extended_hem": {"EXTENDED_HEM"},
        "lower_mass": {"DRESS_LOWER"}, "lower_panels": {"LOWER_PANEL", "CENTER_SEAM"},
        "utility_region": {"LOWER_PANEL"}, "outer_panels": {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"},
        "back_panel": {"BACK_PANEL"},
    }
    if target not in named:
        return []
    return [(x, y) for y in range(start, height) for x in range(16) if regions[y][x] in named[target]]


def _apply_target(target: str, direction: str, frames, defaults, regions, design, start: int, height: int, primary: bool) -> set[tuple[int, int]]:
    upper_targets = {"bodice", "upper_torso", "collar", "lapel", "upper_back"}
    if target in upper_targets:
        points = set().union(*(design.system_cells[system][direction] for system in design.system_cells))
        if target == "upper_back" and direction != "back":
            return set()
        return {(x, y) for x, y in points if y < start}
    candidates = _surface_candidates(target, regions, start, height)
    chosen: set[tuple[int, int]] = set()
    if not candidates:
        return chosen
    color = _story_color(design, "accent" if primary else "secondary")
    if target == "waist":
        chosen = set(candidates)
    elif target in {"hem", "extended_hem"}:
        chosen = {(x, y) for x, y in candidates if (x + y) % (2 if primary else 3) == 0}
    elif target == "utility_region" and direction == "front":
        y0 = min(y for _, y in candidates) + 2
        chosen = {(x, y) for x, y in candidates if y in {y0, y0 + 1} and x in {4, 5, 10, 11}}
    elif target == "lower_panels":
        cadence_rows = {start + 3, start + 6, height - 3}
        chosen = {(x, y) for x, y in candidates if y in cadence_rows and x in {5, 10}}
        chosen |= {(x, y) for x, y in candidates if y == start + 3 and x in {7, 8}}
    elif target == "outer_panels":
        chosen = {(x, y) for x, y in candidates if x in {5, 10} and (y - start) % 2 == 1}
    elif target == "back_panel" and direction == "back":
        y0 = min(y for _, y in candidates) + 2
        chosen = {(7, y0), (8, y0), (6, y0 + 1), (9, y0 + 1), (7, y0 + 2), (8, y0 + 2)} & set(candidates)
    elif target == "lower_mass":
        chosen = {(x, y) for x, y in candidates if x in {7, 8} and (y - start) % 2 == 0}
    for x, y in chosen:
        frames[direction][y][x] = color
        defaults[direction][y][x] = color
    return chosen


def _remove_sleeve_cells(design: FSV3SurfaceRender, frames, defaults, regions) -> None:
    for direction in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                if design.base.regions[direction][y][x] == "SLEEVE":
                    frames[direction][y][x] = TRANSPARENT
                    defaults[direction][y][x] = TRANSPARENT
                    regions[direction][y][x] = None


def _sleeve_colors(design: FSV3SurfaceRender) -> tuple[tuple[int, int, int], ...]:
    ramp = design.base.config["outerMaskRamp"]
    return tuple((ramp[role], ramp[role], ramp[role]) for role in design.base.config["sleeveMaskRoles"][:3])


def render_fs_v5a(recipe: dict[str, Any]) -> FSV5AUnifiedRender:
    validation = validate_v5a_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid V5A recipe: " + "; ".join(validation.errors))
    grammar = load_v5a_fs_grammar()
    design = render_fs_v3(recipe["designRecipe"])
    article = recipe["articleType"]
    height = grammar["frameHeights"][article][recipe["articleIntent"]["length"]]
    start = grammar["transitionRows"][article]
    frames = {direction: blank_image(16, height) for direction in DIRECTION_ORDER}
    defaults = {direction: blank_image(16, height) for direction in DIRECTION_ORDER}
    regions = {direction: [[None for _ in range(16)] for _ in range(height)] for direction in DIRECTION_ORDER}
    for direction in DIRECTION_ORDER:
        for y in range(16):
            frames[direction][y] = list(design.frames[direction][y])
            defaults[direction][y] = list(design.default_frames[direction][y])
            regions[direction][y] = list(design.base.regions[direction][y])
        for y in range(start, 16):
            for x in range(16):
                if design.base.regions[direction][y][x] != "SLEEVE":
                    frames[direction][y][x] = TRANSPARENT
                    defaults[direction][y][x] = TRANSPARENT
                    regions[direction][y][x] = None
    article_regions = _article_cells(recipe, height, start)
    for direction, cells in article_regions.items():
        for (x, y), region in cells.items():
            role = _role_for_cell(cells, x, y, start, height)
            frames[direction][y][x] = _mask_color(role, grammar)
            defaults[direction][y][x] = _default_color(role, design, grammar)
            regions[direction][y][x] = region
    sleeve_info = load_v5a_data()["sleeves"]["sleeves"][recipe["sleeveIntent"]]
    hide_sleeves = bool(sleeve_info["hideSleeves"])
    if hide_sleeves:
        _remove_sleeve_cells(design, frames, defaults, regions)
    targets = [recipe["articleSurfacePlan"]["primaryTarget"], *recipe["articleSurfacePlan"]["supportTargets"]]
    surface_cells = {target: {direction: set() for direction in DIRECTION_ORDER} for target in targets}
    for index, target in enumerate(targets):
        for direction in DIRECTION_ORDER:
            surface_cells[target][direction] = _apply_target(target, direction, frames, defaults, regions[direction], design, start, height, index == 0)
    all_cells = {direction: frozenset((x, y) for y in range(height) for x in range(16) if frames[direction][y][x][3]) for direction in DIRECTION_ORDER}
    extensions = {direction: frozenset((x, y) for x, y in all_cells[direction] if y >= 16) for direction in DIRECTION_ORDER}
    frozen_surface = {target: {direction: frozenset(points) for direction, points in views.items()} for target, views in surface_cells.items()}
    mask_values = set(grammar["roleRamp"].values())
    values = sorted({pixel[0] for direction in DIRECTION_ORDER for row in frames[direction] for pixel in row if pixel[3] and pixel[0] == pixel[1] == pixel[2] and pixel[0] in mask_values})
    return FSV5AUnifiedRender(
        recipe=recipe, design=design, frame_height=height, transition_y=start,
        frames=frames, default_frames=defaults, regions=regions,
        texture=_stack(frames, height), article_cells=all_cells,
        extension_cells=extensions, surface_cells=frozen_surface,
        sleeve_colors=_sleeve_colors(design), hide_sleeves=hide_sleeves,
        active_mask_values=tuple(values),
    )


def connected_components(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    sizes: list[int] = []
    while remaining:
        queue = deque([remaining.pop()])
        size = 0
        while queue:
            x, y = queue.popleft()
            size += 1
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if point in remaining:
                    remaining.remove(point)
                    queue.append(point)
        sizes.append(size)
    return sorted(sizes, reverse=True)
