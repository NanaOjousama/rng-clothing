#!/usr/bin/env python3
"""Revalidate the sealed grammar/palette proof and its installable pack."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.controlled_test.engine import generate_controlled_test_recipes
from generator.controlled_test.validation import validate_collection
from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense.reference_grammar import render_controlled_garment


PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Controlled-Grammar-Palette-Test"
MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))


def main() -> None:
    recipes = generate_controlled_test_recipes()
    renders = [render_controlled_garment(recipe) for recipe in recipes]
    collection = validate_collection(recipes, renders)
    errors: list[str] = []
    if collection["status"] != "PASS_STATIC_RUNTIME_NOT_TESTED":
        errors.append("collection structural validation failed")
    if (PACK / "Sleeves").exists():
        errors.append("custom Sleeves directory leaked into pack")
    presets = json.loads((PACK / "preset_outfits.json").read_text(encoding="utf-8"))
    if len(presets) != 12 or any(item["SleevesId"] != "None" for item in presets):
        errors.append("preset count or native-sleeve contract invalid")
    for recipe, render in zip(recipes, renders):
        folder = "".join(part.capitalize() for part in "".join(ch if ch.isalnum() else " " for ch in recipe["name"]).split())
        texture = PACK / "Shirts" / folder / "shirt.png"
        model_path = PACK / "Shirts" / folder / "shirt.json"
        if not texture.exists() or not model_path.exists():
            errors.append(f"{recipe['id']}: missing Shirt files")
            continue
        image = read_rgba_png(texture)
        if [image["width"], image["height"]] != [16, 64]:
            errors.append(f"{recipe['id']}: texture is not 16x64")
        generated_hash = hashlib.sha256(encode_rgba_png(render.texture)).hexdigest()
        installed_hash = hashlib.sha256(texture.read_bytes()).hexdigest()
        if generated_hash != installed_hash:
            errors.append(f"{recipe['id']}: nondeterministic or stale texture")
        model = json.loads(model_path.read_text(encoding="utf-8"))
        for key, y in MODELS:
            view = model.get(key, {})
            if not (
                view.get("Scale") == 2.0
                and view.get("BodyPosition") == {"X": 0, "Y": 32}
                and view.get("StartingPosition") == {"X": 0, "Y": y}
                and view.get("HideSleeves") is False
                and len(view.get("SleeveColors", [])) == 3
            ):
                errors.append(f"{recipe['id']}: {key} runtime contract invalid")
    if errors:
        print("FAIL_STATIC")
        for error in errors:
            print("-", error)
        raise SystemExit(1)
    print("PASS_STATIC_RUNTIME_NOT_TESTED")
    print("12 recipes; 12 Shirt appearances; 12 presets; 66 diversity pairs")
    print("Native Farmer sleeves only; deterministic 16x64 atlases")


if __name__ == "__main__":
    main()
