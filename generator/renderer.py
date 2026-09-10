"""Constrained logical-pixel renderer for native Stardew shirts only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from generator.png_utils import (
    RGBA,
    TRANSPARENT,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    text_width,
)
from generator.recipe_engine import recipe_details


FRAME_SIZE = 8
SHEET_WIDTH = 256
SHEET_HEIGHT = 32
MASK_X_OFFSET = 128
PREVIEW_SCALE = 8
DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}
DIRECTION_ORDER = ("front", "back", "left", "right")

SHADE_ROLE = {
    "D": "main_deep",
    "S": "main_shadow",
    "B": "main_base",
    "L": "main_light",
    "H": "main_highlight",
}
MAIN_ROLES = frozenset(SHADE_ROLE.values())
PROTECTED_ROLES = frozenset({"secondary_shadow", "secondary", "accent"})


@dataclass
class RenderedShirt:
    recipe: dict[str, Any]
    roles: dict[str, list[list[str | None]]]
    native_pixels: list[list[RGBA]]
    default_composites: dict[str, list[list[RGBA]]]


def _mirror_rows(rows: list[str]) -> list[str]:
    return [row[::-1] for row in rows]


def _resolve_direction_rows(model: dict[str, Any], direction: str) -> list[str]:
    value = model[direction]
    if isinstance(value, dict) and "mirrorOf" in value:
        return _mirror_rows(_resolve_direction_rows(model, value["mirrorOf"]))
    if not isinstance(value, list) or len(value) != FRAME_SIZE:
        raise ValueError(f"invalid {direction} logical template")
    if any(len(row) != FRAME_SIZE for row in value):
        raise ValueError(f"invalid {direction} row width")
    return value


def _new_frame(
    silhouette_rows: list[str], shading_rows: list[str]
) -> list[list[str | None]]:
    frame: list[list[str | None]] = []
    for y in range(FRAME_SIZE):
        row: list[str | None] = []
        for x in range(FRAME_SIZE):
            if silhouette_rows[y][x] == ".":
                row.append(None)
            else:
                shade = shading_rows[y][x]
                if shade not in SHADE_ROLE:
                    raise ValueError(f"occupied silhouette cell has no shade at ({x},{y})")
                row.append(SHADE_ROLE[shade])
        frame.append(row)
    return frame


def _paint(
    frame: list[list[str | None]],
    points: Iterable[tuple[int, int]],
    role: str,
) -> None:
    for x, y in points:
        if 0 <= x < FRAME_SIZE and 0 <= y < FRAME_SIZE and frame[y][x] is not None:
            frame[y][x] = role


def _paint_row(
    frame: list[list[str | None]], y: int, x_values: Iterable[int], role: str
) -> None:
    _paint(frame, ((x, y) for x in x_values), role)


def _mirror_frame(frame: list[list[str | None]]) -> list[list[str | None]]:
    return [list(reversed(row)) for row in frame]


def _has_detail(recipe: dict[str, Any], detail: str) -> bool:
    return detail in recipe_details(recipe)


def _accent_or_secondary(recipe: dict[str, Any]) -> str:
    return "accent" if recipe["accent"] != "none" else "secondary_shadow"


def _apply_fit(frames: dict[str, list[list[str | None]]], recipe: dict[str, Any]) -> None:
    if recipe["fit"] == "relaxed":
        _paint_row(frames["front"], 6, range(2, 6), "main_base")
        _paint_row(frames["front"], 7, range(2, 6), "main_shadow")
        _paint_row(frames["back"], 6, range(2, 6), "main_base")
        _paint_row(frames["right"], 6, range(2, 6), "main_base")
    elif recipe["fit"] == "fitted":
        _paint_row(frames["front"], 6, (1, 6), "main_shadow")
        _paint_row(frames["front"], 7, (1, 2, 5, 6), "main_deep")
        _paint_row(frames["right"], 7, (1, 2, 5, 6), "main_deep")


def _apply_archetype_structure(
    frames: dict[str, list[list[str | None]]], recipe: dict[str, Any]
) -> None:
    front = frames["front"]
    back = frames["back"]
    side = frames["right"]
    archetype = recipe["archetype"]
    if archetype == "SWEATER":
        _paint_row(front, 6, range(1, 7), "main_base")
        _paint_row(front, 7, range(1, 7), "main_shadow")
        _paint_row(back, 6, range(1, 7), "main_base")
        _paint_row(back, 7, range(1, 7), "main_shadow")
        _paint_row(side, 6, range(2, 7), "main_base")
        _paint_row(side, 7, range(2, 7), "main_shadow")
    elif archetype == "BUTTON_SHIRT":
        _paint(front, ((2, y) for y in range(2, 7)), "main_light")
        _paint(front, ((5, y) for y in range(2, 7)), "main_base")
        _paint(back, ((1, y) for y in range(2, 5)), "main_light")
        _paint(side, ((2, y) for y in range(2, 5)), "main_light")
    elif archetype == "JACKET":
        _paint(front, ((1, y) for y in range(2, 6)), "main_light")
        _paint(front, ((6, y) for y in range(2, 6)), "main_base")
        _paint(front, ((2, y) for y in range(2, 7)), "main_shadow")
        _paint(front, ((5, y) for y in range(2, 7)), "main_shadow")
        _paint(back, ((1, y) for y in range(2, 5)), "main_light")
        _paint(back, ((6, y) for y in range(2, 5)), "main_base")
        _paint(side, ((2, y) for y in range(2, 5)), "main_light")
        _paint(side, ((6, y) for y in range(3, 7)), "main_shadow")
    elif archetype == "SAILOR_TOP":
        _paint_row(front, 5, range(2, 6), "main_base")
        _paint_row(back, 5, range(2, 6), "main_base")


def _apply_pattern(
    frames: dict[str, list[list[str | None]]], recipe: dict[str, Any]
) -> None:
    pattern = recipe["pattern"]
    if pattern == "none":
        return
    front, back, side = frames["front"], frames["back"], frames["right"]
    if pattern == "horizontal_stripe":
        for frame in (front, back, side):
            _paint_row(frame, 4, range(1, 7), "secondary")
            _paint(frame, ((1, 4), (6, 4)), "secondary_shadow")
    elif pattern == "vertical_trim":
        _paint(front, ((2, y) for y in range(2, 7)), "secondary_shadow")
        _paint(front, ((5, y) for y in range(2, 7)), "secondary")
        _paint(back, ((1, y) for y in range(1, 3)), "secondary_shadow")
        _paint(back, ((6, y) for y in range(1, 3)), "secondary")
        _paint(side, ((5, y) for y in range(2, 7)), "secondary_shadow")
    elif pattern == "simple_border":
        for frame in (front, back):
            _paint_row(frame, 7, range(1, 7), "secondary_shadow")
            _paint(frame, ((0, 1), (7, 1)), "secondary")
        _paint_row(side, 7, range(2, 7), "secondary_shadow")
        _paint(side, ((0, 1), (6, 1)), "secondary")
    else:
        raise ValueError(f"unsupported pattern {pattern}")


def _apply_closure(
    frames: dict[str, list[list[str | None]]], recipe: dict[str, Any]
) -> None:
    front, back, side = frames["front"], frames["back"], frames["right"]
    closure = recipe["closure"]
    if closure == "none":
        return
    if closure == "center_open":
        if _has_detail(recipe, "inner_layer"):
            _paint(front, ((3, y) for y in range(1, 7)), "secondary_shadow")
            _paint(front, ((4, y) for y in range(1, 7)), "secondary")
            _paint(side, ((6, y) for y in range(2, 7)), "secondary")
        else:
            _paint(front, ((3, y) for y in range(1, 7)), "main_deep")
            _paint(front, ((4, y) for y in range(1, 7)), "main_shadow")
        _paint(front, ((2, y) for y in range(2, 7)), "main_deep")
        _paint(front, ((5, y) for y in range(2, 7)), "main_shadow")
        _paint(side, ((5, y) for y in range(2, 7)), "main_shadow")
        _paint(back, ((3, y) for y in range(4, 7)), "main_shadow")
        _paint(back, ((4, y) for y in range(4, 7)), "main_base")
    elif closure == "buttons":
        _paint(front, ((3, y) for y in range(2, 7)), "main_shadow")
        _paint(front, ((4, y) for y in range(2, 7)), "main_base")
        _paint(side, ((6, y) for y in range(2, 7)), "main_shadow")
        if _has_detail(recipe, "button_line"):
            role = _accent_or_secondary(recipe)
            _paint(front, ((4, 2), (4, 4), (4, 6)), role)
    else:
        raise ValueError(f"unsupported closure {closure}")


def _apply_neckline_or_collar(
    frames: dict[str, list[list[str | None]]], recipe: dict[str, Any]
) -> None:
    front, back, side = frames["front"], frames["back"], frames["right"]
    collar = recipe["collar"]
    if collar == "none":
        neckline = recipe["neckline"]
        if neckline == "round":
            _paint(front, ((2, 1), (5, 1)), "main_shadow")
            _paint(front, ((3, 1), (4, 1)), "main_deep")
            _paint(front, ((3, 2), (4, 2)), "main_shadow")
            _paint(back, ((2, 0), (5, 0)), "main_base")
            _paint(back, ((3, 0), (4, 0)), "main_shadow")
            _paint(side, ((2, 0), (4, 0), (3, 1)), "main_shadow")
        elif neckline == "crew":
            _paint(front, ((2, 1), (5, 1)), "main_light")
            _paint(front, ((3, 1), (4, 1)), "main_deep")
            _paint(back, ((2, 0), (3, 0), (4, 0), (5, 0)), "main_shadow")
            _paint(side, ((2, 0), (4, 0)), "main_shadow")
        elif neckline == "shallow_v":
            _paint(front, ((2, 1), (5, 1)), "main_light")
            _paint(front, ((3, 1), (4, 1)), "main_shadow")
            _paint(front, ((3, 2), (4, 2)), "main_deep")
            _paint(back, ((2, 0), (5, 0)), "main_base")
            _paint(back, ((3, 0), (4, 0)), "main_shadow")
            _paint(side, ((2, 0), (4, 0), (4, 1)), "main_shadow")
        elif neckline == "open":
            _paint(front, ((3, 1), (4, 1), (3, 2), (4, 2)), "main_deep")
        else:
            raise ValueError(f"unsupported neckline {neckline}")
        return

    if collar == "small_folded":
        _paint(front, ((2, 1), (5, 1)), "secondary")
        _paint(front, ((3, 1), (4, 1), (2, 2), (5, 2)), "secondary_shadow")
        _paint(back, ((2, 0), (3, 0), (4, 0), (5, 0)), "secondary")
        _paint(back, ((3, 1), (4, 1)), "secondary_shadow")
        _paint(side, ((4, 0), (5, 0)), "secondary")
        _paint(side, ((4, 1), (5, 1)), "secondary_shadow")
    elif collar == "wide":
        _paint(front, ((1, 1), (2, 1), (5, 1), (6, 1)), "secondary")
        _paint(front, ((2, 2), (5, 2)), "secondary_shadow")
        _paint(front, ((3, 2), (4, 2)), "main_shadow")
        _paint(back, ((x, 0) for x in range(1, 7)), "secondary")
        _paint(back, ((x, 1) for x in range(2, 6)), "secondary_shadow")
        _paint(side, ((2, 0), (4, 0), (5, 0)), "secondary")
        _paint(side, ((2, 1), (3, 1), (4, 1)), "secondary_shadow")
    elif collar == "sailor":
        _paint(front, ((0, 1), (1, 1), (6, 1), (7, 1)), "secondary")
        _paint(front, ((1, 2), (2, 2), (5, 2), (6, 2)), "secondary")
        _paint(front, ((2, 3), (5, 3)), "secondary_shadow")
        _paint(front, ((3, 2), (4, 2)), "main_deep")
        _paint(back, ((x, 0) for x in range(2, 6)), "secondary_shadow")
        _paint(back, ((x, y) for y in (1, 2) for x in range(1, 7)), "secondary")
        _paint(back, ((x, 3) for x in range(2, 6)), "secondary_shadow")
        _paint(side, ((4, 0), (5, 0)), "secondary_shadow")
        _paint(side, ((x, y) for y in (1, 2) for x in range(2, 6)), "secondary")
        _paint(side, ((x, 3) for x in range(3, 6)), "secondary_shadow")
    else:
        raise ValueError(f"unsupported collar {collar}")


def _apply_detail(
    frames: dict[str, list[list[str | None]]], recipe: dict[str, Any], detail: str
) -> None:
    front, back, side = frames["front"], frames["back"], frames["right"]
    if detail in {"none", "inner_layer", "button_line"}:
        return
    if detail == "center_stripe":
        _paint(front, ((3, y) for y in range(3, 7)), "secondary_shadow")
        _paint(front, ((4, y) for y in range(3, 7)), "secondary")
    elif detail == "chest_accent":
        if recipe["archetype"] == "SAILOR_TOP":
            _paint(front, ((3, 3), (4, 3)), "accent")
        else:
            _paint(front, ((5, 3), (5, 4)), "accent")
    elif detail == "lower_trim":
        for frame in (front, back):
            _paint_row(frame, 6, range(1, 7), "secondary")
            _paint(frame, ((1, 6), (6, 6)), "secondary_shadow")
        _paint_row(side, 6, range(2, 7), "secondary")
        _paint(side, ((2, 6), (6, 6)), "secondary_shadow")
    else:
        raise ValueError(f"unsupported detail {detail}")


def _enforce_sleeve_samples(front: list[list[str | None]]) -> None:
    # Installed 1.6.15 uses mask/base front x=0 rows 4,3,2 as dark/mid/light.
    front[2][0] = "main_light"
    front[3][0] = "main_base"
    front[4][0] = "main_shadow"


def build_logical_roles(recipe: dict[str, Any], data: dict[str, Any]) -> dict[str, list[list[str | None]]]:
    grammar = data["grammar"]
    silhouettes = grammar["silhouetteTemplates"][recipe["fit"]]
    shading = grammar["shadingTemplates"]
    frames: dict[str, list[list[str | None]]] = {}
    for direction in ("front", "right", "back"):
        frames[direction] = _new_frame(
            _resolve_direction_rows(silhouettes, direction),
            _resolve_direction_rows(shading, direction),
        )
    _apply_fit(frames, recipe)
    _apply_archetype_structure(frames, recipe)
    _apply_pattern(frames, recipe)
    _apply_closure(frames, recipe)
    _apply_neckline_or_collar(frames, recipe)
    for detail in recipe_details(recipe):
        _apply_detail(frames, recipe, detail)
    _enforce_sleeve_samples(frames["front"])
    frames["left"] = _mirror_frame(frames["right"])
    return {direction: frames[direction] for direction in DIRECTION_Y}


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
    elif role == "accent":
        accent = data["palettes"]["accents"][recipe["accent"]]
        if accent is None:
            rgb = palette["secondary"]["shadow"]
        else:
            rgb = accent
    else:
        raise ValueError(f"unknown protected role {role}")
    return rgb[0], rgb[1], rgb[2], 255


def build_native_sheet(
    recipe: dict[str, Any], roles: dict[str, list[list[str | None]]], data: dict[str, Any]
) -> list[list[RGBA]]:
    sheet = blank_image(SHEET_WIDTH, SHEET_HEIGHT)
    for direction, y0 in DIRECTION_Y.items():
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
                    raise ValueError(f"unsupported logical role {role}")
    return sheet


def _multiply_mask(mask: RGBA, dye: list[int]) -> RGBA:
    return (
        mask[0] * dye[0] // 255,
        mask[1] * dye[1] // 255,
        mask[2] * dye[2] // 255,
        mask[3],
    )


def composite_direction(
    native: list[list[RGBA]], direction: str, recipe: dict[str, Any], data: dict[str, Any]
) -> list[list[RGBA]]:
    result = blank_image(FRAME_SIZE, FRAME_SIZE)
    dye = data["palettes"]["families"][recipe["paletteFamily"]]["defaultDye"]
    y0 = DIRECTION_Y[direction]
    for y in range(FRAME_SIZE):
        for x in range(FRAME_SIZE):
            base = native[y0 + y][x]
            mask = native[y0 + y][MASK_X_OFFSET + x]
            if base[3]:
                result[y][x] = base
            if mask[3]:
                result[y][x] = _multiply_mask(mask, dye)
    return result


def make_contact_sheet(
    composites: dict[str, list[list[RGBA]]], item_name: str
) -> list[list[RGBA]]:
    width, height = 352, 128
    background = (235, 226, 214, 255)
    border = (101, 86, 73, 255)
    checker_a = (211, 201, 188, 255)
    checker_b = (191, 181, 169, 255)
    pixels = blank_image(width, height, background)
    title = item_name.upper()
    title_scale = 1
    if text_width(title, title_scale) > width - 16:
        title = title[:54]
    draw_text(
        pixels,
        title,
        max(8, (width - text_width(title, title_scale)) // 2),
        6,
        scale=title_scale,
    )
    tile_size = FRAME_SIZE * PREVIEW_SCALE
    gap = 16
    start_x = 12
    tile_y = 52
    for index, direction in enumerate(DIRECTION_ORDER):
        x0 = start_x + index * (tile_size + gap)
        label = direction.upper()
        draw_text(
            pixels,
            label,
            x0 + (tile_size - text_width(label, 1)) // 2,
            31,
            scale=1,
        )
        draw_rect(pixels, x0 - 2, tile_y - 2, tile_size + 4, tile_size + 4, border)
        for logical_y in range(FRAME_SIZE):
            for logical_x in range(FRAME_SIZE):
                checker = checker_a if (logical_x + logical_y) % 2 == 0 else checker_b
                draw_rect(
                    pixels,
                    x0 + logical_x * PREVIEW_SCALE,
                    tile_y + logical_y * PREVIEW_SCALE,
                    PREVIEW_SCALE,
                    PREVIEW_SCALE,
                    checker,
                )
        blit(
            pixels,
            nearest_scale(composites[direction], PREVIEW_SCALE),
            x0,
            tile_y,
            transparent=True,
        )
    return pixels


def render_recipe(recipe: dict[str, Any], data: dict[str, Any]) -> RenderedShirt:
    roles = build_logical_roles(recipe, data)
    native = build_native_sheet(recipe, roles, data)
    composites = {
        direction: composite_direction(native, direction, recipe, data)
        for direction in DIRECTION_Y
    }
    return RenderedShirt(recipe, roles, native, composites)

