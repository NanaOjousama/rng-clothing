#!/usr/bin/env python3
"""Generate the V5C2 vanilla-study and hoodie reconstruction diagnostics."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png
from generator.renderers.fashionsense.upper_v5b import render_fs_v5b
from generator.renderers.fashionsense.upper_v5c2 import render_fs_v5c2
from generator.v2_recipe_engine import load_v2_data
from generator.v5b import generate_v5b_benchmark
from generator.v5c2 import diagnose_v5c2_article, diagnose_v5c2_collection, generate_v5c2_batch


OUT = ROOT / "output" / "fashionsense" / "v5c2-vanilla-hoodie"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5C2-Vanilla-Hoodie"
UNIQUE_ID = "RNGClothing.FashionSense.V5C2VanillaHoodie"
PREVIEW_ORDER = ("front", "right", "back", "left")
BG: RGBA = (236, 226, 211, 255)
TILE: RGBA = (214, 205, 192, 255)
INK: RGBA = (46, 43, 40, 255)
BORDER: RGBA = (76, 69, 63, 255)
GROUP: RGBA = (194, 181, 164, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


def _design(recipe):
    return recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]


def _bordered(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, TILE)
    blit(canvas, sprite, x, y)


def _direction_sheet(title: str, frames, scale: int):
    size = 16 * scale
    gap = max(18, scale * 3)
    margin = 16
    top = 43
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 16, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        x = margin + index * (size + gap)
        label = direction.upper()
        draw_text(canvas, label, x + (size - text_width(label)) // 2, 25, color=INK)
        _bordered(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _collection_sheet(title: str, rendered, *, scale: int):
    sprite = 16 * scale
    label_w = 230
    gap = max(14, scale * 2)
    top = 57
    row_h = sprite + 27
    canvas = blank_image(label_w + sprite * 4 + gap * 3 + 20, top + row_h * len(rendered) + 12, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "DIRECT LOGICAL ART - FRONT | RIGHT | BACK | LEFT", 8, 21, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (sprite + gap), 42, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h
        design = _design(recipe)
        draw_text(canvas, f"{row + 1:02d} {design['rarity'].upper()}  {recipe['articleType'].replace('_', ' ')}", 6, y + 1, color=INK)
        draw_text(canvas, design["itemName"][:34], 6, y + 14, color=INK)
        draw_text(canvas, recipe["articleSubtype"].replace("_", " ")[:34], 6, y + 27, color=INK)
        for index, direction in enumerate(PREVIEW_ORDER):
            _bordered(canvas, nearest_scale(render.default_frames[direction], scale), label_w + index * (sprite + gap), y)
    return canvas


def _front_grid(title: str, rendered, *, scale: int = 8, columns: int = 5):
    sprite = 16 * scale
    cell_w = sprite + 76
    cell_h = sprite + 70
    rows = (len(rendered) + columns - 1) // columns
    canvas = blank_image(columns * cell_w, 33 + rows * cell_h, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for index, (recipe, render, _) in enumerate(rendered):
        column = index % columns
        row = index // columns
        x = column * cell_w + 36
        y = 33 + row * cell_h + 48
        design = _design(recipe)
        draw_text(canvas, f"{index + 1:02d} {design['rarity'].upper()}", x - 25, y - 37, color=INK)
        draw_text(canvas, recipe["articleType"].replace("_", " ")[:25], x - 25, y - 24, color=INK)
        draw_text(canvas, design["itemName"][:25], x - 25, y - 11, color=INK)
        _bordered(canvas, nearest_scale(render.default_frames["front"], scale), x, y)
    return canvas


def _hoodie_sheet(rendered):
    hoodies = [entry for entry in rendered if entry[0]["articleType"] == "HOODIE"]
    scale = 6
    sprite = 16 * scale
    cell_w = sprite + 48
    label_w = 170
    top = 58
    row_h = sprite + 22
    canvas = blank_image(label_w + 4 * cell_w + 16, top + len(hoodies) * row_h + 10, BG)
    draw_text(canvas, "V5C2 HOODIE FAMILY - FIVE STRUCTURAL SUBTYPES", 8, 8, color=INK)
    draw_text(canvas, "HOOD MASS, OPENING, POCKET, CROP AND FOCAL DESIGN ARE INDEPENDENT", 8, 21, color=INK)
    for i, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + i * cell_w, 43, color=INK)
    for row, (recipe, render, _) in enumerate(hoodies):
        y = top + row * row_h
        design = _design(recipe)
        draw_text(canvas, design["rarity"].upper(), 6, y + 2, color=INK)
        draw_text(canvas, recipe["articleSubtype"].replace("_", " ")[:25], 6, y + 15, color=INK)
        draw_text(canvas, design["itemName"][:25], 6, y + 28, color=INK)
        for i, direction in enumerate(PREVIEW_ORDER):
            _bordered(canvas, nearest_scale(render.default_frames[direction], scale), label_w + i * cell_w, y)
    return canvas


def _sleeve_sheet(rendered):
    """Show the exact standing source cells used by each animated companion."""
    frame_w, frame_h = 32, 64
    label_w = 230
    gap = 10
    top = 57
    row_h = frame_h + 20
    canvas = blank_image(label_w + frame_w * 4 + gap * 3 + 20, top + row_h * len(rendered) + 10, BG)
    draw_text(canvas, "V5C2 COORDINATED SLEEVES - STANDING SOURCE CELLS", 8, 7, color=INK)
    draw_text(canvas, "FULL MOTION ATLAS IS 384X1344; THESE ARE IDLE DIRECTION DIAGNOSTICS", 8, 21, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (frame_w + gap), 42, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h
        draw_text(canvas, _design(recipe)["itemName"][:33], 6, y + 3, color=INK)
        draw_text(canvas, recipe["sleeveIntent"].replace("_", " ")[:33], 6, y + 17, color=INK)
        for index, direction in enumerate(PREVIEW_ORDER):
            _bordered(canvas, render.sleeve_idle_frames[direction], label_w + index * (frame_w + gap), y)
    return canvas


def _improvement_sheet(rendered):
    old_recipes = generate_v5b_benchmark()["recipes"]
    old_by_name = {_design_from_v5b(r)["itemName"]: render_fs_v5b(r) for r in old_recipes}
    old_names = ["Duskline Waistcoat", "Ribbonstar Bow Blouse", "Mosslight Familiar Knit", "Rookwing Cropped Field Jacket", "Gilded Evening Blazer"]
    notes = ["ARMS + V OPENING", "YOKE + ATTACHED KNOT", "KNIT YOKE + RIBBING", "CROP + LAPELS + POCKETS", "OPENING + YOKE + HEM"]
    new_general = rendered[:5]
    scale = 6
    sprite = 16 * scale
    gap = 30
    label_w = 240
    top = 58
    row_h = sprite + 24
    canvas = blank_image(label_w + sprite * 2 + gap + 20, top + row_h * 5 + 10, BG)
    draw_text(canvas, "V5B PREVIOUS -> V5C2 REVISED", 8, 8, color=INK)
    draw_text(canvas, "OLD FRONT", label_w, 39, color=INK)
    draw_text(canvas, "REVISED FRONT", label_w + sprite + gap, 39, color=INK)
    for row, ((recipe, render, _), old_name, note) in enumerate(zip(new_general, old_names, notes)):
        y = top + row * row_h
        draw_text(canvas, recipe["articleType"].replace("_", " "), 6, y + 3, color=INK)
        draw_text(canvas, note, 6, y + 17, color=INK)
        draw_text(canvas, _design(recipe)["itemName"][:32], 6, y + 31, color=INK)
        _bordered(canvas, nearest_scale(old_by_name[old_name].default_frames["front"], scale), label_w, y)
        _bordered(canvas, nearest_scale(render.default_frames["front"], scale), label_w + sprite + gap, y)
    return canvas


def _design_from_v5b(recipe):
    return recipe["baseArticleRecipe"]["designRecipe"]


def _shirt_model(render, y: int) -> dict[str, Any]:
    base = render.base.base.design.base
    palette = load_v2_data()["palettes"]["families"][base.recipe["paletteFamily"]]
    return {
        "Scale": 2.0,
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Primary Fabric",
            "DefaultColor": palette["defaultDye"],
            "Values": [[base.config["outerMaskRamp"][role]] * 3 for role in base.active_main_roles],
        }],
        "SleeveColors": [list(value) for value in render.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe, render) -> dict[str, Any]:
    design = _design(recipe)
    tags = ["Lifestyle", "RNG Clothing", "Generator V5C2", recipe["articleType"].replace("_", " ").title(), design["rarity"], "Test"]
    return {
        "Name": design["itemName"],
        "Format": "7.5.0",
        "Tags": tags,
        "FrontShirt": _shirt_model(render, 0),
        "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32),
        "BackShirt": _shirt_model(render, 48),
    }


def _preset(recipe, render) -> dict[str, Any]:
    name = _design(recipe)["itemName"]
    return {
        "Name": f"V5C2 - {name}",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{name}",
        "SleevesId": f"{UNIQUE_ID}/Sleeves/{name} Sleeves",
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _readme(rendered) -> str:
    garments = []
    for index, (recipe, _, _) in enumerate(rendered, 1):
        design = _design(recipe)
        garments.append(f"{index}. **{design['itemName']}** — {design['rarity']}; {recipe['articleSubtype'].replace('_', ' ').title()}; {recipe['sleeveIntent'].replace('_', ' ').title()}")
    return """# RNG Clothing V5C2 Vanilla Study + Hoodie Reconstruction

