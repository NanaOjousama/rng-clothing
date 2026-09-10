#!/usr/bin/env python3
"""Generate the Fashion Sense HD jacket POC or refresh its pack metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generator.png_utils import (
    RGBA,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    read_rgba_png,
    text_width,
    write_rgba_png,
)
from generator.renderers.fashionsense import (
    composite_default_frame,
    render_mistral_hd_jacket,
)
from generator.renderers.vanilla import render_v2_recipe
from generator.v2_recipe_engine import load_v2_data


ROOT = PROJECT_ROOT
RECIPE_BATCH = ROOT / "output" / "recipes" / "lifestyle_v2_recipes.json"
CONFIG_PATH = ROOT / "generator" / "data" / "fashionsense" / "hd_jacket_poc.json"
OUTPUT = ROOT / "output" / "fashionsense" / "poc_hd_jacket"
COMPARISON_OUTPUT = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-HD-Jacket-POC"
SHIRT_FOLDER = PACK / "Shirts" / "MistralLapelLayerJacketHD"
VANILLA_ASSET = ROOT / "output" / "vanilla" / "v2" / "mistral_lapel_layer_jacket.png"

NATIVE_NAME = "mistral_lapel_layer_jacket_hd.png"
RAW_PREVIEW_NAME = "mistral_lapel_layer_jacket_hd-native-8x.png"
DEFAULT_PREVIEW_NAME = "mistral_lapel_layer_jacket_hd-default-8x.png"
CONTACT_NAME = "mistral_lapel_layer_jacket_hd-directions-8x.png"
BEFORE_NATIVE_NAME = "mistral_lapel_layer_jacket_hd-before-coverage.png"
BEFORE_AFTER_NAME = "FS_JACKET_SHOULDER_COVERAGE_BEFORE_AFTER.png"
COVERAGE_DEBUG_NAME = "mistral_lapel_layer_jacket_hd-coverage-debug.png"

BACKGROUND: RGBA = (236, 226, 211, 255)
INK: RGBA = (61, 55, 51, 255)
FRAME_BORDER: RGBA = (91, 83, 75, 255)
FRAME_BACK: RGBA = (215, 207, 194, 255)
DEBUG_EMPTY: RGBA = (48, 45, 43, 255)
DEBUG_REQUIRED: RGBA = (232, 180, 74, 255)
DEBUG_COVERED: RGBA = (76, 174, 111, 255)
DEBUG_MISSING: RGBA = (210, 69, 67, 255)
DEBUG_GARMENT: RGBA = (88, 128, 168, 255)


def _load_recipe() -> dict[str, Any]:
    batch = json.loads(RECIPE_BATCH.read_text(encoding="utf-8"))
    matches = [recipe for recipe in batch["recipes"] if recipe["id"] == "lifestyle-v2-16"]
    if len(matches) != 1:
        raise ValueError("expected one lifestyle-v2-16 recipe")
    return matches[0]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _bordered_blit(
    destination: list[list[RGBA]], source: list[list[RGBA]], x: int, y: int
) -> None:
    width = len(source[0])
    height = len(source)
    draw_rect(destination, x - 2, y - 2, width + 4, height + 4, FRAME_BORDER)
    draw_rect(destination, x - 1, y - 1, width + 2, height + 2, FRAME_BACK)
    blit(destination, source, x, y)


def _make_contact(
    frames: dict[str, list[list[RGBA]]], scale: int = 8
) -> list[list[RGBA]]:
    directions = ("front", "back", "left", "right")
    frame_size = 16 * scale
    gap = 24
    margin = 18
    title = "MISTRAL LAPEL LAYER JACKET HD POC"
    width = max(
        margin * 2 + frame_size * len(directions) + gap * (len(directions) - 1),
        text_width(title) + margin * 2,
    )
    height = 28 + 12 + frame_size + 18
    sheet = blank_image(width, height, BACKGROUND)
    draw_text(sheet, title, (width - text_width(title)) // 2, 8, color=INK)
    for index, direction in enumerate(directions):
        x = margin + index * (frame_size + gap)
        label = direction.upper()
        draw_text(sheet, label, x + (frame_size - text_width(label)) // 2, 28, color=INK)
        _bordered_blit(sheet, nearest_scale(frames[direction], scale), x, 40)
    return sheet


def _stack_frames(
    frames: dict[str, list[list[RGBA]]], directions: tuple[str, ...]
) -> list[list[RGBA]]:
    frame_height = len(next(iter(frames.values())))
    frame_width = len(next(iter(frames.values()))[0])
    stack = blank_image(frame_width, frame_height * len(directions))
    for index, direction in enumerate(directions):
        for y, row in enumerate(frames[direction]):
            stack[index * frame_height + y] = list(row)
    return stack


def _frames_from_stack(texture: list[list[RGBA]]) -> dict[str, list[list[RGBA]]]:
    directions = ("front", "right", "left", "back")
    return {
        direction: [list(row) for row in texture[index * 16 : (index + 1) * 16]]
        for index, direction in enumerate(directions)
    }


def _make_before_after(
    before: dict[str, list[list[RGBA]]],
    after: dict[str, list[list[RGBA]]],
) -> list[list[RGBA]]:
    directions = ("front", "back", "left", "right")
    scale = 8
    frame_size = 16 * scale
    gap = 22
    margin = 110
    start_y = 52
    row_gap = 40
    width = margin * 2 + frame_size * 4 + gap * 3
    height = start_y + frame_size * 2 + row_gap + 20
    sheet = blank_image(width, height, BACKGROUND)
    title = "FS JACKET SHOULDER COVERAGE BEFORE AFTER"
    draw_text(sheet, title, (width - text_width(title)) // 2, 8, color=INK)
    for index, direction in enumerate(directions):
        x = margin + index * (frame_size + gap)
        draw_text(sheet, direction.upper(), x + (frame_size - text_width(direction.upper())) // 2, 28, color=INK)
        _bordered_blit(sheet, nearest_scale(before[direction], scale), x, start_y)
        _bordered_blit(sheet, nearest_scale(after[direction], scale), x, start_y + frame_size + row_gap)
    draw_text(sheet, "BEFORE", 22, start_y + frame_size // 2, scale=2, color=INK)
    draw_text(sheet, "AFTER", 28, start_y + frame_size + row_gap + frame_size // 2, scale=2, color=INK)
    return sheet


def _coverage_debug_frame(
    envelope: list[list[bool]],
    garment: list[list[RGBA]] | None,
) -> list[list[RGBA]]:
    frame = blank_image(16, 16, DEBUG_EMPTY)
    for y in range(16):
        for x in range(16):
            required = envelope[y][x]
            occupied = garment is not None and garment[y][x][3] == 255
            if garment is None:
                if required:
                    frame[y][x] = DEBUG_REQUIRED
            elif required and not occupied:
                frame[y][x] = DEBUG_MISSING
            elif required:
                frame[y][x] = DEBUG_COVERED
            elif occupied:
                frame[y][x] = DEBUG_GARMENT
    return frame


def _make_coverage_debug(
    envelopes: dict[str, list[list[bool]]],
    before: dict[str, list[list[RGBA]]],
    after: dict[str, list[list[RGBA]]],
) -> list[list[RGBA]]:
    directions = ("front", "back", "left", "right")
    rows = (
        ("REQUIRED", None),
        ("OLD MASK", before),
        ("CORRECTED", after),
    )
    scale = 6
    frame_size = 16 * scale
    gap = 20
    margin_x = 126
    start_y = 62
    row_gap = 28
    width = margin_x + frame_size * 4 + gap * 3 + 20
    height = start_y + frame_size * 3 + row_gap * 2 + 34
    sheet = blank_image(width, height, BACKGROUND)
    title = "HD JACKET BODY COVERAGE ENVELOPE"
    draw_text(sheet, title, (width - text_width(title)) // 2, 8, color=INK)
    draw_text(sheet, "GOLD REQUIRED  GREEN COVERED  RED EXPOSED  BLUE GARMENT FREEDOM", 18, 24, color=INK)
    for index, direction in enumerate(directions):
        x = margin_x + index * (frame_size + gap)
        draw_text(sheet, direction.upper(), x + (frame_size - text_width(direction.upper())) // 2, 44, color=INK)
    for row_index, (label, garments) in enumerate(rows):
        y = start_y + row_index * (frame_size + row_gap)
        draw_text(sheet, label, 18, y + frame_size // 2 - 4, color=INK)
        for index, direction in enumerate(directions):
            logical = _coverage_debug_frame(
                envelopes[direction],
                None if garments is None else garments[direction],
            )
            x = margin_x + index * (frame_size + gap)
            _bordered_blit(sheet, nearest_scale(logical, scale), x, y)
    return sheet


def _make_comparison(
    vanilla_frames: dict[str, list[list[RGBA]]],
    fs_frames: dict[str, list[list[RGBA]]],
    vanilla_native: list[list[RGBA]],
    fs_native: list[list[RGBA]],
) -> list[list[RGBA]]:
    directions = ("front", "back", "left", "right")
    width, height = 620, 410
    sheet = blank_image(width, height, BACKGROUND)
    title = "VANILLA VS FASHION SENSE MISTRAL JACKET"
    draw_text(sheet, title, (width - text_width(title)) // 2, 10, color=INK)
    draw_text(sheet, "VANILLA FRAME 8X8 64 CELLS SCALE 4 DISPLAY 32X32", 18, 34, color=INK)
    draw_text(sheet, "FS FRAME 16X16 256 CELLS SCALE 2 DISPLAY 32X32", 18, 48, color=INK)
    draw_text(sheet, "REVIEW ZOOM IS EQUAL FOOTPRINT VANILLA 8X FS 4X", 18, 62, color=INK)

    start_x = 210
    for index, direction in enumerate(directions):
        x = start_x + index * 88
        label = direction.upper()
        draw_text(sheet, label, x + (64 - text_width(label)) // 2, 82, color=INK)

    draw_text(sheet, "VANILLA", 24, 126, scale=2, color=INK)
    draw_text(sheet, "8X REVIEW", 24, 146, color=INK)
    for index, direction in enumerate(directions):
        _bordered_blit(sheet, nearest_scale(vanilla_frames[direction], 8), start_x + index * 88, 102)

    draw_text(sheet, "FS HD", 24, 224, scale=2, color=INK)
    draw_text(sheet, "4X REVIEW", 24, 244, color=INK)
    for index, direction in enumerate(directions):
        _bordered_blit(sheet, nearest_scale(fs_frames[direction], 4), start_x + index * 88, 202)

    draw_text(sheet, "AUTHORITATIVE SOURCE TEXTURES", 18, 292, color=INK)
    draw_text(sheet, "VANILLA GAME PNG 256X32", 18, 310, color=INK)
    draw_rect(sheet, 17, 323, 258, 34, FRAME_BORDER)
    blit(sheet, vanilla_native, 18, 324)

    draw_text(sheet, "FS PACK PNG 16X64", 320, 310, color=INK)
    draw_rect(sheet, 319, 323, 18, 66, FRAME_BORDER)
    blit(sheet, fs_native, 320, 324)
    draw_text(sheet, "FS SOURCE IS GRAYSCALE MASK PLUS FIXED INNER LAYER", 360, 336, color=INK)
    draw_text(sheet, "NO VANILLA UPSCALE USED", 360, 352, color=INK)
    draw_text(sheet, "NOMINAL DISPLAY BOX MATCH 32X32 CONFIRMED BY DRAW MATH", 18, 394, color=INK)
    return sheet


def _shirt_model(config: dict[str, Any], y: int) -> dict[str, Any]:
    mask_values = [
        [value, value, value]
        for value in (
            config["primaryMaskRamp"]["deep"],
            config["primaryMaskRamp"]["shadow"],
            config["primaryMaskRamp"]["base"],
            config["primaryMaskRamp"]["light"],
            config["primaryMaskRamp"]["highlight"],
        )
    ]
    sleeve_colors = [[value, value, value] for value in config["sleeveMaskRamp"]]
    return {
        "Scale": config["scale"],
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [
            {
                "Name": "Outer Fabric",
                "DefaultColor": config["defaultPrimaryColor"],
                "Values": mask_values,
            }
        ],
        "SleeveColors": sleeve_colors,
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": config["bodyPosition"],
        "ShirtSize": {
            "Width": config["logicalFrame"]["width"],
            "Length": config["logicalFrame"]["height"],
        },
    }


def _shirt_json(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "Name": "Mistral Lapel Layer Jacket HD POC",
        "Format": "7.5.0",
        "Tags": ["Lifestyle", "Jacket", "Layered", "RNG Clothing", "POC"],
        "FrontShirt": _shirt_model(config, 0),
        "RightShirt": _shirt_model(config, 16),
        "LeftShirt": _shirt_model(config, 32),
        "BackShirt": _shirt_model(config, 48),
    }


def _manifest() -> dict[str, Any]:
    return {
        "Name": "RNG Clothing HD Jacket POC",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.2",
        "Description": "Test-only 2x logical-density Fashion Sense rendering of one V2 jacket recipe.",
        "UniqueID": "RNGClothing.FashionSense.HDJacketPOC",
        "UpdateKeys": [],
        "ContentPackFor": {
            "UniqueID": "PeacefulEnd.FashionSense",
            "MinimumVersion": "7.5.0",
        },
    }


def _readme() -> str:
    return """# RNG Clothing — Fashion Sense HD Jacket POC

