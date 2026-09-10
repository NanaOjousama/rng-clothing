#!/usr/bin/env python3
"""Static validation for the isolated hoodie weather-state test."""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hoodie_layers import generate_hoodie_layer_batch
from generator.png_utils import read_rgba_png
from generator.renderers.fashionsense.hoodie_weather import (
    DIRECTIONS,
    MODEL_KEYS,
    render_fs_weather_hood,
)


OUT = ROOT / "output" / "fashionsense" / "hoodie-weather-test"
TEST_ROOT = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Hoodie-Weather-Test"
FS_PACK = TEST_ROOT / "[FS] RNG Clothing Hoodie Weather Test"
CP_PACK = TEST_ROOT / "[CP] RNG Clothing Hoodie Weather Test"
FS_ID = "RNGClothing.FashionSense.HoodieWeatherTest"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _binary_alpha(png: dict) -> bool:
    return all(pixel[3] in {0, 255} for row in png["pixels"] for pixel in row)


def _opaque_is_connected(frame) -> bool:
    opaque = {
        (x, y)
        for y, row in enumerate(frame)
        for x, pixel in enumerate(row)
        if pixel[3]
    }
    if not opaque:
        return False
    pending = [next(iter(opaque))]
    visited = set()
    while pending:
        x, y = pending.pop()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        pending.extend(
            neighbor
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if neighbor in opaque and neighbor not in visited
        )
    return visited == opaque


def _recipe():
    import copy

    recipe = copy.deepcopy(generate_hoodie_layer_batch()["recipes"][0])
    recipe["id"] = "hoodie-weather-test-01"
    recipe["itemName"] = "Harbor Haze Weather Hoodie"
    recipe["itemDescription"] = "A sea-glass hoodie whose hood rises outdoors in rain or snow."
    recipe["hoodLayer"]["state"] = "down"
    return recipe


