#!/usr/bin/env python3
"""Static/source-contract validator for the Fashion Sense HD jacket POC."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generator.png_utils import encode_rgba_png, nearest_scale, read_rgba_png
from generator.renderers.fashionsense import (
    composite_default_frame,
    render_mistral_hd_jacket,
    validate_body_coverage,
)
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data


ROOT = PROJECT_ROOT
OUTPUT = ROOT / "output" / "fashionsense" / "poc_hd_jacket"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Jacket-POC"
SHIRT_FOLDER = PACK / "Shirts" / "MistralLapelLayerJacketHD"
VANILLA_ASSET = ROOT / "output" / "vanilla" / "v2" / "mistral_lapel_layer_jacket.png"
RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
BEFORE_NATIVE = OUTPUT / "mistral_lapel_layer_jacket_hd-before-coverage.png"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _opaque_count(frame: list[list[tuple[int, int, int, int]]]) -> int:
    return sum(pixel[3] == 255 for row in frame for pixel in row)


def _is_connected(frame: list[list[tuple[int, int, int, int]]]) -> bool:
    opaque = {
        (x, y)
        for y, row in enumerate(frame)
        for x, pixel in enumerate(row)
        if pixel[3] == 255
    }
    if not opaque:
        return False
    visited = {next(iter(opaque))}
    queue = deque(visited)
    while queue:
        x, y = queue.popleft()
        for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if point in opaque and point not in visited:
                visited.add(point)
                queue.append(point)
    return visited == opaque


def _frame_from_texture(texture: dict[str, Any], y0: int, size: int) -> list[list[tuple[int, int, int, int]]]:
    return [list(row[:size]) for row in texture["pixels"][y0 : y0 + size]]


def _binary_occupancy(frame: list[list[tuple[int, int, int, int]]]) -> list[list[bool]]:
    return [[pixel[3] == 255 for pixel in row] for row in frame]


def _two_by_two_uniform_ratio(frame: list[list[tuple[int, int, int, int]]]) -> float:
    uniform = 0
    total = 0
    for y in range(0, len(frame), 2):
        for x in range(0, len(frame[0]), 2):
            block = {
                frame[y + dy][x + dx]
                for dy in range(2)
                for dx in range(2)
            }
            total += 1
            uniform += len(block) == 1
    return uniform / total


def _alpha_values(pixels: list[list[tuple[int, int, int, int]]]) -> list[int]:
    return sorted({pixel[3] for row in pixels for pixel in row})


def main() -> None:
    source_batch = _json(RECIPE_BATCH)
    source_recipe = next(recipe for recipe in source_batch["recipes"] if recipe["id"] == "lifestyle-v2-16")
    exported_recipe = _json(OUTPUT / "semantic_recipe.json")
    _assert(exported_recipe == source_recipe, "exported semantic recipe differs from V2 lifestyle-v2-16")

    rendered = render_mistral_hd_jacket(source_recipe)
    config = rendered.config
    _assert(_json(OUTPUT / "renderer_config.json") == config, "renderer config output drift")

    native_path = OUTPUT / "mistral_lapel_layer_jacket_hd.png"
    native = read_rgba_png(native_path)
    _assert((native["width"], native["height"]) == (16, 64), "FS native texture must be 16x64")
    _assert(native_path.read_bytes() == encode_rgba_png(rendered.texture), "native texture is not renderer output")
    _assert(_alpha_values(native["pixels"]) == [0, 255], "native texture must use binary alpha")
    _assert(set(native["filters"]) == {0}, "generated PNG must use explicit no-filter scanlines")

    raw_preview = read_rgba_png(OUTPUT / "mistral_lapel_layer_jacket_hd-native-8x.png")
    _assert(
        raw_preview["pixels"] == nearest_scale(native["pixels"], 8),
        "raw preview is not exact integer nearest-neighbor 8x",
    )
    default_frames = {
        direction: composite_default_frame(frame, config)
        for direction, frame in rendered.frames.items()
    }
    default_stack = []
    for direction in ("front", "right", "left", "back"):
        default_stack.extend(default_frames[direction])
    default_preview = read_rgba_png(OUTPUT / "mistral_lapel_layer_jacket_hd-default-8x.png")
    _assert(
        default_preview["pixels"] == nearest_scale(default_stack, 8),
        "default-color preview is not exact logical composite plus nearest-neighbor 8x",
    )

    pack_texture = SHIRT_FOLDER / "shirt.png"
    _assert(pack_texture.read_bytes() == native_path.read_bytes(), "test-pack texture differs from output texture")
    _assert(len(list((PACK / "Shirts").glob("*/shirt.json"))) == 1, "POC pack must contain exactly one shirt")
    _assert(not (PACK / "Sleeves").exists(), "POC must not silently add a separate sleeve appearance")

    manifest = _json(PACK / "manifest.json")
    _assert(manifest["ContentPackFor"] == {
        "UniqueID": "PeacefulEnd.FashionSense",
        "MinimumVersion": "7.5.0",
    }, "manifest must target Fashion Sense 7.5.0")
    _assert(manifest["Version"] == "1.0.2", "coverage-corrected test pack version")
    _assert("EntryDll" not in manifest, "content pack must not include an SMAPI DLL")
    _assert("Dependencies" not in manifest, "content pack needs no additional declared dependency")

    shirt = _json(SHIRT_FOLDER / "shirt.json")
    _assert(shirt["Format"] == "7.5.0", "shirt format must be 7.5.0")
    direction_contract = (
        ("FrontShirt", 0),
        ("RightShirt", 16),
        ("LeftShirt", 32),
        ("BackShirt", 48),
    )
    source_rects: list[tuple[int, int, int, int]] = []
    mask_values: list[list[int]] | None = None
    for field, y in direction_contract:
        model = shirt[field]
        _assert(model["StartingPosition"] == {"X": 0, "Y": y}, f"{field} starting position")
        _assert(model["BodyPosition"] == {"X": 0, "Y": 32}, f"{field} body position")
        _assert(model["ShirtSize"] == {"Width": 16, "Length": 16}, f"{field} size")
        _assert(model["Scale"] == 2.0, f"{field} scale")
        _assert(model.get("DisableNativeOffset", False) is False, f"{field} must retain native feature offsets")
        _assert(model["HideSleeves"] is False, f"{field} must preserve native sleeves")
        _assert(model["DisableGrayscale"] is False, f"{field} must preserve mask support")
        _assert("DrawOrderOverride" not in model, f"{field} must use framework shirt draw order")
        _assert(len(model["ColorMaskLayers"]) == 1, f"{field} must have one bounded dye layer")
        layer = model["ColorMaskLayers"][0]
        _assert(layer["Name"] == "Outer Fabric", f"{field} mask name")
        _assert(layer["DefaultColor"] == [112, 130, 145], f"{field} semantic default color")
        mask_values = layer["Values"]
        _assert(all(color in mask_values for color in model["SleeveColors"]), f"{field} sleeve tones must follow outer mask")
        source_rects.append((0, y, 16, 16))
    _assert(len(source_rects) == len(set(source_rects)), "source rectangles overlap")
    _assert(all(x + w <= native["width"] and y + h <= native["height"] for x, y, w, h in source_rects), "source rectangle outside texture")

    connected: dict[str, bool] = {}
    occupied: dict[str, int] = {}
    for direction, frame in rendered.frames.items():
        connected[direction] = _is_connected(frame)
        occupied[direction] = _opaque_count(frame)
        _assert(connected[direction], f"{direction} garment pixels are disconnected")
    _assert(all(count >= 170 for count in occupied.values()), "major garment area is too sparse")

    _assert(rendered.coverage_validation.passes, "corrected jacket fails body coverage")
    _assert(rendered.coverage_validation.required_cells == {
        "front": 40,
        "right": 36,
        "left": 36,
        "back": 44,
    }, "body-coverage envelope drift")
    _assert(not any(rendered.coverage_validation.missing_cells.values()), "corrected coverage has gaps")

    old_native = read_rgba_png(BEFORE_NATIVE)
    _assert((old_native["width"], old_native["height"]) == (16, 64), "coverage baseline must be 16x64")
    old_frames = {
        direction: _frame_from_texture(old_native, index * 16, 16)
        for index, direction in enumerate(("front", "right", "left", "back"))
    }
    old_regions = {
        direction: [
            ["OLD_GARMENT" if pixel[3] == 255 else None for pixel in row]
            for row in frame
        ]
        for direction, frame in old_frames.items()
    }
    old_coverage = validate_body_coverage(old_regions, rendered.coverage_envelopes)
    _assert(not old_coverage.passes, "pre-correction jacket unexpectedly passes coverage")
    _assert({direction: len(cells) for direction, cells in old_coverage.missing_cells.items()} == {
        "front": 10,
        "right": 7,
        "left": 7,
        "back": 12,
    }, "pre-correction coverage regression fixture drift")
    alpha_changes = {
        direction: {
            (x, y)
            for y in range(16)
            for x in range(16)
            if old_frames[direction][y][x][3] != rendered.frames[direction][y][x][3]
        }
        for direction in ("front", "right", "left", "back")
    }
    _assert(alpha_changes == {
        direction: set(old_coverage.missing_cells[direction])
        for direction in ("front", "right", "left", "back")
    }, "structural correction changed cells outside the missing coverage envelope")
    _assert(all(
        old_frames[direction][y][x][3] == 0 and rendered.frames[direction][y][x][3] == 255
        for direction, cells in alpha_changes.items()
        for x, y in cells
    ), "coverage correction must add opaque cells only")

    front_regions = {region for row in rendered.regions["front"] for region in row if region}
    back_regions = {region for row in rendered.regions["back"] for region in row if region}
    side_regions = {region for row in rendered.regions["right"] for region in row if region}
    _assert(
        {"OUTER_PANEL_LEFT", "OUTER_PANEL_RIGHT", "INNER_LAYER", "COLLAR", "HEM", "SLEEVE", "SHOULDER_CAP"} <= front_regions,
        "front loses jacket construction regions",
    )
    _assert({"YOKE", "COLLAR", "HEM", "SLEEVE", "SHOULDER_CAP"} <= back_regions, "back loses outerwear regions")
    _assert({"OUTER_PANEL_RIGHT", "INNER_LAYER", "COLLAR", "HEM", "SLEEVE", "SHOULDER_CAP"} <= side_regions, "side loses layered construction")
    front_top_width = sum(pixel[3] == 255 for pixel in rendered.frames["front"][0])
    front_mid_width = sum(pixel[3] == 255 for pixel in rendered.frames["front"][6])
    _assert(front_top_width < front_mid_width, "front shoulders remain rectangular")
    _assert(all(rendered.frames["front"][0][x][3] == 0 for x in range(6, 10)), "front neck opening is not preserved")

    vanilla_data = load_v2_data()
    vanilla_render = render_v2_recipe(source_recipe, vanilla_data)
    expected_vanilla_png = encode_rgba_png(vanilla_render.native_pixels)
    _assert(VANILLA_ASSET.read_bytes() == expected_vanilla_png, "existing vanilla output regressed or drifted")
    vanilla_frame = vanilla_render.default_composites["front"]
    fs_frame = default_frames["front"]
    vanilla_2x = nearest_scale(vanilla_frame, 2)
    _assert(fs_frame != vanilla_2x, "FS output is a forbidden nearest-neighbor upscale")
    occupancy_difference = sum(
        a != b
        for row_a, row_b in zip(_binary_occupancy(fs_frame), _binary_occupancy(vanilla_2x))
        for a, b in zip(row_a, row_b)
    )
    _assert(occupancy_difference >= 16, "FS structure differs too little from a 2x vanilla occupancy map")
    uniform_ratio = _two_by_two_uniform_ratio(fs_frame)
    _assert(uniform_ratio < 0.9, "FS frame remains suspiciously block-upscaled")

    all_colors = {pixel for row in native["pixels"] for pixel in row if pixel[3] == 255}
    grayscale_masks = {
        (value, value, value, 255) for value in config["primaryMaskRamp"].values()
    }
    _assert(grayscale_masks <= all_colors, "one or more outer mask shades are absent")
    _assert(any(not (r == g == b) for r, g, b, _ in all_colors), "fixed inner-layer palette is absent")

    validation = {
        "status": "PASS_STATIC_SOURCE_CONTRACT",
        "runtimeInGame": {
            "packLoadAndTextureDraw": "CONFIRMED_BY_USER",
            "oldAnchor": "CONFIRMED_MISALIGNED_64_DISPLAY_PIXELS_LOW",
            "correctedAnchor": "AWAITING_IN_GAME_RELOAD",
        },
        "frameworkTarget": {
            "version": "7.5.0",
            "commit": "39e9e9e13c9f9a78416172e73a229cf8703ddb59",
            "game": "Stardew Valley 1.6.15",
        },
        "scope": "one optional Fashion Sense shirt backend; no separate sleeves appearance",
        "semanticRecipe": {
            "id": source_recipe["id"],
            "unchanged": True,
            "sha256": hashlib.sha256(json.dumps(source_recipe, sort_keys=True).encode()).hexdigest(),
        },
        "density": {
            "vanillaLogicalFrame": [8, 8],
            "vanillaLogicalCells": 64,
            "vanillaScale": 4,
            "fashionSenseLogicalFrame": [16, 16],
            "fashionSenseLogicalCells": 256,
            "fashionSenseScale": 2,
            "nominalDisplayedFootprint": [32, 32],
            "logicalCellMultiplier": 4,
        },
        "anchor": {
            "stardewWorldFarmerOrigin": [0, 32],
            "oldBodyPosition": [0, 0],
            "correctedBodyPositionAllDirections": [0, 32],
            "disableNativeOffset": False,
            "nativeScale": 4,
            "fashionSenseScale": 2,
            "oldVerticalResidualDisplayPixels": 64,
            "bodyPositionCorrectionDisplayPixels": -64,
            "correctedVerticalResidualDisplayPixels": 0,
            "worldDerivation": "32 - (32 + 32) * 2 == 32 - 32 * 4",
            "uiCorrectionAtScale2": 64,
            "uiBodyPositionCompensation": -64,
            "directionSpecificOffsetsRequired": False,
        },
        "texture": {
            "dimensions": [native["width"], native["height"]],
            "rgba8": True,
            "alphaValues": _alpha_values(native["pixels"]),
            "pngFilters": sorted(set(native["filters"])),
            "sha256": native["sha256"],
            "packCopySha256": _sha256(pack_texture),
            "rawRgbaBytes": native["width"] * native["height"] * 4,
        },
        "directions": {
            "order": ["front", "right", "left", "back"],
            "sourceRectangles": source_rects,
            "connected": connected,
            "occupiedLogicalPixels": occupied,
        },
        "structure": {
            "frontRegions": sorted(front_regions),
            "backRegions": sorted(back_regions),
            "rightRegions": sorted(side_regions),
            "frontTopWidth": front_top_width,
            "frontMidWidth": front_mid_width,
            "differenceFromVanilla2xOccupancyCells": occupancy_difference,
            "twoByTwoUniformBlockRatio": round(uniform_ratio, 4),
            "nearestNeighborUpscaleRejected": True,
        },
        "bodyCoverage": {
            "status": "PASS",
            "separateFromSilhouetteScoring": True,
            "requiredCells": rendered.coverage_validation.required_cells,
            "missingAfterCorrection": {
                direction: list(cells)
                for direction, cells in rendered.coverage_validation.missing_cells.items()
            },
            "missingBeforeCorrection": {
                direction: [list(cell) for cell in cells]
                for direction, cells in old_coverage.missing_cells.items()
            },
            "addedLogicalCells": {
                direction: [list(cell) for cell in sorted(cells, key=lambda point: (point[1], point[0]))]
                for direction, cells in alpha_changes.items()
            },
            "baselineSha256": old_native["sha256"],
            "rule": "every required coverage-envelope cell must contain a structural garment region",
        },
        "color": {
            "maskLayer": "Outer Fabric",
            "maskValues": mask_values,
            "defaultColor": [112, 130, 145],
            "fixedInnerLayer": True,
            "sleeveColorsUseOuterMask": True,
        },
        "sleeves": {
            "strategy": "Fashion Sense ShirtModel.SleeveColors driving Stardew native animated arm pixels",
            "separateSleevesAppearance": False,
            "standingWalkingToolGeometry": "framework/game-owned; manual runtime verification required",
        },
        "drawOrder": {
            "override": False,
            "effectiveContract": "default Fashion Sense Shirt layer; native Sleeves layer later (back-facing sleeves moved before Hair)",
        },
        "previews": {
            "native8xExactNearest": True,
            "default8xLogicalCompositeThenExactNearest": True,
        },
        "vanillaRegression": {
            "status": "PASS",
            "asset": str(VANILLA_ASSET.relative_to(ROOT)),
            "sha256": _sha256(VANILLA_ASSET),
            "matchesCurrentVanillaRenderer": True,
        },
        "manualTestsRequired": [
            "corrected world and Hand Mirror anchors after fs_reload",
            "four-direction standing and walking",
            "basic tool and slingshot poses",
            "horseback alignment at Scale 2",
            "DefaultColor initialization and sleeve tint synchronization",
            "controller Hand Mirror usability",
            "multiplayer peer appearance",
        ],
        "beautyClaim": "Static metrics reject obvious corruption/upscaling; they do not prove attractiveness.",
    }
    (OUTPUT / "validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    print("PASS_STATIC_SOURCE_CONTRACT")
    print(json.dumps(validation["density"], indent=2))
    print(json.dumps(validation["structure"], indent=2))


if __name__ == "__main__":
    main()
