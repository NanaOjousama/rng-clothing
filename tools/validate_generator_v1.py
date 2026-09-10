#!/usr/bin/env python3
"""Independent reproducibility and static-output check for Generator V1."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.recipe_engine import (  # noqa: E402
    generate_recipes,
    load_data,
    pascal_identifier,
    review_redundancy,
    select_best_five,
    slugify,
    validate_recipe,
)
from generator.renderer import render_recipe  # noqa: E402
from generator.validator import (  # noqa: E402
    validate_exported_files,
    validate_pack,
    validate_rendered_shirt,
)


RECIPE_PATH = ROOT / "output" / "recipes" / "lifestyle_v1_recipes.json"
OUTPUT_DIR = ROOT / "output" / "vanilla" / "v1"
PACK_DIR = ROOT / "test-packs" / "vanilla" / "RNG-Clothing-V1"
VALIDATION_PATH = OUTPUT_DIR / "validation.json"


def main() -> None:
    data = load_data()
    batch = json.loads(RECIPE_PATH.read_text(encoding="utf-8"))
    recipes = generate_recipes(data, batch["seed"])
    if batch["recipes"] != recipes:
        raise AssertionError("saved 20-recipe batch is not deterministic for its recorded seed")
    if len(recipes) != 20:
        raise AssertionError(f"expected 20 recipes, found {len(recipes)}")
    invalid = {
        recipe["id"]: validate_recipe(recipe, data).errors
        for recipe in recipes
        if not validate_recipe(recipe, data).valid
    }
    if invalid:
        raise AssertionError(f"invalid recipes: {invalid}")
    redundancy = review_redundancy(recipes)
    if redundancy["exactDuplicateCount"] or redundancy["nearDuplicateCount"]:
        raise AssertionError(f"redundant recipes: {redundancy}")
    selected, _ = select_best_five(recipes, data)
    selected_ids = [recipe["id"] for recipe in selected]
    if selected_ids != batch["selection"]["selectedRecipeIds"]:
        raise AssertionError("saved selection differs from deterministic selection")

    native_paths = sorted(
        path
        for path in OUTPUT_DIR.glob("*.png")
        if not path.name.endswith("-8x.png")
        and not path.name.endswith("-directions-8x.png")
    )
    preview_paths = sorted(OUTPUT_DIR.glob("*-8x.png"))
    contact_paths = sorted(OUTPUT_DIR.glob("*-directions-8x.png"))
    # The broad *-8x glob includes directional contacts, so distinguish them.
    sheet_previews = [path for path in preview_paths if not path.name.endswith("-directions-8x.png")]
    if (len(native_paths), len(sheet_previews), len(contact_paths)) != (5, 5, 5):
        raise AssertionError(
            "expected exactly five native, five sheet-preview, and five contact PNGs; "
            f"found {(len(native_paths), len(sheet_previews), len(contact_paths))}"
        )

    records = []
    for recipe in selected:
        slug = slugify(recipe["itemName"])
        item_id = f"RNGClothing.V1.{pascal_identifier(recipe['itemName'])}"
        rendered = render_recipe(recipe, data)
        logical = validate_rendered_shirt(rendered, data)
        exported = validate_exported_files(
            rendered,
            OUTPUT_DIR / f"{slug}.png",
            OUTPUT_DIR / f"{slug}-8x.png",
            OUTPUT_DIR / f"{slug}-directions-8x.png",
            data,
        )
        if logical["status"] != "PASS" or exported["status"] != "PASS":
            raise AssertionError(
                f"{recipe['id']} failed: logical={logical['status']}, export={exported['status']}"
            )
        records.append({"itemId": item_id, "slug": slug})
    pack = validate_pack(PACK_DIR, records, OUTPUT_DIR)
    if pack["status"] != "PASS":
        raise AssertionError(f"test pack failed: {pack}")
    saved_validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
    if saved_validation["status"] != "PASS":
        raise AssertionError("saved validation report is not PASS")
    if [record["recipeId"] for record in saved_validation["selected"]] != selected_ids:
        raise AssertionError("saved validation selected IDs differ")

    print("Generator V1 independent validation: PASS")
    print("- deterministic recipes: 20")
    print("- exact/near duplicates: 0/0")
    print("- rendered shirts: exactly 5")
    print("- native/previews/contacts: 5/5/5")
    print("- Content Patcher shirts: 5")
    print("- runtime in game: UNTESTED")


if __name__ == "__main__":
    main()

