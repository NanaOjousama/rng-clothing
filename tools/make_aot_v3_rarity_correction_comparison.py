#!/usr/bin/env python3
"""Build visual evidence for the AoT V3 rarity-art correction."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png
from generator.renderers.fashionsense import render_fs_v3
from generator.v3 import generate_benchmark_batch
from generator.v3.style_profiles import generate_aot_v3_collection


OLD = ROOT / "output" / "recipes" / "aot_v3_collection_pre_rarity_correction.json"
BEFORE_AFTER = ROOT / "output" / "comparisons" / "AOT_V3_RARITY_ART_BEFORE_AFTER.png"
BENCHMARK = ROOT / "output" / "comparisons" / "AOT_V3_RARITY_VS_V3_BENCHMARK.png"
DIRECTIONS = ("front", "back", "left", "right")
BACKGROUND: RGBA = (232, 224, 211, 255)
FRAME: RGBA = (203, 195, 182, 255)
BORDER: RGBA = (70, 64, 59, 255)
INK: RGBA = (46, 42, 39, 255)


def _boxed(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, FRAME)
    blit(canvas, sprite, x, y)


def _before_after(old_rendered, new_rendered):
    scale = 8; sprite = 128; label_w = 184; gap = 32; top = 38; row_h = 152
    canvas = blank_image(label_w + sprite * 2 + gap + 22, top + row_h * 6 + 10, BACKGROUND)
    draw_text(canvas, "AOT V3 RARITY ART CORRECTION - FRONTS AT 8X", 8, 7, color=INK)
    draw_text(canvas, "BEFORE", label_w + (sprite - text_width("BEFORE")) // 2, 24, color=INK)
    draw_text(canvas, "CORRECTED", label_w + sprite + gap + (sprite - text_width("CORRECTED")) // 2, 24, color=INK)
    for row, ((old_recipe, old), (new_recipe, new)) in enumerate(zip(old_rendered, new_rendered)):
        y = top + row * row_h
        draw_text(canvas, f"{new_recipe['rarity'].upper()} {row + 1}", 6, y + 8, color=INK)
        draw_text(canvas, new_recipe["itemName"], 6, y + 22, color=INK)
        draw_text(canvas, new_recipe["surfaceDesign"]["compositionType"].replace("_", " "), 6, y + 36, color=INK)
        _boxed(canvas, nearest_scale(old.default_frames["front"], scale), label_w, y)
        _boxed(canvas, nearest_scale(new.default_frames["front"], scale), label_w + sprite + gap, y)
    return canvas


def _benchmark_rows(benchmark_recipes, aot_recipes):
    representatives = {
        "Common": next(recipe for recipe in benchmark_recipes if recipe["id"] == "v3-benchmark-03"),
        "Uncommon": next(recipe for recipe in benchmark_recipes if recipe["id"] == "v3-benchmark-08"),
        "Rare": next(recipe for recipe in benchmark_recipes if recipe["id"] == "v3-benchmark-11"),
    }
    rows = []
    for rarity in ("Common", "Uncommon", "Rare"):
        rows.append(("V3 FLOOR", representatives[rarity], render_fs_v3(representatives[rarity])))
        rows.extend(("AOT PROFILE", recipe, render_fs_v3(recipe)) for recipe in aot_recipes if recipe["rarity"] == rarity)
    return rows


def _benchmark_sheet(rows):
    scale = 2; sprite = 32; label_w = 194; gap = 18; top = 42; row_h = 48
    canvas = blank_image(label_w + sprite * 4 + gap * 3 + 20, top + row_h * len(rows) + 10, BACKGROUND)
    draw_text(canvas, "AOT RARITY PROFILE VS GENERATOR V3 QUALITY FLOOR", 8, 7, color=INK)
    draw_text(canvas, "EXACT GAMEPLAY FOOTPRINT - AUTOMATION DOES NOT PROVE BEAUTY", 8, 20, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = label_w + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 31, color=INK)
    for row, (kind, recipe, render) in enumerate(rows):
        y = top + row * row_h
        draw_text(canvas, f"{recipe['rarity'].upper()} - {kind}", 6, y + 5, color=INK)
        draw_text(canvas, recipe["itemName"], 6, y + 19, color=INK)
        draw_text(canvas, recipe["surfaceDesign"]["compositionType"].replace("_", " "), 6, y + 33, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            _boxed(canvas, nearest_scale(render.default_frames[direction], scale), label_w + index * (sprite + gap), y)
    return canvas


def main() -> None:
    old_recipes = json.loads(OLD.read_text(encoding="utf-8"))["recipes"]
    new_recipes = generate_aot_v3_collection()["recipes"]
    old_rendered = [(recipe, render_fs_v3(recipe)) for recipe in old_recipes]
    new_rendered = [(recipe, render_fs_v3(recipe)) for recipe in new_recipes]
    write_rgba_png(BEFORE_AFTER, _before_after(old_rendered, new_rendered))
    benchmark_recipes = generate_benchmark_batch()["recipes"]
    write_rgba_png(BENCHMARK, _benchmark_sheet(_benchmark_rows(benchmark_recipes, new_recipes)))
    print(f"Wrote {BEFORE_AFTER}")
    print(f"Wrote {BENCHMARK}")


if __name__ == "__main__":
    main()
