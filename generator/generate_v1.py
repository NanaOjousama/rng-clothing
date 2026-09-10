#!/usr/bin/env python3
"""Build Generator V1 recipes, five vanilla shirts, and an isolated test pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generator import GENERATOR_VERSION
from generator.png_utils import nearest_scale, read_rgba_png, write_rgba_png
from generator.recipe_engine import (
    ARCHETYPE_ORDER,
    GENERATOR_SEED,
    generate_recipes,
    load_data,
    pascal_identifier,
    recipe_details,
    review_redundancy,
    select_best_five,
    slugify,
    validate_recipe,
)
from generator.renderer import composite_direction, make_contact_sheet, render_recipe
from generator.validator import validate_exported_files, validate_pack, validate_rendered_shirt


ROOT = Path(__file__).resolve().parents[1]
RECIPE_OUTPUT = ROOT / "output" / "recipes" / "lifestyle_v1_recipes.json"
VANILLA_OUTPUT = ROOT / "output" / "vanilla" / "v1"
PACK_DIR = ROOT / "test-packs" / "vanilla" / "RNG-Clothing-V1"
RECIPE_REPORT = ROOT / "reports" / "RECIPE_BATCH_V1.md"
FINAL_REPORT = ROOT / "reports" / "GENERATOR_V1.md"
VALIDATION_PATH = VANILLA_OUTPUT / "validation.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _detail_text(recipe: dict[str, Any]) -> str:
    details = recipe_details(recipe)
    return ", ".join(details) if details else "none"


def build_recipe_report(
    recipes: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    reasons: dict[str, str],
    compatibility: dict[str, Any],
    redundancy: dict[str, Any],
) -> str:
    selected_ids = {recipe["id"] for recipe in selected}
    lines = [
        "# Lifestyle recipe batch V1",
        "",
        f"Generator version: `{GENERATOR_VERSION}`  ",
        f"Deterministic seed: `{recipes[0]['seed'] - 7919}`  ",
        "Scope: 20 semantic Lifestyle recipes; exactly five selected for rendering.",
        "",
        "Recipes contain no pixel coordinates. All coordinates belong to the renderer grammar.",
        "",
        "## Automated review",
        "",
        f"- Compatibility: **{'PASS' if compatibility['allValid'] else 'FAIL'}** "
        f"({compatibility['validCount']}/20 valid).",
        f"- Exact duplicate recipes: {redundancy['exactDuplicateCount']}.",
        f"- Near-duplicate structures: {redundancy['nearDuplicateCount']}.",
        f"- Minimum accepted within-archetype semantic distance: "
        f"{redundancy['minimumAcceptedSemanticDistanceWithinArchetype']} fields.",
        f"- Minimum accepted within-archetype visible-structure distance: "
        f"{redundancy['minimumAcceptedVisualStructureDistanceWithinArchetype']} fields.",
        "- Categories and rarity remain separate: every recipe is Lifestyle; rarity is Common, Uncommon, or Rare metadata.",
        "",
        "## Twenty concepts",
        "",
        "| # | Render | Name | Archetype | Rarity | Fit | Neck / collar | Closure | Detail(s) | Pattern | Palette | Accent |",
        "|---:|:---:|---|---|---|---|---|---|---|---|---|---|",
    ]
    for recipe in recipes:
        lines.append(
            "| {generationIndex} | {selected} | {itemName} | {archetype} | {rarity} | "
            "{fit} | {neckline} / {collar} | {closure} | {details} | {pattern} | "
            "{paletteFamily} | {accent} |".format(
                selected="✓" if recipe["id"] in selected_ids else "",
                details=_detail_text(recipe),
                **recipe,
            )
        )
    lines.extend(["", "## Selected five", ""])
    for recipe in selected:
        lines.extend(
            [
                f"### {recipe['itemName']} (`{recipe['id']}`)",
                "",
                reasons[recipe["id"]],
                "",
                f"Recipe: {recipe['archetype']}, {recipe['fit']}, {recipe['neckline']} neckline, "
                f"{recipe['collar']} collar, {recipe['closure']} closure, "
                f"details {_detail_text(recipe)}, {recipe['pattern']} pattern, "
                f"{recipe['paletteFamily']} palette, {recipe['rarity']}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Review boundary",
            "",
            "Compatibility and redundancy checks reject illegal or repetitive recipes. They do not prove that a rendered shirt is attractive. The five rendered contacts still require human visual review.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pack(records: list[dict[str, Any]], data: dict[str, Any]) -> None:
    assets_dir = PACK_DIR / "assets"
    i18n_dir = PACK_DIR / "i18n"
    assets_dir.mkdir(parents=True, exist_ok=True)
    i18n_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "Name": "RNG Clothing V1 - Vanilla Shirts",
        "Author": "RNG Clothing feasibility project",
        "Version": "1.0.0",
        "Description": "Five deterministic logical-pixel vanilla shirt prototypes.",
        "UniqueID": "RNGClothing.V1",
        "MinimumApiVersion": "4.0.0",
        "ContentPackFor": {
            "UniqueID": "Pathoschild.ContentPatcher",
            "MinimumVersion": "2.8.0",
        },
    }
    changes = []
    entries = {}
    i18n = {}
    for record in records:
        recipe = record["recipe"]
        slug = record["slug"]
        target = record["textureAsset"]
        changes.append(
            {
                "LogName": f"Load {recipe['itemName']} shirt texture",
                "Action": "Load",
                "Target": target,
                "FromFile": f"assets/{slug}.png",
            }
        )
        default_dye = data["palettes"]["families"][recipe["paletteFamily"]]["defaultDye"]
        entries[record["itemId"]] = {
            "Name": record["itemId"],
            "DisplayName": f"{{{{i18n:shirts.{slug}.name}}}}",
            "Description": f"{{{{i18n:shirts.{slug}.description}}}}",
            "Price": 250,
            "Texture": target,
            "SpriteIndex": 0,
            "DefaultColor": " ".join(str(channel) for channel in default_dye),
            "CanBeDyed": True,
            "IsPrismatic": False,
            "HasSleeves": True,
            "CanChooseDuringCharacterCustomization": False,
            "CustomFields": {
                "RNGClothing/Category": recipe["category"],
                "RNGClothing/Rarity": recipe["rarity"],
                "RNGClothing/RecipeId": recipe["id"],
                "RNGClothing/GeneratorVersion": GENERATOR_VERSION,
            },
        }
        i18n[f"shirts.{slug}.name"] = recipe["itemName"]
        i18n[f"shirts.{slug}.description"] = recipe["itemDescription"]
        source = VANILLA_OUTPUT / f"{slug}.png"
        (assets_dir / f"{slug}.png").write_bytes(source.read_bytes())
    changes.append(
        {
            "LogName": "Register RNG Clothing V1 vanilla shirts",
            "Action": "EditData",
            "Target": "Data/Shirts",
            "Entries": entries,
        }
    )
    content = {"Format": "2.8.0", "Changes": changes}
    write_json(PACK_DIR / "manifest.json", manifest)
    write_json(PACK_DIR / "content.json", content)
    write_json(i18n_dir / "default.json", i18n)

    commands = "\n".join(f"player_add (S){record['itemId']}" for record in records)
    readme = f"""# RNG Clothing V1 isolated test pack

