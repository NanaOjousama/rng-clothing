#!/usr/bin/env python3
"""Generate recipe-only Hybrid V3 Phase 1 fixtures and debug flats."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.config import is_enabled
from generator.hybrid_v3.data import V3DataRepository
from generator.hybrid_v3.data_validation import validate_repository
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.semantic_flat import emit_semantic_flat
from generator.hybrid_v3.validator import PhysicalValidator

OUT = ROOT / "output/hybrid-v3-phase1"
FIXTURES = ROOT / "tests/fixtures/hybrid_v3_invalid_cases.json"
FAMILY_CASES = {
    "T_SHIRT": ("TEE_CLEAN_ESSENTIAL", "TEE_RELAXED_WEEKEND"),
    "POLO_SHIRT": ("POLO_CLASSIC", "POLO_COASTAL_SPORT"),
    "SWEATER_VEST": ("VEST_ACADEMIC", "VEST_RELAXED_KNIT"),
    "CARDIGAN": ("CARDIGAN_ACADEMIC", "CARDIGAN_RELAXED_WEEKEND"),
    "BLAZER": ("BLAZER_CLEAN_TAILORED", "BLAZER_SOFT_SMART_CASUAL"),
    "SAILOR_TOP": ("SAILOR_DECK_CLASSIC", "SAILOR_SOFT_MARITIME"),
}
FIT_CASES = ("MASC_RELAXED", "FEM_FITTED", "UNISEX_BOXY")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _component_from_definition(repo: V3DataRepository, definition_id: str, instance_id: str, parent: str) -> dict[str, Any]:
    definition = repo.components[definition_id]
    parameters = {key: values[0] for key, values in definition.get("parameterRanges", {}).items()}
    continuity = definition["continuityBehavior"]
    return {
        "instanceId": instance_id,
        "definitionId": definition_id,
        "componentType": definition["componentType"],
        "parent": parent,
        "attachmentRegion": definition["parentAttachmentRegion"],
        "parameters": parameters,
        "directionalVisibilityPolicy": dict(definition["directionalVisibility"]),
        "continuityBehavior": continuity,
        "continuityGroup": f"invalid:{instance_id}" if "WRAP" in continuity else None,
        "pixelPriority": definition["pixelPriority"],
        "silhouetteImpact": definition["silhouetteImpact"],
        "mandatory": False,
    }


def mutate_invalid(model: dict[str, Any], mutation: str, repo: V3DataRepository) -> None:
    by_id = {item["instanceId"]: item for item in model["components"]}
    if mutation == "polo_full_rear_placket":
        by_id["placket"]["parameters"]["length"] = "full"
        by_id["placket"]["directionalVisibilityPolicy"]["back"] = "FULL"
        model["rearStructure"]["rearOpening"] = True
    elif mutation == "vest_add_sleeve":
        model["components"].append(_component_from_definition(repo, "SLEEVE_NATIVE_SHORT", "invalid_sleeve", "body"))
    elif mutation == "cardigan_add_lapel":
        model["components"].append(_component_from_definition(repo, "LAPEL_NOTCHED_TAILORED", "invalid_lapel", "opening"))
    elif mutation == "remove_lapel":
        model["components"] = [item for item in model["components"] if item["componentType"] != "LAPEL"]
    elif mutation == "remove_rear_panel":
        model["components"] = [item for item in model["components"] if item["componentType"] != "REAR_PANEL"]
    elif mutation == "unattach_collar":
        by_id["collar"]["parent"] = "missing_parent"
    elif mutation == "remove_hem_continuity":
        by_id["hem"]["continuityGroup"] = None
    elif mutation == "add_sailor_rear_panel":
        model["components"].append(_component_from_definition(repo, "REAR_PANEL_SAILOR_SQUARE", "invalid_rear", "body"))
    elif mutation == "create_parent_cycle":
        by_id["body"]["parent"] = "collar"
        by_id["collar"]["parent"] = "body"
    else:
        raise KeyError(mutation)


def main() -> int:
    repo = V3DataRepository()
    data_validation = validate_repository(repo)
    if data_validation["status"] != "PASS":
        raise SystemExit(f"V3 data validation failed: {data_validation['errors']}")
    builder = CanonicalGarmentBuilder(repo)
    projector = DirectionalProjector(repo)
    validator = PhysicalValidator(repo)
    valid_results = []

    for family_index, (family, intents) in enumerate(FAMILY_CASES.items()):
        for fit_index, fit in enumerate(FIT_CASES):
            intent = intents[fit_index % len(intents)]
            root_seed = 310000 + family_index * 1000 + fit_index * 37
            model = builder.build(family=family, design_intent=intent, fit_profile=fit, root_seed=root_seed)
            canonical_validation = validator.validate(model)
            projections = projector.project(model)
            projection_validation = validator.validate_projections(model, projections)
            if canonical_validation["status"] != "PASS" or projection_validation["status"] != "PASS":
                raise SystemExit(f"valid fixture failed: {family}/{fit}: {canonical_validation} {projection_validation}")
            case_id = f"{family.lower()}--{intent.lower()}--{fit.lower()}"
            folder = OUT / "valid" / case_id
            flat_path = folder / "semantic-flat.png"
            emit_flat = fit_index == 0
            if emit_flat:
                emit_semantic_flat(model, projections, flat_path)
            elif flat_path.exists():
                flat_path.unlink()
            validation = {"status": "PASS", "canonical": canonical_validation, "projection": projection_validation}
            recipe = {
                "schemaVersion": "3.0.0",
                "mode": "RECIPE_ONLY_NO_RENDERER",
                "canonicalModel": model,
                "projections": projections,
                "validation": validation,
                "provenance": {"rendererInvoked": False, "featureFlagEnabled": is_enabled()},
                "semanticFlat": str(flat_path.relative_to(ROOT)) if emit_flat else None,
            }
            write_json(folder / "canonical-model.json", model)
            write_json(folder / "projections.json", projections)
            write_json(folder / "validation.json", validation)
            write_json(folder / "generated-recipe.json", recipe)
            valid_results.append({"id": case_id, "family": family, "intent": intent, "fit": fit, "seed": root_seed, "status": "PASS", "material": model["material"]["id"], "componentCount": len(model["components"])})

    fixture_data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    invalid_results = []
    for index, case in enumerate(fixture_data["cases"]):
        base = case["base"]
        model = builder.build(family=base["family"], design_intent=base["intent"], fit_profile=base["fit"], root_seed=410000 + index)
        mutate_invalid(model, case["mutation"], repo)
        validation = validator.validate(model)
        actual_codes = {issue["code"] for issue in validation["issues"]}
        missing = sorted(set(case["expectedCodes"]) - actual_codes)
        passed = validation["status"] == "FAIL" and not missing
        folder = OUT / "invalid" / case["id"].lower()
        write_json(folder / "invalid-canonical-model.json", model)
        write_json(folder / "validation.json", {**validation, "expectedCodes": case["expectedCodes"], "missingExpectedCodes": missing, "fixtureStatus": "PASS" if passed else "FAIL"})
        invalid_results.append({"id": case["id"], "status": "PASS" if passed else "FAIL", "actualCodes": sorted(actual_codes), "missingExpectedCodes": missing})

    renderer_modules = sorted(name for name in sys.modules if name.startswith("generator.renderers"))
    summary = {
        "status": "PASS" if all(item["status"] == "PASS" for item in [*valid_results, *invalid_results]) and not renderer_modules and not is_enabled() else "FAIL",
        "mode": "PHASE1_RECIPE_ONLY",
        "featureFlagEnabled": is_enabled(),
        "rendererModulesImported": renderer_modules,
        "rendererInvoked": False,
        "dataValidation": data_validation,
        "validCaseCount": len(valid_results),
        "invalidCaseCount": len(invalid_results),
        "validCases": valid_results,
        "invalidCases": invalid_results,
    }
    write_json(OUT / "phase1-summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("status", "validCaseCount", "invalidCaseCount", "featureFlagEnabled", "rendererModulesImported")}, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
