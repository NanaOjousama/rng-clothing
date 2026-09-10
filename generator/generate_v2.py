#!/usr/bin/env python3
"""Render exactly ten Generator V2 shirts and build the isolated test pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generator.png_utils import (
    RGBA,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    read_rgba_png,
    text_width,
    write_rgba_png,
)
from generator.renderer import make_contact_sheet
from generator.v2_recipe_engine import (
    GENERATOR_V2_SEED,
    GENERATOR_V2_VERSION,
    load_v2_data,
    pascal_identifier,
    slugify,
    validate_recipe_v2,
)
from generator.v2_renderer import composite_direction, render_v2_recipe
from generator.v2_structural import (
    DIRECTION_ORDER,
    PREVIEW_SCALE,
    control_recipes,
    generate_structural_tests,
)
from generator.v2_validator import (
    validate_exported_v2_files,
    validate_rendered_v2,
    validate_v2_pack,
)


ROOT = Path(__file__).resolve().parents[1]
FRESH_RECIPE_PATH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
RECIPE_GATE_PATH = ROOT / "output" / "recipes" / "lifestyle_v2_recipe_validation.json"
VANILLA_OUTPUT = ROOT / "output" / "vanilla" / "v2"
PACK_DIR = ROOT / "test-packs" / "vanilla" / "RNG-Clothing-V2"
VALIDATION_PATH = VANILLA_OUTPUT / "validation.json"
RENDERED_RECIPES_PATH = VANILLA_OUTPUT / "rendered_recipes.json"
ARCHETYPE_COMPARISON = VANILLA_OUTPUT / "V2_ARCHETYPE_COMPARISON.png"
RARITY_COMPARISON = VANILLA_OUTPUT / "V2_RARITY_COMPARISON.png"
FINAL_REPORT = ROOT / "reports" / "GENERATOR_V2.md"

SET_B_IDS = (
    "lifestyle-v2-01",
    "lifestyle-v2-06",
    "lifestyle-v2-10",
    "lifestyle-v2-16",
    "lifestyle-v2-19",
)
SET_B_REASONS = {
    "lifestyle-v2-01": "A plain Common tee establishes that simplicity remains a valid attractive outcome.",
    "lifestyle-v2-06": "A sweater yoke is one connected Uncommon styling decision rather than scattered ornament.",
    "lifestyle-v2-10": "The tailored placket carries identity while the chest accent remains subordinate.",
    "lifestyle-v2-16": "The Rare jacket combines a visible inner layer and broad collar in two large compatible regions.",
    "lifestyle-v2-19": "The Rare sailor top combines a dominant yoke with a structured lower band without an emblem dependency.",
}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def select_render_recipes(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    controls = control_recipes(data)
    batch = json.loads(FRESH_RECIPE_PATH.read_text(encoding="utf-8"))
    by_id = {recipe["id"]: recipe for recipe in batch["recipes"]}
    rarity_demo = [by_id[recipe_id] for recipe_id in SET_B_IDS]
    rarity_counts: dict[str, int] = {}
    for recipe in rarity_demo:
        rarity_counts[recipe["rarity"]] = rarity_counts.get(recipe["rarity"], 0) + 1
    if rarity_counts != {"Common": 1, "Uncommon": 2, "Rare": 2}:
        raise RuntimeError(f"Set B rarity distribution is wrong: {rarity_counts}")
    rare_archetypes = {
        recipe["archetype"] for recipe in rarity_demo if recipe["rarity"] == "Rare"
    }
    if rare_archetypes != {"JACKET", "SAILOR_TOP"}:
        raise RuntimeError(f"Set B Rare archetypes are wrong: {sorted(rare_archetypes)}")
    if len(controls) != 5 or len(rarity_demo) != 5:
        raise RuntimeError("V2 must render exactly five controls and five rarity demonstrations")
    for recipe in [*controls, *rarity_demo]:
        validation = validate_recipe_v2(recipe, data)
        if not validation.valid:
            raise RuntimeError(f"selected invalid recipe {recipe['id']}: {validation.errors}")
    return controls, rarity_demo


def _checker_tile(canvas: list[list[RGBA]], x0: int, y0: int, scale: int = 8) -> None:
    colors = ((211, 201, 188, 255), (191, 181, 169, 255))
    for y in range(8):
        for x in range(8):
            draw_rect(
                canvas,
                x0 + x * scale,
                y0 + y * scale,
                scale,
                scale,
                colors[(x + y) % 2],
            )


def make_set_comparison(
    records: list[dict[str, Any]], title: str, subtitle: str
) -> list[list[RGBA]]:
    width, height = 500, 510
    pixels = blank_image(width, height, (235, 226, 214, 255))
    draw_text(pixels, title, max(8, (width - text_width(title)) // 2), 7)
    draw_text(pixels, subtitle, max(8, (width - text_width(subtitle)) // 2), 20)
    tile_x = 212
    for direction_index, direction in enumerate(DIRECTION_ORDER):
        x0 = tile_x + direction_index * 70
        draw_text(pixels, direction, x0 + (64 - text_width(direction)) // 2, 37)
    for row_index, record in enumerate(records):
        y0 = 58 + row_index * 88
        recipe = record["recipe"]
        name = recipe["itemName"][:31]
        draw_text(pixels, name, 8, y0 + 19)
        meta = f"{recipe['archetype'].replace('_', '-')}  {recipe['rarity']}"
        draw_text(pixels, meta[:32], 8, y0 + 34)
        for direction_index, direction in enumerate(DIRECTION_ORDER):
            x0 = tile_x + direction_index * 70
            draw_rect(pixels, x0 - 1, y0 - 1, 66, 66, (101, 86, 73, 255))
            _checker_tile(pixels, x0, y0)
            blit(
                pixels,
                nearest_scale(record["rendered"].default_composites[direction], 8),
                x0,
                y0,
            )
    draw_text(pixels, "NATIVE 8X8 LOGICAL ART - 8X NEAREST PREVIEW", 126, 493)
    return pixels


def build_pack(records: list[dict[str, Any]], data: dict[str, Any]) -> None:
    assets_dir = PACK_DIR / "assets"
    i18n_dir = PACK_DIR / "i18n"
    assets_dir.mkdir(parents=True, exist_ok=True)
    i18n_dir.mkdir(parents=True, exist_ok=True)
    expected_assets = {f"{record['slug']}.png" for record in records}
    unexpected_assets = {
        path.name for path in assets_dir.glob("*.png") if path.name not in expected_assets
    }
    if unexpected_assets:
        raise RuntimeError(
            "refusing to leave stale V2 pack assets: " + ", ".join(sorted(unexpected_assets))
        )

    manifest = {
        "Name": "RNG Clothing V2 - Vanilla Shirts",
        "Author": "RNG Clothing feasibility project",
        "Version": GENERATOR_V2_VERSION,
        "Description": "Ten construction-first logical-pixel vanilla shirt prototypes.",
        "UniqueID": "RNGClothing.V2",
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
        texture_asset = record["textureAsset"]
        changes.append(
            {
                "LogName": f"Load {recipe['itemName']} shirt texture",
                "Action": "Load",
                "Target": texture_asset,
                "FromFile": f"assets/{slug}.png",
            }
        )
        default_dye = data["palettes"]["families"][recipe["paletteFamily"]]["defaultDye"]
        entries[record["itemId"]] = {
            "Name": record["itemId"],
            "DisplayName": f"{{{{i18n:shirts.{slug}.name}}}}",
            "Description": f"{{{{i18n:shirts.{slug}.description}}}}",
            "Price": 250,
            "Texture": texture_asset,
            "SpriteIndex": 0,
            "DefaultColor": " ".join(str(channel) for channel in default_dye),
            "CanBeDyed": True,
            "IsPrismatic": False,
            "HasSleeves": True,
            "CanChooseDuringCharacterCustomization": False,
            "CustomFields": {
                "RNGClothing/Category": recipe["category"],
                "RNGClothing/StyleProfile": recipe["styleProfile"],
                "RNGClothing/Archetype": recipe["archetype"],
                "RNGClothing/Rarity": recipe["rarity"],
                "RNGClothing/TestSet": record["set"],
                "RNGClothing/RecipeId": recipe["id"],
                "RNGClothing/GeneratorVersion": GENERATOR_V2_VERSION,
            },
        }
        i18n[f"shirts.{slug}.name"] = recipe["itemName"]
        i18n[f"shirts.{slug}.description"] = recipe["itemDescription"]
        source = VANILLA_OUTPUT / f"{slug}.png"
        (assets_dir / f"{slug}.png").write_bytes(source.read_bytes())
    changes.append(
        {
            "LogName": "Register RNG Clothing V2 vanilla shirts",
            "Action": "EditData",
            "Target": "Data/Shirts",
            "Entries": entries,
        }
    )
    write_json(PACK_DIR / "manifest.json", manifest)
    write_json(PACK_DIR / "content.json", {"Format": "2.8.0", "Changes": changes})
    write_json(i18n_dir / "default.json", i18n)

    set_a = [record for record in records if record["set"] == "A"]
    set_b = [record for record in records if record["set"] == "B"]
    commands_a = "\n".join(f"player_add (S){record['itemId']}" for record in set_a)
    commands_b = "\n".join(f"player_add (S){record['itemId']}" for record in set_b)
    readme = f"""# RNG Clothing V2 isolated test pack

