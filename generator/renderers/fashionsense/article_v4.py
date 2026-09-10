"""V4 garment-article translation over the frozen Fashion Sense V3 renderer.

The V3 render is authoritative for construction, surface design, shading, and
coverage.  V4 applies a small renderer-owned article operation afterwards.
Semantic V4 recipes therefore contain no pixel coordinates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA, TRANSPARENT, blank_image
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.surface_v3 import FSV3SurfaceRender, render_fs_v3
from generator.v3.engine import load_v3_data
from generator.v4.engine import to_v3_recipe, validate_v4_recipe


ROOT = Path(__file__).resolve().parents[3]
GRAMMAR = ROOT / "generator" / "data" / "fashionsense" / "v4_article_grammar.json"


@dataclass(frozen=True)
class FSV4ArticleRender:
    recipe: dict[str, Any]
    design: FSV3SurfaceRender
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    article_cells: dict[str, frozenset[tuple[int, int]]]
    removed_cells: dict[str, frozenset[tuple[int, int]]]
    translated_material_cells: dict[str, frozenset[tuple[int, int]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    sleeve_colors: tuple[tuple[int, int, int], ...]


def load_v4_article_grammar() -> dict[str, Any]:
    return json.loads(GRAMMAR.read_text(encoding="utf-8"))


def _stack(frames: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    texture = blank_image(16, 64)
    for index, direction in enumerate(DIRECTION_ORDER):
        for y, row in enumerate(frames[direction]):
            texture[index * 16 + y] = list(row)
    return texture


def _occupied_xs(frame: list[list[RGBA]], y: int) -> list[int]:
    return [x for x, pixel in enumerate(frame[y]) if pixel[3]]


def _clear(frames, defaults, direction: str, x: int, y: int, removed) -> None:
    if frames[direction][y][x][3]:
        frames[direction][y][x] = TRANSPARENT
        defaults[direction][y][x] = TRANSPARENT
        removed[direction].add((x, y))


def _apply_fitted(frames, defaults, grammar, removed) -> None:
    for direction in DIRECTION_ORDER:
        for row, inset in grammar["rowInsets"].items():
            y = int(row)
            xs = _occupied_xs(frames[direction], y)
            # Preserve a minimum eight-cell body mass; taper only the outermost
            # lower-torso cells, never the proven shoulder coverage envelope.
            if len(xs) >= 8 + 2 * inset:
                for x in xs[:inset] + xs[-inset:]:
                    _clear(frames, defaults, direction, x, y, removed)


def _material_color(story: dict[str, Any], role: str | None) -> RGBA:
    if role in {"EXTERIOR_CONTOUR", "DEEP_CREASE", "STRUCTURAL_EDGE", "SHADOW", "SECONDARY_SHADOW"}:
        rgb = story["darkAccent"]
    elif role in {"LIGHT", "OPTIONAL_HIGHLIGHT", "SECONDARY_LIGHT"}:
        rgb = story["lightAccent"]
    else:
        rgb = story["secondary"]
    return rgb[0], rgb[1], rgb[2], 255


def _apply_vest(frames, defaults, design, grammar, translated) -> tuple[tuple[int, int, int], ...]:
    story = load_v3_data()["palettes"]["stories"][design.recipe["paletteStory"]]
    inner_regions = set(grammar["innerShirtRegions"])
    for direction in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                if design.base.regions[direction][y][x] in inner_regions and frames[direction][y][x][3]:
                    role = design.base.roles[direction][y][x]
                    color = _material_color(story, role)
                    frames[direction][y][x] = color
                    defaults[direction][y][x] = color
                    translated[direction].add((x, y))
    return tuple(tuple(story[key]) for key in ("darkAccent", "secondary", "lightAccent"))


def _apply_crop(frames, defaults, grammar, removed) -> None:
    maximum_y = grammar["maximumOccupiedY"]
    for direction in DIRECTION_ORDER:
        for y in range(maximum_y + 1, 16):
            for x in range(16):
                _clear(frames, defaults, direction, x, y, removed)
        # Re-terminate the newly exposed edge with a selective darker cadence.
        # It is intentionally not a full-width bar.
        xs = _occupied_xs(frames[direction], maximum_y)
        for x in xs:
            if x in {xs[0], xs[-1]} or (direction in {"front", "back"} and x in {7, 8}):
                pixel = frames[direction][maximum_y][x]
                if pixel[3] and pixel[0] == pixel[1] == pixel[2]:
                    value = min(pixel[0], 104)
                    frames[direction][maximum_y][x] = (value, value, value, 255)
                    defaults[direction][maximum_y][x] = tuple(max(18, c * value // max(pixel[0], 1)) for c in defaults[direction][maximum_y][x][:3]) + (255,)


def _coverage_missing(frames, config) -> dict[str, tuple[tuple[int, int], ...]]:
    result = {}
    source = config["bodyCoverageEnvelope"]
    for direction in DIRECTION_ORDER:
        name = "right" if direction == "left" else direction
        rows = source[name]
        if direction == "left":
            rows = [row[::-1] for row in rows]
        result[direction] = tuple(
            (x, y) for y, row in enumerate(rows) for x, marker in enumerate(row)
            if marker == "#" and not frames[direction][y][x][3]
        )
    return result


def _outer_sleeve_colors(design: FSV3SurfaceRender) -> tuple[tuple[int, int, int], ...]:
    config = design.base.config
    values = config.get("sleeveMaskRoles", ["SHADOW", "BASE", "LIGHT"])
    ramp = config["outerMaskRamp"]
    result = []
    for role in values:
        value = ramp[role] if isinstance(role, str) else int(role)
        result.append((value, value, value))
    return tuple(result[:3])


def render_fs_v4(recipe: dict[str, Any]) -> FSV4ArticleRender:
    validation = validate_v4_recipe(recipe)
    if not validation.valid:
        raise ValueError("invalid V4 recipe: " + "; ".join(validation.errors))
    design = render_fs_v3(to_v3_recipe(recipe))
    frames = {d: [list(row) for row in design.frames[d]] for d in DIRECTION_ORDER}
    defaults = {d: [list(row) for row in design.default_frames[d]] for d in DIRECTION_ORDER}
    removed = {d: set() for d in DIRECTION_ORDER}
    translated = {d: set() for d in DIRECTION_ORDER}
    grammar = load_v4_article_grammar()["articles"][recipe["articleType"]]
    sleeve_colors = _outer_sleeve_colors(design)
    operation = grammar["operation"]
    if operation == "taper_lower_silhouette":
        _apply_fitted(frames, defaults, grammar, removed)
    elif operation == "translate_vest_materials":
        sleeve_colors = _apply_vest(frames, defaults, design, grammar, translated)
    elif operation == "crop_outer_shell":
        _apply_crop(frames, defaults, grammar, removed)
    elif operation not in {"preserve_heavy_mass", "preserve_full_short_shell"}:
        raise ValueError(f"unknown V4 article operation {operation}")
    coverage = _coverage_missing(frames, design.base.config)
    if any(coverage.values()):
        raise ValueError(f"V4 article operation broke body coverage: {coverage}")
    article_cells = {
        d: frozenset((x, y) for y in range(16) for x in range(16) if frames[d][y][x][3])
        for d in DIRECTION_ORDER
    }
    return FSV4ArticleRender(
        recipe, design, frames, defaults, _stack(frames), article_cells,
        {d: frozenset(v) for d, v in removed.items()},
        {d: frozenset(v) for d, v in translated.items()}, coverage, sleeve_colors,
    )

