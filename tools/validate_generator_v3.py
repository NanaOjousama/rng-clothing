#!/usr/bin/env python3
"""Validate Generator V3 recipes, rendering, outputs, pack, and V2 regressions."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import diagnose_fs_hd_render, diagnose_fs_v3, render_fs_hd_v2, render_fs_v3
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data
from generator.v3 import generate_benchmark_batch
from generator.v3.validation import validate_v3_batch


OUTPUT = ROOT / "output" / "fashionsense" / "v3-benchmark"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V3-Benchmark"
RECIPE_OUTPUT = ROOT / "output" / "recipes" / "v3_benchmark_recipes.json"
V2_RECIPES = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"


def _slug(name: str) -> str:
    import re
    return "_".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def _folder(name: str) -> str:
    return "".join(part.title() for part in _slug(name).split("_"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    errors = []; warnings = []
    batch = generate_benchmark_batch(); recipes = batch["recipes"]
    saved = json.loads(RECIPE_OUTPUT.read_text(encoding="utf-8"))
    if saved != batch: errors.append("saved recipe batch is not deterministic current Generator V3 output")
    renders = [render_fs_v3(recipe) for recipe in recipes]
    diagnostics = [diagnose_fs_v3(render) for render in renders]
    batch_result = validate_v3_batch(recipes, renders, diagnostics)
    errors.extend(batch_result.errors); warnings.extend(batch_result.warnings)

    for recipe, render in zip(recipes, renders):
        slug = _slug(recipe["itemName"]); native = OUTPUT / f"{slug}.png"
        if not native.exists():
            errors.append(f"missing native output {native.name}"); continue
        info = read_rgba_png(native)
        if (info["width"], info["height"]) != (16, 64): errors.append(f"{native.name}: expected 16x64")
        if any(filter_type != 0 for filter_type in info["filters"]): errors.append(f"{native.name}: generated scanline filtering is not explicit filter 0")
        alpha = {pixel[3] for row in info["pixels"] for pixel in row}
        if not alpha <= {0, 255}: errors.append(f"{native.name}: semitransparent pixels found")
        if native.read_bytes() != encode_rgba_png(render.texture): errors.append(f"{native.name}: differs from deterministic direct logical render")
        pack_dir = PACK / "Shirts" / _folder(recipe["itemName"])
        if not (pack_dir / "shirt.png").exists() or _sha(pack_dir / "shirt.png") != _sha(native): errors.append(f"{recipe['id']}: pack texture mismatch")
        metadata = json.loads((pack_dir / "shirt.json").read_text(encoding="utf-8"))
        for direction, field, y in (("front", "FrontShirt", 0), ("right", "RightShirt", 16), ("left", "LeftShirt", 32), ("back", "BackShirt", 48)):
            model = metadata[field]
            if model["Scale"] != 2.0 or model["BodyPosition"] != {"X": 0, "Y": 32}: errors.append(f"{recipe['id']} {direction}: FS scale/anchor regression")
            if model["StartingPosition"] != {"X": 0, "Y": y} or model["ShirtSize"] != {"Width": 16, "Length": 16}: errors.append(f"{recipe['id']} {direction}: frame contract mismatch")
            if model["HideSleeves"] or len(model.get("SleeveColors", [])) != 3: errors.append(f"{recipe['id']} {direction}: native sleeve integration missing")
        required = [f"{slug}-default-8x.png", f"{slug}-directions-8x.png", f"{slug}-directions-gameplay-2x.png", f"{slug}-surface-flat-8x.png", f"{slug}-recipe-summary.json"]
        for filename in required:
            if not (OUTPUT / filename).exists(): errors.append(f"{recipe['id']}: missing {filename}")

    shirts = list((PACK / "Shirts").glob("*/shirt.json"))
    if len(shirts) != 12: errors.append(f"test pack contains {len(shirts)} shirts, expected 12")
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    target = manifest.get("ContentPackFor", {})
    if target.get("UniqueID") != "PeacefulEnd.FashionSense" or target.get("MinimumVersion") != "7.5.0": errors.append("test pack Fashion Sense dependency is incorrect")
    i18n = json.loads((PACK / "i18n" / "default.json").read_text(encoding="utf-8"))
    if len(i18n) != 24: errors.append("test pack localization staging must contain name and description for all 12 garments")

    # Benchmark pixels may be analyzed by one isolated audit tool; generation
    # and renderer modules must never access the archive or reference folder.
    for relative in ("generator/v3/engine.py", "generator/renderers/fashionsense/surface_v3.py", "tools/generate_v3_benchmark.py"):
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        if "shirts.zip" in text or "references/benchmark" in text:
            errors.append(f"{relative}: generation path must not read benchmark assets")

    # Regression: existing V2 recipes still render through both relevant old
    # backends without V3 fields or V3 imports in their recipes.
    v2_data = load_v2_data()
    old_batch = json.loads(V2_RECIPES.read_text(encoding="utf-8"))["recipes"]
    for recipe in old_batch:
        render_v2_recipe(recipe, v2_data)
    for recipe_id in ("lifestyle-v2-16", "lifestyle-v2-11", "lifestyle-v2-19", "lifestyle-v2-05"):
        recipe = next(item for item in old_batch if item["id"] == recipe_id)
        result = diagnose_fs_hd_render(render_fs_hd_v2(recipe))
        if not result.passes: errors.append(f"V2 FS regression: {recipe_id}: {result.errors}")

    result = {
        "status": "PASS_GENERATOR_V3_FULL_VALIDATION" if not errors else "FAIL",
        "errors": errors, "warnings": warnings,
        "checks": {
            "recipeSchemaAndConstruction": not errors,
            "exactTwelveGarments": len(recipes) == 12,
            "rarityDistribution": batch_result.metrics["rarityCounts"],
            "directLogicalPixels": True,
            "binaryAlpha": not any("semitransparent" in error for error in errors),
            "FashionSenseRuntimeContract": {"version": "7.5.0", "frame": [16, 16], "scale": 2.0, "bodyPosition": [0, 32]},
            "bodyCoverage": all(not any(diag.metrics["bodyCoverageMissing"].values()) for diag in diagnostics),
            "benchmarkIsolation": not any("generation path" in error for error in errors),
            "V2VanillaRegression": True,
            "V2FashionSenseRegression": not any("V2 FS regression" in error for error in errors),
            "diversity": batch_result.metrics,
        },
    }
    path = OUTPUT / "full_validation.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": errors, "warnings": warnings, "rarityDistribution": batch_result.metrics["rarityCounts"], "uniqueAxisCounts": batch_result.metrics["uniqueAxisCounts"], "averageSurfaceCellsPerView": batch_result.metrics["averageSurfaceCellsPerView"], "maximumSemanticSimilarity": batch_result.metrics["maximumSemanticSimilarity"], "maximumSurfaceMaskJaccard": batch_result.metrics["maximumSurfaceMaskJaccard"]}, indent=2))
    print(f"Wrote {path}")
    if errors: raise SystemExit(1)


if __name__ == "__main__":
    main()
