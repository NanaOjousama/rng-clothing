#!/usr/bin/env python3
"""Validate the complete vanilla-hair hoodie audit and its honest status."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png


AUDIT = ROOT / "output/fashionsense/hoodie-vanilla-hair-audit/audit.json"
ARCH = ROOT / "generator/data/hoodie_layers/architecture.json"
EXPECTED_SEVERE = [17, 24, 26, 28, 29, 33, 34, 100, 101, 102, 103, 104, 115]


def main() -> None:
    errors: list[str] = []
    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    architecture = json.loads(ARCH.read_text(encoding="utf-8"))
    if data.get("selectableStyleCount") != 74:
        errors.append("audit does not cover all 74 selectable vanilla hairstyles")
    if data.get("compositeCount") != 592:
        errors.append("audit does not cover 74 styles x 2 bodies x 4 directions")
    if data.get("severeStyleIds") != EXPECTED_SEVERE:
        errors.append("severe side-hair compatibility list drifted")
    if data.get("singleDefaultPolicyPassesAllVanillaStyles") is not False:
        errors.append("audit falsely claims one default policy passes every vanilla style")
    if data.get("runtimePromotion") != "NOT_ELIGIBLE_STATIC_AUDIT_ONLY":
        errors.append("static audit was incorrectly promoted as runtime evidence")
    for result in data.get("rankedStressResults", []):
        back = result.get("directionalMetrics", {}).get("back", {})
        if back.get("visibleHairPixels") != 0:
            errors.append(f"hair {result.get('styleId')}: HideBackOnly did not hide back Hair")
            break
    v1 = architecture["rarePlusTemplate"].get("vanillaHairV1Compatibility", {})
    if v1.get("fallbackStyleIds") != EXPECTED_SEVERE:
        errors.append("architecture fallback list differs from audit")
    if architecture["rarePlusTemplate"].get("promotionStatus") != "EXPERIMENTAL":
        errors.append("hoodie template was frozen without live runtime evidence")
    required_pngs = [
        ROOT / "output/comparisons/HOODIE_VANILLA_HAIR_STRESS_SET.png",
        ROOT / "output/comparisons/HOODIE_VANILLA_HAIR_POLICY_FALLBACKS.png",
    ]
    required_pngs += [
        ROOT
        / "output/fashionsense/hoodie-vanilla-hair-audit"
        / f"ALL_VANILLA_HAIR_{body}_{direction}.png"
        for body in ("MASCULINE", "FEMININE")
        for direction in ("FRONT", "RIGHT", "BACK", "LEFT")
    ]
    for path in required_pngs:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        info = read_rgba_png(path)
        if info["width"] <= 0 or info["height"] <= 0:
            errors.append(f"invalid PNG dimensions: {path.relative_to(ROOT)}")
        # These diagnostic composites intentionally retain the installed
        # vanilla Farmer/Hair alpha values. Binary-alpha validation belongs to
        # the generated Hat/Shirt assets and is handled by the weather-pack
        # validator, not to source-faithful screenshots of vanilla layers.
    result = {
        "status": "PASS" if not errors else "FAIL",
        "styles": data.get("selectableStyleCount"),
        "composites": data.get("compositeCount"),
        "severeFallbackStyleIds": data.get("severeStyleIds"),
        "runtimePromotion": architecture["rarePlusTemplate"].get("promotionStatus"),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
