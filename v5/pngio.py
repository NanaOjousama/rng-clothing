"""Dependency-free RGBA8 PNG helpers. Copied so v5 has no dependency on legacy packages."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

RGBA = tuple[int, int, int, int]
TRANSPARENT: RGBA = (0, 0, 0, 0)


def blank_image(width: int, height: int, color: RGBA = TRANSPARENT) -> list[list[RGBA]]:
    return [[color for _ in range(width)] for _ in range(height)]


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def encode_rgba_png(pixels: list[list[RGBA]]) -> bytes:
    height = len(pixels); width = len(pixels[0])
    scan = bytearray()
    for row in pixels:
        if len(row) != width:
            raise ValueError("ragged rows")
        scan.append(0)
        for p in row:
            if len(p) != 4 or any(not 0 <= c <= 255 for c in p):
                raise ValueError(f"bad pixel {p!r}")
            scan.extend(p)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", zlib.compress(bytes(scan), 9)) + _chunk(b"IEND", b"")


def write_rgba_png(path: Path, pixels: list[list[RGBA]]) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encode_rgba_png(pixels))


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def read_rgba_png(path: Path) -> list[list[RGBA]]:
    """Read a non-interlaced 8-bit RGB or RGBA PNG into rows of RGBA tuples."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    cursor, idat, width, height, channels = 8, bytearray(), None, None, 4
    while cursor < len(data):
        length = struct.unpack(">I", data[cursor:cursor + 4])[0]
        kind = data[cursor + 4:cursor + 8]; payload = data[cursor + 8:cursor + 8 + length]
        cursor += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", payload)
            if depth != 8 or interlace != 0 or ctype not in (2, 6):
                raise ValueError(f"{path}: expected non-interlaced 8-bit RGB/RGBA")
            channels = 4 if ctype == 6 else 3
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    raw = zlib.decompress(bytes(idat)); stride = width * channels
    rows: list[list[RGBA]] = []; prev = bytearray(stride); off = 0
    for _ in range(height):
        ftype = raw[off]; off += 1
        enc = raw[off:off + stride]; off += stride
        dec = bytearray(stride)
        for i, v in enumerate(enc):
            left = dec[i - channels] if i >= channels else 0
            up = prev[i]; ul = prev[i - channels] if i >= channels else 0
            pred = (0, left, up, (left + up) // 2, _paeth(left, up, ul))[ftype]
            dec[i] = (v + pred) & 0xFF
        if channels == 4:
            rows.append([tuple(dec[x:x + 4]) for x in range(0, stride, 4)])
        else:
            rows.append([(dec[x], dec[x + 1], dec[x + 2], 255) for x in range(0, stride, 3)])
        prev = dec
    return rows


def nearest_scale(pixels: list[list[RGBA]], factor: int) -> list[list[RGBA]]:
    if factor <= 0:
        raise ValueError("scale factor must be positive")
    out = []
    for row in pixels:
        big = [p for p in row for _ in range(factor)]
        for _ in range(factor):
            out.append(list(big))
    return out


def draw_rect(pixels, x0, y0, w, h, color) -> None:
    for y in range(y0, y0 + h):
        if 0 <= y < len(pixels):
            for x in range(x0, x0 + w):
                if 0 <= x < len(pixels[0]):
                    pixels[y][x] = color


def blit(dst, src, x0, y0) -> None:
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3] and 0 <= y0 + y < len(dst) and 0 <= x0 + x < len(dst[0]):
                dst[y0 + y][x0 + x] = p


def flip_h(pixels):
    return [list(reversed(row)) for row in pixels]


FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"), "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"), "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"), "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"), "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"), "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"), "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"), "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"), "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"), "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"), "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"), "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"), "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"), "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"), "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"), "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"), "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"), "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"), "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"), "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00000", "00100"), ":": ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"), ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"), "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
}


def draw_text(pixels, text: str, x0: int, y0: int, *, scale: int = 1, color: RGBA = (40, 38, 36, 255)) -> None:
    cursor = x0
    for ch in text.upper():
        glyph = FONT_5X7.get(ch)
        if glyph:
            for gy, row in enumerate(glyph):
                for gx, v in enumerate(row):
                    if v == "1":
                        draw_rect(pixels, cursor + gx * scale, y0 + gy * scale, scale, scale, color)
        cursor += 6 * scale
