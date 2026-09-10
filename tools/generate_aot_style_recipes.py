#!/usr/bin/env python3
"""Generate the deterministic five-recipe AoT-inspired style-profile POC batch."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.v2_recipe_engine import load_v2_data, structural_signature, validate_recipe_v2


PROFILE_PATH = ROOT / "style-profiles" / "AoTInspired" / "profile.json"
OUTPUT_PATH = ROOT / "output" / "recipes" / "aot_style_profile_poc.json"
SEED = 202608290700


def _recipe(
    index: int,
    *,
    archetype: str,
    rarity: str,
    construction: dict[str, str],
    features: list[str],
    secondary: str,
    palette: str,
    traits: list[str],
    name: str,
    description: str,
    seed_offset: int = 0,
) -> dict[str, Any]:
    return {
        "id": f"aot-style-poc-{index:02d}",
        "generationIndex": index,
        "seed": SEED + index * 7919 + seed_offset,
        "category": "Lifestyle",
        "styleProfile": "AoTInspired",
        "referenceTraits": traits,
        "archetype": archetype,
        "rarity": rarity,
        "construction": construction,
        "substantialFeatures": features,
        "microDetails": [],
        "colorBlocking": {
            "primaryRegion": "outer_panels" if archetype == "JACKET" else "body",
            "secondaryRegion": secondary,
            "accentRegion": "none",
        },
        "paletteFamily": palette,
        "accent": "none",
        "dyeable": True,
        "itemName": name,
        "itemDescription": description,
    }


def _candidates() -> list[dict[str, Any]]:
    recipes = [
        _recipe(
            1,
            archetype="JACKET",
            rarity="Rare",
            construction={
                "fit": "regular",
                "neckline": "open",
                "collar": "wide",
                "closure": "center_open",
                "layering": "visible_inner_layer",
                "hem": "structured",
                "panelLayout": "split_outer_panels",
            },
            features=["contrast_inner_layer", "broad_collar"],
            secondary="inner_layer",
            palette="field_tan_olive",
            traits=["compact_cropped_outerwear", "structured_military_collar", "disciplined_paneling", "waist_emphasis"],
            name="Rampart Field Jacket",
            description="A compact tan field jacket with a high structured collar, dark inner layer, and a firmly tailored waist.",
            seed_offset=6,
        ),
        _recipe(
            2,
            archetype="JACKET",
            rarity="Rare",
            construction={
                "fit": "regular",
                "neckline": "open",
                "collar": "small_folded",
                "closure": "center_open",
                "layering": "visible_inner_layer",
                "hem": "contrast_band",
                "panelLayout": "split_outer_panels",
            },
            features=["contrast_inner_layer", "structured_lower_band"],
            secondary="inner_layer",
            palette="olive_warm_beige",
            traits=["utility_tailoring", "clean_layering", "disciplined_paneling", "waist_emphasis"],
            name="Mosswatch Utility Jacket",
            description="An olive utility jacket with a warm inner layer, compact panels, and a clearly finished lower band.",
            seed_offset=2,
        ),
        _recipe(
            3,
            archetype="BUTTON_SHIRT",
            rarity="Rare",
            construction={
                "fit": "fitted",
                "neckline": "open",
                "collar": "small_folded",
                "closure": "buttons",
                "layering": "overlay_panel",
                "hem": "contrast_band",
                "panelLayout": "yoke",
            },
            features=["yoke", "structured_lower_band"],
            secondary="yoke",
            palette="ivory_black_brown",
            traits=["utility_tailoring", "structured_military_collar", "disciplined_paneling", "civilian_fieldwear"],
            name="Cadence Yoke Shirt",
            description="A fitted ivory work shirt with a dark vest-like yoke, folded collar, and disciplined waist finish.",
        ),
        _recipe(
            4,
            archetype="BUTTON_SHIRT",
            rarity="Uncommon",
            construction={
                "fit": "fitted",
                "neckline": "open",
                "collar": "small_folded",
                "closure": "buttons",
                "layering": "single_layer",
                "hem": "plain",
                "panelLayout": "center_placket",
            },
            features=["center_placket"],
            secondary="placket",
            palette="dusty_khaki_deep_gray",
            traits=["utility_tailoring", "structured_military_collar", "disciplined_paneling", "civilian_fieldwear"],
            name="Citadel Dress Shirt",
            description="A fitted ivory work shirt organized around a dark tailored placket and compact folded collar.",
        ),
        _recipe(
            5,
            archetype="SWEATER",
            rarity="Rare",
            construction={
                "fit": "regular",
                "neckline": "shallow_v",
                "collar": "wide",
                "closure": "none",
                "layering": "single_layer",
                "hem": "structured",
                "panelLayout": "solid",
            },
            features=["broad_collar", "structured_lower_band"],
            secondary="collar",
            palette="civilian_burgundy_charcoal",
            traits=["civilian_fieldwear", "structured_military_collar", "waist_emphasis", "dark_formal_outerwear"],
            name="Nightwatch Collar Knit",
            description="A dark burgundy civilian knit with a broad charcoal collar rhythm and a firmly structured waist.",
        ),
    ]
    contexts = [
        {
            "styleStrength": "STRONG",
            "branch": "militaryCore",
            "styleEvidence": ["tan compact outer panels", "wide collar/lapel", "dark olive inner layer", "structured waist"],
            "selection": "SELECTED",
        },
        {
            "styleStrength": "STRONG",
            "branch": "militaryCore",
            "styleEvidence": ["olive compact outer layer", "folded collar", "warm visible inner layer", "contrast waist band"],
            "selection": "NOT_SELECTED",
        },
        {
            "styleStrength": "MODERATE",
            "branch": "civilianUtility",
            "styleEvidence": ["fitted ivory uniform shirt", "dark vest-like shoulder yoke", "folded collar", "structured waist"],
            "selection": "SELECTED",
        },
        {
            "styleStrength": "MODERATE",
            "branch": "civilianUtility",
            "styleEvidence": ["ivory fitted shirt", "dark formal placket", "small folded collar"],
            "selection": "NOT_SELECTED",
        },
        {
            "styleStrength": "STRONG",
            "branch": "darkFormal",
            "styleEvidence": ["dark civilian palette", "broad formal collar rhythm", "heavy uninterrupted torso", "structured waist"],
            "selection": "SELECTED",
        },
    ]
    return [{**context, "recipe": recipe} for context, recipe in zip(contexts, recipes, strict=True)]


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    data = load_v2_data()
    candidates = _candidates()
    reviews = []
    signatures = []
    for candidate in candidates:
        recipe = candidate["recipe"]
        result = validate_recipe_v2(recipe, data)
        if not result.valid:
            raise ValueError(f"{recipe['id']}: {result.errors}")
        signature = structural_signature(recipe)
        signatures.append(signature)
        reviews.append({
            "id": recipe["id"],
            "valid": result.valid,
            "errors": list(result.errors),
            "warnings": list(result.warnings),
            "complexity": result.complexity,
            "styleStrength": candidate["styleStrength"],
            "branch": candidate["branch"],
            "styleEvidenceCount": len(candidate["styleEvidence"]),
            "constructionDriven": True,
            "directCopyRisk": "LOW_NO_LOGOS_NO_EXACT_LAYOUT",
            "gameplayReadabilityRisk": "LOW" if recipe["archetype"] == "JACKET" else "MODERATE",
        })
    if len(set(signatures)) != len(signatures):
        raise ValueError("style-profile batch contains duplicate structural signatures")

    output = {
        "formatVersion": 1,
        "generator": "AoTInspired external style-profile POC",
        "seed": SEED,
        "profile": profile["id"],
        "profilePath": str(PROFILE_PATH.relative_to(ROOT)),
        "recipeArchitecture": "unchanged V2 coordinate-free recipe inside bounded style context",
        "styleStrengthStorage": "Style strength belongs to the external profile context; the nested recipe keeps the frozen V2 shape.",
        "candidateCount": 5,
        "selectedCount": 3,
        "selectedIds": [candidate["recipe"]["id"] for candidate in candidates if candidate["selection"] == "SELECTED"],
        "allValid": True,
        "allStructurallyDistinct": True,
        "profileSha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "candidates": candidates,
        "automaticReview": reviews,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Generated five valid profile recipes at {OUTPUT_PATH}")
    for candidate in candidates:
        recipe = candidate["recipe"]
        print(candidate["selection"], candidate["styleStrength"], recipe["id"], recipe["itemName"])


if __name__ == "__main__":
    main()
