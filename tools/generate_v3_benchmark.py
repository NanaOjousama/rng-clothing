#!/usr/bin/env python3
"""Generate the controlled twelve-garment Generator V3 benchmark and test pack."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import (
    RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png,
)
from generator.renderers.fashionsense import diagnose_fs_v3, render_fs_v3
from generator.v2_recipe_engine import load_v2_data
from generator.v3 import generate_benchmark_batch, load_v3_data
from generator.v3.validation import validate_v3_batch


OUTPUT = ROOT / "output" / "fashionsense" / "v3-benchmark"
RECIPE_OUTPUT = ROOT / "output" / "recipes" / "v3_benchmark_recipes.json"
COMPARISON = ROOT / "output" / "comparisons" / "V3_BENCHMARK_12WAY.png"
FRONTS = ROOT / "output" / "comparisons" / "V3_BENCHMARK_FRONTS_8X.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V3-Benchmark"
DIRECTIONS = ("front", "back", "left", "right")
BACKGROUND: RGBA = (236, 226, 211, 255)
INK: RGBA = (58, 52, 48, 255)
BORDER: RGBA = (91, 83, 75, 255)
FRAME_BACK: RGBA = (215, 207, 194, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(name: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def _folder(name: str) -> str:
    return "".join(part.title() for part in _slug(name).split("_"))


def _stack(frames):
    result = blank_image(16, 64)
    for index, direction in enumerate(("front", "right", "left", "back")):
        for y, row in enumerate(frames[direction]):
            result[index * 16 + y] = list(row)
    return result


def _bordered_blit(destination, source, x: int, y: int) -> None:
    draw_rect(destination, x - 2, y - 2, len(source[0]) + 4, len(source) + 4, BORDER)
    draw_rect(destination, x - 1, y - 1, len(source[0]) + 2, len(source) + 2, FRAME_BACK)
    blit(destination, source, x, y)


def _direction_sheet(title: str, frames, scale: int):
    size = 16 * scale; gap = 18; margin = 16; top = 38
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 16, BACKGROUND)
    draw_text(canvas, title, max(3, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        draw_text(canvas, direction, x + (size - text_width(direction)) // 2, 23, color=INK)
        _bordered_blit(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _flat_surface(render):
    base_color = (112, 116, 124, 255); result = {}
    data = load_v3_data(); story = data["palettes"]["stories"][render.recipe["paletteStory"]]
    role_color = {
        "secondary": tuple(story["secondary"]) + (255,), "accent": tuple(story["accent"]) + (255,),
        "light_accent": tuple(story["lightAccent"]) + (255,), "dark_accent": tuple(story["darkAccent"]) + (255,),
    }
    for direction in DIRECTIONS:
        frame = blank_image(16, 16)
        for y in range(16):
            for x in range(16):
                if render.base.regions[direction][y][x] is not None:
                    frame[y][x] = role_color.get(render.surface_roles[direction][y][x], base_color)
        result[direction] = frame
    return result


def _comparison(rendered):
    sprite = 32; label_width = 140; gap = 18; top = 48; row_height = 48
    width = label_width + sprite * 4 + gap * 3 + 20
    height = top + len(rendered) * row_height + 14
    canvas = blank_image(width, height, BACKGROUND)
    draw_text(canvas, "GENERATOR V3 - EXACT GAMEPLAY FOOTPRINT", 8, 7, color=INK)
    draw_text(canvas, "4 COMMON - 4 UNCOMMON - 4 RARE", 8, 20, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = label_width + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 34, color=INK)
    for row_index, (recipe, render) in enumerate(rendered):
        y = top + row_index * row_height
        draw_text(canvas, f"{row_index + 1:02d} {recipe['rarity'].upper()}", 6, y + 5, color=INK)
        draw_text(canvas, recipe["themeFamily"].replace("_", " ")[:20], 6, y + 18, color=INK)
        draw_text(canvas, recipe["surfaceDesign"]["compositionType"].replace("_", " ")[:20], 6, y + 31, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = label_width + index * (sprite + gap)
            _bordered_blit(canvas, nearest_scale(render.default_frames[direction], 2), x, y)
    return canvas


def _fronts(rendered):
    scale = 8; size = 128; cols = 4; rows = 3; gap = 22; cell_w = size + gap; cell_h = size + 34
    canvas = blank_image(cols * cell_w, rows * cell_h, BACKGROUND)
    for index, (recipe, render) in enumerate(rendered):
        x = (index % cols) * cell_w + 10; y = (index // cols) * cell_h + 24
        draw_text(canvas, f"{index + 1:02d} {recipe['rarity'].upper()}", x, y - 18, color=INK)
        _bordered_blit(canvas, nearest_scale(render.default_frames["front"], scale), x, y)
    return canvas


def _shirt_model(render, y: int) -> dict[str, Any]:
    config = render.base.config
    base_recipe = render.base.recipe
    palette = load_v2_data()["palettes"]["families"][base_recipe["paletteFamily"]]
    return {
        "Scale": 2.0,
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Primary Fabric",
            "DefaultColor": palette["defaultDye"],
            "Values": [[config["outerMaskRamp"][role]] * 3 for role in render.base.active_main_roles],
        }],
        "SleeveColors": [[config["outerMaskRamp"][role]] * 3 for role in config["sleeveMaskRoles"]],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe, render):
    return {
        "Name": recipe["itemName"], "Format": "7.5.0",
        "Tags": ["Lifestyle", recipe["themeFamily"].replace("_", " ").title(), recipe["archetype"].replace("_", " ").title(), recipe["rarity"], "RNG Clothing", "Generator V3", "Test"],
        "FrontShirt": _shirt_model(render, 0), "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32), "BackShirt": _shirt_model(render, 48),
    }


def _readme(rendered) -> str:
    garments = "\n".join(f"{i}. **{recipe['itemName']}** — {recipe['rarity']}, {recipe['themeFamily'].replace('_', ' ')}" for i, (recipe, _) in enumerate(rendered, 1))
    return f"""# RNG Clothing Generator V3 Benchmark

