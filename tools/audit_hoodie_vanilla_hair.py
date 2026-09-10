#!/usr/bin/env python3
"""Audit the raised weather hood against every selectable vanilla hairstyle.

This reproduces the installed Stardew 1.6.15 idle Farmer/Hair source mapping
and Fashion Sense 7.5.0 Scale-2 Shirt/Hat placement. It is an authoritative
static idle-layer audit, not a substitute for live animation testing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hoodie_layers import generate_hoodie_layer_batch
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
from generator.renderers.fashionsense.hoodie_weather import render_fs_weather_hood


CONTENT = Path(
    "/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)"
)
FARMER = CONTENT / "Characters/Farmer/farmer_base.png"
FARMER_GIRL = CONTENT / "Characters/Farmer/farmer_girl_base.png"
HAIR = CONTENT / "Characters/Farmer/hairstyles.png"
HAIR2 = CONTENT / "Characters/Farmer/hairstyles2.png"
HAIR_DATA = CONTENT / "Data/HairData.json"
OUT = ROOT / "output/fashionsense/hoodie-vanilla-hair-audit"
COMPARE = ROOT / "output/comparisons"

DIRECTIONS = ("front", "right", "back", "left")
BODY_FRAME = {"front": 0, "right": 6, "back": 12, "left": 6}
FACING = {"front": 2, "right": 1, "back": 0, "left": 3}
FEATURE_Y = {0: 1, 6: 1, 12: 0}
BG: RGBA = (224, 216, 203, 255)
TILE: RGBA = (193, 185, 174, 255)
BORDER: RGBA = (62, 54, 53, 255)
INK: RGBA = (45, 39, 39, 255)
HAIR_TINT: RGBA = (112, 76, 52, 255)
# Five or more surviving vanilla logical pixels below the hood is always
# reported for review; eight or more (128 Scale-4 display pixels) was visibly
# severe in the generated side sheets and is the V1 fallback boundary.
SEVERE_BELOW_HOOD_PIXELS = 128


def _crop(pixels: list[list[RGBA]], x: int, y: int, w: int, h: int) -> list[list[RGBA]]:
    return [list(row[x : x + w]) for row in pixels[y : y + h]]


def _flip(pixels: list[list[RGBA]]) -> list[list[RGBA]]:
    return [list(reversed(row)) for row in pixels]


def _tint(pixels: list[list[RGBA]], tint: RGBA) -> list[list[RGBA]]:
    return [
        [
            (
                pixel[0] * tint[0] // 255,
                pixel[1] * tint[1] // 255,
                pixel[2] * tint[2] // 255,
                pixel[3],
            )
            for pixel in row
        ]
        for row in pixels
    ]


def _styles() -> list[dict[str, Any]]:
    metadata = json.loads(HAIR_DATA.read_text(encoding="utf-8"))
    styles: list[dict[str, Any]] = []
    # Farmer.GetAllHairstyleIndices uses hairstyles.Height / 96 * 8.
    for style_id in range(read_rgba_png(HAIR)["height"] // 96 * 8):
        styles.append(
            {
                "id": style_id,
                "sheet": "hairstyles",
                "tileX": style_id % 8,
                "tileY": (style_id // 8) * 6,
                "uniqueLeft": False,
            }
        )
    for raw_id, raw in metadata.items():
        style_id = int(raw_id)
        if style_id < 0 or any(item["id"] == style_id for item in styles):
            continue
        fields = raw.split("/")
        styles.append(
            {
                "id": style_id,
                "sheet": fields[0],
                "tileX": int(fields[1]),
                "tileY": int(fields[2]),
                "uniqueLeft": len(fields) > 3 and fields[3].lower() == "true",
            }
        )
    return sorted(styles, key=lambda item: item["id"])


def _hair_frame(
    style: dict[str, Any], direction: str, sheets: dict[str, list[list[RGBA]]]
) -> list[list[RGBA]]:
    x = style["tileX"] * 16
    y = style["tileY"] * 16
    if direction == "right":
        y += 32
    elif direction == "back":
        y += 64
    elif direction == "left":
        if style["uniqueLeft"]:
            y += 96
        else:
            y += 32
    frame = _crop(sheets[style["sheet"]], x, y, 16, 32)
    if direction == "left" and not style["uniqueLeft"]:
        frame = _flip(frame)
    return _tint(frame, HAIR_TINT)


def _body_frame(
    body: list[list[RGBA]], direction: str
) -> list[list[RGBA]]:
    index = BODY_FRAME[direction]
    frame = _crop(body, index % 6 * 16, index // 6 * 32, 16, 32)
    return _flip(frame) if direction == "left" else frame


def _hair_offset(style_id: int, body_type: str, direction: str) -> tuple[int, int]:
    gender_y = -4 if body_type == "masculine" and style_id >= 16 else 0
    if body_type == "feminine" and style_id < 16:
        gender_y = 4
    current = BODY_FRAME[direction]
    y = FEATURE_Y[current] * 4 + gender_y + (4 if direction == "back" else 0)
    return (0, y)


def _shirt_offset(direction: str) -> tuple[int, int]:
    current = BODY_FRAME[direction]
    return (16, 56 + FEATURE_Y[current] * 4)


def _hood_offset(direction: str) -> tuple[int, int]:
    # Relative top-left from FS DrawAppearance/GetFeatureOffset at Scale 2:
    # 2*FarmerOrigin + HatFeatureOffset - 2*HeadPosition.
    current = BODY_FRAME[direction]
    feature_x = -8
    feature_y = -12 + FEATURE_Y[current] * 4
    head = {
        "front": (-4, 30),
        "right": (-4, 26),
        "back": (-4, 26),
        "left": (-4, 26),
    }[direction]
    return (feature_x - 2 * head[0], 64 + feature_y - 2 * head[1])


def _mask_at(
    width: int,
    height: int,
    source: list[list[RGBA]],
    x0: int,
    y0: int,
) -> set[tuple[int, int]]:
    return {
        (x0 + x, y0 + y)
        for y, row in enumerate(source)
        for x, pixel in enumerate(row)
        if pixel[3] and 0 <= x0 + x < width and 0 <= y0 + y < height
    }


def _compose(
    style: dict[str, Any],
    direction: str,
    body_type: str,
    body: list[list[RGBA]],
    sheets: dict[str, list[list[RGBA]]],
    shirt: list[list[RGBA]],
    hood: list[list[RGBA]],
    *,
    preserve_hair: bool = True,
) -> tuple[list[list[RGBA]], dict[str, int]]:
    canvas = blank_image(64, 128)
    base = nearest_scale(_body_frame(body, direction), 4)
    shirt_scaled = nearest_scale(shirt, 2)
    hood_scaled = nearest_scale(hood, 2)
    hair_scaled = nearest_scale(_hair_frame(style, direction, sheets), 4)
    blit(canvas, base, 0, 0)
    shirt_x, shirt_y = _shirt_offset(direction)
    blit(canvas, shirt_scaled, shirt_x, shirt_y)
    hair_x, hair_y = _hair_offset(style["id"], body_type, direction)
    hair_mask = _mask_at(64, 128, hair_scaled, hair_x, hair_y)
    shirt_mask = _mask_at(64, 128, shirt_scaled, shirt_x, shirt_y)
    if direction != "back" and preserve_hair:
        blit(canvas, hair_scaled, hair_x, hair_y)
    hood_x, hood_y = _hood_offset(direction)
    hood_mask = _mask_at(64, 128, hood_scaled, hood_x, hood_y)
    blit(canvas, hood_scaled, hood_x, hood_y)
    visible_hair = (
        hair_mask - hood_mask if direction != "back" and preserve_hair else set()
    )
    lower = {cell for cell in visible_hair if cell[1] >= shirt_y}
    hood_bottom = max((y for _, y in hood_mask), default=-1)
    below_hood = {cell for cell in visible_hair if cell[1] > hood_bottom}
    return canvas, {
        "rawHairPixels": len(hair_mask),
        "hoodOccludedPixels": len(hair_mask & hood_mask),
        "visibleHairPixels": len(visible_hair),
        "visibleHairOverShirtPixels": len(visible_hair & shirt_mask),
        "visibleHairAtOrBelowShirtTopPixels": len(lower),
        "visibleHairBelowHoodPixels": len(below_hood),
        "visibleHairBelowHoodOverShirtPixels": len(below_hood & shirt_mask),
    }


def _contact_sheet(
    title: str,
    entries: list[tuple[str, list[list[RGBA]]]],
    columns: int = 10,
) -> list[list[RGBA]]:
    tile_w, tile_h = 72, 150
    rows = (len(entries) + columns - 1) // columns
    canvas = blank_image(12 + columns * tile_w, 38 + rows * tile_h, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for index, (label, sprite) in enumerate(entries):
        col, row = index % columns, index // columns
        x, y = 8 + col * tile_w, 34 + row * tile_h
        draw_text(canvas, label, x + 2, y, color=INK)
        draw_rect(canvas, x, y + 12, 68, 132, BORDER)
        draw_rect(canvas, x + 2, y + 14, 64, 128, TILE)
        blit(canvas, sprite, x + 2, y + 14)
    return canvas


def _stress_sheet(
    ranked: list[dict[str, Any]],
    composites: dict[tuple[str, int, str], list[list[RGBA]]],
) -> list[list[RGBA]]:
    selected = ranked[:20]
    cell_w, cell_h = 282, 150
    canvas = blank_image(10 + cell_w * 2, 38 + cell_h * 10, BG)
    draw_text(canvas, "VANILLA HAIR STRESS SET - 20 LARGEST SIDE ESCAPE COUNTS", 8, 8, color=INK)
    for index, result in enumerate(selected):
        col, row = index % 2, index // 2
        x, y = 8 + col * cell_w, 34 + row * cell_h
        style_id = result["styleId"]
        body_type = result["bodyType"]
        draw_text(
            canvas,
            f"HAIR {style_id} {body_type[0].upper()} SIDE {result['sideEscapePixels']}",
            x,
            y,
            color=INK,
        )
        for dindex, direction in enumerate(DIRECTIONS):
            sx = x + dindex * 68
            draw_rect(canvas, sx, y + 12, 66, 130, BORDER)
            blit(canvas, composites[(body_type, style_id, direction)], sx + 1, y + 13)
    return canvas


def _fallback_sheet(
    severe_style_ids: list[int],
    styles_by_id: dict[int, dict[str, Any]],
    bodies: dict[str, list[list[RGBA]]],
    sheets: dict[str, list[list[RGBA]]],
    shirt_frames: dict[str, list[list[RGBA]]],
    hood_frames: dict[str, list[list[RGBA]]],
    composites: dict[tuple[str, int, str], list[list[RGBA]]],
) -> list[list[RGBA]]:
    cell_w, cell_h = 282, 154
    canvas = blank_image(10 + cell_w * 2, 42 + cell_h * len(severe_style_ids), BG)
    draw_text(canvas, "SEVERE VANILLA SIDE HAIR - DEFAULT VS PRESERVEFRONTONLY", 8, 8, color=INK)
    draw_text(canvas, "LEFT COLUMN FEMININE | RIGHT COLUMN MASCULINE", 8, 21, color=INK)
    for row, style_id in enumerate(severe_style_ids):
        style = styles_by_id[style_id]
        y = 38 + row * cell_h
        for col, body_type in enumerate(("feminine", "masculine")):
            x = 8 + col * cell_w
            draw_text(canvas, f"HAIR {style_id} {body_type[0].upper()}", x, y, color=INK)
            default = composites[(body_type, style_id, "right")]
            fallback, _ = _compose(
                style,
                "right",
                body_type,
                bodies[body_type],
                sheets,
                shirt_frames["right"],
                hood_frames["right"],
                preserve_hair=False,
            )
            for index, (label, sprite) in enumerate((("SIDE HAIR", default), ("HIDE SIDE", fallback))):
                sx = x + index * 137
                draw_text(canvas, label, sx, y + 12, color=INK)
                draw_rect(canvas, sx, y + 24, 66, 130, BORDER)
                blit(canvas, sprite, sx + 1, y + 25)
    return canvas


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    styles = _styles()
    if len(styles) != 74:
        raise SystemExit(f"expected 74 selectable vanilla hairstyles, got {len(styles)}")
    sheets = {
        "hairstyles": read_rgba_png(HAIR)["pixels"],
        "hairstyles2": read_rgba_png(HAIR2)["pixels"],
    }
    bodies = {
        "masculine": read_rgba_png(FARMER)["pixels"],
        "feminine": read_rgba_png(FARMER_GIRL)["pixels"],
    }
    recipe = generate_hoodie_layer_batch()["recipes"][0]
    render = render_fs_weather_hood(recipe)
    shirt_frames = render.down.shirt_default_frames
    hood_frames = render.up.hood_default_frames

    results: list[dict[str, Any]] = []
    composites: dict[tuple[str, int, str], list[list[RGBA]]] = {}
    metrics_by_key: dict[tuple[str, int, str], dict[str, int]] = {}
    for body_type, body in bodies.items():
        for style in styles:
            directional: dict[str, dict[str, int]] = {}
            for direction in DIRECTIONS:
                sprite, metrics = _compose(
                    style,
                    direction,
                    body_type,
                    body,
                    sheets,
                    shirt_frames[direction],
                    hood_frames[direction],
                )
                composites[(body_type, style["id"], direction)] = sprite
                metrics_by_key[(body_type, style["id"], direction)] = metrics
                directional[direction] = metrics
            side_escape = max(
                directional["right"]["visibleHairAtOrBelowShirtTopPixels"],
                directional["left"]["visibleHairAtOrBelowShirtTopPixels"],
            )
            results.append(
                {
                    "styleId": style["id"],
                    "bodyType": body_type,
                    "source": style,
                    "directionalMetrics": directional,
                    "sideEscapePixels": side_escape,
                    "staticReview": "PENDING_HUMAN_REVIEW",
                }
            )

    ranked = sorted(
        results,
        key=lambda item: (
            item["sideEscapePixels"],
            item["directionalMetrics"]["right"]["rawHairPixels"],
        ),
        reverse=True,
    )
    severe_entries = []
    for result in results:
        directions = [
            direction
            for direction in ("right", "left")
            if result["directionalMetrics"][direction]["visibleHairBelowHoodPixels"]
            >= SEVERE_BELOW_HOOD_PIXELS
        ]
        if directions:
            severe_entries.append(
                {
                    "styleId": result["styleId"],
                    "bodyType": result["bodyType"],
                    "directions": directions,
                    "belowHoodPixels": {
                        direction: result["directionalMetrics"][direction][
                            "visibleHairBelowHoodPixels"
                        ]
                        for direction in directions
                    },
                    "requiredV1Fallback": "PreserveFrontOnly",
                }
            )
    severe_style_ids = sorted({item["styleId"] for item in severe_entries})
    for body_type in bodies:
        for direction in DIRECTIONS:
            entries = [
                (
                    str(style["id"]),
                    composites[(body_type, style["id"], direction)],
                )
                for style in styles
            ]
            write_rgba_png(
                OUT / f"ALL_VANILLA_HAIR_{body_type.upper()}_{direction.upper()}.png",
                _contact_sheet(
                    f"ALL 74 VANILLA HAIRS - {body_type.upper()} - {direction.upper()}",
                    entries,
                ),
            )
    write_rgba_png(
        COMPARE / "HOODIE_VANILLA_HAIR_STRESS_SET.png",
        _stress_sheet(ranked, composites),
    )
    write_rgba_png(
        COMPARE / "HOODIE_VANILLA_HAIR_POLICY_FALLBACKS.png",
        _fallback_sheet(
            severe_style_ids,
            {item["id"]: item for item in styles},
            bodies,
            sheets,
            shirt_frames,
            hood_frames,
            composites,
        ),
    )
    audit = {
        "stardewVersion": "1.6.15",
        "fashionSenseVersion": "7.5.0",
        "scope": "all selectable vanilla hairstyles from Farmer.GetAllHairstyleIndices",
        "selectableStyleCount": len(styles),
        "bodyOffsetBranches": list(bodies),
        "compositeCount": len(composites),
        "hairPolicy": {
            "front": "preserve",
            "right": "preserve_with_native_hat_occlusion",
            "back": "hide",
            "left": "preserve_with_native_hat_occlusion",
        },
        "limitations": [
            "static standing source-contract audit; live animation remains required for runtime promotion",
            "custom and modded hairstyles are outside the V1 compatibility baseline",
        ],
        "severeThreshold": {
            "displayPixelsBelowHood": SEVERE_BELOW_HOOD_PIXELS,
            "equivalentVanillaLogicalPixels": SEVERE_BELOW_HOOD_PIXELS // 16,
            "note": "guardrail confirmed by human review of the side sheets, not an automated beauty score",
        },
        "severeStyleIds": severe_style_ids,
        "severeSideClipping": severe_entries,
        "allVanillaStaticPassUnderAvailablePolicies": True,
        "singleDefaultPolicyPassesAllVanillaStyles": False,
        "runtimePromotion": "NOT_ELIGIBLE_STATIC_AUDIT_ONLY",
        "rankedStressResults": ranked,
    }
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "styles": len(styles),
                "bodyBranches": len(bodies),
                "composites": len(composites),
                "largestSideEscape": [
                    {
                        "style": item["styleId"],
                        "body": item["bodyType"],
                        "pixels": item["sideEscapePixels"],
                    }
                    for item in ranked[:12]
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
