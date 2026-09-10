#!/usr/bin/env python3
"""Analyze attached Fashion Sense packs as art-quality benchmarks.

Only aggregate visual metrics leave the reference folder. Benchmark pixels are
never consumed by the generator or emitted as generated garment assets.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png
from generator.renderers.fashionsense import (
    composite_art_default_frame,
    render_hd_art_treatment,
)


BENCHMARK = ROOT / "references" / "benchmark"
OUTPUT = ROOT / "output" / "fashionsense" / "benchmark-refinement" / "benchmark_metrics.json"
RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"

# Color variants are intentionally not repeated: the analysis should weight
# designs, not the number of recolors distributed by a pack.
REPRESENTATIVE_SHIRTS = (
    "[FS] Bonestealer Pack/Shirts/Bone Shirt",
    "[FS] Bonestealer Pack/Shirts/Meat Apron",
    "[FS] Bonestealer Pack/Shirts/Paralysis Suit",
    "[FS] Bonestealer Pack/Shirts/Paralysis Suit 2",
    "[FS] Bonestealer Pack/Shirts/Soul Cloak",
    "[FS] Layicn's Sino-Western Eclectic Style Outfits/Shirts/Changshan 01 - blue",
    "[FS] Layicn's Sino-Western Eclectic Style Outfits/Shirts/Changshan 02 - blue",
    "【FS】SubabyTvanZ's sailor suit Set/Shirts/SubabyTvanZ shirt 1",
    "【FS】SubabyTvanZ's sailor suit Set/Shirts/SubabyTvanZ shirt 2",
    "【FS】SubabyTvanZ's sailor suit Set/Shirts/SubabyTvanZ shirt 3",
    "【FS】SubabyTvanZ's sailor suit Set/Shirts/SubabyTvanZ shirt 4",
)

DIRECTIONS = (
    ("front", "FrontShirt"),
    ("right", "RightShirt"),
    ("left", "LeftShirt"),
    ("back", "BackShirt"),
)


def _load_relaxed_json(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    text = re.sub(r"//.*", "", text)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return json.loads(text)


def _luma(pixel) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


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


def _frame_metrics(frame):
    height = len(frame)
    width = len(frame[0])
    opaque = {
        (x, y)
        for y, row in enumerate(frame)
        for x, pixel in enumerate(row)
        if pixel[3] == 255
    }
    exterior = {
        (x, y)
        for x, y in opaque
        if any(
            nx < 0 or nx >= width or ny < 0 or ny >= height or (nx, ny) not in opaque
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
        )
    }
    colors = {frame[y][x] for x, y in opaque}
    lumas = sorted(_luma(frame[y][x]) for x, y in opaque)
    dark_cutoff = lumas[max(0, int(len(lumas) * 0.35) - 1)]
    dark = {(x, y) for x, y in opaque if _luma(frame[y][x]) <= dark_cutoff}

    same_color_singletons = 0
    color_component_sizes = []
    for color in colors:
        cells = {(x, y) for x, y in opaque if frame[y][x] == color}
        component_sizes = _components(cells)
        color_component_sizes.extend(component_sizes)
        same_color_singletons += component_sizes.count(1)

    counts = sorted(
        (sum(frame[y][x] == color for x, y in opaque) for color in colors),
        reverse=True,
    )
    return {
        "logicalSize": [width, height],
        "opaquePixels": len(opaque),
        "opaqueCoverageShare": round(len(opaque) / (width * height), 4),
        "opaqueComponents": _components(opaque),
        "opaqueColors": len(colors),
        "luminanceRange": round(max(lumas) - min(lumas), 3),
        "dark35ExteriorShare": round(len(dark & exterior) / max(1, len(dark)), 4),
        "exteriorDarkAnchorShare": round(len(dark & exterior) / max(1, len(exterior)), 4),
        "sameColorSingletonComponents": same_color_singletons,
        "sameColorSingletonShareOfOpaque": round(same_color_singletons / max(1, len(opaque)), 4),
        "medianColorClusterSize": statistics.median(color_component_sizes),
        "dominantColorShare": round(counts[0] / max(1, len(opaque)), 4),
    }


def _extract_frame(texture, model):
    start = model["StartingPosition"]
    size = model["ShirtSize"]
    return [
        row[start["X"] : start["X"] + size["Width"]]
        for row in texture[start["Y"] : start["Y"] + size["Length"]]
    ]


def _aggregate(records):
    metrics = [record["metrics"] for record in records]
    keys = (
        "opaqueColors",
        "luminanceRange",
        "dark35ExteriorShare",
        "exteriorDarkAnchorShare",
        "sameColorSingletonShareOfOpaque",
        "medianColorClusterSize",
        "dominantColorShare",
    )
    return {
        key: {
            "minimum": round(min(metric[key] for metric in metrics), 4),
            "median": round(statistics.median(metric[key] for metric in metrics), 4),
            "maximum": round(max(metric[key] for metric in metrics), 4),
        }
        for key in keys
    }


def main() -> None:
    records = []
    for relative in REPRESENTATIVE_SHIRTS:
        folder = BENCHMARK / relative
        metadata = _load_relaxed_json(folder / "shirt.json")
        texture = read_rgba_png(folder / "shirt.png")["pixels"]
        for direction, field in DIRECTIONS:
            records.append({
                "pack": relative.split("/", 1)[0],
                "appearance": metadata.get("Name", folder.name),
                "direction": direction,
                "metrics": _frame_metrics(_extract_frame(texture, metadata[field])),
            })

    recipe_batch = json.loads(RECIPE_BATCH.read_text(encoding="utf-8"))
    recipe = next(item for item in recipe_batch["recipes"] if item["id"] == "lifestyle-v2-16")
    current = render_hd_art_treatment(recipe, "POLISHED_HD")
    refined = render_hd_art_treatment(recipe, "BENCHMARK_REFINED")
    current_records = []
    refined_records = []
    for direction, _ in DIRECTIONS:
        frame = composite_art_default_frame(current.frames[direction], current.art_config)
        current_records.append({"direction": direction, "metrics": _frame_metrics(frame)})
        refined_frame = composite_art_default_frame(refined.frames[direction], refined.art_config)
        refined_records.append({"direction": direction, "metrics": _frame_metrics(refined_frame)})

    cape_inventory = []
    for path in sorted((BENCHMARK / "Sun Haven Cape Collection" / "Accessories").glob("*/accessory.json")):
        if "Colorable" in path.parent.name:
            continue
        metadata = _load_relaxed_json(path)
        front = metadata.get("FrontAccessory", {})
        cape_inventory.append({
            "name": metadata.get("Name", path.parent.name),
            "logicalFrame": list(front.get("AccessorySize", {}).values()),
            "scale": front.get("Scale"),
            "movementFrames": len(front.get("MovementAnimation", [])),
            "note": "Inventory/visual-study only; accessory geometry is not used by the shirt renderer.",
        })

    result = {
        "purpose": "Quality benchmark study only; no benchmark pixels or layouts feed generated assets.",
        "representativeShirtDesigns": len(REPRESENTATIVE_SHIRTS),
        "representativeShirtFrames": len(records),
        "benchmarkAggregate": _aggregate(records),
        "currentMistralPolishedHDAggregate": _aggregate(current_records),
        "benchmarkRefinedMistralAggregate": _aggregate(refined_records),
        "capeInventory": cape_inventory,
        "scopeNotes": [
            "Color variants were deduplicated so designs are weighted once.",
            "Bonestealer long shirts use 8x10/11 frames; the other sampled shirts use 8x8 frames.",
            "Sun Haven capes are 30-40 logical cells at Scale 2.5 and are not direct same-footprint shirt comparisons.",
            "Metrics identify grouping/contrast tendencies; aesthetic conclusions require visual inspection.",
        ],
        "records": records,
        "currentRecords": current_records,
        "refinedRecords": refined_records,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "benchmarkAggregate": result["benchmarkAggregate"],
        "currentMistralPolishedHDAggregate": result["currentMistralPolishedHDAggregate"],
        "benchmarkRefinedMistralAggregate": result["benchmarkRefinedMistralAggregate"],
        "capeInventory": result["capeInventory"],
    }, indent=2))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
