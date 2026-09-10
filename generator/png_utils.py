"""Dependency-free RGBA8 PNG helpers for authoritative logical-pixel output."""

from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path
from typing import Iterable


RGBA = tuple[int, int, int, int]
TRANSPARENT: RGBA = (0, 0, 0, 0)


def blank_image(width: int, height: int, color: RGBA = TRANSPARENT) -> list[list[RGBA]]:
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    return [[color for _ in range(width)] for _ in range(height)]


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def encode_rgba_png(pixels: list[list[RGBA]]) -> bytes:
    height = len(pixels)
    if height == 0:
        raise ValueError("cannot encode an empty image")
    width = len(pixels[0])
    if width == 0:
        raise ValueError("cannot encode an empty row")
    scanlines = bytearray()
    for row in pixels:
        if len(row) != width:
            raise ValueError("ragged pixel rows")
        scanlines.append(0)
        for pixel in row:
            if len(pixel) != 4 or any(not 0 <= channel <= 255 for channel in pixel):
                raise ValueError(f"invalid RGBA pixel: {pixel!r}")
            scanlines.extend(pixel)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9))
        + png_chunk(b"IEND", b"")
    )


def write_rgba_png(path: Path, pixels: list[list[RGBA]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_rgba_png(pixels))


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_rgba_png(path: Path) -> dict:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: invalid PNG signature")
    cursor = 8
    idat = bytearray()
    width = height = None
    chunks: list[str] = []
    while cursor < len(data):
        if cursor + 12 > len(data):
            raise ValueError(f"{path}: truncated PNG chunk")
        length = struct.unpack(">I", data[cursor : cursor + 4])[0]
        kind = data[cursor + 4 : cursor + 8]
        payload = data[cursor + 8 : cursor + 8 + length]
        expected_crc = struct.unpack(">I", data[cursor + 8 + length : cursor + 12 + length])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise ValueError(f"{path}: bad {kind!r} CRC")
        cursor += 12 + length
        chunks.append(kind.decode("ascii"))
        if kind == b"IHDR":
            width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if (depth, color_type, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError(f"{path}: expected non-interlaced RGBA8")
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError(f"{path}: missing IHDR")
    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    if len(raw) != height * (stride + 1):
        raise ValueError(f"{path}: unexpected decompressed size")
    rows: list[list[RGBA]] = []
    filters: list[int] = []
    raw_cursor = 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = raw[raw_cursor]
        filters.append(filter_type)
        raw_cursor += 1
        encoded = raw[raw_cursor : raw_cursor + stride]
        raw_cursor += stride
        decoded = bytearray(stride)
        for index, value in enumerate(encoded):
            left = decoded[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                predictor = _paeth(left, above, upper_left)
            else:
                raise ValueError(f"{path}: unsupported PNG filter {filter_type}")
            decoded[index] = (value + predictor) & 0xFF
        rows.append([tuple(decoded[x : x + 4]) for x in range(0, stride, 4)])
        previous = decoded
    return {
        "width": width,
        "height": height,
        "pixels": rows,
        "filters": filters,
        "chunks": chunks,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def nearest_scale(pixels: list[list[RGBA]], factor: int) -> list[list[RGBA]]:
    if not isinstance(factor, int) or factor <= 0:
        raise ValueError("nearest-neighbor scale must be a positive integer")
    scaled: list[list[RGBA]] = []
    for row in pixels:
        enlarged = [pixel for pixel in row for _ in range(factor)]
        for _ in range(factor):
            scaled.append(list(enlarged))
    return scaled


def draw_rect(
    pixels: list[list[RGBA]], x0: int, y0: int, width: int, height: int, color: RGBA
) -> None:
    for y in range(y0, y0 + height):
        if not 0 <= y < len(pixels):
            continue
        for x in range(x0, x0 + width):
            if 0 <= x < len(pixels[0]):
                pixels[y][x] = color


def blit(
    destination: list[list[RGBA]],
    source: list[list[RGBA]],
    x0: int,
    y0: int,
    *,
    transparent: bool = True,
) -> None:
    for y, row in enumerate(source):
        for x, pixel in enumerate(row):
            if transparent and pixel[3] == 0:
                continue
            if 0 <= y0 + y < len(destination) and 0 <= x0 + x < len(destination[0]):
                destination[y0 + y][x0 + x] = pixel


FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
}


def text_width(text: str, scale: int = 1) -> int:
    return max(0, len(text) * 6 * scale - scale)


def draw_text(
    pixels: list[list[RGBA]],
    text: str,
    x0: int,
    y0: int,
    *,
    scale: int = 1,
    color: RGBA = (67, 56, 48, 255),
) -> None:
    cursor = x0
    for character in text.upper():
        glyph = FONT_5X7.get(character)
        if glyph is not None:
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


def unique_opaque_colors(pixels: Iterable[Iterable[RGBA]]) -> set[RGBA]:
    return {pixel for row in pixels for pixel in row if pixel[3]}

