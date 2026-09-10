"""Semantic recipe assembly for the controlled grammar + palette proof.

This module deliberately exposes exactly twelve curated recipes. It reads the
reference-derived specs and does not participate in open-ended generation,
rarity routing, or production batches.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTROL_PATH = ROOT / "generator" / "data" / "reference_engine" / "controlled_grammar_palette_test.json"
GRAMMAR_PATH = ROOT / "specs" / "reference_corpus" / "garment_grammars.json"
ROLE_PATH = ROOT / "specs" / "palettes" / "color_roles.json"
MATERIAL_PATH = ROOT / "specs" / "palettes" / "material_color_behavior.json"
PALETTE_PATH = ROOT / "specs" / "palettes" / "palette_stories.json"

ALLOWED_GRAMMARS = (
    "FITTED_TEE",
    "OPEN_CASUAL_SHIRT",
    "OPEN_CARDIGAN",
    "SWEATER_VEST",
    "FORMAL_WAISTCOAT",
    "CREWNECK_SWEATSHIRT",
    "CROPPED_BOMBER",
    "WORK_JACKET",
    "FITTED_BLAZER",
    "WRAP_TOP",
    "SAILOR_TOP",
    "BELTED_TUNIC",
)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_controlled_test_data() -> dict[str, Any]:
    grammar_data = _json(GRAMMAR_PATH)
    palette_data = _json(PALETTE_PATH)
    material_data = _json(MATERIAL_PATH)
    role_data = _json(ROLE_PATH)
    return {
        "control": _json(CONTROL_PATH),
        "grammars": {item["id"]: item for item in grammar_data["grammars"]},
        "palettes": {item["id"]: item for item in palette_data["stories"]},
        "materials": {item["id"]: item for item in material_data["behaviors"]},
        "roles": role_data["roles"],
    }


def generate_controlled_test_recipes(data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = data or load_controlled_test_data()
    recipes: list[dict[str, Any]] = []
    for item in data["control"]["specimens"]:
        recipe = copy.deepcopy(item)
        recipe["formatVersion"] = data["control"]["formatVersion"]
        recipe["collection"] = data["control"]["collection"]
        recipe["runtimeContract"] = copy.deepcopy(data["control"]["runtimeContract"])
        recipe["grammar"] = copy.deepcopy(data["grammars"][item["grammarId"]])
        recipe["materialBehavior"] = copy.deepcopy(data["materials"][item["materialId"]])
        recipe["paletteStory"] = copy.deepcopy(data["palettes"][item["paletteStoryId"]])
        recipes.append(recipe)
    return recipes


def validate_controlled_test_recipes(
    recipes: list[dict[str, Any]], data: dict[str, Any] | None = None
) -> tuple[str, ...]:
    data = data or load_controlled_test_data()
    errors: list[str] = []
    ids = [recipe["id"] for recipe in recipes]
    grammars = [recipe["grammarId"] for recipe in recipes]
    if len(recipes) != 12:
        errors.append(f"expected exactly 12 recipes, found {len(recipes)}")
    if tuple(grammars) != ALLOWED_GRAMMARS:
        errors.append(f"grammar selection/order differs from controlled allowlist: {grammars}")
    if len(ids) != len(set(ids)):
        errors.append("recipe identifiers are not unique")
    prohibited = {"HENLEY", "VARSITY_JACKET", "MOTO_JACKET"} & set(grammars)
    if prohibited:
        errors.append(f"provisional grammars leaked into controlled test: {sorted(prohibited)}")
    valid_roles = set(data["roles"])
    for recipe in recipes:
        if recipe["grammarId"] not in data["grammars"]:
            errors.append(f"{recipe['id']}: missing grammar")
        if recipe["materialId"] not in data["materials"]:
            errors.append(f"{recipe['id']}: missing material behavior")
        if recipe["paletteStoryId"] not in data["palettes"]:
            errors.append(f"{recipe['id']}: missing palette story")
        story_roles = set(recipe["paletteStory"]["roles"])
        if not story_roles <= valid_roles:
            errors.append(f"{recipe['id']}: unknown palette roles {sorted(story_roles - valid_roles)}")
        if recipe["nativeSleeveFabric"] not in story_roles:
            errors.append(f"{recipe['id']}: native sleeve fabric role is unavailable")
        contract = recipe["runtimeContract"]
        if not contract["nativeFarmerSleeves"] or contract["customSleeves"]:
            errors.append(f"{recipe['id']}: runtime sleeve contract is not native-only")
        if contract["scale"] != 2.0 or contract["bodyPosition"] != {"X": 0, "Y": 32}:
            errors.append(f"{recipe['id']}: frozen Fashion Sense anchor changed")
        if len(recipe["axes"]) != 10:
            errors.append(f"{recipe['id']}: expected ten diversity axes")
    return tuple(errors)
