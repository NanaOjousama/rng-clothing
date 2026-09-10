#!/usr/bin/env python3
"""Measure a representative installed Stardew 1.6.15 shirt sample.

This is a research/verification tool, not the procedural renderer. It reads the
installed vanilla shirt sheet at its native logical resolution, composites the
base and dye-mask halves with each item's default color, and reports recurring
8x8 structure without copying any tile into generated assets.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from author_vanilla_shirt_poc import (  # noqa: E402
    TRANSPARENT,
    blank_image,
    nearest_scale,
    write_rgba_png,
)
from validate_vanilla_shirt_poc import read_png  # noqa: E402


VANILLA_ROOT = Path("/tmp/RNG_clothing_vanilla_assets")
SHIRT_SHEET = VANILLA_ROOT / "Characters" / "Farmer" / "shirts.png"
SHIRT_DATA = VANILLA_ROOT / "Data" / "Shirts.json"
CONTACT_PATH = Path("/tmp/RNG_clothing_vanilla_shirt_grammar_contact.png")
METRICS_PATH = Path("/tmp/RNG_clothing_vanilla_shirt_grammar_metrics.json")

DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}
DIRECTIONS = tuple(DIRECTION_Y)
SAMPLES = {
    "T_SHIRT": [1, 6, 128, 194, 200, 209],
    "SWEATER": [176, 177, 178, 198, 235, 301],
    "BUTTON_SHIRT": [29, 123, 140, 154, 248, 251],
    "JACKET": [18, 30, 137, 138, 155, 163, 211, 218, 231, 270, 271, 285],
    "SAILOR_TOP": [19, 239, 259, 261],
}


def luminance(pixel: tuple[int, int, int, int]) -> float:
    r, g, b, _ = pixel
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def multiply_mask(mask, dye):
    return (
        mask[0] * dye[0] // 255,
        mask[1] * dye[1] // 255,
        mask[2] * dye[2] // 255,
        mask[3],
    )


def parse_color(value):
    if not value:
        return 255, 255, 255
    values = tuple(int(channel) for channel in value.split())
    if len(values) != 3:
        raise ValueError(f"invalid DefaultColor: {value!r}")
    return values


def sprite_origin(sprite_index: int):
    return (sprite_index * 8) % 128, (sprite_index * 8 // 128) * 32


def extract_layers(sheet, sprite_index: int, direction: str):
    x0, y0 = sprite_origin(sprite_index)
    y0 += DIRECTION_Y[direction]
    base = [[sheet[y0 + y][x0 + x] for x in range(8)] for y in range(8)]
    mask = [[sheet[y0 + y][x0 + 128 + x] for x in range(8)] for y in range(8)]
    return base, mask


def composite(base, mask, dye):
    result = blank_image(8, 8)
    for y in range(8):
        for x in range(8):
            # Matches the renderer's base-then-mask draw order. Vanilla data
            # normally avoids overlap, but this keeps the observed contract.
            pixel = base[y][x]
            if pixel[3]:
                result[y][x] = pixel
            if mask[y][x][3]:
                result[y][x] = multiply_mask(mask[y][x], dye)
    return result


def connected_components(points):
    remaining = set(points)
    components = []
    while remaining:
        pending = [remaining.pop()]
        component = set(pending)
        while pending:
            x, y = pending.pop()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        components.append(component)
    return sorted((len(component) for component in components), reverse=True)


def frame_metrics(base, mask, rendered):
    occupied = {
        (x, y)
        for y, row in enumerate(rendered)
        for x, pixel in enumerate(row)
        if pixel[3]
    }
    colors = Counter(pixel for row in rendered for pixel in row if pixel[3])
    lumas = sorted({round(luminance(pixel), 2) for pixel in colors})
    if occupied:
        xs = [point[0] for point in occupied]
        ys = [point[1] for point in occupied]
        bbox = [min(xs), min(ys), max(xs), max(ys)]
    else:
        bbox = None
    isolated = 0
    for x, y in occupied:
        neighbors = {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)}
        isolated += not bool(occupied & neighbors)
    edge_points = {point for point in occupied if point[0] in (0, 7) or point[1] in (0, 7)}
    interior_points = occupied - edge_points
    edge_luma = statistics.fmean(luminance(rendered[y][x]) for x, y in edge_points) if edge_points else 0
    interior_luma = (
        statistics.fmean(luminance(rendered[y][x]) for x, y in interior_points)
        if interior_points
        else 0
    )
    return {
        "occupiedPixels": len(occupied),
        "bbox": bbox,
        "rowWidths": [sum(pixel[3] > 0 for pixel in row) for row in rendered],
        "basePixels": sum(pixel[3] > 0 for row in base for pixel in row),
        "maskPixels": sum(pixel[3] > 0 for row in mask for pixel in row),
        "baseMaskOverlap": sum(
            base[y][x][3] > 0 and mask[y][x][3] > 0
            for y in range(8)
            for x in range(8)
        ),
        "meaningfulColors": len(colors),
        "luminanceRange": round((lumas[-1] - lumas[0]) if lumas else 0, 2),
        "edgeMinusInteriorLuminance": round(edge_luma - interior_luma, 2),
        "isolatedPixels": isolated,
        "componentSizes": connected_components(occupied),
    }


def add_checker(canvas, x0, y0, size=64):
    colors = ((211, 201, 188, 255), (191, 181, 169, 255))
    scale = size // 8
    for y in range(8):
        for x in range(8):
            color = colors[(x + y) % 2]
            for py in range(y0 + y * scale, y0 + (y + 1) * scale):
                for px in range(x0 + x * scale, x0 + (x + 1) * scale):
                    canvas[py][px] = color


def make_contact(rows):
    scale = 8
    tile = 8 * scale
    group_gap = 12
    sample_gap = 8
    direction_gap = 2
    margin = 10
    max_samples = max(len(samples) for samples in SAMPLES.values())
    sample_width = len(DIRECTIONS) * tile + (len(DIRECTIONS) - 1) * direction_gap
    width = margin * 2 + max_samples * sample_width + (max_samples - 1) * sample_gap
    height = margin * 2 + len(SAMPLES) * tile + (len(SAMPLES) - 1) * group_gap
    canvas = blank_image(width, height, (235, 226, 214, 255))
    for group_index, (_, samples) in enumerate(SAMPLES.items()):
        y0 = margin + group_index * (tile + group_gap)
        for sample_index, sprite_index in enumerate(samples):
            x_base = margin + sample_index * (sample_width + sample_gap)
            for direction_index, direction in enumerate(DIRECTIONS):
                x0 = x_base + direction_index * (tile + direction_gap)
                add_checker(canvas, x0, y0, tile)
                frame = nearest_scale(rows[sprite_index][direction], scale)
                for y, row in enumerate(frame):
                    for x, pixel in enumerate(row):
                        if pixel[3]:
                            canvas[y0 + y][x0 + x] = pixel
    return canvas


def aggregate(values):
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def main():
    if not SHIRT_SHEET.exists() or not SHIRT_DATA.exists():
        raise SystemExit("Installed vanilla audit assets are missing from /tmp")
    sheet_info = read_png(SHIRT_SHEET)
    if (sheet_info["width"], sheet_info["height"]) != (256, 608):
        raise ValueError("unexpected installed vanilla shirt sheet dimensions")
    data = json.loads(SHIRT_DATA.read_text(encoding="utf-8"))
    by_sprite = {int(value["SpriteIndex"]): value for value in data.values()}
    rendered_rows = {}
    records = []
    for archetype, sprite_indices in SAMPLES.items():
        print(f"{archetype}: {sprite_indices}")
        for sprite_index in sprite_indices:
            item = by_sprite[sprite_index]
            dye = parse_color(item.get("DefaultColor"))
            rendered_rows[sprite_index] = {}
            direction_metrics = {}
            for direction in DIRECTIONS:
                base, mask = extract_layers(sheet_info["pixels"], sprite_index, direction)
                rendered = composite(base, mask, dye)
                rendered_rows[sprite_index][direction] = rendered
                direction_metrics[direction] = frame_metrics(base, mask, rendered)
            records.append(
                {
                    "archetypeStudyGroup": archetype,
                    "spriteIndex": sprite_index,
                    "name": item["Name"],
                    "canBeDyed": item["CanBeDyed"],
                    "hasSleeves": item["HasSleeves"],
                    "defaultColor": item.get("DefaultColor"),
                    "directions": direction_metrics,
                }
            )
    all_frames = [metrics for record in records for metrics in record["directions"].values()]
    summary = {
        "installedSheet": str(SHIRT_SHEET),
        "installedSheetDimensions": [sheet_info["width"], sheet_info["height"]],
        "sampleCount": len(records),
        "frameCount": len(all_frames),
        "sampleGroups": SAMPLES,
        "aggregate": {
            "occupiedPixels": aggregate([frame["occupiedPixels"] for frame in all_frames]),
            "meaningfulColors": aggregate([frame["meaningfulColors"] for frame in all_frames]),
            "luminanceRange": aggregate([frame["luminanceRange"] for frame in all_frames]),
            "isolatedPixels": aggregate([frame["isolatedPixels"] for frame in all_frames]),
            "baseMaskOverlap": aggregate([frame["baseMaskOverlap"] for frame in all_frames]),
        },
        "records": records,
    }
    METRICS_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_rgba_png(CONTACT_PATH, make_contact(rendered_rows))
    print(json.dumps(summary["aggregate"], indent=2))
    print(f"Wrote {METRICS_PATH}")
    print(f"Wrote {CONTACT_PATH}")


if __name__ == "__main__":
    main()