This Content Patcher pack registers exactly ten native Stardew Valley shirts: five neutral archetype controls and five rarity demonstrations. It requires SMAPI and Content Patcher. It does not require Fashion Sense.

## Install

1. Copy the entire `RNG-Clothing-V2` folder into your Stardew Valley `Mods` folder.
2. Launch Stardew Valley through SMAPI.
3. Load a test save.

Do not copy only `assets`; the manifest, content file, localization file, and assets must stay together. This project did not install the pack automatically.

## Set A — archetype controls

```text
{commands_a}
```

## Set B — rarity demonstration

```text
{commands_b}
```

Each command adds one native shirt item to inventory. Move it into the shirt equipment slot. Use the normal sewing-machine dye workflow to test light, dark, and saturated dye choices.

## Test focus

- compare all five Set A items using the same neutral palette;
- confirm the jacket reads as an outer layer and the sailor top retains its yoke;
- compare Common, Uncommon, and Rare construction in Set B;
- inspect front, back, left, and right while standing, walking, and using tools;
- test both Farmer body presentations, save/reload, and multiplayer if available.

Static V2 validation passes only after generation. It cannot substitute for an in-game visual test.
"""
    (PACK_DIR / "README.md").write_text(readme, encoding="utf-8")


def build_final_report(
    controls: list[dict[str, Any]],
    rarity_demo: list[dict[str, Any]],
    records: list[dict[str, Any]],
    validation: dict[str, Any],
) -> str:
    commands = "\n".join(f"player_add (S){record['itemId']}" for record in records)
    recipe_rows = []
    for record in records:
        recipe = record["recipe"]
        construction = recipe["construction"]
        recipe_rows.append(
            f"| {record['set']} | {recipe['itemName']} | {recipe['archetype']} | {recipe['rarity']} | "
            f"{construction['panelLayout']} / {construction['layering']} / {construction['hem']} | "
            f"{', '.join(recipe['substantialFeatures']) or 'none'} | {recipe['paletteFamily']} |"
        )
    structural = validation["structuralGate"]["similarity"]
    return f"""# Generator V2 completion report