This pack registers exactly five native Stardew Valley shirts. It requires SMAPI and Content Patcher. It does not require Fashion Sense.

## Install

1. Copy the entire `RNG-Clothing-V1` folder into your Stardew Valley `Mods` folder.
2. Launch the game through SMAPI.
3. Load a test save.

Do not copy only the `assets` folder; Content Patcher needs the manifest, content file, localization file, and assets together.

## Obtain the shirts

Enter these commands in the SMAPI console (Console Commands is included with a normal SMAPI installation):

```text
{commands}
```

Each command adds the shirt item to inventory. Move it into the shirt equipment slot to test it. Use the sewing-machine dye pots or another normal vanilla dye workflow to test color changes.

## Test focus

- front, back, left, and right while standing and walking;
- tool-use offsets;
- inventory icon/readability;
- light and dark dye choices;
- save/reload;
- both Farmer body presentations you normally use.

Static file validation passes, but in-game testing has not been performed by the generator.
"""
    (PACK_DIR / "README.md").write_text(readme, encoding="utf-8")


def build_final_report(
    recipes: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    records: list[dict[str, Any]],
    validation: dict[str, Any],
) -> str:
    item_rows = []
    for record in records:
        recipe = record["recipe"]
        result = validation["shirts"][recipe["id"]]
        item_rows.append(
            f"| {recipe['itemName']} | {recipe['archetype']} | {recipe['rarity']} | "
            f"{recipe['paletteFamily']} | {result['status']} | {result['diagnosticScore']:.1f} |"
        )
    commands = "\n".join(f"player_add (S){record['itemId']}" for record in records)
    selected_names = ", ".join(recipe["itemName"] for recipe in selected)
    return f"""# Generator V1 completion report

