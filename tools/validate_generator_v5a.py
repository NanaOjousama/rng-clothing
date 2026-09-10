#!/usr/bin/env python3
"""Validate Generator V5A semantics, pixels, Fashion Sense pack, and scope."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import render_fs_v5a
from generator.v5a import generate_v5a_collection, validate_v5a_recipe
from generator.v5a.validation import diagnose_v5a, diagnose_v5a_collection


OUT = ROOT / "output" / "fashionsense" / "v5a"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5A-Unified-Garments"


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def slug(value: str) -> str:
    import re
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    first = generate_v5a_collection()
    second = generate_v5a_collection()
    check(first == second, "V5A semantic generation is not deterministic", errors)
    saved = ROOT / "output" / "recipes" / "v5a_unified_collection.json"
    check(saved.exists(), "saved V5A recipe collection is missing", errors)
    if saved.exists():
        check(json.loads(saved.read_text(encoding="utf-8")) == first, "saved V5A recipes differ from engine", errors)
    renders = []
    diagnostics = []
    folder_map = {"DRESS": "dress", "ONE_PIECE": "one-piece", "BOUNDED_LONG_OUTERWEAR": "long-outerwear"}
    texture_hashes: dict[str, str] = {}
    for recipe in first["recipes"]:
        semantic = validate_v5a_recipe(recipe)
        errors.extend(f"{recipe['id']}: {message}" for message in semantic.errors)
        render_a = render_fs_v5a(recipe)
        render_b = render_fs_v5a(recipe)
        check(encode_rgba_png(render_a.texture) == encode_rgba_png(render_b.texture), f"{recipe['id']}: render is not deterministic", errors)
        render = render_a
        diagnostic = diagnose_v5a(render)
        renders.append(render)
        diagnostics.append(diagnostic)
        errors.extend(f"{recipe['id']}: {message}" for message in diagnostic.errors)
        warnings.extend(f"{recipe['id']}: {message}" for message in diagnostic.warnings)
        path = OUT / folder_map[recipe["articleType"]] / f"{slug(recipe['designRecipe']['itemName'])}.png"
        check(path.exists(), f"{recipe['id']}: native PNG missing", errors)
        if path.exists():
            png = read_rgba_png(path)
            check((png["width"], png["height"]) == (16, render.frame_height * 4), f"{recipe['id']}: wrong native texture dimensions", errors)
            check(set(png["filters"]) == {0}, f"{recipe['id']}: PNG scanline filtering must be zero", errors)
            check({pixel[3] for row in png["pixels"] for pixel in row} <= {0, 255}, f"{recipe['id']}: semitransparent pixels found", errors)
            expected_hash = hashlib.sha256(encode_rgba_png(render.texture)).hexdigest()
            check(png["sha256"] == expected_hash, f"{recipe['id']}: saved pixels differ from renderer", errors)
            texture_hashes[recipe["id"]] = expected_hash
    collection = diagnose_v5a_collection(first["recipes"], renders, diagnostics)
    errors.extend(collection.errors)
    warnings.extend(collection.warnings)
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    check(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, "Fashion Sense dependency contract changed", errors)
    shirts = sorted((PACK / "Shirts").glob("*/shirt.json"))
    check(len(shirts) == 9, "V5A test pack must contain exactly nine Shirt appearances", errors)
    by_name = {recipe["designRecipe"]["itemName"]: (recipe, render) for recipe, render in zip(first["recipes"], renders)}
    for path in shirts:
        model = json.loads(path.read_text(encoding="utf-8"))
        check(model["Name"] in by_name, f"{path}: unknown test garment", errors)
        if model["Name"] not in by_name:
            continue
        recipe, render = by_name[model["Name"]]
        h = render.frame_height
        for field, y in (("FrontShirt", 0), ("RightShirt", h), ("LeftShirt", h * 2), ("BackShirt", h * 3)):
            view = model[field]
            check(view["Scale"] == 2.0 and view["BodyPosition"] == {"X": 0, "Y": 32}, f"{path}: scale/anchor regression", errors)
            check(view["StartingPosition"] == {"X": 0, "Y": y}, f"{path}: direction source row mismatch", errors)
            check(view["ShirtSize"] == {"Width": 16, "Length": h}, f"{path}: frame size mismatch", errors)
            check(view["HideSleeves"] is render.hide_sleeves and len(view["SleeveColors"]) == 3, f"{path}: sleeve translation mismatch", errors)
            check(view["HideWhileSwimming"] is True and view["HideWhileWearingBathingSuit"] is True, f"{path}: environment hide policy mismatch", errors)
    for name in ("V5A_GAMEPLAY_FOOTPRINT.png", "V5A_DIRECTIONS_8X.png", "V5A_ARTICLE_COMPARISON.png"):
        check((OUT / name).exists(), f"missing comparison sheet {name}", errors)
    check(len(set(texture_hashes.values())) == 9, "V5A contains byte-identical garments", errors)
    check(all(recipe["promotionStatus"] == "EXPERIMENTAL" for recipe in first["recipes"]), "a garment was improperly promoted without runtime evidence", errors)
    report = {
        "status": "PASS_STATIC" if not errors else "FAIL",
        "runtimeStatus": "NOT_TESTED",
        "promotionStatus": "EXPERIMENTAL",
        "errors": errors,
        "warnings": warnings,
        "contracts": {"FashionSense": "7.5.0", "width": 16, "frameHeights": sorted({render.frame_height for render in renders}), "Scale": 2.0, "BodyPosition": [0, 32], "binaryAlpha": True, "directLogicalPixels": True, "legArticulationClaimed": False},
        "collection": collection.metrics,
        "textureHashes": texture_hashes,
        "scope": {"V3Changed": False, "V4Changed": False, "V46Deleted": False, "TFWRTouched": False, "pantsOrShoesGenerated": False, "legendaryOrMythicImplemented": False},
    }
    (OUT / "full_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": errors, "warnings": warnings}, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