Generator version: `{GENERATOR_V2_VERSION}`  
Deterministic recipe seed: `{GENERATOR_V2_SEED}`  
Scope: native Stardew Valley shirts only; exactly ten full V2 garments.

## 1. Why V1's recipe architecture was insufficient

V1 treated `detail`, `secondaryDetail`, and `pattern` as peer-level additions. That encouraged rarity to stack lines, pins, and borders after a shared shirt body had already been chosen. The five in-game garments consequently had identical occupied masks, and their differences were concentrated in a few late overlay cells. Exact findings are in `reports/V2_STRUCTURAL_AUDIT.md`.

## 2. New V2 recipe architecture

V2 resolves category/style, archetype, seven construction fields, substantial features, rarity budget, named color blocks, micro details, and palette in that order. Recipes contain no coordinates. `BODY`, `COLLAR`, `YOKE`, `PLACKET`, `OUTER_PANEL_LEFT`, `OUTER_PANEL_RIGHT`, `INNER_LAYER`, `HEM`, `RIBBING`, plus neckline/stripe masks are renderer-owned data.

## 3. V1 to V2 migration

All 20 V1 recipes migrated deterministically and pass the V2 schema. Large cues became construction/features; chest marks and button dots became micro details; over-budget cues were explicitly dropped or absorbed into construction. The migration is for regression comparison and is not claimed to be optimal. See `reports/V1_TO_V2_RECIPE_MIGRATION.md`.

## 4. Twenty fresh V2 recipes

