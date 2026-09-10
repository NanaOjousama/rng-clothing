#!/usr/bin/env python3
"""Independent static validation for generated V5B assets and test pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png
from generator.renderers.fashionsense import render_fs_v5b
from generator.v5b import diagnose_v5b_article, diagnose_v5b_collection, generate_v5b_benchmark


OUT = ROOT / "output" / "fashionsense" / "v5b-upper-garments"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5B-Upper-Garments"
UNIQUE_ID = "RNGClothing.FashionSense.V5BUpper"


def _folder(value: str) -> str:
    import re
    slug = "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
    return "".join(piece.title() for piece in slug.split("_"))


def _json(path: Path): return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    errors: list[str] = []; checks: list[str] = []
    batch = generate_v5b_benchmark(); renders = [render_fs_v5b(r) for r in batch["recipes"]]
    rerenders = [render_fs_v5b(r) for r in batch["recipes"]]
    diagnostics = [diagnose_v5b_article(r) for r in renders]
    collection = diagnose_v5b_collection(batch["recipes"], renders, diagnostics)
    if not collection.passes: errors.extend(collection.errors)
    if any(a.texture != b.texture or a.sleeves_texture != b.sleeves_texture for a, b in zip(renders, rerenders)):
        errors.append("deterministic rerender mismatch")
    else: checks.append("deterministic shirt and sleeve rendering")

    manifest = _json(PACK / "manifest.json")
    if manifest.get("UniqueID") != UNIQUE_ID: errors.append("wrong pack UniqueID")
    if manifest.get("ContentPackFor") != {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}: errors.append("wrong Fashion Sense dependency contract")
    else: checks.append("Fashion Sense 7.5.0 content-pack dependency")
    if (PACK / "Pants").exists() or (PACK / "Shoes").exists(): errors.append("deferred lower-body article leaked into V5B pack")
    presets = _json(PACK / "preset_outfits.json")
    if len(presets) != 12: errors.append(f"expected 12 paired presets, found {len(presets)}")
    preset_by_name = {p["Name"]: p for p in presets}
    companion_count = 0
    for recipe, render in zip(batch["recipes"], renders):
        design = recipe["baseArticleRecipe"]["designRecipe"]; name = design["itemName"]
        shirt_dir = PACK / "Shirts" / _folder(name)
        shirt_png = read_rgba_png(shirt_dir / "shirt.png"); shirt_json = _json(shirt_dir / "shirt.json")
        if (shirt_png["width"], shirt_png["height"]) != (16, 64): errors.append(f"{name}: wrong shirt texture dimensions")
        if shirt_png["pixels"] != render.texture: errors.append(f"{name}: packed shirt differs from deterministic renderer")
        if any(px[3] not in {0, 255} for row in shirt_png["pixels"] for px in row): errors.append(f"{name}: non-binary shirt alpha")
        direction_contract = {"FrontShirt": 0, "RightShirt": 16, "LeftShirt": 32, "BackShirt": 48}
        for key, y in direction_contract.items():
            model = shirt_json.get(key, {})
            if model.get("StartingPosition") != {"X": 0, "Y": y}: errors.append(f"{name}: wrong {key} row")
            if model.get("ShirtSize") != {"Width": 16, "Length": 16}: errors.append(f"{name}: wrong {key} frame size")
            if model.get("Scale") != 2.0 or model.get("BodyPosition") != {"X": 0, "Y": 32}: errors.append(f"{name}: wrong {key} anchor/scale")
        preset = preset_by_name.get(f"V5B - {name}")
        if preset is None: errors.append(f"{name}: missing coordinated preset")
        elif preset.get("ShirtId") != f"{UNIQUE_ID}/Shirt/{name}": errors.append(f"{name}: preset shirt ID mismatch")
        if render.companion_required:
            companion_count += 1; sleeve_dir = PACK / "Sleeves" / (_folder(name) + "Sleeves")
            sleeve_png = read_rgba_png(sleeve_dir / "sleeves.png"); sleeve_json = _json(sleeve_dir / "sleeves.json")
            if (sleeve_png["width"], sleeve_png["height"]) != (384, 1344): errors.append(f"{name}: wrong sleeves atlas dimensions")
            if sleeve_png["pixels"] != render.sleeves_texture: errors.append(f"{name}: packed sleeves differ from deterministic renderer")
            if any(px[3] not in {0, 255} for row in sleeve_png["pixels"] for px in row): errors.append(f"{name}: non-binary sleeves alpha")
            if sleeve_json.get("Name") != f"{name} Sleeves": errors.append(f"{name}: companion Name mismatch")
            if preset and preset.get("SleevesId") != f"{UNIQUE_ID}/Sleeves/{name} Sleeves": errors.append(f"{name}: preset sleeves ID mismatch")
        elif recipe["sleeveIntent"] == "SHORT_SLEEVE":
            if preset and preset.get("SleevesId") != "PeacefulEnd.FashionSense.LocalPack/Sleeves/Default (Short)": errors.append(f"{name}: short-sleeve preset does not select FS Default (Short)")
        else:
            if preset and preset.get("SleevesId") != "None": errors.append(f"{name}: sleeveless preset should select None")
    if companion_count != 10: errors.append(f"expected 10 custom sleeves companions, found {companion_count}")
    else: checks.append("ten coordinated full-motion custom Sleeves appearances")
    validation = _json(OUT / "validation.json")
    if validation.get("status") != "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED": errors.append("output promotion status is not explicitly experimental")
    else: checks.append("runtime state remains EXPERIMENTAL / NOT TESTED")
    result = {
        "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors,
        "garments": 12, "customSleeves": companion_count, "shirtFrame": [16, 16], "shirtScale": 2,
        "customSleeveFrame": [32, 64], "customSleeveScale": 2,
        "previewOrder": ["FRONT", "RIGHT", "BACK", "LEFT"], "runtimePromotion": "EXPERIMENTAL",
    }
    (OUT / "filesystem-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors: raise SystemExit(1)


if __name__ == "__main__": main()
