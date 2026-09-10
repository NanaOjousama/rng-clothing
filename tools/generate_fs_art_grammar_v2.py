#!/usr/bin/env python3
"""Generate the four-archetype permanent Fashion Sense HD grammar control set."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from generator.renderers.fashionsense import (
    composite_art_default_frame,
    diagnose_fs_hd_render,
    render_fs_hd_v2,
    render_hd_art_treatment,
)
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data


RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
OUTPUT = ROOT / "output" / "fashionsense" / "art-grammar-v2"
COMPARISON = ROOT / "output" / "comparisons" / "FS_ART_GRAMMAR_V2_COMPARISON.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Art-Grammar-V2"

DIRECTIONS = ("front", "back", "left", "right")
STACK_ORDER = ("front", "right", "left", "back")
SELECTED = (
    ("lifestyle-v2-16", "mistral_permanent_hd", "Mistral Permanent HD", "PRIOR FS"),
    ("lifestyle-v2-11", "harbor_yoke_work_shirt_hd", "Harbor Yoke Work Shirt HD", "VANILLA V2"),
    ("lifestyle-v2-19", "garnet_yoke_top_hd", "Garnet Yoke Top HD", "VANILLA V2"),
    ("lifestyle-v2-05", "hearth_ribbed_sweater_hd", "Hearth Ribbed Sweater HD", "VANILLA V2"),
)

BACKGROUND: RGBA = (236, 226, 211, 255)
INK: RGBA = (61, 55, 51, 255)
BORDER: RGBA = (91, 83, 75, 255)
FRAME_BACK: RGBA = (215, 207, 194, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _recipes() -> dict[str, dict[str, Any]]:
    batch = json.loads(RECIPE_BATCH.read_text(encoding="utf-8"))
    return {recipe["id"]: recipe for recipe in batch["recipes"]}


def _stack(frames):
    result = blank_image(16, 64)
    for index, direction in enumerate(STACK_ORDER):
        for y, row in enumerate(frames[direction]):
            result[index * 16 + y] = list(row)
    return result


def _bordered_blit(destination, source, x: int, y: int) -> None:
    draw_rect(destination, x - 2, y - 2, len(source[0]) + 4, len(source) + 4, BORDER)
    draw_rect(destination, x - 1, y - 1, len(source[0]) + 2, len(source) + 2, FRAME_BACK)
    blit(destination, source, x, y)


def _direction_contact(title: str, frames, scale: int):
    size = 16 * scale
    gap = 18
    margin = 16
    top = 36
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 16, BACKGROUND)
    draw_text(canvas, title, (len(canvas[0]) - text_width(title)) // 2, 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        draw_text(canvas, direction, x + (size - text_width(direction)) // 2, 22, color=INK)
        _bordered_blit(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _main_comparison(rows):
    # Both baselines and new FS output are exactly 32x32 displayed pixels:
    # vanilla 8x8 * 4, or Fashion Sense 16x16 * 2.
    sprite = 32
    label_width = 112
    gap = 18
    top = 54
    row_height = 48
    section_gap = 13
    width = label_width + sprite * 4 + gap * 3 + 22
    height = top + len(rows) * (row_height * 2 + section_gap) + 12
    canvas = blank_image(width, height, BACKGROUND)
    title = "FS ART GRAMMAR V2 - EXACT GAMEPLAY FOOTPRINT"
    subtitle = "JACKET PRIOR FS - OTHERS VANILLA V2"
    draw_text(canvas, title, (width - text_width(title)) // 2, 8, color=INK)
    draw_text(canvas, subtitle, (width - text_width(subtitle)) // 2, 22, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = label_width + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 39, color=INK)

    y = top
    for archetype, baseline_label, baseline, new_frames in rows:
        draw_text(canvas, archetype.replace("_", " "), 8, y + 2, color=INK)
        draw_text(canvas, baseline_label, 8, y + 15, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = label_width + index * (sprite + gap)
            _bordered_blit(canvas, baseline[direction], x, y)
        y += row_height
        draw_text(canvas, "NEW FS HD", 8, y + 12, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = label_width + index * (sprite + gap)
            _bordered_blit(canvas, nearest_scale(new_frames[direction], 2), x, y)
        y += row_height + section_gap
    return canvas


def _shirt_model(render, y: int) -> dict[str, Any]:
    config = render.config
    v2 = load_v2_data()
    palette = v2["palettes"]["families"][render.recipe["paletteFamily"]]
    values = [
        [config["outerMaskRamp"][role]] * 3
        for role in render.active_main_roles
    ]
    sleeves = [[config["outerMaskRamp"][role]] * 3 for role in config["sleeveMaskRoles"]]
    return {
        "Scale": config["scale"],
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Primary Fabric",
            "DefaultColor": palette["defaultDye"],
            "Values": values,
        }],
        "SleeveColors": sleeves,
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": config["bodyPosition"],
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(render, display_name: str) -> dict[str, Any]:
    return {
        "Name": display_name,
        "Format": "7.5.0",
        "Tags": [
            "Lifestyle",
            render.recipe["archetype"].replace("_", " ").title(),
            render.recipe["rarity"],
            "RNG Clothing",
            "Permanent Art Grammar V2",
            "Test",
        ],
        "FrontShirt": _shirt_model(render, 0),
        "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32),
        "BackShirt": _shirt_model(render, 48),
    }


def _readme(names: list[str]) -> str:
    listing = "\n".join(f"- {name}" for name in names)
    return f"""# RNG Clothing - Fashion Sense Permanent Art Grammar V2 Test

