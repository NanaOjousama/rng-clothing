#!/usr/bin/env python3
"""Run the V2 semantic-recipe gate without importing or invoking a renderer."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any

from generator.v2_recipe_engine import (
    ARCHETYPE_ORDER,
    CONSTRUCTION_FIELDS,
    GENERATOR_V2_SEED,
    GENERATOR_V2_VERSION,
    generate_v2_recipes,
    load_v2_data,
    migrate_v1_recipes,
    review_v2_redundancy,
    validate_recipe_v2,
)


ROOT = Path(__file__).resolve().parents[1]
MIGRATED_OUTPUT = ROOT / "output" / "recipes" / "lifestyle_v1_migrated_to_v2.json"
FRESH_OUTPUT = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
VALIDATION_OUTPUT = ROOT / "output" / "recipes" / "lifestyle_v2_recipe_validation.json"
MIGRATION_REPORT = ROOT / "reports" / "V1_TO_V2_RECIPE_MIGRATION.md"
FRESH_REPORT = ROOT / "reports" / "RECIPE_BATCH_V2.md"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _construction_text(recipe: dict[str, Any]) -> str:
    construction = recipe["construction"]
    return "; ".join(f"{field}={construction[field]}" for field in CONSTRUCTION_FIELDS)


def build_migration_report(records: list[dict[str, Any]]) -> str:
    lines = [
        "# V1 to V2 recipe migration",
        "",
        f"Migration utility: Generator V2 `{GENERATOR_V2_VERSION}`  ",
        "Purpose: deterministic regression comparison, not automatic art direction.",
        "",
        "V1's `detail`, `secondaryDetail`, and `pattern` fields were interpreted as evidence about construction. Large, legal regions were retained first; button dots and chest marks were demoted to micro details. When a V1 combination exceeded its V2 rarity budget, the migration records the dropped or construction-absorbed cue rather than hiding the loss.",
        "",
        "All 20 migrated recipes pass the V2 schema and compatibility rules. This only confirms faithful legal translation; it does not mean the migrated recipes are optimal V2 designs.",
        "",
    ]
    for index, record in enumerate(records, start=1):
        source = record["sourceFlatFields"]
        lines.extend(
            [
                f"## {index}. {record['sourceName']} (`{record['sourceRecipeId']}`)",
                "",
                f"- V1 flat fields: `detail={source['detail']}`, `secondaryDetail={source['secondaryDetail']}`, `pattern={source['pattern']}`.",
                f"- V2 construction: " + "; ".join(f"`{key}={value}`" for key, value in record["construction"].items()) + ".",
                f"- Substantial features: {', '.join(f'`{value}`' for value in record['substantialFeatures']) or 'none'}.",
                f"- Micro details: {', '.join(f'`{value}`' for value in record['microDetails']) or 'none'}.",
                f"- Color blocking: primary `{record['colorBlocking']['primaryRegion']}`, secondary `{record['colorBlocking']['secondaryRegion']}`, accent `{record['colorBlocking']['accentRegion']}`.",
            ]
        )
        for note in record["mappingNotes"]:
            lines.append(f"- Translation: {note}.")
        lines.extend([f"- Caveat: {record['warning']}", ""])
    return "\n".join(lines)


def build_fresh_report(
    recipes: list[dict[str, Any]], redundancy: dict[str, Any]
) -> str:
    lines = [
        "# Lifestyle recipe batch V2",
        "",
        f"Generator version: `{GENERATOR_V2_VERSION}`  ",
        f"Deterministic seed: `{GENERATOR_V2_SEED}`  ",
        "Scope: 20 coordinate-free Lifestyle recipes; construction resolved before decoration.",
        "",
        "## Recipe-only gate",
        "",
        "- Schema and semantic coordinate ban: **PASS** (20/20).",
        "- Archetype construction compatibility: **PASS** (20/20).",
        "- Rarity budgets: **PASS** (20/20).",
        "- Color-block region compatibility: **PASS** (20/20).",
        f"- Exact duplicate constructions: {redundancy['exactDuplicateCount']}.",
        f"- Near-duplicate constructions: {redundancy['nearDuplicateCount']}.",
        f"- Minimum accepted within-archetype structural distance: {redundancy['minimumAcceptedStructuralDistance']} semantic changes.",
        "",
        "This gate was run before any V2 renderer or mask output. It rejects broken recipe architecture but does not claim beauty.",
        "",
        "## Twenty construction-first concepts",
        "",
        "| # | Name | Archetype | Rarity | Construction | Substantial | Micro | Color blocks | Palette |",
        "|---:|---|---|---|---|---|---|---|---|",
    ]
    for recipe in recipes:
        construction = recipe["construction"]
        construction_short = (
            f"{construction['fit']}; {construction['collar']}/{construction['neckline']}; "
            f"{construction['layering']}; {construction['hem']}; {construction['panelLayout']}"
        )
        substantial = ", ".join(recipe["substantialFeatures"]) or "none"
        micro = ", ".join(recipe["microDetails"]) or "none"
        blocks = recipe["colorBlocking"]
        blocking = f"{blocks['primaryRegion']} → {blocks['secondaryRegion']} → {blocks['accentRegion']}"
        lines.append(
            f"| {recipe['generationIndex']} | {recipe['itemName']} | {recipe['archetype']} | "
            f"{recipe['rarity']} | {construction_short} | {substantial} | {micro} | {blocking} | "
            f"{recipe['paletteFamily']} |"
        )
    counts = Counter(recipe["rarity"] for recipe in recipes)
    lines.extend(
        [
            "",
            "## Distribution and review boundary",
            "",
            f"- Archetypes: " + ", ".join(f"`{archetype}`=4" for archetype in ARCHETYPE_ORDER) + ".",
            f"- Rarity: Common={counts['Common']}, Uncommon={counts['Uncommon']}, Rare={counts['Rare']}.",
            "- Category remains `Lifestyle`; rarity is separate reward metadata.",
            "- Micro details never satisfy the Rare structural requirement.",
            "- Construction diversity and legality are machine-checkable; desirability still requires rendered logical-grid review.",
            "",
        ]
    )
    return "\n".join(lines)


def prepare(seed: int = GENERATOR_V2_SEED) -> dict[str, Any]:
    data = load_v2_data()
    migrated, migration_records = migrate_v1_recipes(data)
    migrated_results = {
        recipe["id"]: validate_recipe_v2(recipe, data) for recipe in migrated
    }
    if not all(result.valid for result in migrated_results.values()):
        raise RuntimeError(
            {key: value.errors for key, value in migrated_results.items() if not value.valid}
        )

    fresh = generate_v2_recipes(data, seed)
    fresh_results = {recipe["id"]: validate_recipe_v2(recipe, data) for recipe in fresh}
    if not all(result.valid for result in fresh_results.values()):
        raise RuntimeError(
            {key: value.errors for key, value in fresh_results.items() if not value.valid}
        )
    redundancy = review_v2_redundancy(fresh)
    if redundancy["exactDuplicateCount"] or redundancy["nearDuplicateCount"]:
        raise RuntimeError(f"fresh V2 recipe redundancy gate failed: {redundancy}")
    archetype_counts = Counter(recipe["archetype"] for recipe in fresh)
    rarity_counts = Counter(recipe["rarity"] for recipe in fresh)
    if archetype_counts != Counter({archetype: 4 for archetype in ARCHETYPE_ORDER}):
        raise RuntimeError(f"unexpected archetype distribution: {archetype_counts}")
    if set(rarity_counts) != {"Common", "Uncommon", "Rare"}:
        raise RuntimeError(f"not all V2 rarities represented: {rarity_counts}")

    negative_cases: dict[str, list[str]] = {}
    invalid_tee_layer = copy.deepcopy(fresh[0])
    invalid_tee_layer["construction"]["layering"] = "visible_inner_layer"
    invalid_rare_micro = copy.deepcopy(fresh[0])
    invalid_rare_micro["rarity"] = "Rare"
    invalid_rare_micro["substantialFeatures"] = []
    invalid_rare_micro["microDetails"] = ["small_pin"]
    invalid_rare_micro["colorBlocking"]["secondaryRegion"] = "none"
    invalid_rare_micro["colorBlocking"]["accentRegion"] = "body"
    invalid_rare_micro["accent"] = "rust"
    invalid_sailor_opening = copy.deepcopy(next(recipe for recipe in fresh if recipe["archetype"] == "SAILOR_TOP"))
    invalid_sailor_opening["construction"]["closure"] = "center_open"
    invalid_button_collar = copy.deepcopy(next(recipe for recipe in fresh if recipe["archetype"] == "BUTTON_SHIRT"))
    invalid_button_collar["construction"]["collar"] = "sailor"
    duplicate_region_features = copy.deepcopy(next(recipe for recipe in fresh if recipe["id"] == "lifestyle-v2-10"))
    duplicate_region_features["rarity"] = "Rare"
    duplicate_region_features["construction"]["layering"] = "single_layer"
    duplicate_region_features["construction"]["panelLayout"] = "center_placket"
    duplicate_region_features["substantialFeatures"] = ["center_placket", "major_panel_contrast"]
    duplicate_region_features["microDetails"] = []
    duplicate_region_features["colorBlocking"] = {
        "primaryRegion": "body",
        "secondaryRegion": "placket",
        "accentRegion": "none",
    }
    duplicate_region_features["accent"] = "none"
    for label, invalid_recipe in {
        "t_shirt_visible_inner_layer": invalid_tee_layer,
        "rare_micro_only_identity": invalid_rare_micro,
        "sailor_center_opening": invalid_sailor_opening,
        "button_shirt_sailor_collar": invalid_button_collar,
        "two_features_same_major_region": duplicate_region_features,
    }.items():
        result = validate_recipe_v2(invalid_recipe, data)
        if result.valid:
            raise RuntimeError(f"negative recipe case was incorrectly accepted: {label}")
        negative_cases[label] = list(result.errors)

    migrated_batch = {
        "formatVersion": 2,
        "generatorVersion": GENERATOR_V2_VERSION,
        "source": "output/recipes/lifestyle_v1_recipes.json",
        "purpose": "deterministic V1-to-V2 regression migration; not optimal V2 art direction",
        "recipeCount": len(migrated),
        "allValid": True,
        "recipes": migrated,
        "migrationRecords": migration_records,
    }
    fresh_batch = {
        "formatVersion": 2,
        "generatorVersion": GENERATOR_V2_VERSION,
        "seed": seed,
        "scope": "Lifestyle / vanilla Stardew shirts only",
        "recipeCount": len(fresh),
        "pipelineOrder": [
            "category_style_profile",
            "archetype",
            "construction",
            "substantial_features",
            "rarity_budget",
            "color_blocking",
            "micro_details",
            "palette",
        ],
        "compatibilityReview": {"allValid": True, "validCount": 20},
        "redundancyReview": redundancy,
        "recipes": fresh,
    }
    validation = {
        "status": "PASS",
        "gate": "V2 semantic recipes only; renderer not imported",
        "generatorVersion": GENERATOR_V2_VERSION,
        "seed": seed,
        "migrated": {
            "count": len(migrated),
            "valid": sum(result.valid for result in migrated_results.values()),
            "warnings": {
                key: list(result.warnings)
                for key, result in migrated_results.items()
                if result.warnings
            },
        },
        "fresh": {
            "count": len(fresh),
            "valid": sum(result.valid for result in fresh_results.values()),
            "archetypes": dict(sorted(archetype_counts.items())),
            "rarities": dict(sorted(rarity_counts.items())),
            "redundancy": redundancy,
            "warnings": {
                key: list(result.warnings)
                for key, result in fresh_results.items()
                if result.warnings
            },
        },
        "negativeCompatibilityCases": {
            "status": "PASS",
            "rejectedCount": len(negative_cases),
            "cases": negative_cases,
        },
    }
    write_json(MIGRATED_OUTPUT, migrated_batch)
    write_json(FRESH_OUTPUT, fresh_batch)
    write_json(VALIDATION_OUTPUT, validation)
    MIGRATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    MIGRATION_REPORT.write_text(build_migration_report(migration_records), encoding="utf-8")
    FRESH_REPORT.write_text(build_fresh_report(fresh, redundancy), encoding="utf-8")
    return validation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=GENERATOR_V2_SEED)
    args = parser.parse_args()
    result = prepare(args.seed)
    print(
        f"V2 recipe gate {result['status']}: {result['migrated']['valid']}/20 migrated and "
        f"{result['fresh']['valid']}/20 fresh recipes valid; renderer not invoked."
    )
    print(f"Validation: {VALIDATION_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
