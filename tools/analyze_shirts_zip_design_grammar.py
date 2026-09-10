#!/usr/bin/env python3
"""Inventory Shirts.zip as a design-variety benchmark corpus.

This tool emits aggregate measurements only. It never writes benchmark pixels
into generator data or generated garment assets.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png


ARCHIVE_CANDIDATES = (
    Path("/mnt/data/Shirts.zip"),
    ROOT / "references" / "benchmark" / "shirts.zip",
)
OUTPUT = ROOT / "output" / "analysis" / "shirts_zip_design_metrics.json"
DIRECTIONS = ("FrontShirt", "RightShirt", "LeftShirt", "BackShirt")


def _archive() -> Path:
    for path in ARCHIVE_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("Shirts.zip not found in /mnt/data or references/benchmark")


def _frame(texture, model):
    start = model["StartingPosition"]
    size = model["ShirtSize"]
    return [
        row[start["X"] : start["X"] + size["Width"]]
        for row in texture[start["Y"] : start["Y"] + size["Length"]]
    ]


def _luma(pixel) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


def _metrics(frame):
    h = len(frame); w = len(frame[0])
    opaque = [(x, y, frame[y][x]) for y in range(h) for x in range(w) if frame[y][x][3]]
    colors = Counter(pixel for _, _, pixel in opaque)
    if not opaque:
        return {"opaquePixels": 0, "opaqueColors": 0, "luminanceRange": 0, "symmetryShare": 1.0, "upperShare": 0, "middleShare": 0, "lowerShare": 0}
    lumas = [_luma(pixel) for _, _, pixel in opaque]
    symmetric = sum(
        (frame[y][x][3] > 0) == (frame[y][w - 1 - x][3] > 0)
        for y in range(h) for x in range((w + 1) // 2)
    )
    denom = h * ((w + 1) // 2)
    zones = [0, 0, 0]
    for _, y, _ in opaque:
        zones[min(2, y * 3 // h)] += 1
    return {
        "opaquePixels": len(opaque),
        "opaqueColors": len(colors),
        "luminanceRange": round(max(lumas) - min(lumas), 3),
        "dominantColorShare": round(max(colors.values()) / len(opaque), 4),
        "symmetryShare": round(symmetric / denom, 4),
        "upperShare": round(zones[0] / len(opaque), 4),
        "middleShare": round(zones[1] / len(opaque), 4),
        "lowerShare": round(zones[2] / len(opaque), 4),
    }


def _summary(values):
    return {"minimum": min(values), "median": round(statistics.median(values), 4), "maximum": max(values)}


def main() -> None:
    archive = _archive()
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    appearances = []
    with tempfile.TemporaryDirectory(prefix="rng-clothing-shirts-v3-") as temp:
        temp_path = Path(temp)
        with zipfile.ZipFile(archive) as source:
            source.extractall(temp_path)
        for metadata_path in sorted((temp_path / "shirts").glob("*/shirt.json")):
            metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
            texture_info = read_rgba_png(metadata_path.with_name("shirt.png"))
            direction_records = []
            for field in DIRECTIONS:
                model = metadata[field]
                frame = _frame(texture_info["pixels"], model)
                direction_records.append({
                    "direction": field.replace("Shirt", "").lower(),
                    "logicalSize": [model["ShirtSize"]["Width"], model["ShirtSize"]["Length"]],
                    "scale": model.get("Scale", 4),
                    "metrics": _metrics(frame),
                })
            appearances.append({"name": metadata.get("Name", metadata_path.parent.name), "folder": metadata_path.parent.name, "directions": direction_records})

    fronts = [item["directions"][0] for item in appearances]
    size_counts = Counter(tuple(item["logicalSize"]) for item in fronts)
    scales = Counter(str(item["scale"]) for item in fronts)
    compact = [item for item in fronts if item["logicalSize"][0] <= 16 and item["logicalSize"][1] <= 16]
    oversized = [item for item in fronts if item not in compact]
    explicit_names = [item["name"].lower() for item in appearances if not item["name"].lower().startswith("saljjakung_shirts_")]
    named_tokens = Counter(
        token for name in explicit_names for token in (
            "beach", "fire", "rabbit", "octopus", "cyber", "dream", "fairy", "flower", "hibiscus",
            "honey", "crystal", "machinery", "mirror", "rose", "puzzle", "heart", "spring", "cake",
            "sun", "witch", "wind",
        ) if token in name
    )
    result = {
        "purpose": "Aggregate design-variety study only; no benchmark pixel data feeds Generator V3.",
        "archiveUsed": str(archive),
        "archiveSha256": archive_hash,
        "appearanceCount": len(appearances),
        "directionFrameCount": len(appearances) * 4,
        "logicalSizeCounts": {f"{w}x{h}": count for (w, h), count in sorted(size_counts.items())},
        "scaleCounts": dict(sorted(scales.items())),
        "compactAppearanceCount": len(compact),
        "oversizedAppearanceCount": len(oversized),
        "compactFrontMetrics": {
            key: _summary([item["metrics"][key] for item in compact])
            for key in ("opaquePixels", "opaqueColors", "luminanceRange", "dominantColorShare", "symmetryShare")
        },
        "oversizedFrontMetrics": {
            key: _summary([item["metrics"][key] for item in oversized])
            for key in ("opaquePixels", "opaqueColors", "luminanceRange", "dominantColorShare", "symmetryShare")
        },
        "explicitNameThemeSignals": dict(named_tokens),
        "interpretationLimits": [
            "Names and pixel statistics do not prove semantic theme or beauty.",
            "The 58x80 definitions use a materially different footprint/anchor model and are composition references only.",
            "The analysis report's theme families come from visual inspection across the corpus, not automatic labels.",
        ],
        "appearances": appearances,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "archiveUsed", "archiveSha256", "appearanceCount", "directionFrameCount", "logicalSizeCounts",
        "scaleCounts", "compactAppearanceCount", "oversizedAppearanceCount", "compactFrontMetrics",
        "oversizedFrontMetrics", "explicitNameThemeSignals")}, indent=2))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
