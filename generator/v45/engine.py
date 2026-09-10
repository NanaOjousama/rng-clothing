"""Coordinate-free V4.5 prototype semantics over the frozen V3/V4 concept."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEMANTICS = ROOT / "generator" / "data" / "v45" / "article_semantics.json"


def load_v45_data() -> dict[str, Any]:
    return json.loads(SEMANTICS.read_text(encoding="utf-8"))


def _recipe(identifier, name, description, article, subtype, rarity, primary, support, focal, status):
    return {
        "formatVersion": "4.5", "id": identifier, "name": name, "description": description,
        "designConcept": "aot-scout-fieldwear-v45", "styleProfile": "AoTInspired",
        "articleType": article, "articleSubtype": subtype, "rarity": rarity,
        "composition": {"primarySystem": primary, "supportSystem": support, "focalFeature": focal},
        "runtimeStatus": status,
    }


def generate_v45_prototypes() -> list[dict[str, Any]]:
    recipes = [
        _recipe("v45-pants-01", "Wayfarer Field Trousers", "Fitted cream field trousers with a disciplined waistband and dark utility cuffs.", "PANTS", "FITTED_FIELD_TROUSERS", "Common", "waist_trim", "none", "none", "EXPERIMENTAL"),
        _recipe("v45-pants-02", "Crossline Scout Trousers", "Olive fitted trousers with knee panels and one restrained leather utility rhythm.", "PANTS", "PANEL_FIELD_TROUSERS", "Rare", "knee_panel", "side_utility_seam", "single_harness_rhythm", "EXPERIMENTAL"),
        _recipe("v45-skirt-01", "Palisade Field Skirt", "A compact tan field skirt with controlled pleats and a dark structured hem.", "SKIRT", "SHORT_PLEATED_SKIRT", "Uncommon", "pleat_rhythm", "hem_border", "none", "EXPERIMENTAL"),
        _recipe("v45-shoes-01", "Trailguard Field Shoes", "Practical dark field shoes with a restrained contrasting sole.", "FOOTWEAR", "FIELD_SHOES", "Common", "sole_contrast", "none", "none", "EXPERIMENTAL"),
        _recipe("v45-shoes-02", "Rampart Scout Boots", "Tall dark utility boots with fitted cuffs and one leather-like strap.", "FOOTWEAR", "TALL_BOOTS", "Rare", "cuff_trim", "sole_contrast", "single_strap", "EXPERIMENTAL"),
        _recipe("v45-mantle-01", "Verdant Regiment Mantle", "A muted field-green mantle with an original split-feather back crest and warm border.", "MANTLE", "BACK_FIELD_MANTLE", "Rare", "back_emblem", "border_trim", "clasp_accent", "EXPERIMENTAL"),
        _recipe("v45-tail-01", "Rookfield Coat-Tail Diagnostic", "A split lower-tail companion for static and motion-failure evaluation only.", "COAT_TAIL_COMPANION", "SPLIT_TAIL", "Rare", "split_tail", "edge_trim", "back_hem", "NOT_READY"),
    ]
    for recipe in recipes:
        errors = validate_v45_recipe(recipe)
        if errors:
            raise ValueError(f"{recipe['id']}: {'; '.join(errors)}")
    return copy.deepcopy(recipes)


def validate_v45_recipe(recipe: dict[str, Any]) -> tuple[str, ...]:
    data = load_v45_data(); errors = []
    if recipe.get("formatVersion") != "4.5": errors.append("formatVersion must be 4.5")
    article = recipe.get("articleType")
    if article not in data["articles"]: errors.append("unknown article type")
    else:
        allowed = set(data["articles"][article]["allowedSystems"]) | {"none"}
        for key in ("primarySystem", "supportSystem", "focalFeature"):
            if recipe.get("composition", {}).get(key) not in allowed:
                errors.append(f"{key} is not valid for {article}")
    rarity = recipe.get("rarity")
    if rarity not in data["rarity"]: errors.append("unsupported rarity")
    elif recipe.get("composition"):
        support = recipe["composition"]["supportSystem"] != "none"
        focal = recipe["composition"]["focalFeature"] != "none"
        budget = data["rarity"][rarity]
        if support and budget["supportSystems"] < 1: errors.append("support exceeds rarity budget")
        if focal and budget["focalFeatures"] < 1: errors.append("focal feature exceeds rarity budget")
        if rarity == "Rare" and (not support or not focal): errors.append("Rare misses support/focal richness floor")
    if article == "COAT_TAIL_COMPANION" and recipe.get("runtimeStatus") != "NOT_READY": errors.append("coat tail must remain NOT_READY")
    return tuple(errors)
