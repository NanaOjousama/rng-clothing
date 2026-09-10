#!/usr/bin/env python3
"""Independent, non-writing reproducibility check for Generator V2."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.v2_recipe_engine import (  # noqa: E402
    generate_v2_recipes,
    load_v2_data,
    migrate_v1_recipes,
    pascal_identifier,
    review_v2_redundancy,
    slugify,
    validate_recipe_v2,
)
from generator.v2_renderer import render_v2_recipe  # noqa: E402
from generator.v2_structural import (  # noqa: E402
    StructuralGarment,
    build_structural_regions,
    control_recipes,
    validate_structural_similarity,
)
from generator.v2_validator import (  # noqa: E402
    validate_exported_v2_files,
    validate_rendered_v2,
    validate_v2_pack,
)


MIGRATED_PATH = ROOT / "output" / "recipes" / "lifestyle_v1_migrated_to_v2.json"
RECIPE_PATH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
RECIPE_VALIDATION_PATH = ROOT / "output" / "recipes" / "lifestyle_v2_recipe_validation.json"
STRUCTURAL_VALIDATION_PATH = ROOT / "output" / "structural-tests" / "v2" / "structural_validation.json"
OUTPUT_DIR = ROOT / "output" / "vanilla" / "v2"
PACK_DIR = ROOT / "test-packs" / "vanilla" / "RNG-Clothing-V2"
VALIDATION_PATH = OUTPUT_DIR / "validation.json"
RENDERED_PATH = OUTPUT_DIR / "rendered_recipes.json"
SET_B_IDS = (
    "lifestyle-v2-01",
    "lifestyle-v2-06",
    "lifestyle-v2-10",
    "lifestyle-v2-16",
    "lifestyle-v2-19",
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_png_counts() -> None:
    all_pngs = list(OUTPUT_DIR.glob("*.png"))
    contacts = [path for path in all_pngs if path.name.endswith("-directions-8x.png")]
    previews = [
        path
        for path in all_pngs
        if path.name.endswith("-8x.png")
        and not path.name.endswith("-directions-8x.png")
    ]
    comparisons = [
        OUTPUT_DIR / "V2_ARCHETYPE_COMPARISON.png",
        OUTPUT_DIR / "V2_RARITY_COMPARISON.png",
        OUTPUT_DIR / "V2_JACKET_SHOULDER_BEFORE_AFTER.png",
        OUTPUT_DIR / "V2_JACKET_SLEEVE_BEFORE_AFTER.png",
    ]
    natives = [
        path
        for path in all_pngs
        if path not in comparisons
        and not path.name.endswith("-8x.png")
        and not path.name.endswith("-directions-8x.png")
    ]
    counts = (len(natives), len(previews), len(contacts))
    if counts != (10, 10, 10):
        raise AssertionError(
            "expected exactly 10 native, 10 sheet-preview, and 10 contact PNGs; "
            f"found {counts}"
        )
    missing = [path.name for path in comparisons if not path.is_file()]
    if missing:
        raise AssertionError(f"missing required V2 comparison sheets: {missing}")


def main() -> None:
    data = load_v2_data()
    recipe_gate = _load(RECIPE_VALIDATION_PATH)
    if recipe_gate["status"] != "PASS":
        raise AssertionError("saved recipe-only gate is not PASS")

    fresh_batch = _load(RECIPE_PATH)
    fresh = generate_v2_recipes(data, fresh_batch["seed"])
    if fresh_batch["recipes"] != fresh:
        raise AssertionError("saved fresh V2 batch is not deterministic for its seed")
    if len(fresh) != 20:
        raise AssertionError(f"expected 20 fresh V2 recipes, found {len(fresh)}")
    redundancy = review_v2_redundancy(fresh)
    if redundancy["exactDuplicateCount"] or redundancy["nearDuplicateCount"]:
        raise AssertionError(f"fresh V2 recipes are redundant: {redundancy}")

    migrated_batch = _load(MIGRATED_PATH)
    migrated, _ = migrate_v1_recipes(data)
    if migrated_batch["recipes"] != migrated:
        raise AssertionError("saved V1-to-V2 migration is not deterministic")
    invalid = {
        recipe["id"]: validate_recipe_v2(recipe, data).errors
        for recipe in [*fresh, *migrated]
        if not validate_recipe_v2(recipe, data).valid
    }
    if invalid:
        raise AssertionError(f"invalid saved V2 recipes: {invalid}")

    controls = control_recipes(data)
    control_garments = [
        StructuralGarment(recipe, build_structural_regions(recipe, data))
        for recipe in controls
    ]
    structural = validate_structural_similarity(control_garments, data)
    saved_structural = _load(STRUCTURAL_VALIDATION_PATH)
    if structural["status"] != "PASS" or structural != saved_structural["similarity"]:
        raise AssertionError("saved two-color structural result is stale or failed")

    fresh_by_id = {recipe["id"]: recipe for recipe in fresh}
    selected = [*controls, *(fresh_by_id[recipe_id] for recipe_id in SET_B_IDS)]
    if len(selected) != 10:
        raise AssertionError("V2 selection does not contain exactly ten recipes")
    rarities = [fresh_by_id[recipe_id]["rarity"] for recipe_id in SET_B_IDS]
    if rarities.count("Common") != 1 or rarities.count("Uncommon") != 2 or rarities.count("Rare") != 2:
        raise AssertionError(f"Set B rarity contract failed: {rarities}")
    rare_archetypes = {
        fresh_by_id[recipe_id]["archetype"]
        for recipe_id in SET_B_IDS
        if fresh_by_id[recipe_id]["rarity"] == "Rare"
    }
    if rare_archetypes != {"JACKET", "SAILOR_TOP"}:
        raise AssertionError(f"Set B Rare archetypes are wrong: {sorted(rare_archetypes)}")

    _assert_png_counts()
    pack_records = []
    for recipe in selected:
        rendered = render_v2_recipe(recipe, data)
        logical = validate_rendered_v2(rendered, data)
        slug = slugify(recipe["itemName"])
        exported = validate_exported_v2_files(
            rendered,
            OUTPUT_DIR / f"{slug}.png",
            OUTPUT_DIR / f"{slug}-8x.png",
            OUTPUT_DIR / f"{slug}-directions-8x.png",
            data,
        )
        if logical["status"] != "PASS" or exported["status"] != "PASS":
            raise AssertionError(
                f"{recipe['id']} failed: logical={logical['status']}, "
                f"export={exported['status']}"
            )
        pack_records.append(
            {
                "itemId": f"RNGClothing.V2.{pascal_identifier(recipe['itemName'])}",
                "slug": slug,
            }
        )

    pack = validate_v2_pack(PACK_DIR, pack_records, OUTPUT_DIR)
    if pack["status"] != "PASS":
        raise AssertionError(f"test pack failed: {pack}")
    saved_rendered = _load(RENDERED_PATH)
    saved_ids = [
        recipe["id"]
        for group in (saved_rendered["setA"], saved_rendered["setB"])
        for recipe in group["recipes"]
    ]
    if saved_ids != [recipe["id"] for recipe in selected]:
        raise AssertionError("saved rendered selection differs from deterministic selection")
    saved_validation = _load(VALIDATION_PATH)
    if saved_validation["status"] != "PASS":
        raise AssertionError("saved full V2 validation is not PASS")

    print("Generator V2 independent validation: PASS")
    print("- deterministic migrated/fresh recipes: 20/20")
    print("- exact/near fresh duplicates: 0/0")
    print("- two-color archetypes/pair rejections: 5/0")
    print("- full rendered shirts: exactly 10")
    print("- native/previews/contacts: 10/10/10")
    print("- Content Patcher shirts: 10")
    print("- runtime in game: UNTESTED FOR V2")


if __name__ == "__main__":
    main()
