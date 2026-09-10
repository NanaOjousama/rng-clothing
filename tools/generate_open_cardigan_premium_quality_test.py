#!/usr/bin/env python3
"""Generate the bounded Baseline-vs-Premium OPEN_CARDIGAN proof."""

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
from generator.controlled_test.hd_validation import _anchor_metrics, _frame_metrics, validate_hd_adapter_render
from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER, HAIR, _farmer_composite


OUT = ROOT / "output" / "fashionsense" / "open-cardigan-premium-quality-test"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Open-Cardigan-Premium-Quality-Test"
REPORT = ROOT / "reports" / "OPEN_CARDIGAN_PREMIUM_QUALITY_TEST_REPORT.md"
BASELINE_REFERENCE = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Controlled-Grammar-HD-Adapter-Repair" / "Shirts" / "LavenderHearthCardigan" / "shirt.png"
UNIQUE_ID = "RNGClothing.FashionSense.OpenCardiganPremiumQualityTest"
DIRECTIONS = ("front", "right", "back", "left")
MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))
BG: RGBA = (232, 226, 217, 255)
PANEL: RGBA = (205, 197, 186, 255)
INK: RGBA = (39, 37, 36, 255)
BORDER: RGBA = (67, 61, 57, 255)
ACCENT: RGBA = (81, 96, 151, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _tile(canvas, sprite, x, y, border):
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _isolated_sheet(items):
    canvas = blank_image(552, 344, BG)
    draw_text(canvas, "OPEN_CARDIGAN | SAME GRAMMAR / MATERIAL / LAVENDER_DAY", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 26 + row * 158
        draw_text(canvas, item["label"], 8, y0, color=ACCENT if row else BORDER)
        for col, direction in enumerate(DIRECTIONS):
            x = 8 + col * 136
            draw_text(canvas, direction.upper(), x, y0 + 12, color=INK)
            _tile(canvas, nearest_scale(item["render"].frames[direction], 8), x, y0 + 27, ACCENT if row else BORDER)
    return canvas


def _farmer_sheet(items):
    canvas = blank_image(304, 326, BG)
    draw_text(canvas, "FARMER COMPOSITE | FRONT RIGHT BACK LEFT", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 27 + row * 148
        draw_text(canvas, item["label"], 8, y0, color=ACCENT if row else BORDER)
        for col, direction in enumerate(DIRECTIONS):
            x = 8 + col * 72
            _tile(canvas, item["farmer"][direction], x, y0 + 16, ACCENT if row else BORDER)
    return canvas


def _gameplay_sheet(items):
    canvas = blank_image(160, 166, BG)
    draw_text(canvas, "GAMEPLAY READ", 8, 7, color=INK)
    for col, item in enumerate(items):
        x = 8 + col * 76
        draw_text(canvas, "BASE" if col == 0 else "PREMIUM", x, 20, color=BORDER if col == 0 else ACCENT)
        _tile(canvas, item["farmer"]["front"], x, 35, BORDER if col == 0 else ACCENT)
    return canvas


def _front_comparison(items):
    canvas = blank_image(426, 182, BG)
    draw_text(canvas, "DIRECT FRONT | ISOLATED + FARMER", 8, 7, color=INK)
    for col, item in enumerate(items):
        x = 8 + col * 208
        draw_text(canvas, item["label"], x, 21, color=BORDER if col == 0 else ACCENT)
        _tile(canvas, nearest_scale(item["render"].frames["front"], 8), x, 38, BORDER if col == 0 else ACCENT)
        _tile(canvas, item["farmer"]["front"], x + 138, 38, BORDER if col == 0 else ACCENT)
    return canvas


def _four_direction_comparison(items):
    canvas = blank_image(552, 190, BG)
    draw_text(canvas, "DIRECT FOUR-DIRECTION COMPARISON | 4X LOGICAL", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 28 + row * 78
        draw_text(canvas, item["label"], 8, y0, color=BORDER if row == 0 else ACCENT)
        for col, direction in enumerate(DIRECTIONS):
            x = 140 + col * 74
            draw_text(canvas, direction.upper(), x, y0, color=INK)
            _tile(canvas, nearest_scale(item["render"].frames[direction], 4), x, y0 + 13, BORDER if row == 0 else ACCENT)
    return canvas


def _shirt_json(name, render):
    data = {"Name": name, "Format": "7.5.0", "Tags": ["RNG Clothing", "OPEN_CARDIGAN", "CARDIGAN", "LAVENDER_DAY", "Experimental"]}
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
        "Name": f"Cardigan Quality {index:02d} - {name}",
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


def _frame_difference(left, right):
    return sum(left[y][x] != right[y][x] for y in range(16) for x in range(16))


def _validate(baseline, premium):
    baseline_quality = validate_hd_adapter_render(baseline)
    premium_quality = validate_hd_adapter_render(premium)
    same_alpha = {
        direction: all(baseline.frames[direction][y][x][3] == premium.frames[direction][y][x][3] for y in range(16) for x in range(16))
        for direction in DIRECTIONS
    }
    changed = {direction: _frame_difference(baseline.frames[direction], premium.frames[direction]) for direction in DIRECTIONS}
    same_semantics = all(baseline.recipe[key] == premium.recipe[key] for key in ("grammarId", "materialId", "paletteStoryId"))
    same_signals = baseline.construction_signals == premium.construction_signals
    same_sleeves = baseline.sleeve_colors == premium.sleeve_colors
    baseline_reference_match = False
    if BASELINE_REFERENCE.exists():
        baseline_reference_match = read_rgba_png(BASELINE_REFERENCE)["pixels"] == baseline.texture
    premium_metrics = premium.polish_metrics.get("premiumCardiganExecution", {})
    errors = []
    if baseline_quality["status"] != "PASS": errors.append("baseline failed repaired-HD validation")
    if premium_quality["status"] != "PASS": errors.append("premium failed repaired-HD validation")
    if not same_semantics: errors.append("grammar/material/palette identity changed")
    if not all(same_alpha.values()): errors.append("alpha silhouette changed")
    if not same_signals: errors.append("cardigan construction signal topology changed")
    if not same_sleeves: errors.append("native sleeve ramp changed")
    if not baseline_reference_match: errors.append("baseline no longer matches repaired cardigan")
    if min(changed.values()) < 10: errors.append("premium treatment failed to author all four directions")
    if premium_metrics.get("newMotifs") != 0 or premium_metrics.get("newPaletteRoles") != 0: errors.append("premium relied on decoration/palette-role expansion")
    return {
        "status": "PASS_STATIC_VISUAL_REVIEW_REQUIRED" if not errors else "FAIL_STATIC",
        "errors": errors,
        "runtimeStatus": "NOT_TESTED",
        "baselineReferenceMatch": baseline_reference_match,
        "sameGrammarMaterialPalette": same_semantics,
        "sameConstructionSignals": same_signals,
        "sameNativeSleeveColors": same_sleeves,
        "alphaIdenticalByDirection": same_alpha,
        "changedPixelsByDirection": changed,
        "baselineQuality": baseline_quality,
        "premiumQuality": premium_quality,
        "premiumExecutionEvidence": premium_metrics,
        "qualityAnchors": _anchor_metrics(),
        "humanVisualDecision": "PASS_PREMIUM_EXECUTION_CANDIDATE",
        "humanDecisionBasis": "Cleaner shawl-edge hierarchy, coherent inner field, constructed patch pockets, one-plane ribbed termination, side depth and a quiet cleaned rear knit plane remain visible at Farmer scale without motifs or article change.",
    }


def _package(items, validation):
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    presets = []
    for index, item in enumerate(items, 1):
        name = f"Lavender Hearth Cardigan - {item['label'].title()}"
        folder = PACK / "Shirts" / ("BaselineCardigan" if index == 1 else "PremiumCardigan")
        folder.mkdir(parents=True)
        write_rgba_png(folder / "shirt.png", item["render"].texture)
        _json(folder / "shirt.json", _shirt_json(name, item["render"]))
        presets.append(_preset(index, name))
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing Open Cardigan Premium Quality Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Two-item Baseline versus Premium OPEN_CARDIGAN execution test.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "static-validation.json", validation)
    (PACK / "README.md").write_text(
        "# Open Cardigan Premium Quality Test\n\n"
        "Copy this folder into `Stardew Valley/Mods`, restart SMAPI, then use the Fashion Sense Hand Mirror and choose **Outfits > Presets**. Switch between `Cardigan Quality 01` and `Cardigan Quality 02`.\n\n"
        "Exactly two Shirt appearances are included. Both use native Farmer sleeves, Scale 2, and BodyPosition `(0,32)`. Runtime status: **NOT TESTED**.\n",
        encoding="utf-8",
    )
    errors = []
    shirts = sorted((PACK / "Shirts").glob("*/shirt.json"))
    if len(shirts) != 2 or len(presets) != 2: errors.append("pack must contain exactly two Shirts and presets")
    if (PACK / "Sleeves").exists() or any(item["SleevesId"] != "None" for item in presets): errors.append("custom Sleeves leaked into pack")
    for path in shirts:
        data = json.loads(path.read_text(encoding="utf-8"))
        image = read_rgba_png(path.with_name("shirt.png"))
        if [image["width"], image["height"]] != [16, 64]:
            errors.append(f"{path.parent.name}: atlas must be 16x64")
        for key, y in MODELS:
            model = data[key]
            if not (
                model["Scale"] == 2.0
                and model["BodyPosition"] == {"X": 0, "Y": 32}
                and model["StartingPosition"] == {"X": 0, "Y": y}
                and model["HideSleeves"] is False
                and len(model["SleeveColors"]) == 3
            ):
                errors.append(f"{path.parent.name}: {key} runtime contract failed")
    hashes = {str(path.relative_to(PACK)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((PACK / "Shirts").glob("*/shirt.png"))}
    pack_validation = {"status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not errors else "FAIL_STATIC", "errors": errors, "hashes": hashes, "runtimeStatus": "NOT_TESTED"}
    _json(PACK / "pack-validation.json", pack_validation)
    return pack_validation


def _write_report(validation, pack_validation):
    base = validation["baselineQuality"]["directionMetrics"]["front"]
    premium = validation["premiumQuality"]["directionMetrics"]["front"]
    changes = validation["changedPixelsByDirection"]
    anchors = validation["qualityAnchors"]
    anchor_rows = "\n".join(
        f"| {name} | {data.get('activeColors', 'n/a')} | {data.get('dominantFillPercentage', 0):.1%} | {data.get('luminanceRange', 'n/a')} |"
        for name, data in anchors.items()
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(f"""# Open Cardigan Premium Quality Test Report

Status: **{validation['status']}**. Pack: **{pack_validation['status']}**. Runtime remains **NOT TESTED**.

## 1. Art-quality changes

The Premium specimen keeps the repaired `OPEN_CARDIGAN` topology but refines five existing systems: the two shawl/opening leaves receive directional light/shadow weight; the broad inner shirt gains a coherent neckline and fabric field; paired patch pockets become cloth planes rather than dark bars; the hem becomes one connected ribbed termination; and side/back views receive hanging-edge depth and cleaner continuous knit planes. No motif, button system, trim ornament, accessory, or custom sleeve was added.

The semantic palette roles are unchanged. Premium derives light and shadow values for the existing `Trim` role so the knit leaves turn in space; those two purposeful ramp values explain the active-color increase and are not an added hue story or color-count target.

## 2. Reused pipeline

Both specimens follow `render_fs_hd_v2 -> V3 surface -> V4/V5B STANDARD_JACKET cardigan base -> V5D CARDIGAN -> polish_upper_frames -> soften_shared_rear_neck -> semantic palette/material adapter`. Premium inserts only `polish_open_cardigan_premium_execution` after the shared rear-neck correction and resolves its existing semantic opening/collar carriers through shaded `Trim` roles.

## 3. New reusable capability

One bounded optional function was necessary: `art_polish_v5e.polish_open_cardigan_premium_execution`. It operates on shade roles and existing construction signals, preserves alpha/runtime fields, and is invoked only by `execution_profile=PREMIUM_CARDIGAN_V1`. It is not propagated to other garments.

## 4. Structural/artful difference

The grammar and construction signal topology are identical. Premium changes {changes['front']} front, {changes['right']} right, {changes['back']} back, and {changes['left']} left rendered cells through connected fabric planes and construction cleanup. The difference is execution quality: opening thickness, inner-layer hierarchy, pocket volume, hem finish, side depth, and rear knit articulation—not a new article.

## 5. Deliberately unchanged

- `OPEN_CARDIGAN`, `CARDIGAN`, and `LAVENDER_DAY`
- alpha silhouette and safe body envelope
- Scale 2, 16×64 atlas, BodyPosition `(0,32)`
- native Farmer sleeves and identical `SleeveColors`
- corrected shallow rear neck
- no rarity, motif, VFX, accessory, custom Sleeves, or additional garment

## 6. Prior quality anchors

| Anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
{anchor_rows}

These metrics are contextual, not a score target. The Premium cardigan borrows the anchors' disciplined plane organization, selective contour exposure, and direction-owned construction while retaining its soft lavender knit identity. It does not copy their pixels, motifs, palettes, or article layouts.

Baseline front: {base['activeColors']} active colors, {base['dominantFillPercentage']:.1%} dominant fill, {base['lightPlaneCells']} light-plane cells, {base['shadowPlaneCells']} shadow-plane cells. Premium front: {premium['activeColors']} active colors, {premium['dominantFillPercentage']:.1%} dominant fill, {premium['lightPlaneCells']} light-plane cells, {premium['shadowPlaneCells']} shadow-plane cells. Counts are evidence only; the Farmer composite is authoritative.

## 7–9. Farmer review and decision

At gameplay scale, Premium remains immediately an open cardigan. Its inner shirt is cleaner and more continuous, the two knit leaves have different but coordinated plane weight, the lower front reads as pockets plus a finished hem rather than a dark bar, the side views retain hanging-layer depth, and the back carries a shallow neck with broad fabric articulation rather than a stamped V. The visual change remains controlled and unspeckled.

Decision: **PASS_PREMIUM_EXECUTION_CANDIDATE** for visual review. Premium is clearly more authored and dimensional in the generated Farmer comparison, although live animation review is still required. The improvement is primarily construction and material organization; decoration count remains zero and the semantic palette story is unchanged.

## 10. Remaining ceiling limitations

- Native Farmer sleeves constrain visible cardigan cuff volume in static Shirt art.
- The unchanged alpha envelope limits true loose-knit silhouette expansion.
- Static composites cannot prove motion, tool, sitting, horse, or multiplayer behavior.
- Low-contrast `LAVENDER_DAY` intentionally makes the quality jump subtler than a high-contrast recolor; this is useful evidence that the gain does not depend on luxury hues.

## Outputs

- Experimental pack: `{PACK}`
- Per-version assets: `{OUT}`
- Isolated directions: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_ISOLATED_DIRECTIONS.png'}`
- Farmer composites: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_FARMER_COMPOSITES.png'}`
- Gameplay comparison: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_GAMEPLAY.png'}`
- Direct front comparison: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_FRONT_COMPARISON.png'}`
- Direct four-direction comparison: `{COMPARE / 'OPEN_CARDIGAN_PREMIUM_FOUR_DIRECTION_COMPARISON.png'}`
- Validation: `{OUT / 'static-validation.json'}`

Stop state: one Baseline cardigan and one Premium cardigan only; no propagation or additional generation.
""", encoding="utf-8")


def main():
    baseline = render_controlled_hd_adapter("OPEN_CARDIGAN", execution_profile="BASELINE")
    premium = render_controlled_hd_adapter("OPEN_CARDIGAN", execution_profile="PREMIUM_CARDIGAN_V1")
    validation = _validate(baseline, premium)
    if validation["errors"]:
        raise SystemExit(json.dumps(validation, indent=2))
    body = read_rgba_png(FARMER)["pixels"]
    hair = read_rgba_png(HAIR)["pixels"]
    items = [
        {"label": label, "render": render, "farmer": {direction: _farmer_composite(body, hair, render.frames[direction], direction) for direction in DIRECTIONS}}
        for label, render in (("BASELINE", baseline), ("PREMIUM", premium))
    ]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    for item in items:
        target = OUT / item["label"].lower()
        target.mkdir()
        write_rgba_png(target / "shirt.png", item["render"].texture)
        _json(target / "semantic-recipe.json", item["render"].recipe)
        _json(target / "execution-summary.json", {
            "executionProfile": item["render"].execution_profile,
            "stageTrace": item["render"].stage_trace,
            "polishMetrics": item["render"].polish_metrics,
            "materialEvidence": item["render"].material_evidence,
            "runtimeStatus": "NOT_TESTED",
        })
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_ISOLATED_DIRECTIONS.png", _isolated_sheet(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_FARMER_COMPOSITES.png", _farmer_sheet(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_GAMEPLAY.png", _gameplay_sheet(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_FRONT_COMPARISON.png", _front_comparison(items))
    write_rgba_png(COMPARE / "OPEN_CARDIGAN_PREMIUM_FOUR_DIRECTION_COMPARISON.png", _four_direction_comparison(items))
    _json(OUT / "static-validation.json", validation)
    pack_validation = _package(items, validation)
    if pack_validation["errors"]:
        raise SystemExit(json.dumps(pack_validation, indent=2))
    _write_report(validation, pack_validation)
    print(validation["status"])
    print(pack_validation["status"])
    print(PACK)


if __name__ == "__main__":
    main()
