"""V4 article selection and coordinate-free translation recipes.

V4 wraps an unchanged V3 design recipe with an article target. Article masks,
material cells, and Fashion Sense coordinates remain renderer-owned.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v3 import generate_benchmark_batch
from generator.v3.engine import validate_recipe_v3
from generator.v3.style_profiles import generate_aot_v3_collection


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "generator" / "data" / "v4"
SCHEMA = ROOT / "generator" / "schema" / "garment_recipe_v4.schema.json"


@dataclass(frozen=True)
class V4RecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v4_data() -> dict[str, Any]:
    return {"schema": _json(SCHEMA), "articles": _json(DATA / "article_adapters.json")}


def to_v3_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(recipe["designRecipe"])


def _coordinate_key_errors(value: Any, path: str = "$") -> list[str]:
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"x", "y", "row", "column", "coordinates", "pixels"}:
                errors.append(f"{path}.{key}: renderer coordinate key is forbidden in semantic V4 recipe")
            errors.extend(_coordinate_key_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_coordinate_key_errors(child, f"{path}[{index}]"))
    return errors


def validate_v4_recipe(recipe: dict[str, Any], data: dict[str, Any] | None = None) -> V4RecipeValidation:
    data = data or load_v4_data(); errors: list[str] = []; warnings: list[str] = []
    required = {"formatVersion", "id", "collection", "articleType", "articleIntent", "articleFeatures", "designRecipe"}
    if set(recipe) != required:
        errors.append(f"V4 recipe keys must be exactly {sorted(required)}")
    if recipe.get("formatVersion") != 4: errors.append("formatVersion must be 4")
    if recipe.get("collection") not in {"AoTInspired", "NeutralBenchmark"}: errors.append("invalid V4 collection")
    article_type = recipe.get("articleType")
    articles = data["articles"]["articles"]
    if article_type not in articles:
        errors.append(f"unknown article type {article_type!r}")
        return V4RecipeValidation(False, tuple(errors), tuple(warnings))
    adapter = articles[article_type]
    if adapter["status"].startswith("EXPERIMENTAL_REJECTED"):
        errors.append(f"{article_type} is deliberately rejected from V4 output: {adapter['status']}")
    design = recipe.get("designRecipe", {})
    v3 = validate_recipe_v3(design)
    errors.extend(f"V3 design: {message}" for message in v3.errors)
    warnings.extend(f"V3 design: {message}" for message in v3.warnings)
    if design:
        if design.get("archetype") not in adapter["compatibleArchetypes"]:
            errors.append(f"{article_type} is incompatible with {design.get('archetype')}")
        if design.get("concept", {}).get("focalArea") not in adapter["validFocalAreas"]:
            errors.append(f"{article_type} cannot place its focal design at {design.get('concept', {}).get('focalArea')}")
        if recipe.get("collection") == "AoTInspired" and design.get("styleProfile") != "AoTInspired":
            errors.append("AoT V4 recipe must retain the AoTInspired V3 design profile")
    features = set(recipe.get("articleFeatures", []))
    missing = set(adapter["requiredFeatures"]) - features
    if missing: errors.append(f"{article_type} misses required article features {sorted(missing)}")
    intent = recipe.get("articleIntent", {})
    if intent.get("sleeveMaterial") != adapter["sleeveMaterial"]:
        errors.append(f"{article_type} has wrong sleeve material")
    if article_type == "FITTED_SHIRT" and design.get("construction", {}).get("fit") != "fitted":
        errors.append("FITTED_SHIRT requires fitted V3 construction")
    if article_type == "SWEATER_TOP" and design.get("archetype") != "SWEATER":
        errors.append("SWEATER_TOP requires SWEATER construction")
    if article_type == "VEST_TOP":
        if design.get("construction", {}).get("layering") != "overlay_panel": errors.append("VEST_TOP requires overlay-panel layering")
        if design.get("construction", {}).get("panelLayout") not in {"yoke", "center_placket"}: errors.append("VEST_TOP requires yoke/placket organization")
    if article_type == "CROPPED_JACKET":
        construction = design.get("construction", {})
        if construction.get("panelLayout") != "split_outer_panels" or construction.get("layering") != "visible_inner_layer":
            errors.append("CROPPED_JACKET requires split shell and visible inner layer")
    if article_type == "SHORT_OUTERWEAR" and design.get("archetype") != "JACKET":
        errors.append("SHORT_OUTERWEAR requires JACKET construction")
    errors.extend(_coordinate_key_errors({key: value for key, value in recipe.items() if key != "designRecipe"}))
    return V4RecipeValidation(not errors, tuple(errors), tuple(warnings))


ARTICLE_INTENTS = {
    "FITTED_SHIRT": {
        "lengthClass": "fitted_standard", "sleeveMaterial": "outer_fabric", "silhouetteGoal": "tailored_taper",
        "primaryArticleRead": "narrow tailored lower torso with shirt closure logic", "focalZones": ["collar", "placket", "chest", "waist"],
    },
    "SWEATER_TOP": {
        "lengthClass": "soft_standard", "sleeveMaterial": "outer_fabric", "silhouetteGoal": "soft_mass",
        "primaryArticleRead": "uninterrupted soft cloth mass with sweater termination", "focalZones": ["collar", "yoke", "chest", "hem"],
    },
    "VEST_TOP": {
        "lengthClass": "vest_standard", "sleeveMaterial": "inner_shirt", "silhouetteGoal": "layered_vest_frame",
        "primaryArticleRead": "outer vest frame over visibly different inner-shirt sleeves", "focalZones": ["collar", "yoke", "chest", "placket", "waist"],
    },
    "CROPPED_JACKET": {
        "lengthClass": "cropped", "sleeveMaterial": "outer_fabric", "silhouetteGoal": "cropped_outer_shell",
        "primaryArticleRead": "split outer shell ending visibly above the standard shirt hem", "focalZones": ["collar", "outer_panels", "inner_layer", "chest", "waist", "back_yoke"],
    },
    "SHORT_OUTERWEAR": {
        "lengthClass": "standard_outer", "sleeveMaterial": "outer_fabric", "silhouetteGoal": "full_short_shell",
        "primaryArticleRead": "full shirt-footprint outer shell with jacket opening and structured back", "focalZones": ["collar", "outer_panels", "inner_layer", "chest", "hem", "back_yoke"],
    },
}


ARTICLE_FEATURES = {
    "FITTED_SHIRT": ["tailored_lower_taper"],
    "SWEATER_TOP": ["uninterrupted_cloth_mass", "ribbed_termination"],
    "VEST_TOP": ["contrasting_under_shirt", "vest_body_frame", "inner_shirt_sleeves"],
    "CROPPED_JACKET": ["shortened_outer_shell", "cropped_termination", "split_outer_shell", "visible_inner_layer", "structured_back"],
    "SHORT_OUTERWEAR": ["full_short_hem", "structured_back", "visible_inner_layer"],
}


def _wrap(design: dict[str, Any], *, outer_id: str, collection: str, article_type: str) -> dict[str, Any]:
    recipe = {
        "formatVersion": 4, "id": outer_id, "collection": collection, "articleType": article_type,
        "articleIntent": copy.deepcopy(ARTICLE_INTENTS[article_type]),
        "articleFeatures": list(ARTICLE_FEATURES[article_type]), "designRecipe": design,
    }
    result = validate_v4_recipe(recipe)
    if not result.valid: raise ValueError(f"invalid V4 recipe {outer_id}: {'; '.join(result.errors)}")
    return recipe


def _force_fitted(design: dict[str, Any]) -> None:
    design["construction"]["fit"] = "fitted"


def _force_vest(design: dict[str, Any]) -> None:
    design["archetype"] = "BUTTON_SHIRT"
    design["concept"]["garmentRole"] = "tailored_shirt"
    design["concept"]["silhouetteGoal"] = "fitted_tailored"
    design["construction"] = {
        "fit": "fitted", "neckline": "open", "collar": "small_folded", "closure": "buttons",
        "layering": "overlay_panel", "hem": "plain", "panelLayout": "yoke",
    }
    design["substantialFeatures"] = ["yoke"]


def _force_short_outerwear(design: dict[str, Any]) -> None:
    design["archetype"] = "JACKET"
    design["concept"]["garmentRole"] = "outer_jacket"
    design["concept"]["silhouetteGoal"] = "layered_outerwear"
    design["construction"] = {
        "fit": "regular", "neckline": "open", "collar": "small_folded", "closure": "center_open",
        "layering": "visible_inner_layer", "hem": "structured", "panelLayout": "split_outer_panels",
    }
    design["substantialFeatures"] = ["contrast_inner_layer"]
    # Translate the source pullover's full side block into an outerwear-scale
    # shoulder shell. This keeps the same support-system intent without
    # exceeding the Uncommon V3 surface budget on the larger jacket mask.
    if design["colorBlocking"]["type"] == "side_panels":
        design["colorBlocking"]["type"] = "shoulder_block"


def generate_v4_aot_collection() -> dict[str, Any]:
    source = generate_aot_v3_collection(); designs = [copy.deepcopy(item) for item in source["recipes"]]
    article_types = ["FITTED_SHIRT", "SWEATER_TOP", "VEST_TOP", "SHORT_OUTERWEAR", "CROPPED_JACKET", "SHORT_OUTERWEAR"]
    _force_fitted(designs[0]); _force_vest(designs[2]); _force_short_outerwear(designs[3])
    designs[3]["itemName"] = "Crosswall Utility Jacket"
    designs[3]["itemDescription"] = "A compact olive utility jacket with a visible inner layer, structured shell, and small original field badge."
    recipes = [_wrap(design, outer_id=f"v4-aot-{index:02d}", collection="AoTInspired", article_type=article_types[index - 1]) for index, design in enumerate(designs, 1)]
    return {"generatorVersion": "4.0.0", "collection": "AoTInspired", "count": 6, "rarityCounts": {rarity: sum(item["designRecipe"]["rarity"] == rarity for item in recipes) for rarity in ("Common", "Uncommon", "Rare")}, "recipes": recipes}


def generate_v4_neutral_collection() -> dict[str, Any]:
    source = {item["id"]: copy.deepcopy(item) for item in generate_benchmark_batch()["recipes"]}
    selections = [
        ("v3-benchmark-03", "FITTED_SHIRT"), ("v3-benchmark-02", "SWEATER_TOP"),
        ("v3-benchmark-07", "VEST_TOP"), ("v3-benchmark-08", "CROPPED_JACKET"), ("v3-benchmark-06", "SWEATER_TOP"),
        ("v3-benchmark-10", "VEST_TOP"), ("v3-benchmark-11", "SHORT_OUTERWEAR"), ("v3-benchmark-12", "SWEATER_TOP"),
    ]
    recipes = []
    for index, (source_id, article_type) in enumerate(selections, 1):
        design = source[source_id]
        if article_type == "FITTED_SHIRT": _force_fitted(design)
        elif article_type == "VEST_TOP": _force_vest(design)
        recipes.append(_wrap(design, outer_id=f"v4-neutral-{index:02d}", collection="NeutralBenchmark", article_type=article_type))
    return {"generatorVersion": "4.0.0", "collection": "NeutralBenchmark", "count": 8, "rarityCounts": {rarity: sum(item["designRecipe"]["rarity"] == rarity for item in recipes) for rarity in ("Common", "Uncommon", "Rare")}, "recipes": recipes}
