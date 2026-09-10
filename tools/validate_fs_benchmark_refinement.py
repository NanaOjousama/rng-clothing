#!/usr/bin/env python3
"""Validate the benchmark-informed, original Mistral refinement."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, nearest_scale, read_rgba_png
from generator.renderers.fashionsense import (
    composite_art_default_frame,
    render_hd_art_treatment,
    render_mistral_hd_jacket,
)
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data


OUTPUT = ROOT / "output" / "fashionsense" / "benchmark-refinement"
CURRENT_C = ROOT / "output" / "fashionsense" / "art-grammar-test" / "c_polished_hd.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Benchmark-Refinement-Test"
SHIRT = PACK / "Shirts" / "MistralBenchmarkRefinedHD"
RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
VANILLA_ASSET = ROOT / "output" / "vanilla" / "v2" / "mistral_lapel_layer_jacket.png"
STACK_ORDER = ("front", "right", "left", "back")
DIRECTIONS = ("front", "back", "left", "right")


def _assert(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _points(frame, predicate):
    return {
        (x, y)
        for y, row in enumerate(frame)
        for x, value in enumerate(row)
        if predicate(value)
    }


def _components(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    sizes = []
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
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _exterior(regions, x: int, y: int) -> bool:
    return any(
        nx < 0 or nx >= 16 or ny < 0 or ny >= 16 or regions[ny][nx] is None
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
    )


def _stack(frames):
    rows = []
    for direction in STACK_ORDER:
        rows.extend(frames[direction])
    return rows


def main() -> None:
    batch = _json(RECIPE_BATCH)
    recipe = next(item for item in batch["recipes"] if item["id"] == "lifestyle-v2-16")
    current = render_hd_art_treatment(recipe, "POLISHED_HD")
    refined = render_hd_art_treatment(recipe, "BENCHMARK_REFINED")
    coverage_baseline = render_mistral_hd_jacket(recipe)

    _assert(_json(OUTPUT / "semantic_recipe.json") == recipe, "semantic recipe changed")
    _assert(CURRENT_C.read_bytes() == encode_rgba_png(current.texture), "current C baseline drift")
    _assert((OUTPUT / "current_polished_hd.png").read_bytes() == CURRENT_C.read_bytes(), "exported current is not untouched C")
    _assert(refined.regions == current.regions, "refinement changed structural regions")
    _assert(refined.texture != current.texture, "refinement made no art-role changes")

    # The render backend has no access to the benchmark directory. Only the
    # analysis tool may read those packs.
    renderer_source = (ROOT / "generator" / "renderers" / "fashionsense" / "hd_art_grammar.py").read_text(encoding="utf-8")
    generator_source = (ROOT / "tools" / "generate_fs_benchmark_refinement.py").read_text(encoding="utf-8")
    _assert("references/benchmark" not in renderer_source, "renderer reads benchmark assets")
    _assert("references/benchmark" not in generator_source, "output generator reads benchmark assets")

    art_metrics = {}
    for direction in DIRECTIONS:
        regions = refined.regions[direction]
        roles = refined.roles[direction]
        frame = refined.frames[direction]
        occupancy = _points(regions, lambda value: value is not None)
        current_occupancy = _points(current.regions[direction], lambda value: value is not None)
        _assert(occupancy == current_occupancy, f"{direction} silhouette changed")
        _assert(_components(occupancy) == [len(occupancy)], f"{direction} garment disconnected")

        missing = [
            (x, y)
            for y, row in enumerate(coverage_baseline.coverage_envelopes[direction])
            for x, required in enumerate(row)
            if required and regions[y][x] is None
        ]
        _assert(not missing, f"{direction} body exposure: {missing}")

        exterior = {(x, y) for x, y in occupancy if _exterior(regions, x, y)}
        contour = _points(roles, lambda value: value == "EXTERIOR_CONTOUR") & exterior
        contour_share = len(contour) / len(exterior)
        _assert(0.75 <= contour_share < 1.0, f"{direction} contour is weak or uniformly automatic")
        highlights = _points(roles, lambda value: value == "OPTIONAL_HIGHLIGHT")
        _assert(len(highlights) <= 3, f"{direction} highlight budget exceeded")
        if highlights:
            _assert(_components(highlights) == [len(highlights)], f"{direction} highlight is noisy/disconnected")

        default = composite_art_default_frame(frame, refined.art_config)
        colors = {pixel for row in default for pixel in row if pixel[3] == 255}
        _assert(len(colors) <= 10, f"{direction} palette exceeds Stardew blend budget")
        _assert({pixel[3] for row in frame for pixel in row} <= {0, 255}, f"{direction} semitransparent pixel")
        art_metrics[direction] = {
            "occupiedPixels": len(occupancy),
            "connectedComponents": _components(occupancy),
            "exteriorPixels": len(exterior),
            "darkestContourAnchorPixels": len(contour),
            "darkestContourAnchorShare": round(contour_share, 4),
            "optionalHighlightPixels": len(highlights),
            "defaultTintOpaqueColors": len(colors),
            "changedRoleCellsFromCurrent": sum(
                refined.roles[direction][y][x] != current.roles[direction][y][x]
                for y in range(16)
                for x in range(16)
            ),
        }

    _assert(all(refined.regions["front"][0][x] is None for x in range(6, 10)), "front neck opening closed")

    native_path = OUTPUT / "mistral_benchmark_refined_hd.png"
    native = read_rgba_png(native_path)
    _assert((native["width"], native["height"]) == (16, 64), "native texture must be 16x64")
    _assert(native_path.read_bytes() == encode_rgba_png(refined.texture), "native output differs from logical renderer")
    _assert(set(native["filters"]) == {0}, "PNG writer applied a scanline filter")
    _assert({pixel[3] for row in native["pixels"] for pixel in row} <= {0, 255}, "native alpha is not binary")
    default_frames = {
        direction: composite_art_default_frame(frame, refined.art_config)
        for direction, frame in refined.frames.items()
    }
    preview = read_rgba_png(OUTPUT / "mistral_benchmark_refined_hd-default-8x.png")
    _assert(preview["pixels"] == nearest_scale(_stack(default_frames), 8), "preview is not exact nearest-neighbor")

    manifest = _json(PACK / "manifest.json")
    _assert(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "pack dependency contract")
    _assert("EntryDll" not in manifest, "test pack must remain content-only")
    _assert(len(list((PACK / "Shirts").glob("*/shirt.json"))) == 1, "pack must contain one controlled shirt")
    _assert((SHIRT / "shirt.png").read_bytes() == native_path.read_bytes(), "pack texture differs from output")
    shirt = _json(SHIRT / "shirt.json")
    ramp = refined.art_config["outerMaskRamp"]
    for field, y in (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48)):
        model = shirt[field]
        _assert(model["StartingPosition"] == {"X": 0, "Y": y}, f"{field} source mapping")
        _assert(model["ShirtSize"] == {"Width": 16, "Length": 16}, f"{field} size")
        _assert(model["Scale"] == 2.0, f"{field} scale")
        _assert(model["BodyPosition"] == {"X": 0, "Y": 32}, f"{field} anchor")
        _assert(model["HideSleeves"] is False, f"{field} native sleeves hidden")
        _assert(model["SleeveColors"] == [[ramp[role]] * 3 for role in refined.art_config["sleeveMaskRoles"]], f"{field} sleeve integration")

    vanilla = render_v2_recipe(recipe, load_v2_data())
    _assert(VANILLA_ASSET.read_bytes() == encode_rgba_png(vanilla.native_pixels), "vanilla renderer/output regressed")

    result = {
        "status": "PASS_STATIC_BENCHMARK_REFINEMENT_CONTRACT",
        "beautyClaim": "PROVISIONAL_OFFLINE_ONLY",
        "semanticRecipe": {
            "id": recipe["id"],
            "unchanged": True,
            "sha256": hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest(),
        },
        "runtime": {
            "FashionSense": "7.5.0",
            "logicalFrame": [16, 16],
            "Scale": 2.0,
            "BodyPosition": [0, 32],
            "nativeAnimatedSleeves": True,
            "refinedAssetInGame": "UNTESTED",
        },
        "benchmarkIsolation": {
            "rendererReadsBenchmarkAssets": False,
            "outputGeneratorReadsBenchmarkAssets": False,
            "benchmarkPixelsCopied": False,
        },
        "artMetrics": art_metrics,
        "bodyCoverage": "PASS_ALL_DIRECTIONS",
        "neckOpening": "PRESERVED",
        "currentBaseline": "BYTE_IDENTICAL",
        "vanillaRegression": "PASS_BYTE_EQUIVALENCE",
        "warning": "Metrics verify restraint, coverage, and hierarchy; they do not prove community-level beauty.",
    }
    (OUTPUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
