#!/usr/bin/env python3
"""Author the single Juniper Trail Cardigan POC on Stardew's logical grid.

This is deliberately not a general clothing generator. Every visible source
pixel is encoded in the four 8x8 symbolic grids below. PNG output uses only
standard-library lossless encoding, and previews are read back from the native
PNG before integer nearest-neighbor enlargement.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output" / "vanilla"
PACK_DIR = (
    PROJECT_ROOT
    / "test-packs"
    / "vanilla"
    / "[CP] Juniper Trail Cardigan POC"
)
NATIVE_PATH = OUTPUT_DIR / "juniper_trail_cardigan.png"
PREVIEW_PATH = OUTPUT_DIR / "juniper_trail_cardigan-8x.png"
CONTACT_PATH = OUTPUT_DIR / "juniper_trail_cardigan-directions-8x.png"
PACK_ASSET_PATH = PACK_DIR / "assets" / "juniper_trail_cardigan.png"

SHEET_WIDTH = 256
SHEET_HEIGHT = 32
FRAME_SIZE = 8
MASK_X_OFFSET = 128
PREVIEW_SCALE = 8
DEFAULT_DYE = (85, 122, 94)

# Protected authored colors. The outer cardigan is absent from the base layer;
# it is supplied by the grayscale mask so it can be dyed cleanly.
BASE_COLORS = {
    "k": (64, 55, 46, 255),      # warm outline / cardigan opening
    "C": (242, 220, 173, 255),  # henley highlight
    "c": (199, 175, 131, 255),  # henley shadow
    "b": (214, 154, 70, 255),   # single brass closure
}

# These three values also occupy front x=0 at y=2,3,4 respectively. The
# installed 1.6.15 renderer samples those mask pixels for native sleeve colors.
MASK_COLORS = {
    "L": (235, 235, 235, 255),
    "M": (176, 176, 176, 255),
    "D": (104, 104, 104, 255),
}

TRANSPARENT = (0, 0, 0, 0)

# Main inspiration: references/lifestyle/lifestyle.jpg
# Broad traits only: relaxed open cardigan, light inner layer, waist length,
# long-sleeve impression, localized contrast at opening/cuffs, one closure cue.
FRAMES = {
    "front": (
        "..kCCk..",
        ".LkCCkL.",
        "LMkCCkML",
        "MMkcckMM",
        "DDkcbkDD",
        "DDkcckDD",
        "DMMkkMMD",
        ".DDMMDD.",
    ),
    "right": (
        "...kC...",
        "..LkCL..",
        ".LMkcML.",
        ".MMkcMM.",
        ".DMkbMD.",
        ".DMkcMDD",
        ".DMMkMDD",
        "..DDMDD.",
    ),
    "left": (),  # filled as an exact horizontal mirror of right below
    "back": (
        "..kCCk..",
        ".LkDDkL.",
        "LLMDDMLL",
        "MMDDDDMM",
        "DMMMMMMD",
        "DDMMMMDD",
        "DMMMMMMD",
        ".DDMMDD.",
    ),
}
FRAMES["left"] = tuple(row[::-1] for row in FRAMES["right"])

# Native 1.6 shirt order inside one 8x32 item block.
DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}


def validate_symbolic_frames() -> None:
    allowed = {".", *BASE_COLORS, *MASK_COLORS}
    for direction, rows in FRAMES.items():
        if len(rows) != FRAME_SIZE:
            raise ValueError(f"{direction}: expected 8 rows, got {len(rows)}")
        for row_index, row in enumerate(rows):
            if len(row) != FRAME_SIZE:
                raise ValueError(
                    f"{direction} row {row_index}: expected 8 cells, got {len(row)}"
                )
            unexpected = set(row) - allowed
            if unexpected:
                raise ValueError(f"{direction} row {row_index}: bad cells {unexpected}")


def blank_image(width: int, height: int, color=TRANSPARENT):
    return [[color for _ in range(width)] for _ in range(height)]


def make_native_sheet():
    validate_symbolic_frames()
    pixels = blank_image(SHEET_WIDTH, SHEET_HEIGHT)
    for direction, rows in FRAMES.items():
        y_offset = DIRECTION_Y[direction]
        for y, row in enumerate(rows):
            for x, symbol in enumerate(row):
                if symbol in BASE_COLORS:
                    pixels[y_offset + y][x] = BASE_COLORS[symbol]
                elif symbol in MASK_COLORS:
                    pixels[y_offset + y][MASK_X_OFFSET + x] = MASK_COLORS[symbol]
    return pixels


def png_chunk(name: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + name
        + payload
        + struct.pack(">I", zlib.crc32(name + payload) & 0xFFFFFFFF)
    )


def encode_rgba_png(pixels) -> bytes:
    height = len(pixels)
    width = len(pixels[0])
    scanlines = bytearray()
    for row in pixels:
        if len(row) != width:
            raise ValueError("ragged pixel rows")
        scanlines.append(0)  # PNG filter: None
        for pixel in row:
            scanlines.extend(pixel)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9))
        + png_chunk(b"IEND", b"")
    )


def write_rgba_png(path: Path, pixels) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_rgba_png(pixels))


def read_authored_rgba_png(path: Path):
    """Read our filter-0 RGBA PNG so previews demonstrably use the native file."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: invalid PNG signature")
    offset = 8
    width = height = None
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if (depth, color_type, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError(f"{path}: expected non-interlaced RGBA8")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError(f"{path}: missing IHDR")
    raw = zlib.decompress(bytes(compressed))
    stride = width * 4
    if len(raw) != height * (stride + 1):
        raise ValueError(f"{path}: unexpected decompressed length")
    pixels = []
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        if filter_type != 0:
            raise ValueError(f"{path}: preview source must use filter 0")
        row_bytes = raw[cursor : cursor + stride]
        cursor += stride
        pixels.append(
            [tuple(row_bytes[x : x + 4]) for x in range(0, stride, 4)]
        )
    return width, height, pixels


def nearest_scale(pixels, factor: int):
    scaled = []
    for row in pixels:
        enlarged_row = [pixel for pixel in row for _ in range(factor)]
        for _ in range(factor):
            scaled.append(list(enlarged_row))
    return scaled


def multiply_mask(mask, dye):
    return (
        mask[0] * dye[0] // 255,
        mask[1] * dye[1] // 255,
        mask[2] * dye[2] // 255,
        mask[3],
    )


def composite_direction(native_pixels, direction: str):
    y_offset = DIRECTION_Y[direction]
    result = blank_image(FRAME_SIZE, FRAME_SIZE)
    for y in range(FRAME_SIZE):
        for x in range(FRAME_SIZE):
            base = native_pixels[y_offset + y][x]
            mask = native_pixels[y_offset + y][MASK_X_OFFSET + x]
            if mask[3]:
                result[y][x] = multiply_mask(mask, DEFAULT_DYE)
            elif base[3]:
                result[y][x] = base
    return result


FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
}