This is a test-only Fashion Sense content pack for one controlled renderer experiment. It does not replace the vanilla RNG Clothing V2 pack and contains no Fashion Sense binaries.

## Requirements

- Stardew Valley 1.6.15
- SMAPI compatible with Stardew 1.6.15
- Fashion Sense 7.5.0

Content Patcher is not required by this pack.

## Install

Copy the whole `RNG-Clothing-HD-Jacket-POC` folder into your Stardew Valley `Mods` folder. Do not copy the project `output` folder and do not copy the audited Fashion Sense source tree.

Expected result:

```text
Stardew Valley/Mods/RNG-Clothing-HD-Jacket-POC/manifest.json
```

Fashion Sense itself must be installed separately from its official distribution.

**First install requires a full game/SMAPI restart.** Fashion Sense's `fs_reload` command reloads content packs that SMAPI discovered when the game launched; it does not register a brand-new manifest copied into `Mods` during the current session.

## Equip and test

1. Start the game through SMAPI and load a save.
2. In the SMAPI console, run `fs_add_mirror` if you do not already have a Hand Mirror.
3. Use the Hand Mirror, select the **Shirts** category, and choose **Mistral Lapel Layer Jacket HD POC**.
4. Face front, back, left, and right; then test standing, walking, and basic tools.
5. The jacket's `Outer Fabric` mask defaults to Mistral cool neutral. Fashion Sense has an open report about `DefaultColor` initialization; if the first tint is unexpected, set the Outer Fabric color once in the Hand Mirror to approximately RGB `112, 130, 145` before judging the palette or sleeves.

