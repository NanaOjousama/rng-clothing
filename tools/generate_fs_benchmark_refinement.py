#!/usr/bin/env python3
"""Generate the controlled current-vs-benchmark-refined Mistral test."""

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
    render_hd_art_treatment,
)


RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
CURRENT_C = ROOT / "output" / "fashionsense" / "art-grammar-test" / "c_polished_hd.png"
OUTPUT = ROOT / "output" / "fashionsense" / "benchmark-refinement"
COMPARISON = ROOT / "output" / "comparisons" / "FS_MISTRAL_CURRENT_VS_BENCHMARK_REFINED.png"
GAMEPLAY = ROOT / "output" / "comparisons" / "FS_MISTRAL_CURRENT_VS_REFINED_GAMEPLAY_SIZE.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Benchmark-Refinement-Test"
SHIRT = PACK / "Shirts" / "MistralBenchmarkRefinedHD"

DIRECTIONS = ("front", "back", "left", "right")
STACK_ORDER = ("front", "right", "left", "back")
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
    return {
        direction: composite_art_default_frame(frame, rendered.art_config)
        for direction, frame in rendered.frames.items()
    }


def _stack(frames):
    result = blank_image(16, 64)
    for index, direction in enumerate(STACK_ORDER):
        for y, row in enumerate(frames[direction]):
            result[index * 16 + y] = list(row)
    return result


def _bordered_blit(destination, source, x, y):
    draw_rect(destination, x - 2, y - 2, len(source[0]) + 4, len(source) + 4, BORDER)
    draw_rect(destination, x - 1, y - 1, len(source[0]) + 2, len(source) + 2, FRAME_BACK)
    blit(destination, source, x, y)