def main() -> None:
    errors: list[str] = []
    checks: list[str] = []
    render = render_fs_weather_hood(_recipe())
    rerender = render_fs_weather_hood(_recipe())
    if render.texture != rerender.texture or render.down.shirt_texture != rerender.down.shirt_texture:
        errors.append("weather hood render is not deterministic")
    else:
        checks.append("deterministic Shirt and eight-state Hat texture")

    hood_png = read_rgba_png(OUT / "weather-hood.png")
    shirt_png = read_rgba_png(OUT / "shirt.png")
    if hashlib.sha256((OUT / "shirt.png").read_bytes()).hexdigest() != "6238c8f9615a94963711a9daf0548f373ff7ea165870fd07d867c3c245d6457e":
        errors.append("protected working Shirt pixels changed during hood-only polish")
    else:
        checks.append("working Shirt remains byte-identical through hood-only polish")
    if (hood_png["width"], hood_png["height"]) != (128, 64):
        errors.append("dynamic Hat texture must be 128x64 (eight 32x32 cells)")
    if hood_png["pixels"] != render.texture:
        errors.append("output dynamic Hat differs from renderer")
    if shirt_png["pixels"] != render.down.shirt_texture:
        errors.append("output Shirt differs from renderer")
    if not _binary_alpha(hood_png) or not _binary_alpha(shirt_png):
        errors.append("weather test textures must use binary alpha")

    for state in ("down", "up"):
        source = render.down if state == "down" else render.up
        for direction in DIRECTIONS:
            if not any(pixel[3] for row in source.hood_frames[direction] for pixel in row):
                errors.append(f"{state} {direction}: empty hood art")
    if not errors:
        checks.append("complete front/right/back/left art for both hood states")
    down_front = render.down.hood_frames["front"]
    if not _opaque_is_connected(down_front):
        errors.append("lowered front hood must be one connected folded mass")
    if not any(down_front[y][x][3] for y in range(2, 7) for x in (11, 12)):
        errors.append("lowered front hood lost complete center fabric")
    front_opaque_x = {
        x
        for row in down_front
        for x, pixel in enumerate(row)
        if pixel[3]
    }
    if len(front_opaque_x) < 22:
        errors.append("lowered front hood lacks readable shoulder spread")
    raised_front = render.up.hood_frames["front"]
    if any(raised_front[y][x][3] for y in range(27, 32) for x in range(12, 20)):
        errors.append("raised front lower opening can cover the mouth")
    if not any("lowered front hood" in error for error in errors):
        checks.append("complete lowered front hood uses Player occlusion instead of an art cutout")
    raised_side = render.up.hood_frames["right"]
    if not all(any(pixel[3] for pixel in raised_side[y]) for y in (30, 31)):
        errors.append("micro-polished raised side lost its tapered neck termination")
    if not all(raised_front[30][x][3] for x in (7, 8, 23, 24)):
        errors.append("micro-polished raised front lost its shoulder connection")
    if any(raised_side[16][x][3] for x in range(16, 21)):
        errors.append("raised side visual mask blocks the upper/front hair opening")
    if not all(raised_side[y][x][3] for y, x in ((22, 10), (23, 11), (24, 12), (25, 13), (26, 13))):
        errors.append("raised side hood lacks the diagonal lower/rear hair-masking plane")

    fs_manifest = _json(FS_PACK / "manifest.json")
    cp_manifest = _json(CP_PACK / "manifest.json")
    if fs_manifest.get("UniqueID") != FS_ID or fs_manifest.get("ContentPackFor") != {
        "UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"
    }:
        errors.append("invalid Fashion Sense weather-test manifest")
    if fs_manifest.get("Version") != "1.6.0":
        errors.append("automatic-policy weather pack must be version 1.6.0")
    if cp_manifest.get("ContentPackFor") != {
        "UniqueID": "Pathoschild.ContentPatcher", "MinimumVersion": "2.9.1"
    }:
        errors.append("invalid Content Patcher weather-policy manifest")
    if cp_manifest.get("Version") != "1.4.0":
        errors.append("automatic hair-policy data pack must be version 1.4.0")

    hat_json = _json(FS_PACK / "Hats" / "HarborHazeWeatherHood" / "hat.json")
    packed_hat = read_rgba_png(FS_PACK / "Hats" / "HarborHazeWeatherHood" / "hat.png")
    if packed_hat["pixels"] != render.texture:
        errors.append("packed dynamic Hat differs from output")
    expected_up_heads = {
        "front": {"X": -4, "Y": 30},
        "right": {"X": -4, "Y": 26},
        "back": {"X": -4, "Y": 26},
        "left": {"X": -4, "Y": 26},
    }
    expected_down_heads = {
        "front": {"X": -8, "Y": 0},
        "right": {"X": -6, "Y": 0},
        "back": {"X": -12, "Y": -2},
        "left": {"X": -18, "Y": 0},
    }
    for direction in DIRECTIONS:
        key = MODEL_KEYS[direction]
        model = hat_json[key]
        if model.get("Scale") != 2.0 or model.get("HatSize") != {"Width": 32, "Length": 32}:
            errors.append(f"{direction}: invalid dynamic Hat Scale/size")
        if model.get("HeadPosition") != expected_up_heads[direction]:
            errors.append(f"{direction}: wrong raised-hood base origin")
        if model.get("HideHair") is not False:
            errors.append(f"{direction}: PreserveHair base model must preserve Hair")
        animations = model.get("UniformAnimation", [])
        if len(animations) != 2:
            errors.append(f"{direction}: expected exactly two conditional state frames")
            continue
        up_animation, down_animation = animations
        if up_animation.get("Frame") != render.frame_map["up"][direction]:
            errors.append(f"{direction}: wrong hood-up frame")
        if down_animation.get("Frame") != render.frame_map["down"][direction]:
            errors.append(f"{direction}: wrong hood-down frame")
        expected_offset = {
            axis: expected_down_heads[direction][axis] - expected_up_heads[direction][axis]
            for axis in ("X", "Y")
        }
        if down_animation.get("Offset") != expected_offset:
            errors.append(f"{direction}: down-state animation offset loses calibrated origin")
        expected_down_order = (
            {"Preposition": "After", "AppearanceType": "Shirt"}
            if direction == "back"
            else {"Preposition": "Before", "AppearanceType": "Player"}
        )
        if down_animation.get("DrawOrderOverride") != expected_down_order:
            errors.append(f"{direction}: wrong lowered-hood draw order")
        if "DrawOrderOverride" in up_animation:
            errors.append(f"{direction}: raised hood must use native topmost Hat order")
    if not any("dynamic Hat" in error or "hood" in error.lower() for error in errors):
        checks.append("conditional Hat frames retain calibrated per-state anchors and draw order")

    conditions = _json(FS_PACK / "conditions.json")
    if conditions != render.conditions_json:
        errors.append("packed Fashion Sense conditions differ from renderer contract")
    for required in ("HasPrecipitation", "IsOutdoorsAndHasPrecipitation", "IsOutdoorsAndNoPrecipitation"):
        if required not in conditions:
            errors.append(f"missing Fashion Sense condition group {required}")
    else:
        checks.append("Fashion Sense rain/snow/outdoor condition groups present")

    cp_content = _json(CP_PACK / "content.json")
    if cp_content.get("Format") != "2.9.0":
        errors.append("Content Patcher weather policy must target format 2.9.0")
    schema = cp_content.get("ConfigSchema", {}).get("HoodUpHairMode", {})
    if schema.get("AllowValues") != "PreserveHair, HideBackOnly, PreserveFrontOnly, HideHair" or schema.get("Default") != "HideBackOnly":
        errors.append("direction-aware hair-mode schema is invalid")
    expected_target = f"{FS_ID}/Hat/Harbor Haze Weather Hood"
    changes = cp_content.get("Changes", [])
    base_changes = [change for change in changes if change.get("TargetField") == [expected_target]]
    if len(base_changes) != 5:
        errors.append("Content Patcher hair-policy edits target the wrong appearance")
    if _json(CP_PACK / "config.json") != {"HoodUpHairMode": "HideBackOnly"}:
        errors.append("HideBackOnly must preserve side Hair for the visual-mask test")
    else:
        checks.append("HideBackOnly default preserves side Hair for Hat-layer masking")

    change_by_mode = {
        change.get("When", {}).get("HoodUpHairMode"): change
        for change in base_changes
        if change.get("When", {}).get("HoodUpHairMode")
    }
    expected_hair_fields = {
        "PreserveHair": {
            direction: {"HideHair": False}
            for direction in ("FrontHat", "BackHat", "LeftHat", "RightHat")
        },
        "HideBackOnly": {
            "FrontHat": {"HideHair": False},
            "RightHat": {"HideHair": False},
            "BackHat": {"HideHair": True},
            "LeftHat": {"HideHair": False},
        },
        "PreserveFrontOnly": {
            "FrontHat": {"HideHair": False},
            "RightHat": {"HideHair": True},
            "BackHat": {"HideHair": True},
            "LeftHat": {"HideHair": True},
        },
        "HideHair": {
            direction: {"HideHair": True}
            for direction in ("FrontHat", "BackHat", "LeftHat", "RightHat")
        },
    }
    for mode, expected_fields in expected_hair_fields.items():
        if change_by_mode.get(mode, {}).get("Fields") != expected_fields:
            errors.append(f"{mode}: wrong direction-specific HideHair policy")

    internal_hats = {
        "Harbor Haze Weather Hood - Auto HideBackOnly": expected_hair_fields["HideBackOnly"],
        "Harbor Haze Weather Hood - Auto PreserveFrontOnly": expected_hair_fields["PreserveFrontOnly"],
    }
    for folder, name in (
        ("HarborHazeWeatherHoodAutoBack", "Harbor Haze Weather Hood - Auto HideBackOnly"),
        ("HarborHazeWeatherHoodAutoFront", "Harbor Haze Weather Hood - Auto PreserveFrontOnly"),
    ):
        internal_dir = FS_PACK / "Hats" / folder
        internal_json = _json(internal_dir / "hat.json")
        internal_png = read_rgba_png(internal_dir / "hat.png")
        if internal_json.get("Name") != name or internal_json.get("IsLocked") is not True:
            errors.append(f"{name}: automatic policy Hat must be locked and correctly named")
        if internal_png["pixels"] != packed_hat["pixels"]:
            errors.append(f"{name}: automatic policy Hat pixels differ from the base Hat")
        target = f"{FS_ID}/Hat/{name}"
        target_changes = [change for change in changes if change.get("TargetField") == [target]]
        if len(target_changes) != 2:
            errors.append(f"{name}: expected one hood-down and one hood-up policy edit")
            continue
        raised = next((change for change in target_changes if change.get("When", {}).get("IsOutdoors") is True), None)
        if raised is None or raised.get("Fields") != internal_hats[name]:
            errors.append(f"{name}: wrong automatic raised-hood HideHair policy")

    preset = _json(FS_PACK / "preset_outfits.json")
    if len(preset) != 1:
        errors.append("weather test must contain exactly one preset")
    else:
        preset = preset[0]
        if preset.get("HatId") != f"{FS_ID}/Hat/Harbor Haze Weather Hood":
            errors.append("weather preset selects wrong Hat")
        if preset.get("SleevesId") != "None" or preset.get("AccessoryIds") != ["None", "None", "None"]:
            errors.append("weather preset must preserve native sleeves and in-Shirt strings")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "appearanceCount": 3,
        "hoodStates": ["down", "up"],
        "directionCountPerState": 4,
        "automaticRule": "outdoors + rain/snow (storm through IsRaining) => up; otherwise down",
        "hairModes": ["PreserveHair", "HideBackOnly", "PreserveFrontOnly", "HideHair"],
        "defaultHairMode": "HideBackOnly",
        "reason": "Raised side Hat art now visually masks lower/rear side hair while preserving the full hairstyle.",
        "runtimePromotion": "EXPERIMENTAL",
    }
    (OUT / "validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
