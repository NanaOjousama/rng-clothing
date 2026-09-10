#!/usr/bin/env python3
"""Study installed Stardew 1.6.15 shirts as compact design grammar.

This is a research tool, never a generation input. It composites the native
base and dye halves at the real 8x8 logical resolution, measures reusable
design tendencies, and creates a labeled contact sheet for human inspection.
No vanilla pixels are copied into RNG Clothing renderer data.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator.png_utils import (
    RGBA,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    read_rgba_png,
    write_rgba_png,
)


INSTALLED = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley")
EXTRACTED = Path("/tmp/RNG_clothing_vanilla_assets")
SHEET = EXTRACTED / "Characters" / "Farmer" / "shirts.png"
DATA = EXTRACTED / "Data" / "Shirts.json"
OUT = ROOT / "output" / "research" / "v5c2"

DIRECTIONS = ("front", "right", "back", "left")
DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}

# The sample is deliberately broad and nameable. It includes early and 1.6-era
# examples and several members of each family instead of treating one sprite as
# the definition of an article.
SAMPLE_GROUPS: dict[str, list[int]] = {
    "EARLY ARTICLE SIGNALS": [0, 2, 10, 18, 19, 20],
    "JACKETS AND LAYERS": [30, 137, 138, 155, 163, 218],
    "VESTS AND WORKWEAR": [29, 157, 167, 172, 216, 217],
    "FORMAL AND BLOUSE": [35, 173, 183, 185, 197, 202],
    "KNIT AND HOODIE": [160, 161, 162, 178, 198, 301],
    "UNIFORM AND OUTER": [211, 213, 221, 239, 240, 260],
    "LATE VEST AND JACKET": [231, 242, 270, 271, 278, 285],
    "PATTERN AND MOTIF": [39, 186, 187, 200, 246, 298],
    "GRAPHIC AND RHYTHM": [192, 204, 222, 247, 272, 274],
}

BG: RGBA = (236, 227, 214, 255)
PANEL: RGBA = (207, 198, 186, 255)
PANEL_ALT: RGBA = (190, 182, 172, 255)
INK: RGBA = (55, 48, 43, 255)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _luma(pixel: RGBA) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


def _parse_color(value: str | None) -> tuple[int, int, int]:
    if not value:
        return 255, 255, 255
    result = tuple(int(channel) for channel in value.split())
    if len(result) != 3:
        raise ValueError(f"invalid vanilla DefaultColor {value!r}")
    return result


def _origin(index: int) -> tuple[int, int]:
    return index * 8 % 128, index * 8 // 128 * 32


def _extract(sheet: list[list[RGBA]], index: int, direction: str):
    x0, y0 = _origin(index)
    y0 += DIRECTION_Y[direction]
    base = [[sheet[y0 + y][x0 + x] for x in range(8)] for y in range(8)]
    dye = [[sheet[y0 + y][x0 + 128 + x] for x in range(8)] for y in range(8)]
    return base, dye


def _composite(base, mask, dye_color):
    frame = blank_image(8, 8)
    for y in range(8):
        for x in range(8):
            if base[y][x][3]:
                frame[y][x] = base[y][x]
            if mask[y][x][3]:
                pixel = mask[y][x]
                frame[y][x] = tuple(pixel[i] * dye_color[i] // 255 for i in range(3)) + (255,)
    return frame


def _components(points: set[tuple[int, int]]) -> list[int]:
    remaining = set(points)
    sizes = []
    while remaining:
        queue = deque([remaining.pop()])
        size = 0
        while queue:
            x, y = queue.popleft()
            size += 1
            for cell in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if cell in remaining:
                    remaining.remove(cell)
                    queue.append(cell)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _frame_metrics(frame, base, mask):
    occupied = {(x, y) for y, row in enumerate(frame) for x, p in enumerate(row) if p[3]}
    colors = Counter(p for row in frame for p in row if p[3])
    dominant = colors.most_common(1)[0][1] if colors else 0
    exterior = {
        (x, y)
        for x, y in occupied
        if any((nx, ny) not in occupied for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    }
    interior = occupied - exterior
    edge_luma = statistics.fmean(_luma(frame[y][x]) for x, y in exterior) if exterior else 0
    inner_luma = statistics.fmean(_luma(frame[y][x]) for x, y in interior) if interior else 0
    row_transitions = 0
    for row in frame:
        opaque = [p for p in row if p[3]]
        row_transitions += sum(a != b for a, b in zip(opaque, opaque[1:]))
    center_signal = sum(
        frame[y][x][3] and colors[frame[y][x]] < dominant
        for y in range(8)
        for x in (3, 4)
    )
    return {
        "opaqueCells": len(occupied),
        "opaqueColors": len(colors),
        "dominantShare": round(dominant / max(1, len(occupied)), 4),
        "luminanceRange": round(max(map(_luma, colors), default=0) - min(map(_luma, colors), default=0), 2),
        "edgeMinusInteriorLuminance": round(edge_luma - inner_luma, 2),
        "connectedComponents": _components(occupied),
        "rowColorTransitions": row_transitions,
        "centerSignalCells": center_signal,
        "baseCells": sum(p[3] > 0 for row in base for p in row),
        "dyeMaskCells": sum(p[3] > 0 for row in mask for p in row),
    }


def _alpha_symmetry(frame) -> float:
    matches = sum(bool(frame[y][x][3]) == bool(frame[y][7 - x][3]) for y in range(8) for x in range(8))
    return round(matches / 64, 4)


def _alpha_jaccard(a, b) -> float:
    left = {(x, y) for y, row in enumerate(a) for x, p in enumerate(row) if p[3]}
    right = {(x, y) for y, row in enumerate(b) for x, p in enumerate(row) if p[3]}
    return round(len(left & right) / max(1, len(left | right)), 4)


def _contact(records: list[dict], frames: dict[int, dict[str, list[list[RGBA]]]]):
    scale = 4
    tile = 8 * scale
    view_gap = 2
    sample_w = tile * 4 + view_gap * 3
    cell_w = sample_w + 12
    header_h = 50
    row_h = 78
    width = 10 + cell_w * 6
    height = header_h + row_h * len(SAMPLE_GROUPS) + 10
    canvas = blank_image(width, height, BG)
    draw_text(canvas, "INSTALLED STARDEW 1.6.15 CLOTHING DESIGN STUDY", 8, 7, color=INK)
    draw_text(canvas, "FRONT RIGHT BACK LEFT - NATIVE 8X8 SHIRT CELLS AT 4X", 8, 20, color=INK)
    draw_text(canvas, "RESEARCH ONLY - VANILLA PIXELS ARE NOT GENERATOR INPUT", 8, 33, color=INK)
    by_index = {record["spriteIndex"]: record for record in records}
    for group_row, (group, indices) in enumerate(SAMPLE_GROUPS.items()):
        y0 = header_h + group_row * row_h
        draw_text(canvas, group[:30], 8, y0, color=INK)
        for column, index in enumerate(indices):
            record = by_index[index]
            x0 = 8 + column * cell_w
            label = record["name"].upper().replace("'", "")[:20]
            draw_text(canvas, label, x0, y0 + 12, color=INK)
            for direction_index, direction in enumerate(DIRECTIONS):
                px = x0 + direction_index * (tile + view_gap)
                py = y0 + 25
                for y in range(tile):
                    for x in range(tile):
                        canvas[py + y][px + x] = PANEL if ((x // scale) + (y // scale)) % 2 == 0 else PANEL_ALT
                blit(canvas, nearest_scale(frames[index][direction], scale), px, py)
    return canvas


def _aggregate(values):
    return {
        "minimum": min(values),
        "median": statistics.median(values),
        "maximum": max(values),
    }


def main() -> None:
    installed_sheet = INSTALLED / "Content" / "Characters" / "Farmer" / "shirts.xnb"
    installed_data = INSTALLED / "Content" / "Data" / "Shirts.xnb"
    for path in (installed_sheet, installed_data, SHEET, DATA):
        if not path.exists():
            raise SystemExit(f"required installed/audit asset missing: {path}")
    sheet = read_rgba_png(SHEET)
    if (sheet["width"], sheet["height"]) != (256, 608):
        raise ValueError(f"unexpected installed shirt sheet {sheet['width']}x{sheet['height']}")
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_sprite = {int(value["SpriteIndex"]): value for value in data.values()}
    wanted = [index for indices in SAMPLE_GROUPS.values() for index in indices]
    records = []
    rendered: dict[int, dict[str, list[list[RGBA]]]] = {}
    for index in wanted:
        item = by_sprite[index]
        dye_color = _parse_color(item.get("DefaultColor"))
        rendered[index] = {}
        directions = {}
        for direction in DIRECTIONS:
            base, mask = _extract(sheet["pixels"], index, direction)
            frame = _composite(base, mask, dye_color)
            rendered[index][direction] = frame
            directions[direction] = _frame_metrics(frame, base, mask)
        records.append({
            "spriteIndex": index,
            "name": item["Name"],
            "canBeDyed": item["CanBeDyed"],
            "hasSleeves": item["HasSleeves"],
            "frontAlphaSymmetry": _alpha_symmetry(rendered[index]["front"]),
            "frontBackAlphaJaccard": _alpha_jaccard(rendered[index]["front"], rendered[index]["back"]),
            "directions": directions,
        })
    all_frames = [view for record in records for view in record["directions"].values()]
    summary = {
        "status": "INSTALLED_1_6_15_ASSET_STUDY",
        "authority": {
            "installedDataXnb": str(installed_data),
            "installedDataSha256": _sha(installed_data),
            "installedTextureXnb": str(installed_sheet),
            "installedTextureSha256": _sha(installed_sheet),
            "extractedTexture": str(SHEET),
            "extractedTextureSha256": sheet["sha256"],
            "sheetDimensions": [sheet["width"], sheet["height"]],
            "shirtDataEntries": len(data),
        },
        "sampleCount": len(records),
        "directionalFrameCount": len(all_frames),
        "sampleGroups": SAMPLE_GROUPS,
        "aggregate": {
            "opaqueCells": _aggregate([x["opaqueCells"] for x in all_frames]),
            "opaqueColors": _aggregate([x["opaqueColors"] for x in all_frames]),
            "luminanceRange": _aggregate([x["luminanceRange"] for x in all_frames]),
            "dominantShare": _aggregate([x["dominantShare"] for x in all_frames]),
            "rowColorTransitions": _aggregate([x["rowColorTransitions"] for x in all_frames]),
            "frontAlphaSymmetry": _aggregate([x["frontAlphaSymmetry"] for x in records]),
            "frontBackAlphaJaccard": _aggregate([x["frontBackAlphaJaccard"] for x in records]),
        },
        "records": records,
        "boundary": "Research only. Generated renderers do not read this sheet, data, metrics, or contact image.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vanilla_clothing_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_rgba_png(OUT / "VANILLA_CLOTHING_DESIGN_STUDY.png", _contact(records, rendered))
    print(json.dumps(summary["aggregate"], indent=2))
    print(OUT / "VANILLA_CLOTHING_DESIGN_STUDY.png")


if __name__ == "__main__":
    main()
