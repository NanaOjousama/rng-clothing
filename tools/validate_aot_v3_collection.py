#!/usr/bin/env python3
"""Validate the six-garment AoTInspired V3 collection and isolated FS pack."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import encode_rgba_png, read_rgba_png
from generator.renderers.fashionsense import diagnose_fs_v3, render_fs_v3
from generator.v3.style_profiles import (
    generate_aot_v3_collection, validate_aot_v3_collection, validate_aot_v3_renders,
)


OUTPUT = ROOT / "output" / "fashionsense" / "v3-style-aot"
RECIPES = ROOT / "output" / "recipes" / "aot_v3_collection.json"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V3-AoT-Collection"


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    errors: list[str] = []; warnings: list[str] = []
    collection = generate_aot_v3_collection(); recipes = collection["recipes"]
    saved = json.loads(RECIPES.read_text(encoding="utf-8"))
    if saved != collection:
        errors.append("saved collection is not the current deterministic profile output")
    semantic = validate_aot_v3_collection(collection)
    errors.extend(semantic.errors); warnings.extend(semantic.warnings)
    renders = [render_fs_v3(recipe) for recipe in recipes]
    diagnostics = [diagnose_fs_v3(render) for render in renders]
    rendered = validate_aot_v3_renders(collection, renders, diagnostics)
    errors.extend(rendered.errors); warnings.extend(rendered.warnings)

    expected_artifacts = {
        "-default-8x.png", "-directions-8x.png", "-gameplay-size.png", "-surface-flat-8x.png",
        "-design-concept.json", "-recipe.json", "-surface-summary.json",
    }
    for recipe, render, diagnostic in zip(recipes, renders, diagnostics):
        slug = _slug(recipe["itemName"]); native = OUTPUT / f"{slug}.png"
        if not native.exists():
            errors.append(f"{recipe['id']}: missing native texture"); continue
        info = read_rgba_png(native)
        if (info["width"], info["height"]) != (16, 64):
            errors.append(f"{recipe['id']}: native texture must be 16x64")
        if any(filter_type != 0 for filter_type in info["filters"]):
            errors.append(f"{recipe['id']}: PNG scanlines are not explicit filter 0")
        if {pixel[3] for row in info["pixels"] for pixel in row} - {0, 255}:
            errors.append(f"{recipe['id']}: semitransparent logical pixels found")
        if native.read_bytes() != encode_rgba_png(render.texture):
            errors.append(f"{recipe['id']}: output differs from deterministic direct logical render")
        if any(diagnostic.metrics["bodyCoverageMissing"].values()):
            errors.append(f"{recipe['id']}: body coverage regression")
        for suffix in expected_artifacts:
            if not (OUTPUT / f"{slug}{suffix}").exists():
                errors.append(f"{recipe['id']}: missing {slug}{suffix}")

        shirt_dir = PACK / "Shirts" / _folder(recipe["itemName"])
        if not (shirt_dir / "shirt.png").exists() or _sha(shirt_dir / "shirt.png") != _sha(native):
            errors.append(f"{recipe['id']}: pack texture mismatch")
        metadata = json.loads((shirt_dir / "shirt.json").read_text(encoding="utf-8"))
        for direction, field, y in (("front", "FrontShirt", 0), ("right", "RightShirt", 16), ("left", "LeftShirt", 32), ("back", "BackShirt", 48)):
            model = metadata[field]
            if model.get("Scale") != 2.0 or model.get("BodyPosition") != {"X": 0, "Y": 32}:
                errors.append(f"{recipe['id']} {direction}: Scale/BodyPosition regression")
            if model.get("StartingPosition") != {"X": 0, "Y": y} or model.get("ShirtSize") != {"Width": 16, "Length": 16}:
                errors.append(f"{recipe['id']} {direction}: frame mapping regression")
            if model.get("HideSleeves") or len(model.get("SleeveColors", [])) != 3:
                errors.append(f"{recipe['id']} {direction}: native animated sleeve integration missing")

    shirts = sorted((PACK / "Shirts").glob("*/shirt.json"))
    if len(shirts) != 6:
        errors.append(f"test pack contains {len(shirts)} shirts, expected exactly 6")
    manifest = json.loads((PACK / "manifest.json").read_text(encoding="utf-8"))
    target = manifest.get("ContentPackFor", {})
    if target.get("UniqueID") != "PeacefulEnd.FashionSense" or target.get("MinimumVersion") != "7.5.0":
        errors.append("Fashion Sense 7.5.0 content-pack dependency is incorrect")
    localization = json.loads((PACK / "i18n" / "default.json").read_text(encoding="utf-8"))
    if len(localization) != 12:
        errors.append("localization staging must contain six names and six descriptions")

    for comparison in (
        ROOT / "output" / "comparisons" / "AOT_V3_COLLECTION_FRONTS_8X.png",
        ROOT / "output" / "comparisons" / "AOT_V3_COLLECTION_DIRECTIONS.png",
        ROOT / "output" / "comparisons" / "AOT_V3_RARITY_ART_BEFORE_AFTER.png",
        ROOT / "output" / "comparisons" / "AOT_V3_RARITY_VS_V3_BENCHMARK.png",
    ):
        if not comparison.exists(): errors.append(f"missing comparison {comparison.name}")

    # References inform the curated profile/report only. Runtime generation and
    # the frozen renderer must never inspect the corpus or benchmark assets.
    for relative in (
        "generator/v3/style_profiles/aot_inspired.py",
        "generator/renderers/fashionsense/surface_v3.py",
        "tools/generate_aot_v3_collection.py",
        "tools/make_aot_v3_rarity_correction_comparison.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8").lower()
        if "references/style-profiles/aotinspired" in source or "shirts.zip" in source:
            errors.append(f"{relative}: generation path reads visual reference assets")

    result = {
        "status": "PASS_AOT_V3_COLLECTION_FULL_VALIDATION" if not errors else "FAIL",
        "errors": errors, "warnings": warnings,
        "checks": {
            "exactVisibleConceptCount": len(recipes), "hiddenCandidateCount": collection["hiddenCandidateCount"],
            "rarityDistribution": collection["rarityCounts"], "deterministicRecipeOutput": saved == collection,
            "directLogicalPixelOutput": True, "binaryAlpha": not any("semitransparent" in error for error in errors),
            "runtimeContract": {"FashionSense": "7.5.0", "frame": [16, 16], "Scale": 2.0, "BodyPosition": [0, 32]},
            "bodyCoverage": all(not any(item.metrics["bodyCoverageMissing"].values()) for item in diagnostics),
            "designInterestWithoutShading": {recipe["id"]: diagnostic.metrics["designInterestWithoutShading"] for recipe, diagnostic in zip(recipes, diagnostics)},
            "semanticDiversity": semantic.metrics, "renderDiversity": rendered.metrics,
        },
    }
    path = OUTPUT / "full_validation.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "errors": errors, "warnings": warnings,
        "rarityDistribution": collection["rarityCounts"],
        "maximumSemanticSimilarity": semantic.metrics["maximumSemanticSimilarity"],
        "maximumSurfaceMaskJaccard": rendered.metrics["maximumSurfaceMaskJaccard"],
        "maximumSideMaskJaccard": rendered.metrics["maximumSideMaskJaccard"],
        "rareSideTemplates": rendered.metrics["rareSideTemplates"],
    }, indent=2))
    print(f"Wrote {path}")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
