"""A PNG reader wide enough for real content-pack art.

`v5.pngio` reads what our own pipeline writes: 8-bit non-interlaced RGB/RGBA.
The source library also ships palette-indexed sprites at 1, 2 and 4 bits per
pixel (15 of 319 files), which that reader rejects outright.  Rejecting them
would silently drop assets from the catalog, so this handles the palette
colour type at every sub-byte depth, with tRNS transparency.

Everything is returned as straight RGBA rows, so downstream code never has to
know which encoding a source file happened to use.
"""
from __future__ import annotations

import struct
import zlib

import sys
sys.path.insert(0, "/run/media/deck/USD00/RNG_clothing")
from v5.pngio import read_rgba_png as _read_rgba


def _unfilter(raw: bytes, width: int, height: int, bpp: int, stride: int):
    out = bytearray()
    prev = bytearray(stride)
    pos = 0
    for _ in range(height):
        ft = raw[pos]; pos += 1
        line = bytearray(raw[pos:pos + stride]); pos += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise ValueError(f"unknown PNG filter {ft}")
        out += line
        prev = line
    return out


def read(path: str):
    """RGBA rows, whatever the file's colour type and bit depth."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", data[16:29])
    if ctype != 3:
        return _read_rgba(path)               # the common path, already solved
    if interlace:
        raise ValueError(f"{path}: interlaced palette PNGs are not supported")

    pos, idat, plte, trns = 8, bytearray(), None, b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if tag == b"IDAT":
            idat += body
        elif tag == b"PLTE":
            plte = body
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IEND":
            break
        pos += 12 + ln
    if plte is None:
        raise ValueError(f"{path}: palette PNG without PLTE")

    per_byte = 8 // depth
    stride = (w * depth + 7) // 8
    raw = _unfilter(zlib.decompress(bytes(idat)), w, h, 1, stride)
    mask = (1 << depth) - 1
    rows = []
    for y in range(h):
        line = raw[y * stride:(y + 1) * stride]
        row = []
        for x in range(w):
            byte = line[x // per_byte]
            shift = 8 - depth * (x % per_byte + 1)
            idx = (byte >> shift) & mask
            r, g, b = plte[idx * 3:idx * 3 + 3]
            a = trns[idx] if idx < len(trns) else 255
            row.append((r, g, b, a))
        rows.append(row)
    return rows
