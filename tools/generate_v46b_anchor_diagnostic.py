#!/usr/bin/env python3
"""Build a minimal Scale-2 Pants anchor probe outside the six-item test pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png


CONTRACT_PATH = ROOT / "generator" / "data" / "fashionsense" / "v46b" / "article_frame_contracts.json"
OUT = ROOT / "output" / "fashionsense" / "v46b-runtime-anchor-diagnostic" / "Pants" / "Scale2AnchorProbe"
SHEET = ROOT / "output" / "comparisons" / "V46B_RUNTIME_ANCHOR_DIAGNOSTIC.png"
FARMER = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
BG: RGBA = (229, 221, 208, 255)
TILE: RGBA = (199, 192, 181, 255)
INK: RGBA = (43, 39, 38, 255)
OUTLINE: RGBA = (36, 31, 32, 255)
WAIST: RGBA = (220, 55, 121, 255)
BODY: RGBA = (39, 172, 199, 255)
END: RGBA = (247, 193, 65, 255)
DIRECTIONS = ("front", "back", "right", "left")
SAMPLES = (
    ("FRONT STAND", "front", 0),
    ("RIGHT STAND", "right", 6),
    ("BACK STAND", "back", 12),
    ("LEFT STAND", "left", 6),
    ("FRONT WALK 1", "front", 1),
)


def cells(rows: list[dict]) -> set[tuple[int, int]]:
    return {(x, row["y"]) for row in rows for a, b in row["spans"] for x in range(a, b + 1)}


def neighbors(cell: tuple[int, int]):
    x, y = cell
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))


def marker_frame(entry: dict) -> list[list[RGBA]]:
    frame = blank_image(32, 64)
    envelope = cells(entry["highDensityEnvelope"])
    if not envelope:
        return frame
    top = entry["top"]
    end = min(entry["bottom"] - 4, top + 18)
    visible = {(x, y) for x, y in envelope if top <= y <= end}
    for x, y in visible:
        exterior = any(item not in visible for item in neighbors((x, y)))
        if exterior:
            color = OUTLINE
        elif y <= top + 2:
            color = WAIST
        elif y >= end - 2:
            color = END
        else:
            color = BODY
        frame[y][x] = color
    return frame


def place(texture: list[list[RGBA]], frame: list[list[RGBA]], index: int, block_y: int) -> None:
    x0 = (index % 6) * 32
    y0 = block_y + (index // 6) * 64
    for y, row in enumerate(frame):
        texture[y0 + y][x0:x0 + 32] = list(row)


def crop_farmer(pixels: list[list[RGBA]], index: int) -> list[list[RGBA]]:
    x0 = (index % 6) * 16
    y0 = (index // 6) * 32
    return [list(row[x0:x0 + 16]) for row in pixels[y0:y0 + 32]]


def flip(pixels: list[list[RGBA]]) -> list[list[RGBA]]:
    return [list(reversed(row)) for row in pixels]


def composite(farmer: list[list[RGBA]], frame: list[list[RGBA]], direction: str, index: int) -> list[list[RGBA]]:
    body_source = crop_farmer(farmer, index)
    garment_source = frame
    if direction == "left":
        body_source = flip(body_source)
        garment_source = flip(garment_source)
    body = nearest_scale(body_source, 4)
    garment = nearest_scale(garment_source, 2)
    # Correct target reproduces the official Pants four-display-pixel drop.
    blit(body, garment, 0, 4)
    return body


def appearance(contract: dict) -> dict:
    root = {"Name": "V4.6B Scale-2 Anchor Probe", "Format": "7.5.0", "Tags": ["RNG Clothing", "V4.6B", "Anchor Diagnostic"]}
    for direction in DIRECTIONS:
        root[direction.title() + "Pants"] = {
            "Scale": 2.0,
            "DisableNativeOffset": True,
            "DisableGrayscale": True,
            "StartingPosition": {"X": 0, "Y": contract["directionBlocks"][direction]},
            "BodyPosition": contract["bodyPosition"],
            "PantsSize": {"Width": 32, "Length": 64},
            "Flipped": contract["directionFlips"][direction],
            "HideWhileSwimming": True,
            "HideWhileWearingBathingSuit": True,
            "HideLegs": False,
            "HideShadow": False,
            "UniformAnimation": contract["uniformAnimation"][direction],
        }
    return root


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["bodyPosition"] == {"X": 0, "Y": 30}
    texture = blank_image(contract["frame"]["textureWidth"], contract["frame"]["textureHeight"])
    frames: dict[str, dict[int, list[list[RGBA]]]] = {}
    for direction in DIRECTIONS:
        frames[direction] = {}
        for index in range(126):
            frame = marker_frame(contract["frames"][str(index)])
            frames[direction][index] = frame
            place(texture, frame, index, contract["directionBlocks"][direction])

    OUT.mkdir(parents=True, exist_ok=True)
    write_rgba_png(OUT / "pants.png", texture)
    (OUT / "pants.json").write_text(json.dumps(appearance(contract), indent=2) + "\n", encoding="utf-8")

    farmer = read_rgba_png(FARMER)["pixels"]
    tile_w = 116
    canvas = blank_image(tile_w * len(SAMPLES) + 12, 213, BG)
    draw_text(canvas, "V4.6B SCALE-2 SHARED PANTS ANCHOR PROBE - BODYPOSITION 0,30", 7, 7, color=INK)
    draw_text(canvas, "MAGENTA WAIST | CYAN BODY | GOLD TERMINATION | STATIC SOURCE-CONTRACT RENDER", 7, 21, color=INK)
    for col, (label, direction, index) in enumerate(SAMPLES):
        x = 10 + col * tile_w
        draw_text(canvas, label, x, 39, color=INK)
        draw_text(canvas, f"SOURCE {index}", x, 52, color=INK)
        image = composite(farmer, frames[direction][index], direction, index)
        draw_rect(canvas, x - 2, 67, 68, 132, OUTLINE)
        draw_rect(canvas, x, 69, 64, 128, TILE)
        blit(canvas, image, x, 69)
    write_rgba_png(SHEET, canvas)

    old_y = 32 - (32 - 2) * 2
    corrected_y = 32 - (32 + 30) * 2
    source_y = 32 - (32 - 1) * 4
    (OUT / "anchor_math.json").write_text(json.dumps({
        "nativeFarmerOriginY": 32,
        "sourceContract": {"frame": [16, 32], "scale": 4, "bodyPositionY": -1, "topLeftRelativeY": source_y},
        "failedContract": {"frame": [32, 64], "scale": 2, "bodyPositionY": -2, "topLeftRelativeY": old_y, "displayErrorY": old_y - source_y},
        "correctedContract": {"frame": [32, 64], "scale": 2, "bodyPositionY": 30, "topLeftRelativeY": corrected_y, "displayErrorY": corrected_y - source_y},
        "runtimeStatus": "NOT_RETESTED",
    }, indent=2) + "\n", encoding="utf-8")
    print("Generated V4.6B shared Scale-2 anchor diagnostic")


if __name__ == "__main__":
    main()
