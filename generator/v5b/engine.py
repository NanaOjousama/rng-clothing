"""Coordinate-free V5B upper-article and SleeveIntent recipes.

V5B deliberately wraps the frozen V4/V3 design recipe.  Sleeve atlas cells,
shirt masks, animation frame indices, and Fashion Sense offsets remain in the
backend.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.v3 import generate_v3_recipe
from generator.v3.style_profiles import generate_aot_v3_collection
from generator.v4.engine import _force_fitted, _force_short_outerwear, _force_vest, _wrap, load_v4_data, validate_v4_recipe


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "generator" / "data" / "v5b"


@dataclass(frozen=True)
class V5BRecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v5b_data() -> dict[str, Any]:
    return {
        "sleeves": _json(DATA / "sleeve_capabilities.json"),
        "articles": _json(DATA / "upper_article_compatibility.json"),
    }


def _coordinate_key_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"x", "y", "row", "column", "coordinates", "pixels", "frameindex"}:
                errors.append(f"{path}.{key}: renderer coordinate key is forbidden in semantic V5B recipes")
            errors.extend(_coordinate_key_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_coordinate_key_errors(child, f"{path}[{index}]"))
    return errors


def validate_v5b_recipe(recipe: dict[str, Any], data: dict[str, Any] | None = None) -> V5BRecipeValidation:
    data = data or load_v5b_data(); errors: list[str] = []; warnings: list[str] = []
    required = {
        "formatVersion", "id", "collection", "articleType", "constructionVariant", "sleeveIntent",
        "shoulderIntent", "necklineIntent", "collarIntent", "layeringIntent", "openingIntent",
        "surfaceTranslation", "baseArticleRecipe",
    }
    if set(recipe) != required:
        errors.append(f"V5B recipe keys must be exactly {sorted(required)}")
    if recipe.get("formatVersion") != "5.2.0": errors.append("formatVersion must be 5.2.0")
    if recipe.get("collection") != "V5BUpperBenchmark": errors.append("wrong V5B collection")
    article = recipe.get("articleType"); article_data = data["articles"]["articles"]
    if article not in article_data:
        errors.append(f"unknown V5B article {article!r}")
        return V5BRecipeValidation(False, tuple(errors), tuple(warnings))
    contract = article_data[article]
    if recipe.get("constructionVariant") not in contract["variants"]:
        errors.append(f"{article} does not support variant {recipe.get('constructionVariant')!r}")
    if recipe.get("sleeveIntent") not in contract["sleeves"]:
        errors.append(f"{article} does not support sleeve {recipe.get('sleeveIntent')!r}")
    if recipe.get("shoulderIntent") not in contract["shoulders"]:
        errors.append(f"{article} does not support shoulder {recipe.get('shoulderIntent')!r}")
    if recipe.get("necklineIntent") not in contract["necklines"]:
        errors.append(f"{article} does not support neckline {recipe.get('necklineIntent')!r}")
    if recipe.get("collarIntent") not in contract["collars"]:
        errors.append(f"{article} does not support collar {recipe.get('collarIntent')!r}")
    sleeve = data["sleeves"]["families"].get(recipe.get("sleeveIntent"), {})
    if sleeve.get("status") in {"EXPERIMENTAL", "NOT_VIABLE"}:
        errors.append(f"diagnostic batch may not use unproven sleeve family {recipe.get('sleeveIntent')}")
    base = recipe.get("baseArticleRecipe", {})
    v4 = validate_v4_recipe(base)
    errors.extend(f"V4 base: {message}" for message in v4.errors)
    warnings.extend(f"V4 base: {message}" for message in v4.warnings)
    if base and base.get("articleType") != contract["baseArticle"]:
        errors.append(f"{article} requires V4 base {contract['baseArticle']}")
    if article == "VEST_TOP" and recipe.get("layeringIntent") != "vest_over_inner":
        errors.append("VEST_TOP requires vest_over_inner layering")
    if article in {"CROPPED_JACKET", "STANDARD_JACKET"} and recipe.get("openingIntent") not in {"center_open", "partial_open"}:
        errors.append(f"{article} requires an outerwear opening")
    surface = recipe.get("surfaceTranslation", {})
    if set(surface) != {"primaryZone", "sleeveContinuation", "cuffTreatment"}:
        errors.append("surfaceTranslation has wrong semantic fields")
    if recipe.get("sleeveIntent") == "SLEEVELESS" and surface.get("sleeveContinuation") != "none":
        errors.append("sleeveless garment cannot continue surface design onto sleeves")
    if recipe.get("sleeveIntent") == "SHORT_SLEEVE" and surface.get("cuffTreatment") == "layered":
        errors.append("native short sleeves cannot request layered custom cuffs")
    errors.extend(_coordinate_key_errors({key: value for key, value in recipe.items() if key != "baseArticleRecipe"}))
    return V5BRecipeValidation(not errors, tuple(errors), tuple(warnings))


def _design(index: int, theme: str, rarity: str, archetype: str, name: str) -> dict[str, Any]:
    seed = 2026083000 + index * 104729 + (7919 if index in {9, 10} else 0)
    recipe = generate_v3_recipe(
        {"themeFamily": theme, "rarity": rarity, "archetype": archetype, "itemName": name},
        index,
        seed,
    )
    return recipe


def _base(index: int, design: dict[str, Any], base_article: str, *, aot: bool = False) -> dict[str, Any]:
    if base_article == "FITTED_SHIRT": _force_fitted(design)
    elif base_article == "VEST_TOP": _force_vest(design)
    elif base_article == "SHORT_OUTERWEAR": _force_short_outerwear(design)
    valid_focal = load_v4_data()["articles"]["articles"][base_article]["validFocalAreas"]
    if design["concept"]["focalArea"] not in valid_focal:
        design["concept"]["focalArea"] = "upper_chest" if "upper_chest" in valid_focal else valid_focal[0]
    collection = "AoTInspired" if aot else "NeutralBenchmark"
    return _wrap(design, outer_id=f"v4-v5b-{index:02d}", collection=collection, article_type=base_article)


def generate_v5b_benchmark() -> dict[str, Any]:
    """Return exactly twelve visible concepts; there is no hidden candidate pool."""

    aot = copy.deepcopy(next(r for r in generate_aot_v3_collection()["recipes"] if r["id"] == "aot-v3-05"))
    aot["itemName"] = "Rookwing Cropped Field Jacket"
    aot["itemDescription"] = "A premium cropped field jacket with layered cuffs, disciplined panels, and an original wing-like field crest."

    specs = [
        # article, variant, sleeve, shoulder, neckline, collar, layering, opening, theme, rarity, archetype, name, zone, continuation, cuff
        ("FITTED_SHIRT", "plain_tee", "SHORT_SLEEVE", "standard", "crew", "none", "single_layer", "closed", "beach_casual", "Common", "BUTTON_SHIRT", "Saltair Fitted Tee", "chest", "fabric_match", "simple"),
        ("FITTED_SHIRT", "structured_shirt", "ROLLED_CUFFED_SLEEVE", "narrow", "high", "utility", "single_layer", "buttoned", "cyber_tech", "Uncommon", "BUTTON_SHIRT", "Signalwork Rolled Shirt", "yoke", "trim_echo", "contrast"),
        ("SWEATER", "fitted_knit", "FITTED_LONG_SLEEVE", "standard", "crew", "none", "single_layer", "closed", "seasonal_soft", "Common", "SWEATER", "Maple Loom Knit", "hem", "fabric_match", "simple"),
        ("SWEATER", "patterned_knit", "LAYERED_INNER_OUTER_SLEEVE", "dropped", "high", "rounded", "collar_overlay", "closed", "creature_inspired", "Rare", "SWEATER", "Mosslight Familiar Knit", "chest", "trim_echo", "layered"),
        ("VEST_TOP", "waistcoat", "SLEEVELESS", "narrow", "v_neck", "none", "vest_over_inner", "buttoned", "formal_elegant", "Common", "BUTTON_SHIRT", "Duskline Waistcoat", "placket", "none", "none"),
        ("VEST_TOP", "utility_vest", "FITTED_LONG_SLEEVE", "standard", "high", "utility", "vest_over_inner", "buttoned", "cyber_tech", "Uncommon", "BUTTON_SHIRT", "Relay Utility Vest", "chest", "inner_layer_match", "simple"),
        ("CROPPED_JACKET", "moto_jacket", "ROLLED_CUFFED_SLEEVE", "dropped", "open", "lapel", "visible_inner_layer", "partial_open", "military_structured", "Uncommon", "JACKET", "Cinderstep Moto Jacket", "outer_panels", "trim_echo", "contrast"),
        ("CROPPED_JACKET", "military_jacket", "LAYERED_INNER_OUTER_SLEEVE", "standard", "high", "utility", "visible_inner_layer", "center_open", None, "Rare", "JACKET", None, "outer_panels", "trim_echo", "layered"),
        ("STANDARD_JACKET", "cardigan", "FITTED_LONG_SLEEVE", "dropped", "crew", "none", "visible_inner_layer", "center_open", "seasonal_soft", "Common", "JACKET", "Juniper Rain Cardigan", "hem", "fabric_match", "simple"),
        ("STANDARD_JACKET", "blazer", "LAYERED_INNER_OUTER_SLEEVE", "standard", "open", "lapel", "visible_inner_layer", "center_open", "celestial_fantasy", "Rare", "JACKET", "Gilded Evening Blazer", "outer_panels", "trim_echo", "layered"),
        ("BLOUSE", "sailor_blouse", "SHORT_SLEEVE", "narrow", "square", "sailor_like", "collar_overlay", "partial_open", "cyber_tech", "Uncommon", "BUTTON_SHIRT", "Rose Circuit Sailor Blouse", "collar", "fabric_match", "simple"),
        ("BLOUSE", "bow_blouse", "ROLLED_CUFFED_SLEEVE", "standard", "v_neck", "rounded", "collar_overlay", "partial_open", "storybook_whimsical", "Rare", "BUTTON_SHIRT", "Ribbonstar Bow Blouse", "collar", "trim_echo", "contrast"),
    ]
    recipes: list[dict[str, Any]] = []
    for index, spec in enumerate(specs, 1):
        article, variant, sleeve, shoulder, neckline, collar, layering, opening, theme, rarity, archetype, name, zone, continuation, cuff = spec
        design = aot if index == 8 else _design(index, theme, rarity, archetype, name)
        if index == 11:
            design["concept"]["focalArea"] = "center_chest"
            # Reuse the proven V3 two-system topology while translating it to
            # a romantic blouse vocabulary. Color-block remains the dominant
            # readable gesture; the small flower replaces the abstract glyph.
            design["paletteStory"] = "rose_sage"
        base_article = load_v5b_data()["articles"]["articles"][article]["baseArticle"]
        base = _base(index, design, base_article, aot=index == 8)
        recipe = {
            "formatVersion": "5.2.0", "id": f"v5b-{index:02d}", "collection": "V5BUpperBenchmark",
            "articleType": article, "constructionVariant": variant, "sleeveIntent": sleeve,
            "shoulderIntent": shoulder, "necklineIntent": neckline, "collarIntent": collar,
            "layeringIntent": layering, "openingIntent": opening,
            "surfaceTranslation": {"primaryZone": zone, "sleeveContinuation": continuation, "cuffTreatment": cuff},
            "baseArticleRecipe": base,
        }
        result = validate_v5b_recipe(recipe)
        if not result.valid: raise ValueError(f"invalid V5B recipe {recipe['id']}: {'; '.join(result.errors)}")
        recipes.append(recipe)
    return {
        "generatorVersion": "5.2.0", "collection": "V5BUpperBenchmark", "seed": 2026083000,
        "count": len(recipes), "hiddenCandidateCount": 0,
        "rarityCounts": {r: sum(x["baseArticleRecipe"]["designRecipe"]["rarity"] == r for x in recipes) for r in ("Common", "Uncommon", "Rare")},
        "recipes": recipes,
    }