Generator version: `{GENERATOR_VERSION}`  
Deterministic seed: `{validation['seed']}`  
Scope: vanilla Stardew Valley shirts only.

## 1. Vanilla shirt grammar learned

V1 was grounded in 34 installed vanilla shirts (136 direction frames). The sample established the recurring connected 53–64-pixel garment field, centered shoulder/neck gap, compressed side geometry, simpler backs, edge/under-collar shadows, attached highlight clusters, sparse accents, and a median six rendered colors. Exact evidence and limits are in `reports/VANILLA_SHIRT_GRAMMAR.md` and `generator/data/vanilla_shirt_grammar.json`.

## 2. Archetypes implemented

Exactly five semantic archetypes exist: `T_SHIRT`, `SWEATER`, `BUTTON_SHIRT`, `JACKET`, and `SAILOR_TOP`. Each data file declares valid necklines, collars, closures, fits, details, patterns, directional structure, shading intent, and incompatibilities. Recipes never contain coordinates.

## 3. Palette and shading approach

Eight authored Lifestyle palette families are available. Main fabric uses the single native grayscale dye mask with a five-step restrained ramp; Common items collapse the brightest step to keep their palette smaller. Secondary cloth and one optional accent remain protected in the base half. No RGB auto-lightening, gradients, antialiasing, resampling, high-resolution source art, or downscaling occurs.

## 4. Recipe compatibility system

Components carry archetype allowlists, requirements, and exclusions. The validator rejects invalid collar/neckline, closure/detail, layer/pattern, accent, rarity, and two-detail combinations before rendering. The batch also enforces minimum semantic and visible-structure distance within each archetype.

## 5. Twenty generated recipes

The deterministic batch contains exactly {len(recipes)} compatible Lifestyle recipes: four per archetype, spanning all eight palette families and Common/Uncommon/Rare. Exact duplicates: {validation['recipeReview']['redundancy']['exactDuplicateCount']}; near-duplicate structures: {validation['recipeReview']['redundancy']['nearDuplicateCount']}.

See `output/recipes/lifestyle_v1_recipes.json` and `reports/RECIPE_BATCH_V1.md`.

## 6. Five selected and why

The selection is one recipe per archetype: {selected_names}. It deliberately varies palette, neck/closure landmark, construction mass, rarity, and visible detail. The sweater and button shirt use quieter Common recipes so the final set does not mistake extra stripes for quality; the jacket and sailor top carry the denser layered/collar tests.

## 7. Rendered shirts

| Shirt | Archetype | Rarity | Palette | Validation | Rejection score* |
|---|---|---|---|---|---:|
{chr(10).join(item_rows)}

*The score only summarizes obvious-failure checks. It does not prove beauty.

## 8. Validation results

Overall static result: **{validation['status']}**.

- every native PNG is exactly 256×32 RGBA8 with only alpha 0/255;
- all art is authored directly on four 8×8 logical grids;
- base frames occupy `x=0..7`, dye masks occupy `x=128..135`, with no spill or V1 overlap;
- front/right/left/back sit at `y=0/8/16/24`;
- dye masks are grayscale and use only the declared ramp;
- front sleeve sample cells are opaque and ordered dark/mid/light for the installed 1.6.15 renderer;
- every garment is connected, within occupied/color/accent budgets, and directionally consistent;
- every 8× preview is verified exact nearest-neighbor replication of the saved native PNG;
- the Content Patcher pack contains exactly five loads and five localization-ready `Data/Shirts` entries;
- pack PNGs are byte-identical to the approved output PNGs.

Not confirmed: actual in-game loading, movement/tool offsets, extreme dye choices, save/reload, or multiplayer. Static validation cannot substitute for those tests.

## 9. Files created

- grammar/component/palette/budget data under `generator/data/`;
- individual recipe schema at `generator/schema/garment_recipe.schema.json`;
- deterministic Python pipeline under `generator/`;
- independent checker at `tools/validate_generator_v1.py`;
- 20-recipe batch under `output/recipes/`;
- five native PNGs, five exact 8× sheet previews, five labeled direction contacts, and validation JSON under `output/vanilla/v1/`;
- one isolated Content Patcher pack under `test-packs/vanilla/RNG-Clothing-V1/`;
- grammar, recipe-batch, and V1 reports under `reports/`.

