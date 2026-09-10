#!/usr/bin/env python3
"""Render, validate, and package the three-garment HD-adapter repair proof."""

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

from generator.controlled_test.hd_adapter import render_repair_set
from generator.controlled_test.hd_validation import validate_hd_adapter_collection
from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png


OUT = ROOT / "output" / "fashionsense" / "controlled-grammar-hd-adapter-repair"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Controlled-Grammar-HD-Adapter-Repair"
REPORT = ROOT / "reports" / "CONTROLLED_GRAMMAR_HD_ADAPTER_REPAIR_REPORT.md"
BACK_NECK_REPORT = ROOT / "reports" / "CONTROLLED_GRAMMAR_BACK_NECK_MICRO_FIX_REPORT.md"
UNIQUE_ID = "RNGClothing.FashionSense.ControlledGrammarHDAdapterRepair"
DIRECTIONS = ("front", "right", "back", "left")
MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))

FARMER = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
HAIR = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hairstyles.png")
BODY_FRAME = {"front": 0, "right": 6, "back": 12, "left": 6}
FEATURE_Y = {0: 1, 6: 1, 12: 0}
HAIR_TINT: RGBA = (112, 76, 52, 255)
BG: RGBA = (232, 226, 217, 255)
PANEL: RGBA = (205, 197, 186, 255)
INK: RGBA = (39, 37, 36, 255)
BORDER: RGBA = (67, 61, 57, 255)
ACCENT: RGBA = (57, 117, 121, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _folder(value: str) -> str:
    return "".join(part.capitalize() for part in "".join(ch if ch.isalnum() else " " for ch in value).split())


def _crop(pixels, x, y, width, height):
    return [list(row[x:x+width]) for row in pixels[y:y+height]]


def _flip(pixels):
    return [list(reversed(row)) for row in pixels]


def _tint(pixels, tint):
    return [[(p[0]*tint[0]//255, p[1]*tint[1]//255, p[2]*tint[2]//255, p[3]) for p in row] for row in pixels]


def _farmer_body(body, direction):
    index = BODY_FRAME[direction]
    frame = _crop(body, index % 6 * 16, index // 6 * 32, 16, 32)
    return _flip(frame) if direction == "left" else frame


def _farmer_hair(hair, direction):
    y = 32 if direction in {"right", "left"} else 64 if direction == "back" else 0
    frame = _crop(hair, 0, y, 16, 32)
    return _tint(_flip(frame) if direction == "left" else frame, HAIR_TINT)


def _farmer_composite(body, hair, frame, direction):
    canvas = blank_image(64, 128)
    blit(canvas, nearest_scale(_farmer_body(body, direction), 4), 0, 0)
    blit(canvas, nearest_scale(frame, 2), 16, 56 + FEATURE_Y[BODY_FRAME[direction]] * 4)
    blit(canvas, nearest_scale(_farmer_hair(hair, direction), 4), 0, FEATURE_Y[BODY_FRAME[direction]] * 4 + (4 if direction == "back" else 0))
    return canvas


def _tile(canvas, sprite, x, y, border=BORDER):
    draw_rect(canvas, x-2, y-2, len(sprite[0])+4, len(sprite)+4, border)
    draw_rect(canvas, x-1, y-1, len(sprite[0])+2, len(sprite)+2, PANEL)
    blit(canvas, sprite, x, y)


def _isolated_single(item):
    canvas = blank_image(4*132+16, 164, BG)
    draw_text(canvas, item["render"].recipe["name"].upper(), 8, 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = 8 + index*132
        draw_text(canvas, direction.upper(), x, 20, color=ACCENT)
        _tile(canvas, nearest_scale(item["render"].frames[direction], 8), x, 34, ACCENT)
    return canvas


def _farmer_single(item):
    canvas = blank_image(4*70+16, 164, BG)
    draw_text(canvas, item["render"].recipe["name"].upper(), 8, 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = 8 + index*70
        draw_text(canvas, direction.upper(), x, 20, color=ACCENT)
        _tile(canvas, item["farmer"][direction], x, 34, ACCENT)
    return canvas


def _isolated_collection(items):
    card_h = 166
    canvas = blank_image(4*132+16, card_h*3+28, BG)
    draw_text(canvas, "HD ADAPTER REPAIR | PROVEN V5/HD STACK | DIRECT LOGICAL PIXELS 8X", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 28 + row*card_h
        render = item["render"]
        draw_text(canvas, f"{render.recipe['grammarId']} | {render.recipe['materialId']} | {render.recipe['paletteStoryId']}", 8, y0, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = 8 + index*132
            draw_text(canvas, direction.upper(), x, y0+11, color=ACCENT)
            _tile(canvas, nearest_scale(render.frames[direction], 8), x, y0+25, ACCENT)
    return canvas


def _farmer_collection(items):
    card_w = 286
    canvas = blank_image(card_w*3+14, 180, BG)
    draw_text(canvas, "THREE-GRAMMAR FARMER READABILITY GATE | FRONT RIGHT BACK LEFT", 8, 7, color=INK)
    for col, item in enumerate(items):
        x0 = 8 + col*card_w
        render = item["render"]
        draw_text(canvas, render.recipe["grammarId"], x0, 21, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = x0 + index*69
            draw_text(canvas, direction.upper(), x, 32, color=ACCENT)
            _tile(canvas, item["farmer"][direction], x, 46, ACCENT)
    return canvas


def _gameplay_fronts(items):
    canvas = blank_image(3*92+16, 181, BG)
    draw_text(canvas, "GAMEPLAY-SIZE ARTICLE READ | NAMES BELOW ONLY", 8, 7, color=INK)
    for index, item in enumerate(items):
        x = 8 + index*92
        _tile(canvas, item["farmer"]["front"], x, 29, ACCENT)
        draw_text(canvas, item["render"].recipe["grammarId"], x, 164, color=INK)
    return canvas


def _old_vs_repaired(items):
    old_root = ROOT / "output" / "fashionsense" / "controlled-grammar-palette-test"
    old_paths = {
        "FITTED_TEE": old_root / "01-fitted-tee" / "shirt.png",
        "OPEN_CARDIGAN": old_root / "03-open-cardigan" / "shirt.png",
        "WORK_JACKET": old_root / "08-work-jacket" / "shirt.png",
    }
    canvas = blank_image(3*206+16, 187, BG)
    draw_text(canvas, "REGRESSED STRUCTURE-DEBUG OUTPUT  ->  REPAIRED HD ADAPTER", 8, 7, color=INK)
    for index, item in enumerate(items):
        x0 = 8 + index*206
        grammar = item["render"].recipe["grammarId"]
        draw_text(canvas, grammar, x0, 21, color=INK)
        if old_paths[grammar].exists():
            old = read_rgba_png(old_paths[grammar])["pixels"][:16]
            draw_text(canvas, "OLD DEBUG", x0, 33, color=BORDER)
            _tile(canvas, nearest_scale(old, 8), x0, 47, BORDER)
        draw_text(canvas, "HD ADAPTER", x0+137, 33, color=ACCENT)
        _tile(canvas, nearest_scale(item["render"].frames["front"], 8), x0+137, 47, ACCENT)
    return canvas


def _back_neck_before_after(before_items, after_items):
    card_w = 278
    canvas = blank_image(card_w * 3 + 16, 322, BG)
    draw_text(canvas, "SHARED REAR-NECK MICRO-FIX | BACK VIEW ONLY | BEFORE / AFTER", 8, 7, color=INK)
    for index, (before, after) in enumerate(zip(before_items, after_items)):
        x0 = 8 + index * card_w
        grammar = after["render"].recipe["grammarId"]
        draw_text(canvas, grammar, x0, 21, color=INK)
        draw_text(canvas, "BEFORE", x0, 34, color=BORDER)
        draw_text(canvas, "AFTER", x0 + 140, 34, color=ACCENT)
        _tile(canvas, nearest_scale(before["render"].frames["back"], 8), x0, 49, BORDER)
        _tile(canvas, nearest_scale(after["render"].frames["back"], 8), x0 + 140, 49, ACCENT)
        draw_text(canvas, "FARMER", x0, 185, color=BORDER)
        _tile(canvas, before["farmer"]["back"], x0 + 42, 185, BORDER)
        _tile(canvas, after["farmer"]["back"], x0 + 182, 185, ACCENT)
    return canvas


def _validate_back_neck_micro_fix(before_renders, after_renders):
    errors = []
    results = []
    for before, after in zip(before_renders, after_renders):
        grammar = after.recipe["grammarId"]
        non_back_identical = all(before.frames[d] == after.frames[d] for d in ("front", "right", "left"))
        alpha_identical = all(
            [[pixel[3] for pixel in row] for row in before.frames[d]]
            == [[pixel[3] for pixel in row] for row in after.frames[d]]
            for d in DIRECTIONS
        )
        metrics = after.polish_metrics.get("rearNeckMicroFix", {})
        if not non_back_identical:
            errors.append(f"{grammar}: front or side pixels changed")
        if not alpha_identical:
            errors.append(f"{grammar}: alpha geometry changed")
        if not metrics.get("frontSideUntouched") or not metrics.get("alphaGeometryPreserved"):
            errors.append(f"{grammar}: shared micro-fix invariants missing")
        results.append({
            "grammarId": grammar,
            "frontRightLeftByteIdentical": non_back_identical,
            "alphaGeometryIdentical": alpha_identical,
            **metrics,
        })
    return {
        "status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not errors else "FAIL_STATIC",
        "errors": errors,
        "sharedFunction": "art_polish_v5e.soften_shared_rear_neck",
        "changedMaskRoles": ["DEEP_CREASE", "STRUCTURAL_EDGE"],
        "perGarment": results,
        "runtimeStatus": "NOT_TESTED",
    }


def _write_back_neck_report(micro_validation):
    rows = []
    for item in micro_validation["perGarment"]:
        rows.append(
            f"| `{item['grammarId']}` | {item['changedCells']} | {item['removedPointDepth']} | "
            f"{str(item['frontRightLeftByteIdentical']).upper()} | {str(item['alphaGeometryIdentical']).upper()} |"
        )
    BACK_NECK_REPORT.write_text(f"""# Controlled Grammar Back-Neck Micro-Fix

Status: **{micro_validation['status']}**. Runtime remains **NOT TESTED**.

## Shared correction

The shared `generator/renderers/fashionsense/art_polish_v5e.py::soften_shared_rear_neck` shade-mask pass now removes the unprotected lower point of the inherited rear-opening crease after `polish_upper_frames`. It replaces those cells with adjacent existing fabric shade roles, so upper-left lighting and material ramps remain intact.

Only rear-view `DEEP_CREASE` / `STRUCTURAL_EDGE` cells in the shallow neck window are eligible. Garment-authored cardigan collar and work-jacket yoke signal cells are protected. Alpha, runtime fields, palettes, grammars, native sleeves, front, right, and left art are unchanged.

| Grammar | Back shade cells changed | Old point depth row | Front/right/left identical | Alpha identical |
|---|---:|---:|---|---|
{chr(10).join(rows)}

The fitted tee already had a shallow rear neckline after its closed-opening translation, so the shared pass correctly made no destructive change to it. It was nevertheless regenerated through the same corrected route. The cardigan and work jacket lost only the deep stamped-on point beneath their distinct rear collar/yoke construction.

## Outputs

- Before/after back views: `{COMPARE / 'CONTROLLED_GRAMMAR_BACK_NECK_BEFORE_AFTER.png'}`
- Regenerated directions: `{COMPARE / 'CONTROLLED_GRAMMAR_HD_ADAPTER_DIRECTIONS.png'}`
- Regenerated Farmer composites: `{COMPARE / 'CONTROLLED_GRAMMAR_HD_ADAPTER_FARMER_DIRECTIONS.png'}`
- Micro-fix validation: `{OUT / 'back-neck-micro-fix-validation.json'}`
- Experimental test pack: `{PACK}`

Stop state: shared rear-neck micro-fix only; no additional garments or design changes.
""", encoding="utf-8")


def _shirt_json(render):
    result = {
        "Name": render.recipe["name"],
        "Format": "7.5.0",
        "Tags": ["RNG Clothing", "HD Adapter Repair", render.recipe["grammarId"], render.recipe["materialId"], "Experimental"],
    }
    for key, y in MODELS:
        result[key] = {
            "Scale": 2.0,
            "HideSleeves": False,
            "DisableGrayscale": True,
            "SleeveColors": [list(color) for color in render.sleeve_colors],
            "StartingPosition": {"X": 0, "Y": y},
            "BodyPosition": {"X": 0, "Y": 32},
            "ShirtSize": {"Width": 16, "Length": 16},
        }
    return result


def _preset(index, render):
    return {
        "Name": f"HD Adapter {index:02d} - {render.recipe['name']}",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None", "HatId": "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{render.recipe['name']}",
        "SleevesId": "None", "PantsId": "None", "ShoesId": "None", "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _package(items, validation):
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    presets = []
    index_data = []
    for index, item in enumerate(items, 1):
        render = item["render"]
        folder = _folder(render.recipe["name"])
        target = PACK / "Shirts" / folder
        target.mkdir(parents=True)
        write_rgba_png(target / "shirt.png", render.texture)
        _json(target / "shirt.json", _shirt_json(render))
        presets.append(_preset(index, render))
        index_data.append({"index": index, "name": render.recipe["name"], "grammar": render.recipe["grammarId"], "backend": render.backend, "preset": f"HD Adapter {index:02d} - {render.recipe['name']}", "runtime": "NOT_TESTED", "promotion": "EXPERIMENTAL"})
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing Controlled Grammar HD Adapter Repair",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Three experimental semantic grammars routed through the proven V5/HD art stack.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "specimen-index.json", index_data)
    _json(PACK / "static-validation.json", validation)
    (PACK / "README.md").write_text(
        "# Controlled Grammar HD Adapter Repair\n\n"
        "Copy this entire folder into `Stardew Valley/Mods`, fully restart SMAPI, open the Fashion Sense Hand Mirror, and choose **Outfits > Presets**. Test presets `HD Adapter 01` through `03`.\n\n"
        "This pack contains exactly three Shirts and no custom Sleeves. All use Scale 2, BodyPosition `(0,32)`, `HideSleeves: false`, and the proven native Farmer `SleeveColors` path. Status: **EXPERIMENTAL / STATIC PASS / LIVE TEST REQUIRED**.\n",
        encoding="utf-8",
    )


def _validate_pack(items):
    errors = []
    shirts = sorted((PACK / "Shirts").glob("*/shirt.json"))
    presets = json.loads((PACK / "preset_outfits.json").read_text(encoding="utf-8"))
    if len(shirts) != 3 or len(presets) != 3:
        errors.append("pack must contain exactly three Shirts and three presets")
    if (PACK / "Sleeves").exists() or any(p["SleevesId"] != "None" for p in presets):
        errors.append("custom Sleeves leaked into native-only pack")
    hashes = {}
    for item, path in zip(items, shirts):
        data = json.loads(path.read_text(encoding="utf-8"))
        texture = path.with_name("shirt.png")
        image = read_rgba_png(texture)
        if [image["width"], image["height"]] != [16,64]:
            errors.append(f"{path.parent.name}: wrong atlas dimensions")
        for key, y in MODELS:
            model = data[key]
            if not (model["Scale"] == 2.0 and model["BodyPosition"] == {"X":0,"Y":32} and model["StartingPosition"] == {"X":0,"Y":y} and model["HideSleeves"] is False and len(model["SleeveColors"]) == 3):
                errors.append(f"{path.parent.name}: {key} runtime contract failed")
        hashes[str(texture.relative_to(PACK))] = hashlib.sha256(texture.read_bytes()).hexdigest()
    return {"status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not errors else "FAIL_STATIC", "errors": errors, "hashes": hashes, "runtimeStatus": "NOT_TESTED", "promotion": "EXPERIMENTAL"}


def _write_report(items, validation, pack_validation):
    metrics = {item["grammarId"]: item for item in validation["perGarment"]}
    rows = []
    for item in items:
        render = item["render"]
        metric = metrics[render.recipe["grammarId"]]
        front = metric["directionMetrics"]["front"]
        rows.append(f"| `{render.recipe['grammarId']}` | `{render.recipe['materialId']}` | `{render.recipe['paletteStoryId']}` | {front['dominantFillPercentage']:.1%} | {front['lightPlaneCells']} | {front['shadowPlaneCells']} | {front['structuralDarkCells']} | {metric['frontBackDifference']:.1%} | PASS |")
    anchor_rows = []
    for name, data in validation["qualityAnchors"].items():
        anchor_rows.append(f"| {name} | {data.get('activeColors','n/a')} | {data.get('dominantFillPercentage',0):.1%} | {data.get('luminanceRange','n/a')} |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(f"""# Controlled Grammar HD Adapter Repair Report

Status: **{validation['status']}**. Pack: **{pack_validation['status']}**. Runtime remains **NOT TESTED**.

## 1. Adapter and modules

- `generator/controlled_test/hd_adapter.py` is the bounded semantic adapter. It supports exactly `FITTED_TEE`, `OPEN_CARDIGAN`, and `WORK_JACKET`.
- `generator/controlled_test/hd_validation.py` adds finished-art gates and V5E/V6 anchor measurements.
- `tools/generate_controlled_grammar_hd_adapter_repair.py` exports only the three repaired specimens, previews, validation, and isolated test pack.
- `generator/renderers/fashionsense/reference_grammar.py` is marked `STRUCTURE_DEBUG_ONLY` / `FINAL_ART_ELIGIBLE = False`.
- The old twelve-item export command is hard-disabled. Its existing files remain archived but are not valid quality candidates.

No production renderer was rewritten.

## 2. Reused renderer stages

All three routes begin at `render_fs_hd_v2`, retaining HD region construction, edge exposure, gesture hierarchy, broad upper-left light planes, lower-right shadow masses, termination/cuff rules, binary alpha, and the body-coverage envelope. They then pass through V4/V5B article translation. Cardigan and work jacket additionally use existing V5D construction programs. Every item finally passes through `polish_upper_frames` before palette resolution.

- Tee: `render_fs_hd_v2 -> V3 surface/V4 -> V5B plain tee -> existing reset_v3_surface -> polish_upper_frames`.
- Cardigan: `render_fs_hd_v2 -> V4/V5B STANDARD_JACKET -> V5D CARDIGAN -> polish_upper_frames`.
- Work jacket: `render_fs_hd_v2 -> V4 SHORT_OUTERWEAR -> V5B utility_jacket -> V5D WORK_SHIRT construction -> polish_upper_frames`.

No custom Sleeves appearance is exported. Native Farmer arms remain authoritative.

## 3. Disabled regressed path

`reference_grammar.render_controlled_garment` remains available only for topology/debug visualization. `generate_controlled_grammar_palette_test.py` now exits immediately instead of exporting its flat role grid as final art.

## 4. Semantic mapping

- `FITTED_TEE` maps to the existing fitted Shirt/plain-tee translator, crew binding, closed single layer, short native sleeves, and clean normal termination. Inherited V3 decoration is removed with the existing reset helper; no replacement motif or center stripe is added.
- `OPEN_CARDIGAN` maps to the existing soft STANDARD_JACKET base plus V5D's broad inner field, two knit edges, lower pockets, side hanging edge, coherent rear neck band, and ribbed termination.
- `WORK_JACKET` maps to the existing boxy SHORT_OUTERWEAR/utility-jacket base plus V5D's work collar, firm placket, paired practical pockets, straight termination, side pocket carrier, and broad rear yoke.

## 5–6. Palette and material behavior

The adapter does not paint one RGB across a semantic fabric region. Existing HD mask roles map as follows: exterior contour → `DeepShadow`; deep crease/structural edge → the `DeepShadow`/`StructuralDark` ramp; shadow/base/light/highlight → material-spaced `PrimaryFabric` ramps. Fixed layer fields map into `SecondaryFabric`, `Trim`, or `Accent`, with their own positional light/base/shadow treatment.

Material policy changes actual shade pixels: cotton uses moderate spacing, cardigan compresses its fabric ramp for softer knit transitions, and denim expands shadow/light separation for a firmer shell. Every specimen records the chosen policy, affected shade-cell count, and proven mask-role counts in its summary and validation. The material gate requires both a non-generic policy and at least 24 affected pixels; all three pass.

## 7. Quality metrics

| Grammar | Material | Palette | Dominant front fill | Light plane | Shadow plane | Structural dark | Front/back difference | Result |
|---|---|---|---:|---:|---:|---:|---:|---|
{"\n".join(rows)}

The regressed Orchard front was 91.5% one fill. The repaired tee is below the 65% simple-garment ceiling and carries full light, shadow, crease, and contour planes without adding decoration.

## 8. V5E/V6 anchor comparison

| Prior anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
{"\n".join(anchor_rows)}

The anchor comparison is contextual rather than a demand that a minimal tee match Rare feature count. All repaired garments reuse the same underlying HD shade-role and polish logic. Cardigan/work jacket meet the richer construction gates; the tee meets a stricter simplicity-aware dominant-fill ceiling while retaining meaningful form planes.

## 9. Farmer composites

Static worn review shows three distinct reads: a fitted closed tee; a soft open cardigan with a broad inner shirt; and a boxy work shell with pockets/placket/yoke. Front/right/back/left reconstructions are exported. The Farmer composite is still a static idle approximation; native SleeveColors and motion require live Fashion Sense testing.

## 10. Unresolved issues

- Static previews cannot prove walk, tools, sitting, horse, or multiplayer behavior.
- Native Farmer geometry limits visible cardigan sleeve volume; no unsafe custom atlas was introduced.
- The work jacket uses the proven workwear construction program over a heavier outerwear base. Live review must confirm that shell weight survives animation.
- The palette output is fixed-color (`DisableGrayscale: true`) for this adapter proof; dye/customization integration is intentionally deferred.

## 11. Expansion decision

The adapter is structurally safe to review for expansion because it leaves production renderers untouched and explicitly allowlists three grammars. It should **not** expand until live Farmer review confirms these three. Future grammars should add semantic mappings into existing article/construction programs, not new rasterizers.

## Outputs

- Test pack: `{PACK}`
- Per-garment output: `{OUT}`
- Isolated directions: `{COMPARE / 'CONTROLLED_GRAMMAR_HD_ADAPTER_DIRECTIONS.png'}`
- Farmer directions: `{COMPARE / 'CONTROLLED_GRAMMAR_HD_ADAPTER_FARMER_DIRECTIONS.png'}`
- Gameplay fronts: `{COMPARE / 'CONTROLLED_GRAMMAR_HD_ADAPTER_GAMEPLAY.png'}`
- Old/debug versus repaired: `{COMPARE / 'CONTROLLED_GRAMMAR_HD_ADAPTER_OLD_VS_REPAIRED.png'}`
- Validation: `{OUT / 'static-validation.json'}`

Stop state: exactly three repaired garments; no rarity, additional grammar, custom sleeve, or production-batch work was performed.
""", encoding="utf-8")


def main():
    before_renders = render_repair_set(soften_back_neck=False)
    renders = render_repair_set(soften_back_neck=True)
    validation = validate_hd_adapter_collection(renders)
    if validation["status"] != "PASS_STATIC_RUNTIME_NOT_TESTED":
        raise SystemExit(json.dumps(validation, indent=2))
    if not FARMER.exists() or not HAIR.exists():
        raise SystemExit("installed Farmer assets are required")
    body = read_rgba_png(FARMER)["pixels"]
    hair = read_rgba_png(HAIR)["pixels"]
    before_items = [{"render": render, "farmer": {d: _farmer_composite(body, hair, render.frames[d], d) for d in DIRECTIONS}} for render in before_renders]
    items = [{"render": render, "farmer": {d: _farmer_composite(body, hair, render.frames[d], d) for d in DIRECTIONS}} for render in renders]
    micro_validation = _validate_back_neck_micro_fix(before_renders, renders)
    if micro_validation["errors"]:
        raise SystemExit(json.dumps(micro_validation, indent=2))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    metric_by_grammar = {item["grammarId"]: item for item in validation["perGarment"]}
    for item in items:
        render = item["render"]
        target = OUT / _slug(render.recipe["grammarId"])
        target.mkdir(parents=True)
        write_rgba_png(target / "shirt.png", render.texture)
        write_rgba_png(target / "directions-8x.png", _isolated_single(item))
        write_rgba_png(target / "farmer-directions.png", _farmer_single(item))
        _json(target / "semantic-recipe.json", render.recipe)
        _json(target / "backend-recipe.json", render.backend_recipe)
        _json(target / "summary.json", {"backend": render.backend, "stageTrace": render.stage_trace, "polishMetrics": render.polish_metrics, "materialEvidence": render.material_evidence, "paletteRamps": render.palette_ramps, "quality": metric_by_grammar[render.recipe["grammarId"]], "runtime": "NOT_TESTED", "promotion": "EXPERIMENTAL"})

    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_HD_ADAPTER_DIRECTIONS.png", _isolated_collection(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_HD_ADAPTER_FARMER_DIRECTIONS.png", _farmer_collection(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_HD_ADAPTER_GAMEPLAY.png", _gameplay_fronts(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_HD_ADAPTER_OLD_VS_REPAIRED.png", _old_vs_repaired(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_BACK_NECK_BEFORE_AFTER.png", _back_neck_before_after(before_items, items))
    _json(OUT / "static-validation.json", validation)
    _json(OUT / "back-neck-micro-fix-validation.json", micro_validation)
    _package(items, validation)
    pack_validation = _validate_pack(items)
    _json(PACK / "pack-validation.json", pack_validation)
    if pack_validation["errors"]:
        raise SystemExit(json.dumps(pack_validation, indent=2))
    _write_report(items, validation, pack_validation)
    _write_back_neck_report(micro_validation)
    print("Generated exactly 3 HD-adapter repair specimens")
    print(validation["status"])
    print(pack_validation["status"])
    print(PACK)


if __name__ == "__main__":
    main()