The fresh deterministic batch contains four recipes per archetype, represents Common/Uncommon/Rare, and has zero exact or near-duplicate construction signatures. Five deliberately invalid combinations were also rejected by the recipe gate. See `output/recipes/lifestyle_v2_recipes.json` and `reports/RECIPE_BATCH_V2.md`.

## 5. Rarity budget implementation

- Common: zero or one substantial feature, no micro detail, and archetype-specific restrictions on risky construction.
- Uncommon: exactly one substantial feature, optional one micro detail, and broader construction choices.
- Rare: one or two substantial features (the fresh batch uses two), optional one micro detail, and the widest legal construction/color-block freedom.

Two features which merely alias the same major region are rejected. Micro detail can never satisfy Rare identity.

## 6. V1 structural collapse

Every selected V1 garment occupied the same 62 front/back and 56 side cells. The button shirt and jacket differed by only 13 front, 10 back, and 13 side broad-role cells after decoration was included. Mistral and Garnet survived better because their connected inner-layer/yoke regions were larger. V2 addresses the actionable cause rather than blaming the 8×8 canvas.

## 7. Structural changes by archetype

- T-shirt: deliberately minimal body and neckline, with no borrowed collar/placket masks.
- Sweater: heavier neck plus connected lower ribbing/hem mass.
- Button shirt: continuous placket, folded collar, and tailored back yoke; buttons remain micro.
- Jacket: persistent left/right outer panels, broad visible inner layer, forward side opening, back yoke, and outerwear hem.
- Sailor top: dominant upper yoke/collar across front, back, and side with a clear lower body.

## 8. Major-region mask system

Named masks persist from construction through color blocking and shading. Micro details are applied only after those regions exist. Left/right are derived from one side, including outer-panel handedness.

## 9. Two-color comparison result

Result: **{validation['structuralGate']['status']}**. All five archetypes were rendered with only primary Color A and structural Color B before shading. The first run rejected the Button Shirt back as too close to the T-shirt; a real back yoke was added. The final gate compared {structural['comparisonCount']} pairs, rejected {structural['rejectedCount']}, and issued {structural['warningCount']} warnings.

## 10. Structural similarity checks

The validator compares secondary-region placement on front, back, and side; exact named-region matches; total differing cells; per-direction survival; and high Jaccard overlap. It rejects obvious collapse but makes no beauty claim.

## 11. Ten rendered garments and recipes

| Set | Name | Archetype | Rarity | Panel / layering / hem | Substantial features | Palette |
|---|---|---|---|---|---|---|
{chr(10).join(recipe_rows)}

Set A uses one neutral palette, no micro details, and minimum surface patterning. Set B uses one Common, two Uncommon, and two Rare recipes. Selection reasons are recorded in `output/vanilla/v2/rendered_recipes.json`.

## 12. Validation results

Overall static result: **{validation['status']}**.

- {len(records)}/10 semantic recipes valid;
- {sum(result['status'] == 'PASS' for result in validation['shirts'].values())}/10 logical renders pass technical/readability/design rejection checks;
- {sum(result['status'] == 'PASS' for result in validation['exports'].values())}/10 native PNG/preview exports pass;
- Content Patcher pack: {validation['pack']['status']};
- native sheets are 256×32 RGBA8, base at x=0..7, dye mask at x=128..135, directions at y=0/8/16/24;
- alpha is binary, masks are grayscale, base/mask cells do not overlap, sleeve samples are ordered, and previews are exact 8× nearest-neighbor replications.

No Farmer composite was fabricated because no reliably decoded authoritative installed Farmer base is available. Runtime movement, extreme dyes, save/reload, and multiplayer remain untested for V2.

## 13. Install and spawn commands

Copy `test-packs/vanilla/RNG-Clothing-V2/` into the normal Stardew `Mods` directory, launch through SMAPI, and run:

```text
{commands}
```

Move each item into the native shirt slot. The project did not install the pack or touch the normal Mods folder.

## 14. Most improved archetype

The jacket is the largest structural improvement. It no longer relies on a center stripe: outer panels, inner layer, collar, side opening, back yoke, and hem all have persistent region ownership.

## 15. Weakest archetype

The Button Shirt remains the weakest directionally. Its front placket reads clearly and its back yoke prevents total collapse, but the physically correct side view cannot carry the center placket and still approaches the Jacket more closely than any other control pair (six differing side cells). The T-shirt is less elaborate, but that simplicity is its intended identity. Human curation is still needed for side-facing tailored shirts.

