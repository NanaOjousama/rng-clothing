#!/usr/bin/env python3
"""Validate the bounded Fashion Sense HD art-grammar comparison."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, nearest_scale, read_rgba_png
from generator.renderers.fashionsense import (
    composite_art_default_frame,
    composite_default_frame,
    render_hd_art_treatment,
    render_mistral_hd_jacket,
)
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data


OUTPUT = ROOT / "output" / "fashionsense" / "art-grammar-test"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Art-Grammar-Test"
COMPARISON = ROOT / "output" / "comparisons" / "FS_ART_GRAMMAR_A_B_C.png"
CURRENT_POC = ROOT / "output" / "fashionsense" / "poc_hd_jacket" / "mistral_lapel_layer_jacket_hd.png"
VANILLA_ASSET = ROOT / "output" / "vanilla" / "v2" / "mistral_lapel_layer_jacket.png"
RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
DIRECTION_ORDER = ("front", "right", "left", "back")

SLUGS = {
    "CURRENT": "a_current",
    "STRONGER_STARDEW": "b_stronger_stardew",
    "POLISHED_HD": "c_polished_hd",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _srgb_luma(rgb) -> float:
    r, g, b = rgb[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _wcag_luma(rgb) -> float:
    channels = []
    for value in rgb[:3]:
        value /= 255
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _tint(value: int, dye: list[int]) -> tuple[int, int, int]:
    return tuple(value * channel // 255 for channel in dye)


def _opaque_points(frame) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y, row in enumerate(frame)
        for x, pixel in enumerate(row)
        if pixel[3] == 255
    }


def _component_sizes(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    result = []
    while remaining:
        queue = deque([remaining.pop()])
        size = 0
        while queue:
            x, y = queue.popleft()
            size += 1
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        result.append(size)
    return sorted(result, reverse=True)


def _role_points(role_map, role: str) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y, row in enumerate(role_map)
        for x, value in enumerate(row)
        if value == role
    }


def _stack(frames):
    rows = []
    for direction in DIRECTION_ORDER:
        rows.extend(frames[direction])
    return rows


def main() -> None:
    batch = _json(RECIPE_BATCH)
    recipe = next(value for value in batch["recipes"] if value["id"] == "lifestyle-v2-16")
    _assert(_json(OUTPUT / "semantic_recipe.json") == recipe, "semantic recipe changed")

    treatments = {
        name: render_hd_art_treatment(recipe, name) for name in SLUGS
    }
    current = treatments["CURRENT"]
    coverage_baseline = render_mistral_hd_jacket(recipe)
    stronger = treatments["STRONGER_STARDEW"]
    polished = treatments["POLISHED_HD"]
    _assert(encode_rgba_png(current.texture) == CURRENT_POC.read_bytes(), "A is not untouched current POC")
    _assert(stronger.regions == current.regions, "B changed construction instead of art roles")
    _assert(stronger.texture != polished.texture != current.texture, "treatments are not distinct")

    # C may reassign renderer-owned structural regions, but the semantic recipe,
    # silhouette, body coverage, and runtime footprint must remain identical.
    for direction in DIRECTION_ORDER:
        current_occupancy = [[value is not None for value in row] for row in current.regions[direction]]
        polished_occupancy = [[value is not None for value in row] for row in polished.regions[direction]]
        _assert(current_occupancy == polished_occupancy, f"C changed {direction} silhouette")
        # validate_body_coverage expects all four directions, so use direct
        # envelope verification for this direction.
        missing = [
            (x, y)
            for y, row in enumerate(coverage_baseline.coverage_envelopes[direction])
            for x, required in enumerate(row)
            if required and polished.regions[direction][y][x] is None
        ]
        _assert(not missing, f"C exposes required {direction} body cells: {missing}")
        _assert(all(polished.regions[direction][0][x] is None for x in range(6, 10)) if direction == "front" else True, "front neck opening closed")

    art = polished.art_config
    ramp = art["outerMaskRamp"]
    dye = art["defaultPrimaryColor"]
    role_rgb = {role: _tint(value, dye) for role, value in ramp.items()}
    requirements = art["contrastRequirements"]
    contrast = {
        "exteriorToBaseSrgb": _srgb_luma(role_rgb["BASE"]) - _srgb_luma(role_rgb["EXTERIOR_CONTOUR"]),
        "shadowToBaseSrgb": _srgb_luma(role_rgb["BASE"]) - _srgb_luma(role_rgb["SHADOW"]),
        "baseToLightSrgb": _srgb_luma(role_rgb["LIGHT"]) - _srgb_luma(role_rgb["BASE"]),
        "exteriorToBaseWcag": _wcag_luma(role_rgb["BASE"]) - _wcag_luma(role_rgb["EXTERIOR_CONTOUR"]),
    }
    _assert(contrast["exteriorToBaseSrgb"] >= requirements["minimumExteriorToBaseSrgbLuminanceDelta"], "outer contour too weak")
    _assert(contrast["shadowToBaseSrgb"] >= requirements["minimumShadowToBaseSrgbLuminanceDelta"], "shadow collapses into base")
    _assert(contrast["baseToLightSrgb"] >= requirements["minimumBaseToLightSrgbLuminanceDelta"], "light collapses into base")
    _assert(contrast["exteriorToBaseWcag"] >= requirements["minimumExteriorToBaseWcagLuminanceDelta"], "WCAG-value contour delta too weak")

    secondary = load_v2_data()["palettes"]["families"][recipe["paletteFamily"]]["secondary"]
    inner_outer_delta = abs(_srgb_luma(secondary["base"]) - _srgb_luma(role_rgb["BASE"]))
    _assert(inner_outer_delta >= requirements["minimumInnerToOuterBaseSrgbLuminanceDelta"], "inner layer collapses into outer panels")

    art_metrics = {}
    for name in ("STRONGER_STARDEW", "POLISHED_HD"):
        treatment = treatments[name]
        direction_metrics = {}
        for direction in DIRECTION_ORDER:
            frame = treatment.frames[direction]
            points = _opaque_points(frame)
            _assert(_component_sizes(points) == [len(points)], f"{name} {direction} garment disconnected")
            _assert(all(pixel[3] in {0, 255} for row in frame for pixel in row), f"{name} {direction} has semitransparency")
            highlights = _role_points(treatment.roles[direction], "OPTIONAL_HIGHLIGHT")
            _assert(len(highlights) <= art["clusterBudget"]["maximumOptionalHighlightPixelsPerDirection"], f"{name} {direction} highlight budget")
            if highlights:
                _assert(all(size >= 2 for size in _component_sizes(highlights)), f"{name} {direction} isolated highlight noise")
            default_frame = composite_art_default_frame(frame, art)
            colors = {pixel for row in default_frame for pixel in row if pixel[3] == 255}
            _assert(len(colors) <= art["clusterBudget"]["maximumOpaqueColorsAtDefaultTint"], f"{name} {direction} palette spam")
            direction_metrics[direction] = {
                "opaquePixels": len(points),
                "connectedComponents": _component_sizes(points),
                "opaqueColorsAtDefaultTint": len(colors),
                "optionalHighlightPixels": len(highlights),
                "optionalHighlightClusterSizes": _component_sizes(highlights),
            }
        art_metrics[name] = direction_metrics

    # Native logical outputs and previews.
    for name, slug in SLUGS.items():
        treatment = treatments[name]
        native_path = OUTPUT / f"{slug}.png"
        native = read_rgba_png(native_path)
        _assert((native["width"], native["height"]) == (16, 64), f"{name} native dimensions")
        _assert(native_path.read_bytes() == encode_rgba_png(treatment.texture), f"{name} native differs from logical renderer")
        _assert(set(native["filters"]) == {0}, f"{name} PNG scanline filter changed")
        _assert({pixel[3] for row in native["pixels"] for pixel in row} <= {0, 255}, f"{name} alpha not binary")
        raw_preview = read_rgba_png(OUTPUT / f"{slug}-native-8x.png")
        _assert(raw_preview["pixels"] == nearest_scale(treatment.texture, 8), f"{name} raw preview not nearest-neighbor")
        default_frames = (
            {d: composite_default_frame(f, current.backend_config) for d, f in treatment.frames.items()}
            if name == "CURRENT"
            else {d: composite_art_default_frame(f, art) for d, f in treatment.frames.items()}
        )
        default_preview = read_rgba_png(OUTPUT / f"{slug}-default-8x.png")
        _assert(default_preview["pixels"] == nearest_scale(_stack(default_frames), 8), f"{name} default preview not nearest-neighbor")

    comparison = read_rgba_png(COMPARISON)
    _assert(comparison["width"] > 0 and comparison["height"] > 0, "comparison missing")

    # Fashion Sense content pack: exactly B and C, same runtime contract.
    manifest = _json(PACK / "manifest.json")
    _assert(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "pack dependency contract")
    _assert("EntryDll" not in manifest, "test pack must not include code")
    shirt_folders = sorted((PACK / "Shirts").iterdir())
    _assert([folder.name for folder in shirt_folders] == ["MistralPolishedHD", "MistralStrongerStardew"], "pack must contain exactly B and C")
    for folder, name in ((PACK / "Shirts" / "MistralStrongerStardew", "STRONGER_STARDEW"), (PACK / "Shirts" / "MistralPolishedHD", "POLISHED_HD")):
        shirt = _json(folder / "shirt.json")
        expected_y = {"FrontShirt": 0, "RightShirt": 16, "LeftShirt": 32, "BackShirt": 48}
        for field, y in expected_y.items():
            model = shirt[field]
            _assert(model["Scale"] == 2.0, f"{name} scale changed")
            _assert(model["BodyPosition"] == {"X": 0, "Y": 32}, f"{name} anchor changed")
            _assert(model["ShirtSize"] == {"Width": 16, "Length": 16}, f"{name} size changed")
            _assert(model["StartingPosition"] == {"X": 0, "Y": y}, f"{name} direction mapping")
            _assert(model["HideSleeves"] is False, f"{name} native sleeves hidden")
            _assert("DisableNativeOffset" not in model, f"{name} native offset behavior changed")
            expected_values = [[value, value, value] for value in ramp.values()]
            _assert(model["ColorMaskLayers"][0]["Values"] == expected_values, f"{name} edge ramp missing")
            _assert(model["SleeveColors"] == [[ramp[role]] * 3 for role in art["sleeveMaskRoles"]], f"{name} sleeve ramp mismatch")
        _assert((folder / "shirt.png").read_bytes() == encode_rgba_png(treatments[name].texture), f"{name} pack texture drift")

    # Existing vanilla output remains byte-equivalent to its renderer.
    vanilla = render_v2_recipe(recipe, load_v2_data())
    _assert(VANILLA_ASSET.read_bytes() == encode_rgba_png(vanilla.native_pixels), "vanilla V2 renderer/output regressed")

    current_hash = hashlib.sha256(CURRENT_POC.read_bytes()).hexdigest()
    result = {
        "status": "PASS_STATIC_ART_AND_RUNTIME_CONTRACT",
        "beautyClaim": "NOT_AUTOMATED; requires normal-zoom human and in-game judgment",
        "runtime": {
            "framework": "Fashion Sense 7.5.0",
            "shirtSize": [16, 16],
            "scale": 2.0,
            "bodyPosition": [0, 32],
            "nativeAnimatedSleeves": True,
            "newTreatmentsInGame": "UNTESTED",
        },
        "semanticRecipe": {
            "id": recipe["id"],
            "unchanged": True,
            "sha256": hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest(),
        },
        "currentBaseline": {"untouched": True, "sha256": current_hash},
        "contrastAtDefaultDye": {key: round(value, 3) for key, value in contrast.items()} | {
            "innerToOuterBaseSrgb": round(inner_outer_delta, 3),
            "roleRgb": {key: list(value) for key, value in role_rgb.items()},
        },
        "artMetrics": art_metrics,
        "bodyCoverage": "PASS_ALL_DIRECTIONS",
        "neckOpening": "PRESERVED",
        "vanillaRendererRegression": "PASS_BYTE_EQUIVALENCE",
        "warnings": [
            "A numeric validator rejects weak contrast/noise/coverage regressions but cannot prove attractiveness.",
            "B and C still need comparison on a live Farmer at normal gameplay zoom.",
        ],
    }
    (OUTPUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