Test-only Fashion Sense content pack. It is not installed automatically and is not production-ready.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the entire `RNG-Clothing-V5C2-Vanilla-Hoodie` folder into the Stardew Valley `Mods` folder, then fully restart SMAPI.

## Equip correctly

Open the Fashion Sense Hand Mirror, choose **Outfits**, switch to **Presets**, and select a preset beginning with `V5C2 -`. Each preset equips the coordinated Shirt and custom animated Sleeves appearance together. If equipped manually, choose entries with the same garment name in both **Shirts** and **Sleeves**.

The hood is intentionally hood-down and integrated into the Shirt appearance. Hood-up would require a separately generated Fashion Sense Hat companion and is outside this milestone.

## Garments

""" + "\n".join(garments) + """

## Runtime status

All ten appearances are `EXPERIMENTAL / NOT TESTED`. Static validation cannot prove walk, tool, sit, horse, or multiplayer behavior. The waistcoat no longer hides the arm layer; verify all directions and tool poses in-game.
"""


def main() -> None:
    batch = generate_v5c2_batch()
    renders = [render_fs_v5c2(recipe) for recipe in batch["recipes"]]
    diagnostics = [diagnose_v5c2_article(render) for render in renders]
    collection = diagnose_v5c2_collection(batch["recipes"], renders, diagnostics)
    if not collection.passes:
        raise ValueError("V5C2 collection failed: " + "; ".join(collection.errors))
    rendered = list(zip(batch["recipes"], renders, diagnostics))
    OUT.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    PACK.mkdir(parents=True, exist_ok=True)
    presets = []
    localization = {}
    for recipe, render, diagnostic in rendered:
        design = _design(recipe)
        name = design["itemName"]
        target = OUT / _slug(name)
        target.mkdir(parents=True, exist_ok=True)
        write_rgba_png(target / "shirt.png", render.texture)
        write_rgba_png(target / "shirt-8x.png", nearest_scale(render.texture, 8))
        write_rgba_png(target / "directions-8x.png", _direction_sheet(name, render.default_frames, 8))
        write_rgba_png(target / "gameplay-footprint.png", _direction_sheet(name + " - SCALE 2", render.default_frames, 2))
        write_rgba_png(target / "sleeves.png", render.sleeves_texture)
        _json(target / "sleeves.json", render.sleeves_json)
        write_rgba_png(target / "sleeves-idle-directions.png", _sleeve_sheet([(recipe, render, diagnostic)]))
        _json(target / "summary.json", {
            "name": name,
            "description": design["itemDescription"],
            "rarity": design["rarity"],
            "articleType": recipe["articleType"],
            "articleSubtype": recipe["articleSubtype"],
            "sleeveIntent": recipe["sleeveIntent"],
            "constructionFeatures": recipe["constructionFeatures"],
            "surfacePlan": recipe["surfacePlan"],
            "referenceInfluence": recipe["referenceInfluence"],
            "hoodIntent": recipe["hoodIntent"],
            "promotion": "EXPERIMENTAL",
            "runtime": "NOT_TESTED",
            "recipe": recipe,
            "diagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics},
        })
        shirt_dir = PACK / "Shirts" / _folder(name)
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)
        sleeves_dir = PACK / "Sleeves" / (_folder(name) + "Sleeves")
        sleeves_dir.mkdir(parents=True, exist_ok=True)
        _json(sleeves_dir / "sleeves.json", render.sleeves_json)
        write_rgba_png(sleeves_dir / "sleeves.png", render.sleeves_texture)
        presets.append(_preset(recipe, render))
        localization[f"garment.{recipe['id']}.name"] = name
        localization[f"garment.{recipe['id']}.description"] = design["itemDescription"]
    _json(ROOT / "output" / "recipes" / "v5c2_vanilla_hoodie_diagnostics.json", batch)
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED",
        "runtimePromotion": "EXPERIMENTAL",
        "beautyClaim": "HUMAN_REVIEW_REQUIRED",
        "collection": {"passes": collection.passes, "errors": list(collection.errors), "warnings": list(collection.warnings), "metrics": collection.metrics},
        "garments": [{"id": recipe["id"], "name": _design(recipe)["itemName"], "passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics} for recipe, diagnostic in zip(batch["recipes"], diagnostics)],
    })
    write_rgba_png(OUT / "V5C2_GAMEPLAY_FOOTPRINT.png", _collection_sheet("V5C2 GAMEPLAY-FOOTPRINT REVIEW", rendered, scale=2))
    write_rgba_png(OUT / "V5C2_ENLARGED_DIRECTIONS.png", _collection_sheet("V5C2 ENLARGED DIRECTION REVIEW", rendered, scale=6))
    write_rgba_png(OUT / "V5C2_ARTICLE_COMPARISON.png", _front_grid("V5C2 ARTICLE COMPARISON", rendered))
    write_rgba_png(OUT / "V5C2_HOODIE_COMPARISON.png", _hoodie_sheet(rendered))
    write_rgba_png(OUT / "V5C2_SLEEVE_COVERAGE_DIAGNOSTIC.png", _sleeve_sheet(rendered))
    write_rgba_png(COMPARE / "V5C2_FRONT_RIGHT_BACK_LEFT.png", _collection_sheet("V5C2 ORIENTATION: FRONT | RIGHT | BACK | LEFT", rendered, scale=4))
    write_rgba_png(COMPARE / "V5C2_PREVIOUS_VS_REVISED.png", _improvement_sheet(rendered))
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing V5C2 Vanilla Study and Hoodies",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Test-only V5C2 vanilla-informed upper garments and hoodie diagnostics.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "i18n" / "default.json", localization)
    (PACK / "README.md").write_text(_readme(rendered), encoding="utf-8")
    print(f"Generated {len(rendered)} V5C2 garments with {sum(r.companion_required for r in renders)} coordinated sleeve companions")
    print(OUT)
    print(PACK)


if __name__ == "__main__":
    main()
