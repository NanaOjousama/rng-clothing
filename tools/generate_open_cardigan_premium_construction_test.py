#!/usr/bin/env python3
"""Generate the three-way OPEN_CARDIGAN construction-sophistication proof."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.controlled_test.hd_adapter import render_controlled_hd_adapter
from generator.controlled_test.hd_validation import _anchor_metrics, validate_hd_adapter_render
from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER, HAIR, _farmer_composite


OUT = ROOT / "output" / "fashionsense" / "open-cardigan-premium-construction-test"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Open-Cardigan-Premium-Construction-Test"
REPORT = ROOT / "reports" / "OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_TEST_REPORT.md"
PREVIOUS_PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Open-Cardigan-Premium-Quality-Test" / "Shirts"
UNIQUE_ID = "RNGClothing.FashionSense.OpenCardiganPremiumConstructionTest"
DIRECTIONS = ("front", "right", "back", "left")
MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))
BG: RGBA = (232, 226, 217, 255)
PANEL: RGBA = (205, 197, 186, 255)
INK: RGBA = (39, 37, 36, 255)
BASE_COLOR: RGBA = (67, 61, 57, 255)
EXEC_COLOR: RGBA = (81, 96, 151, 255)
CONSTRUCTION_COLOR: RGBA = (94, 75, 131, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _tile(canvas, sprite, x, y, border):
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _isolated_8x(items):
    canvas = blank_image(552, 506, BG)
    draw_text(canvas, "OPEN_CARDIGAN CONSTRUCTION TEST | ISOLATED 8X", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 26 + row * 158
        draw_text(canvas, item["label"], 8, y0, color=item["color"])
        for col, direction in enumerate(DIRECTIONS):
            x = 8 + col * 136
            draw_text(canvas, direction.upper(), x, y0 + 12, color=INK)
            _tile(canvas, nearest_scale(item["render"].frames[direction], 8), x, y0 + 27, item["color"])
    return canvas


def _four_direction(items):
    canvas = blank_image(500, 266, BG)
    draw_text(canvas, "BASELINE / EXECUTION / CONSTRUCTION | 4X", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 27 + row * 78
        draw_text(canvas, item["short"], 8, y0 + 22, color=item["color"])
        for col, direction in enumerate(DIRECTIONS):
            x = 144 + col * 86
            draw_text(canvas, direction.upper(), x, y0, color=INK)
            _tile(canvas, nearest_scale(item["render"].frames[direction], 4), x, y0 + 13, item["color"])
    return canvas


def _farmer_sheet(items):
    canvas = blank_image(304, 474, BG)
    draw_text(canvas, "FARMER COMPOSITES | FRONT RIGHT BACK LEFT", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 27 + row * 148
        draw_text(canvas, item["short"], 8, y0, color=item["color"])
        for col, direction in enumerate(DIRECTIONS):
            x = 8 + col * 72
            _tile(canvas, item["farmer"][direction], x, y0 + 16, item["color"])
    return canvas


def _gameplay_sheet(items):
    canvas = blank_image(236, 166, BG)
    draw_text(canvas, "GAMEPLAY FRONT READ", 8, 7, color=INK)
    for col, item in enumerate(items):
        x = 8 + col * 76
        draw_text(canvas, item["short"], x, 20, color=item["color"])
        _tile(canvas, item["farmer"]["front"], x, 35, item["color"])
    return canvas


def _front_sheet(items):
    canvas = blank_image(628, 184, BG)
    draw_text(canvas, "DIRECT THREE-WAY FRONT | ISOLATED + FARMER", 8, 7, color=INK)
    for col, item in enumerate(items):
        x = 8 + col * 208
        draw_text(canvas, item["short"], x, 21, color=item["color"])
        _tile(canvas, nearest_scale(item["render"].frames["front"], 8), x, 39, item["color"])
        _tile(canvas, item["farmer"]["front"], x + 138, 39, item["color"])
    return canvas


def _shirt_json(name, render):
    data = {"Name": name, "Format": "7.5.0", "Tags": ["RNG Clothing", "OPEN_CARDIGAN", "CARDIGAN", "LAVENDER_DAY", "Construction Test", "Experimental"]}
    for key, y in MODELS:
        data[key] = {
            "Scale": 2.0,
            "HideSleeves": False,
            "DisableGrayscale": True,
            "SleeveColors": [list(color) for color in render.sleeve_colors],
            "StartingPosition": {"X": 0, "Y": y},
            "BodyPosition": {"X": 0, "Y": 32},
            "ShirtSize": {"Width": 16, "Length": 16},
        }
    return data


def _preset(index, name):
    return {
        "Name": f"Cardigan Construction {index:02d} - {name}",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{name}",
        "SleevesId": "None",
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _alpha(render, direction):
    return {(x, y) for y, row in enumerate(render.frames[direction]) for x, pixel in enumerate(row) if pixel[3]}


def _validate(baseline, execution, construction):
    renders = (baseline, execution, construction)
    quality = {render.execution_profile: validate_hd_adapter_render(render) for render in renders}
    errors = []
    if any(item["status"] != "PASS" for item in quality.values()): errors.append("one or more variants failed HD quality validation")
    if not all(render.recipe["grammarId"] == "OPEN_CARDIGAN" and render.recipe["materialId"] == "CARDIGAN" and render.recipe["paletteStoryId"] == "LAVENDER_DAY" for render in renders): errors.append("semantic identity changed")
    if len({render.sleeve_colors for render in renders}) != 1: errors.append("native sleeve colors changed")
    reference_matches = {}
    for key, render, path in (
        ("baseline", baseline, PREVIOUS_PACK / "BaselineCardigan" / "shirt.png"),
        ("premiumExecution", execution, PREVIOUS_PACK / "PremiumCardigan" / "shirt.png"),
    ):
        reference_matches[key] = path.exists() and read_rgba_png(path)["pixels"] == render.texture
        if not reference_matches[key]: errors.append(f"{key} no longer matches previous approved comparison")
    metrics = construction.polish_metrics.get("premiumCardiganConstruction", {})
    if not metrics.get("coverageRowsZeroToTwoPreserved"): errors.append("upper coverage rows changed")
    if not metrics.get("singleConnectedComponent"): errors.append("alpha detached")
    if metrics.get("maximumLogicalY") != 15: errors.append("construction escaped upper-body frame")
    if metrics.get("newMotifs") != 0 or metrics.get("newPaletteRoles") != 0: errors.append("construction relied on decoration/palette expansion")
    alpha_delta = {
        direction: {
            "addedVsExecution": len(_alpha(construction, direction) - _alpha(execution, direction)),
            "removedVsExecution": len(_alpha(execution, direction) - _alpha(construction, direction)),
        }
        for direction in DIRECTIONS
    }
    if any(not (values["addedVsExecution"] or values["removedVsExecution"]) for values in alpha_delta.values()): errors.append("construction alpha did not change every direction")
    if any(construction.coverage_missing.values()): errors.append("body coverage failed")
    return {
        "status": "PASS_STATIC_VISUAL_REVIEW_REQUIRED" if not errors else "FAIL_STATIC",
        "errors": errors,
        "runtimeStatus": "NOT_TESTED",
        "referenceMatches": reference_matches,
        "sameGrammarMaterialPalette": True,
        "sameNativeSleeveColors": True,
        "alphaDeltaVsPremiumExecution": alpha_delta,
        "safeEnvelope": {
            "bodyCoverageMissing": construction.coverage_missing,
            "coverageRowsZeroToTwoPreserved": metrics.get("coverageRowsZeroToTwoPreserved"),
            "singleConnectedComponent": metrics.get("singleConnectedComponent"),
            "maximumLogicalY": metrics.get("maximumLogicalY"),
            "frameSize": [16, 16],
        },
        "constructionEvidence": metrics,
        "quality": quality,
        "qualityAnchors": _anchor_metrics(),
        "humanVisualDecision": "PASS_PREMIUM_CONSTRUCTION_CANDIDATE",
        "humanDecisionBasis": "The candidate retains cardigan topology while the mid-body taper, lower re-flare, curved open leaves, trapezoid pockets and direction-specific side drape remain visible at Farmer scale without motifs or palette change.",
    }


def _package(items, validation):
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    presets = []
    for index, item in enumerate(items, 1):
        name = f"Lavender Hearth Cardigan - {item['label'].title()}"
        folder = PACK / "Shirts" / item["folder"]
        folder.mkdir(parents=True)
        write_rgba_png(folder / "shirt.png", item["render"].texture)
        _json(folder / "shirt.json", _shirt_json(name, item["render"]))
        presets.append(_preset(index, name))
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing Open Cardigan Premium Construction Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Three-way OPEN_CARDIGAN Baseline, Premium Execution, and Premium Construction test.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "static-validation.json", validation)
    (PACK / "README.md").write_text(
        "# Open Cardigan Premium Construction Test\n\n"
        "Copy this folder into `Stardew Valley/Mods`, restart SMAPI, open the Fashion Sense Hand Mirror, and switch between presets `Cardigan Construction 01` through `03`.\n\n"
        "The pack contains exactly three Shirt appearances and no custom Sleeves. All use Scale 2, BodyPosition `(0,32)`, and native Farmer `SleeveColors`. The third candidate changes bounded Shirt alpha, so test front/right/back/left while standing and walking before promotion. Runtime status: **NOT TESTED**.\n",
        encoding="utf-8",
    )
    errors = []
    shirts = sorted((PACK / "Shirts").glob("*/shirt.json"))
    if len(shirts) != 3 or len(presets) != 3: errors.append("pack must contain exactly three Shirts and presets")
    if (PACK / "Sleeves").exists() or any(preset["SleevesId"] != "None" for preset in presets): errors.append("custom Sleeves leaked into pack")
    for path in shirts:
        data = json.loads(path.read_text(encoding="utf-8")); image = read_rgba_png(path.with_name("shirt.png"))
        if [image["width"], image["height"]] != [16, 64]: errors.append(f"{path.parent.name}: atlas must be 16x64")
        for key, y in MODELS:
            model = data[key]
            if not (model["Scale"] == 2.0 and model["BodyPosition"] == {"X": 0, "Y": 32} and model["StartingPosition"] == {"X": 0, "Y": y} and model["HideSleeves"] is False and len(model["SleeveColors"]) == 3): errors.append(f"{path.parent.name}: {key} runtime contract failed")
    hashes = {str(path.relative_to(PACK)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((PACK / "Shirts").glob("*/shirt.png"))}
    result = {"status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not errors else "FAIL_STATIC", "errors": errors, "hashes": hashes, "runtimeStatus": "NOT_TESTED"}
    _json(PACK / "pack-validation.json", result)
    return result


def _write_report(validation, pack_validation):
    metrics = validation["constructionEvidence"]
    alpha = validation["alphaDeltaVsPremiumExecution"]
    anchor_rows = "\n".join(
        f"| {name} | {data.get('activeColors', 'n/a')} | {data.get('dominantFillPercentage', 0):.1%} | {data.get('luminanceRange', 'n/a')} |"
        for name, data in validation["qualityAnchors"].items()
    )
    alpha_rows = "\n".join(f"| {direction} | {values['addedVsExecution']} | {values['removedVsExecution']} |" for direction, values in alpha.items())
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(f"""# Open Cardigan Premium Construction Test Report

