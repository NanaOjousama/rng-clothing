#!/usr/bin/env python3
"""Generate the single V5E Rare+ structured-field-jacket proof and test pack."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, text_width, write_rgba_png
from generator.renderers.fashionsense.structured_outerwear_v5e import render_fs_v5e
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.upper_v5b import _stack
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v2_recipe_engine import load_v2_data
from generator.v5d.engine import generate_v5d_batch
from generator.v5e import generate_v5e_recipe

OUT = ROOT / "output" / "fashionsense" / "v5e-rareplus-field-jacket"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5E-RarePlus-Field-Jacket"
UNIQUE_ID = "RNGClothing.FashionSense.V5ERarePlusFieldJacket"
DIRECTIONS = ("front", "right", "back", "left")
BG: RGBA = (235, 227, 216, 255)
PANEL: RGBA = (211, 203, 191, 255)
INK: RGBA = (45, 42, 39, 255)
BORDER: RGBA = (73, 66, 60, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _tile(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, PANEL)
    blit(canvas, sprite, x, y)


def _directions(title: str, frames, scale: int):
    size = 16 * scale; gap = 16; margin = 14; top = 42
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 14, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 6, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        draw_text(canvas, direction.upper(), x + max(0, (size - text_width(direction)) // 2), 23, color=INK)
        _tile(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _sleeve_directions(frames):
    width, height, gap, margin, top = 32, 64, 12, 14, 43
    canvas = blank_image(margin * 2 + width * 4 + gap * 3, top + height + 14, BG)
    draw_text(canvas, "GENERATED FULL LONG SLEEVES - FS IDLE SOURCE VIEWS", 7, 6, color=INK)
    draw_text(canvas, "COMPONENT DIAGNOSTIC - RUNTIME ASSEMBLY MUST BE TESTED IN GAME", 7, 19, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (width + gap)
        draw_text(canvas, direction.upper(), x, 32, color=INK)
        _tile(canvas, frames[direction], x, top)
    return canvas


def _before_after(old, new):
    scale = 8; size = 16 * scale; gap = 35; label = 150; top = 48
    canvas = blank_image(label + size * 2 + gap + 20, top + size + 20, BG)
    draw_text(canvas, "SUNFIELD DIRECTION - PREVIOUS V5D VS V5E RARE PLUS", 8, 7, color=INK)
    draw_text(canvas, "PREVIOUS", label, 27, color=INK)
    draw_text(canvas, "V5E", label + size + gap, 27, color=INK)
    draw_text(canvas, "ROLLED ARM", 8, top + 22, color=INK)
    draw_text(canvas, "FULL STRIPE", 8, top + 36, color=INK)
    draw_text(canvas, "LONG SLEEVES", 8, top + 74, color=INK)
    draw_text(canvas, "BOUNDED LAYER", 8, top + 88, color=INK)
    _tile(canvas, nearest_scale(old.default_frames["front"], scale), label, top)
    _tile(canvas, nearest_scale(new.default_frames["front"], scale), label + size + gap, top)
    return canvas


def _vanilla_frame(sprite_index: int):
    sheet_path = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/shirts.png")
    if not sheet_path.exists(): return None
    sheet = read_rgba_png(sheet_path)["pixels"]
    x0 = sprite_index * 8 % 128; y0 = sprite_index * 8 // 128 * 32
    base = [[sheet[y0 + y][x0 + x] for x in range(8)] for y in range(8)]
    mask = [[sheet[y0 + y][x0 + 128 + x] for x in range(8)] for y in range(8)]
    result = blank_image(8, 8)
    dye = (192, 150, 91)
    for y in range(8):
        for x in range(8):
            if base[y][x][3]: result[y][x] = base[y][x]
            if mask[y][x][3]: result[y][x] = tuple(mask[y][x][i] * dye[i] // 255 for i in range(3)) + (255,)
    return result


def _quality_baseline(render):
    references = [(18, "BROWN"), (231, "CANVAS"), (271, "SHORT")]
    scale = 4; tile = 32; gap = 34; top = 50
    canvas = blank_image(16 + tile * 4 + gap * 3 + 18, top + tile + 18, BG)
    draw_text(canvas, "EQUAL 32PX FOOTPRINT - VANILLA BASELINE VS V5E", 7, 7, color=INK)
    x = 16
    for sprite_index, name in references:
        draw_text(canvas, name, x, 29, color=INK)
        frame = _vanilla_frame(sprite_index)
        if frame is not None: _tile(canvas, nearest_scale(frame, scale), x, top)
        x += tile + gap
    draw_text(canvas, "V5E FIELD", x, 29, color=INK)
    _tile(canvas, nearest_scale(render.default_frames["front"], 2), x, top)
    return canvas


def _shirt_model(render, y: int):
    permanent = render.base.base.design.base
    palette = load_v2_data()["palettes"]["families"][permanent.recipe["paletteFamily"]]
    return {
        "Scale": 2.0, "HideSleeves": False, "DisableGrayscale": False,
        "ColorMaskLayers": [{"Name": "Primary Fabric", "DefaultColor": palette["defaultDye"], "Values": [[permanent.config["outerMaskRamp"][role]] * 3 for role in permanent.active_main_roles]}],
        "SleeveColors": [list(value) for value in render.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y}, "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(render):
    name = render.recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"]
    return {
        "Name": name, "Format": "7.5.0",
        "Tags": ["Lifestyle", "RNG Clothing", "V5E", "Rare", "Rare Plus", "Fieldwear", "Test"],
        "FrontShirt": _shirt_model(render, 0), "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32), "BackShirt": _shirt_model(render, 48),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack-only", action="store_true", help="rebuild only the installable V5E test pack")
    args = parser.parse_args()
    recipe = generate_v5e_recipe(); render = render_fs_v5e(recipe)
    polished = polish_upper_frames(render.base, render.frames, render.default_frames, article_family="STRUCTURED_FIELD_JACKET")
    export_texture = _stack(polished.frames)
    name = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"]
    description = recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemDescription"]
    if PACK.exists(): shutil.rmtree(PACK)
    if not args.pack_only:
        old_recipe = generate_v5d_batch()["recipes"][7]; old = render_fs_v5d(old_recipe)
        if OUT.exists(): shutil.rmtree(OUT)
        OUT.mkdir(parents=True); COMPARE.mkdir(parents=True, exist_ok=True)
        write_rgba_png(OUT / "shirt.png", export_texture)
        write_rgba_png(OUT / "shirt-8x.png", nearest_scale(export_texture, 8))
        write_rgba_png(OUT / "directions-8x.png", _directions(name + " - DIRECT LOGICAL PIXELS", polished.default_frames, 8))
        write_rgba_png(OUT / "gameplay-footprint.png", _directions(name + " - SCALE 2 GAMEPLAY FOOTPRINT", polished.default_frames, 2))
        write_rgba_png(COMPARE / "V5E_SUNFIELD_BEFORE_AFTER.png", _before_after(old, render))
        write_rgba_png(COMPARE / "V5E_RAREPLUS_FIELD_JACKET.png", _directions("V5E RARE PLUS FIELD JACKET - FRONT RIGHT BACK LEFT", polished.default_frames, 6))
        # Baseline helper expects a render-like object with default_frames.
        baseline_holder = type("PolishedBaseline", (), {"default_frames": polished.default_frames})()
        write_rgba_png(COMPARE / "V5E_VANILLA_FIELD_JACKET_BASELINE.png", _quality_baseline(baseline_holder))
        _json(OUT / "recipe.json", recipe)

    shirt_dir = PACK / "Shirts" / "SunfieldPathfinderJacket"
    shirt_dir.mkdir(parents=True)
    _json(shirt_dir / "shirt.json", _shirt_json(render)); write_rgba_png(shirt_dir / "shirt.png", export_texture)
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing V5E Rare+ Field Jacket", "Author": "RNG Clothing Experiment", "Version": "1.3.0",
        "Description": "Test-only single Rare+ structured field-jacket proof.", "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", [{
        "Name": "V5E - Sunfield Pathfinder Jacket", "Author": "RNG Clothing Experiment", "Version": 3,
        "AccessoryIds": ["None", "None", "None"], "HairId": "None", "HatId": "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{name}", "SleevesId": "None",
        "PantsId": "None", "ShoesId": "None", "BodyId": "None", "AppearanceToMaskColors": {},
    }])
    _json(PACK / "i18n" / "default.json", {"garment.v5e.name": name, "garment.v5e.description": description})
    (PACK / "README.md").write_text("""# V5E Rare+ Sunfield Pathfinder Jacket\n\nTest-only Fashion Sense 7.5.0 content pack. It is not installed automatically.\n\nCopy this entire folder into `Stardew Valley/Mods`, fully restart SMAPI, open the Fashion Sense Hand Mirror, choose **Outfits > Presets**, and equip **V5E - Sunfield Pathfinder Jacket**. Version 1.3 freezes the live-proven native arm contract: the Shirt supplies `SleeveColors`, while Stardew/Fashion Sense owns native animated arm attachment. The preset intentionally has `SleevesId: None`, and this pack intentionally contains no custom `Sleeves/` folder.\n\nVersion 1.3 changes shirt-layer art only: shell-fabric lapels, integrated back collar/undershirt, constructed side profile, jacket-fabric pockets, and a softer upper torso edge that visually joins the native long sleeves. Scale, BodyPosition, direction mapping, alpha geometry, and runtime fields remain unchanged.\n\nNo Hat, Accessory, Pants, Shoes, weather logic, or hair policy is used. Status: **NATIVE ARM CONTRACT FROZEN / ART RETEST REQUIRED**.\n""", encoding="utf-8")
    if not args.pack_only:
        summary = {
            "name": name, "description": description, "rarity": "Rare", "rendererTier": recipe["rendererTier"],
            "layers": ["Shirt", "Native animated sleeves via SleeveColors", "Preset"], "omittedLayers": ["Custom Sleeves", "Hat", "Accessory", "Pants", "Shoes"],
            "logicalShirt": [16, 16], "shirtScale": 2, "bodyPosition": [0, 32],
            "sleeveRuntimeContract": render.sleeve_metrics,
            "artPolish": polished.metrics,
            "directionOrder": ["front", "right", "left", "back"], "previewOrder": list(DIRECTIONS),
            "constructionFeatures": recipe["constructionFeatures"], "surfacePlan": recipe["surfacePlan"],
            "coverageMissing": {d: list(v) for d, v in render.coverage_missing.items()},
            "promotion": "EXPERIMENTAL", "runtime": "NATIVE_ARMS_PASS_ART_RETEST_REQUIRED",
            "qualityJudgment": "Art-only runtime polish strengthens shell-fabric lapels, shoulder-to-sleeve continuity, integrated back collar, constructed pockets, and side profile while preserving the frozen native arm contract.",
        }
        _json(OUT / "summary.json", summary)
    print(f"Generated one V5E Rare+ garment: {name}")
    print(OUT); print(PACK)


if __name__ == "__main__": main()
