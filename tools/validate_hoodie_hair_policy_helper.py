#!/usr/bin/env python3
"""Validate the optional vanilla-hair policy selector against its audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "output" / "fashionsense" / "hoodie-vanilla-hair-audit" / "audit.json"
SOURCE = ROOT / "test-helpers" / "RNG-Clothing-Hoodie-HairPolicy"
PACK = (
    ROOT
    / "test-packs"
    / "fashionsense"
    / "RNG-Clothing-Hoodie-Weather-Test"
    / "[SMAPI] RNG Clothing Hoodie Hair Policy"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    errors: list[str] = []
    audit = load(AUDIT)
    source_map = load(SOURCE / "vanilla-hair-policy-map.json")
    packed_map = load(PACK / "vanilla-hair-policy-map.json")

    if source_map != packed_map:
        errors.append("packed policy map differs from helper source map")

    expected_supported = list(range(56)) + list(range(100, 118))
    if source_map.get("SupportedVanillaHairIds") != expected_supported:
        errors.append("vanilla hairstyle allowlist is not the audited 74-style set")

    expected_by_branch = {"Masculine": set(), "Feminine": set()}
    for case in audit.get("severeSideClipping", []):
        branch = "Masculine" if case["bodyType"] == "masculine" else "Feminine"
        expected_by_branch[branch].add(case["styleId"])
    for branch, expected in expected_by_branch.items():
        actual = set(source_map.get("PreserveFrontOnly", {}).get(branch, []))
        if actual != expected:
            errors.append(
                f"{branch}: fallback map differs from audit; expected {sorted(expected)}, got {sorted(actual)}"
            )

    source = (SOURCE / "ModEntry.cs").read_text(encoding="utf-8")
    required_contracts = (
        "who.IsLocalPlayer",
        "FashionSense.CustomHair.Id",
        "FashionSense.CustomBody.Id",
        "Game1.IsRainingHere",
        "Game1.IsSnowingHere",
        "Harbor Haze Weather Hoodie",
        "Harbor Haze Weather Hood - Auto HideBackOnly",
        "Harbor Haze Weather Hood - Auto PreserveFrontOnly",
    )
    for contract in required_contracts:
        if contract not in source:
            errors.append(f"helper source is missing required scope/safety contract: {contract}")
    for forbidden in ("Harmony", "RegisterAppearanceDrawOverride", "FarmerRendererPatch"):
        if forbidden in source:
            errors.append(f"helper contains forbidden renderer/patch mechanism: {forbidden}")

    manifest = load(PACK / "manifest.json")
    if manifest.get("UniqueID") != "RNGClothing.HoodieHairPolicyHelper":
        errors.append("helper manifest has wrong UniqueID")
    dependencies = {entry["UniqueID"]: entry for entry in manifest.get("Dependencies", [])}
    required_dependencies = {
        "PeacefulEnd.FashionSense": "7.5.0",
        "RNGClothing.FashionSense.HoodieWeatherTest": "1.6.0",
        "RNGClothing.ContentPatcher.HoodieWeatherTest": "1.4.0",
    }
    for unique_id, minimum in required_dependencies.items():
        dependency = dependencies.get(unique_id)
        if not dependency or dependency.get("MinimumVersion") != minimum or dependency.get("IsRequired") is not True:
            errors.append(f"missing exact required dependency {unique_id} >= {minimum}")

    dll = PACK / manifest.get("EntryDll", "")
    if not dll.is_file() or dll.stat().st_size == 0:
        errors.append("built helper DLL is missing or empty")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "supportedVanillaHairstyles": len(expected_supported),
        "preserveFrontOnlyMasculine": sorted(expected_by_branch["Masculine"]),
        "preserveFrontOnlyFeminine": sorted(expected_by_branch["Feminine"]),
        "dllSha256": hashlib.sha256(dll.read_bytes()).hexdigest() if dll.is_file() else None,
        "scope": "local Farmer + exact Harbor Haze Shirt/Hat + hood-up precipitation state",
        "unsupportedPolicy": "fail open to base Hat / configured Content Patcher policy",
        "runtimePromotion": "EXPERIMENTAL_PENDING_USER_TEST",
    }
    output = ROOT / "output" / "fashionsense" / "hoodie-weather-test" / "hair-policy-helper-validation.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
