"""V5A semantic recipes for unified Fashion Sense garments.

V5A wraps frozen V3 designs.  It adds article and sleeve intent, but never
renderer coordinates or Fashion Sense offsets.
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
DATA = ROOT / "generator" / "data" / "v5a"
SCHEMA = ROOT / "generator" / "schema" / "garment_recipe_v5a.schema.json"


@dataclass(frozen=True)
class V5ARecipeValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v5a_data() -> dict[str, Any]:
    return {
        "schema": _json(SCHEMA),
        "articles": _json(DATA / "article_adapters.json"),
        "sleeves": _json(DATA / "sleeve_grammar.json"),
    }


def _coordinate_key_errors(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"x", "y", "row", "column", "coordinates", "pixels", "offset"}:
                errors.append(f"{path}.{key}: renderer coordinate key is forbidden in semantic V5A recipes")
            errors.extend(_coordinate_key_errors(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_coordinate_key_errors(child, f"{path}[{index}]"))
    return errors


def validate_v5a_recipe(recipe: dict[str, Any], data: dict[str, Any] | None = None) -> V5ARecipeValidation:
    data = data or load_v5a_data()
    errors: list[str] = []
    warnings: list[str] = []
    expected = {"formatVersion", "id", "articleType", "promotionStatus", "sleeveIntent", "articleIntent", "articleSurfacePlan", "designRecipe"}
    if set(recipe) != expected:
        errors.append(f"V5A keys must be exactly {sorted(expected)}")
    if recipe.get("formatVersion") != "5A":
        errors.append("formatVersion must be V5A")
    if recipe.get("promotionStatus") != "EXPERIMENTAL":
        errors.append("V5A prototypes may only be EXPERIMENTAL")
    article_type = recipe.get("articleType")
    articles = data["articles"]["articles"]
    if article_type not in articles:
        errors.append(f"unknown V5A article type {article_type!r}")
        return V5ARecipeValidation(False, tuple(errors), tuple(warnings))
    adapter = articles[article_type]
    design = recipe.get("designRecipe", {})
    v3 = validate_recipe_v3(design)
    errors.extend(f"V3 design: {message}" for message in v3.errors)
    warnings.extend(f"V3 design: {message}" for message in v3.warnings)
    if design.get("archetype") not in adapter["compatibleArchetypes"]:
        errors.append(f"{article_type} is incompatible with V3 archetype {design.get('archetype')}")
    intent = recipe.get("articleIntent", {})
    missing = set(adapter["requiredIntentKeys"]) - set(intent)
    if missing:
        errors.append(f"{article_type} misses article intent {sorted(missing)}")
    length = intent.get("length")
    if length not in adapter["allowedLengths"]:
        errors.append(f"{article_type} length {length!r} is unsupported")
    sleeve_name = recipe.get("sleeveIntent")
    sleeves = data["sleeves"]["sleeves"]
    if sleeve_name not in sleeves:
        errors.append(f"unknown sleeve intent {sleeve_name!r}")
    else:
        sleeve = sleeves[sleeve_name]
        if article_type not in sleeve["compatibleArticles"]:
            errors.append(f"{sleeve_name} is incompatible with {article_type}")
        if sleeve["status"] == "COMPANION_REQUIRED":
            errors.append(f"{sleeve_name} needs a separate full-animation Fashion Sense Sleeves appearance")
    surface = recipe.get("articleSurfacePlan", {})
    targets = [surface.get("primaryTarget")] + list(surface.get("supportTargets", []))
    invalid_targets = set(targets) - set(adapter["validSurfaceTargets"])
    if invalid_targets:
        errors.append(f"{article_type} has invalid surface targets {sorted(invalid_targets)}")
    rarity = design.get("rarity")
    expected_systems = {"Common": 1, "Uncommon": 2, "Rare": 3}.get(rarity)
    if expected_systems is not None and len(targets) != expected_systems:
        errors.append(f"{rarity} V5A article plan must use exactly {expected_systems} article-aware target(s)")
    errors.extend(_coordinate_key_errors({key: value for key, value in recipe.items() if key != "designRecipe"}))
    return V5ARecipeValidation(not errors, tuple(errors), tuple(warnings))


def _named(design: dict[str, Any], name: str, description: str) -> dict[str, Any]:
    result = copy.deepcopy(design)
    result["itemName"] = name
    result["itemDescription"] = description
    return result


def _as_pinafore_bodice(design: dict[str, Any]) -> dict[str, Any]:
    """Translate a V3 surface concept to the reusable buttoned pinafore frame."""
    result = copy.deepcopy(design)
    result["archetype"] = "BUTTON_SHIRT"
    result["concept"]["garmentRole"] = "tailored_shirt"
    result["concept"]["silhouetteGoal"] = "fitted_tailored"
    result["construction"] = {
        "fit": "fitted", "neckline": "open", "collar": "small_folded", "closure": "buttons",
        "layering": "overlay_panel", "hem": "plain", "panelLayout": "yoke",
    }
    result["substantialFeatures"] = ["yoke"]
    return result


def _wrap(
    design: dict[str, Any], *, item_id: str, article_type: str,
    sleeve: str, intent: dict[str, str], primary: str,
    supports: list[str], topology: str,
) -> dict[str, Any]:
    recipe = {
        "formatVersion": "5A",
        "id": item_id,
        "articleType": article_type,
        "promotionStatus": "EXPERIMENTAL",
        "sleeveIntent": sleeve,
        "articleIntent": intent,
        "articleSurfacePlan": {"primaryTarget": primary, "supportTargets": supports, "topology": topology},
        "designRecipe": design,
    }
    validation = validate_v5a_recipe(recipe)
    if not validation.valid:
        raise ValueError(f"invalid V5A recipe {item_id}: {'; '.join(validation.errors)}")
    return recipe


def generate_v5a_collection() -> dict[str, Any]:
    neutral = {item["id"]: item for item in generate_benchmark_batch()["recipes"]}
    aot = {item["id"]: item for item in generate_aot_v3_collection()["recipes"]}
    recipes = [
        _wrap(
            _named(neutral["v3-benchmark-04"], "Meadowline Day Dress", "A light A-line day dress with a neat waist and a restrained meadow accent."),
            item_id="v5a-dress-common", article_type="DRESS", sleeve="short_sleeve",
            intent={"silhouette": "a_line", "length": "short", "waist": "natural", "bodice": "relaxed", "hem": "clean"},
            primary="bodice", supports=[], topology="front_only",
        ),
        _wrap(
            _named(_as_pinafore_bodice(neutral["v3-benchmark-05"]), "Berryglass Pinafore Dress", "A layered berry-toned pinafore with a buttoned bodice, high waist, and playful finished hem."),
            item_id="v5a-dress-uncommon", article_type="DRESS", sleeve="sleeveless",
            intent={"silhouette": "pinafore", "length": "medium", "waist": "high", "bodice": "layered", "hem": "layered"},
            primary="waist", supports=["hem"], topology="wrap",
        ),
        _wrap(
            _named(neutral["v3-benchmark-09"], "Gilded Starfall Dress", "A softly flared midnight dress with a bright belt rhythm and restrained celestial finishing."),
            item_id="v5a-dress-rare", article_type="DRESS", sleeve="fitted_long_sleeve",
            intent={"silhouette": "soft_flare", "length": "medium", "waist": "belted", "bodice": "panelled", "hem": "layered"},
            primary="bodice", supports=["waist", "hem"], topology="front_back",
        ),
        _wrap(
            _named(neutral["v3-benchmark-02"], "Mapleforge Work One-Piece", "A warm practical work one-piece organized around a clean apron front and useful waist."),
            item_id="v5a-onepiece-common", article_type="ONE_PIECE", sleeve="short_sleeve",
            intent={"concept": "blacksmith_workwear", "lowerForm": "work_apron", "length": "short", "waist": "belted", "hem": "clean"},
            primary="utility_region", supports=[], topology="front_only",
        ),
        _wrap(
            _named(neutral["v3-benchmark-07"], "Circuit Cadet Uniform", "A technical academy uniform with a disciplined waist and coordinated lower panels."),
            item_id="v5a-onepiece-uncommon", article_type="ONE_PIECE", sleeve="fitted_long_sleeve",
            intent={"concept": "academy_uniform", "lowerForm": "uniform_panel", "length": "medium", "waist": "contrast", "hem": "structured"},
            primary="upper_torso", supports=["waist"], topology="front_back",
        ),
        _wrap(
            _named(neutral["v3-benchmark-10"], "Ribbonward Story Costume", "A premium storybook one-piece with a fitted upper frame, sash, and layered adventuring panels."),
            item_id="v5a-onepiece-rare", article_type="ONE_PIECE", sleeve="short_sleeve",
            intent={"concept": "storybook_adventurer", "lowerForm": "split_tabard", "length": "bounded_long", "waist": "sashed", "hem": "layered"},
            primary="upper_torso", supports=["waist", "lower_panels"], topology="asymmetric_front",
        ),
        _wrap(
            _named(neutral["v3-benchmark-03"], "Slateway Long Cardigan", "A quiet open-front cardigan with a rounded hip-length fall and tailored collar line."),
            item_id="v5a-outer-common", article_type="BOUNDED_LONG_OUTERWEAR", sleeve="fitted_long_sleeve",
            intent={"length": "hip", "front": "open", "construction": "cardigan", "hem": "rounded"},
            primary="lapel", supports=[], topology="construction_bound",
        ),
        _wrap(
            _named(neutral["v3-benchmark-08"], "Brasswatch Field Coat", "A structured upper-thigh field coat with a partial opening, split hem, and disciplined utility trim."),
            item_id="v5a-outer-uncommon", article_type="BOUNDED_LONG_OUTERWEAR", sleeve="fitted_long_sleeve",
            intent={"length": "upper_thigh", "front": "partially_open", "construction": "military", "hem": "split"},
            primary="outer_panels", supports=["extended_hem"], topology="front_back",
        ),
        _wrap(
            _named(aot["aot-v3-05"], "Rookwatch Field Long Jacket", "A premium bounded field jacket with a tan shell, fitted dark layer, regiment-like geometry, and controlled long panels."),
            item_id="v5a-outer-rare", article_type="BOUNDED_LONG_OUTERWEAR", sleeve="fitted_long_sleeve",
            intent={"length": "bounded_long", "front": "open", "construction": "military", "hem": "layered"},
            primary="lapel", supports=["outer_panels", "back_panel"], topology="front_back",
        ),
    ]
    return {
        "generatorVersion": "5A.0.0",
        "status": "EXPERIMENTAL",
        "count": 9,
        "articleCounts": {article: sum(item["articleType"] == article for item in recipes) for article in ("DRESS", "ONE_PIECE", "BOUNDED_LONG_OUTERWEAR")},
        "rarityCounts": {rarity: sum(item["designRecipe"]["rarity"] == rarity for item in recipes) for rarity in ("Common", "Uncommon", "Rare")},
        "recipes": recipes,
    }