No Farmer composite was created. The installed Farmer base is an XNB, and the available unpack helper required a graphics device unavailable in this isolated environment. Using a Fashion Sense body, a modded body, or a reference-image Farmer would have invented a non-authoritative alignment. The labeled native contacts are therefore the honest preview boundary for V1.

## 10. Test-pack installation

Copy the entire folder:

```text
test-packs/vanilla/RNG-Clothing-V1/
```

into your normal Stardew Valley `Mods` directory, then launch through SMAPI. This project did not copy or install it automatically.

Use these SMAPI console commands:

```text
{commands}
```

Move each resulting item into the native shirt slot. Full instructions are also in the pack's `README.md`.

## 11. What remains programmer-art-like

- The shared vanilla-aligned outer contour is necessarily similar across archetypes; garment identity lives in only a handful of interior cells.
- Back and side views are coherent but intentionally quieter, so the T-shirt and button shirt can look generic from behind.
- The sweater's knit identity is a neck/hem/value-mass suggestion, not literal texture.
- The sailor top's high-contrast yoke is clear but still close to the abstraction limit of 8×8.
- The chest pin/pocket cue on the tee is intentionally tiny and may read differently at different display scaling.

## 12. Where human judgment is still required

Automated checks cannot judge whether a collar feels elegant, whether a palette is emotionally appealing, or whether two clean designs are still too similar. Human review remains necessary for batch curation, accent placement, names, default dye color, and actual Farmer-body screenshots. Extreme player dyes may also undermine a protected secondary relationship even when luminance at the authored default passes.

## 13. Comparison with the Juniper Trail Cardigan POC

V1 is a material systems improvement: it replaces one hand-authored fixed grid with reusable grammar, legal semantic recipes, deterministic batch diversity, five archetypes, directional construction, palette roles, complexity rejection, repeatable export, and one five-item pack. Visually, the selected set is broader and cleaner than a palette-variant batch would have been.

The comparison is not a blanket claim that every V1 item is more art-directed than Juniper Trail Cardigan. The POC benefited from hand-tuning one garment; V1's quiet sweater and button shirt remain more generic. The promising result is that the jacket and broad-collar top retain deliberate identities while coming from shared rules. V1 passes the static technical test and, after three logical-grid review passes, passes the preliminary visual-quality bar for an in-game test—but final art success remains **untested until viewed on the real Farmer in motion**.

## Stop condition

