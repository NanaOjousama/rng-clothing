#!/usr/bin/env python3
"""Generate the exact six-garment AoTInspired Generator V3 test collection."""

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
from generator.v3 import load_v3_data
from generator.v3.style_profiles import (
    generate_aot_v3_collection, validate_aot_v3_collection, validate_aot_v3_renders,
)


OUTPUT = ROOT / "output" / "fashionsense" / "v3-style-aot"
RECIPES = ROOT / "output" / "recipes" / "aot_v3_collection.json"
FRONTS = ROOT / "output" / "comparisons" / "AOT_V3_COLLECTION_FRONTS_8X.png"
DIRECTIONS_OUT = ROOT / "output" / "comparisons" / "AOT_V3_COLLECTION_DIRECTIONS.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V3-AoT-Collection"
DIRECTIONS = ("front", "back", "left", "right")
BACKGROUND: RGBA = (232, 224, 211, 255)
FRAME_BACK: RGBA = (207, 199, 185, 255)
BORDER: RGBA = (74, 68, 62, 255)
INK: RGBA = (48, 44, 41, 255)

# These are stated profile targets. Final visual judgments are recorded in the report.
RECOGNITION_TARGETS = {
    "aot-v3-01": "LOW", "aot-v3-02": "MODERATE", "aot-v3-03": "MODERATE",
    "aot-v3-04": "MODERATE", "aot-v3-05": "STRONG", "aot-v3-06": "STRONG",
}

# Static equal-footprint review using the user-defined LOW/MODERATE/STRONG
# scale. Runtime review remains the final aesthetic boundary.
RECOGNITION_RATINGS = {
    "aot-v3-01": "LOW", "aot-v3-02": "MODERATE", "aot-v3-03": "MODERATE",
    "aot-v3-04": "MODERATE", "aot-v3-05": "STRONG", "aot-v3-06": "STRONG",
}