This isolated, test-only content pack contains four original garments rendered from unchanged Generator V2 semantic recipes through the permanent 16x16 Scale-2 Fashion Sense backend.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the whole `RNG-Clothing-HD-Art-Grammar-V2` folder into `Stardew Valley/Mods`, then fully restart SMAPI.

Expected path:

```text
Stardew Valley/Mods/RNG-Clothing-HD-Art-Grammar-V2/manifest.json
```

## Garments

{listing}

Run `fs_add_mirror` if you need a Hand Mirror, then select each garment in the Shirts category. Judge all directions while standing and walking; also check basic tools and horse riding. All four retain 16x16 frames, Scale 2, BodyPosition `(0,32)`, and Fashion Sense's native animated sleeve recoloring.

This pack is not production content and is not installed automatically.
"""


def main() -> None:
    recipes = _recipes()
    data = load_v2_data()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    comparison_rows = []
    validation = {
        "status": "PASS",
        "beautyClaim": "PROVISIONAL_STATIC_REVIEW_ONLY",
        "runtimeContract": {
            "FashionSense": "7.5.0",
            "logicalFrame": [16, 16],
            "Scale": 2.0,
            "BodyPosition": [0, 32],
            "nativeAnimatedSleeves": True,
        },
        "garments": [],
    }
    pack_names = []

    for recipe_id, slug, display_name, baseline_label in SELECTED:
        recipe = recipes[recipe_id]
        render = render_fs_hd_v2(recipe)
        diagnostics = diagnose_fs_hd_render(render)
        if not diagnostics.passes:
            raise ValueError(f"{recipe_id} failed permanent FS diagnostics: {diagnostics.errors}")

        write_rgba_png(OUTPUT / f"{slug}.png", render.texture)
        write_rgba_png(OUTPUT / f"{slug}-default-8x.png", nearest_scale(_stack(render.default_frames), 8))
        write_rgba_png(
            OUTPUT / f"{slug}-directions-8x.png",
            _direction_contact(display_name, render.default_frames, 8),
        )
        write_rgba_png(
            OUTPUT / f"{slug}-directions-gameplay-2x.png",
            _direction_contact(display_name + " GAME SIZE", render.default_frames, 2),
        )
        _json(OUTPUT / f"{slug}-recipe.json", recipe)

        if recipe["archetype"] == "JACKET":
            prior = render_hd_art_treatment(recipe, "POLISHED_HD")
            baseline = {
                direction: nearest_scale(
                    composite_art_default_frame(prior.frames[direction], prior.art_config), 2
                )
                for direction in DIRECTIONS
            }
        else:
            vanilla = render_v2_recipe(recipe, data)
            baseline = {
                direction: nearest_scale(vanilla.default_composites[direction], 4)
                for direction in DIRECTIONS
            }
        comparison_rows.append((recipe["archetype"], baseline_label, baseline, render.default_frames))

        shirt_dir = PACK / "Shirts" / "".join(part.title() for part in slug.split("_"))
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(render, display_name))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)
        pack_names.append(display_name)
        validation["garments"].append({
            "recipeId": recipe_id,
            "name": display_name,
            "archetype": recipe["archetype"],
            "rarity": recipe["rarity"],
            "sideTemplate": render.side_template,
            "activeMainRoles": list(render.active_main_roles),
            "diagnostics": {
                "passes": diagnostics.passes,
                "errors": list(diagnostics.errors),
                "warnings": list(diagnostics.warnings),
                "metrics": diagnostics.metrics,
            },
            "baseline": "previous Fashion Sense POLISHED_HD" if recipe["archetype"] == "JACKET" else "vanilla V2 because no prior FS render existed",
        })

    write_rgba_png(COMPARISON, _main_comparison(comparison_rows))
    _json(OUTPUT / "validation.json", validation)
    _json(OUTPUT / "selected_recipes.json", {
        "source": str(RECIPE_BATCH.relative_to(ROOT)),
        "semanticRecipesUnchanged": True,
        "recipes": [recipes[item[0]] for item in SELECTED],
    })
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing HD Art Grammar V2 Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Test-only Fashion Sense pack for the permanent four-archetype HD art grammar control set.",
        "UniqueID": "RNGClothing.FashionSense.HDArtGrammarV2Test",
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    (PACK / "README.md").write_text(_readme(pack_names), encoding="utf-8")
    print(f"Generated permanent FS art grammar set at {OUTPUT}")
    print(f"Generated exact-footprint comparison at {COMPARISON}")
    print(f"Generated isolated test pack at {PACK}")


if __name__ == "__main__":
    main()
