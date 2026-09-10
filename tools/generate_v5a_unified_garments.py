#!/usr/bin/env python3
"""Generate the exact nine-item V5A unified-garment diagnostic collection."""

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
from generator.renderers.fashionsense import render_fs_v5a
from generator.v2_recipe_engine import load_v2_data
from generator.v5a import generate_v5a_collection
from generator.v5a.validation import diagnose_v5a, diagnose_v5a_collection


OUT = ROOT / "output" / "fashionsense" / "v5a"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5A-Unified-Garments"
RECIPE_OUT = ROOT / "output" / "recipes" / "v5a_unified_collection.json"
PREVIEW_ORDER = ("front", "right", "back", "left")
ARTICLE_FOLDER = {"DRESS": "dress", "ONE_PIECE": "one-piece", "BOUNDED_LONG_OUTERWEAR": "long-outerwear"}
BG: RGBA = (235, 227, 214, 255)
INK: RGBA = (50, 46, 44, 255)
BORDER: RGBA = (77, 70, 66, 255)
TILE: RGBA = (213, 205, 193, 255)
MASK_COLORS = {
    "DRESS_LOWER": (181, 102, 137, 255), "WAIST": (230, 180, 84, 255), "HEM": (119, 70, 126, 255), "FOLD": (80, 129, 167, 255),
    "BELT": (221, 149, 73, 255), "LOWER_PANEL": (80, 141, 127, 255), "CENTER_SEAM": (45, 70, 72, 255),
    "OUTER_PANEL_LEFT": (177, 119, 64, 255), "OUTER_PANEL_RIGHT": (153, 87, 57, 255), "INNER_LAYER": (103, 132, 84, 255),
    "BACK_PANEL": (116, 99, 139, 255), "EXTENDED_HEM": (70, 68, 85, 255),
}


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
    height = len(frames["front"])
    sprite_w, sprite_h = 16 * scale, height * scale
    gap, margin, top = 18, 16, 40
    canvas = blank_image(margin * 2 + sprite_w * 4 + gap * 3, top + sprite_h + 16, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        x = margin + index * (sprite_w + gap)
        label = direction.upper()
        draw_text(canvas, label, x + (sprite_w - text_width(label)) // 2, 24, color=INK)
        _bordered(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _article_debug(render):
    result = {}
    for direction in PREVIEW_ORDER:
        frame = blank_image(16, render.frame_height)
        for y in range(render.frame_height):
            for x in range(16):
                region = render.regions[direction][y][x]
                if region is not None:
                    frame[y][x] = MASK_COLORS.get(region, (105, 114, 123, 255))
        result[direction] = frame
    return result


def _all_direction_sheet(title: str, rendered, scale: int):
    sprite_w = 16 * scale
    label_w, gap, top = 205, 18, 51
    row_heights = [render.frame_height * scale + 20 for _, render, _ in rendered]
    width = label_w + sprite_w * 4 + gap * 3 + 20
    canvas = blank_image(width, top + sum(row_heights) + 12, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "DIRECT LOGICAL PIXELS / SCALE 2 RUNTIME / NEAREST-NEIGHBOR PREVIEW", 8, 20, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (sprite_w + gap), 37, color=INK)
    y = top
    for recipe, render, _ in rendered:
        design = recipe["designRecipe"]
        draw_text(canvas, f"{design['rarity'].upper()}  {recipe['articleType'].replace('_', ' ')}", 6, y + 3, color=INK)
        draw_text(canvas, design["itemName"][:29], 6, y + 17, color=INK)
        for index, direction in enumerate(PREVIEW_ORDER):
            _bordered(canvas, nearest_scale(render.default_frames[direction], scale), label_w + index * (sprite_w + gap), y)
        y += render.frame_height * scale + 20
    return canvas


def _gameplay_grid(rendered):
    scale, cell_w, cell_h, top = 2, 240, 94, 45
    canvas = blank_image(cell_w * 3, top + cell_h * 3, BG)
    draw_text(canvas, "V5A GARMENT-ONLY GAMEPLAY FOOTPRINT - SCALE 2", 8, 7, color=INK)
    articles = ("DRESS", "ONE_PIECE", "BOUNDED_LONG_OUTERWEAR")
    for col, article in enumerate(articles):
        draw_text(canvas, article.replace("_", " "), col * cell_w + 8, 25, color=INK)
        selected = [item for item in rendered if item[0]["articleType"] == article]
        selected.sort(key=lambda item: {"Common": 0, "Uncommon": 1, "Rare": 2}[item[0]["designRecipe"]["rarity"]])
        for row, (recipe, render, _) in enumerate(selected):
            x, y = col * cell_w + 12, top + row * cell_h
            draw_text(canvas, recipe["designRecipe"]["rarity"].upper(), x, y + 2, color=INK)
            draw_text(canvas, recipe["designRecipe"]["itemName"][:24], x, y + 16, color=INK)
            _bordered(canvas, nearest_scale(render.default_frames["front"], scale), x + 174, y + 2)
    return canvas


def _article_comparison(rendered):
    ordered = sorted(rendered, key=lambda item: ({"DRESS": 0, "ONE_PIECE": 1, "BOUNDED_LONG_OUTERWEAR": 2}[item[0]["articleType"]], {"Common": 0, "Uncommon": 1, "Rare": 2}[item[0]["designRecipe"]["rarity"]]))
    return _all_direction_sheet("V5A ARTICLE COMPARISON - DRESS / ONE-PIECE / BOUNDED LONG OUTERWEAR", ordered, 2)


def _shirt_model(render, y: int) -> dict[str, Any]:
    palette = load_v2_data()["palettes"]["families"][render.design.base.recipe["paletteFamily"]]
    return {
        "Scale": 2.0,
        "HideSleeves": render.hide_sleeves,
        "HideWhileSwimming": True,
        "HideWhileWearingBathingSuit": True,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{"Name": "Primary Fabric", "DefaultColor": palette["defaultDye"], "Values": [[value, value, value] for value in render.active_mask_values]}],
        "SleeveColors": [list(value) for value in render.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": render.frame_height},
    }


def _shirt_json(recipe, render) -> dict[str, Any]:
    design = recipe["designRecipe"]
    tags = ["Lifestyle", design["themeFamily"].replace("_", " ").title(), recipe["articleType"].replace("_", " ").title(), design["rarity"], recipe["sleeveIntent"].replace("_", " ").title(), "RNG Clothing", "Generator V5A", "Experimental", "Test"]
    h = render.frame_height
    return {
        "Name": design["itemName"], "Format": "7.5.0", "Tags": tags,
        "FrontShirt": _shirt_model(render, 0), "RightShirt": _shirt_model(render, h),
        "LeftShirt": _shirt_model(render, h * 2), "BackShirt": _shirt_model(render, h * 3),
    }


def _readme(rendered) -> str:
    rows = "\n".join(f"{index}. **{recipe['designRecipe']['itemName']}** — {recipe['designRecipe']['rarity']}; {recipe['articleType'].replace('_', ' ').title()}; {recipe['sleeveIntent'].replace('_', ' ')}" for index, (recipe, _, _) in enumerate(rendered, 1))
    return f"""# RNG Clothing V5A Unified Garments\n\nTest-only Fashion Sense pack. Nothing is installed automatically. Every appearance is **EXPERIMENTAL**, not runtime-passed.\n\n## Requirements\n\n- Stardew Valley 1.6.15\n- SMAPI\n- Fashion Sense 7.5.0 installed separately\n\n## Install\n\nCopy the entire `RNG-Clothing-V5A-Unified-Garments` folder into `Stardew Valley/Mods`, fully restart SMAPI, obtain a Fashion Sense Hand Mirror (`fs_add_mirror` if needed), and select the garments in the **Shirts** category. Fashion Sense has no Dress or Coat category, so this test intentionally exports bounded unified garments as extended Shirt appearances.\n\n## Garments\n\n{rows}\n\n## Important runtime boundary\n\nThe source frames are 16 pixels wide, 19–24 logical pixels tall, Scale 2, BodyPosition `(0,32)`. The extended hem is attached to Fashion Sense's torso-following Shirt layer. It is not articulated to the legs. Test walking, tools, sitting, horse, and swimming before promotion. Sleeveless hides the sleeve layer; other prototypes preserve the existing native animated SleeveColors approach.\n"""


def main() -> None:
    batch = generate_v5a_collection()
    renders = [render_fs_v5a(recipe) for recipe in batch["recipes"]]
    diagnostics = [diagnose_v5a(render) for render in renders]
    collection = diagnose_v5a_collection(batch["recipes"], renders, diagnostics)
    if not collection.passes:
        raise ValueError("V5A collection failed: " + "; ".join(collection.errors))
    rendered = list(zip(batch["recipes"], renders, diagnostics))
    OUT.mkdir(parents=True, exist_ok=True)
    for recipe, render, diagnostic in rendered:
        design = recipe["designRecipe"]
        target = OUT / ARTICLE_FOLDER[recipe["articleType"]]
        target.mkdir(parents=True, exist_ok=True)
        slug = _slug(design["itemName"])
        write_rgba_png(target / f"{slug}.png", render.texture)
        write_rgba_png(target / f"{slug}-native-8x.png", nearest_scale(render.texture, 8))
        write_rgba_png(target / f"{slug}-directions-8x.png", _direction_sheet(design["itemName"], render.default_frames, 8))
        write_rgba_png(target / f"{slug}-gameplay-size.png", _direction_sheet(design["itemName"] + " - SCALE 2", render.default_frames, 2))
        write_rgba_png(target / f"{slug}-article-mask-8x.png", _direction_sheet(design["itemName"] + " - SEMANTIC ARTICLE REGIONS", _article_debug(render), 8))
        _json(target / f"{slug}-summary.json", {
            "recipe": recipe,
            "frameContract": {"logicalSize": [16, render.frame_height], "Scale": 2.0, "BodyPosition": [0, 32], "directionOrder": ["front", "right", "left", "back"]},
            "extraResolutionUse": ["waist transition", "extended silhouette", "hem termination", "article-aware surface targets", "direction-specific side/back reconstruction"],
            "staticDiagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics},
            "promotionStatus": "EXPERIMENTAL",
        })
        shirt_dir = PACK / "Shirts" / _folder(design["itemName"])
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)
    _json(RECIPE_OUT, batch)
    _json(OUT / "validation.json", {"status": "PASS_STATIC", "runtimeStatus": "NOT_TESTED", "promotionStatus": "EXPERIMENTAL", "collection": {"passes": collection.passes, "errors": list(collection.errors), "warnings": list(collection.warnings), "metrics": collection.metrics}, "garments": [{"id": recipe["id"], "name": recipe["designRecipe"]["itemName"], "articleType": recipe["articleType"], "rarity": recipe["designRecipe"]["rarity"], "frameHeight": render.frame_height, "diagnostics": diagnostic.metrics} for recipe, render, diagnostic in rendered]})
    _json(PACK / "manifest.json", {"Name": "RNG Clothing V5A Unified Garments", "Author": "RNG Clothing Experiment", "Version": "0.1.0", "Description": "Test-only experimental Dress, One-Piece, and bounded Long Outerwear Fashion Sense prototypes.", "UniqueID": "RNGClothing.FashionSense.V5AUnified", "UpdateKeys": [], "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}})
    _json(PACK / "i18n" / "default.json", {key: value for recipe in batch["recipes"] for key, value in ((f"shirt.{recipe['id']}.name", recipe["designRecipe"]["itemName"]), (f"shirt.{recipe['id']}.description", recipe["designRecipe"]["itemDescription"]))})
    (PACK / "README.md").write_text(_readme(rendered), encoding="utf-8")
    write_rgba_png(OUT / "V5A_GAMEPLAY_FOOTPRINT.png", _gameplay_grid(rendered))
    write_rgba_png(OUT / "V5A_DIRECTIONS_8X.png", _all_direction_sheet("V5A UNIFIED GARMENTS - FRONT / RIGHT / BACK / LEFT", rendered, 8))
    write_rgba_png(OUT / "V5A_ARTICLE_COMPARISON.png", _article_comparison(rendered))
    print(f"Generated {len(rendered)} V5A garments at {OUT}; all remain EXPERIMENTAL")


if __name__ == "__main__":
    main()