## 16. Jacket identity

Static logical review says **materially improved**: the inner region is four cells wide through much of the front, survives at the side's forward edge, and is replaced by outerwear-specific yoke/hem structure on the back. In-game motion still needs confirmation.

## 17. Rarity progression

V2 now changes connected construction and color-block composition rather than merely adding pixels. Common can remain plain; Uncommon adds one major region; Rare combines two compatible substantial decisions. The result is meaningful in the static comparison, but desirability still needs an in-game Farmer review.

## 18. External style-profile stress-test readiness

The V2 recipe and mask architecture is ready for a **bounded semantic style-profile stress test** after this isolated pack is inspected in game. It is not yet a production reward generator: themed profiles still need similarity safeguards and human art direction, and no anime/Sun/Fashion Sense work belongs in V2.

## Critical visual boundary

Manual nearest-neighbor review covered both comparison sheets and all ten directional contact sheets. The set passes this feasibility art review: the garments read as deliberate clustered sprites, and the two Rare designs are compositionally stronger without becoming noisy. Mistral and Garnet are the strongest; the Woodland Sweater's yoke can approach sailor vocabulary, and the Button Shirt's side remains the least communicative view.

This is not a production beauty certification. V2 reduces programmer-art convergence, but it does not automate taste. Palette choice, exactly how far a yoke descends, lapel proportions, dye behavior at extreme colors, and final batch curation remain human/artistic judgments. Static validation cannot certify that a reward feels desirable on the animated Farmer.

## Stop condition

