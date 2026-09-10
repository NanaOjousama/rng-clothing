#!/usr/bin/env python3
"""Generate the two controlled Generator V4 multi-article collections."""

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
from generator.renderers.fashionsense import render_fs_v4
from generator.v2_recipe_engine import load_v2_data
from generator.v4 import diagnose_v4_article, diagnose_v4_collection, generate_v4_aot_collection, generate_v4_neutral_collection


OUT = ROOT / "output" / "fashionsense" / "v4"
PACK_ROOT = ROOT / "test-packs" / "fashionsense"
DIRECTIONS = ("front", "back", "left", "right")
BG: RGBA = (236, 226, 211, 255); INK: RGBA = (52, 48, 45, 255)
BORDER: RGBA = (82, 75, 69, 255); TILE: RGBA = (215, 207, 194, 255)


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


def _sheet(title: str, frames, scale: int):
    size = 16 * scale; gap = 18; margin = 16; top = 39
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 16, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        draw_text(canvas, direction, x + (size - text_width(direction)) // 2, 23, color=INK)
        _bordered(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _article_debug(render):
    colors = {
        "FITTED_SHIRT": (91, 135, 176, 255), "SWEATER_TOP": (141, 102, 161, 255),
        "VEST_TOP": (181, 126, 62, 255), "CROPPED_JACKET": (166, 78, 68, 255),
        "SHORT_OUTERWEAR": (69, 125, 87, 255),
    }
    result = {}
    for direction in DIRECTIONS:
        frame = blank_image(16, 16)
        for x, y in render.article_cells[direction]:
            frame[y][x] = colors[render.recipe["articleType"]]
        for x, y in render.translated_material_cells[direction]:
            frame[y][x] = (235, 210, 126, 255)
        result[direction] = frame
    return result


def _collection_sheet(title: str, rendered, *, scale: int = 2):
    sprite = 16 * scale; label = 188; gap = 18; top = 48; row_h = sprite + 18
    canvas = blank_image(label + sprite * 4 + gap * 3 + 20, top + row_h * len(rendered) + 12, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "EXACT EQUAL FASHION SENSE FOOTPRINT - 16X16 AT SCALE 2", 8, 20, color=INK)
    for i, direction in enumerate(DIRECTIONS):
        draw_text(canvas, direction, label + i * (sprite + gap), 35, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h; design = recipe["designRecipe"]
        draw_text(canvas, f"{design['rarity'].upper()}  {recipe['articleType'].replace('_', ' ')}", 6, y + 2, color=INK)
        draw_text(canvas, design["itemName"][:27], 6, y + 15, color=INK)
        for i, direction in enumerate(DIRECTIONS):
            _bordered(canvas, nearest_scale(render.default_frames[direction], scale), label + i * (sprite + gap), y)
    return canvas


def _front_grid(title: str, rendered):
    scale = 8; size = 128; cols = 4; rows = (len(rendered) + cols - 1) // cols; cell_w = 190; cell_h = 180
    canvas = blank_image(cols * cell_w, 34 + rows * cell_h, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for i, (recipe, render, _) in enumerate(rendered):
        x = (i % cols) * cell_w + 24; y = 34 + (i // cols) * cell_h + 34; design = recipe["designRecipe"]
        draw_text(canvas, f"{design['rarity'].upper()} - {recipe['articleType'].replace('_', ' ')}", x, y - 28, color=INK)
        draw_text(canvas, design["itemName"][:23], x, y - 15, color=INK)
        _bordered(canvas, nearest_scale(render.default_frames["front"], scale), x, y)
    return canvas


def _shirt_model(render, y: int) -> dict[str, Any]:
    base = render.design.base; palette = load_v2_data()["palettes"]["families"][base.recipe["paletteFamily"]]
    return {
        "Scale": 2.0, "HideSleeves": False, "DisableGrayscale": False,
        "ColorMaskLayers": [{"Name": "Primary Fabric", "DefaultColor": palette["defaultDye"],
            "Values": [[base.config["outerMaskRamp"][role]] * 3 for role in base.active_main_roles]}],
        "SleeveColors": [list(value) for value in render.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y}, "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe, render):
    design = recipe["designRecipe"]
    tags = ["Lifestyle", recipe["collection"], recipe["articleType"].replace("_", " ").title(), design["rarity"], "RNG Clothing", "Generator V4", "Test"]
    return {"Name": design["itemName"], "Format": "7.5.0", "Tags": tags,
        "FrontShirt": _shirt_model(render, 0), "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32), "BackShirt": _shirt_model(render, 48)}


def _readme(name: str, rendered) -> str:
    rows = "\n".join(f"{i}. **{r['designRecipe']['itemName']}** — {r['designRecipe']['rarity']}; {r['articleType'].replace('_', ' ').title()}" for i, (r, _, _) in enumerate(rendered, 1))
    return f"""# {name}\n\nTest-only Fashion Sense Generator V4 collection. It is not installed automatically.\n\n## Requirements\n\n- Stardew Valley 1.6.15\n- SMAPI\n- Fashion Sense 7.5.0 installed separately\n\n## Install\n\nCopy the entire `{name}` folder into `Stardew Valley/Mods`, then fully restart SMAPI. Use `fs_add_mirror` if needed and select these items in the Fashion Sense Shirts category.\n\n## Garments\n\n{rows}\n\nAll use 16x16 frames, Scale 2, BodyPosition `(0,32)`, and the proven native animated sleeve approach. `LONG_OUTERWEAR` is intentionally absent because lower-body coat animation has not been proven.\n"""


def _generate(batch, folder: str, pack_name: str, unique_id: str, expected_counts):
    recipes = batch["recipes"]; renders = [render_fs_v4(r) for r in recipes]
    diagnostics = [diagnose_v4_article(r) for r in renders]
    collection = diagnose_v4_collection(recipes, renders, diagnostics, expected_counts=expected_counts)
    if not collection.passes:
        raise ValueError("V4 collection failed: " + "; ".join(collection.errors))
    target = OUT / folder; pack = PACK_ROOT / pack_name; target.mkdir(parents=True, exist_ok=True)
    rendered = []
    for recipe, render, diagnostic in zip(recipes, renders, diagnostics):
        design = recipe["designRecipe"]; slug = _slug(design["itemName"]); rendered.append((recipe, render, diagnostic))
        write_rgba_png(target / f"{slug}.png", render.texture)
        write_rgba_png(target / f"{slug}-default-8x.png", nearest_scale(render.texture, 8))
        write_rgba_png(target / f"{slug}-directions-8x.png", _sheet(design["itemName"], render.default_frames, 8))
        write_rgba_png(target / f"{slug}-gameplay-size.png", _sheet(design["itemName"] + " - GAME SIZE", render.default_frames, 2))
        write_rgba_png(target / f"{slug}-article-mask-8x.png", _sheet(design["itemName"] + " - ARTICLE MASK", _article_debug(render), 8))
        _json(target / f"{slug}-summary.json", {"v4Recipe": recipe, "articleReadWithoutName": diagnostic.metrics["inferredArticle"],
            "articleTranslation": {"removedCells": diagnostic.metrics["removedCells"], "translatedMaterialCells": diagnostic.metrics["translatedMaterialCells"], "maximumOccupiedY": diagnostic.metrics["maximumOccupiedY"]},
            "primaryDesignIdea": f"{design['surfaceDesign']['compositionType'].replace('_', ' ')} at {design['concept']['focalArea'].replace('_', ' ')}",
            "diagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics}})
        shirt_dir = pack / "Shirts" / _folder(design["itemName"]); shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render)); write_rgba_png(shirt_dir / "shirt.png", render.texture)
    _json(ROOT / "output" / "recipes" / f"v4_{folder}_collection.json", batch)
    _json(target / "validation.json", {"status": "PASS_V4_STATIC_CONTRACT", "beautyClaim": "STATIC_REVIEW_REQUIRED",
        "collection": {"passes": collection.passes, "errors": list(collection.errors), "warnings": list(collection.warnings), "metrics": collection.metrics},
        "garments": [{"id": r["id"], "name": r["designRecipe"]["itemName"], "articleType": r["articleType"], "rarity": r["designRecipe"]["rarity"], "diagnostics": {"passes": d.passes, "errors": list(d.errors), "warnings": list(d.warnings), "metrics": d.metrics}} for r, d in zip(recipes, diagnostics)]})
    _json(pack / "manifest.json", {"Name": pack_name, "Author": "RNG Clothing Experiment", "Version": "1.0.0", "Description": "Test-only Generator V4 multi-garment Fashion Sense collection.", "UniqueID": unique_id, "UpdateKeys": [], "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}})
    _json(pack / "i18n" / "default.json", {key: value for r in recipes for key, value in ((f"shirt.{r['id']}.name", r["designRecipe"]["itemName"]), (f"shirt.{r['id']}.description", r["designRecipe"]["itemDescription"]))})
    (pack / "README.md").write_text(_readme(pack_name, rendered), encoding="utf-8")
    return rendered


def main() -> None:
    aot = _generate(generate_v4_aot_collection(), "aot", "RNG-Clothing-V4-AoT", "RNGClothing.FashionSense.V4AoT", {"Common": 2, "Uncommon": 2, "Rare": 2})
    neutral = _generate(generate_v4_neutral_collection(), "neutral", "RNG-Clothing-V4-Neutral-Benchmark", "RNGClothing.FashionSense.V4Neutral", {"Common": 2, "Uncommon": 3, "Rare": 3})
    write_rgba_png(OUT / "V4_AOT_ARTICLE_COMPARISON.png", _collection_sheet("V4 AOT ARTICLE COMPARISON", aot))
    write_rgba_png(OUT / "V4_NEUTRAL_ARTICLE_COMPARISON.png", _collection_sheet("V4 NEUTRAL ARTICLE COMPARISON", neutral))
    write_rgba_png(OUT / "V4_GAMEPLAY_SIZE_COMPARISON.png", _collection_sheet("V4 ALL COLLECTIONS - GAMEPLAY SIZE", aot + neutral))
    write_rgba_png(OUT / "V4_ARTICLE_FRONTS_8X.png", _front_grid("V4 MULTI-GARMENT ARTICLE FRONTS", aot + neutral))
    # Rarity-organized by construction so parity is visible across article families.
    ordered = sorted(aot + neutral, key=lambda item: ({"Common": 0, "Uncommon": 1, "Rare": 2}[item[0]["designRecipe"]["rarity"]], item[0]["articleType"], item[0]["id"]))
    write_rgba_png(OUT / "V4_RARITY_COMPARISON.png", _collection_sheet("V4 CROSS-ARTICLE RARITY COMPARISON", ordered))
    print(f"Generated V4 AoT={len(aot)}, neutral={len(neutral)} at {OUT}")


if __name__ == "__main__":
    main()
