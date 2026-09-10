"""Dependency-free validation of the versioned Phase 1 data namespace."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data import ROOT, V3DataRepository

REQUIRED_COMPONENT_TYPES = {
    "BODY", "COLLAR", "LAPEL", "SLEEVE", "ARMHOLE", "OPENING", "PLACKET",
    "POCKET", "HEM", "WAISTBAND", "REAR_PANEL", "RIBBING", "INNER_LAYER",
}
REQUIRED_COMPONENT_FIELDS = {
    "id", "componentType", "parentAttachmentRegion", "compatibleFamilies",
    "compatibleMaterials", "parameterRanges", "directionalVisibility",
    "continuityBehavior", "pixelPriority", "silhouetteImpact", "hardCompatibilityRules",
}


def validate_repository(repository: V3DataRepository | None = None) -> dict[str, Any]:
    repo = repository or V3DataRepository()
    errors: list[str] = []
    manifest = repo.documents["manifest"]
    families = set(manifest["families"])
    if set(repo.architectures) != families:
        errors.append("manifest/architecture family mismatch")
    if manifest.get("featureFlagDefault") is not False:
        errors.append("feature flag must default false")
    if manifest.get("rendererIntegration") is not False:
        errors.append("Phase 1 renderer integration must be false")

    types = {component.get("componentType") for component in repo.components.values()}
    missing_types = REQUIRED_COMPONENT_TYPES - types
    if missing_types:
        errors.append(f"missing component types: {sorted(missing_types)}")
    forbidden_keys = {"x", "y", "coordinates", "pixels", "sprite", "sourceRectangle"}
    for component in repo.components.values():
        missing = REQUIRED_COMPONENT_FIELDS - set(component)
        if missing:
            errors.append(f"{component.get('id')}: missing fields {sorted(missing)}")
        if forbidden_keys & set(component):
            errors.append(f"{component['id']}: renderer coordinates forbidden")
        if set(component["directionalVisibility"]) != {"front", "right", "back", "left"}:
            errors.append(f"{component['id']}: incomplete direction policy")
        if not set(component["compatibleFamilies"]).issubset(families):
            errors.append(f"{component['id']}: unknown compatible family")

    material_doc = json.loads((ROOT / "specs/palettes/material_color_behavior.json").read_text(encoding="utf-8"))
    approved_materials = {item["id"] for item in material_doc["behaviors"]}
    for family, policy in repo.material_families.items():
        if not set(policy["allowed"]).issubset(approved_materials):
            errors.append(f"{family}: material not in approved behavior library")
        if policy["default"] not in policy["allowed"]:
            errors.append(f"{family}: default material not allowed")
    if repo.material_families["POLO_SHIRT"]["default"] == "WOVEN_SHIRT":
        errors.append("POLO_SHIRT still defaults to WOVEN_SHIRT")

    for family in families:
        try:
            resolved = repo.resolve_architecture(family)
        except Exception as exc:
            errors.append(f"{family}: architecture resolution failed: {exc}")
            continue
        slots = {item["slot"] for item in resolved["componentSlots"]}
        if not set(resolved["mandatoryIdentitySlots"]).issubset(slots):
            errors.append(f"{family}: mandatory slot missing after inheritance")
    for intent in repo.intents.values():
        if "palette" in json.dumps(intent).lower():
            errors.append(f"{intent['id']}: intent must not assign palette")
        if not intent.get("dominant") or not intent.get("supporting"):
            errors.append(f"{intent['id']}: incomplete design hierarchy")
    if len(repo.fit_profiles) != 7:
        errors.append("expected seven fit profiles")

    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "digests": repo.digests}
