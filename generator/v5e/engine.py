"""Semantic V5E Rare+ structured-outerwear recipe.

V5E deliberately adds no renderer coordinates.  It selects a bounded short
outerwear article, a coordinated animated-sleeve companion, and an authored
construction hierarchy from the existing V3/V4/V5 systems.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.v2_recipe_engine import _coordinate_key_errors
from generator.v5b.engine import validate_v5b_recipe
from generator.v5d.engine import generate_v5d_batch


@dataclass(frozen=True)
class V5EValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def generate_v5e_recipe() -> dict[str, Any]:
    """Return the one controlled Sunfield-derived semantic recipe."""
    old = generate_v5d_batch()["recipes"][7]
    upper = copy.deepcopy(old["baseUpperRecipe"])
    article = upper["baseArticleRecipe"]
    design = article["designRecipe"]

    upper.update({
        "articleType": "STANDARD_JACKET",
        "constructionVariant": "field_jacket",
        "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE",
        "shoulderIntent": "standard",
        "surfaceTranslation": {
            "primaryZone": "outer_panels",
            "sleeveContinuation": "trim_echo",
            "cuffTreatment": "layered",
        },
    })
    article.update({
        "articleType": "SHORT_OUTERWEAR",
        "articleIntent": {
            "lengthClass": "short",
            "sleeveMaterial": "outer_fabric",
            "silhouetteGoal": "structured_short_outerwear",
            "primaryArticleRead": "split field-jacket shell with a bounded inner shirt and full short hem",
            "focalZones": ["collar", "outer_panels", "inner_layer", "chest", "waist", "back_yoke"],
        },
        "articleFeatures": ["full_short_hem", "structured_back", "visible_inner_layer", "split_outer_shell"],
    })
    design.update({
        "rarity": "Rare",
        "itemName": "Sunfield Pathfinder Jacket",
        "itemDescription": "A premium tan field jacket with shaped lapels, a fitted olive shirt, long sleeves, and practical scout pockets.",
    })
    design["construction"].update({
        "fit": "regular",
        "neckline": "open",
        "collar": "small_folded",
        "closure": "center_open",
        "layering": "visible_inner_layer",
        "hem": "structured",
        "panelLayout": "split_outer_panels",
    })
    design["concept"].update({
        "garmentRole": "outer_jacket",
        "focalArea": "upper_chest",
        "designDensity": "rich_restrained",
    })

    recipe = {
        "formatVersion": "5.5.0",
        "id": "v5e-rareplus-field-jacket-01",
        "collection": "V5ERarePlusStructuredOuterwear",
        "rendererTier": "RARE_PLUS_COMPLEX_LAYER_GARMENT_V1",
        "articleType": "STRUCTURED_FIELD_JACKET",
        "garmentRole": "premium_short_outerwear",
        "rarity": "Rare",
        "fitIntent": "structured_short",
        "sleeveIntent": "LAYERED_INNER_OUTER_SLEEVE",
        "shoulderIntent": "reinforced_sloped",
        "collarIntent": "folded_field_lapel",
        "openingIntent": "bounded_open_front",
        "layeringIntent": "visible_inner_shirt",
        "hemIntent": "short_structured",
        "constructionFeatures": [
            "shaped_lapels", "bounded_inner_shirt", "shoulder_panels", "paired_pocket_flaps",
            "side_shell_seams", "layered_cuffs", "short_structured_hem", "back_yoke",
        ],
        "surfacePlan": {
            "primaryGesture": "lapel_opening",
            "secondaryRegion": "pocket_yoke_relationship",
            "accentFeature": "single_field_tab",
            "topology": "front_lapel_pockets_side_shell_back_yoke",
            "density": "high_controlled",
        },
        "paletteStory": "aot_high_contrast_field",
        "layerPlan": {
            "shirt": "required",
            "sleeves": "native_animated_via_shirt_colors",
            "accessory": "none",
            "hat": "none",
            "pants": "none",
            "shoes": "none",
            "preset": "required_coordinated",
        },
        "benchmarkBasis": {
            "sources": ["vanilla_clothing", "male_non_mixed_coats_jackets", "sunfield_scout_direction"],
            "generalizedTraits": ["compact_outer_shell", "lapel_opening", "paired_pocket_rhythm", "quiet_authored_back"],
            "copiedPixels": False,
        },
        "baseUpperRecipe": upper,
    }
    result = validate_v5e_recipe(recipe)
    if not result.valid:
        raise ValueError("invalid V5E recipe: " + "; ".join(result.errors))
    return recipe


def validate_v5e_recipe(recipe: dict[str, Any]) -> V5EValidation:
    errors: list[str] = []
    warnings: list[str] = []
    required = {
        "formatVersion", "id", "collection", "rendererTier", "articleType", "garmentRole", "rarity",
        "fitIntent", "sleeveIntent", "shoulderIntent", "collarIntent", "openingIntent", "layeringIntent",
        "hemIntent", "constructionFeatures", "surfacePlan", "paletteStory", "layerPlan", "benchmarkBasis",
        "baseUpperRecipe",
    }
    missing = required - set(recipe)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
        return V5EValidation(False, tuple(errors), tuple(warnings))
    if recipe["formatVersion"] != "5.5.0": errors.append("formatVersion must be 5.5.0")
    if recipe["rendererTier"] != "RARE_PLUS_COMPLEX_LAYER_GARMENT_V1": errors.append("wrong Rare+ renderer tier")
    if recipe["articleType"] != "STRUCTURED_FIELD_JACKET": errors.append("V5E proof accepts only STRUCTURED_FIELD_JACKET")
    if recipe["rarity"] != "Rare": errors.append("Rare+ is a renderer capability tier; semantic rarity remains Rare")
    expected_layers = {"shirt": "required", "sleeves": "native_animated_via_shirt_colors", "accessory": "none", "hat": "none", "pants": "none", "shoes": "none", "preset": "required_coordinated"}
    if recipe["layerPlan"] != expected_layers: errors.append("field jacket must use Shirt + native animated SleeveColors + preset")
    if recipe["benchmarkBasis"].get("copiedPixels") is not False: errors.append("reference pixels may not enter the recipe")
    for message in _coordinate_key_errors({key: value for key, value in recipe.items() if key != "baseUpperRecipe"}):
        errors.append(message)
    base = validate_v5b_recipe(recipe["baseUpperRecipe"])
    errors.extend(f"V5B base: {message}" for message in base.errors)
    warnings.extend(f"V5B base: {message}" for message in base.warnings)
    features = set(recipe["constructionFeatures"])
    expected_features = {"shaped_lapels", "bounded_inner_shirt", "paired_pocket_flaps", "layered_cuffs", "back_yoke"}
    if not expected_features <= features: errors.append("required structured-outerwear construction vocabulary is incomplete")
    return V5EValidation(not errors, tuple(errors), tuple(warnings))
