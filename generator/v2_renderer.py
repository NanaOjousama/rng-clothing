"""Construction-first logical-pixel renderer for vanilla V2 shirts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from generator.png_utils import RGBA, blank_image
from generator.v2_structural import FRAME_SIZE, VANILLA_DIRECTION_Y, build_structural_regions


SHEET_WIDTH = 256
SHEET_HEIGHT = 32
MASK_X_OFFSET = 128
MAIN_ROLES = frozenset(
    {"main_deep", "main_shadow", "main_base", "main_light", "main_highlight"}
)
PROTECTED_ROLES = frozenset(
    {"secondary_shadow", "secondary", "secondary_light", "accent"}
)
SHADE_ROLE = {
    "D": "main_deep",
    "S": "main_shadow",
    "B": "main_base",
    "L": "main_light",
    "H": "main_highlight",
}
SECONDARY_REGION_GROUPS = {
    "none": frozenset(),
    "collar": frozenset({"COLLAR"}),
    "yoke": frozenset({"YOKE", "COLLAR"}),
    "placket": frozenset({"PLACKET"}),
    "outer_panels": frozenset({"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}),
    "inner_layer": frozenset({"INNER_LAYER"}),
    "hem": frozenset({"HEM"}),
    "ribbing": frozenset({"RIBBING", "NECKLINE"}),
    "stripe": frozenset({"STRIPE"}),
}


@dataclass
class RenderedV2Shirt:
    recipe: dict[str, Any]
    regions: dict[str, list[list[str | None]]]
    roles: dict[str, list[list[str | None]]]
    native_pixels: list[list[RGBA]]
    default_composites: dict[str, list[list[RGBA]]]


def _resolve_shading_rows(grammar: dict[str, Any], direction: str) -> list[str]:
    value = grammar["shadingTemplates"][direction]
    if isinstance(value, dict) and "mirrorOf" in value:
        return [row[::-1] for row in _resolve_shading_rows(grammar, value["mirrorOf"])]
    return value


def _region_bounds(
    frame: list[list[str | None]], region: str
) -> tuple[int, int, int, int] | None:
    points = [
        (x, y)
        for y, row in enumerate(frame)
        for x, value in enumerate(row)
        if value == region
    ]
    if not points:
        return None
    return (
        min(x for x, _ in points),
        min(y for _, y in points),
        max(x for x, _ in points),
        max(y for _, y in points),
    )


def _touches_other_horizontally(
    frame: list[list[str | None]], x: int, y: int, region: str
) -> bool:
    for nx in (x - 1, x + 1):
        if 0 <= nx < FRAME_SIZE and frame[y][nx] not in {None, region}:
            return True
    return False


def _secondary_role(
    frame: list[list[str | None]], region: str, x: int, y: int
) -> str:
    bounds = _region_bounds(frame, region)
    if bounds is None:
        return "secondary"
    min_x, min_y, max_x, max_y = bounds
    if region in {"HEM", "RIBBING"}:
        if y == max_y:
            return "secondary_shadow"
        if y == min_y and min_x < x < max_x:
            return "secondary_light"
        return "secondary"
    if region == "PLACKET":
        return "secondary_shadow" if x == min_x else "secondary_light"
    if region == "INNER_LAYER":
        if _touches_other_horizontally(frame, x, y, region):
            return "secondary_shadow"
        return "secondary_light" if y <= min_y + 1 else "secondary"
    if region in {"COLLAR", "YOKE"}:
        if y == max_y:
            return "secondary_shadow"
        if y == min_y and x not in {min_x, max_x}:
            return "secondary_light"
        return "secondary"
    if region == "STRIPE":
        return "secondary_shadow" if x in {min_x, max_x} else "secondary"
    if region in {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}:
        return "secondary_shadow" if _touches_other_horizontally(frame, x, y, region) else "secondary"
    return "secondary"


def _main_role(
    frame: list[list[str | None]],
    region: str,
    x: int,
    y: int,
    base_role: str,
) -> str:
    bounds = _region_bounds(frame, region)
    if region == "NECKLINE":
        return "main_deep" if y <= 1 else "main_shadow"
    if region == "COLLAR":
        if bounds and y == bounds[1]:
            return "main_light"
        return "main_shadow"
    if region == "YOKE":
        if bounds and y == bounds[1]:
            return "main_light"
        if bounds and y == bounds[3]:
            return "main_shadow"
        return "main_base"
    if region == "PLACKET":
        if bounds and x == bounds[0]:
            return "main_deep"
        return "main_light" if y in {2, 3} else "main_shadow"
    if region == "INNER_LAYER":
        if _touches_other_horizontally(frame, x, y, region):
            return "main_shadow"
        return "main_light" if y <= 3 else "main_base"
    if region in {"HEM", "RIBBING"}:
        if bounds and y == bounds[3]:
            return "main_deep" if x in {bounds[0], bounds[2]} else "main_shadow"
        return "main_base"
    if region == "STRIPE":
        return "main_shadow" if bounds and x in {bounds[0], bounds[2]} else "main_light"
    if region in {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}:
        if _touches_other_horizontally(frame, x, y, region):
            return "main_deep" if y >= 2 else "main_shadow"
        return base_role
    return base_role


def _apply_micro_detail(
    roles: dict[str, list[list[str | None]]],
    regions: dict[str, list[list[str | None]]],
    recipe: dict[str, Any],
) -> None:
    if not recipe["microDetails"]:
        return
    detail = recipe["microDetails"][0]
    front = roles["front"]
    region_frame = regions["front"]
    archetype = recipe["archetype"]
    if detail in {"small_chest_accent", "small_pin"}:
        candidates = (
            [(6, 3), (6, 4)]
            if archetype == "JACKET"
            else [(5, 3), (5, 4)]
        )
        for x, y in candidates:
            if front[y][x] is not None and region_frame[y][x] not in {"INNER_LAYER", "PLACKET"}:
                front[y][x] = "accent"
    elif detail == "tiny_button":
        candidates = [(4, 3), (4, 5)]
        for x, y in candidates:
            if region_frame[y][x] == "PLACKET":
                front[y][x] = "accent"
    elif detail == "single_accent_pixel":
        x, y = (6, 3) if archetype == "JACKET" else (5, 3)
        if front[y][x] is not None:
            front[y][x] = "accent"
    elif detail == "tiny_trim_mark":
        for x, y in ((5, 7), (6, 7)):
            if front[y][x] is not None:
                front[y][x] = "accent"
    else:
        raise ValueError(f"unsupported V2 micro detail {detail}")


def _enforce_sleeve_samples(
    front: list[list[str | None]], archetype: str
) -> None:
    # Installed 1.6.15 samples front x=0 at y=4,3,2 for dark/mid/light.
    # Vanilla fixes sleeve geometry, so jackets use one deeper terminal sample
    # to clarify the existing cuff/end pixel without inventing longer arms.
    front[4][0] = "main_deep" if archetype == "JACKET" else "main_shadow"
    front[3][0] = "main_base"
    front[2][0] = "main_light"


def build_logical_roles(
    recipe: dict[str, Any],
    regions: dict[str, list[list[str | None]]],
    data: dict[str, Any],
) -> dict[str, list[list[str | None]]]:
    secondary_regions = SECONDARY_REGION_GROUPS[recipe["colorBlocking"]["secondaryRegion"]]
    roles: dict[str, list[list[str | None]]] = {}
    for direction in ("front", "right", "back"):
        region_frame = regions[direction]
        shade_rows = _resolve_shading_rows(data["grammar"], direction)
        role_frame: list[list[str | None]] = []
        for y, row in enumerate(region_frame):
            role_row: list[str | None] = []
            for x, region in enumerate(row):
                if region is None:
                    role_row.append(None)
                    continue
                if region in secondary_regions:
                    role_row.append(_secondary_role(region_frame, region, x, y))
                    continue
                shade_symbol = shade_rows[y][x]
                if shade_symbol not in SHADE_ROLE:
                    # A fitted silhouette may expose a cell where the shared
                    # grammar was transparent; use a conservative base value.
                    base_role = "main_base"
                else:
                    base_role = SHADE_ROLE[shade_symbol]
                role_row.append(_main_role(region_frame, region, x, y, base_role))
            role_frame.append(role_row)
        roles[direction] = role_frame
    roles["left"] = [list(reversed(row)) for row in roles["right"]]
    _apply_micro_detail(roles, regions, recipe)
    _enforce_sleeve_samples(roles["front"], recipe["archetype"])
    return roles


def _main_mask_value(role: str, recipe: dict[str, Any], data: dict[str, Any]) -> int:
    ramp = data["palettes"]["mainMaskRamp"]
    if role == "main_highlight" and recipe["rarity"] == "Common":
        return ramp["main_light"]
    return ramp[role]


def _protected_color(role: str, recipe: dict[str, Any], data: dict[str, Any]) -> RGBA:
    palette = data["palettes"]["families"][recipe["paletteFamily"]]
    if role == "secondary_shadow":
        rgb = palette["secondary"]["shadow"]
    elif role == "secondary":
        rgb = palette["secondary"]["base"]
    elif role == "secondary_light":
        # Common and Uncommon retain V1's conservative six/eight-color
        # ceilings; Rare may use the full three-value secondary ramp.
        key = "light" if recipe["rarity"] == "Rare" else "base"
        rgb = palette["secondary"][key]
    elif role == "accent":
        rgb = data["palettes"]["accents"][recipe["accent"]]
        if rgb is None:
            raise ValueError("accent role used with accent=none")
    else:
        raise ValueError(f"unsupported protected role {role}")
    return rgb[0], rgb[1], rgb[2], 255


def build_native_sheet(
    recipe: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
    data: dict[str, Any],
) -> list[list[RGBA]]:
    sheet = blank_image(SHEET_WIDTH, SHEET_HEIGHT)
    for direction, y0 in VANILLA_DIRECTION_Y.items():
        frame = roles[direction]
        for y in range(FRAME_SIZE):
            for x in range(FRAME_SIZE):
                role = frame[y][x]
                if role is None:
                    continue
                if role in MAIN_ROLES:
                    value = _main_mask_value(role, recipe, data)
                    sheet[y0 + y][MASK_X_OFFSET + x] = (value, value, value, 255)
                elif role in PROTECTED_ROLES:
                    sheet[y0 + y][x] = _protected_color(role, recipe, data)
                else:
                    raise ValueError(f"unsupported V2 logical role {role}")
    return sheet


def _multiply_mask(mask: RGBA, dye: list[int]) -> RGBA:
    return (
        mask[0] * dye[0] // 255,
        mask[1] * dye[1] // 255,
        mask[2] * dye[2] // 255,
        mask[3],
    )


def composite_direction(
    native: list[list[RGBA]],
    direction: str,
    recipe: dict[str, Any],
    data: dict[str, Any],
) -> list[list[RGBA]]:
    result = blank_image(FRAME_SIZE, FRAME_SIZE)
    dye = data["palettes"]["families"][recipe["paletteFamily"]]["defaultDye"]
    y0 = VANILLA_DIRECTION_Y[direction]
    for y in range(FRAME_SIZE):
        for x in range(FRAME_SIZE):
            base = native[y0 + y][x]
            mask = native[y0 + y][MASK_X_OFFSET + x]
            if base[3]:
                result[y][x] = base
            if mask[3]:
                result[y][x] = _multiply_mask(mask, dye)
    return result


def render_v2_recipe(recipe: dict[str, Any], data: dict[str, Any]) -> RenderedV2Shirt:
    regions = build_structural_regions(recipe, data)
    roles = build_logical_roles(recipe, regions, data)
    native = build_native_sheet(recipe, roles, data)
    composites = {
        direction: composite_direction(native, direction, recipe, data)
        for direction in VANILLA_DIRECTION_Y
    }
    return RenderedV2Shirt(recipe, regions, roles, native, composites)
