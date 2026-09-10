#!/usr/bin/env python3
"""Validate Generator V4 recipes, article renders, outputs, and FS packs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import render_fs_v4
from generator.v4 import diagnose_v4_article, diagnose_v4_collection, generate_v4_aot_collection, generate_v4_neutral_collection, validate_v4_recipe


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    errors: list[str] = []; warnings: list[str] = []
    specifications = (
        ("aot", generate_v4_aot_collection, {"Common": 2, "Uncommon": 2, "Rare": 2}, "RNG-Clothing-V4-AoT"),
        ("neutral", generate_v4_neutral_collection, {"Common": 2, "Uncommon": 3, "Rare": 3}, "RNG-Clothing-V4-Neutral-Benchmark"),
    )
    collection_results = {}
    all_hashes = {}
    for label, factory, rarity_counts, pack_name in specifications:
        first = factory(); second = factory()
        check(first == second, f"{label}: recipe generation is not deterministic", errors)
        recipe_path = ROOT / "output" / "recipes" / f"v4_{label}_collection.json"
        check(recipe_path.exists(), f"{label}: missing saved recipe batch", errors)
        if recipe_path.exists():
            check(json.loads(recipe_path.read_text(encoding="utf-8")) == first, f"{label}: saved recipes differ from engine", errors)
        renders = []; diagnostics = []
        for recipe in first["recipes"]:
            validated = validate_v4_recipe(recipe)
            errors.extend(f"{recipe['id']}: {value}" for value in validated.errors)
            check(recipe["articleType"] != "LONG_OUTERWEAR", f"{recipe['id']}: unproven long outerwear rendered", errors)
            render_a = render_fs_v4(recipe); render_b = render_fs_v4(recipe)
            check(encode_rgba_png(render_a.texture) == encode_rgba_png(render_b.texture), f"{recipe['id']}: render is not deterministic", errors)
            render = render_a; diagnostic = diagnose_v4_article(render)
            renders.append(render); diagnostics.append(diagnostic)
            errors.extend(f"{recipe['id']}: {value}" for value in diagnostic.errors)
            if diagnostic.warnings: warnings.extend(f"{recipe['id']}: {value}" for value in diagnostic.warnings)
            slug = "_".join(__import__("re").sub(r"[^a-z0-9]+", " ", recipe["designRecipe"]["itemName"].lower()).split())
            png_path = ROOT / "output" / "fashionsense" / "v4" / label / f"{slug}.png"
            check(png_path.exists(), f"{recipe['id']}: missing native texture", errors)
            if png_path.exists():
                png = read_rgba_png(png_path)
                check((png["width"], png["height"]) == (16, 64), f"{recipe['id']}: native texture must be 16x64", errors)
                check(set(png["filters"]) == {0}, f"{recipe['id']}: PNG uses nonzero filtering", errors)
                alpha = {pixel[3] for row in png["pixels"] for pixel in row}
                check(alpha <= {0, 255}, f"{recipe['id']}: texture has semitransparent pixels", errors)
                check(png["sha256"] == hashlib.sha256(encode_rgba_png(render.texture)).hexdigest(), f"{recipe['id']}: saved pixels differ from renderer", errors)
                all_hashes[recipe["id"]] = png["sha256"]
        result = diagnose_v4_collection(first["recipes"], renders, diagnostics, expected_counts=rarity_counts)
        errors.extend(f"{label}: {value}" for value in result.errors)
        warnings.extend(f"{label}: {value}" for value in result.warnings)
        pack = ROOT / "test-packs" / "fashionsense" / pack_name
        manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
        check(manifest["ContentPackFor"] == {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}, f"{label}: FS dependency contract changed", errors)
        shirts = sorted((pack / "Shirts").glob("*/shirt.json"))
        check(len(shirts) == len(first["recipes"]), f"{label}: test pack must contain exactly {len(first['recipes'])} shirts", errors)
        for path in shirts:
            model = json.loads(path.read_text(encoding="utf-8"))
            for field, y in (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48)):
                view = model[field]
                check(view["Scale"] == 2.0 and view["BodyPosition"] == {"X": 0, "Y": 32}, f"{path}: anchor/scale regression", errors)
                check(view["StartingPosition"] == {"X": 0, "Y": y} and view["ShirtSize"] == {"Width": 16, "Length": 16}, f"{path}: direction/frame mapping regression", errors)
                check(view["HideSleeves"] is False and len(view["SleeveColors"]) == 3, f"{path}: native sleeve integration regression", errors)
        collection_results[label] = {"passes": result.passes, "errors": list(result.errors), "warnings": list(result.warnings), "metrics": result.metrics}
    check(len(set(all_hashes.values())) == len(all_hashes), "two V4 garments produced byte-identical native textures", errors)
    required_sheets = ("V4_AOT_ARTICLE_COMPARISON.png", "V4_NEUTRAL_ARTICLE_COMPARISON.png", "V4_GAMEPLAY_SIZE_COMPARISON.png", "V4_ARTICLE_FRONTS_8X.png", "V4_RARITY_COMPARISON.png")
    for name in required_sheets:
        check((ROOT / "output" / "fashionsense" / "v4" / name).exists(), f"missing comparison {name}", errors)
    report = {"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings,
        "contracts": {"FashionSense": "7.5.0", "logicalFrame": [16, 16], "Scale": 2.0, "BodyPosition": [0, 32], "binaryAlpha": True, "integerLogicalPixels": True, "longOuterwearRendered": False},
        "collections": collection_results, "textureHashes": all_hashes,
        "scope": {"TFWRTouched": False, "vanillaRendererChanged": False, "rewardSystemImplemented": False}}
    path = ROOT / "output" / "fashionsense" / "v4" / "full_validation.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "errors": errors, "warnings": warnings}, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
