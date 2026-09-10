"""Permanent construction-first Fashion Sense high-detail shirt renderer.

This backend consumes unchanged V2 semantic recipes. All coordinates, edge
classification, directional reconstruction, and Fashion Sense runtime fields
belong to renderer data or renderer grammar.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA, blank_image
from generator.v2_recipe_engine import load_v2_data, validate_recipe_v2


ROOT = Path(__file__).resolve().parents[3]
GRAMMAR_PATH = ROOT / "generator" / "data" / "fashionsense" / "hd_garment_grammar_v2.json"
DIRECTION_ORDER = ("front", "right", "left", "back")
SUPPORTED_ARCHETYPES = frozenset({"JACKET", "BUTTON_SHIRT", "SAILOR_TOP", "SWEATER"})

MAIN_ROLES = frozenset({
    "EXTERIOR_CONTOUR",
    "DEEP_CREASE",
    "STRUCTURAL_EDGE",
    "SHADOW",
    "BASE",
    "LIGHT",
    "OPTIONAL_HIGHLIGHT",
})
SECONDARY_ROLES = frozenset({"SECONDARY_SHADOW", "SECONDARY_BASE", "SECONDARY_LIGHT"})
SECONDARY_REGION_GROUPS = {
    "none": frozenset(),
    "body": frozenset({"BODY"}),
    "collar": frozenset({"COLLAR", "NECKLINE"}),
    "yoke": frozenset({"YOKE", "COLLAR"}),
    "placket": frozenset({"PLACKET"}),
    "outer_panels": frozenset({"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}),
    "inner_layer": frozenset({"INNER_LAYER"}),
    "hem": frozenset({"HEM"}),
    "ribbing": frozenset({"RIBBING"}),
    "stripe": frozenset(),
}


@dataclass(frozen=True)
class FSPermanentGarmentRender:
    recipe: dict[str, Any]
    config: dict[str, Any]
    side_template: str
    regions: dict[str, list[list[str | None]]]
    edge_exposure: dict[str, list[list[str | None]]]
    gesture_hierarchy: dict[str, dict[str, tuple[str, ...]]]
    roles: dict[str, list[list[str | None]]]
    active_main_roles: tuple[str, ...]
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]


def load_hd_garment_grammar_v2() -> dict[str, Any]:
    return json.loads(GRAMMAR_PATH.read_text(encoding="utf-8"))


def _assert_supported(recipe: dict[str, Any]) -> None:
    validation = validate_recipe_v2(recipe, load_v2_data())
    if not validation.valid:
        raise ValueError("invalid V2 recipe: " + "; ".join(validation.errors))
    if recipe["archetype"] not in SUPPORTED_ARCHETYPES:
        raise ValueError(f"FS HD permanent backend does not support {recipe['archetype']}")


def _decode_rows(config: dict[str, Any], rows: list[str]) -> list[list[str | None]]:
    legend = config["regionLegend"]
    if len(rows) != 16 or any(len(row) != 16 for row in rows):
        raise ValueError("FS HD structural template must contain sixteen 16-cell rows")
    try:
        return [[legend[symbol] for symbol in row] for row in rows]
    except KeyError as exc:
        raise ValueError(f"unknown FS HD structural symbol {exc.args[0]!r}") from exc


def _compatible_side_templates(recipe: dict[str, Any], config: dict[str, Any]):
    templates = config["archetypes"][recipe["archetype"]]["sideTemplates"]
    panel_layout = recipe["construction"]["panelLayout"]
    specialized = [
        (name, model)
        for name, model in sorted(templates.items())
        if panel_layout in model.get("requiresPanelLayout", [])
    ]
    compatible = specialized or [
        (name, model)
        for name, model in sorted(templates.items())
        if "requiresPanelLayout" not in model
    ]
    if not compatible:
        raise ValueError(f"no compatible FS HD side template for {recipe['id']}")
    return compatible


def select_side_template(recipe: dict[str, Any], config: dict[str, Any]) -> str:
    compatible = _compatible_side_templates(recipe, config)
    stable = f"{recipe['seed']}|{recipe['id']}|{recipe['archetype']}|{recipe['construction']['panelLayout']}"
    index = int.from_bytes(hashlib.sha256(stable.encode()).digest()[:8], "big") % len(compatible)
    return compatible[index][0]


def _resolve_termination(region: str | None, recipe: dict[str, Any]) -> str | None:
    if region != "TERMINATION_SLOT":
        return region
    hem = recipe["construction"]["hem"]
    if hem == "ribbed":
        return "RIBBING"
    if hem in {"structured", "contrast_band"}:
        return "HEM"
    if recipe["archetype"] == "JACKET":
        return "HEM"
    return "BODY"


def _resolve_semantic_regions(
    frame: list[list[str | None]], recipe: dict[str, Any]
) -> list[list[str | None]]:
    resolved = [[_resolve_termination(region, recipe) for region in row] for row in frame]
    if (
        recipe["archetype"] != "JACKET"
        and recipe["construction"]["panelLayout"] != "yoke"
    ):
        resolved = [["BODY" if region == "YOKE" else region for region in row] for row in resolved]

    # Fitted garments taper only below the torso/sleeve junction. Coverage rows
    # and archetype-defining upper construction remain unchanged.
    if recipe["construction"]["fit"] == "fitted":
        for y in range(9, 15):
            occupied = [x for x, region in enumerate(resolved[y]) if region is not None]
            if len(occupied) < 12:
                continue
            for x in (min(occupied), max(occupied)):
                if resolved[y][x] in {"BODY", "HEM"}:
                    resolved[y][x] = None
    return resolved


def _mirror(frame: list[list[str | None]]) -> list[list[str | None]]:
    swaps = {
        "OUTER_PANEL_LEFT": "OUTER_PANEL_RIGHT",
        "OUTER_PANEL_RIGHT": "OUTER_PANEL_LEFT",
    }
    return [[swaps.get(region, region) for region in reversed(row)] for row in frame]


def build_hd_regions(
    recipe: dict[str, Any], config: dict[str, Any]
) -> tuple[dict[str, list[list[str | None]]], str]:
    model = config["archetypes"][recipe["archetype"]]
    side_name = select_side_template(recipe, config)
    side_rows = model["sideTemplates"][side_name]["rows"]
    front = _resolve_semantic_regions(_decode_rows(config, model["front"]), recipe)
    back = _resolve_semantic_regions(_decode_rows(config, model["back"]), recipe)
    right = _resolve_semantic_regions(_decode_rows(config, side_rows), recipe)
    return {"front": front, "right": right, "left": _mirror(right), "back": back}, side_name


def _neighbors(x: int, y: int):
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 <= nx < 16 and 0 <= ny < 16:
            yield nx, ny
        else:
            yield None


def _is_exterior(frame: list[list[str | None]], x: int, y: int) -> bool:
    return any(
        neighbor is None or frame[neighbor[1]][neighbor[0]] is None
        for neighbor in _neighbors(x, y)
    )


def _row_bounds(frame: list[list[str | None]], y: int) -> tuple[int, int] | None:
    occupied = [x for x, region in enumerate(frame[y]) if region is not None]
    return None if not occupied else (min(occupied), max(occupied))


def _adjacent_regions(frame: list[list[str | None]], x: int, y: int) -> set[str]:
    return {
        frame[ny][nx]
        for neighbor in _neighbors(x, y)
        if neighbor is not None
        for nx, ny in (neighbor,)
        if frame[ny][nx] is not None and frame[ny][nx] != frame[y][x]
    }


def classify_edge_exposure(
    regions: dict[str, list[list[str | None]]]
) -> dict[str, list[list[str | None]]]:
    result: dict[str, list[list[str | None]]] = {}
    for direction, frame in regions.items():
        classified: list[list[str | None]] = [[None for _ in range(16)] for _ in range(16)]
        for y, row in enumerate(frame):
            bounds = _row_bounds(frame, y)
            for x, region in enumerate(row):
                if region is None:
                    continue
                adjacent = _adjacent_regions(frame, x, y)
                exterior = _is_exterior(frame, x, y)
                central_recess = exterior and y <= 3 and 5 <= x <= 10
                if central_recess and region in {"COLLAR", "NECKLINE", "INNER_LAYER", "PLACKET", "YOKE"}:
                    classified[y][x] = "neck_anchor"
                elif {"INNER_LAYER", "PLACKET"} & adjacent and region in {
                    "OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT", "COLLAR", "BODY"
                }:
                    classified[y][x] = "overlap_anchor"
                elif exterior and y >= 14 and bounds and x in {bounds[0], bounds[1]}:
                    classified[y][x] = "hem_corner_anchor"
                elif exterior and region == "SLEEVE" and 3 <= y <= 7:
                    classified[y][x] = "underarm_anchor"
                elif exterior and bounds and x in {bounds[0], bounds[1]} and y >= 5:
                    classified[y][x] = "outer_side_anchor"
                elif exterior and y <= 3 and x <= 7:
                    classified[y][x] = "lit_edge"
                elif exterior:
                    classified[y][x] = "shadow_edge"
        result[direction] = classified
    return result


def _coverage_envelope(config: dict[str, Any], direction: str) -> list[str]:
    source = "right" if direction == "left" else direction
    rows = config["bodyCoverageEnvelope"][source]
    return [row[::-1] for row in rows] if direction == "left" else rows


def validate_hd_coverage(
    regions: dict[str, list[list[str | None]]], config: dict[str, Any]
) -> dict[str, tuple[tuple[int, int], ...]]:
    return {
        direction: tuple(
            (x, y)
            for y, row in enumerate(_coverage_envelope(config, direction))
            for x, marker in enumerate(row)
            if marker == "#" and regions[direction][y][x] is None
        )
        for direction in DIRECTION_ORDER
    }


def _gesture_hierarchy(
    recipe: dict[str, Any], config: dict[str, Any]
) -> dict[str, dict[str, tuple[str, ...]]]:
    model = config["constructionGestures"][recipe["archetype"]]
    result = {}
    for direction in DIRECTION_ORDER:
        view = "side" if direction in {"left", "right"} else direction
        source = model[view]
        if "primary" in source:
            primary = source["primary"]
        elif recipe["construction"]["panelLayout"] == "yoke":
            primary = source.get("primaryWhenYoke", [])
        else:
            primary = source.get("primaryOtherwise", [])
        result[direction] = {
            "PRIMARY": tuple(primary),
            "SECONDARY": tuple(source.get("secondary", [])),
            "SUBORDINATE": tuple(source.get("subordinate", [])),
            "MICRO": tuple(source.get("micro", [])),
        }
    return result


def _secondary_regions(recipe: dict[str, Any]) -> frozenset[str]:
    return SECONDARY_REGION_GROUPS[recipe["colorBlocking"]["secondaryRegion"]]


def _region_boundary(frame: list[list[str | None]], x: int, y: int) -> bool:
    return bool(_adjacent_regions(frame, x, y))


def _base_roles(
    recipe: dict[str, Any],
    regions: dict[str, list[list[str | None]]],
) -> dict[str, list[list[str | None]]]:
    secondary = _secondary_regions(recipe)
    roles = {}
    for direction, frame in regions.items():
        role_frame = []
        for y, row in enumerate(frame):
            role_row = []
            for x, region in enumerate(row):
                if region is None:
                    role_row.append(None)
                elif region in secondary:
                    role_row.append("SECONDARY_BASE")
                else:
                    role_row.append("BASE")
            role_frame.append(role_row)
        roles[direction] = role_frame
    return roles


def _apply_large_light_and_shadow(
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    secondary: frozenset[str],
) -> None:
    for direction in DIRECTION_ORDER:
        frame = regions[direction]
        role_frame = roles[direction]
        # One screen-upper-left light plane. This is intentionally recomputed
        # for the left view instead of mirroring right-view shade pixels.
        for y in range(2, 6):
            for x in range(2, 7):
                if frame[y][x] is not None and frame[y][x] not in secondary and not _is_exterior(frame, x, y):
                    role_frame[y][x] = "LIGHT"
        # Restrained lower-right shadow mass; termination grammar may replace it.
        for y in range(9, 12):
            for x in range(10, 14):
                if frame[y][x] is not None and frame[y][x] not in secondary and not _is_exterior(frame, x, y):
                    role_frame[y][x] = "SHADOW"


def _apply_edges(
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    exposure: dict[str, list[list[str | None]]],
    secondary: frozenset[str],
) -> None:
    main_edge_role = {
        "neck_anchor": "EXTERIOR_CONTOUR",
        "outer_side_anchor": "EXTERIOR_CONTOUR",
        "underarm_anchor": "EXTERIOR_CONTOUR",
        "overlap_anchor": "DEEP_CREASE",
        "hem_corner_anchor": "EXTERIOR_CONTOUR",
        "shadow_edge": "SHADOW",
        "lit_edge": "LIGHT",
    }
    for direction in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                edge = exposure[direction][y][x]
                region = regions[direction][y][x]
                if edge is None or region is None:
                    continue
                if region in secondary:
                    roles[direction][y][x] = (
                        "SECONDARY_LIGHT" if edge == "lit_edge" else "SECONDARY_SHADOW"
                    )
                else:
                    roles[direction][y][x] = main_edge_role[edge]


def _apply_gestures(
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    gestures: dict[str, dict[str, tuple[str, ...]]],
    secondary: frozenset[str],
) -> None:
    strength_role = {
        "PRIMARY": "DEEP_CREASE",
        "SECONDARY": "STRUCTURAL_EDGE",
        "SUBORDINATE": "SHADOW",
        "MICRO": "BASE",
    }
    for direction in DIRECTION_ORDER:
        frame = regions[direction]
        for strength in ("SUBORDINATE", "SECONDARY", "PRIMARY"):
            for region_name in gestures[direction][strength]:
                for y, row in enumerate(frame):
                    for x, region in enumerate(row):
                        if region != region_name or not _region_boundary(frame, x, y) or _is_exterior(frame, x, y):
                            continue
                        roles[direction][y][x] = (
                            "SECONDARY_SHADOW" if region in secondary else strength_role[strength]
                        )


def _apply_optical_reinforcement(
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    exposure: dict[str, list[list[str | None]]],
    secondary: frozenset[str],
) -> None:
    for direction in DIRECTION_ORDER:
        for y in range(6, 12):
            bounds = _row_bounds(regions[direction], y)
            if bounds is None or bounds[1] - bounds[0] < 6:
                continue
            for edge_x, inner_x in ((bounds[0], bounds[0] + 1), (bounds[1], bounds[1] - 1)):
                if exposure[direction][y][edge_x] not in {"outer_side_anchor", "underarm_anchor"}:
                    continue
                inner_region = regions[direction][y][inner_x]
                if inner_region is not None and inner_region not in secondary and roles[direction][y][inner_x] in {"BASE", "SHADOW"}:
                    roles[direction][y][inner_x] = "DEEP_CREASE"


def _apply_termination(
    recipe: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    secondary: frozenset[str],
) -> None:
    hem = recipe["construction"]["hem"]
    for direction in DIRECTION_ORDER:
        frame = regions[direction]
        role_frame = roles[direction]
        termination = {"HEM", "RIBBING"}
        cells = [(x, y) for y, row in enumerate(frame) for x, region in enumerate(row) if region in termination]
        if not cells:
            # Plain lower edge: base reaches the edge with two attached corner shadows.
            y = max(y for y, row in enumerate(frame) if any(region is not None for region in row))
            xs = [x for x, region in enumerate(frame[y]) if region is not None]
            for x in xs[1:3] + xs[-3:-1]:
                if frame[y][x] not in secondary:
                    role_frame[y][x] = "SHADOW"
            continue
        min_y = min(y for _, y in cells)
        max_y = max(y for _, y in cells)
        for x, y in cells:
            region = frame[y][x]
            if region in secondary:
                if hem == "ribbed" and y == min_y and x % 4 in {1, 2}:
                    role_frame[y][x] = "SECONDARY_LIGHT"
                elif y == max_y or x in {min(px for px, py in cells if py == y), max(px for px, py in cells if py == y)}:
                    role_frame[y][x] = "SECONDARY_SHADOW"
                else:
                    role_frame[y][x] = "SECONDARY_BASE"
            else:
                role_frame[y][x] = "BASE"
        if hem == "structured":
            # Two attached overlap terminations, never a full-width shadow bar.
            for y in range(min_y, max_y + 1):
                xs = [x for x, region in enumerate(frame[y]) if region in termination]
                for x in xs[:1] + xs[-1:]:
                    if frame[y][x] not in secondary:
                        role_frame[y][x] = "SHADOW"
        elif hem == "contrast_band":
            # A semantic contrast band may retain a continuous weaker top edge.
            for x, y in cells:
                if y == min_y:
                    role_frame[y][x] = "SECONDARY_SHADOW" if frame[y][x] in secondary else "STRUCTURAL_EDGE"
        elif hem == "ribbed":
            # Two short vertical rib creases; no alternating checker texture.
            for x in (5, 10):
                for y in range(max(min_y, max_y - 1), max_y + 1):
                    if frame[y][x] in termination:
                        role_frame[y][x] = "SECONDARY_SHADOW" if frame[y][x] in secondary else "SHADOW"


def _apply_cuffs(
    recipe: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    secondary: frozenset[str],
) -> None:
    for direction in DIRECTION_ORDER:
        frame = regions[direction]
        sleeve_cells = [(x, y) for y, row in enumerate(frame) for x, region in enumerate(row) if region == "SLEEVE"]
        if not sleeve_cells:
            continue
        max_y = max(y for _, y in sleeve_cells)
        depth = 2 if recipe["archetype"] in {"JACKET", "SWEATER"} else 1
        for x, y in sleeve_cells:
            if y >= max_y - depth + 1:
                roles[direction][y][x] = "SHADOW" if "SLEEVE" not in secondary else "SECONDARY_SHADOW"


def _active_roles(recipe: dict[str, Any], config: dict[str, Any]) -> tuple[str, ...]:
    return tuple(config["shadeActivation"][recipe["rarity"]])


def _fallback_role(role: str, active: set[str], config: dict[str, Any]) -> str:
    while role in MAIN_ROLES and role not in active:
        role = config["roleFallbacks"][role]
    return role


def _activate_roles(
    roles: dict[str, list[list[str | None]]], active: tuple[str, ...], config: dict[str, Any]
) -> None:
    active_set = set(active)
    for frame in roles.values():
        for y, row in enumerate(frame):
            for x, role in enumerate(row):
                if role in MAIN_ROLES:
                    frame[y][x] = _fallback_role(role, active_set, config)


def _components(points: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(points)
    result = []
    while remaining:
        queue = deque([remaining.pop()])
        component = set()
        while queue:
            point = queue.popleft()
            component.add(point)
            x, y = point
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return sorted(result, key=len, reverse=True)


def _apply_highlight_cluster(
    recipe: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    gestures: dict[str, dict[str, tuple[str, ...]]],
    active: tuple[str, ...],
) -> None:
    if "OPTIONAL_HIGHLIGHT" not in active:
        return
    for direction in DIRECTION_ORDER:
        primary_regions = set(gestures[direction]["PRIMARY"])
        # Select only from a main-fabric light plane belonging to the primary
        # gesture. If that gesture is fixed secondary cloth, this garment simply
        # does not activate the optional main-fabric highlight.
        candidates = {
            (x, y)
            for y, row in enumerate(roles[direction])
            for x, role in enumerate(row)
            if role == "LIGHT" and regions[direction][y][x] in primary_regions
        }
        components = _components(candidates)
        if not components or len(components[0]) < 3:
            continue
        component = components[0]
        ordered = sorted(component, key=lambda point: (point[1], point[0]))
        chosen = None
        for first in ordered:
            for second in ordered:
                pair = {first, second}
                if first == second or abs(first[0] - second[0]) + abs(first[1] - second[1]) != 1:
                    continue
                if all(
                    any(neighbor in component - pair for neighbor in _neighbors(x, y) if neighbor is not None)
                    for x, y in pair
                ):
                    chosen = pair
                    break
            if chosen:
                break
        # Leave part of the larger LIGHT plane intact. A two-cell attached
        # glint has optical weight at Scale 2 without becoming a sparkle or
        # consuming the whole illuminated cluster.
        if chosen:
            for x, y in chosen:
                roles[direction][y][x] = "OPTIONAL_HIGHLIGHT"
def _apply_micro_detail(
    recipe: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
) -> None:
    if not recipe["microDetails"]:
        return
    # Renderer-owned candidates are semantic: upper body cells outside primary
    # openings. At most two attached cells are used by the V2 rarity contract.
    candidates = [
        (x, y)
        for y in range(4, 8)
        for x in range(3, 7)
        if regions["front"][y][x] in {"BODY", "OUTER_PANEL_LEFT"}
    ]
    if candidates:
        x, y = candidates[0]
        roles["front"][y][x] = "ACCENT"


def build_hd_roles(
    recipe: dict[str, Any],
    config: dict[str, Any],
    regions: dict[str, list[list[str | None]]],
    exposure: dict[str, list[list[str | None]]],
    gestures: dict[str, dict[str, tuple[str, ...]]],
) -> tuple[dict[str, list[list[str | None]]], tuple[str, ...]]:
    secondary = _secondary_regions(recipe)
    roles = _base_roles(recipe, regions)
    _apply_large_light_and_shadow(roles, regions, secondary)
    _apply_edges(roles, regions, exposure, secondary)
    _apply_gestures(roles, regions, gestures, secondary)
    _apply_optical_reinforcement(roles, regions, exposure, secondary)
    _apply_termination(recipe, roles, regions, secondary)
    _apply_cuffs(recipe, roles, regions, secondary)
    allowed = _active_roles(recipe, config)
    _activate_roles(roles, allowed, config)
    _apply_highlight_cluster(recipe, roles, regions, gestures, allowed)
    _apply_micro_detail(recipe, roles, regions)
    used = {
        role
        for frame in roles.values()
        for row in frame
        for role in row
        if role in MAIN_ROLES
    }
    active = tuple(role for role in config["outerMaskRamp"] if role in used)
    return roles, active


def _role_color(role: str, recipe: dict[str, Any], config: dict[str, Any]) -> RGBA:
    if role in MAIN_ROLES:
        value = config["outerMaskRamp"][role]
        return value, value, value, 255
    palette = load_v2_data()["palettes"]["families"][recipe["paletteFamily"]]
    if role == "SECONDARY_SHADOW":
        rgb = palette["secondary"]["shadow"]
    elif role == "SECONDARY_BASE":
        rgb = palette["secondary"]["base"]
    elif role == "SECONDARY_LIGHT":
        key = "light" if recipe["rarity"] != "Common" else "base"
        rgb = palette["secondary"][key]
    elif role == "ACCENT":
        rgb = load_v2_data()["palettes"]["accents"][recipe["accent"]]
        if rgb is None:
            raise ValueError("FS HD accent role requires a semantic accent color")
    else:
        raise ValueError(f"unsupported FS HD role {role}")
    return rgb[0], rgb[1], rgb[2], 255


def _build_frames(
    recipe: dict[str, Any], config: dict[str, Any], roles: dict[str, list[list[str | None]]]
) -> dict[str, list[list[RGBA]]]:
    return {
        direction: [
            [(0, 0, 0, 0) if role is None else _role_color(role, recipe, config) for role in row]
            for row in roles[direction]
        ]
        for direction in DIRECTION_ORDER
    }


def _composite_default(frame: list[list[RGBA]], recipe: dict[str, Any], config: dict[str, Any]):
    values = set(config["outerMaskRamp"].values())
    dye = load_v2_data()["palettes"]["families"][recipe["paletteFamily"]]["defaultDye"]
    result = blank_image(16, 16)
    for y, row in enumerate(frame):
        for x, pixel in enumerate(row):
            if pixel[3] and pixel[0] == pixel[1] == pixel[2] and pixel[0] in values:
                result[y][x] = tuple(pixel[index] * dye[index] // 255 for index in range(3)) + (255,)
            else:
                result[y][x] = pixel
    return result


def _stack(frames: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    texture = blank_image(16, 64)
    for index, direction in enumerate(DIRECTION_ORDER):
        for y, row in enumerate(frames[direction]):
            texture[index * 16 + y] = list(row)
    return texture


def render_fs_hd_v2(recipe: dict[str, Any]) -> FSPermanentGarmentRender:
    _assert_supported(recipe)
    config = load_hd_garment_grammar_v2()
    regions, side_template = build_hd_regions(recipe, config)
    coverage_missing = validate_hd_coverage(regions, config)
    if any(coverage_missing.values()):
        raise ValueError(f"FS HD body coverage failed: {coverage_missing}")
    exposure = classify_edge_exposure(regions)
    gestures = _gesture_hierarchy(recipe, config)
    roles, active = build_hd_roles(recipe, config, regions, exposure, gestures)
    frames = _build_frames(recipe, config, roles)
    default_frames = {
        direction: _composite_default(frame, recipe, config)
        for direction, frame in frames.items()
    }
    return FSPermanentGarmentRender(
        recipe=recipe,
        config=config,
        side_template=side_template,
        regions=regions,
        edge_exposure=exposure,
        gesture_hierarchy=gestures,
        roles=roles,
        active_main_roles=active,
        frames=frames,
        default_frames=default_frames,
        texture=_stack(frames),
        coverage_missing=coverage_missing,
    )
