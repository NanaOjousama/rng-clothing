"""Debug-only neutral-flat annotation. Never consumed by a renderer/compiler."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any

from generator.png_utils import draw_rect, draw_text, write_rgba_png

from .data import ROOT
from .projector import DIRECTIONS

FLAT = ROOT / "RNG_Clothing_Codex_Architecture_Study_v2_1/REAL_TO_PIXEL_TRANSLATION_FLAT.png"
PANEL_X = {"front": 8, "right": 302, "back": 596, "left": 890}
VISIBILITY_COLORS = {
    "FULL": (38, 120, 78, 255), "COMPRESSED": (62, 116, 151, 255), "DEPTH_ONLY": (111, 84, 151, 255),
    "EDGE_ONLY": (166, 112, 45, 255), "OCCLUDED": (126, 126, 126, 255), "HIDDEN": (150, 150, 150, 255), "FORBIDDEN": (171, 60, 58, 255),
}


def _paeth(a: int, b: int, c: int) -> int:
    estimate = a + b - c
    distances = (abs(estimate - a), abs(estimate - b), abs(estimate - c))
    return (a, b, c)[distances.index(min(distances))]


def _read_rgb_flat(path: Path) -> list[list[tuple[int, int, int, int]]]:
    """Read the supplied non-interlaced RGB8 authoring flat locally.

    Garment PNG helpers remain strict RGBA8; this conversion is debug-only.
    """

    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: invalid PNG")
    cursor = 8
    compressed = bytearray()
    width = height = None
    while cursor < len(data):
        length = struct.unpack(">I", data[cursor:cursor + 4])[0]
        kind = data[cursor + 4:cursor + 8]
        payload = data[cursor + 8:cursor + 8 + length]
        cursor += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
            if (depth, color_type, interlace) != (8, 2, 0):
                raise ValueError(f"{path}: expected RGB8 authoring flat")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError(f"{path}: missing IHDR")
    raw = zlib.decompress(bytes(compressed))
    stride = width * 3
    previous = bytearray(stride)
    rows: list[list[tuple[int, int, int, int]]] = []
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        encoded = raw[offset:offset + stride]
        offset += stride
        decoded = bytearray(stride)
        for index, value in enumerate(encoded):
            left = decoded[index - 3] if index >= 3 else 0
            above = previous[index]
            upper_left = previous[index - 3] if index >= 3 else 0
            predictor = {
                0: 0,
                1: left,
                2: above,
                3: (left + above) // 2,
                4: _paeth(left, above, upper_left),
            }.get(filter_type)
            if predictor is None:
                raise ValueError(f"{path}: unsupported PNG filter {filter_type}")
            decoded[index] = (value + predictor) & 0xFF
        rows.append([(decoded[x], decoded[x + 1], decoded[x + 2], 255) for x in range(0, stride, 3)])
        previous = decoded
    return rows


def emit_semantic_flat(canonical: dict[str, Any], projections: dict[str, list[dict[str, Any]]], target: Path) -> None:
    pixels = _read_rgb_flat(FLAT)
    draw_rect(pixels, 0, 0, 1180, 26, (238, 234, 226, 255))
    draw_text(pixels, f"V3 DEBUG ONLY {canonical['identity']['family']} {canonical['designIntent']['id']}", 8, 8, color=(36, 35, 34, 255))
    for direction in DIRECTIONS:
        x = PANEL_X[direction]
        draw_rect(pixels, x, 500, 282, 252, (244, 241, 234, 255))
        draw_text(pixels, direction, x + 4, 506, color=(36, 35, 34, 255))
        y = 520
        for item in projections[direction]:
            color = VISIBILITY_COLORS[item["visibility"]]
            draw_rect(pixels, x + 4, y, 5, 7, color)
            label = f"{item['componentInstance']}-{item['visibility']} P{item['pixelPriority']}"[:43]
            draw_text(pixels, label, x + 13, y, color=color)
            continuity = item.get("continuityGroup") or "NONE"
            detail = f"A-{item['attachmentRegion'] or 'ROOT'} C-{continuity}"[:43]
            draw_text(pixels, detail, x + 13, y + 9, color=(70, 68, 64, 255))
            y += 21
    write_rgba_png(target, pixels)
