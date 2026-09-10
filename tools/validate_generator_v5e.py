#!/usr/bin/env python3
"""Static validator for the single V5E Rare+ structured field jacket."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png
from generator.renderers.fashionsense.structured_outerwear_v5e import render_fs_v5e
from generator.renderers.fashionsense.runtime_sleeve_contracts import load_runtime_sleeve_contracts, validate_native_animated_sleeves
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.upper_v5b import _stack
from generator.v5e import generate_v5e_recipe, validate_v5e_recipe

OUT = ROOT / "output" / "fashionsense" / "v5e-rareplus-field-jacket"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5E-RarePlus-Field-Jacket"


def main() -> None:
    checks: list[dict] = []
    def check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    recipe = generate_v5e_recipe(); validation = validate_v5e_recipe(recipe); render = render_fs_v5e(recipe)
    polished = polish_upper_frames(render.base, render.frames, render.default_frames, article_family="STRUCTURED_FIELD_JACKET")
    check("semantic recipe", validation.valid, list(validation.errors))
    first = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    second = hashlib.sha256(json.dumps(generate_v5e_recipe(), sort_keys=True).encode()).hexdigest()
    check("deterministic recipe", first == second, first)
    check("body coverage", not any(render.coverage_missing.values()), {d: list(v) for d, v in render.coverage_missing.items()})
    check("bounded inner layer", all(render.default_frames["front"][y][x] != render.default_frames["front"][6][x] for y in (11, 12) for x in (7, 8)), "inner shirt ends above lower jacket opening")
    check("directional authored signals", all(sum(len(render.signal_cells[s][d]) for s in render.signal_cells) >= 8 for d in ("front", "right", "back", "left")), {d: sum(len(render.signal_cells[s][d]) for s in render.signal_cells) for d in ("front", "right", "back", "left")})
    check("native animated sleeve mechanism", not render.companion_required and render.sleeves_texture is None and render.sleeve_metrics.get("mechanism") == "NATIVE_ANIMATED_SLEEVES_V1", render.sleeve_metrics)
    check("binary alpha", {p[3] for row in render.texture for p in row} <= {0, 255}, "shirt")
    shirt = read_rgba_png(PACK / "Shirts" / "SunfieldPathfinderJacket" / "shirt.png")
    check("pack texture dimensions", (shirt["width"], shirt["height"]) == (16, 64), [shirt["width"], shirt["height"]])
    check("packed post-V5E art polish", shirt["pixels"] == _stack(polished.frames) and polished.metrics["alphaGeometryPreserved"], polished.metrics)
    model = json.loads((PACK / "Shirts" / "SunfieldPathfinderJacket" / "shirt.json").read_text())
    mapping = {k: model[k]["StartingPosition"]["Y"] for k in ("FrontShirt", "RightShirt", "LeftShirt", "BackShirt")}
    check("FS direction map", mapping == {"FrontShirt": 0, "RightShirt": 16, "LeftShirt": 32, "BackShirt": 48}, mapping)
    check("shirt anchor contract", all(model[k]["Scale"] == 2.0 and model[k]["BodyPosition"] == {"X": 0, "Y": 32} for k in mapping), "Scale 2, BodyPosition (0,32)")
    forbidden = [name for name in ("Sleeves", "Hats", "Accessories", "Pants", "Shoes") if (PACK / name).exists()]
    check("minimal Rare+ layers", not forbidden, forbidden)
    presets = json.loads((PACK / "preset_outfits.json").read_text())
    check("single coordinated preset", len(presets) == 1 and presets[0]["HatId"] == "None" and presets[0]["AccessoryIds"] == ["None", "None", "None"], presets)
    contract_errors = validate_native_animated_sleeves(PACK, model, presets[0])
    check("frozen native animated sleeve contract", not contract_errors, list(contract_errors))
    contracts = load_runtime_sleeve_contracts()
    native_contract = contracts["contracts"]["NATIVE_ANIMATED_SLEEVES_V1"]
    check("native sleeve contract frozen by live V5E evidence", native_contract.get("status") == "FROZEN_RUNTIME_PASS" and native_contract.get("runtimeEvidence", {}).get("v5eSunfieldPathfinder") == ["front", "right", "back"], native_contract.get("runtimeEvidence"))
    check("rejected detached atlas guarded", contracts["rejectedContracts"]["CUSTOM_32X64_SCALE2_DISABLE_NATIVE_OFFSET"]["mayNotBeGeneratedForProductionOrRuntimeTestPacks"] is True, contracts["rejectedContracts"]["CUSTOM_32X64_SCALE2_DISABLE_NATIVE_OFFSET"])
    contour = render.base.base.design.base.config["outerMaskRamp"]["EXTERIOR_CONTOUR"]
    bridge_ok = True
    bridge_cells = {}
    for direction in ("front", "right", "back", "left"):
        cells = []
        frame = polished.frames[direction]
        for y in range(3, 7):
            xs = [x for x, pixel in enumerate(frame[y]) if pixel[3]]
            if not xs: continue
            for x in (min(xs), max(xs)):
                cells.append((x, y, frame[y][x][0]))
                bridge_ok &= frame[y][x][:3] != (contour, contour, contour)
        bridge_cells[direction] = cells
    check("native sleeve visual bridge is not vest-contoured", bridge_ok, bridge_cells)
    back = polished.default_frames["back"]
    check("integrated back neck transition", back[1][7] == back[1][8] and back[2][7] == back[2][8] and back[1][7] != back[2][7], "two-cell undershirt glimpse over two-cell collar recess")
    check("no benchmark renderer dependency", "references/benchmark" not in (ROOT / "generator" / "renderers" / "fashionsense" / "structured_outerwear_v5e.py").read_text(), "renderer contains reusable grammar only")
    result = {"status": "PASS_STATIC_NATIVE_ARM_RUNTIME_FROZEN_ART_RETEST" if all(c["passed"] for c in checks) else "FAIL", "checks": checks, "runtimePromotion": "NATIVE_ARM_CONTRACT_FROZEN", "beautyClaim": "LIVE_SCREENSHOT_ART_REVIEW_REQUIRED"}
    (PACK / "runtime-contract-validation.json").write_text(json.dumps(result, indent=2) + "\n")
    for item in checks: print(("PASS" if item["passed"] else "FAIL") + "  " + item["name"])
    if result["status"] == "FAIL": raise SystemExit(1)


if __name__ == "__main__": main()
