"""Semantic recipes for coordinated Fashion Sense hoodie appearances.

The recipe decides which runtime-safe layers express one hoodie. It contains no
sprite coordinates; Hat and Shirt geometry belongs to the Fashion Sense hoodie
renderer, while animated arms use the Shirt's native SleeveColors contract.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v2_recipe_engine import _coordinate_key_errors, _schema_errors
from generator.v5c2.engine import generate_v5c2_batch, validate_v5c2_recipe


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "generator" / "data" / "hoodie_layers" / "architecture.json"
SCHEMA = ROOT / "generator" / "schema" / "hoodie_layer_recipe.schema.json"


@dataclass(frozen=True)
class HoodieLayerRecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_hoodie_layer_data() -> dict[str, Any]:
    return {"architecture": _json(ARCHITECTURE), "schema": _json(SCHEMA)}


def validate_hoodie_layer_recipe(
    recipe: dict[str, Any], data: dict[str, Any] | None = None
) -> HoodieLayerRecipeValidation:
    data = data or load_hoodie_layer_data()
    errors = _schema_errors(recipe, data["schema"])
    errors.extend(
        _coordinate_key_errors(
            {key: value for key, value in recipe.items() if key != "baseUpperRecipe"}
        )
    )
    warnings: list[str] = []
    if errors:
        return HoodieLayerRecipeValidation(False, tuple(errors), tuple(warnings))

    base_result = validate_v5c2_recipe(recipe["baseUpperRecipe"])
    errors.extend(f"V5C2 upper foundation: {message}" for message in base_result.errors)
    warnings.extend(f"V5C2 upper foundation: {message}" for message in base_result.warnings)
    if recipe["baseUpperRecipe"].get("articleType") != "HOODIE":
        errors.append("coordinated hoodie requires a V5C2 HOODIE upper foundation")
    base_rarity = recipe["baseUpperRecipe"]["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["rarity"]
    if recipe["rarity"] != base_rarity:
        errors.append(f"wrapper rarity {recipe['rarity']} does not match upper foundation {base_rarity}")
    if recipe["assembly"]["sleeves"] != "native_sleeve_colors":
        errors.append("corrected hoodie presets must use native animated SleeveColors")
    if recipe["assembly"]["accessory"]:
        errors.append("drawstrings must remain in the body-anchored Shirt layer")
    if not recipe["assembly"]["hat"] or not recipe["assembly"]["preset"]:
        errors.append("runtime-readable hoodies require a Hat and coordinated Preset")
    if recipe["referenceInfluence"]["copiedPixels"]:
        errors.append("reference pixels may never enter a semantic hoodie recipe")
    return HoodieLayerRecipeValidation(not errors, tuple(errors), tuple(warnings))


def _hoodie_foundations() -> dict[str, dict[str, Any]]:
    batch = generate_v5c2_batch()
    return {
        recipe["articleSubtype"]: recipe
        for recipe in batch["recipes"]
        if recipe["articleType"] == "HOODIE"
    }


def _rename_foundation(
    foundation: dict[str, Any], *, name: str, description: str
) -> dict[str, Any]:
    foundation = copy.deepcopy(foundation)
    design = foundation["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]
    design["itemName"] = name
    design["itemDescription"] = description
    return foundation


def _contrast_foundation(foundations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    foundation = _rename_foundation(
        foundations["pullover"],
        name="Tidecap Contrast Hoodie",
        description="A clear blue hoodie whose pale hood lining makes the head-framing layer unmistakable.",
    )
    foundation["hoodIntent"] = {
        "state": "down",
        "lining": "contrast",
        "drawstrings": False,
        "volume": "standard",
    }
    foundation["constructionFeatures"] = [
        "hood_ring",
        "contrast_hood",
        "ribbed_hem",
        "cuff_echo",
    ]
    foundation["referenceInfluence"] = {
        "source": "hoodie_corpus_aggregate",
        "traitsOnly": [
            "contrasting_hood_interior",
            "clean_pullover_mass",
            "head_framing_color_block",
        ],
        "copiedPixels": False,
    }
    result = validate_v5c2_recipe(foundation)
    if not result.valid:
        raise ValueError("invalid contrast hoodie foundation: " + "; ".join(result.errors))
    return foundation


def generate_hoodie_layer_batch() -> dict[str, Any]:
    """Return the exact six requested hoodie concepts; no hidden candidate pool."""

    foundations = _hoodie_foundations()
    specs = [
        {
            "itemName": "Harbor Haze Pullover",
            "itemDescription": "A sea-glass pullover assembled with a visible hood, animated sleeves, and tidy drawstrings.",
            "rarity": "Common",
            "hoodieSubtype": "pullover",
            "fitIntent": "regular",
            "hoodLayer": {"state": "down", "lining": "self", "volume": "standard", "drawstrings": True},
            "sourceSubtype": "pullover",
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["pullover_mass", "hood_neck_bridge", "simple_ribbed_finish"], "copiedPixels": False},
        },
        {
            "itemName": "Rainline Zip Hoodie",
            "itemDescription": "A fitted rain-blue zip hoodie with a compact lowered hood and a crisp opening rhythm.",
            "rarity": "Uncommon",
            "hoodieSubtype": "zip",
            "fitIntent": "fitted",
            "hoodLayer": {"state": "down", "lining": "self", "volume": "compact", "drawstrings": False},
            "sourceSubtype": "zip",
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["zip_front", "compact_lowered_hood", "lightweight_fit"], "copiedPixels": False},
        },
        {
            "itemName": "Cloudberry Pouch Hoodie",
            "itemDescription": "A relaxed berry hoodie whose pouch, strings, and lowered hood form one readable construction.",
            "rarity": "Uncommon",
            "hoodieSubtype": "pouch",
            "fitIntent": "relaxed",
            "hoodLayer": {"state": "down", "lining": "contrast", "volume": "standard", "drawstrings": True},
            "sourceSubtype": "pouch_contrast",
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["broad_pouch", "contrast_lining", "relaxed_sweatwear_mass"], "copiedPixels": False},
        },
        {
            "itemName": "Tidecap Contrast Hoodie",
            "itemDescription": "A clear blue hoodie whose pale raised hood provides the dominant color-block focal.",
            "rarity": "Common",
            "hoodieSubtype": "contrast_hood",
            "fitIntent": "regular",
            "hoodLayer": {"state": "up", "lining": "contrast", "volume": "standard", "drawstrings": False},
            "foundation": _contrast_foundation(foundations),
            "referenceInfluence": {"source": "hoodie_corpus_aggregate", "traitsOnly": ["raised_hood_silhouette", "contrasting_hood_interior", "quiet_torso"], "copiedPixels": False},
        },
        {
            "itemName": "Sproutwing Cropped Hoodie",
            "itemDescription": "A soft cropped hoodie with a raised lined hood, small original charm, pouch seam, and layered cuffs.",
            "rarity": "Rare",
            "hoodieSubtype": "reference_soft_charm",
            "fitIntent": "cropped",
            "hoodLayer": {"state": "up", "lining": "contrast", "volume": "standard", "drawstrings": True},
            "sourceSubtype": "cropped_charm",
            "referenceInfluence": {"source": "hoodie/hoodie_design1.png", "traitsOnly": ["soft_sage_family", "long_drawstrings", "small_asymmetric_charm", "relaxed_cropped_shape"], "copiedPixels": False},
        },
        {
            "itemName": "Nightgarden Crest Hoodie",
            "itemDescription": "A baggy dark hoodie with a lowered hood, broad ribbing, and an original restrained tonal garden crest.",
            "rarity": "Rare",
            "hoodieSubtype": "reference_tonal_crest",
            "fitIntent": "baggy",
            "hoodLayer": {"state": "down", "lining": "self", "volume": "baggy", "drawstrings": False},
            "sourceSubtype": "baggy_crest",
            "referenceInfluence": {"source": "hoodie/hoodie_design2.png", "traitsOnly": ["oversized_sweatshirt_mass", "tonal_center_graphic", "restrained_monochrome", "broad_ribbing"], "copiedPixels": False},
        },
    ]

    recipes: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, 1):
        source_subtype = spec.pop("sourceSubtype", None)
        foundation = spec.pop("foundation", None)
        if foundation is None:
            foundation = _rename_foundation(
                foundations[source_subtype],
                name=spec["itemName"],
                description=spec["itemDescription"],
            )
        recipe = {
            "formatVersion": "5.5.0",
            "id": f"hoodie-layer-{index:02d}",
            "collection": "HoodieLayerArchitectureCorrection",
            **spec,
            "assembly": {
                "shirt": True,
                "sleeves": "native_sleeve_colors",
                "hat": True,
                "accessory": False,
                "preset": True,
            },
            "baseUpperRecipe": foundation,
        }
        result = validate_hoodie_layer_recipe(recipe)
        if not result.valid:
            raise ValueError(f"invalid hoodie layer recipe {recipe['id']}: {'; '.join(result.errors)}")
        recipes.append(recipe)
    return {
        "generatorVersion": "5.5.0",
        "collection": "HoodieLayerArchitectureCorrection",
        "seed": 2026083055,
        "count": len(recipes),
        "hiddenCandidateCount": 0,
        "recipes": recipes,
    }
