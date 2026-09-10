"""Bounded 2x-density Fashion Sense renderer for the jacket POC.

This is intentionally not a general Fashion Sense garment generator. It proves
that the existing renderer-independent V2 recipe can select a higher-density
structural grammar, while all Fashion Sense coordinates remain backend data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA, blank_image
from generator.v2_recipe_engine import load_v2_data, validate_recipe_v2


ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "generator" / "data" / "fashionsense" / "hd_jacket_poc.json"
DIRECTION_ORDER = ("front", "right", "left", "back")


@dataclass(frozen=True)
class FashionSenseJacketRender:
    recipe: dict[str, Any]
    config: dict[str, Any]
    regions: dict[str, list[list[str | None]]]
    roles: dict[str, list[list[str | None]]]
    frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    coverage_envelopes: dict[str, list[list[bool]]]
    coverage_validation: "BodyCoverageValidation"


@dataclass(frozen=True)
class BodyCoverageValidation:
    passes: bool
    required_cells: dict[str, int]
    missing_cells: dict[str, tuple[tuple[int, int], ...]]


def load_backend_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _assert_supported_recipe(recipe: dict[str, Any]) -> None:
    validation = validate_recipe_v2(recipe, load_v2_data())
    if not validation.valid:
        raise ValueError("invalid V2 recipe: " + "; ".join(validation.errors))
    expected_construction = {
        "fit": "relaxed",
        "neckline": "open",
        "collar": "wide",
        "closure": "center_open",
        "layering": "visible_inner_layer",
        "hem": "structured",
        "panelLayout": "split_outer_panels",
    }
    if recipe.get("id") != "lifestyle-v2-16":
        raise ValueError("the POC backend accepts only lifestyle-v2-16")
    if recipe.get("archetype") != "JACKET" or recipe.get("rarity") != "Rare":
        raise ValueError("the POC requires the Rare JACKET semantic identity")
    if recipe.get("construction") != expected_construction:
        raise ValueError("Mistral construction changed from the controlled recipe")
    if recipe.get("substantialFeatures") != ["contrast_inner_layer", "broad_collar"]:
        raise ValueError("Mistral substantial features changed")
    if recipe.get("microDetails") != []:
        raise ValueError("the controlled Mistral recipe has no micro details")
    if recipe.get("colorBlocking") != {
        "primaryRegion": "outer_panels",
        "secondaryRegion": "inner_layer",
        "accentRegion": "none",
    }:
        raise ValueError("Mistral color blocking changed")
    if recipe.get("paletteFamily") != "cool_neutral":
        raise ValueError("Mistral palette family changed")


def _decode_rows(config: dict[str, Any], direction: str) -> list[list[str | None]]:
    legend = config["regionLegend"]
    size = config["logicalFrame"]
    rows = config["masks"][direction]
    if len(rows) != size["height"] or any(len(row) != size["width"] for row in rows):
        raise ValueError(f"invalid {direction} high-density mask dimensions")
    try:
        return [[legend[symbol] for symbol in row] for row in rows]
    except KeyError as exc:
        raise ValueError(f"unknown high-density region symbol {exc.args[0]!r}") from exc


def _mirror_side(
    right: list[list[str | None]],
) -> list[list[str | None]]:
    swaps = {
        "OUTER_PANEL_RIGHT": "OUTER_PANEL_LEFT",
        "OUTER_PANEL_LEFT": "OUTER_PANEL_RIGHT",
    }
    return [[swaps.get(region, region) for region in reversed(row)] for row in right]


def build_regions(config: dict[str, Any]) -> dict[str, list[list[str | None]]]:
    regions = {
        "front": _decode_rows(config, "front"),
        "right": _decode_rows(config, "right"),
        "back": _decode_rows(config, "back"),
    }
    regions["left"] = _mirror_side(regions["right"])
    return regions


def build_body_coverage_envelopes(
    config: dict[str, Any],
) -> dict[str, list[list[bool]]]:
    size = config["logicalFrame"]
    raw = config["bodyCoverageEnvelope"]
    envelopes: dict[str, list[list[bool]]] = {}
    for direction in ("front", "right", "back"):
        rows = raw[direction]
        if len(rows) != size["height"] or any(len(row) != size["width"] for row in rows):
            raise ValueError(f"invalid {direction} body-coverage envelope dimensions")
        if any(symbol not in {".", "#"} for row in rows for symbol in row):
            raise ValueError(f"invalid {direction} body-coverage envelope symbol")
        envelopes[direction] = [[symbol == "#" for symbol in row] for row in rows]
    envelopes["left"] = [list(reversed(row)) for row in envelopes["right"]]
    return envelopes


def validate_body_coverage(
    regions: dict[str, list[list[str | None]]],
    envelopes: dict[str, list[list[bool]]],
) -> BodyCoverageValidation:
    required_cells: dict[str, int] = {}
    missing_cells: dict[str, tuple[tuple[int, int], ...]] = {}
    for direction in DIRECTION_ORDER:
        required = envelopes[direction]
        frame = regions[direction]
        required_cells[direction] = sum(value for row in required for value in row)
        missing_cells[direction] = tuple(
            (x, y)
            for y, row in enumerate(required)
            for x, is_required in enumerate(row)
            if is_required and frame[y][x] is None
        )
    return BodyCoverageValidation(
        passes=not any(missing_cells.values()),
        required_cells=required_cells,
        missing_cells=missing_cells,
    )


def _bounds(frame: list[list[str | None]], region: str) -> tuple[int, int, int, int] | None:
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


def _role_for_region(
    frame: list[list[str | None]], direction: str, region: str, x: int, y: int
) -> str:
    bounds = _bounds(frame, region)
    if bounds is None:
        raise ValueError(f"missing bounds for {region}")
    min_x, min_y, max_x, max_y = bounds

    if region == "INNER_LAYER":
        if x in {min_x, max_x}:
            return "secondary_shadow"
        if y <= min_y + 3:
            return "secondary_light"
        return "secondary_base"

    if region == "COLLAR":
        if y == min_y and x not in {min_x, max_x}:
            return "primary_highlight"
        if y == max_y or (direction in {"left", "right"} and x == max_x):
            return "primary_shadow"
        return "primary_light"

    if region == "YOKE":
        if y == max_y:
            return "primary_shadow"
        if y == min_y and x not in {min_x, max_x}:
            return "primary_light"
        return "primary_base"

    if region == "HEM":
        if y == max_y:
            return "primary_deep"
        return "primary_shadow" if x in {min_x, max_x} else "primary_base"

    if region == "SHOULDER_CAP":
        if y == min_y:
            return "primary_light"
        if x in {min_x, max_x}:
            return "primary_shadow"
        return "primary_base"

    if region == "SLEEVE":
        center = (min_x + max_x) / 2
        outside = x < center if direction != "left" else x > center
        if y == max_y or outside and x in {min_x, max_x}:
            return "primary_deep"
        if y <= min_y + 2:
            return "primary_light"
        return "primary_shadow" if x in {min_x, max_x} else "primary_base"

    if region in {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT"}:
        is_inner_edge = (
            region == "OUTER_PANEL_LEFT" and x == max_x
        ) or (
            region == "OUTER_PANEL_RIGHT" and x == min_x
        )
        if is_inner_edge:
            return "primary_deep" if y >= 4 else "primary_shadow"
        if y == min_y or (y <= min_y + 4 and (x + y) % 4 in {0, 1}):
            return "primary_light"
        if x in {min_x, max_x} or y == max_y:
            return "primary_shadow"
        return "primary_base"

    raise ValueError(f"unsupported high-density region {region}")


def build_roles(
    regions: dict[str, list[list[str | None]]]
) -> dict[str, list[list[str | None]]]:
    roles: dict[str, list[list[str | None]]] = {}
    for direction, frame in regions.items():
        roles[direction] = [
            [
                None if region is None else _role_for_region(frame, direction, region, x, y)
                for x, region in enumerate(row)
            ]
            for y, row in enumerate(frame)
        ]
    return roles


def _role_color(role: str, recipe: dict[str, Any], config: dict[str, Any]) -> RGBA:
    if role.startswith("primary_"):
        shade = role.removeprefix("primary_")
        value = config["primaryMaskRamp"][shade]
        return value, value, value, 255

    palette = load_v2_data()["palettes"]["families"][recipe["paletteFamily"]]["secondary"]
    key = {
        "secondary_shadow": "shadow",
        "secondary_base": "base",
        "secondary_light": "light",
    }[role]
    rgb = palette[key]
    return rgb[0], rgb[1], rgb[2], 255


def build_frames(
    recipe: dict[str, Any],
    config: dict[str, Any],
    roles: dict[str, list[list[str | None]]],
) -> dict[str, list[list[RGBA]]]:
    width = config["logicalFrame"]["width"]
    height = config["logicalFrame"]["height"]
    frames: dict[str, list[list[RGBA]]] = {}
    for direction in DIRECTION_ORDER:
        frame = blank_image(width, height)
        for y, row in enumerate(roles[direction]):
            for x, role in enumerate(row):
                if role is not None:
                    frame[y][x] = _role_color(role, recipe, config)
        frames[direction] = frame
    return frames


def composite_default_frame(
    frame: list[list[RGBA]], config: dict[str, Any]
) -> list[list[RGBA]]:
    """Apply the declared default mask color on the authoritative logical grid.

    Fashion Sense performs the same multiplicative tint at draw time. This
    helper exists only for deterministic human-review previews; it does not
    alter the pack's grayscale mask texture.
    """
    masked_values = set(config["primaryMaskRamp"].values())
    dye = config["defaultPrimaryColor"]
    composite = blank_image(len(frame[0]), len(frame))
    for y, row in enumerate(frame):
        for x, pixel in enumerate(row):
            if pixel[3] and pixel[0] == pixel[1] == pixel[2] and pixel[0] in masked_values:
                composite[y][x] = (
                    pixel[0] * dye[0] // 255,
                    pixel[1] * dye[1] // 255,
                    pixel[2] * dye[2] // 255,
                    pixel[3],
                )
            else:
                composite[y][x] = pixel
    return composite


def stack_frames(
    frames: dict[str, list[list[RGBA]]], config: dict[str, Any]
) -> list[list[RGBA]]:
    width = config["logicalFrame"]["width"]
    height = config["logicalFrame"]["height"]
    texture = blank_image(width, height * len(DIRECTION_ORDER))
    for index, direction in enumerate(DIRECTION_ORDER):
        for y, row in enumerate(frames[direction]):
            texture[index * height + y] = list(row)
    return texture


def render_mistral_hd_jacket(recipe: dict[str, Any]) -> FashionSenseJacketRender:
    _assert_supported_recipe(recipe)
    config = load_backend_config()
    regions = build_regions(config)
    coverage_envelopes = build_body_coverage_envelopes(config)
    coverage_validation = validate_body_coverage(regions, coverage_envelopes)
    if not coverage_validation.passes:
        failures = ", ".join(
            f"{direction}: {list(cells)}"
            for direction, cells in coverage_validation.missing_cells.items()
            if cells
        )
        raise ValueError(f"high-detail jacket violates the body-coverage envelope ({failures})")
    roles = build_roles(regions)
    frames = build_frames(recipe, config, roles)
    return FashionSenseJacketRender(
        recipe=recipe,
        config=config,
        regions=regions,
        roles=roles,
        frames=frames,
        texture=stack_frames(frames, config),
        coverage_envelopes=coverage_envelopes,
        coverage_validation=coverage_validation,
    )
