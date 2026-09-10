#!/usr/bin/env python3
"""Generate the six-layer hoodie architecture correction batch."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hoodie_layers import generate_hoodie_layer_batch
from generator.png_utils import (
    RGBA,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    text_width,
    write_rgba_png,
)
from generator.renderers.fashionsense.hoodie_layers import FSHoodieLayerRender, render_fs_hoodie_layers
from generator.v2_recipe_engine import load_v2_data


OUT = ROOT / "output" / "fashionsense" / "hoodie-layer-correction"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Hoodie-Layer-Correction"
UNIQUE_ID = "RNGClothing.FashionSense.HoodieLayerCorrection"
PREVIEW_ORDER = ("front", "right", "back", "left")
BG: RGBA = (238, 228, 207, 255)
TILE: RGBA = (77, 69, 67, 255)
BORDER: RGBA = (45, 39, 39, 255)
INK: RGBA = (52, 43, 40, 255)
MUTED: RGBA = (112, 88, 75, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


def _bordered(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, TILE)
    blit(canvas, sprite, x, y)


def _shirt_mask_layer(render: FSHoodieLayerRender) -> dict[str, Any]:
    permanent = render.upper.base.base.design.base
    palette = load_v2_data()["palettes"]["families"][permanent.recipe["paletteFamily"]]
    return {
        "Name": "Primary Hoodie Fabric",
        "DefaultColor": palette["defaultDye"],
        "Values": [
            [permanent.config["outerMaskRamp"][role]] * 3
            for role in permanent.active_main_roles
        ],
    }


def _shirt_model(render: FSHoodieLayerRender, y: int) -> dict[str, Any]:
    return {
        "Scale": 2.0,
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [_shirt_mask_layer(render)],
        "SleeveColors": [list(value) for value in render.upper.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe: dict[str, Any], render: FSHoodieLayerRender) -> dict[str, Any]:
    tags = ["Lifestyle", "RNG Clothing", "Hoodie", recipe["hoodieSubtype"].replace("_", " ").title(), recipe["rarity"], "Test"]
    return {
        "Name": recipe["itemName"],
        "Format": "7.5.0",
        "Tags": tags,
        "FrontShirt": _shirt_model(render, 0),
        "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32),
        "BackShirt": _shirt_model(render, 48),
    }


def _preset(recipe: dict[str, Any]) -> dict[str, Any]:
    name = recipe["itemName"]
    return {
        "Name": f"Hoodie Layers - {name}",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": f"{UNIQUE_ID}/Hat/{name} Hood",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{name}",
        "SleevesId": "None",
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _isolated_sheet(title: str, render: FSHoodieLayerRender, scale: int) -> list[list[RGBA]]:
    size = 16 * scale
    gap = max(18, scale * 3)
    margin = 16
    top = 48
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 18, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    draw_text(canvas, "ISOLATED SHIRT SHELL", max(4, (len(canvas[0]) - text_width("ISOLATED SHIRT SHELL")) // 2), 20, color=MUTED)
    for index, direction in enumerate(PREVIEW_ORDER):
        x = margin + index * (size + gap)
        draw_text(canvas, direction.upper(), x + (size - text_width(direction.upper())) // 2, 34, color=INK)
        _bordered(canvas, nearest_scale(render.shirt_default_frames[direction], scale), x, top)
    return canvas


def _assembled_frame(render: FSHoodieLayerRender, direction: str) -> list[list[RGBA]]:
    """Generated-layer assembly schematic; deliberately excludes a fake Farmer."""
    canvas = blank_image(32, 48)
    hood = render.hood_default_frames[direction]
    if render.recipe["hoodLayer"]["state"] == "up":
        blit(canvas, hood, 0, 0)
        shirt_y = 26 if direction == "front" else 24
    elif direction == "front":
        blit(canvas, hood, (32 - len(hood[0])) // 2, 24)
        shirt_y = 24
    else:
        # The visible lowered-hood pixels occupy only the first ten rows of the
        # 16x32 cell. This schematic places that mass behind the Shirt bridge.
        blit(canvas, hood, 8, 18)
        shirt_y = 24
    blit(canvas, render.shirt_default_frames[direction], 8, shirt_y)
    return canvas


def _assembled_sheet(title: str, render: FSHoodieLayerRender, scale: int) -> list[list[RGBA]]:
    w, h = 32 * scale, 48 * scale
    gap = max(18, scale * 3)
    margin = 14
    top = 58
    canvas = blank_image(margin * 2 + w * 4 + gap * 3, top + h + 20, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "GENERATED-LAYER ASSEMBLY SCHEMATIC - NOT A RUNTIME SCREENSHOT", 8, 20, color=MUTED)
    for index, direction in enumerate(PREVIEW_ORDER):
        x = margin + index * (w + gap)
        draw_text(canvas, direction.upper(), x + (w - text_width(direction.upper())) // 2, 42, color=INK)
        _bordered(canvas, nearest_scale(_assembled_frame(render, direction), scale), x, top)
    return canvas


def _collection_sheet(title: str, rendered, *, scale: int, assembled: bool) -> list[list[RGBA]]:
    logical_w, logical_h = (32, 48) if assembled else (16, 16)
    sprite_w, sprite_h = logical_w * scale, logical_h * scale
    gap = max(10, scale * 2)
    label_w = 230
    top = 58
    row_h = sprite_h + 26
    canvas = blank_image(label_w + sprite_w * 4 + gap * 3 + 18, top + row_h * len(rendered) + 12, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    subtitle = "ASSEMBLED GENERATED LAYERS - NO FAKE FARMER" if assembled else "ISOLATED SHIRT SHELLS"
    draw_text(canvas, subtitle, 8, 20, color=MUTED)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (sprite_w + gap), 42, color=INK)
    for row, (recipe, render) in enumerate(rendered):
        y = top + row * row_h
        layers = "SHIRT + NATIVE SLEEVES + HAT"
        if recipe["hoodLayer"]["drawstrings"]:
            layers += " + IN-SHIRT STRINGS"
        draw_text(canvas, f"{row + 1:02d} {recipe['rarity'].upper()}  {recipe['hoodieSubtype'].replace('_', ' ').upper()}", 6, y + 1, color=INK)
        draw_text(canvas, recipe["itemName"][:34], 6, y + 15, color=INK)
        draw_text(canvas, layers[:36], 6, y + 29, color=MUTED)
        draw_text(canvas, f"HOOD {recipe['hoodLayer']['state'].upper()} / HAIR {render.metrics['hairPolicy'].upper()}", 6, y + 43, color=MUTED)
        for index, direction in enumerate(PREVIEW_ORDER):
            frame = _assembled_frame(render, direction) if assembled else render.shirt_default_frames[direction]
            _bordered(canvas, nearest_scale(frame, scale), label_w + index * (sprite_w + gap), y)
    return canvas


def _breakdown_sheet(rendered) -> list[list[RGBA]]:
    cell_w = 274
    cell_h = 244
    columns = 2
    rows = 3
    canvas = blank_image(columns * cell_w, 36 + rows * cell_h, BG)
    draw_text(canvas, "HOODIE LAYER CONSTRUCTION BREAKDOWN", 8, 8, color=INK)
    for index, (recipe, render) in enumerate(rendered):
        col, row = index % columns, index // columns
        x0, y0 = col * cell_w + 8, 36 + row * cell_h
        draw_text(canvas, f"{index + 1:02d} {recipe['itemName'][:31]}", x0, y0, color=INK)
        draw_text(canvas, "SHIRT", x0, y0 + 15, color=MUTED)
        _bordered(canvas, nearest_scale(render.shirt_default_frames["front"], 4), x0, y0 + 28)
        draw_text(canvas, "HOOD", x0 + 78, y0 + 15, color=MUTED)
        hood = render.hood_default_frames["front"] if recipe["hoodLayer"]["state"] == "up" else render.hood_default_frames["back"]
        hood_scale = 2 if len(hood[0]) == 32 else 4
        _bordered(canvas, nearest_scale(hood, hood_scale), x0 + 78, y0 + 28)
        draw_text(canvas, "STRINGS", x0 + 158, y0 + 15, color=MUTED)
        draw_text(canvas, "IN SHIRT" if recipe["hoodLayer"]["drawstrings"] else "NONE", x0 + 158, y0 + 48, color=MUTED)
        draw_text(canvas, "NATIVE SLEEVE COLORS", x0, y0 + 112, color=MUTED)
        for color_index, color in enumerate(render.upper.sleeve_colors):
            draw_rect(canvas, x0 + color_index * 12, y0 + 128, 10, 20, tuple(color) + (255,))
        draw_text(canvas, "PRESET", x0 + 48, y0 + 112, color=MUTED)
        assembled = nearest_scale(_assembled_frame(render, "front"), 2)
        _bordered(canvas, assembled, x0 + 48, y0 + 126)
        draw_text(canvas, "ONE RECIPE -> COORDINATED COMPONENTS", x0, y0 + 228, color=MUTED)
    return canvas


def _hood_anchor_sheet(rendered) -> list[list[RGBA]]:
    """Show the actual Hat frames and corrected category-specific origins."""

    label_w = 238
    cell_w = 124
    cell_h = 92
    top = 58
    canvas = blank_image(label_w + cell_w * 4 + 12, top + cell_h * len(rendered) + 12, BG)
    draw_text(canvas, "HOOD-ONLY SCALE-2 ANCHOR VALIDATION", 8, 7, color=INK)
    draw_text(canvas, "ACTUAL HAT FRAMES / HEADPOSITION IN PARENTHESES / NOT A RUNTIME SCREENSHOT", 8, 20, color=MUTED)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * cell_w + 20, 42, color=INK)
    model_keys = {
        "front": "FrontHat",
        "right": "RightHat",
        "back": "BackHat",
        "left": "LeftHat",
    }
    for row, (recipe, render) in enumerate(rendered):
        y = top + row * cell_h
        draw_text(canvas, f"{row + 1:02d} {recipe['itemName'][:32]}", 6, y + 2, color=INK)
        draw_text(canvas, f"HOOD {recipe['hoodLayer']['state'].upper()} / SCALE 2", 6, y + 16, color=MUTED)
        draw_text(canvas, "SHIRT/SLEEVES UNCHANGED", 6, y + 30, color=MUTED)
        for index, direction in enumerate(PREVIEW_ORDER):
            model = render.hood_json[model_keys[direction]]
            head = model["HeadPosition"]
            label = f"({head['X']},{head['Y']})"
            frame = nearest_scale(render.hood_default_frames[direction], 2)
            x = label_w + index * cell_w + (64 - len(frame[0])) // 2
            _bordered(canvas, frame, x, y)
            draw_text(canvas, label, label_w + index * cell_w + 70, y + 30, color=MUTED)
    return canvas


def _readme(rendered) -> str:
    lines = []
    for index, (recipe, _) in enumerate(rendered, 1):
        components = ["Shirt", "native animated sleeves via SleeveColors", "Hood/Hat"]
        if recipe["hoodLayer"]["drawstrings"]:
            components.append("drawstrings integrated into Shirt")
        lines.append(
            f"{index}. **{recipe['itemName']}** — {recipe['rarity']}; "
            f"{recipe['hoodieSubtype'].replace('_', ' ').title()}; "
            f"hood {recipe['hoodLayer']['state']}; " + ", ".join(components) + "; Preset"
        )
    return """# RNG Clothing Hoodie Layer Architecture Correction

