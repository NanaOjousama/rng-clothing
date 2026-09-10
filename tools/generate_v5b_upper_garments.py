#!/usr/bin/env python3
"""Generate the V5B sleeve/upper-garment diagnostic batch and test pack."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png
from generator.renderers.fashionsense import render_fs_v5b
from generator.v2_recipe_engine import load_v2_data
from generator.v5b import diagnose_v5b_article, diagnose_v5b_collection, generate_v5b_benchmark


OUT = ROOT / "output" / "fashionsense" / "v5b-upper-garments"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5B-Upper-Garments"
UNIQUE_ID = "RNGClothing.FashionSense.V5BUpper"
PREVIEW_ORDER = ("front", "right", "back", "left")
BG: RGBA = (236, 226, 211, 255); TILE: RGBA = (216, 207, 193, 255)
INK: RGBA = (50, 47, 44, 255); BORDER: RGBA = (83, 76, 69, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


def _bordered(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, TILE)
    blit(canvas, sprite, x, y)


def _direction_sheet(title: str, frames, scale: int):
    size = 16 * scale; gap = 18; margin = 16; top = 42
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 15, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        x = margin + index * (size + gap)
        label = direction.upper(); draw_text(canvas, label, x + (size - text_width(label)) // 2, 24, color=INK)
        _bordered(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _collection_sheet(title: str, rendered, *, scale: int = 2):
    sprite = 16 * scale; label_w = 214; gap = 17; top = 53; row_h = sprite + 21
    canvas = blank_image(label_w + sprite * 4 + gap * 3 + 20, top + row_h * len(rendered) + 12, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "FRONT | RIGHT | BACK | LEFT - EXACT SHIRT FOOTPRINT", 8, 21, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (sprite + gap), 39, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h; design = recipe["baseArticleRecipe"]["designRecipe"]
        draw_text(canvas, f"{design['rarity'].upper()}  {recipe['articleType'].replace('_', ' ')}", 6, y + 1, color=INK)
        draw_text(canvas, design["itemName"][:30], 6, y + 13, color=INK)
        draw_text(canvas, recipe["sleeveIntent"].replace("_", " ")[:31], 6, y + 25, color=INK)
        for index, direction in enumerate(PREVIEW_ORDER):
            _bordered(canvas, nearest_scale(render.default_frames[direction], scale), label_w + index * (sprite + gap), y)
    return canvas


def _front_grid(title: str, rendered):
    scale = 8; sprite = 128; columns = 4; cell_w = 208; cell_h = 184
    rows = (len(rendered) + columns - 1) // columns
    canvas = blank_image(columns * cell_w, 34 + rows * cell_h, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for index, (recipe, render, _) in enumerate(rendered):
        x = (index % columns) * cell_w + 34; y = 34 + (index // columns) * cell_h + 39
        design = recipe["baseArticleRecipe"]["designRecipe"]
        draw_text(canvas, f"{design['rarity'].upper()} - {recipe['articleType'].replace('_', ' ')}", x - 24, y - 32, color=INK)
        draw_text(canvas, design["itemName"][:25], x - 24, y - 20, color=INK)
        draw_text(canvas, recipe["sleeveIntent"].replace("_", " ")[:25], x - 24, y - 8, color=INK)
        _bordered(canvas, nearest_scale(render.default_frames["front"], scale), x, y)
    return canvas


def _sleeve_sheet(title: str, rendered):
    frame_w, frame_h, scale = 32, 64, 1
    label_w = 220; gap = 10; top = 52; row_h = frame_h + 19
    canvas = blank_image(label_w + frame_w * 4 + gap * 3 + 20, top + row_h * len(rendered) + 10, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "TARGET LOGICAL CELLS; CUSTOM FRAMES ARE 32X64 AT SCALE 2", 8, 20, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER): draw_text(canvas, direction.upper(), label_w + index * (frame_w + gap), 39, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h; design = recipe["baseArticleRecipe"]["designRecipe"]
        draw_text(canvas, design["itemName"][:29], 6, y + 3, color=INK)
        draw_text(canvas, recipe["sleeveIntent"].replace("_", " ")[:29], 6, y + 16, color=INK)
        if render.sleeve_idle_frames:
            for index, direction in enumerate(PREVIEW_ORDER):
                _bordered(canvas, nearest_scale(render.sleeve_idle_frames[direction], scale), label_w + index * (frame_w + gap), y)
        else:
            label = "NATIVE" if recipe["sleeveIntent"] == "SHORT_SLEEVE" else "HIDDEN"
            for index in range(4): draw_text(canvas, label, label_w + index * (frame_w + gap), y + 28, color=INK)
    return canvas


def _shirt_model(render, y: int) -> dict[str, Any]:
    base = render.base.design.base
    palette = load_v2_data()["palettes"]["families"][base.recipe["paletteFamily"]]
    return {
        "Scale": 2.0, "HideSleeves": render.hide_native_sleeves, "DisableGrayscale": False,
        "ColorMaskLayers": [{"Name": "Primary Fabric", "DefaultColor": palette["defaultDye"],
            "Values": [[base.config["outerMaskRamp"][role]] * 3 for role in base.active_main_roles]}],
        "SleeveColors": [list(value) for value in render.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y}, "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe, render) -> dict[str, Any]:
    design = recipe["baseArticleRecipe"]["designRecipe"]
    tags = ["Lifestyle", "RNG Clothing", "Generator V5B", recipe["articleType"].replace("_", " ").title(), design["rarity"], design["styleProfile"], "Test"]
    return {
        "Name": design["itemName"], "Format": "7.5.0", "Tags": tags,
        "FrontShirt": _shirt_model(render, 0), "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32), "BackShirt": _shirt_model(render, 48),
    }


def _preset(recipe, render) -> dict[str, Any]:
    name = recipe["baseArticleRecipe"]["designRecipe"]["itemName"]
    shirt_id = f"{UNIQUE_ID}/Shirt/{name}"
    if render.companion_required:
        sleeves_id = f"{UNIQUE_ID}/Sleeves/{name} Sleeves"
    elif recipe["sleeveIntent"] == "SHORT_SLEEVE":
        sleeves_id = "PeacefulEnd.FashionSense.LocalPack/Sleeves/Default (Short)"
    else:
        sleeves_id = "None"
    return {
        "Name": f"V5B - {name}", "Author": "RNG Clothing Experiment", "Version": 3,
        "AccessoryIds": ["None", "None", "None"], "HairId": "None", "HatId": "None",
        "ShirtId": shirt_id, "SleevesId": sleeves_id, "PantsId": "None", "ShoesId": "None", "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _readme(rendered) -> str:
    rows = []
    for index, (recipe, render, _) in enumerate(rendered, 1):
        design = recipe["baseArticleRecipe"]["designRecipe"]
        pair = "paired custom Sleeves" if render.companion_required else "native short sleeves"
        rows.append(f"{index}. **{design['itemName']}** — {design['rarity']}; {recipe['articleType'].replace('_', ' ').title()}; {recipe['sleeveIntent'].replace('_', ' ').title()} ({pair})")
    return """# RNG Clothing V5B Upper-Garment Runtime Test

