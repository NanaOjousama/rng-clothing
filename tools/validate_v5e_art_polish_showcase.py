#!/usr/bin/env python3
"""Static validation for the post-V5E five-piece art-polish showcase."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from generator.png_utils import read_rgba_png
from tools.generate_v5e_art_polish_showcase import _concepts, _render

OUT=ROOT/"output"/"fashionsense"/"v5e-art-polish-showcase"


def main():
    errors=[]; checks=[]; concepts=_concepts(); renders=[_render(c) for c in concepts]
    if len(concepts)!=5: errors.append("showcase must contain exactly five garments")
    if len({c["family"] for c in concepts})!=5: errors.append("showcase article families are not distinct")
    if sum("JACKET" in c["family"] for c in concepts)!=2: errors.append("showcase requires exactly two distinct jacket families")
    if not any("HOOD" in c["family"] for c in concepts): errors.append("showcase lacks hoodie")
    if not any("WAISTCOAT" in c["family"] for c in concepts): errors.append("showcase lacks formal/semi-formal top")
    if not any("CASUAL" in c["family"] for c in concepts): errors.append("showcase lacks stylish casual top")
    if not errors: checks.append("five distinct requested fashion roles")
    for concept,render in zip(concepts,renders):
        if not render["metrics"]["alphaGeometryPreserved"]: errors.append(f"{concept['name']}: polish changed alpha")
        if render["metrics"]["runtimeFieldsChanged"]: errors.append(f"{concept['name']}: polish changed runtime fields")
        if render["runtime"].get("customSleevesAppearance") is True: errors.append(f"{concept['name']}: rejected custom Sleeves leaked")
        png=read_rgba_png(OUT/concept["key"]/"shirt.png")
        if (png["width"],png["height"])!=(16,64): errors.append(f"{concept['name']}: wrong Shirt texture size")
        if any(p[3] not in {0,255} for row in png["pixels"] for p in row): errors.append(f"{concept['name']}: nonbinary alpha")
        if not any(render["metrics"]["changedShadeRoleCells"].values()): errors.append(f"{concept['name']}: polish stage was inert")
    if not any("alpha" in e for e in errors): checks.append("frozen alpha geometry and binary direct pixels")
    hoodie=next(r for c,r in zip(concepts,renders) if "HOOD" in c["family"])
    expected={"FrontHat":{"X":-4,"Y":30},"RightHat":{"X":-4,"Y":26},"BackHat":{"X":-4,"Y":26},"LeftHat":{"X":-4,"Y":26}}
    actual={key:hoodie["raw"].hood_json[key]["HeadPosition"] for key in expected}
    if actual!=expected: errors.append(f"hood anchors changed: {actual}")
    else: checks.append("hood anchors and category contract preserved")
    v5e=renders[0]
    if v5e["runtime"].get("mechanism")!="NATIVE_ANIMATED_SLEEVES_V1": errors.append("V5E native sleeve correction regressed")
    else: checks.append("known-good native sleeve contract retained")
    expected_files=(OUT/"V5E_POST_POLISH_GAMEPLAY.png",OUT/"V5E_POST_POLISH_DIRECTIONS.png",ROOT/"output"/"comparisons"/"V5E_POST_POLISH_SHOWCASE.png",ROOT/"output"/"comparisons"/"V5E_ART_POLISH_BEFORE_AFTER.png")
    for path in expected_files:
        if not path.exists(): errors.append(f"missing comparison {path}")
    result={"status":"PASS_STATIC_RUNTIME_RETEST_REQUIRED" if not errors else "FAIL","checks":checks,"errors":errors,"garments":5,"customSleeves":0,"runtimePromotion":"EXPERIMENTAL","beautyClaim":"HUMAN_GAMEPLAY_REVIEW_REQUIRED"}
    (OUT/"filesystem-validation.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if errors: raise SystemExit(1)


if __name__=="__main__": main()