Test-only Fashion Sense content pack. Nothing is installed automatically.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

Content Patcher is **not required**. The weather-reactive reference logic was studied, but this batch deliberately uses static generated hood states.

## Install

Copy the entire `RNG-Clothing-Hoodie-Layer-Correction` folder into Stardew Valley's `Mods` folder, then fully restart SMAPI.

## Equip the complete hoodie

Open the Fashion Sense Hand Mirror, choose **Outfits**, switch to **Presets**, and select a preset beginning with `Hoodie Layers -`.

Use the preset. The corrected runtime-safe assembly is **Shirt + native animated Farmer sleeves + Hood/Hat**. Drawstrings, when present, are part of the body-anchored Shirt art.

Version 1.9.0 preserves every proven anchor and layer-order contract. It micro-polishes the collapsed fold clusters and changes rigid parallel drawstrings into two connected inward-falling cords. Hat anchors, Hat draw order, Shirt anchor, native sleeves, and hair behavior are unchanged.

Hood-up presets intentionally hide hair. Hood-down presets preserve hair and use direction-specific Fashion Sense draw order.

## Garments

""" + "\n".join(lines) + """

## Runtime status

All six are `EXPERIMENTAL / NOT TESTED`. Static validation proves component contracts, deterministic pixels, preset pairing, and alpha integrity; it does not prove every hairstyle, walk/tool pose, horse pose, or multiplayer sync state.