V1 ends here. No pants, hats, Fashion Sense content, reward integration, TFWR changes, scraping, machine learning, GUI, or additional rendered shirts were added.
"""


def generate(seed: int = GENERATOR_SEED) -> dict[str, Any]:
    data = load_data()
    recipes = generate_recipes(data, seed)
    validations = {recipe["id"]: validate_recipe(recipe, data) for recipe in recipes}
    compatibility = {
        "allValid": all(result.valid for result in validations.values()),
        "validCount": sum(result.valid for result in validations.values()),
        "invalid": {
            recipe_id: list(result.errors)
            for recipe_id, result in validations.items()
            if not result.valid
        },
        "warnings": {
            recipe_id: list(result.warnings)
            for recipe_id, result in validations.items()
            if result.warnings
        },
    }
    if not compatibility["allValid"]:
        raise RuntimeError(f"recipe batch failed compatibility: {compatibility['invalid']}")
    redundancy = review_redundancy(recipes)
    if redundancy["exactDuplicateCount"] or redundancy["nearDuplicateCount"]:
        raise RuntimeError(f"recipe batch failed redundancy review: {redundancy}")
    selected, reasons = select_best_five(recipes, data)
    selected_ids = [recipe["id"] for recipe in selected]

    batch = {
        "formatVersion": 1,
        "generatorVersion": GENERATOR_VERSION,
        "seed": seed,
        "scope": "Lifestyle / vanilla Stardew shirts only",
        "recipeCount": len(recipes),
        "compatibilityReview": compatibility,
        "redundancyReview": redundancy,
        "selection": {"selectedRecipeIds": selected_ids, "reasons": reasons},
        "recipes": recipes,
    }
    write_json(RECIPE_OUTPUT, batch)
    RECIPE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    RECIPE_REPORT.write_text(
        build_recipe_report(recipes, selected, reasons, compatibility, redundancy),
        encoding="utf-8",
    )

    VANILLA_OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    rendered_by_id = {}
    for recipe in selected:
        rendered = render_recipe(recipe, data)
        slug = slugify(recipe["itemName"])
        item_id = f"RNGClothing.V1.{pascal_identifier(recipe['itemName'])}"
        texture_asset = f"Mods/RNGClothing/V1/{pascal_identifier(recipe['itemName'])}/Shirts"
        native_path = VANILLA_OUTPUT / f"{slug}.png"
        preview_path = VANILLA_OUTPUT / f"{slug}-8x.png"
        contact_path = VANILLA_OUTPUT / f"{slug}-directions-8x.png"
        write_rgba_png(native_path, rendered.native_pixels)
        native_from_disk = read_rgba_png(native_path)
        write_rgba_png(preview_path, nearest_scale(native_from_disk["pixels"], 8))
        disk_composites = {
            direction: composite_direction(native_from_disk["pixels"], direction, recipe, data)
            for direction in ("front", "right", "left", "back")
        }
        write_rgba_png(contact_path, make_contact_sheet(disk_composites, recipe["itemName"]))
        record = {
            "recipe": recipe,
            "slug": slug,
            "itemId": item_id,
            "textureAsset": texture_asset,
            "nativePath": native_path,
            "previewPath": preview_path,
            "contactPath": contact_path,
        }
        records.append(record)
        rendered_by_id[recipe["id"]] = rendered
    if len(records) != 5:
        raise RuntimeError("V1 must render exactly five shirts")

    build_pack(records, data)
    shirt_results = {}
    export_results = {}
    for record in records:
        recipe_id = record["recipe"]["id"]
        rendered = rendered_by_id[recipe_id]
        shirt_results[recipe_id] = validate_rendered_shirt(rendered, data)
        export_results[recipe_id] = validate_exported_files(
            rendered,
            record["nativePath"],
            record["previewPath"],
            record["contactPath"],
            data,
        )
    public_records = [
        {
            "recipeId": record["recipe"]["id"],
            "itemName": record["recipe"]["itemName"],
            "itemId": record["itemId"],
            "slug": record["slug"],
            "textureAsset": record["textureAsset"],
            "nativePath": str(record["nativePath"].relative_to(ROOT)),
            "previewPath": str(record["previewPath"].relative_to(ROOT)),
            "contactPath": str(record["contactPath"].relative_to(ROOT)),
        }
        for record in records
    ]
    pack_result = validate_pack(PACK_DIR, public_records, VANILLA_OUTPUT)
    all_pass = (
        all(result["status"] == "PASS" for result in shirt_results.values())
        and all(result["status"] == "PASS" for result in export_results.values())
        and pack_result["status"] == "PASS"
    )
    validation = {
        "status": "PASS" if all_pass else "FAIL",
        "generatorVersion": GENERATOR_VERSION,
        "seed": seed,
        "scope": "static vanilla 1.6.15 shirt and Content Patcher contract",
        "runtimeInGame": "UNTESTED",
        "beautyClaim": "No numeric validator proves beauty; contacts received manual logical-grid review.",
        "recipeReview": {"compatibility": compatibility, "redundancy": redundancy},
        "selected": public_records,
        "shirts": shirt_results,
        "exports": export_results,
        "pack": pack_result,
        "farmerCompositePreview": {
            "created": False,
            "reason": "No reliably decoded installed vanilla Farmer base PNG was available; non-authoritative bodies were not substituted.",
        },
    }
    write_json(VALIDATION_PATH, validation)
    if not all_pass:
        raise RuntimeError(f"Generator V1 validation failed; see {VALIDATION_PATH}")
    FINAL_REPORT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_REPORT.write_text(
        build_final_report(recipes, selected, records, validation),
        encoding="utf-8",
    )
    return validation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed",
        type=int,
        default=GENERATOR_SEED,
        help="deterministic recipe seed (default: installed-game V1 audit seed)",
    )
    args = parser.parse_args()
    validation = generate(args.seed)
    print(
        f"Generator V1 {validation['status']}: 20 recipes, "
        f"{len(validation['selected'])} rendered shirts, isolated test pack ready."
    )
    for record in validation["selected"]:
        print(f"- {record['itemName']}: (S){record['itemId']}")
    print(f"Validation: {VALIDATION_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
