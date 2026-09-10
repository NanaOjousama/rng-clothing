#!/usr/bin/env python3
"""Generate one isolated weather-responsive Fashion Sense hoodie test."""

from __future__ import annotations

import copy
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
    write_rgba_png,
)
from generator.renderers.fashionsense.hoodie_weather import (
    DIRECTIONS,
    render_fs_weather_hood,
)
from generator.renderers.fashionsense.hoodie_layers import _default, _solid
from generator.v2_recipe_engine import load_v2_data


OUT = ROOT / "output" / "fashionsense" / "hoodie-weather-test"
COMPARE = ROOT / "output" / "comparisons"
TEST_ROOT = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Hoodie-Weather-Test"
FS_PACK = TEST_ROOT / "[FS] RNG Clothing Hoodie Weather Test"
CP_PACK = TEST_ROOT / "[CP] RNG Clothing Hoodie Weather Test"
FS_ID = "RNGClothing.FashionSense.HoodieWeatherTest"
BASE_HAT_NAME = "Harbor Haze Weather Hood"
AUTO_BACK_HAT_NAME = "Harbor Haze Weather Hood - Auto HideBackOnly"
AUTO_FRONT_HAT_NAME = "Harbor Haze Weather Hood - Auto PreserveFrontOnly"
BG: RGBA = (238, 228, 207, 255)
TILE: RGBA = (77, 69, 67, 255)
BORDER: RGBA = (45, 39, 39, 255)
INK: RGBA = (52, 43, 40, 255)
MUTED: RGBA = (112, 88, 75, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _recipe() -> dict[str, Any]:
    recipe = copy.deepcopy(generate_hoodie_layer_batch()["recipes"][0])
    recipe["id"] = "hoodie-weather-test-01"
    recipe["itemName"] = "Harbor Haze Weather Hoodie"
    recipe["itemDescription"] = "A sea-glass hoodie whose hood rises outdoors in rain or snow."
    recipe["hoodLayer"]["state"] = "down"
    return recipe


def _shirt_mask_layer(render) -> dict[str, Any]:
    permanent = render.down.upper.base.base.design.base
    palette = load_v2_data()["palettes"]["families"][permanent.recipe["paletteFamily"]]
    return {
        "Name": "Primary Hoodie Fabric",
        "DefaultColor": palette["defaultDye"],
        "Values": [
            [permanent.config["outerMaskRamp"][role]] * 3
            for role in permanent.active_main_roles
        ],
    }


def _shirt_json(recipe: dict[str, Any], render) -> dict[str, Any]:
    def model(y: int) -> dict[str, Any]:
        return {
            "Scale": 2.0,
            "HideSleeves": False,
            "DisableGrayscale": False,
            "ColorMaskLayers": [_shirt_mask_layer(render)],
            "SleeveColors": [list(value) for value in render.down.upper.sleeve_colors],
            "StartingPosition": {"X": 0, "Y": y},
            "BodyPosition": {"X": 0, "Y": 32},
            "ShirtSize": {"Width": 16, "Length": 16},
        }

    return {
        "Name": recipe["itemName"],
        "Format": "7.5.0",
        "Tags": ["Lifestyle", "RNG Clothing", "Hoodie", "Weather Hood", "Test"],
        "FrontShirt": model(0),
        "RightShirt": model(16),
        "LeftShirt": model(32),
        "BackShirt": model(48),
    }


def _preset(recipe: dict[str, Any]) -> dict[str, Any]:
    return {
        "Name": "Hoodie Weather Test - Harbor Haze",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": f"{FS_ID}/Hat/{BASE_HAT_NAME}",
        "ShirtId": f"{FS_ID}/Shirt/{recipe['itemName']}",
        "SleevesId": "None",
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _assembled(render, state: str, direction: str) -> list[list[RGBA]]:
    source = render.up if state == "up" else render.down
    canvas = blank_image(32, 48)
    hood = source.hood_default_frames[direction]
    if state == "up":
        blit(canvas, hood, 0, 0)
        shirt_y = 26 if direction == "front" else 24
    elif direction == "front":
        # Front lowered hood is a body-zone fold drawn before Player. Its
        # wider 24-cell source is centered around the 16-cell Shirt and shares
        # the torso-level diagnostic Y rather than the head-level preview Y.
        blit(canvas, hood, (32 - len(hood[0])) // 2, 24)
        shirt_y = 24
    else:
        blit(canvas, hood, 8, 18)
        shirt_y = 24
    blit(canvas, render.down.shirt_default_frames[direction], 8, shirt_y)
    return canvas


def _bordered(canvas, sprite, x: int, y: int) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, TILE)
    blit(canvas, sprite, x, y)


def _state_sheet(render, state: str) -> list[list[RGBA]]:
    scale = 4
    w, h = 32 * scale, 48 * scale
    canvas = blank_image(30 + w * 4 + 22 * 3, 58 + h + 18, BG)
    draw_text(canvas, f"HARBOR HAZE WEATHER HOOD - {state.upper()}", 8, 8, color=INK)
    subtitle = (
        "HAIR PRESERVED / NATURAL OCCLUSION"
        if state == "up"
        else "RAW LAYERS; FRONT HOOD DRAWS BEFORE PLAYER IN GAME"
    )
    draw_text(canvas, subtitle, 8, 21, color=MUTED)
    for index, direction in enumerate(DIRECTIONS):
        x = 14 + index * (w + 22)
        draw_text(canvas, direction.upper(), x + 36, 42, color=INK)
        _bordered(canvas, nearest_scale(_assembled(render, state, direction), scale), x, 58)
    return canvas


def _hood_down_front_layering_sheet(render) -> list[list[RGBA]]:
    """Explain the front draw contract without fabricating a Farmer sprite."""

    scale = 8
    raw = render.down.hood_default_frames["front"]
    raw_scaled = nearest_scale(raw, scale)
    canvas = blank_image(720, 340, BG)
    draw_text(canvas, "HOOD-DOWN FRONT LAYERING DIAGNOSTIC", 8, 8, color=INK)
    draw_text(
        canvas,
        "SCHEMATIC ONLY - PLAYER BLOCK IS NOT VANILLA FARMER ART",
        8,
        21,
        color=MUTED,
    )

    draw_text(canvas, "1  COMPLETE HOOD LAYER", 24, 48, color=INK)
    _bordered(canvas, raw_scaled, 24, 68)

    draw_text(canvas, "2  RUNTIME Z ORDER", 250, 48, color=INK)
    for index, (label, color) in enumerate(
        (("HOOD HAT", (62, 130, 126, 255)), ("PLAYER", (104, 95, 92, 255)), ("HAIR", (97, 67, 48, 255)))
    ):
        y = 82 + index * 66
        draw_rect(canvas, 268, y, 130, 38, color)
        draw_text(canvas, label, 290, y + 14, color=(245, 238, 220, 255))
        if index < 2:
            draw_text(canvas, "THEN", 312, y + 46, color=MUTED)

    draw_text(canvas, "3  OCCLUSION PRINCIPLE", 458, 48, color=INK)
    x0, y0 = 500, 68
    _bordered(canvas, raw_scaled, x0, y0)
    # This neutral block communicates masking only. It intentionally does not
    # pretend to be an authoritative Farmer composite.
    draw_rect(canvas, x0 + 4 * scale, y0, 16 * scale, 15 * scale, (96, 90, 88, 255))
    diagnostic_ink = (238, 228, 207, 255)
    draw_text(canvas, "CENTER MASKED", 548, 278, color=diagnostic_ink)
    draw_text(canvas, "SIDE FOLDS", 552, 292, color=diagnostic_ink)
    draw_text(canvas, "HAIR NORMAL", 556, 306, color=diagnostic_ink)
    return canvas


def _legacy_front_down(render) -> list[list[RGBA]]:
    """Recreate the previous front frame only for an honest A/B diagnostic."""

    upper = render.down.upper
    recipe = render.recipe
    frame = blank_image(16, 32)
    expansion = 1 if recipe["hoodLayer"]["volume"] == "baggy" else 0
    contrast = recipe["hoodLayer"]["lining"] == "contrast"
    contour = _default(upper, "EXTERIOR_CONTOUR")
    crease = _default(upper, "DEEP_CREASE")
    shadow = _default(upper, "SHADOW")
    base = _default(upper, "BASE")
    light = _default(upper, "LIGHT")
    lining = _solid(upper, "secondary" if contrast else "dark_accent")
    rows = ((5, 10), (3, 12), (2, 13), (1, 14), (2, 13), (3, 12), (4, 11))
    for y, (lo0, hi0) in enumerate(rows):
        lo = max(0, lo0 - (expansion if y in {2, 3, 4} else 0))
        hi = min(15, hi0 + (expansion if y in {2, 3, 4} else 0))
        for x in range(lo, hi + 1):
            if x in {lo, hi} or y == 0:
                color = contour
            elif y >= 5 or x <= lo + 1:
                color = shadow
            elif x in {7, 8} and 2 <= y <= 5:
                color = crease if y in {3, 5} else lining
            elif x >= hi - 2 and y <= 3:
                color = light
            else:
                color = base
            frame[y][x] = color
    return frame


def _front_runtime_schematic(
    hood: list[list[RGBA]], *, old: bool
) -> list[list[RGBA]]:
    """Show anchor effect with a neutral mask, not fabricated Farmer art."""

    canvas = blank_image(32, 48)
    hood_x = (32 - len(hood[0])) // 2
    hood_y = 0 if old else 24
    blit(canvas, hood, hood_x, hood_y)
    # Neutral Player proxy. The hood is drawn first, so this masks its middle.
    draw_rect(canvas, 8, 8, 16, 32, (96, 90, 88, 255))
    return canvas


def _front_before_after_sheet(render) -> list[list[RGBA]]:
    old = _legacy_front_down(render)
    new = render.down.hood_default_frames["front"]
    scale = 4
    old_scene = nearest_scale(_front_runtime_schematic(old, old=True), scale)
    new_scene = nearest_scale(_front_runtime_schematic(new, old=False), scale)
    canvas = blank_image(620, 290, BG)
    draw_text(canvas, "FRONT HOOD-DOWN - BEFORE / AFTER", 8, 8, color=INK)
    draw_text(canvas, "SCHEMATIC PLAYER MASK; NOT A VANILLA FARMER COMPOSITE", 8, 21, color=MUTED)

    draw_text(canvas, "BEFORE", 82, 48, color=INK)
    draw_text(canvas, "16X32 / HEADPOSITION (0,32)", 24, 61, color=MUTED)
    _bordered(canvas, old_scene, 24, 78)

    draw_text(canvas, "AFTER", 394, 48, color=INK)
    draw_text(canvas, "24X32 / HEADPOSITION (-8,0)", 332, 61, color=MUTED)
    _bordered(canvas, new_scene, 332, 78)

    draw_text(canvas, "HEAD-LEVEL / NARROW", 56, 274, color=MUTED)
    draw_text(canvas, "TORSO-LEVEL / SHOULDER SPREAD", 348, 274, color=MUTED)
    return canvas


def _front_centering_sheet(render) -> list[list[RGBA]]:
    """Show the runtime X-origin correction using unchanged current art."""

    hood = render.down.hood_default_frames["front"]
    scale = 4

    def scene(hood_x: int):
        canvas = blank_image(48, 48)
        blit(canvas, hood, hood_x, 16)
        # Neutral Player proxy: the Hat is Before Player at runtime.
        draw_rect(canvas, 16, 8, 16, 32, (96, 90, 88, 255))
        return nearest_scale(canvas, scale)

    # Changing the SpriteBatch origin from +4 to -8 shifts the art twelve
    # logical cells / 24 display pixels right. The art itself is unchanged.
    old_scene = scene(0)
    new_scene = scene(12)
    canvas = blank_image(900, 270, BG)
    draw_text(canvas, "FRONT HOOD-DOWN X POSITION - UNCHANGED ART", 8, 8, color=INK)
    draw_text(canvas, "SCHEMATIC PLAYER MASK; POSITION CONTRACT ONLY", 8, 21, color=MUTED)
    draw_text(canvas, "BEFORE  HEADPOSITION X=4", 24, 48, color=MUTED)
    draw_text(canvas, "AFTER  HEADPOSITION X=-8", 484, 48, color=MUTED)
    _bordered(canvas, old_scene, 24, 66)
    _bordered(canvas, new_scene, 484, 66)
    draw_text(canvas, "LEFT-BIASED", 84, 258, color=MUTED)
    draw_text(canvas, "CENTERED OVER 16-CELL TORSO", 522, 258, color=MUTED)
    return canvas


def _legacy_up_front(render) -> list[list[RGBA]]:
    """Previous raised-front opening, retained only for the focused A/B."""

    upper = render.up.upper
    recipe = render.recipe
    frame = blank_image(32, 32)
    expansion = 1 if recipe["hoodLayer"]["volume"] == "baggy" else 0
    contrast = recipe["hoodLayer"]["lining"] == "contrast"
    contour = _default(upper, "EXTERIOR_CONTOUR")
    shadow = _default(upper, "SHADOW")
    base = _default(upper, "BASE")
    light = _default(upper, "LIGHT")
    lining = _solid(upper, "secondary" if contrast else "dark_accent")
    rows = (
        (14, 17), (12, 19), (10, 21), (8, 23), (7, 24), (6, 25),
        (5, 26), (5, 26), (4, 27), (4, 27), (4, 27), (4, 27),
        (4, 27), (4, 27), (4, 27), (4, 27), (4, 27), (4, 27),
        (4, 27), (4, 27), (5, 26), (5, 26), (6, 25), (7, 24),
        (8, 23), (9, 22),
    )
    opening = {
        y: (max(10, 15 - min(5, y - 10)), min(21, 16 + min(5, y - 10)))
        for y in range(11, 27)
    }
    for row_index, (lo0, hi0) in enumerate(rows):
        y = row_index + 6
        lo, hi = max(0, lo0 - expansion), min(31, hi0 + expansion)
        for x in range(lo, hi + 1):
            if y in opening and opening[y][0] <= x <= opening[y][1]:
                continue
            outer = x in {lo, hi} or y in {6, 31}
            near_open = y in opening and x in {opening[y][0] - 1, opening[y][1] + 1}
            if outer:
                color = contour
            elif near_open:
                color = lining
            elif x <= 7 or y >= 27:
                color = shadow
            elif x >= 22 and 11 <= y <= 23:
                color = light
            else:
                color = base
            frame[y][x] = color
    return frame


def _hood_up_front_before_after_sheet(render) -> list[list[RGBA]]:
    scale = 4

    def scene(hood, y_offset: int):
        canvas = blank_image(32, 38)
        # A neutral face proxy makes lower-rim encroachment visible without
        # pretending to reproduce Farmer art.
        draw_rect(canvas, 10, 9, 12, 23, (186, 139, 105, 255))
        blit(canvas, hood, 0, y_offset)
        return nearest_scale(canvas, scale)

    old_scene = scene(_legacy_up_front(render), 2)
    new_scene = scene(render.up.hood_default_frames["front"], 0)
    canvas = blank_image(620, 250, BG)
    draw_text(canvas, "HOOD-UP FRONT OPENING - BEFORE / AFTER", 8, 8, color=INK)
    draw_text(canvas, "NEUTRAL FACE PROXY; NOT A VANILLA FARMER COMPOSITE", 8, 21, color=MUTED)
    draw_text(canvas, "BEFORE  HEADPOSITION (-4,28)", 24, 50, color=MUTED)
    draw_text(canvas, "AFTER  HEADPOSITION (-4,30)", 332, 50, color=MUTED)
    _bordered(canvas, old_scene, 24, 68)
    _bordered(canvas, new_scene, 332, 68)
    draw_text(canvas, "LOWER RIM CLOSED", 72, 230, color=MUTED)
    draw_text(canvas, "OPEN THROUGH LOWER FACE", 372, 230, color=MUTED)
    return canvas


def _back_layer_order_sheet() -> list[list[RGBA]]:
    canvas = blank_image(640, 330, BG)
    draw_text(canvas, "HOOD-UP DIRECTIONAL LAYER AUDIT", 8, 8, color=INK)
    draw_text(canvas, "FASHION SENSE 7.5.0 - ALL FOUR RAISED DIRECTIONS", 8, 21, color=MUTED)

    def stack(x: int, title: str, rows):
        draw_text(canvas, title, x, 48, color=INK)
        for index, (label, color) in enumerate(rows):
            y = 72 + index * 54
            draw_rect(canvas, x, y, 230, 34, color)
            draw_text(canvas, label, x + 12, y + 12, color=(245, 238, 220, 255))

    stack(
        24,
        "BEFORE - EXPLICIT OVERRIDES",
        (
            ("PLAYER", (96, 90, 88, 255)),
            ("SHIRT", (62, 96, 104, 255)),
            ("HOOD FORCED BELOW HAIR", (116, 72, 72, 255)),
            ("HAIR / SLEEVES CAN BURY IT", (97, 67, 48, 255)),
        ),
    )
    stack(
        362,
        "AFTER - NATIVE HAT ORDER",
        (
            ("PLAYER", (96, 90, 88, 255)),
            ("SHIRT / HAIR / SLEEVES", (97, 67, 48, 255)),
            ("HOOD HAT - TOPMOST", (62, 130, 126, 255)),
            ("FACE/HAIR SHOW IN OPENING", (62, 96, 104, 255)),
        ),
    )
    draw_text(canvas, "NO HOOD-UP DRAWORDEROVERRIDE IN ANY DIRECTION", 300, 304, color=MUTED)
    return canvas


def _transition_sheet(render) -> list[list[RGBA]]:
    scale = 2
    w, h = 32 * scale, 48 * scale
    label_w = 150
    canvas = blank_image(label_w + w * 4 + 16 * 3 + 18, 72 + (h + 24) * 2, BG)
    draw_text(canvas, "WEATHER HOOD STATE COMPARISON", 8, 8, color=INK)
    draw_text(canvas, "CLEAR/INDOORS = DOWN   RAIN/SNOW/STORM OUTDOORS = UP", 8, 21, color=MUTED)
    for index, direction in enumerate(DIRECTIONS):
        draw_text(canvas, direction.upper(), label_w + index * (w + 16), 44, color=INK)
    for row, state in enumerate(("down", "up")):
        y = 64 + row * (h + 24)
        draw_text(canvas, state.upper(), 8, y + 8, color=INK)
        draw_text(canvas, "PRESERVE HAIR" if state == "up" else "HAIR NATURAL", 8, y + 22, color=MUTED)
        for index, direction in enumerate(DIRECTIONS):
            _bordered(canvas, nearest_scale(_assembled(render, state, direction), scale), label_w + index * (w + 16), y)
    return canvas


def _cp_content() -> dict[str, Any]:
    target_id = f"{FS_ID}/Hat/{BASE_HAT_NAME}"
    auto_back_id = f"{FS_ID}/Hat/{AUTO_BACK_HAT_NAME}"
    auto_front_id = f"{FS_ID}/Hat/{AUTO_FRONT_HAT_NAME}"
    directions = ("FrontHat", "BackHat", "LeftHat", "RightHat")

    def hair_fields(hidden: bool) -> dict[str, Any]:
        return {direction: {"HideHair": hidden} for direction in directions}

    def back_only_fields() -> dict[str, Any]:
        return {
            "FrontHat": {"HideHair": False},
            "RightHat": {"HideHair": False},
            "BackHat": {"HideHair": True},
            "LeftHat": {"HideHair": False},
        }

    def front_only_fields() -> dict[str, Any]:
        return {
            "FrontHat": {"HideHair": False},
            "RightHat": {"HideHair": True},
            "BackHat": {"HideHair": True},
            "LeftHat": {"HideHair": True},
        }

    changes = [
            {
                "LogName": "Preserve hair while hood is down",
                "Action": "EditData",
                "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                "TargetField": [target_id],
                "Fields": hair_fields(False),
                "When": {
                    "Query: {{IsOutdoors}} = false OR '{{Weather}}' NOT IN ('Snow', 'Rain', 'Storm')": True
                },
                "Update": "OnDayStart, OnLocationChange",
            },
            {
                "LogName": "Preserve hair inside raised weather hood",
                "Action": "EditData",
                "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                "TargetField": [target_id],
                "Fields": hair_fields(False),
                "When": {
                    "HoodUpHairMode": "PreserveHair",
                    "IsOutdoors": True,
                    "Weather": "Rain, Storm, Snow",
                },
                "Update": "OnDayStart, OnLocationChange",
            },
            {
                "LogName": "Hide only back hair inside raised weather hood",
                "Action": "EditData",
                "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                "TargetField": [target_id],
                "Fields": back_only_fields(),
                "When": {
                    "HoodUpHairMode": "HideBackOnly",
                    "IsOutdoors": True,
                    "Weather": "Rain, Storm, Snow",
                },
                "Update": "OnDayStart, OnLocationChange",
            },
            {
                "LogName": "Preserve only front hair inside raised weather hood",
                "Action": "EditData",
                "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                "TargetField": [target_id],
                "Fields": front_only_fields(),
                "When": {
                    "HoodUpHairMode": "PreserveFrontOnly",
                    "IsOutdoors": True,
                    "Weather": "Rain, Storm, Snow",
                },
                "Update": "OnDayStart, OnLocationChange",
            },
            {
                "LogName": "Hide hair inside raised weather hood fallback",
                "Action": "EditData",
                "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                "TargetField": [target_id],
                "Fields": hair_fields(True),
                "When": {
                    "HoodUpHairMode": "HideHair",
                    "IsOutdoors": True,
                    "Weather": "Rain, Storm, Snow",
                },
                "Update": "OnDayStart, OnLocationChange",
            },
        ]

    # The optional SMAPI selector swaps only between these two locked Hat
    # appearances. Their pixels, animation, anchors, and dye mask are exact
    # copies of the player-facing Hat; Content Patcher changes only HideHair.
    for appearance_id, up_fields, label in (
        (auto_back_id, back_only_fields(), "automatic HideBackOnly"),
        (auto_front_id, front_only_fields(), "automatic PreserveFrontOnly"),
    ):
        changes.extend(
            [
                {
                    "LogName": f"Preserve hair while {label} hood is down",
                    "Action": "EditData",
                    "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                    "TargetField": [appearance_id],
                    "Fields": hair_fields(False),
                    "When": {
                        "Query: {{IsOutdoors}} = false OR '{{Weather}}' NOT IN ('Snow', 'Rain', 'Storm')": True
                    },
                    "Update": "OnDayStart, OnLocationChange",
                },
                {
                    "LogName": f"Apply {label} while hood is raised",
                    "Action": "EditData",
                    "Target": "Data/PeacefulEnd/FashionSense/AppearanceData",
                    "TargetField": [appearance_id],
                    "Fields": up_fields,
                    "When": {
                        "IsOutdoors": True,
                        "Weather": "Rain, Storm, Snow",
                    },
                    "Update": "OnDayStart, OnLocationChange",
                },
            ]
        )

    return {
        "Format": "2.9.0",
        "ConfigSchema": {
            "HoodUpHairMode": {
                "AllowValues": "PreserveHair, HideBackOnly, PreserveFrontOnly, HideHair",
                # Raised side art now masks lower/rear hair while preserving
                # full side Hair. Hide only the back direction by default.
                "Default": "HideBackOnly",
            }
        },
        "Changes": changes,
    }


def main() -> None:
    recipe = _recipe()
    render = render_fs_weather_hood(recipe)
    OUT.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)

    write_rgba_png(OUT / "weather-hood.png", render.texture)
    write_rgba_png(OUT / "shirt.png", render.down.shirt_texture)
    down_sheet = _state_sheet(render, "down")
    up_sheet = _state_sheet(render, "up")
    transition = _transition_sheet(render)
    down_layering = _hood_down_front_layering_sheet(render)
    front_before_after = _front_before_after_sheet(render)
    front_centering = _front_centering_sheet(render)
    hood_up_front_before_after = _hood_up_front_before_after_sheet(render)
    back_layer_order = _back_layer_order_sheet()
    write_rgba_png(OUT / "HOOD_DOWN_DIRECTIONS.png", down_sheet)
    write_rgba_png(OUT / "HOOD_UP_DIRECTIONS.png", up_sheet)
    write_rgba_png(OUT / "WEATHER_HOOD_STATE_COMPARISON.png", transition)
    write_rgba_png(OUT / "HOOD_DOWN_FRONT_LAYERING.png", down_layering)
    write_rgba_png(OUT / "FRONT_HOOD_DOWN_BEFORE_AFTER.png", front_before_after)
    write_rgba_png(OUT / "FRONT_HOOD_DOWN_CENTERING.png", front_centering)
    write_rgba_png(OUT / "HOOD_UP_FRONT_BEFORE_AFTER.png", hood_up_front_before_after)
    write_rgba_png(OUT / "BACK_HOOD_LAYER_ORDER.png", back_layer_order)
    write_rgba_png(OUT / "HOOD_UP_DIRECTIONAL_LAYER_AUDIT.png", back_layer_order)
    write_rgba_png(COMPARE / "WEATHER_HOOD_STATE_COMPARISON.png", transition)
    write_rgba_png(COMPARE / "HOOD_DOWN_FRONT_LAYERING.png", down_layering)
    write_rgba_png(COMPARE / "FRONT_HOOD_DOWN_BEFORE_AFTER.png", front_before_after)
    write_rgba_png(COMPARE / "FRONT_HOOD_DOWN_CENTERING.png", front_centering)
    write_rgba_png(COMPARE / "HOOD_UP_FRONT_BEFORE_AFTER.png", hood_up_front_before_after)
    write_rgba_png(COMPARE / "BACK_HOOD_LAYER_ORDER.png", back_layer_order)
    write_rgba_png(COMPARE / "HOOD_UP_DIRECTIONAL_LAYER_AUDIT.png", back_layer_order)
    _json(OUT / "recipe.json", recipe)
    _json(OUT / "frame-map.json", render.frame_map)

    shirt_dir = FS_PACK / "Shirts" / "HarborHazeWeatherHoodie"
    hat_dir = FS_PACK / "Hats" / "HarborHazeWeatherHood"
    _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
    write_rgba_png(shirt_dir / "shirt.png", render.down.shirt_texture)
    _json(hat_dir / "hat.json", render.hat_json)
    write_rgba_png(hat_dir / "hat.png", render.texture)
    for folder_name, appearance_name in (
        ("HarborHazeWeatherHoodAutoBack", AUTO_BACK_HAT_NAME),
        ("HarborHazeWeatherHoodAutoFront", AUTO_FRONT_HAT_NAME),
    ):
        internal_hat = copy.deepcopy(render.hat_json)
        internal_hat["Name"] = appearance_name
        internal_hat["IsLocked"] = True
        internal_hat["Tags"] = [*internal_hat["Tags"], "Automatic Hair Policy", "Internal"]
        internal_dir = FS_PACK / "Hats" / folder_name
        _json(internal_dir / "hat.json", internal_hat)
        write_rgba_png(internal_dir / "hat.png", render.texture)
    _json(FS_PACK / "conditions.json", render.conditions_json)
    _json(FS_PACK / "preset_outfits.json", [_preset(recipe)])
    _json(FS_PACK / "manifest.json", {
        "Name": "RNG Clothing Hoodie Weather Test",
        "Author": "RNG Clothing Experiment",
        "Version": "1.6.0",
        "Description": "One experimental Fashion Sense hoodie with automatic weather hood frames.",
        "UniqueID": FS_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(FS_PACK / "i18n" / "default.json", {
        "hoodie.weather.name": recipe["itemName"],
        "hoodie.weather.description": recipe["itemDescription"],
    })

    _json(CP_PACK / "manifest.json", {
        "Name": "RNG Clothing Hoodie Weather Hair Policy",
        "Author": "RNG Clothing Experiment",
        "Version": "1.4.0",
        "Description": "Direction-aware PreserveHair/HideBackOnly/PreserveFrontOnly/HideHair policy for the experimental weather hood.",
        "UniqueID": "RNGClothing.ContentPatcher.HoodieWeatherTest",
        "UpdateKeys": [],
        "Dependencies": [
            {"UniqueID": FS_ID, "IsRequired": True},
            {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0", "IsRequired": True},
        ],
        "ContentPackFor": {"UniqueID": "Pathoschild.ContentPatcher", "MinimumVersion": "2.9.1"},
    })
    _json(CP_PACK / "config.json", {"HoodUpHairMode": "HideBackOnly"})
    _json(CP_PACK / "content.json", _cp_content())

    TEST_ROOT.mkdir(parents=True, exist_ok=True)
    (TEST_ROOT / "README.md").write_text(
        """# RNG Clothing Hoodie Weather Test

Copy the `[FS]` and `[CP]` child folders into Stardew Valley's `Mods` folder, then fully restart SMAPI. Copy the `[SMAPI]` child too if you want automatic vanilla-hairstyle policy selection. The Fashion Sense child is version **1.6.0**, the Content Patcher child is version **1.4.0**, and the optional helper is version **1.0.0**.

Equip **Hoodie Weather Test - Harbor Haze** from Fashion Sense > Outfits > Presets.

- Indoors or outdoors without precipitation: hood down with normal Hair preserved.
- Outdoors in rain, storm, or snow: hood up.
- Without the optional helper, `HoodUpHairMode` remains manually configurable as `PreserveHair`, `HideBackOnly`, `PreserveFrontOnly`, or `HideHair`.
- With the helper, passing audited vanilla styles automatically use `HideBackOnly`.
- Severe vanilla side-clipping styles automatically use `PreserveFrontOnly`; IDs `28`, `100`, and `115` do so only on the feminine vanilla body branch.
- Unsupported custom/Fashion Sense Hair, unrecognized Hair IDs, and custom Fashion Sense bodies fail open to the normal configured policy.
- The helper is narrowly scoped to this exact Shirt and Hat. It contains no draw code, clipping, Harmony, or renderer patches.
- The helper checks the local Farmer four times per second and writes only when the desired Hat policy changes.
- Each multiplayer player who wants automatic selection should install the same three child folders.

This remains an EXPERIMENTAL runtime test. Fashion Sense selects state frames, Content Patcher controls state-sensitive `HideHair`, and the optional helper selects one of two locked, pixel-identical Hat policies.
""",
        encoding="utf-8",
    )
    print(OUT)
    print(TEST_ROOT)


if __name__ == "__main__":
    main()