This isolated test-only Fashion Sense content pack contains twelve original garments generated through the V3 design-concept and surface-composition system.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the entire `RNG-Clothing-V3-Benchmark` folder into `Stardew Valley/Mods`, then fully restart SMAPI.

Expected path:

```text
Stardew Valley/Mods/RNG-Clothing-V3-Benchmark/manifest.json
```

Run `fs_add_mirror` if you need a Hand Mirror, then select the garments in Fashion Sense's Shirts category.

## Garments

{garments}

All garments use 16x16 logical frames, Scale 2, BodyPosition `(0,32)`, and native animated sleeve recoloring. This pack is not installed automatically and is not production reward content.
"""


def main() -> None:
    batch = generate_benchmark_batch(); recipes = batch["recipes"]
    renders = [render_fs_v3(recipe) for recipe in recipes]
    diagnostics = [diagnose_fs_v3(render) for render in renders]
    batch_validation = validate_v3_batch(recipes, renders, diagnostics)
    if not batch_validation.passes:
        raise ValueError("V3 batch validation failed: " + "; ".join(batch_validation.errors))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    _json(RECIPE_OUTPUT, batch)
    rendered = []
    for recipe, render, diagnostic in zip(recipes, renders, diagnostics):
        slug = _slug(recipe["itemName"]); rendered.append((recipe, render))
        write_rgba_png(OUTPUT / f"{slug}.png", render.texture)
        write_rgba_png(OUTPUT / f"{slug}-default-8x.png", nearest_scale(_stack(render.default_frames), 8))
        write_rgba_png(OUTPUT / f"{slug}-directions-8x.png", _direction_sheet(recipe["itemName"], render.default_frames, 8))
        write_rgba_png(OUTPUT / f"{slug}-directions-gameplay-2x.png", _direction_sheet(recipe["itemName"] + " GAME SIZE", render.default_frames, 2))
        write_rgba_png(OUTPUT / f"{slug}-surface-flat-8x.png", _direction_sheet(recipe["itemName"] + " NO SHADING", _flat_surface(render), 8))
        summary = {
            "recipe": recipe,
            "primaryDesignIdea": f"{recipe['surfaceDesign']['compositionType'].replace('_', ' ')} focused at {recipe['concept']['focalArea'].replace('_', ' ')}",
            "activeSurfaceSystems": diagnostic.metrics["activeSystems"],
            "directionalTopology": {
                "colorBlock": recipe["colorBlocking"]["topology"], "trim": recipe["surfaceDesign"]["trim"]["topology"],
                "motif": recipe["surfaceDesign"]["motif"]["topology"], "pattern": recipe["surfaceDesign"]["pattern"]["topology"],
            },
            "diagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics},
        }
        _json(OUTPUT / f"{slug}-recipe-summary.json", summary)
        shirt_dir = PACK / "Shirts" / _folder(recipe["itemName"])
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)

    write_rgba_png(COMPARISON, _comparison(rendered))
    write_rgba_png(FRONTS, _fronts(rendered))
    validation = {
        "status": "PASS_GENERATOR_V3_STATIC_CONTRACT",
        "beautyClaim": "STATIC_SELF_REVIEW_PASSED_RUNTIME_REVIEW_PENDING",
        "runtimeContract": {"FashionSense": "7.5.0", "logicalFrame": [16, 16], "Scale": 2.0, "BodyPosition": [0, 32], "nativeAnimatedSleeves": True},
        "batch": {"errors": list(batch_validation.errors), "warnings": list(batch_validation.warnings), "metrics": batch_validation.metrics},
        "garments": [{"id": recipe["id"], "name": recipe["itemName"], "rarity": recipe["rarity"], "themeFamily": recipe["themeFamily"], "diagnostics": {"passes": diag.passes, "errors": list(diag.errors), "warnings": list(diag.warnings), "metrics": diag.metrics}} for recipe, diag in zip(recipes, diagnostics)],
    }
    _json(OUTPUT / "validation.json", validation)
    _json(PACK / "manifest.json", {"Name": "RNG Clothing Generator V3 Benchmark", "Author": "RNG Clothing Experiment", "Version": "1.0.0", "Description": "Test-only Fashion Sense pack for the Generator V3 design-variety benchmark.", "UniqueID": "RNGClothing.FashionSense.GeneratorV3Benchmark", "UpdateKeys": [], "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}})
    _json(PACK / "i18n" / "default.json", {key: value for recipe in recipes for key, value in ((f"shirt.{_slug(recipe['itemName']).replace('_', '-')}.name", recipe["itemName"]), (f"shirt.{_slug(recipe['itemName']).replace('_', '-')}.description", recipe["itemDescription"]))})
    (PACK / "README.md").write_text(_readme(rendered), encoding="utf-8")
    print(f"Generated {len(rendered)} V3 garments at {OUTPUT}")
    print(f"Generated exact-footprint comparison at {COMPARISON}")
    print(f"Generated isolated test pack at {PACK}")


if __name__ == "__main__":
    main()