After the pack has appeared in SMAPI's startup list once, `fs_reload RNGClothing.FashionSense.HDJacketPOC` can reload later JSON/PNG edits without restarting the game.

## Scale-2 torso anchor

Every direction uses `BodyPosition: { "X": 0, "Y": 32 }`. Stardew's normal Farmer draw origin is `(0,32)`, and Fashion Sense includes that origin in the source-space origin multiplied by the appearance `Scale`. At `Scale: 2`, the extra positive 32 source pixels move the shirt upward by 64 display pixels and restore the vanilla `Scale: 4` torso position. A negative Y would move the shirt farther down. `DisableNativeOffset` remains false so walking and directional Farmer feature offsets still apply.

## Shoulder/body coverage

Version 1.0.2 retains the sloped 16×16 silhouette but restores the minimum upper-torso coverage needed at the native sleeve junction. A permanent coverage-envelope validator now rejects transparent jacket cells inside that required zone. The neck opening, Scale 2, `(0,32)` anchor, palette, lapels, inner layer, back yoke, and native `SleeveColors` strategy are unchanged.

## Sleeve scope

This POC deliberately uses Fashion Sense shirt `SleeveColors`, not a separate custom Sleeves appearance. Fashion Sense recolors Stardew's native animated sleeve/arm pixels from those three values, so standing, walking, and basic tool poses remain owned by the game. The high-density shirt adds better shoulder and cuff transitions, but it does not replace native arm geometry. A fully custom sleeve atlas would be a separate appearance requiring its own equip state and extensive pose animation data; that is outside this one-jacket POC.

