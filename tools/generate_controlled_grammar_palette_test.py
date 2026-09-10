#!/usr/bin/env python3
"""Build the sealed twelve-garment grammar/palette implementation proof."""

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

from generator.controlled_test.engine import generate_controlled_test_recipes
from generator.controlled_test.validation import AXES, validate_collection
from generator.png_utils import (
    RGBA,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    read_rgba_png,
    write_rgba_png,
)
from generator.renderers.fashionsense.reference_grammar import render_controlled_garment


OUT = ROOT / "output" / "fashionsense" / "controlled-grammar-palette-test"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Controlled-Grammar-Palette-Test"
REPORT = ROOT / "reports" / "CONTROLLED_GRAMMAR_PALETTE_IMPLEMENTATION.md"
UNIQUE_ID = "RNGClothing.FashionSense.ControlledGrammarPaletteTest"
DIRECTIONS = ("front", "right", "back", "left")
ATLAS_DIRECTIONS = ("front", "right", "left", "back")
MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))

FARMER = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
HAIR = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/hairstyles.png")
BODY_FRAME = {"front": 0, "right": 6, "back": 12, "left": 6}
FEATURE_Y = {0: 1, 6: 1, 12: 0}

BG: RGBA = (232, 226, 217, 255)
PANEL: RGBA = (207, 199, 188, 255)
INK: RGBA = (39, 37, 36, 255)
BORDER: RGBA = (72, 65, 60, 255)
ACCENT: RGBA = (57, 117, 121, 255)
HAIR_TINT: RGBA = (112, 76, 52, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def _folder(value: str) -> str:
    return "".join(part.capitalize() for part in "".join(ch if ch.isalnum() else " " for ch in value).split())


def _crop(pixels, x: int, y: int, width: int, height: int):
    return [list(row[x : x + width]) for row in pixels[y : y + height]]


def _flip(pixels):
    return [list(reversed(row)) for row in pixels]


def _tint(pixels, tint: RGBA):
    return [[(p[0] * tint[0] // 255, p[1] * tint[1] // 255, p[2] * tint[2] // 255, p[3]) for p in row] for row in pixels]


def _farmer_body(body, direction: str):
    index = BODY_FRAME[direction]
    frame = _crop(body, index % 6 * 16, index // 6 * 32, 16, 32)
    return _flip(frame) if direction == "left" else frame


def _farmer_hair(hair, direction: str):
    y = 32 if direction in {"right", "left"} else 64 if direction == "back" else 0
    frame = _crop(hair, 0, y, 16, 32)
    if direction == "left":
        frame = _flip(frame)
    return _tint(frame, HAIR_TINT)


def _farmer_composite(body, hair, frame, direction: str):
    canvas = blank_image(64, 128)
    blit(canvas, nearest_scale(_farmer_body(body, direction), 4), 0, 0)
    blit(canvas, nearest_scale(frame, 2), 16, 56 + FEATURE_Y[BODY_FRAME[direction]] * 4)
    blit(canvas, nearest_scale(_farmer_hair(hair, direction), 4), 0, FEATURE_Y[BODY_FRAME[direction]] * 4 + (4 if direction == "back" else 0))
    return canvas


def _tile(canvas, sprite, x: int, y: int, border: RGBA = BORDER) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _isolated_sheet(items: list[dict[str, Any]]):
    card_w, card_h = 176, 98
    canvas = blank_image(card_w * 3 + 12, card_h * 4 + 34, BG)
    draw_text(canvas, "CONTROLLED GRAMMAR + PALETTE TEST | DIRECT LOGICAL PIXELS | 4X", 8, 7, color=INK)
    for index, item in enumerate(items):
        col, row = index % 3, index // 3
        x0, y0 = 8 + col * card_w, 31 + row * card_h
        draw_text(canvas, f"{index + 1:02d} {item['recipe']['grammarId']}", x0, y0, color=INK)
        draw_text(canvas, item["recipe"]["paletteStoryId"], x0, y0 + 10, color=ACCENT)
        for d_index, direction in enumerate(DIRECTIONS):
            x = x0 + d_index * 42
            draw_text(canvas, direction[0].upper(), x, y0 + 21, color=INK)
            _tile(canvas, nearest_scale(item["render"].frames[direction], 4), x, y0 + 30)
    return canvas


def _farmer_front_sheet(items: list[dict[str, Any]]):
    card_w = 76
    canvas = blank_image(card_w * 6 + 12, 2 * 166 + 37, BG)
    draw_text(canvas, "FARMER GAMEPLAY FOOTPRINT | STRUCTURE IS AUTHORITATIVE", 8, 7, color=INK)
    draw_text(canvas, "NATIVE FARMER ARMS / SLEEVES | STATIC IDLE COMPOSITE", 8, 18, color=ACCENT)
    for index, item in enumerate(items):
        col, row = index % 6, index // 6
        x, y = 8 + col * card_w, 38 + row * 166
        draw_text(canvas, f"{index + 1:02d} {item['recipe']['grammarId'][:10]}", x, y, color=INK)
        _tile(canvas, item["farmer"]["front"], x, y + 14, ACCENT)
        draw_text(canvas, item["recipe"]["paletteStoryId"][:11], x, y + 147, color=INK)
    return canvas


def _farmer_direction_sheet(items: list[dict[str, Any]]):
    card_w, card_h = 294, 161
    canvas = blank_image(card_w * 2 + 12, card_h * 6 + 34, BG)
    draw_text(canvas, "WORN DIRECTIONAL RECONSTRUCTION | FRONT RIGHT BACK LEFT", 8, 7, color=INK)
    for index, item in enumerate(items):
        col, row = index % 2, index // 2
        x0, y0 = 8 + col * card_w, 31 + row * card_h
        draw_text(canvas, f"{item['recipe']['grammarId']} | {item['recipe']['name']}", x0, y0, color=INK)
        for d_index, direction in enumerate(DIRECTIONS):
            x = x0 + d_index * 71
            draw_text(canvas, direction.upper(), x, y0 + 11, color=ACCENT)
            _tile(canvas, item["farmer"][direction], x, y0 + 26, ACCENT)
    return canvas


def _diversity_matrix(items: list[dict[str, Any]], validation: dict[str, Any]):
    labels = [item["recipe"]["grammarId"] for item in items]
    pair_map = {(p["left"], p["right"]): p for p in validation["pairwiseDiversity"]["pairs"]}
    cell, left, top = 27, 142, 91
    canvas = blank_image(left + cell * 12 + 14, top + cell * 12 + 18, BG)
    draw_text(canvas, "PAIRWISE STRUCTURAL DIVERSITY | SHARED AXES / 10", 8, 7, color=INK)
    draw_text(canvas, "FAIL >=7 OR SHARED SILHOUETTE+OPENING+LAYERING", 8, 18, color=ACCENT)
    for i, label in enumerate(labels):
        draw_text(canvas, f"{i + 1:02d} {label[:17]}", 5, top + i * cell + 8, color=INK)
        draw_text(canvas, str(i + 1), left + i * cell + 8, top - 12, color=INK)
    for row in range(12):
        for col in range(12):
            x, y = left + col * cell, top + row * cell
            draw_rect(canvas, x, y, cell - 2, cell - 2, PANEL)
            if row == col:
                draw_text(canvas, "--", x + 7, y + 8, color=BORDER)
            else:
                a, b = sorted((row, col))
                pair = pair_map[(labels[a], labels[b])]
                color = (157, 69, 61, 255) if pair["status"] == "FAIL" else ACCENT
                draw_text(canvas, str(pair["sharedCount"]), x + 10, y + 8, color=color)
    return canvas


def _shirt_json(item: dict[str, Any]) -> dict[str, Any]:
    render = item["render"]
    data: dict[str, Any] = {
        "Name": item["recipe"]["name"],
        "Format": "7.5.0",
        "Tags": ["RNG Clothing", "Controlled Grammar Test", item["recipe"]["grammarId"], item["recipe"]["materialId"]],
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


def _preset(item: dict[str, Any]) -> dict[str, Any]:
    name = item["recipe"]["name"]
    return {
        "Name": f"Grammar Proof {item['index']:02d} - {name}",
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


def _package(items: list[dict[str, Any]], validation: dict[str, Any]) -> None:
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    presets = []
    index = []
    for item in items:
        recipe, render = item["recipe"], item["render"]
        folder = _folder(recipe["name"])
        target = PACK / "Shirts" / folder
        target.mkdir(parents=True)
        write_rgba_png(target / "shirt.png", render.texture)
        _json(target / "shirt.json", _shirt_json(item))
        presets.append(_preset(item))
        index.append({
            "number": item["index"], "id": recipe["id"], "name": recipe["name"],
            "grammar": recipe["grammarId"], "material": recipe["materialId"],
            "palette": recipe["paletteStoryId"], "preset": f"Grammar Proof {item['index']:02d} - {recipe['name']}",
            "status": "EXPERIMENTAL", "runtime": "NOT_TESTED",
        })
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing Controlled Grammar Palette Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Twelve experimental grammar and palette specimens. No production appearances are replaced.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "specimen-index.json", index)
    _json(PACK / "static-validation.json", validation)
    (PACK / "README.md").write_text(
        "# Controlled Grammar + Palette Test\n\n"
        "Copy this entire folder into `Stardew Valley/Mods`, fully restart SMAPI, open the Fashion Sense Hand Mirror, then choose **Outfits > Presets**. "
        "The twelve presets are numbered `Grammar Proof 01` through `Grammar Proof 12`.\n\n"
        "Every specimen uses the safe Shirt contract: Scale 2, BodyPosition `(0,32)`, native Farmer animated arms, `HideSleeves: false`, and `SleevesId: None`. "
        "There is no custom Sleeves folder. Status: **EXPERIMENTAL / STATIC PASS / LIVE TEST REQUIRED**.\n",
        encoding="utf-8",
    )


def _validate_pack(items: list[dict[str, Any]]) -> dict[str, Any]:
    checks = []
    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    shirt_jsons = sorted((PACK / "Shirts").glob("*/shirt.json"))
    presets = json.loads((PACK / "preset_outfits.json").read_text(encoding="utf-8"))
    check("exactly twelve Shirt appearances", len(shirt_jsons) == 12, len(shirt_jsons))
    check("exactly twelve presets", len(presets) == 12, len(presets))
    check("custom Sleeves directory absent", not (PACK / "Sleeves").exists(), "native Farmer sleeves only")
    check("all presets use native sleeve path", all(p["SleevesId"] == "None" for p in presets), [p["SleevesId"] for p in presets])
    models = []
    for path in shirt_jsons:
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, y in MODELS:
            model = data[key]
            models.append(model)
            check(f"{path.parent.name}/{key} contract", model["Scale"] == 2.0 and model["BodyPosition"] == {"X": 0, "Y": 32} and model["StartingPosition"] == {"X": 0, "Y": y} and model["HideSleeves"] is False, model)
    check("all 48 directional models present", len(models) == 48, len(models))
    textures = sorted((PACK / "Shirts").glob("*/shirt.png"))
    dimensions = {str(p.relative_to(PACK)): [read_rgba_png(p)["width"], read_rgba_png(p)["height"]] for p in textures}
    check("all Shirt atlases are 16x64", len(textures) == 12 and all(value == [16, 64] for value in dimensions.values()), dimensions)
    hashes = {str(p.relative_to(PACK)): hashlib.sha256(p.read_bytes()).hexdigest() for p in textures}
    failed = [c["name"] for c in checks if not c["passed"]]
    return {"status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not failed else "FAIL_STATIC", "failed": failed, "checks": checks, "textureHashes": hashes, "runtime": "NOT_TESTED", "promotion": "EXPERIMENTAL"}


def _write_report(items: list[dict[str, Any]], validation: dict[str, Any], pack_validation: dict[str, Any]) -> None:
    rows = "\n".join(
        f"| {item['index']:02d} | {item['recipe']['name']} | `{item['recipe']['grammarId']}` | `{item['recipe']['materialId']}` | `{item['recipe']['paletteStoryId']}` | {item['humanReview']} |"
        for item in items
    )
    max_shared = validation["pairwiseDiversity"]["maximumSharedDimensions"]
    text = f"""# Controlled Grammar + Palette Implementation Test

Status: **{validation['status']}**. Runtime status: **NOT TESTED**. These twelve appearances remain **EXPERIMENTAL**.

## Shared implementation

This phase adds a bounded semantic recipe assembler, a direct-logical-pixel Fashion Sense renderer for only the approved twelve grammars, structural/directional validation, pairwise diversity validation, Farmer compositing, and an isolated test-pack exporter. It does not alter rarity or enable open-ended generation.

Every appearance uses the proven Fashion Sense 7.5 Shirt contract: 16×16 logical frames, Scale 2, BodyPosition `(0,32)`, native animated Farmer sleeves through three `SleeveColors`, `HideSleeves: false`, and no custom Sleeves atlas. The renderer first authors silhouette, collar, opening/layering, hem, and directional carriers, then resolves semantic palette roles and applies restrained material finishing.

## Specimens

| # | Garment | Grammar | Material | Palette story | Farmer-composite review |
|---:|---|---|---|---|---|
{rows}

## Structural separation

Neighboring garments do not use color as their primary distinction. The tee is a fitted closed single mass; the open shirt has two woven leaves and a broad inner tee; the cardigan has soft knit edges and pockets; the sweater vest uses bound armholes over native shirt sleeves; the waistcoat uses a tailored deep V, buttons, welt pockets, and shaped points. The sweatshirt is soft and boxy; the bomber is short and rounded with a gathered band; the work jacket is a firm box with large patch pockets and rear yoke; the blazer uses lapel masses, tailored waist, and rear vent. The wrap is diagonally overlapped, the sailor top is carried by its front/rear collar, and the tunic uses a belt, longer-looking upper-safe fall, and split termination.

The automatic 66-pair gate passed. Maximum shared semantic dimensions: **{max_shared}/10**. No pair shares seven dimensions, and no pair shares silhouette + opening + layering. Numeric checks are guardrails; the exported worn Farmer sheet was also reviewed at native gameplay scale.

## Runtime risk and limitations

No custom sleeve workaround was used. BELTED_TUNIC stays entirely inside the known-safe Shirt frame and implies length with belt/termination topology; it does not draw rigid geometry over moving legs. Static Farmer composites cannot prove walking, tools, sitting, horse, recolor UI, or multiplayer behavior. Side silhouettes are constrained by the same safe upper-body footprint, so runtime review should focus on whether soft/boxy/cropped/tailored differences survive animation.

No grammar was declared impossible in this bounded proof. The most constrained are BELTED_TUNIC (safe bounds limit apparent length) and OPEN_CARDIGAN (native arm geometry limits loose sleeve volume). Neither was expanded with an unsafe layer.

The closest worn comparisons are FITTED_TEE versus CREWNECK_SWEATSHIRT (both closed single-fabric tops, separated by fitted versus boxy mass and clean versus ribbed hem) and SWEATER_VEST versus FORMAL_WAISTCOAT (both layered sleeveless outer frames, separated by knit binding versus tailored opening, buttons, pockets, and shaped points). These are acceptable in the static Farmer sheet but deserve explicit live review. The matrix uses exact semantic-axis equality and therefore does not replace this visual judgment.

## Outputs

- Test pack: `{PACK}`
- Per-specimen assets and recipes: `{OUT}`
- Gameplay fronts: `{COMPARE / 'CONTROLLED_GRAMMAR_PALETTE_FARMER_FRONTS.png'}`
- Four-direction Farmer composites: `{COMPARE / 'CONTROLLED_GRAMMAR_PALETTE_FARMER_DIRECTIONS.png'}`
- Enlarged isolated art: `{COMPARE / 'CONTROLLED_GRAMMAR_PALETTE_ISOLATED_4X.png'}`
- Pairwise matrix: `{COMPARE / 'CONTROLLED_GRAMMAR_PALETTE_DIVERSITY_MATRIX.png'}`
- Validation: `{OUT / 'static-validation.json'}`
- Pack validation: `{PACK / 'static-validation.json'}`

## Live review

Install only the dedicated pack, then test each numbered preset front/right/back/left, walk, run, and use a tool. Confirm native arms remain attached, nothing appears near the feet, side/back carriers stay readable, and each article is identifiable without its preset name. No appearance should be promoted based on this static pass.
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")


def main() -> None:
    raise SystemExit(
        "DISABLED: reference_grammar is structure-debug-only and may not export final art. "
        "Use generate_controlled_grammar_hd_adapter_repair.py for the bounded repaired path."
    )
    recipes = generate_controlled_test_recipes()
    renders = [render_controlled_garment(recipe) for recipe in recipes]
    validation = validate_collection(recipes, renders)
    if validation["status"] != "PASS_STATIC_RUNTIME_NOT_TESTED":
        raise SystemExit(json.dumps(validation, indent=2))
    if not FARMER.exists() or not HAIR.exists():
        raise SystemExit("installed Farmer assets required for authoritative composites")
    body = read_rgba_png(FARMER)["pixels"]
    hair = read_rgba_png(HAIR)["pixels"]
    reviews = {
        "FITTED_TEE": "Clear fitted basic; quiet side/back are appropriate.",
        "OPEN_CASUAL_SHIRT": "Two leaves and broad inner tee survive front; side keeps one open edge.",
        "OPEN_CARDIGAN": "Soft open knit and pockets read; loose sleeve volume remains runtime-limited.",
        "SWEATER_VEST": "Bound armhole/V and inner shirt separate it from a plain knit.",
        "FORMAL_WAISTCOAT": "Deep formal V, button rhythm, welt cues, and pointed hem read distinctly.",
        "CREWNECK_SWEATSHIRT": "Boxy mass and ribbed terminations separate it from the fitted tee.",
        "CROPPED_BOMBER": "Rounded crop, shoulder block, zip, pocket cue, and gathered band read strongly.",
        "WORK_JACKET": "Firm box, large pockets, side pocket depth, and rear yoke read as workwear.",
        "FITTED_BLAZER": "Lapel hierarchy and tailored rear carrier read; side remains deliberately restrained.",
        "WRAP_TOP": "Diagonal overlap is geometry-first and survives front/right reconstruction.",
        "SAILOR_TOP": "Large rear collar is the strongest non-front carrier in the set.",
        "BELTED_TUNIC": "Belt and split fall read, but safe Shirt bounds limit apparent length.",
    }
    items = []
    for index, (recipe, render) in enumerate(zip(recipes, renders), 1):
        farmer = {direction: _farmer_composite(body, hair, render.frames[direction], direction) for direction in DIRECTIONS}
        items.append({"index": index, "recipe": recipe, "render": render, "farmer": farmer, "humanReview": reviews[recipe["grammarId"]]})

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    for item in items:
        recipe, render = item["recipe"], item["render"]
        target = OUT / f"{item['index']:02d}-{_slug(recipe['grammarId'])}"
        target.mkdir(parents=True)
        write_rgba_png(target / "shirt.png", render.texture)
        write_rgba_png(target / "isolated-directions-8x.png", _isolated_single(item))
        write_rgba_png(target / "farmer-directions.png", _farmer_single(item))
        _json(target / "semantic-recipe.json", recipe)
        _json(target / "render-summary.json", {"activeRoles": render.active_roles, "sleeveColors": render.sleeve_colors, "materialBehavior": render.material_behavior_id, "runtimeStatus": "NOT_TESTED"})

    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_PALETTE_ISOLATED_4X.png", _isolated_sheet(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_PALETTE_FARMER_FRONTS.png", _farmer_front_sheet(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_PALETTE_FARMER_DIRECTIONS.png", _farmer_direction_sheet(items))
    write_rgba_png(COMPARE / "CONTROLLED_GRAMMAR_PALETTE_DIVERSITY_MATRIX.png", _diversity_matrix(items, validation))
    _json(OUT / "recipes.json", recipes)
    _json(OUT / "static-validation.json", validation)
    _package(items, validation)
    pack_validation = _validate_pack(items)
    _json(PACK / "static-validation.json", {"collection": validation, "pack": pack_validation})
    if pack_validation["failed"]:
        raise SystemExit("pack validation failed: " + ", ".join(pack_validation["failed"]))
    _write_report(items, validation, pack_validation)
    print(f"Generated {len(items)} controlled specimens")
    print(validation["status"])
    print(pack_validation["status"])
    print(PACK)


def _isolated_single(item: dict[str, Any]):
    canvas = blank_image(4 * 128 + 24, 164, BG)
    draw_text(canvas, item["recipe"]["name"].upper(), 8, 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = 8 + index * 130
        draw_text(canvas, direction.upper(), x, 21, color=ACCENT)
        _tile(canvas, nearest_scale(item["render"].frames[direction], 8), x, 34, ACCENT)
    return canvas


def _farmer_single(item: dict[str, Any]):
    canvas = blank_image(4 * 70 + 16, 164, BG)
    draw_text(canvas, item["recipe"]["name"].upper(), 8, 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = 8 + index * 70
        draw_text(canvas, direction.upper(), x, 20, color=ACCENT)
        _tile(canvas, item["farmer"][direction], x, 34, ACCENT)
    return canvas


if __name__ == "__main__":
    main()