Suggested first test: Harbor Haze Pullover (hood down) and Tidecap Contrast Hoodie (hood up), then Sproutwing Cropped Hoodie for the richest corrected assembly.
"""


def main() -> None:
    batch = generate_hoodie_layer_batch()
    rendered = [(recipe, render_fs_hoodie_layers(recipe)) for recipe in batch["recipes"]]
    OUT.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    PACK.mkdir(parents=True, exist_ok=True)
    presets = []
    localization: dict[str, str] = {}
    for recipe, render in rendered:
        name = recipe["itemName"]
        target = OUT / _slug(name)
        target.mkdir(parents=True, exist_ok=True)
        write_rgba_png(target / "shirt.png", render.shirt_texture)
        write_rgba_png(target / "hood.png", render.hood_texture)
        write_rgba_png(target / "isolated-shirt-directions-8x.png", _isolated_sheet(name, render, 8))
        write_rgba_png(target / "gameplay-footprint.png", _assembled_sheet(name, render, 2))
        write_rgba_png(target / "assembled-preset-4x.png", _assembled_sheet(name, render, 4))
        _json(target / "recipe.json", recipe)
        _json(target / "summary.json", {
            "name": name,
            "description": recipe["itemDescription"],
            "rarity": recipe["rarity"],
            "hoodieSubtype": recipe["hoodieSubtype"],
            "layers": {
                "Shirt": True,
                "Sleeves": "native animated via Shirt SleeveColors",
                "HatHood": True,
                "Accessory": False,
                "Preset": True,
            },
            "hoodLayer": recipe["hoodLayer"],
            "referenceInfluence": recipe["referenceInfluence"],
            "metrics": render.metrics,
            "promotion": "EXPERIMENTAL",
            "runtime": "NOT_TESTED",
        })

        shirt_dir = PACK / "Shirts" / _folder(name)
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
        write_rgba_png(shirt_dir / "shirt.png", render.shirt_texture)
        hood_dir = PACK / "Hats" / (_folder(name) + "Hood")
        hood_dir.mkdir(parents=True, exist_ok=True)
        _json(hood_dir / "hat.json", render.hood_json)
        write_rgba_png(hood_dir / "hat.png", render.hood_texture)
        presets.append(_preset(recipe))
        localization[f"hoodie.{recipe['id']}.name"] = name
        localization[f"hoodie.{recipe['id']}.description"] = recipe["itemDescription"]

    _json(ROOT / "output" / "recipes" / "hoodie_layer_correction.json", batch)
    isolated = _collection_sheet("HOODIE LAYER CORRECTION - ISOLATED SHIRTS", rendered, scale=6, assembled=False)
    gameplay = _collection_sheet("HOODIE LAYER CORRECTION - GAMEPLAY FOOTPRINT", rendered, scale=2, assembled=True)
    assembled = _collection_sheet("HOODIE LAYER CORRECTION - ASSEMBLED PRESETS", rendered, scale=4, assembled=True)
    breakdown = _breakdown_sheet(rendered)
    hood_anchor = _hood_anchor_sheet(rendered)
    write_rgba_png(OUT / "HOODIE_LAYER_ISOLATED.png", isolated)
    write_rgba_png(OUT / "HOODIE_LAYER_GAMEPLAY_FOOTPRINT.png", gameplay)
    write_rgba_png(OUT / "HOODIE_LAYER_ASSEMBLED_PRESETS.png", assembled)
    write_rgba_png(OUT / "HOODIE_LAYER_CONSTRUCTION_BREAKDOWN.png", breakdown)
    write_rgba_png(OUT / "HOOD_ONLY_ANCHOR_VALIDATION.png", hood_anchor)
    write_rgba_png(COMPARE / "HOODIE_LAYER_ISOLATED.png", isolated)
    write_rgba_png(COMPARE / "HOODIE_LAYER_GAMEPLAY_FOOTPRINT.png", gameplay)
    write_rgba_png(COMPARE / "HOODIE_LAYER_ASSEMBLED_PRESETS.png", assembled)
    write_rgba_png(COMPARE / "HOODIE_LAYER_CONSTRUCTION_BREAKDOWN.png", breakdown)
    write_rgba_png(COMPARE / "HOOD_ONLY_ANCHOR_VALIDATION.png", hood_anchor)
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing Hoodie Layer Architecture Correction",
        "Author": "RNG Clothing Experiment",
        "Version": "1.9.0",
        "Description": "Test-only hoodies with corrected Hat origins and complete directional hood art.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "i18n" / "default.json", localization)
    (PACK / "README.md").write_text(_readme(rendered), encoding="utf-8")
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED",
        "garments": 6,
        "shirts": 6,
        "customSleeves": 0,
        "nativeSleeveColorSets": 6,
        "hats": 6,
        "accessories": 0,
        "presets": 6,
        "hoodUp": sum(recipe["hoodLayer"]["state"] == "up" for recipe, _ in rendered),
        "hoodDown": sum(recipe["hoodLayer"]["state"] == "down" for recipe, _ in rendered),
        "hoodAnchorFix": "farmer_origin_0_32_plus_twice_scale4_head_origin",
        "runtimePromotion": "EXPERIMENTAL",
        "beautyClaim": "HUMAN_AND_RUNTIME_REVIEW_REQUIRED",
        "garmentMetrics": {recipe["id"]: render.metrics for recipe, render in rendered},
    })
    print(f"Generated {len(rendered)} coordinated hoodie presets")
    print(OUT)
    print(PACK)


if __name__ == "__main__":
    main()