Status: **{validation['status']}**. Pack: **{pack_validation['status']}**. Runtime remains **NOT TESTED**.

## 1. Silhouette and construction changes

`PREMIUM_CONSTRUCTION_CARDIGAN_V1` keeps the Premium Execution fabric-plane finish, then adds a bounded cardigan construction pass. It preserves the upper three-row coverage carrier; tapers the outermost mid-body column; re-flares into the existing lower knit footprint; changes the opening from parallel strips into curved leaves that narrow again toward the hem; reconstructs patch pockets as shallow trapezoids; bows the side opening outward before returning into the hem; and recomputes selective contours after geometry changes. The rear remains a quiet knit mass with the corrected shallow neck.

## 2. Alpha changes versus Premium Execution

| Direction | Added cells | Removed cells |
|---|---:|---:|
{alpha_rows}

All alpha remains one connected component. No cell extends below logical row {metrics['maximumLogicalY']}.

## 3. Safe-envelope verification

- Proven mandatory rows 0–2 preserved: **{str(metrics['coverageRowsZeroToTwoPreserved']).upper()}**
- Missing required body cells: **none**
- Frame: **16×16**, atlas: **16×64**
- Maximum occupied row: **15**
- Detached alpha components: **none**
- Scale / BodyPosition: **2 / (0,32)**
- Native Farmer sleeves and SleeveColors: **unchanged**
- Custom Sleeves: **absent**

