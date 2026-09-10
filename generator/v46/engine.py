"""Coordinate-free semantic fixtures for the V4.6 runtime proof."""

from __future__ import annotations

import copy


def generate_v46_prototypes() -> list[dict]:
    items = [
        {"formatVersion": "4.6", "id": "v46-pants-common-01", "name": "Wayfarer Field Trousers", "description": "Fitted field trousers with a clean waistband and deliberate ankle finish.", "styleProfile": "AoTInspired", "articleType": "FITTED_PANTS", "rarity": "Common", "semanticZones": {"primary": "fitted_leg_mass", "support": "waistband", "accent": "ankle_termination"}, "paletteStory": "warm_field_neutral", "runtimeStatus": "EXPERIMENTAL"},
        {"formatVersion": "4.6", "id": "v46-pants-rare-01", "name": "Crossline Scout Trousers", "description": "Fitted scout trousers with side panels, knee articulation, and one restrained utility rhythm.", "styleProfile": "AoTInspired", "articleType": "FITTED_PANTS", "rarity": "Rare", "semanticZones": {"primary": "side_panel", "support": "knee_panel", "accent": "single_harness_rhythm"}, "paletteStory": "field_olive_leather", "runtimeStatus": "EXPERIMENTAL"},
        {"formatVersion": "4.6", "id": "v46-shoes-common-01", "name": "Trailguard Field Shoes", "description": "Compact practical field shoes with a clearly terminated sole.", "styleProfile": "AoTInspired", "articleType": "FOOTWEAR", "rarity": "Common", "semanticZones": {"primary": "vamp", "support": "sole", "accent": "none"}, "paletteStory": "charcoal_leather", "runtimeStatus": "EXPERIMENTAL"},
        {"formatVersion": "4.6", "id": "v46-shoes-rare-01", "name": "Rampart Scout Boots", "description": "Compact scout boots with a shaped shaft, cuff, sole, and controlled strap accent.", "styleProfile": "AoTInspired", "articleType": "FOOTWEAR", "rarity": "Rare", "semanticZones": {"primary": "shaft", "support": "cuff_and_sole", "accent": "single_strap"}, "paletteStory": "deep_brown_brass", "runtimeStatus": "EXPERIMENTAL"},
    ]
    for item in items:
        errors = validate_v46_recipe(item)
        if errors:
            raise ValueError(f"{item['id']}: {'; '.join(errors)}")
    return copy.deepcopy(items)


def validate_v46_recipe(recipe: dict) -> tuple[str, ...]:
    errors = []
    if recipe.get("formatVersion") != "4.6": errors.append("formatVersion must be 4.6")
    if recipe.get("articleType") not in {"FITTED_PANTS", "FOOTWEAR"}: errors.append("unsupported V4.6 article")
    if recipe.get("rarity") not in {"Common", "Rare"}: errors.append("runtime proof supports Common and Rare only")
    if recipe.get("runtimeStatus") != "EXPERIMENTAL": errors.append("prototype must remain EXPERIMENTAL before manual evidence")
    zones = recipe.get("semanticZones", {})
    if set(zones) != {"primary", "support", "accent"}: errors.append("semantic zones are incomplete")
    if recipe.get("rarity") == "Rare" and zones.get("accent") in {None, "none"}: errors.append("Rare needs a controlled accent")
    return tuple(errors)
