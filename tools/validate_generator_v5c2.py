#!/usr/bin/env python3
"""Independent static validation for V5C2 outputs and FS test pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png
from generator.renderers.fashionsense.upper_v5c2 import render_fs_v5c2
from generator.v5c2 import diagnose_v5c2_article, diagnose_v5c2_collection, generate_v5c2_batch


OUT = ROOT / "output" / "fashionsense" / "v5c2-vanilla-hoodie"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5C2-Vanilla-Hoodie"
UNIQUE_ID = "RNGClothing.FashionSense.V5C2VanillaHoodie"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _slug(value: str) -> str:
    import re
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


def _design(recipe):
    return recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]


def main() -> None:
    errors: list[str] = []
    checks: list[str] = []
    batch = generate_v5c2_batch()
    renders = [render_fs_v5c2(recipe) for recipe in batch["recipes"]]
    rerenders = [render_fs_v5c2(recipe) for recipe in batch["recipes"]]
    diagnostics = [diagnose_v5c2_article(render) for render in renders]
    collection = diagnose_v5c2_collection(batch["recipes"], renders, diagnostics)
    if not collection.passes:
        errors.extend(collection.errors)
    if any(a.texture != b.texture or a.sleeves_texture != b.sleeves_texture for a, b in zip(renders, rerenders)):
        errors.append("deterministic rerender mismatch")
    else:
        checks.append("deterministic direct logical-pixel shirt and sleeve rendering")
    manifest = _json(PACK / "manifest.json")
    expected_dependency = {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}
    if manifest.get("UniqueID") != UNIQUE_ID:
        errors.append("wrong test-pack UniqueID")
    if manifest.get("ContentPackFor") != expected_dependency:
        errors.append("wrong Fashion Sense 7.5.0 dependency contract")
    else:
        checks.append("Fashion Sense 7.5.0 content-pack contract")
    presets = _json(PACK / "preset_outfits.json")
    if len(presets) != 10:
        errors.append(f"expected ten coordinated presets, found {len(presets)}")
    preset_by_name = {preset["Name"]: preset for preset in presets}
    for recipe, render, diagnostic in zip(batch["recipes"], renders, diagnostics):
        name = _design(recipe)["itemName"]
        if not diagnostic.passes:
            errors.extend(f"{name}: {message}" for message in diagnostic.errors)
        output_dir = OUT / _slug(name)
        packed_shirt = read_rgba_png(output_dir / "shirt.png")
        if (packed_shirt["width"], packed_shirt["height"]) != (16, 64):
            errors.append(f"{name}: output Shirt must be 16x64")
        if packed_shirt["pixels"] != render.texture:
            errors.append(f"{name}: output Shirt differs from deterministic renderer")
        if any(pixel[3] not in {0, 255} for row in packed_shirt["pixels"] for pixel in row):
            errors.append(f"{name}: output Shirt has non-binary alpha")
        shirt_dir = PACK / "Shirts" / _folder(name)
        shirt_png = read_rgba_png(shirt_dir / "shirt.png")
        shirt_json = _json(shirt_dir / "shirt.json")
        if shirt_png["pixels"] != render.texture:
            errors.append(f"{name}: packed Shirt differs from renderer")
        direction_contract = {"FrontShirt": 0, "RightShirt": 16, "LeftShirt": 32, "BackShirt": 48}
        for key, y in direction_contract.items():
            model = shirt_json.get(key, {})
            if model.get("StartingPosition") != {"X": 0, "Y": y}:
                errors.append(f"{name}: wrong {key} source row")
            if model.get("ShirtSize") != {"Width": 16, "Length": 16}:
                errors.append(f"{name}: wrong {key} logical frame")
            if model.get("Scale") != 2.0 or model.get("BodyPosition") != {"X": 0, "Y": 32}:
                errors.append(f"{name}: wrong {key} scale/body anchor")
            if model.get("HideSleeves") is not False:
                errors.append(f"{name}: HideSleeves must remain false (missing-arm regression)")
        sleeves_dir = PACK / "Sleeves" / (_folder(name) + "Sleeves")
        sleeves_png = read_rgba_png(sleeves_dir / "sleeves.png")
        sleeves_json = _json(sleeves_dir / "sleeves.json")
        if (sleeves_png["width"], sleeves_png["height"]) != (384, 1344):
            errors.append(f"{name}: Sleeves atlas must be 384x1344")
        if sleeves_png["pixels"] != render.sleeves_texture:
            errors.append(f"{name}: packed Sleeves differ from deterministic renderer")
        for key, count in {"FrontSleeves": 62, "BackSleeves": 28, "RightSleeves": 42, "LeftSleeves": 42}.items():
            part = sleeves_json.get(key, {})
            if len(part.get("UniformAnimation", [])) != count:
                errors.append(f"{name}: {key} animation mapping is incomplete")
            if part.get("Scale") != 2.0 or part.get("BodyPosition") != {"X": 0, "Y": 0}:
                errors.append(f"{name}: {key} wrong Scale/BodyPosition")
            if not part.get("DisableNativeOffset") or not part.get("DrawBeforeShirt") or not part.get("UseShirtColors"):
                errors.append(f"{name}: {key} lost proven FS Sleeves flags")
        preset = preset_by_name.get(f"V5C2 - {name}")
        if not preset:
            errors.append(f"{name}: missing coordinated outfit preset")
        elif preset.get("ShirtId") != f"{UNIQUE_ID}/Shirt/{name}" or preset.get("SleevesId") != f"{UNIQUE_ID}/Sleeves/{name} Sleeves":
            errors.append(f"{name}: preset does not pair its Shirt and Sleeves")
    forbidden = ["Pants", "Shoes", "Accessories", "Hats"]
    leaked = [name for name in forbidden if (PACK / name).exists()]
    if leaked:
        errors.append(f"out-of-scope appearance folders leaked into pack: {leaked}")
    source = (ROOT / "generator" / "renderers" / "fashionsense" / "upper_v5c2.py").read_text(encoding="utf-8")
    if "hoodie.zip" in source or "style-profiles/hoodie" in source or "read_rgba_png" in source:
        errors.append("renderer appears to read or name a reference-art source")
    else:
        checks.append("generation code is isolated from reference pixels")
    validation = _json(OUT / "validation.json")
    if validation.get("status") != "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED":
        errors.append("output must remain explicitly experimental")
    else:
        checks.append("runtime status remains EXPERIMENTAL / NOT TESTED")
    result = {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "garments": 10,
        "hoodies": 5,
        "coordinatedSleeves": 10,
        "shirtFrame": [16, 16],
        "shirtScale": 2,
        "shirtBodyPosition": [0, 32],
        "previewOrder": ["FRONT", "RIGHT", "BACK", "LEFT"],
        "runtimePromotion": "EXPERIMENTAL",
    }
    (OUT / "filesystem-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
