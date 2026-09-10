#!/usr/bin/env python3
"""Measure edge/cluster tendencies in representative installed vanilla shirts.

This research tool reads native 8x8 logical frames only. It does not export or
copy vanilla pixels into the Fashion Sense renderer.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png


INSTALLED_CONTENT = Path(
    "/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)"
)
SHIRT_SHEET = INSTALLED_CONTENT / "Characters" / "Farmer" / "shirts.png"
SHIRT_DATA = INSTALLED_CONTENT / "Data" / "Shirts.json"
OUTPUT = ROOT / "output" / "fashionsense" / "art-grammar-test" / "vanilla_edge_study.json"

DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}
SAMPLES = {
    "T_SHIRT": [1, 6, 128, 194, 200, 209],
    "SWEATER": [176, 177, 178, 198, 235, 301],
    "BUTTON_SHIRT": [29, 123, 140, 154, 248, 251],
    "JACKET": [18, 30, 137, 138, 155, 163, 211, 218, 231, 270, 271, 285],
    "SAILOR_TOP": [19, 239, 259, 261],
}


def srgb_luminance(pixel: tuple[int, int, int, int]) -> float:
    r, g, b, _ = pixel
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _origin(sprite_index: int) -> tuple[int, int]:
    return (sprite_index * 8) % 128, (sprite_index * 8 // 128) * 32


def _color(value: str | None) -> tuple[int, int, int]:
    return (255, 255, 255) if not value else tuple(int(c) for c in value.split())


def _composite(sheet, sprite_index: int, direction: str, dye):
    x0, y0 = _origin(sprite_index)
    y0 += DIRECTION_Y[direction]
    result = [[(0, 0, 0, 0) for _ in range(8)] for _ in range(8)]
    for y in range(8):
        for x in range(8):
            base = sheet[y0 + y][x0 + x]
            mask = sheet[y0 + y][x0 + 128 + x]
            if base[3]:
                result[y][x] = base
            if mask[3]:
                result[y][x] = (
                    mask[0] * dye[0] // 255,
                    mask[1] * dye[1] // 255,
                    mask[2] * dye[2] // 255,
                    255,
                )
    return result


def _components(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    sizes = []
    while remaining:
        queue = deque([remaining.pop()])
        size = 0
        while queue:
            x, y = queue.popleft()
            size += 1
            for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if point in remaining:
                    remaining.remove(point)
                    queue.append(point)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _metrics(frame):
    occupied = {
        (x, y)
        for y, row in enumerate(frame)
        for x, pixel in enumerate(row)
        if pixel[3] == 255
    }
    exterior = {
        (x, y)
        for x, y in occupied
        if any(
            nx < 0 or nx >= 8 or ny < 0 or ny >= 8 or (nx, ny) not in occupied
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
        )
    }
    interior = occupied - exterior
    colors = Counter(frame[y][x] for x, y in occupied)
    exterior_luma = [srgb_luminance(frame[y][x]) for x, y in exterior]
    interior_luma = [srgb_luminance(frame[y][x]) for x, y in interior]
    all_luma = sorted(srgb_luminance(frame[y][x]) for x, y in occupied)
    darkest_cutoff = all_luma[max(0, len(all_luma) // 4 - 1)]
    darkest = {(x, y) for x, y in occupied if srgb_luminance(frame[y][x]) <= darkest_cutoff}
    isolated = sum(
        not any((nx, ny) in occupied for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
        for x, y in occupied
    )
    return {
        "occupiedPixels": len(occupied),
        "meaningfulColors": len(colors),
        "connectedComponents": _components(occupied),
        "isolatedOpaquePixels": isolated,
        "exteriorPixelCount": len(exterior),
        "exteriorMedianLuminance": round(statistics.median(exterior_luma), 2),
        "interiorMedianLuminance": round(statistics.median(interior_luma), 2) if interior_luma else None,
        "exteriorMinusInteriorMedianLuminance": round(
            statistics.median(exterior_luma) - statistics.median(interior_luma), 2
        ) if interior_luma else None,
        "darkestQuartileOnExteriorShare": round(len(darkest & exterior) / max(1, len(darkest)), 3),
        "luminanceRange": round(max(all_luma) - min(all_luma), 2),
    }


def _aggregate(values):
    return {
        "minimum": round(min(values), 3),
        "median": round(statistics.median(values), 3),
        "maximum": round(max(values), 3),
    }


def main() -> None:
    if not SHIRT_SHEET.is_file() or not SHIRT_DATA.is_file():
        raise FileNotFoundError("installed Stardew 1.6.15 shirt assets are not unpacked")
    sheet = read_rgba_png(SHIRT_SHEET)
    if (sheet["width"], sheet["height"]) != (256, 608):
        raise ValueError("installed 1.6.15 shirt sheet dimensions changed")
    shirts = json.loads(SHIRT_DATA.read_text(encoding="utf-8"))
    by_sprite = {int(entry["SpriteIndex"]): entry for entry in shirts.values()}

    records = []
    for group, sprite_indices in SAMPLES.items():
        for sprite_index in sprite_indices:
            entry = by_sprite[sprite_index]
            dye = _color(entry.get("DefaultColor"))
            for direction in DIRECTION_Y:
                records.append({
                    "studyGroup": group,
                    "spriteIndex": sprite_index,
                    "direction": direction,
                    "metrics": _metrics(_composite(sheet["pixels"], sprite_index, direction, dye)),
                })

    metrics = [record["metrics"] for record in records]
    exterior_deltas = [
        metric["exteriorMinusInteriorMedianLuminance"]
        for metric in metrics
        if metric["exteriorMinusInteriorMedianLuminance"] is not None
    ]
    result = {
        "source": str(SHIRT_SHEET),
        "sourceDimensions": [256, 608],
        "gameVersion": "1.6.15",
        "sampleGarments": sum(len(values) for values in SAMPLES.values()),
        "sampleFrames": len(records),
        "sampleGroups": SAMPLES,
        "aggregate": {
            "occupiedPixels": _aggregate([m["occupiedPixels"] for m in metrics]),
            "meaningfulColors": _aggregate([m["meaningfulColors"] for m in metrics]),
            "luminanceRange": _aggregate([m["luminanceRange"] for m in metrics]),
            "exteriorMinusInteriorMedianLuminance": _aggregate(exterior_deltas),
            "darkestQuartileOnExteriorShare": _aggregate([m["darkestQuartileOnExteriorShare"] for m in metrics]),
            "isolatedOpaquePixels": _aggregate([m["isolatedOpaquePixels"] for m in metrics]),
            "singleConnectedGarmentFrameShare": round(
                sum(len(m["connectedComponents"]) == 1 for m in metrics) / len(metrics), 3
            ),
        },
        "interpretationBoundary": "Statistics describe tendencies, not mandatory per-frame rules. Multicolor motifs can make some exterior medians lighter.",
        "records": records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["aggregate"], indent=2))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