PROFILE_MOTIF_NAMES = {
    "aot-v3-04": "small_split_wing_shoulder_badge",
    "aot-v3-05": "modest_split_wing_regiment_crest",
}


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


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
    sprite = 16 * scale; gap = 18; margin = 16; top = 40
    canvas = blank_image(margin * 2 + sprite * 4 + gap * 3, top + sprite + 16, BACKGROUND)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 25, color=INK)
        _bordered_blit(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _flat_surface(render):
    story = load_v3_data()["palettes"]["stories"][render.recipe["paletteStory"]]
    colors = {
        "secondary": tuple(story["secondary"]) + (255,), "accent": tuple(story["accent"]) + (255,),
        "light_accent": tuple(story["lightAccent"]) + (255,), "dark_accent": tuple(story["darkAccent"]) + (255,),
    }
    result = {}
    for direction in DIRECTIONS:
        frame = blank_image(16, 16)
        for y in range(16):
            for x in range(16):
                if render.base.regions[direction][y][x] is not None:
                    frame[y][x] = colors.get(render.surface_roles[direction][y][x], (126, 122, 113, 255))
        result[direction] = frame
    return result


def _fronts(rendered):
    scale = 8; sprite = 128; cell_w = 220; cell_h = 172
    canvas = blank_image(cell_w * 2, cell_h * 3, BACKGROUND)
    for index, (recipe, render) in enumerate(rendered):
        col = index % 2; row = index // 2; x = col * cell_w + 12; y = row * cell_h + 34
        draw_text(canvas, f"{recipe['rarity'].upper()} {index + 1}", x, y - 25, color=INK)
        draw_text(canvas, recipe["itemName"], x, y - 13, color=INK)
        _bordered_blit(canvas, nearest_scale(render.default_frames["front"], scale), x, y)
        draw_text(canvas, RECOGNITION_TARGETS[recipe["id"]] + " TARGET", x + 140, y + 8, color=INK)
        draw_text(canvas, recipe["archetype"].replace("_", " "), x + 140, y + 22, color=INK)
        draw_text(canvas, recipe["surfaceDesign"]["compositionType"].replace("_", " "), x + 140, y + 36, color=INK)
    return canvas


def _directions_comparison(rendered):
    sprite = 32; label_w = 176; gap = 18; top = 42; row_h = 48
    canvas = blank_image(label_w + sprite * 4 + gap * 3 + 20, top + row_h * 6 + 12, BACKGROUND)
    draw_text(canvas, "AOT V3 COLLECTION - EXACT GAMEPLAY FOOTPRINT", 8, 7, color=INK)
    draw_text(canvas, "COMMON / COMMON / UNCOMMON / UNCOMMON / RARE / RARE", 8, 20, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = label_w + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 31, color=INK)
    for row, (recipe, render) in enumerate(rendered):
        y = top + row * row_h
        draw_text(canvas, f"{row + 1} {recipe['rarity'].upper()}", 6, y + 5, color=INK)
        draw_text(canvas, recipe["itemName"], 6, y + 18, color=INK)
        draw_text(canvas, RECOGNITION_TARGETS[recipe["id"]] + " RECOGNITION TARGET", 6, y + 31, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = label_w + index * (sprite + gap)
            _bordered_blit(canvas, nearest_scale(render.default_frames[direction], 2), x, y)
    return canvas


def _shirt_model(render, y: int) -> dict[str, Any]:
    config = render.base.config; base_recipe = render.base.recipe
    palette = load_v2_data()["palettes"]["families"][base_recipe["paletteFamily"]]
    return {
        "Scale": 2.0, "HideSleeves": False, "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Primary Fabric", "DefaultColor": palette["defaultDye"],
            "Values": [[config["outerMaskRamp"][role]] * 3 for role in render.base.active_main_roles],
        }],
        "SleeveColors": [[config["outerMaskRamp"][role]] * 3 for role in config["sleeveMaskRoles"]],
        "StartingPosition": {"X": 0, "Y": y}, "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe, render) -> dict[str, Any]:
    model = lambda y: _shirt_model(render, y)
    return {
        "Name": recipe["itemName"], "Format": "7.5.0",
        "Tags": ["Lifestyle", "AoT Inspired", recipe["archetype"].replace("_", " ").title(), recipe["rarity"], "RNG Clothing", "Generator V3", "Test"],
        "FrontShirt": model(0), "RightShirt": model(16), "LeftShirt": model(32), "BackShirt": model(48),
    }


def _readme(recipes: list[dict[str, Any]]) -> str:
    garments = "\n".join(
        f"{index}. **{recipe['itemName']}** — {recipe['rarity']}; recognition target: {RECOGNITION_TARGETS[recipe['id']]}"
        for index, recipe in enumerate(recipes, 1)
    )
    return f"""# RNG Clothing V3 — AoT-Inspired Collection Test

This isolated Fashion Sense research pack contains exactly six original garments generated by the frozen Generator V3 architecture through its curated `AoTInspired` profile. It contains no logos, insignia, character names, or copied reference pixels.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the entire `RNG-Clothing-V3-AoT-Collection` folder into `Stardew Valley/Mods`, then fully restart SMAPI.

Expected path:

```text
Stardew Valley/Mods/RNG-Clothing-V3-AoT-Collection/manifest.json
```

Run `fs_add_mirror` in the SMAPI console if you need a Hand Mirror. Use the mirror, open Fashion Sense's Shirts category, and select each garment. Check front/back/left/right while standing and walking, then basic tools and horse mounting.

## Garments

{garments}

All garments use 16x16 logical frames, Scale 2, BodyPosition `(0,32)`, and native animated `SleeveColors`. This pack is test-only, is not installed automatically, and is not reward-system content.
"""


def main() -> None:
    collection = generate_aot_v3_collection()
    semantic = validate_aot_v3_collection(collection)
    recipes = collection["recipes"]
    renders = [render_fs_v3(recipe) for recipe in recipes]
    diagnostics = [diagnose_fs_v3(render) for render in renders]
    rendered_gate = validate_aot_v3_renders(collection, renders, diagnostics)
    if not semantic.passes or not rendered_gate.passes:
        messages = list(semantic.errors) + list(rendered_gate.errors)
        raise ValueError("AoT V3 collection failed: " + "; ".join(messages))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    _json(RECIPES, collection)
    rendered = []
    concepts = {concept["id"]: concept for concept in collection["designConcepts"]}
    for recipe, render, diagnostic in zip(recipes, renders, diagnostics):
        slug = _slug(recipe["itemName"]); rendered.append((recipe, render))
        write_rgba_png(OUTPUT / f"{slug}.png", render.texture)
        write_rgba_png(OUTPUT / f"{slug}-default-8x.png", nearest_scale(_stack(render.default_frames), 8))
        write_rgba_png(OUTPUT / f"{slug}-directions-8x.png", _direction_sheet(recipe["itemName"], render.default_frames, 8))
        write_rgba_png(OUTPUT / f"{slug}-gameplay-size.png", _direction_sheet(recipe["itemName"] + " - GAME SIZE", render.default_frames, 2))
        write_rgba_png(OUTPUT / f"{slug}-surface-flat-8x.png", _direction_sheet(recipe["itemName"] + " - SURFACE WITHOUT SHADING", _flat_surface(render), 8))
        _json(OUTPUT / f"{slug}-design-concept.json", concepts[recipe["id"]])
        _json(OUTPUT / f"{slug}-recipe.json", recipe)
        _json(OUTPUT / f"{slug}-surface-summary.json", {
            "id": recipe["id"], "name": recipe["itemName"], "rarity": recipe["rarity"],
            "recognitionTarget": RECOGNITION_TARGETS[recipe["id"]],
            "recognitionRating": RECOGNITION_RATINGS[recipe["id"]],
            "primaryDesignIdea": recipe["concept"]["primaryGesture"],
            "secondaryDesignIdea": recipe["concept"]["secondaryGesture"],
            "surfaceCompositionType": recipe["surfaceDesign"]["compositionType"],
            "profileMotif": PROFILE_MOTIF_NAMES.get(recipe["id"], "none"),
            "activeSurfaceSystems": diagnostic.metrics["activeSystems"],
            "directionalTopology": {
                "colorBlock": recipe["colorBlocking"]["topology"],
                "trim": recipe["surfaceDesign"]["trim"]["topology"],
                "motif": recipe["surfaceDesign"]["motif"]["topology"],
                "pattern": recipe["surfaceDesign"]["pattern"]["topology"],
            },
            "designInterestWithoutShading": diagnostic.metrics["designInterestWithoutShading"],
            "sideTemplate": render.base.side_template,
            "diagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics},
        })
        shirt_dir = PACK / "Shirts" / _folder(recipe["itemName"])
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)

    write_rgba_png(FRONTS, _fronts(rendered))
    write_rgba_png(DIRECTIONS_OUT, _directions_comparison(rendered))
    _json(OUTPUT / "validation.json", {
        "status": "PASS_STATIC_CONTRACT_RUNTIME_REVIEW_PENDING",
        "beautyClaim": "CRITICAL_STATIC_SELF_REVIEW_REQUIRED; AUTOMATION IS A GUARDRAIL ONLY",
        "runtimeContract": {"FashionSense": "7.5.0", "logicalFrame": [16, 16], "Scale": 2.0, "BodyPosition": [0, 32], "nativeAnimatedSleeves": True},
        "collection": {"errors": list(semantic.errors), "warnings": list(semantic.warnings), "metrics": semantic.metrics},
        "renderDiversity": {"errors": list(rendered_gate.errors), "warnings": list(rendered_gate.warnings), "metrics": rendered_gate.metrics},
        "garments": [{
            "id": recipe["id"], "name": recipe["itemName"], "rarity": recipe["rarity"],
            "recognitionTarget": RECOGNITION_TARGETS[recipe["id"]],
            "recognitionRating": RECOGNITION_RATINGS[recipe["id"]], "passes": diagnostic.passes,
            "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics,
        } for recipe, diagnostic in zip(recipes, diagnostics)],
    })
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing V3 AoT-Inspired Collection Test", "Author": "RNG Clothing Experiment", "Version": "1.0.0",
        "Description": "Test-only six-garment V3 external style-profile integration collection.",
        "UniqueID": "RNGClothing.FashionSense.V3AoTCollection", "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "i18n" / "default.json", {
        key: value for recipe in recipes for key, value in (
            (f"shirt.{recipe['id']}.name", recipe["itemName"]),
            (f"shirt.{recipe['id']}.description", recipe["itemDescription"]),
        )
    })
    (PACK / "README.md").write_text(_readme(recipes), encoding="utf-8")
    print(f"Generated exactly {len(recipes)} AoTInspired V3 garments at {OUTPUT}")
    print(f"Generated rarity-organized fronts at {FRONTS}")
    print(f"Generated exact-gameplay directions at {DIRECTIONS_OUT}")
    print(f"Generated isolated test pack at {PACK}")
    for warning in rendered_gate.warnings:
        print("WARNING:", warning)


if __name__ == "__main__":
    main()
