#!/usr/bin/env python3
"""Independent static validator for the Juniper Trail Cardigan vanilla POC."""

from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "vanilla"
PACK = ROOT / "test-packs" / "vanilla" / "[CP] Juniper Trail Cardigan POC"
NATIVE = OUTPUT / "juniper_trail_cardigan.png"
PREVIEW = OUTPUT / "juniper_trail_cardigan-8x.png"
CONTACT = OUTPUT / "juniper_trail_cardigan-directions-8x.png"
PACK_ASSET = PACK / "assets" / "juniper_trail_cardigan.png"
CONTENT = PACK / "content.json"
MANIFEST = PACK / "manifest.json"
REPORT = OUTPUT / "juniper_trail_cardigan.validation.json"

ITEM_ID = "RNGClothing.VanillaPOC.JuniperTrailCardigan"
TEXTURE_ASSET = "Mods/RNGClothing/VanillaPOC/JuniperTrailCardigan/Shirts"
DEFAULT_COLOR = "85 122 94"
DIRECTION_Y = {"front": 0, "right": 8, "left": 16, "back": 24}
BASE_PALETTE = {
    (64, 55, 46, 255),
    (242, 220, 173, 255),
    (199, 175, 131, 255),
    (214, 154, 70, 255),
}
MASK_PALETTE = {
    (235, 235, 235, 255),
    (176, 176, 176, 255),
    (104, 104, 104, 255),
}
TRANSPARENT = (0, 0, 0, 0)


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path: Path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path}: PNG signature"
    cursor = 8
    idat = bytearray()
    width = height = None
    chunk_names = []
    while cursor < len(data):
        length = struct.unpack(">I", data[cursor : cursor + 4])[0]
        kind = data[cursor + 4 : cursor + 8]
        payload = data[cursor + 8 : cursor + 8 + length]
        expected_crc = struct.unpack(">I", data[cursor + 8 + length : cursor + 12 + length])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        assert expected_crc == actual_crc, f"{path}: bad {kind!r} CRC"
        cursor += 12 + length
        chunk_names.append(kind.decode("ascii"))
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            assert (bit_depth, color_type, compression, filtering, interlace) == (
                8,
                6,
                0,
                0,
                0,
            ), f"{path}: expected non-interlaced RGBA8"
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break
    assert width is not None and height is not None, f"{path}: missing IHDR"
    raw = zlib.decompress(bytes(idat))
    bytes_per_pixel = 4
    stride = width * bytes_per_pixel
    assert len(raw) == height * (stride + 1), f"{path}: decompressed size"
    rows = []
    filters = []
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
            left = decoded[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            above = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                predictor = paeth(left, above, upper_left)
            else:
                raise AssertionError(f"{path}: unsupported PNG filter {filter_type}")
            decoded[index] = (value + predictor) & 0xFF
        rows.append([tuple(decoded[x : x + 4]) for x in range(0, stride, 4)])
        previous = decoded
    return {
        "width": width,
        "height": height,
        "pixels": rows,
        "filters": filters,
        "chunks": chunk_names,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def assert_nearest_preview(native, preview, factor=8):
    assert preview["width"] == native["width"] * factor
    assert preview["height"] == native["height"] * factor
    for y in range(native["height"]):
        for x in range(native["width"]):
            expected = native["pixels"][y][x]
            for dy in range(factor):
                for dx in range(factor):
                    actual = preview["pixels"][y * factor + dy][x * factor + dx]
                    assert actual == expected, f"preview is not nearest at ({x},{y})"


def frame_pixels(native, x_offset, y_offset):
    return [
        [native["pixels"][y_offset + y][x_offset + x] for x in range(8)]
        for y in range(8)
    ]


def occupied(frame):
    return {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}


def validate_native(native):
    assert (native["width"], native["height"]) == (256, 32)
    assert set(native["filters"]) == {0}, "native PNG must use explicit unfiltered scanlines"
    assert native["chunks"] == ["IHDR", "IDAT", "IEND"]

    alpha_values = set()
    transparent_rgbs = set()
    pixels_outside_frames = []
    used_base_colors = set()
    used_mask_colors = set()
    frame_counts = {}

    for y, row in enumerate(native["pixels"]):
        for x, pixel in enumerate(row):
            alpha_values.add(pixel[3])
            if pixel[3] == 0:
                transparent_rgbs.add(pixel[:3])
                continue
            if not (0 <= x < 8 or 128 <= x < 136):
                pixels_outside_frames.append((x, y))
            if x < 128:
                used_base_colors.add(pixel)
            else:
                used_mask_colors.add(pixel)

    assert alpha_values <= {0, 255}, f"unexpected alpha values: {alpha_values}"
    assert transparent_rgbs == {(0, 0, 0)}, "transparent pixels must have zero RGB"
    assert not pixels_outside_frames, f"opaque pixels outside frames: {pixels_outside_frames}"
    assert used_base_colors == BASE_PALETTE, f"base palette mismatch: {used_base_colors}"
    assert used_mask_colors == MASK_PALETTE, f"mask palette mismatch: {used_mask_colors}"
    assert all(r == g == b for r, g, b, _ in used_mask_colors), "mask must be grayscale"

    for direction, y_offset in DIRECTION_Y.items():
        base = frame_pixels(native, 0, y_offset)
        mask = frame_pixels(native, 128, y_offset)
        base_occupied = occupied(base)
        mask_occupied = occupied(mask)
        combined = base_occupied | mask_occupied
        assert base_occupied, f"{direction}: no protected/base pixels"
        assert mask_occupied, f"{direction}: no dye-mask pixels"
        assert not (base_occupied & mask_occupied), f"{direction}: base/mask overlap"
        assert {y for _, y in combined} == set(range(8)), f"{direction}: incomplete vertical coverage"
        for x, y in combined:
            neighbors = {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)}
            assert combined & neighbors, f"{direction}: isolated logical pixel at ({x},{y})"
        frame_counts[direction] = {
            "base_pixels": len(base_occupied),
            "mask_pixels": len(mask_occupied),
            "combined_pixels": len(combined),
        }

    # This garment is symmetric, so native left must be the exact horizontal
    # mirror of native right in both protected and mask layers.
    for x_offset in (0, 128):
        right = frame_pixels(native, x_offset, DIRECTION_Y["right"])
        left = frame_pixels(native, x_offset, DIRECTION_Y["left"])
        for y in range(8):
            for x in range(8):
                assert left[y][x] == right[y][7 - x], "left/right alignment mismatch"

    # Installed renderer sleeve sampling contract for sprite index 0.
    assert native["pixels"][2][128] == (235, 235, 235, 255)
    assert native["pixels"][3][128] == (176, 176, 176, 255)
    assert native["pixels"][4][128] == (104, 104, 104, 255)
    return frame_counts, sorted(alpha_values), used_base_colors, used_mask_colors


def validate_pack():
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert content["Format"] == "2.8.0"
    assert len(content["Changes"]) == 2
    load, edit = content["Changes"]
    assert load == {
        "Action": "Load",
        "Target": TEXTURE_ASSET,
        "FromFile": "assets/juniper_trail_cardigan.png",
    }
    assert edit["Action"] == "EditData"
    assert edit["Target"] == "Data/Shirts"
    assert list(edit["Entries"]) == [ITEM_ID]
    item = edit["Entries"][ITEM_ID]
    assert item["Name"] == ITEM_ID
    assert item["DisplayName"] == "Juniper Trail Cardigan"
    assert item["Texture"] == TEXTURE_ASSET
    assert item["SpriteIndex"] == 0
    assert item["DefaultColor"] == DEFAULT_COLOR
    assert item["CanBeDyed"] is True
    assert item["IsPrismatic"] is False
    assert item["HasSleeves"] is True
    assert item["CanChooseDuringCharacterCustomization"] is False
    assert manifest["UniqueID"] == "RNGClothing.VanillaPOC.JuniperTrailCardigan"
    assert manifest["ContentPackFor"] == {
        "UniqueID": "Pathoschild.ContentPatcher",
        "MinimumVersion": "2.8.0",
    }
    assert hashlib.sha256(NATIVE.read_bytes()).digest() == hashlib.sha256(
        PACK_ASSET.read_bytes()
    ).digest(), "pack asset differs from approved native output"
    return content, manifest


def serializable_palette(palette):
    return [list(color) for color in sorted(palette)]


def main() -> None:
    native = read_png(NATIVE)
    preview = read_png(PREVIEW)
    contact = read_png(CONTACT)
    pack_asset = read_png(PACK_ASSET)

    frame_counts, alphas, base_palette, mask_palette = validate_native(native)
    assert_nearest_preview(native, preview, 8)
    assert (contact["width"], contact["height"]) == (352, 112)
    assert set(contact["filters"]) == {0}
    assert (pack_asset["width"], pack_asset["height"]) == (256, 32)
    assert pack_asset["sha256"] == native["sha256"]
    validate_pack()

    report = {
        "status": "PASS",
        "scope": "static vanilla 1.6.15 shirt/Content Patcher contract",
        "runtime_in_game": "not run; isolated pack is ready for user testing",
        "item_id": f"(S){ITEM_ID}",
        "native_png": {
            "path": str(NATIVE.relative_to(ROOT)),
            "width": native["width"],
            "height": native["height"],
            "format": "RGBA8 non-interlaced PNG",
            "filters": sorted(set(native["filters"])),
            "sha256": native["sha256"],
            "alpha_values": alphas,
            "base_palette_rgba": serializable_palette(base_palette),
            "mask_palette_rgba": serializable_palette(mask_palette),
            "frame_counts": frame_counts,
        },
        "preview": {
            "path": str(PREVIEW.relative_to(ROOT)),
            "width": preview["width"],
            "height": preview["height"],
            "scale": 8,
            "resampling": "verified exact nearest-neighbor replication",
        },
        "contact_sheet": {
            "path": str(CONTACT.relative_to(ROOT)),
            "width": contact["width"],
            "height": contact["height"],
            "directions": ["front", "back", "left", "right"],
        },
        "checks": [
            "native sheet is exactly 256x32",
            "sprite index 0 base frames are x=0..7 at y=0/8/16/24",
            "dye masks are x=128..135 at matching y positions",
            "all four directions contain protected and dyeable pixels",
            "base and dye-mask cells never overlap",
            "left is the exact logical mirror of right",
            "front sleeve sample ramp matches installed 1.6.15 renderer",
            "opaque alpha is 255 and transparent RGB/alpha is zero",
            "only the declared protected and grayscale-mask palettes occur",
            "no isolated single-pixel speckles occur",
            "8x sheet preview is exact integer nearest-neighbor",
            "Content Patcher JSON and manifest parse and match the texture/item contract",
            "test-pack native PNG is byte-identical to output native PNG",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
