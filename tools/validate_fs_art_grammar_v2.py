#!/usr/bin/env python3
"""Validate the permanent four-archetype Fashion Sense HD grammar control set."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, nearest_scale, read_rgba_png
from generator.renderers.fashionsense import (
    diagnose_fs_hd_render,
    load_hd_garment_grammar_v2,
    render_fs_hd_v2,
    select_side_template,
)
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data, validate_recipe_v2


RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
OUTPUT = ROOT / "output" / "fashionsense" / "art-grammar-v2"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Art-Grammar-V2"
COMPARISON = ROOT / "output" / "comparisons" / "FS_ART_GRAMMAR_V2_COMPARISON.png"
SELECTED = {
    "lifestyle-v2-16": ("mistral_permanent_hd", "JACKET", "MistralPermanentHd"),
    "lifestyle-v2-11": ("harbor_yoke_work_shirt_hd", "BUTTON_SHIRT", "HarborYokeWorkShirtHd"),
    "lifestyle-v2-19": ("garnet_yoke_top_hd", "SAILOR_TOP", "GarnetYokeTopHd"),
    "lifestyle-v2-05": ("hearth_ribbed_sweater_hd", "SWEATER", "HearthRibbedSweaterHd"),
}
STACK_ORDER = ("front", "right", "left", "back")


def _assert(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _stack(frames):
    return [row for direction in STACK_ORDER for row in frames[direction]]


def main() -> None:
    batch = _json(RECIPE_BATCH)
    recipe_map = {recipe["id"]: recipe for recipe in batch["recipes"]}
    selected_export = _json(OUTPUT / "selected_recipes.json")
    _assert(selected_export["semanticRecipesUnchanged"] is True, "recipe export contract missing")
    _assert(selected_export["recipes"] == [recipe_map[key] for key in SELECTED], "selected recipes changed or reordered")

    data = load_v2_data()
    config = load_hd_garment_grammar_v2()
    _assert(config["logicalFrame"] == [16, 16], "logical frame drift")
    _assert(config["scale"] == 2.0, "Scale drift")
    _assert(config["bodyPosition"] == {"X": 0, "Y": 32}, "BodyPosition drift")
    _assert(config["lightPolicy"]["direction"] == "screen_upper_left", "global lighting policy missing")
    _assert(config["edgePolicy"]["blanketTwoCellBorder"] is False, "blanket outline enabled")
    _assert(len(config["archetypes"]["JACKET"]["sideTemplates"]) >= 3, "jacket needs three side templates")
    _assert(len(config["archetypes"]["BUTTON_SHIRT"]["sideTemplates"]) >= 2, "button shirt side templates missing")
    _assert(len(config["archetypes"]["SAILOR_TOP"]["sideTemplates"]) >= 2, "sailor side templates missing")

    permanent_source = (ROOT / "generator" / "renderers" / "fashionsense" / "hd_garment_v2.py").read_text(encoding="utf-8")
    output_source = (ROOT / "tools" / "generate_fs_art_grammar_v2.py").read_text(encoding="utf-8")
    _assert("references/benchmark" not in permanent_source, "permanent renderer samples benchmark packs")
    _assert("references/benchmark" not in output_source, "output generator samples benchmark packs")

    validation = _json(OUTPUT / "validation.json")
    _assert(
        validation["status"] in {"PASS", "PASS_PERMANENT_FS_HD_GRAMMAR_STATIC_CONTRACT"},
        "generated validation status",
    )
    _assert(validation["beautyClaim"] == "PROVISIONAL_STATIC_REVIEW_ONLY", "metrics must not claim beauty")
    _assert(len(validation["garments"]) == 4, "control set must contain four garments")

    metrics = []
    vanilla_hashes = {}
    for recipe_id, (slug, archetype, pack_dir) in SELECTED.items():
        recipe = recipe_map[recipe_id]
        _assert(recipe["archetype"] == archetype, f"{recipe_id}: archetype drift")
        recipe_validation = validate_recipe_v2(recipe, data)
        _assert(recipe_validation.valid, f"{recipe_id}: invalid semantic recipe")
        render = render_fs_hd_v2(recipe)
        rerender = render_fs_hd_v2(recipe)
        _assert(render.texture == rerender.texture, f"{recipe_id}: nondeterministic pixels")
        _assert(render.side_template == select_side_template(recipe, config), f"{recipe_id}: nondeterministic side selection")
        diagnostics = diagnose_fs_hd_render(render)
        _assert(diagnostics.passes, f"{recipe_id}: diagnostics failed {diagnostics.errors}")
        _assert(not diagnostics.warnings, f"{recipe_id}: unresolved warnings {diagnostics.warnings}")
        _assert(not any(render.coverage_missing.values()), f"{recipe_id}: body coverage regression")
        _assert(all(render.regions["front"][0][x] is None for x in range(6, 10)), f"{recipe_id}: neck opening closed")

        native_path = OUTPUT / f"{slug}.png"
        native = read_rgba_png(native_path)
        _assert((native["width"], native["height"]) == (16, 64), f"{slug}: native dimensions")
        _assert(native_path.read_bytes() == encode_rgba_png(render.texture), f"{slug}: output differs from logical renderer")
        _assert(set(native["filters"]) == {0}, f"{slug}: unexpected PNG scanline filter")
        _assert({pixel[3] for row in native["pixels"] for pixel in row} <= {0, 255}, f"{slug}: alpha is not binary")
        preview = read_rgba_png(OUTPUT / f"{slug}-default-8x.png")
        _assert(preview["pixels"] == nearest_scale(_stack(render.default_frames), 8), f"{slug}: preview is not exact NN")
        _assert(_json(OUTPUT / f"{slug}-recipe.json") == recipe, f"{slug}: recipe export drift")

        shirt_dir = PACK / "Shirts" / pack_dir
        shirt = _json(shirt_dir / "shirt.json")
        _assert((shirt_dir / "shirt.png").read_bytes() == native_path.read_bytes(), f"{slug}: pack/output texture mismatch")
        expected_values = [[config["outerMaskRamp"][role]] * 3 for role in render.active_main_roles]
        expected_sleeves = [[config["outerMaskRamp"][role]] * 3 for role in config["sleeveMaskRoles"]]
        for field, y in (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48)):
            model = shirt[field]
            _assert(model["Scale"] == 2.0, f"{slug}/{field}: Scale")
            _assert(model["BodyPosition"] == {"X": 0, "Y": 32}, f"{slug}/{field}: BodyPosition")
            _assert(model["StartingPosition"] == {"X": 0, "Y": y}, f"{slug}/{field}: direction mapping")
            _assert(model["ShirtSize"] == {"Width": 16, "Length": 16}, f"{slug}/{field}: ShirtSize")
            _assert(model["HideSleeves"] is False, f"{slug}/{field}: native sleeves hidden")
            _assert(model["DisableGrayscale"] is False, f"{slug}/{field}: grayscale disabled")
            _assert(model["ColorMaskLayers"][0]["Values"] == expected_values, f"{slug}/{field}: shade role mask")
            _assert(model["SleeveColors"] == expected_sleeves, f"{slug}/{field}: sleeve colors")

        vanilla = render_v2_recipe(recipe, data)
        vanilla_hashes[recipe_id] = hashlib.sha256(encode_rgba_png(vanilla.native_pixels)).hexdigest()
        metrics.append({
            "recipeId": recipe_id,
            "archetype": archetype,
            "sideTemplate": render.side_template,
            "activeMainRoles": list(render.active_main_roles),
            "diagnostics": diagnostics.metrics,
        })

    manifest = _json(PACK / "manifest.json")
    _assert(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "Fashion Sense dependency")
    _assert("EntryDll" not in manifest, "test pack must remain content-only")
    _assert(len(list((PACK / "Shirts").glob("*/shirt.json"))) == 4, "test pack must contain four shirts")
    comparison = read_rgba_png(COMPARISON)
    _assert(comparison["width"] > 0 and comparison["height"] > 0, "comparison missing")

    result = {
        "status": "PASS_PERMANENT_FS_HD_GRAMMAR_STATIC_CONTRACT",
        "beautyClaim": "PROVISIONAL_STATIC_REVIEW_ONLY",
        "semanticRecipes": "UNCHANGED_EXISTING_V2_RECIPES",
        "runtime": {
            "FashionSense": "7.5.0",
            "logicalFrame": [16, 16],
            "Scale": 2.0,
            "BodyPosition": [0, 32],
            "nativeAnimatedSleeves": True,
            "inGameTestOfThisFourGarmentSet": "PENDING",
        },
        "benchmarkIsolation": {
            "rendererReadsBenchmarkPacks": False,
            "outputGeneratorReadsBenchmarkPacks": False,
            "benchmarkPixelsCopied": False,
        },
        "garments": metrics,
        "vanillaRegression": {
            "rendererInvokedSuccessfullyForAllFourUnchangedRecipes": True,
            "logicalNativePngSha256": vanilla_hashes,
        },
        "guardrails": "PASS_ALL_FOUR_WITH_NO_WARNINGS",
        "warning": "Static diagnostics reject collapse, gaps, noise risks, and hierarchy violations; they do not prove artistic parity or runtime beauty.",
    }
    _write_json(OUTPUT / "validation.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