V2 ends here. No pants, hats, Fashion Sense, anime/Sun content, TFWR integration, reward economy, GUI, scraping, or machine learning was added.
"""


def generate(seed: int = GENERATOR_V2_SEED) -> dict[str, Any]:
    if seed != GENERATOR_V2_SEED:
        raise ValueError(
            "V2 rendering is tied to the validated recipe batch seed; rerun the recipe gate before changing it"
        )
    recipe_gate = json.loads(RECIPE_GATE_PATH.read_text(encoding="utf-8"))
    if recipe_gate.get("status") != "PASS" or recipe_gate.get("gate") != "V2 semantic recipes only; renderer not imported":
        raise RuntimeError("V2 recipe-only gate has not passed")
    data = load_v2_data()
    structural_gate = generate_structural_tests()
    controls, rarity_demo = select_render_recipes(data)
    selected = [("A", recipe) for recipe in controls] + [("B", recipe) for recipe in rarity_demo]
    if len(selected) != 10:
        raise RuntimeError("V2 must render exactly ten full garments")

    VANILLA_OUTPUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    rendered_by_id = {}
    for test_set, recipe in selected:
        rendered = render_v2_recipe(recipe, data)
        slug = slugify(recipe["itemName"])
        item_id = f"RNGClothing.V2.{pascal_identifier(recipe['itemName'])}"
        texture_asset = f"Mods/RNGClothing/V2/{pascal_identifier(recipe['itemName'])}/Shirts"
        native_path = VANILLA_OUTPUT / f"{slug}.png"
        preview_path = VANILLA_OUTPUT / f"{slug}-8x.png"
        contact_path = VANILLA_OUTPUT / f"{slug}-directions-8x.png"
        write_rgba_png(native_path, rendered.native_pixels)
        native = read_rgba_png(native_path)
        write_rgba_png(preview_path, nearest_scale(native["pixels"], PREVIEW_SCALE))
        disk_composites = {
            direction: composite_direction(native["pixels"], direction, recipe, data)
            for direction in ("front", "right", "left", "back")
        }
        write_rgba_png(contact_path, make_contact_sheet(disk_composites, recipe["itemName"]))
        record = {
            "set": test_set,
            "recipe": recipe,
            "slug": slug,
            "itemId": item_id,
            "textureAsset": texture_asset,
            "nativePath": native_path,
            "previewPath": preview_path,
            "contactPath": contact_path,
            "rendered": rendered,
        }
        records.append(record)
        rendered_by_id[recipe["id"]] = rendered

    set_a_records = [record for record in records if record["set"] == "A"]
    set_b_records = [record for record in records if record["set"] == "B"]
    write_rgba_png(
        ARCHETYPE_COMPARISON,
        make_set_comparison(
            set_a_records,
            "V2 ARCHETYPE CONTROL",
            "SAME PALETTE - NO MICRO DETAIL",
        ),
    )
    write_rgba_png(
        RARITY_COMPARISON,
        make_set_comparison(
            set_b_records,
            "V2 RARITY DEMONSTRATION",
            "1 COMMON - 2 UNCOMMON - 2 RARE",
        ),
    )

    build_pack(records, data)
    shirt_results = {}
    export_results = {}
    for record in records:
        recipe_id = record["recipe"]["id"]
        rendered = rendered_by_id[recipe_id]
        shirt_results[recipe_id] = validate_rendered_v2(rendered, data)
        export_results[recipe_id] = validate_exported_v2_files(
            rendered,
            record["nativePath"],
            record["previewPath"],
            record["contactPath"],
            data,
        )
    public_records = [
        {
            "set": record["set"],
            "recipeId": record["recipe"]["id"],
            "itemName": record["recipe"]["itemName"],
            "itemId": record["itemId"],
            "slug": record["slug"],
            "textureAsset": record["textureAsset"],
            "nativePath": str(record["nativePath"].relative_to(ROOT)),
            "previewPath": str(record["previewPath"].relative_to(ROOT)),
            "contactPath": str(record["contactPath"].relative_to(ROOT)),
            "selectionReason": (
                "Neutral no-micro control used to isolate archetype construction."
                if record["set"] == "A"
                else SET_B_REASONS[record["recipe"]["id"]]
            ),
        }
        for record in records
    ]
    rendered_recipe_output = {
        "formatVersion": 2,
        "generatorVersion": GENERATOR_V2_VERSION,
        "fullGarmentCount": 10,
        "setA": {
            "purpose": "same-palette, no-micro archetype control",
            "recipeCount": 5,
            "recipes": controls,
        },
        "setB": {
            "purpose": "construction-first rarity progression",
            "recipeCount": 5,
            "rarityDistribution": {"Common": 1, "Uncommon": 2, "Rare": 2},
            "selectionReasons": SET_B_REASONS,
            "recipes": rarity_demo,
        },
        "items": public_records,
    }
    write_json(RENDERED_RECIPES_PATH, rendered_recipe_output)

    pack_result = validate_v2_pack(PACK_DIR, public_records, VANILLA_OUTPUT)
    all_pass = (
        structural_gate["status"] == "PASS"
        and all(result["status"] == "PASS" for result in shirt_results.values())
        and all(result["status"] == "PASS" for result in export_results.values())
        and pack_result["status"] == "PASS"
    )
    validation = {
        "status": "PASS" if all_pass else "FAIL",
        "generatorVersion": GENERATOR_V2_VERSION,
        "seed": seed,
        "scope": "static vanilla Stardew 1.6.15 shirt and Content Patcher contract",
        "runtimeInGame": "UNTESTED FOR V2",
        "beautyClaim": "No numeric validator proves beauty; comparison sheets require manual logical-grid review.",
        "recipeGate": recipe_gate,
        "structuralGate": structural_gate,
        "selected": public_records,
        "shirts": shirt_results,
        "exports": export_results,
        "comparisons": {
            "archetype": str(ARCHETYPE_COMPARISON.relative_to(ROOT)),
            "rarity": str(RARITY_COMPARISON.relative_to(ROOT)),
        },
        "pack": pack_result,
        "farmerCompositePreview": {
            "created": False,
            "reason": "No reliably decoded installed vanilla Farmer base PNG was available; a non-authoritative body was not substituted.",
        },
    }
    write_json(VALIDATION_PATH, validation)
    if not all_pass:
        failures = {
            "shirts": {key: value["status"] for key, value in shirt_results.items()},
            "exports": {key: value["status"] for key, value in export_results.items()},
            "pack": pack_result["status"],
        }
        raise RuntimeError(f"Generator V2 validation failed: {failures}; see {VALIDATION_PATH}")
    FINAL_REPORT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_REPORT.write_text(
        build_final_report(controls, rarity_demo, records, validation), encoding="utf-8"
    )
    return validation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=GENERATOR_V2_SEED)
    args = parser.parse_args()
    result = generate(args.seed)
    print(
        f"Generator V2 {result['status']}: 20 fresh recipes, "
        f"{len(result['selected'])} full shirts, isolated test pack ready."
    )
    for record in result["selected"]:
        print(f"- Set {record['set']} / {record['itemName']}: (S){record['itemId']}")
    print(f"Validation: {VALIDATION_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