## Known test boundaries

- Runtime loading and the corrected `(0,32)` torso anchor are confirmed. The 1.0.2 shoulder-coverage correction still needs one in-game `fs_reload` check.
- Fashion Sense has an open report about non-default `Scale` alignment on horseback. Horseback alignment is therefore a required manual check and is not claimed here.
- Multiplayer peers should install Fashion Sense 7.5.0 and this same pack.
"""


def _refresh_pack_metadata_only() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    exported_config = json.loads((OUTPUT / "renderer_config.json").read_text(encoding="utf-8"))
    if exported_config != config:
        raise ValueError("renderer_config.json does not match the backend anchor configuration")

    pack_texture = SHIRT_FOLDER / "shirt.png"
    output_texture = OUTPUT / NATIVE_NAME
    if not pack_texture.is_file() or not output_texture.is_file():
        raise FileNotFoundError("existing POC texture is missing; refusing metadata-only refresh")
    if pack_texture.read_bytes() != output_texture.read_bytes():
        raise ValueError("pack and output textures differ; refusing metadata-only refresh")

    SHIRT_FOLDER.mkdir(parents=True, exist_ok=True)
    _write_json(PACK / "manifest.json", _manifest())
    _write_json(SHIRT_FOLDER / "shirt.json", _shirt_json(config))
    (PACK / "README.md").write_text(_readme(), encoding="utf-8")
    print(f"Refreshed Fashion Sense pack metadata only at {PACK}")
    print("Preserved existing shirt.png byte-for-byte")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="refresh manifest, shirt.json, and README without regenerating artwork",
    )
    args = parser.parse_args()
    if args.pack_only:
        _refresh_pack_metadata_only()
        return

    recipe = _load_recipe()
    rendered = render_mistral_hd_jacket(recipe)
    config = rendered.config
    default_frames = {
        direction: composite_default_frame(frame, config)
        for direction, frame in rendered.frames.items()
    }
    default_texture = _stack_frames(default_frames, ("front", "right", "left", "back"))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    COMPARISON_OUTPUT.mkdir(parents=True, exist_ok=True)
    SHIRT_FOLDER.mkdir(parents=True, exist_ok=True)

    native_path = OUTPUT / NATIVE_NAME
    before_native_path = OUTPUT / BEFORE_NATIVE_NAME
    if not before_native_path.exists():
        if not native_path.exists():
            raise FileNotFoundError("pre-correction FS native texture is missing")
        old_native = read_rgba_png(native_path)
        if (old_native["width"], old_native["height"]) != (16, 64):
            raise ValueError("pre-correction FS native texture must be 16x64")
        write_rgba_png(before_native_path, old_native["pixels"])

    before_native = read_rgba_png(before_native_path)
    if (before_native["width"], before_native["height"]) != (16, 64):
        raise ValueError("body-coverage baseline texture must be 16x64")
    before_raw_frames = _frames_from_stack(before_native["pixels"])
    before_default_frames = {
        direction: composite_default_frame(frame, config)
        for direction, frame in before_raw_frames.items()
    }

    write_rgba_png(native_path, rendered.texture)
    write_rgba_png(OUTPUT / RAW_PREVIEW_NAME, nearest_scale(rendered.texture, 8))
    write_rgba_png(OUTPUT / DEFAULT_PREVIEW_NAME, nearest_scale(default_texture, 8))
    write_rgba_png(OUTPUT / CONTACT_NAME, _make_contact(default_frames))
    _write_json(OUTPUT / "semantic_recipe.json", recipe)
    _write_json(OUTPUT / "renderer_config.json", config)
    write_rgba_png(
        COMPARISON_OUTPUT / BEFORE_AFTER_NAME,
        _make_before_after(before_default_frames, default_frames),
    )
    write_rgba_png(
        OUTPUT / COVERAGE_DEBUG_NAME,
        _make_coverage_debug(
            rendered.coverage_envelopes,
            before_raw_frames,
            rendered.frames,
        ),
    )

    vanilla_data = load_v2_data()
    vanilla_render = render_v2_recipe(recipe, vanilla_data)
    vanilla_native = read_rgba_png(VANILLA_ASSET)["pixels"]
    write_rgba_png(
        COMPARISON_OUTPUT / "VANILLA_VS_FS_JACKET.png",
        _make_comparison(
            vanilla_render.default_composites,
            default_frames,
            vanilla_native,
            rendered.texture,
        ),
    )

    _write_json(PACK / "manifest.json", _manifest())
    _write_json(SHIRT_FOLDER / "shirt.json", _shirt_json(config))
    write_rgba_png(SHIRT_FOLDER / "shirt.png", rendered.texture)
    (PACK / "README.md").write_text(_readme(), encoding="utf-8")

    print(f"Generated Fashion Sense HD jacket POC at {OUTPUT}")
    print(f"Generated test pack at {PACK}")


if __name__ == "__main__":
    main()
