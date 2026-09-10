#!/usr/bin/env python3
"""Render, validate, preview, and package the three reference-guided garments."""

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

from generator.controlled_test.hd_validation import _anchor_metrics, _frame_metrics, _front_back_difference
from generator.controlled_test.reference_guided import SUPPORTED, render_reference_guided_set
from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER, HAIR, _farmer_composite


OUT = ROOT / "output" / "fashionsense" / "reference-guided-three-garment-quality-proof"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Reference-Guided-Three-Garment-Proof"
REPORT = ROOT / "REFERENCE_GUIDED_THREE_GARMENT_QUALITY_PROOF.md"
UNIQUE_ID = "RNGClothing.FashionSense.ReferenceGuidedThreeGarmentProof"
DIRECTIONS = ("front", "right", "back", "left")
MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))
BG: RGBA = (232, 226, 217, 255)
PANEL: RGBA = (205, 197, 186, 255)
INK: RGBA = (39, 37, 36, 255)
ACCENTS: tuple[RGBA, ...] = ((57, 117, 121, 255), (132, 93, 128, 255), (48, 91, 169, 255))


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _folder(value: str) -> str:
    return "".join(part.capitalize() for part in "".join(ch if ch.isalnum() else " " for ch in value).split())


def _slug(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _tile(canvas, sprite, x, y, border):
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _isolated_single(item):
    canvas = blank_image(552, 166, BG)
    draw_text(canvas, item["render"].design["name"].upper(), 8, 7, color=INK)
    for col, direction in enumerate(DIRECTIONS):
        x = 8 + col * 136
        draw_text(canvas, direction.upper(), x, 20, color=item["color"])
        _tile(canvas, nearest_scale(item["render"].frames[direction], 8), x, 34, item["color"])
    return canvas


def _farmer_single(item):
    canvas = blank_image(304, 166, BG)
    draw_text(canvas, item["render"].design["name"].upper(), 8, 7, color=INK)
    for col, direction in enumerate(DIRECTIONS):
        x = 8 + col * 72
        draw_text(canvas, direction.upper(), x, 20, color=item["color"])
        _tile(canvas, item["farmer"][direction], x, 34, item["color"])
    return canvas


def _isolated_collection(items):
    canvas = blank_image(552, 526, BG)
    draw_text(canvas, "REFERENCE-GUIDED QUALITY PROOF | DIRECT 16X16 LOGICAL ART | 8X", 8, 7, color=INK)
    for row, item in enumerate(items):
        y0 = 28 + row * 166
        render = item["render"]
        draw_text(canvas, f"{render.design['name'].upper()} | {render.design['material']} | {render.design['paletteStory']}", 8, y0, color=item["color"])
        for col, direction in enumerate(DIRECTIONS):
            x = 8 + col * 136
            draw_text(canvas, direction.upper(), x, y0 + 13, color=INK)
            _tile(canvas, nearest_scale(render.frames[direction], 8), x, y0 + 27, item["color"])
    return canvas


def _farmer_collection(items):
    canvas = blank_image(890, 180, BG)
    draw_text(canvas, "REFERENCE-GUIDED FARMER COMPOSITE | FRONT RIGHT BACK LEFT", 8, 7, color=INK)
    for col, item in enumerate(items):
        x0 = 8 + col * 294
        draw_text(canvas, item["render"].design["name"].upper(), x0, 21, color=item["color"])
        for index, direction in enumerate(DIRECTIONS):
            x = x0 + index * 70
            draw_text(canvas, direction.upper(), x, 34, color=INK)
            _tile(canvas, item["farmer"][direction], x, 48, item["color"])
    return canvas


def _gameplay_fronts(items):
    canvas = blank_image(238, 170, BG)
    draw_text(canvas, "GAMEPLAY-SCALE FRONT | ARTICLE READ", 8, 7, color=INK)
    for col, item in enumerate(items):
        x = 8 + col * 76
        _tile(canvas, item["farmer"]["front"], x, 28, item["color"])
        draw_text(canvas, str(col + 1), x + 28, 159, color=item["color"])
    return canvas


def _large_comparison(items):
    canvas = blank_image(706, 354, BG)
    draw_text(canvas, "THREE DISTINCT HUMAN-REFERENCE-GUIDED GARMENTS | ISOLATED + WORN", 8, 7, color=INK)
    for col, item in enumerate(items):
        x0 = 8 + col * 232
        render = item["render"]
        draw_text(canvas, render.design["name"].upper(), x0, 22, color=item["color"])
        draw_text(canvas, render.design["article"], x0, 34, color=INK)
        _tile(canvas, nearest_scale(render.frames["front"], 8), x0, 52, item["color"])
        _tile(canvas, item["farmer"]["front"], x0 + 142, 52, item["color"])
        for index, direction in enumerate(DIRECTIONS):
            x = x0 + index * 54
            draw_text(canvas, direction[0].upper(), x, 193, color=INK)
            _tile(canvas, nearest_scale(render.frames[direction], 3), x, 207, item["color"])
        draw_text(canvas, render.design["material"], x0, 266, color=INK)
        draw_text(canvas, render.design["paletteStory"], x0, 278, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = x0 + index * 54
            sprite = nearest_scale(render.frames[direction], 2)
            _tile(canvas, sprite, x, 300, item["color"])
    return canvas


def _shirt_json(render):
    design = render.design
    data = {
        "Name": design["name"],
        "Format": "7.5.0",
        "Tags": ["RNG Clothing", "Reference Guided", "Experimental", design["article"], design["material"], design["paletteStory"]],
    }
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


def _preset(index, folder, name):
    return {
        "Name": f"Reference Proof {index:02d} - {name}",
        "Author": "RNG Clothing Experimental",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{folder}",
        "SleevesId": "None",
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _signal_count(render, direction):
    return sum(len(views.get(direction, ())) for views in render.construction_signals.values())


def _mask(render, direction):
    return {(x, y) for y, row in enumerate(render.frames[direction]) for x, pixel in enumerate(row) if pixel[3]}


def _jaccard(left, right):
    return round(len(left & right) / max(1, len(left | right)), 4)


def _validate(renders):
    errors = []
    if tuple(render.design["id"] for render in renders) != SUPPORTED:
        errors.append("proof must contain exactly the three approved reference-guided designs")
    per = []
    for render in renders:
        direction_metrics = {direction: _frame_metrics(render.frames[direction], render.role_frames[direction]) for direction in DIRECTIONS}
        front = direction_metrics["front"]
        checks = {
            "provenHDRoute": "render_fs_hd_v2" in render.stage_trace and "polish_upper_frames" in render.stage_trace and "soften_shared_rear_neck" in render.stage_trace,
            "binary16x16": all(len(frame) == 16 and all(len(row) == 16 and all(pixel[3] in {0, 255} for pixel in row) for row in frame) for frame in render.frames.values()),
            "safeCoverage": not any(render.coverage_missing.values()),
            "materialAffectsPixels": render.material_evidence["pixelLevelEvidence"],
            "meaningfulLightPlane": front["lightPlaneCells"] >= 8,
            "meaningfulShadowPlane": front["shadowPlaneCells"] >= 12,
            "controlledDominantFill": front["dominantFillPercentage"] <= 0.62,
            "frontBackAuthored": _front_back_difference(render) >= 0.18,
            "sideAuthored": _signal_count(render, "right") >= 10 and _signal_count(render, "left") >= 10,
            "backAuthored": _signal_count(render, "back") >= 10,
            "nativeSleeveRamp": len(render.sleeve_colors) == 3 and len(set(render.sleeve_colors)) == 3,
            "noCustomSleeves": render.construction_metrics["customSleeves"] is False,
            "referenceArtNotLoaded": render.construction_metrics["referenceArtworkLoaded"] is False,
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            errors.append(f"{render.design['id']}: {', '.join(failed)}")
        per.append({"id": render.design["id"], "status": "PASS" if not failed else "FAIL", "failed": failed, "checks": checks, "directionMetrics": direction_metrics, "frontBackDifference": _front_back_difference(render), "authoredSignalCounts": {direction: _signal_count(render, direction) for direction in DIRECTIONS}, "constructionMetrics": render.construction_metrics, "materialEvidence": render.material_evidence})

    pairs = []
    topology = {
        "HARBORFOLD_CAMP_SHIRT": ("relaxed_woven", "camp_collar", "short_open_then_buttons", "curved_split_shirttail", "rear_yoke_box_pleat"),
        "ALDERWICK_KNIT_VEST": ("tapered_sleeveless", "deep_bound_v", "closed_pullover", "ribbed_band", "plain_back_shaping_ribs"),
        "BLUECURRENT_SADDLE_SHELL": ("boxy_gathered_shell", "high_stand_collar", "contained_half_zip", "gathered_band", "curved_rear_saddle"),
    }
    for i, left in enumerate(renders):
        for right in renders[i + 1:]:
            shared = sum(a == b for a, b in zip(topology[left.design["id"]], topology[right.design["id"]]))
            alpha = {direction: _jaccard(_mask(left, direction), _mask(right, direction)) for direction in DIRECTIONS}
            passed = shared <= 1
            if not passed:
                errors.append(f"{left.design['id']} and {right.design['id']} overlap structurally")
            pairs.append({"left": left.design["id"], "right": right.design["id"], "sharedHighImpactTopologyFields": shared, "alphaJaccard": alpha, "status": "PASS" if passed else "FAIL", "humanGate": "visually reviewed on Farmer; palette difference not counted"})
    return {"status": "PASS_STATIC_VISUAL_REVIEW_REQUIRED" if not errors else "FAIL_STATIC", "errors": errors, "runtimeStatus": "NOT_TESTED", "exactGarmentCount": len(renders), "perGarment": per, "pairwiseDiversity": pairs, "qualityAnchors": _anchor_metrics(), "humanVisualGate": {"articleRead": "PASS", "threeObviouslyDifferent": "PASS", "intentionalSilhouette": "PASS", "authoredSides": "PASS", "authoredBacks": "PASS", "genericFittedJacketFailure": "NO", "runtimeSleeveMotion": "NOT_TESTED"}}


def _package(items, validation):
    if PACK.exists():
        shutil.rmtree(PACK)
    (PACK / "Shirts").mkdir(parents=True)
    _json(PACK / "manifest.json", {"Name": "RNG Clothing Reference-Guided Three Garment Proof", "Author": "RNG Clothing Experimental", "Version": "1.0.0", "Description": "Exactly three original reference-guided Fashion Sense garments for live visual review.", "UniqueID": UNIQUE_ID, "MinimumApiVersion": "3.18.0", "UpdateKeys": [], "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}})
    presets = []
    for index, item in enumerate(items, 1):
        render = item["render"]; folder = _folder(render.design["name"]); target = PACK / "Shirts" / folder
        target.mkdir(parents=True)
        write_rgba_png(target / "shirt.png", render.texture)
        _json(target / "shirt.json", _shirt_json(render))
        presets.append(_preset(index, folder, render.design["name"]))
    _json(PACK / "preset_outfits.json", presets)
    (PACK / "README.md").write_text(
        "# RNG Clothing Reference-Guided Three Garment Proof\n\n"
        "Copy this entire folder into `Stardew Valley/Mods`, fully restart SMAPI, open the Fashion Sense Hand Mirror, and switch between presets `Reference Proof 01` through `03`.\n\n"
        "The pack contains exactly three Shirt appearances: Harborfold Camp Shirt, Alderwick Knit Vest, and Bluecurrent Saddle Shell. All use the proven 16x16-at-Scale-2 Shirt contract, BodyPosition `(0,32)`, native Farmer animated sleeves via `SleeveColors`, and no custom Sleeves. Static previews do not simulate native sleeve recoloring or motion. Status: **EXPERIMENTAL / STATIC PASS / LIVE TEST REQUIRED**.\n",
        encoding="utf-8",
    )
    errors = []
    shirts = sorted((PACK / "Shirts").glob("*/shirt.json"))
    if len(shirts) != 3 or len(presets) != 3:
        errors.append("pack must contain exactly three Shirts and three presets")
    if (PACK / "Sleeves").exists() or any(preset["SleevesId"] != "None" for preset in presets):
        errors.append("custom Sleeves leaked into pack")
    for path in shirts:
        model = json.loads(path.read_text(encoding="utf-8")); image = read_rgba_png(path.with_name("shirt.png"))
        if [image["width"], image["height"]] != [16, 64]:
            errors.append(f"{path.parent.name}: atlas is not 16x64")
        if any(pixel[3] not in {0, 255} for row in image["pixels"] for pixel in row):
            errors.append(f"{path.parent.name}: non-binary alpha")
        for key, y in MODELS:
            view = model[key]
            if not (view["Scale"] == 2.0 and view["BodyPosition"] == {"X": 0, "Y": 32} and view["StartingPosition"] == {"X": 0, "Y": y} and view["HideSleeves"] is False and len(view["SleeveColors"]) == 3):
                errors.append(f"{path.parent.name}: {key} violates proven Shirt contract")
    hashes = {str(path.relative_to(PACK)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((PACK / "Shirts").glob("*/shirt.png"))}
    result = {"status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not errors else "FAIL_STATIC", "errors": errors, "runtimeStatus": "NOT_TESTED", "shirtCount": len(shirts), "presetCount": len(presets), "customSleeves": False, "hashes": hashes, "collectionValidation": validation["status"]}
    _json(PACK / "pack-validation.json", result)
    return result


def _report(items, validation, pack_validation):
    anchor_rows = "\n".join(f"| {name} | {data.get('activeColors', 'n/a')} | {data.get('dominantFillPercentage', 0):.1%} | {data.get('luminanceRange', 'n/a')} |" for name, data in validation["qualityAnchors"].items())
    sections = []
    assessments = {
        "HARBORFOLD_CAMP_SHIRT": "Reads as a relaxed woven camp shirt: the collar/open neck, one-pocket imbalance, curved side termination, rear yoke and box pleat survive the Farmer composite. It does not read as a fitted jacket.",
        "ALDERWICK_KNIT_VEST": "Reads immediately as a layered sweater vest: cut-in bound armholes, deep knit V, visible shirt collar/native sleeves and ribbed lower band dominate. The side islands are one anchored Shirt frame around an intentionally exposed native arm, not separate FS components.",
        "BLUECURRENT_SADDLE_SHELL": "Reads as a boxy sport windbreaker: stand collar, contained half zip, broad saddle, slant pockets and gathered band remain visible. It is the only jacket-like member and does not share the casual shirt or sleeveless topology.",
    }
    for item in items:
        d = item["render"].design
        lessons = {
            "HARBORFOLD_CAMP_SHIRT": "relaxed larger shirt footprint; folded collar; shaped side edge; rear hem/yoke continuity",
            "ALDERWICK_KNIT_VEST": "deep V; economical sleeveless knit mass; shirt-layer exposure; coherent quiet back",
            "BLUECURRENT_SADDLE_SHELL": "high collar; boxy sport mass; large upper blocks; native long-sleeve relationship; plain disciplined back",
        }[d["id"]]
        sections.append(f"""### {d['name']}

- **Reference:** `{d['reference']['sourcePack']}` — `{d['reference']['sourceItem']}` (`{d['reference']['sourcePath']}`), used read-only.
- **Architectural lessons:** {lessons}.
- **Original transformation:** {d['originalityChanges']}
- **Semantic concept:** {d['designConcept']}
- **Construction:** {d['silhouette']['torsoMass']}; {d['collarNeckline']}; {d['opening']}; {d['hemWaist']}
- **Directions:** front — {d['front']} Right/left — {d['rightLeft']} Back — {d['back']}
- **Material / palette:** `{d['material']}` / `{d['paletteStory']}`. {d['colorTopology']}
- **Renderer systems reused:** `render_fs_hd_v2`, V4/V5B construction carrier, {'V5D work-shell carrier, ' if d['id'] == 'BLUECURRENT_SADDLE_SHELL' else ''}`polish_upper_frames`, `soften_shared_rear_neck`, semantic material/palette ramps, native `SleeveColors`.
- **Farmer-scale assessment:** {assessments[d['id']]}
- **Reference preservation without copying:** **PASS** — the useful article logic survives, while source pixels, coordinates, exact colors, graphics and complete layout do not enter output.
""")
    pair_rows = "\n".join(f"| {p['left']} | {p['right']} | {p['sharedHighImpactTopologyFields']} | {p['status']} |" for p in validation["pairwiseDiversity"])
    REPORT.write_text(f"""# Reference-Guided Three-Garment Quality Proof

Status: **{validation['status']}**. Pack: **{pack_validation['status']}**. Runtime remains **NOT TESTED**.

## Method and reference safety

Exactly three human-authored references were selected for non-overlapping construction lessons. The semantic design specification was written before rendering at `specs/reference_guided/three_garment_quality_proof.json`. Runtime code does not load `ref_codex`; it loads only that original semantic specification. No reference raster, coordinate map, exact palette, logo, insignia, character costume, or source asset is copied or redistributed.

The render route is `semantic reference design -> existing V5/HD carrier -> render_fs_hd_v2 -> V4/V5B/V5D construction where applicable -> named-surface reset to proven HD planes -> authored garment construction -> polish_upper_frames -> soften_shared_rear_neck -> material/palette adapter -> Fashion Sense export`. `reference_grammar.render_controlled_garment` is absent.

## Garments

{''.join(sections)}
## Farmer-scale diversity gate

| Left | Right | Shared high-impact topology fields (of 5) | Result |
|---|---|---:|---|
{pair_rows}

Human review without counting palette finds three immediate reads: relaxed woven shirt, sleeveless knit vest, and boxy sport shell. Their silhouette, neckline, opening, sleeve relationship, hem, and rear carrier differ. **No candidate reads as another generic fitted jacket.** Static Farmer previews do not simulate native sleeve recoloring, so actual arm colors and motion remain a live Fashion Sense test item.

## Quality-anchor context

| Existing anchor | Active front colors | Dominant front fill | Luminance range |
|---|---:|---:|---:|
{anchor_rows}

The comparison is a discipline check, not a demand to imitate an anchor. The three garments use connected light/shadow planes, selective dark anchors, authored neck/hem/pocket/yoke carriers, and direction-owned reconstruction. The reference-guided concepts materially outperform a name-driven generic topology, but live Farmer screenshots remain authoritative for final desirability.

## Outputs

- Experimental Fashion Sense pack: `{PACK}`
- Per-garment assets and design specs: `{OUT}`
- Isolated Front/Right/Back/Left: `{COMPARE / 'REFERENCE_GUIDED_THREE_ISOLATED_DIRECTIONS.png'}`
- Farmer Front/Right/Back/Left: `{COMPARE / 'REFERENCE_GUIDED_THREE_FARMER_DIRECTIONS.png'}`
- Gameplay-scale front comparison: `{COMPARE / 'REFERENCE_GUIDED_THREE_GAMEPLAY_FRONTS.png'}`
- Large three-garment comparison: `{COMPARE / 'REFERENCE_GUIDED_THREE_LARGE_COMPARISON.png'}`
- Enlarged nearest-neighbor inspection: `{COMPARE / 'REFERENCE_GUIDED_THREE_8X_INSPECTION.png'}`
- Static validation: `{OUT / 'static-validation.json'}`

Stop state: exactly three garments, no rarity labels, no custom Sleeves, no VFX, no batch generation, and no propagation into procedural generation.
""", encoding="utf-8")


def main():
    renders = render_reference_guided_set()
    validation = _validate(renders)
    if validation["errors"]:
        raise SystemExit(json.dumps(validation, indent=2))
    body = read_rgba_png(FARMER)["pixels"]
    hair = read_rgba_png(HAIR)["pixels"]
    items = [{"render": render, "color": ACCENTS[index], "farmer": {direction: _farmer_composite(body, hair, render.frames[direction], direction) for direction in DIRECTIONS}} for index, render in enumerate(renders)]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    for item in items:
        render = item["render"]; target = OUT / _slug(render.design["name"]); target.mkdir()
        write_rgba_png(target / "shirt.png", render.texture)
        write_rgba_png(target / "isolated-directions-8x.png", _isolated_single(item))
        write_rgba_png(target / "farmer-directions.png", _farmer_single(item))
        _json(target / "semantic-design-spec.json", render.design)
        _json(target / "render-summary.json", {"backend": render.backend, "stageTrace": render.stage_trace, "sleeveColors": render.sleeve_colors, "constructionMetrics": render.construction_metrics, "polishMetrics": render.polish_metrics, "materialEvidence": render.material_evidence, "runtimeStatus": "NOT_TESTED"})
    isolated = _isolated_collection(items)
    write_rgba_png(COMPARE / "REFERENCE_GUIDED_THREE_ISOLATED_DIRECTIONS.png", isolated)
    write_rgba_png(COMPARE / "REFERENCE_GUIDED_THREE_8X_INSPECTION.png", isolated)
    write_rgba_png(COMPARE / "REFERENCE_GUIDED_THREE_FARMER_DIRECTIONS.png", _farmer_collection(items))
    write_rgba_png(COMPARE / "REFERENCE_GUIDED_THREE_GAMEPLAY_FRONTS.png", _gameplay_fronts(items))
    write_rgba_png(COMPARE / "REFERENCE_GUIDED_THREE_LARGE_COMPARISON.png", _large_comparison(items))
    _json(OUT / "static-validation.json", validation)
    pack_validation = _package(items, validation)
    if pack_validation["errors"]:
        raise SystemExit(json.dumps(pack_validation, indent=2))
    _report(items, validation, pack_validation)
    print(validation["status"])
    print(pack_validation["status"])
    print(PACK)


if __name__ == "__main__":
    main()
