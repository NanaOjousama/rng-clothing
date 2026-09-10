#!/usr/bin/env python3
"""Generate the controlled A/B/C Fashion Sense HD jacket art comparison."""

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
    encode_rgba_png,
    nearest_scale,
    text_width,
    write_rgba_png,
)
from generator.renderers.fashionsense import (
    composite_art_default_frame,
    composite_default_frame,
    render_hd_art_treatment,
)


RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
CURRENT_POC = ROOT / "output" / "fashionsense" / "poc_hd_jacket" / "mistral_lapel_layer_jacket_hd.png"
OUTPUT = ROOT / "output" / "fashionsense" / "art-grammar-test"
COMPARISON = ROOT / "output" / "comparisons" / "FS_ART_GRAMMAR_A_B_C.png"
GAMEPLAY_COMPARISON = ROOT / "output" / "comparisons" / "FS_ART_GRAMMAR_GAMEPLAY_SIZE.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Art-Grammar-Test"

TREATMENTS = (
    ("CURRENT", "A_CURRENT", "Mistral Current"),
    ("STRONGER_STARDEW", "B_STRONGER_STARDEW", "Mistral Stronger Stardew"),
    ("POLISHED_HD", "C_POLISHED_HD", "Mistral Polished HD"),
)
DIRECTIONS = ("front", "back", "left", "right")
BACKGROUND: RGBA = (236, 226, 211, 255)
INK: RGBA = (61, 55, 51, 255)
BORDER: RGBA = (91, 83, 75, 255)
FRAME_BACK: RGBA = (215, 207, 194, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_recipe() -> dict[str, Any]:
    batch = json.loads(RECIPE_BATCH.read_text(encoding="utf-8"))
    return next(recipe for recipe in batch["recipes"] if recipe["id"] == "lifestyle-v2-16")


def _default_frames(rendered):
    if rendered.name == "CURRENT":
        return {
            direction: composite_default_frame(frame, rendered.backend_config)
            for direction, frame in rendered.frames.items()
        }
    return {
        direction: composite_art_default_frame(frame, rendered.art_config)
        for direction, frame in rendered.frames.items()
    }


def _stack(frames):
    result = blank_image(16, 64)
    for index, direction in enumerate(("front", "right", "left", "back")):
        for y, row in enumerate(frames[direction]):
            result[index * 16 + y] = list(row)
    return result


def _bordered_blit(destination, source, x, y):
    draw_rect(destination, x - 2, y - 2, len(source[0]) + 4, len(source) + 4, BORDER)
    draw_rect(destination, x - 1, y - 1, len(source[0]) + 2, len(source) + 2, FRAME_BACK)
    blit(destination, source, x, y)


def _direction_contact(title: str, frames) -> list[list[RGBA]]:
    scale = 8
    size = 16 * scale
    gap = 22
    margin = 18
    width = margin * 2 + size * 4 + gap * 3
    height = 38 + size + 18
    canvas = blank_image(width, height, BACKGROUND)
    draw_text(canvas, title.upper(), (width - text_width(title.upper())) // 2, 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        draw_text(canvas, direction.upper(), x + (size - text_width(direction.upper())) // 2, 23, color=INK)
        _bordered_blit(canvas, nearest_scale(frames[direction], scale), x, 36)
    return canvas


def _comparison(all_frames) -> list[list[RGBA]]:
    scale = 4
    size = 16 * scale
    column_gap = 30
    row_gap = 23
    left = 76
    top = 72
    width = left + size * 3 + column_gap * 2 + 22
    height = top + size * 4 + row_gap * 3 + 24
    canvas = blank_image(width, height, BACKGROUND)
    title = "FS HD ART GRAMMAR A B C"
    draw_text(canvas, title, (width - text_width(title)) // 2, 8, color=INK)
    draw_text(canvas, "SAME RECIPE  16X16  SCALE 2  BODYPOSITION 0 32", 18, 25, color=INK)
    draw_text(canvas, "EQUAL 32X32 GAME FOOTPRINT  SHOWN AT 2X GAMEPLAY", 18, 39, color=INK)
    headings = ("A CURRENT", "B STRONGER", "C POLISHED")
    for column, heading in enumerate(headings):
        x = left + column * (size + column_gap)
        draw_text(canvas, heading, x + (size - text_width(heading)) // 2, 57, color=INK)
    for row_index, direction in enumerate(DIRECTIONS):
        y = top + row_index * (size + row_gap)
        draw_text(canvas, direction.upper(), 12, y + size // 2 - 4, color=INK)
        for column, key in enumerate(("CURRENT", "STRONGER_STARDEW", "POLISHED_HD")):
            x = left + column * (size + column_gap)
            _bordered_blit(canvas, nearest_scale(all_frames[key][direction], scale), x, y)
    return canvas


def _gameplay_comparison(all_frames) -> list[list[RGBA]]:
    """Exact Scale-2 shirt footprint, without an additional review zoom."""
    scale = 2
    size = 16 * scale
    column_gap = 22
    row_gap = 16
    left = 64
    top = 58
    width = left + size * 3 + column_gap * 2 + 18
    height = top + size * 4 + row_gap * 3 + 18
    canvas = blank_image(width, height, BACKGROUND)
    title = "FS ART GRAMMAR NORMAL GAME SIZE"
    draw_text(canvas, title, (width - text_width(title)) // 2, 8, color=INK)
    draw_text(canvas, "16X16 TIMES SCALE 2 EQUALS 32X32", 16, 24, color=INK)
    for column, heading in enumerate(("A", "B", "C")):
        x = left + column * (size + column_gap)
        draw_text(canvas, heading, x + (size - text_width(heading)) // 2, 43, color=INK)
    for row_index, direction in enumerate(DIRECTIONS):
        y = top + row_index * (size + row_gap)
        draw_text(canvas, direction.upper(), 8, y + size // 2 - 4, color=INK)
        for column, key in enumerate(("CURRENT", "STRONGER_STARDEW", "POLISHED_HD")):
            x = left + column * (size + column_gap)
            _bordered_blit(canvas, nearest_scale(all_frames[key][direction], scale), x, y)
    return canvas


def _shirt_model(rendered, y: int) -> dict[str, Any]:
    config = rendered.backend_config
    art = rendered.art_config
    values = [
        [value, value, value]
        for value in art["outerMaskRamp"].values()
    ]
    sleeves = [
        [art["outerMaskRamp"][role]] * 3
        for role in art["sleeveMaskRoles"]
    ]
    return {
        "Scale": config["scale"],
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Outer Fabric",
            "DefaultColor": art["defaultPrimaryColor"],
            "Values": values,
        }],
        "SleeveColors": sleeves,
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": config["bodyPosition"],
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(rendered, display_name: str, treatment: str) -> dict[str, Any]:
    return {
        "Name": display_name,
        "Format": "7.5.0",
        "Tags": ["Lifestyle", "Jacket", "Layered", "RNG Clothing", "Art Grammar Test", treatment],
        "FrontShirt": _shirt_model(rendered, 0),
        "RightShirt": _shirt_model(rendered, 16),
        "LeftShirt": _shirt_model(rendered, 32),
        "BackShirt": _shirt_model(rendered, 48),
    }


def _readme() -> str:
    return """# RNG Clothing — Fashion Sense HD Art Grammar Test

This isolated test pack contains only the B and C treatments of the same Mistral semantic recipe. It is for in-game art comparison and is not a production dependency.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0

## Install

Copy the whole `RNG-Clothing-HD-Art-Grammar-Test` folder into `Stardew Valley/Mods`, then fully restart SMAPI so it discovers the new manifest.

Expected path:

```text
Stardew Valley/Mods/RNG-Clothing-HD-Art-Grammar-Test/manifest.json
```

Fashion Sense itself must be installed separately. This pack contains no Fashion Sense binaries and does not require Content Patcher.

## Compare

1. Run `fs_add_mirror` in the SMAPI console if you need a Hand Mirror.
2. In the mirror's Shirts category, compare **Mistral Stronger Stardew** and **Mistral Polished HD**.
3. Keep the outer-fabric color near RGB `112, 130, 145` for the controlled comparison.
4. Judge at normal gameplay zoom in all four directions, walking, and basic tool poses.

Both shirts intentionally keep `ShirtSize 16x16`, `Scale 2`, `BodyPosition (0,32)`, native animated sleeves, and the same cool-neutral Rare jacket recipe. Only renderer-owned art grammar differs.
"""


def main() -> None:
    recipe = _load_recipe()
    rendered = {
        treatment: render_hd_art_treatment(recipe, treatment)
        for treatment, _, _ in TREATMENTS
    }
    if encode_rgba_png(rendered["CURRENT"].texture) != CURRENT_POC.read_bytes():
        raise ValueError("A CURRENT no longer matches the corrected runtime-tested POC")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    all_default_frames = {}
    for treatment, slug, _ in TREATMENTS:
        result = rendered[treatment]
        frames = _default_frames(result)
        all_default_frames[treatment] = frames
        stem = slug.lower()
        write_rgba_png(OUTPUT / f"{stem}.png", result.texture)
        write_rgba_png(OUTPUT / f"{stem}-native-8x.png", nearest_scale(result.texture, 8))
        write_rgba_png(OUTPUT / f"{stem}-default-8x.png", nearest_scale(_stack(frames), 8))
        write_rgba_png(OUTPUT / f"{stem}-directions-8x.png", _direction_contact(slug.replace("_", " "), frames))

    write_rgba_png(COMPARISON, _comparison(all_default_frames))
    write_rgba_png(GAMEPLAY_COMPARISON, _gameplay_comparison(all_default_frames))
    _json(OUTPUT / "semantic_recipe.json", recipe)
    _json(OUTPUT / "art_grammar.json", rendered["POLISHED_HD"].art_config)
    _json(OUTPUT / "runtime_contract.json", {
        "FashionSense": "7.5.0",
        "logicalFrame": [16, 16],
        "Scale": 2.0,
        "BodyPosition": [0, 32],
        "directionOrder": ["front", "right", "left", "back"],
        "nativeAnimatedSleeves": True,
        "semanticRecipeUnchanged": True,
    })

    for folder_name, treatment, display_name in (
        ("MistralStrongerStardew", "STRONGER_STARDEW", "Mistral Stronger Stardew"),
        ("MistralPolishedHD", "POLISHED_HD", "Mistral Polished HD"),
    ):
        folder = PACK / "Shirts" / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        _json(folder / "shirt.json", _shirt_json(rendered[treatment], display_name, treatment))
        write_rgba_png(folder / "shirt.png", rendered[treatment].texture)
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing HD Art Grammar Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Test-only in-game comparison of two art treatments for one Fashion Sense HD jacket recipe.",
        "UniqueID": "RNGClothing.FashionSense.HDArtGrammarTest",
        "UpdateKeys": [],
        "ContentPackFor": {
            "UniqueID": "PeacefulEnd.FashionSense",
            "MinimumVersion": "7.5.0"
        }
    })
    (PACK / "README.md").write_text(_readme(), encoding="utf-8")
    print(f"Generated A/B/C art test at {OUTPUT}")
    print(f"Generated B/C Fashion Sense test pack at {PACK}")
    print(f"Generated comparison at {COMPARISON}")


if __name__ == "__main__":
    main()