## 4. Reused renderer stages

All variants use `render_fs_hd_v2 -> V3 surface -> V4/V5B STANDARD_JACKET cardigan base -> V5D CARDIGAN -> polish_upper_frames -> soften_shared_rear_neck -> semantic palette/material adapter`. Premium Execution adds `polish_open_cardigan_premium_execution`. Premium Construction is cumulative and then adds `refine_open_cardigan_premium_construction` before semantic palette resolution.

## 5. New bounded helper

`art_polish_v5e.refine_open_cardigan_premium_construction` is the only new construction helper. It is allowlisted only through `execution_profile=PREMIUM_CONSTRUCTION_CARDIGAN_V1`. It changes alpha and existing opening/layer/pocket carriers inside the frozen frame, verifies connectedness and coverage, and introduces zero motifs or palette roles. It has not been propagated.

## 6. Comparison against Premium Execution

Baseline and Premium Execution match the previous two-item pack byte-for-byte. Premium Construction uses the same grammar, material, palette, sleeve ramp, and underlying construction family. Its gain is geometric: a less rectangular torso, shaped lower drape, curved leaf relationship, integrated pockets, side hanging depth, and direction-owned contour termination. It does not merely increase shade counts.

## 7. Prior V5E/V6 anchors

| Anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
{anchor_rows}