def _comparison(current_frames, refined_frames, scale: int, title: str, subtitle: str):
    size = 16 * scale
    gap = 38 if scale == 4 else 24
    left = 78
    top = 62
    row_gap = 22 if scale == 4 else 14
    width = left + size * 2 + gap + 22
    height = top + size * 4 + row_gap * 3 + 24
    canvas = blank_image(width, height, BACKGROUND)
    draw_text(canvas, title, (width - text_width(title)) // 2, 8, color=INK)
    draw_text(canvas, subtitle, (width - text_width(subtitle)) // 2, 24, color=INK)
    headings = ("CURRENT C", "BENCHMARK REFINED") if scale >= 4 else ("CURRENT", "REFINED")
    for column, heading in enumerate(headings):
        x = left + column * (size + gap)
        draw_text(canvas, heading, x + (size - text_width(heading)) // 2, 46, color=INK)
    for row_index, direction in enumerate(DIRECTIONS):
        y = top + row_index * (size + row_gap)
        draw_text(canvas, direction.upper(), 10, y + size // 2 - 4, color=INK)
        _bordered_blit(canvas, nearest_scale(current_frames[direction], scale), left, y)
        _bordered_blit(canvas, nearest_scale(refined_frames[direction], scale), left + size + gap, y)
    return canvas


def _contact(title: str, frames):
    scale = 8
    size = 16 * scale
    gap = 22
    margin = 18
    width = margin * 2 + size * 4 + gap * 3
    height = 40 + size + 18
    canvas = blank_image(width, height, BACKGROUND)
    draw_text(canvas, title, (width - text_width(title)) // 2, 8, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = margin + index * (size + gap)
        draw_text(canvas, direction.upper(), x + (size - text_width(direction)) // 2, 25, color=INK)
        _bordered_blit(canvas, nearest_scale(frames[direction], scale), x, 38)
    return canvas


def _shirt_model(rendered, y: int):
    config = rendered.backend_config
    art = rendered.art_config
    values = [[value, value, value] for value in art["outerMaskRamp"].values()]
    sleeves = [[art["outerMaskRamp"][role]] * 3 for role in art["sleeveMaskRoles"]]
    return {
        "Scale": 2.0,
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


def _shirt_json(refined):
    return {
        "Name": "Mistral Benchmark-Refined HD",
        "Format": "7.5.0",
        "Tags": ["Lifestyle", "Jacket", "Layered", "RNG Clothing", "Benchmark Refinement", "Test"],
        "FrontShirt": _shirt_model(refined, 0),
        "RightShirt": _shirt_model(refined, 16),
        "LeftShirt": _shirt_model(refined, 32),
        "BackShirt": _shirt_model(refined, 48),
    }


def _readme():
    return """# RNG Clothing — FS Benchmark Refinement Test

This isolated test-only Fashion Sense pack contains one original Mistral jacket refinement. Attached community packs were studied only for general quality grammar; no benchmark artwork, layout, motif, palette, or outfit was copied into this asset.

## Requirements and installation

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

Copy the whole `RNG-Clothing-HD-Benchmark-Refinement-Test` folder into `Stardew Valley/Mods`, then fully restart SMAPI.

Expected path:

```text
Stardew Valley/Mods/RNG-Clothing-HD-Benchmark-Refinement-Test/manifest.json
```

## Test

Run `fs_add_mirror` if you need a Hand Mirror. In Shirts, select **Mistral Benchmark-Refined HD**. For the controlled palette comparison, keep Outer Fabric near RGB `(112,130,145)`.

The asset retains 16×16 frames, Scale 2, BodyPosition `(0,32)`, and native animated sleeve integration. Judge front/back/side while standing, walking, and using basic tools.
"""


def main() -> None:
    recipe = _load_recipe()
    current = render_hd_art_treatment(recipe, "POLISHED_HD")
    refined = render_hd_art_treatment(recipe, "BENCHMARK_REFINED")
    if encode_rgba_png(current.texture) != CURRENT_C.read_bytes():
        raise ValueError("controlled current C baseline drifted")

    current_frames = _default_frames(current)
    refined_frames = _default_frames(refined)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_rgba_png(OUTPUT / "current_polished_hd.png", current.texture)
    write_rgba_png(OUTPUT / "mistral_benchmark_refined_hd.png", refined.texture)
    write_rgba_png(OUTPUT / "current_polished_hd-default-8x.png", nearest_scale(_stack(current_frames), 8))
    write_rgba_png(OUTPUT / "mistral_benchmark_refined_hd-default-8x.png", nearest_scale(_stack(refined_frames), 8))
    write_rgba_png(OUTPUT / "mistral_benchmark_refined_hd-directions-8x.png", _contact("MISTRAL BENCHMARK REFINED HD", refined_frames))
    write_rgba_png(
        COMPARISON,
        _comparison(
            current_frames,
            refined_frames,
            4,
            "MISTRAL CURRENT VS BENCHMARK REFINED",
            "SAME RECIPE  16X16  SCALE 2  EQUAL FOOTPRINT",
        ),
    )
    write_rgba_png(
        GAMEPLAY,
        _comparison(
            current_frames,
            refined_frames,
            2,
            "MISTRAL NORMAL GAME SIZE",
            "AUTHORITATIVE 16X16 TIMES SCALE 2",
        ),
    )
    _json(OUTPUT / "semantic_recipe.json", recipe)
    _json(OUTPUT / "runtime_contract.json", {
        "FashionSense": "7.5.0",
        "logicalFrame": [16, 16],
        "Scale": 2.0,
        "BodyPosition": [0, 32],
        "nativeAnimatedSleeves": True,
        "semanticRecipeUnchanged": True,
        "benchmarkPixelsUsedByRenderer": False,
    })
    _json(OUTPUT / "applied_grammar.json", refined.art_config["benchmarkRefinement"])

    SHIRT.mkdir(parents=True, exist_ok=True)
    _json(SHIRT / "shirt.json", _shirt_json(refined))
    write_rgba_png(SHIRT / "shirt.png", refined.texture)
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing HD Benchmark Refinement Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Test-only Fashion Sense pack for one benchmark-informed original Mistral refinement.",
        "UniqueID": "RNGClothing.FashionSense.HDBenchmarkRefinementTest",
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    (PACK / "README.md").write_text(_readme(), encoding="utf-8")
    print(f"Generated benchmark refinement at {OUTPUT}")
    print(f"Generated comparison at {COMPARISON}")
    print(f"Generated isolated test pack at {PACK}")


if __name__ == "__main__":
    main()