def draw_rect(pixels, x0, y0, width, height, color):
    for y in range(y0, y0 + height):
        for x in range(x0, x0 + width):
            if 0 <= y < len(pixels) and 0 <= x < len(pixels[0]):
                pixels[y][x] = color


def draw_text(pixels, text, x0, y0, scale=2, color=(67, 56, 48, 255)):
    cursor = x0
    for char in text:
        glyph = FONT_5X7[char]
        for gy, row in enumerate(glyph):
            for gx, value in enumerate(row):
                if value == "1":
                    draw_rect(
                        pixels,
                        cursor + gx * scale,
                        y0 + gy * scale,
                        scale,
                        scale,
                        color,
                    )
        cursor += 6 * scale


def make_contact_sheet(native_pixels):
    width, height = 352, 112
    background = (235, 226, 214, 255)
    border = (101, 86, 73, 255)
    checker_a = (211, 201, 188, 255)
    checker_b = (191, 181, 169, 255)
    pixels = blank_image(width, height, background)
    order = ("front", "back", "left", "right")
    tile_size = FRAME_SIZE * PREVIEW_SCALE
    gap = 16
    start_x = 12
    tile_y = 36
    for index, direction in enumerate(order):
        x0 = start_x + index * (tile_size + gap)
        label = direction.upper()
        label_width = len(label) * 12 - 2
        draw_text(pixels, label, x0 + (tile_size - label_width) // 2, 10)
        draw_rect(pixels, x0 - 2, tile_y - 2, tile_size + 4, tile_size + 4, border)
        for logical_y in range(FRAME_SIZE):
            for logical_x in range(FRAME_SIZE):
                checker = checker_a if (logical_x + logical_y) % 2 == 0 else checker_b
                draw_rect(
                    pixels,
                    x0 + logical_x * PREVIEW_SCALE,
                    tile_y + logical_y * PREVIEW_SCALE,
                    PREVIEW_SCALE,
                    PREVIEW_SCALE,
                    checker,
                )
        composite = nearest_scale(composite_direction(native_pixels, direction), PREVIEW_SCALE)
        for y, row in enumerate(composite):
            for x, pixel in enumerate(row):
                if pixel[3]:
                    pixels[tile_y + y][x0 + x] = pixel
    return pixels


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PACK_ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)

    native = make_native_sheet()
    native_bytes = encode_rgba_png(native)
    NATIVE_PATH.write_bytes(native_bytes)
    PACK_ASSET_PATH.write_bytes(native_bytes)

    width, height, native_from_disk = read_authored_rgba_png(NATIVE_PATH)
    if (width, height) != (SHEET_WIDTH, SHEET_HEIGHT):
        raise ValueError("native PNG dimensions changed during encoding")

    write_rgba_png(PREVIEW_PATH, nearest_scale(native_from_disk, PREVIEW_SCALE))
    write_rgba_png(CONTACT_PATH, make_contact_sheet(native_from_disk))

    print(f"Wrote {NATIVE_PATH.relative_to(PROJECT_ROOT)} ({width}x{height})")
    print(
        f"Wrote {PREVIEW_PATH.relative_to(PROJECT_ROOT)} "
        f"({width * PREVIEW_SCALE}x{height * PREVIEW_SCALE}, nearest-neighbor)"
    )
    print(f"Wrote {CONTACT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Copied native bytes to {PACK_ASSET_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
