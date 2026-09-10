#!/usr/bin/env python3
"""Independent validation of Hybrid V3 Phase 1 artifacts and isolation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hybrid_v3.config import is_enabled
from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.data import V3DataRepository
from generator.hybrid_v3.data_validation import validate_repository
from generator.hybrid_v3.seeding import derive_seed

OUT = ROOT / "output/hybrid-v3-phase1"


def main() -> int:
    errors: list[str] = []
    repo_result = validate_repository(V3DataRepository())
    if repo_result["status"] != "PASS":
        errors.extend(repo_result["errors"])
    summary_path = OUT / "phase1-summary.json"
    if not summary_path.exists():
        errors.append("phase1-summary.json missing")
    else:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary["status"] != "PASS": errors.append("generation summary failed")
        if summary["validCaseCount"] != 18: errors.append("expected 18 valid cases")
        if summary["invalidCaseCount"] != 9: errors.append("expected 9 invalid cases")
        if summary["rendererInvoked"]: errors.append("renderer was invoked")
        if summary["rendererModulesImported"]: errors.append("renderer modules imported")
    if is_enabled(): errors.append("production feature flag must remain false")

    recipes = sorted((OUT / "valid").glob("*/generated-recipe.json"))
    flats = sorted((OUT / "valid").glob("*/semantic-flat.png"))
    if len(recipes) != 18 or len(flats) != 6:
        errors.append(f"artifact counts recipes={len(recipes)} flats={len(flats)}")
    for path in recipes:
        recipe = json.loads(path.read_text(encoding="utf-8"))
        if recipe["mode"] != "RECIPE_ONLY_NO_RENDERER": errors.append(f"{path}: wrong mode")
        if set(recipe["projections"]) != {"front", "right", "back", "left"}: errors.append(f"{path}: incomplete directions")
        if recipe["provenance"]["rendererInvoked"]: errors.append(f"{path}: renderer invoked")
        serialized = json.dumps(recipe["canonicalModel"], sort_keys=True).lower()
        if any(token in serialized for token in ('"x":', '"y":', 'sourcerectangle', 'pixelcoordinates')):
            errors.append(f"{path}: renderer coordinate leaked into canonical model")

    if derive_seed(123, "family", "POLO_SHIRT") != derive_seed(123, "family", "POLO_SHIRT"):
        errors.append("seed derivation unstable")
    if derive_seed(123, "palette") == derive_seed(123, "family", "POLO_SHIRT"):
        errors.append("stage seed namespace collision")
    builder = CanonicalGarmentBuilder()
    first = builder.build(family="POLO_SHIRT", design_intent="POLO_CLASSIC", fit_profile="UNISEX_REGULAR", root_seed=777)
    second = builder.build(family="POLO_SHIRT", design_intent="POLO_CLASSIC", fit_profile="UNISEX_REGULAR", root_seed=777)
    if first != second:
        errors.append("same seed and data did not reproduce canonical model")
    architecture_seeds_before = dict(first["provenance"]["stageSeeds"])
    derive_seed(777, "palette", "FUTURE_TEST")
    if first["provenance"]["stageSeeds"] != architecture_seeds_before:
        errors.append("future palette seed perturbed architecture provenance")

    result = {"status": "PASS" if not errors else "FAIL", "errors": errors, "validRecipes": len(recipes), "semanticFlats": len(flats), "featureFlagEnabled": is_enabled()}
    (OUT / "independent-validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