Test-only Fashion Sense content pack. It is not installed automatically and is not production-ready.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the entire `RNG-Clothing-V5B-Upper-Garments` folder into your Stardew Valley `Mods` folder, then fully restart SMAPI.

## Equip the coordinated pairs

1. Open the Fashion Sense Hand Mirror.
2. Open **Outfits** and switch to the **Preset** list.
3. Select the preset whose name starts with `V5B -`.

The preset equips the Shirt and its matching custom Sleeves appearance together. Presets also clear unrelated Fashion Sense appearance slots, so use them on a test save/outfit. You can instead select the matching entries manually under **Shirts** and **Sleeves**. Short-sleeve presets use Fashion Sense's built-in `Default (Short)` sleeves. The sleeveless waistcoat uses a generated skin-tone-masked animated arm companion and never sets `HideSleeves`.

## Garments

""" + "\n".join(rows) + """

## Required runtime checks

Test idle, walk, run, axe, pickaxe, watering can, fishing, sitting, horse, equip/unequip, recolor, and every direction. Custom fitted/rolled/layered sleeves remain `EXPERIMENTAL` until this manual test is completed.
"""


def main() -> None:
    batch = generate_v5b_benchmark(); renders = []; diagnostics = []
    for recipe in batch["recipes"]:
        render = render_fs_v5b(recipe); diagnostic = diagnose_v5b_article(render)
        if not diagnostic.passes: raise ValueError(f"{recipe['id']} failed: {'; '.join(diagnostic.errors)}")
        renders.append(render); diagnostics.append(diagnostic)
    collection = diagnose_v5b_collection(batch["recipes"], renders, diagnostics)
    if not collection.passes: raise ValueError("V5B collection failed: " + "; ".join(collection.errors))
    rendered = list(zip(batch["recipes"], renders, diagnostics))
    OUT.mkdir(parents=True, exist_ok=True); COMPARE.mkdir(parents=True, exist_ok=True); PACK.mkdir(parents=True, exist_ok=True)

    presets = []; localization = {}
    for recipe, render, diagnostic in rendered:
        design = recipe["baseArticleRecipe"]["designRecipe"]; name = design["itemName"]; slug = _slug(name)
        target = OUT / slug; target.mkdir(parents=True, exist_ok=True)
        write_rgba_png(target / "shirt.png", render.texture)
        write_rgba_png(target / "shirt-8x.png", nearest_scale(render.texture, 8))
        write_rgba_png(target / "directions-8x.png", _direction_sheet(name, render.default_frames, 8))
        write_rgba_png(target / "gameplay-footprint.png", _direction_sheet(name + " - SCALE 2", render.default_frames, 2))
        if render.sleeves_texture is not None:
            write_rgba_png(target / "sleeves.png", render.sleeves_texture)
            _json(target / "sleeves.json", render.sleeves_json)
            write_rgba_png(target / "sleeves-idle-directions.png", _sleeve_sheet(name + " - SLEEVES", [(recipe, render, diagnostic)]))
        _json(target / "summary.json", {
            "name": name, "rarity": design["rarity"], "articleType": recipe["articleType"],
            "constructionVariant": recipe["constructionVariant"], "sleeveIntent": recipe["sleeveIntent"],
            "shoulderIntent": recipe["shoulderIntent"], "necklineIntent": recipe["necklineIntent"],
            "collarIntent": recipe["collarIntent"], "layeringIntent": recipe["layeringIntent"],
            "openingIntent": recipe["openingIntent"], "surfaceTranslation": recipe["surfaceTranslation"],
            "themeFamily": design["themeFamily"], "styleProfile": design["styleProfile"],
            "promotion": "EXPERIMENTAL", "runtime": "NOT_TESTED", "recipe": recipe,
            "diagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics},
        })

        shirt_dir = PACK / "Shirts" / _folder(name); shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render)); write_rgba_png(shirt_dir / "shirt.png", render.texture)
        if render.companion_required:
            sleeves_dir = PACK / "Sleeves" / (_folder(name) + "Sleeves"); sleeves_dir.mkdir(parents=True, exist_ok=True)
            _json(sleeves_dir / "sleeves.json", render.sleeves_json); write_rgba_png(sleeves_dir / "sleeves.png", render.sleeves_texture)
        presets.append(_preset(recipe, render))
        localization[f"garment.{recipe['id']}.name"] = name
        localization[f"garment.{recipe['id']}.description"] = design["itemDescription"]

    _json(ROOT / "output" / "recipes" / "v5b_upper_garment_benchmark.json", batch)
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED", "runtimePromotion": "EXPERIMENTAL",
        "beautyClaim": "HUMAN_REVIEW_REQUIRED", "collection": {"passes": collection.passes, "errors": list(collection.errors), "warnings": list(collection.warnings), "metrics": collection.metrics},
        "garments": [{"id": r["id"], "name": r["baseArticleRecipe"]["designRecipe"]["itemName"], "passes": d.passes, "errors": list(d.errors), "warnings": list(d.warnings), "metrics": d.metrics} for r, d in zip(batch["recipes"], diagnostics)],
    })
    write_rgba_png(OUT / "V5B_GAMEPLAY_FOOTPRINT.png", _collection_sheet("V5B UPPER GARMENTS - GAMEPLAY FOOTPRINT", rendered, scale=2))
    write_rgba_png(OUT / "V5B_ARTICLE_COMPARISON_8X.png", _collection_sheet("V5B UPPER ARTICLE COMPARISON - 8X DIAGNOSTIC", rendered, scale=8))
    write_rgba_png(OUT / "V5B_SLEEVE_COMPARISON.png", _sleeve_sheet("V5B SEMANTIC SLEEVE COMPARISON", rendered))
    write_rgba_png(COMPARE / "V5B_UPPER_ARTICLE_FRONTS_8X.png", _front_grid("V5B UPPER-GARMENT FRONTS", rendered))

    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing V5B Upper Garments", "Author": "RNG Clothing Experiment", "Version": "1.0.0",
        "Description": "Test-only V5B semantic sleeve and upper-garment diagnostics.", "UniqueID": UNIQUE_ID, "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "i18n" / "default.json", localization)
    (PACK / "README.md").write_text(_readme(rendered), encoding="utf-8")
    print(f"Generated {len(rendered)} V5B upper garments ({sum(r.companion_required for r in renders)} custom sleeve companions)")
    print(OUT)
    print(PACK)


if __name__ == "__main__": main()