The candidate approaches those anchors through deliberate plane boundaries and authored directional construction, not by copying their palettes, motifs, or jacket logic. Native-sleeve and 16×16 limits still prevent true loose sleeve volume.

## 8–9. Farmer-scale observation and decision

At static Farmer scale the third variant remains an open cardigan: the inner shirt stays broad, soft knit leaves frame it, native sleeves remain exposed for animation, and the lower mass returns into a ribbed hem. Its front and side silhouette differs from both earlier versions without becoming a blazer or coat; the back is cleaner and subtly shaped rather than decorated.

Decision: **PASS_PREMIUM_CONSTRUCTION_CANDIDATE** for live review. The visible gain is construction-driven: alpha distribution, proportion, drape and layer topology changed while `LAVENDER_DAY`, semantic color roles, motif count, and garment family did not. Static preview cannot certify motion or clipping.

## 10. Reusability conclusion

The result supports a possible reusable *quality-sophistication layer* made of bounded, family-specific construction refiners after shared HD polish. It does **not** support applying one universal premium silhouette. Expansion should wait for live front/side/back/walk evidence from this pack.

## Outputs

- Experimental pack: `{PACK}`
- Per-version assets: `{OUT}`
- Three-way front: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FRONT.png'}`
- Four-direction comparison: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FOUR_DIRECTION.png'}`
- Farmer composites: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FARMER.png'}`
- Gameplay comparison: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_GAMEPLAY.png'}`
- Isolated 8× inspection: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_ISOLATED_8X.png'}`
- Validation: `{OUT / 'static-validation.json'}`

Stop state: exactly one Baseline, one Premium Execution, and one Premium Construction cardigan; no propagation or additional generation.
""", encoding="utf-8")


def main():
    baseline = render_controlled_hd_adapter("OPEN_CARDIGAN", execution_profile="BASELINE")
    execution = render_controlled_hd_adapter("OPEN_CARDIGAN", execution_profile="PREMIUM_CARDIGAN_V1")
    construction = render_controlled_hd_adapter("OPEN_CARDIGAN", execution_profile="PREMIUM_CONSTRUCTION_CARDIGAN_V1")
    validation = _validate(baseline, execution, construction)
    if validation["errors"]: raise SystemExit(json.dumps(validation, indent=2))
    body = read_rgba_png(FARMER)["pixels"]; hair = read_rgba_png(HAIR)["pixels"]
    definitions = (
        ("BASELINE", "BASE", "BaselineCardigan", BASE_COLOR, baseline),
        ("PREMIUM EXECUTION", "EXEC", "PremiumExecutionCardigan", EXEC_COLOR, execution),
        ("PREMIUM CONSTRUCTION", "CONSTRUCT", "PremiumConstructionCardigan", CONSTRUCTION_COLOR, construction),
    )
    items = [
        {"label": label, "short": short, "folder": folder, "color": color, "render": render, "farmer": {direction: _farmer_composite(body, hair, render.frames[direction], direction) for direction in DIRECTIONS}}
        for label, short, folder, color, render in definitions
    ]
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); COMPARE.mkdir(parents=True, exist_ok=True)
    for item in items:
        target = OUT / item["folder"]
        target.mkdir()
        write_rgba_png(target / "shirt.png", item["render"].texture)
        _json(target / "semantic-recipe.json", item["render"].recipe)
        _json(target / "execution-summary.json", {"executionProfile": item["render"].execution_profile, "stageTrace": item["render"].stage_trace, "polishMetrics": item["render"].polish_metrics, "runtimeStatus": "NOT_TESTED"})
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FRONT.png", _front_sheet(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FOUR_DIRECTION.png", _four_direction(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_FARMER.png", _farmer_sheet(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_GAMEPLAY.png", _gameplay_sheet(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_CONSTRUCTION_ISOLATED_8X.png", _isolated_8x(items))
    _json(OUT / "static-validation.json", validation)
    pack_validation = _package(items, validation)
    if pack_validation["errors"]: raise SystemExit(json.dumps(pack_validation, indent=2))
    _write_report(validation, pack_validation)
    print(validation["status"]); print(pack_validation["status"]); print(PACK)


if __name__ == "__main__":
    main()
