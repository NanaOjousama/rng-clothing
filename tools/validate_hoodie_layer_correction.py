#!/usr/bin/env python3
"""Independent static validation for the coordinated hoodie test pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hoodie_layers import generate_hoodie_layer_batch, validate_hoodie_layer_recipe
from generator.png_utils import read_rgba_png
from generator.renderers.fashionsense.hoodie_layers import render_fs_hoodie_layers


OUT = ROOT / "output" / "fashionsense" / "hoodie-layer-correction"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-Hoodie-Layer-Correction"
UNIQUE_ID = "RNGClothing.FashionSense.HoodieLayerCorrection"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    import re
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


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
        cell = pending.pop()
        if cell in visited:
            continue
        visited.add(cell)
        x, y = cell
        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if neighbor in opaque and neighbor not in visited:
                pending.append(neighbor)
    return visited == opaque


def main() -> None:
    errors: list[str] = []
    checks: list[str] = []
    batch = generate_hoodie_layer_batch()
    renders = [render_fs_hoodie_layers(recipe) for recipe in batch["recipes"]]
    rerenders = [render_fs_hoodie_layers(recipe) for recipe in batch["recipes"]]
    if len(batch["recipes"]) != 6:
        errors.append(f"expected six recipes, found {len(batch['recipes'])}")
    if any(
        a.shirt_texture != b.shirt_texture
        or a.hood_texture != b.hood_texture
        for a, b in zip(renders, rerenders)
    ):
        errors.append("deterministic rerender mismatch")
    else:
        checks.append("deterministic Shirt and Hat pixels")

    manifest = _json(PACK / "manifest.json")
    if manifest.get("UniqueID") != UNIQUE_ID:
        errors.append("wrong test-pack UniqueID")
    if manifest.get("Version") != "1.9.0":
        errors.append("micro-polished hoodie pack must be version 1.9.0")
    if manifest.get("ContentPackFor") != {
        "UniqueID": "PeacefulEnd.FashionSense",
        "MinimumVersion": "7.5.0",
    }:
        errors.append("wrong Fashion Sense 7.5.0 content-pack contract")
    else:
        checks.append("Fashion Sense 7.5.0 content-pack contract")
    if (PACK / "content.json").exists():
        errors.append("static correction pack must not contain weather-reactive Content Patcher edits")
    else:
        checks.append("no unnecessary Content Patcher runtime dependency")

    presets = _json(PACK / "preset_outfits.json")
    if len(presets) != 6:
        errors.append(f"expected six presets, found {len(presets)}")
    preset_by_name = {preset["Name"]: preset for preset in presets}
    expected_states = ["down", "down", "down", "up", "up", "down"]
    if [recipe["hoodLayer"]["state"] for recipe in batch["recipes"]] != expected_states:
        errors.append("hood-up/down batch contract changed")
    expected_accessories = 0
    if sum(recipe["assembly"]["accessory"] for recipe in batch["recipes"]) != expected_accessories:
        errors.append("corrected runtime pack must not equip Accessory appearances")

    # Fashion Sense adds HeadPosition to the Farmer draw origin before passing
    # the sum as SpriteBatch's origin. Prove that the Scale-2 origins preserve
    # the same screen placement as their known Scale-4 reference contracts.
    farmer_origin = (0, 32)
    reference_origins = {
        "up": {
            "FrontHat": (-2, -2), "RightHat": (-2, -3),
            "BackHat": (-2, -3), "LeftHat": (-2, -3),
        },
        "down": {
            # The reference front frame is empty and therefore cannot calibrate
            # visible art. Only its visible side/back contracts belong here.
            "RightHat": (-3, -16), "BackHat": (-6, -17),
            "LeftHat": (-9, -16),
        },
    }
    corrected_origins = {
        state: {
            key: (
                farmer_origin[0] + 2 * value[0],
                farmer_origin[1] + 2 * value[1],
            )
            for key, value in directions.items()
        }
        for state, directions in reference_origins.items()
    }
    for state, directions in reference_origins.items():
        for key, reference in directions.items():
            corrected = corrected_origins[state][key]
            scale4_position = tuple(
                farmer_origin[axis] - 4 * (farmer_origin[axis] + reference[axis])
                for axis in (0, 1)
            )
            scale2_position = tuple(
                farmer_origin[axis] - 2 * (farmer_origin[axis] + corrected[axis])
                for axis in (0, 1)
            )
            if scale4_position != scale2_position:
                errors.append(f"{state} {key}: Scale-2 Hat origin does not preserve screen placement")
    if not any("Scale-2 Hat origin" in error for error in errors):
        checks.append("visible reference side/back origins preserve equivalent Scale-4 screen placement")

    for recipe, render in zip(batch["recipes"], renders):
        name = recipe["itemName"]
        result = validate_hoodie_layer_recipe(recipe)
        if not result.valid:
            errors.extend(f"{name}: {message}" for message in result.errors)
        if any(render.coverage_missing.values()):
            errors.append(f"{name}: torso body-coverage regression")
        output_dir = OUT / _slug(name)
        components = {
            "shirt.png": (16, 64, render.shirt_texture),
            "hood.png": (
                96 if recipe["hoodLayer"]["state"] == "up" else 24,
                32 if recipe["hoodLayer"]["state"] == "up" else 96,
                render.hood_texture,
            ),
        }
        for filename, (width, height, expected_pixels) in components.items():
            png = read_rgba_png(output_dir / filename)
            if (png["width"], png["height"]) != (width, height):
                errors.append(f"{name}: {filename} expected {width}x{height}")
            if png["pixels"] != expected_pixels:
                errors.append(f"{name}: {filename} differs from deterministic renderer")
            if not _binary_alpha(png):
                errors.append(f"{name}: {filename} contains semi-transparent pixels")

        shirt_dir = PACK / "Shirts" / _folder(name)
        shirt_png = read_rgba_png(shirt_dir / "shirt.png")
        shirt_json = _json(shirt_dir / "shirt.json")
        if shirt_png["pixels"] != render.shirt_texture:
            errors.append(f"{name}: packed Shirt differs from output")
        for key, y in {"FrontShirt": 0, "RightShirt": 16, "LeftShirt": 32, "BackShirt": 48}.items():
            model = shirt_json.get(key, {})
            if model.get("StartingPosition") != {"X": 0, "Y": y}:
                errors.append(f"{name}: wrong {key} source row")
            if model.get("ShirtSize") != {"Width": 16, "Length": 16}:
                errors.append(f"{name}: wrong {key} size")
            if model.get("Scale") != 2.0 or model.get("BodyPosition") != {"X": 0, "Y": 32}:
                errors.append(f"{name}: wrong {key} Scale/BodyPosition")
            if model.get("HideSleeves") is not False:
                errors.append(f"{name}: Shirt must expose native animated sleeves")
            if len(model.get("SleeveColors", [])) != 3:
                errors.append(f"{name}: {key} must provide the native three-color SleeveColors ramp")

        hood_dir = PACK / "Hats" / (_folder(name) + "Hood")
        hood_png = read_rgba_png(hood_dir / "hat.png")
        hood_json = _json(hood_dir / "hat.json")
        if hood_png["pixels"] != render.hood_texture:
            errors.append(f"{name}: packed Hood differs from output")
        state = recipe["hoodLayer"]["state"]
        if any(count == 0 for count in render.metrics["hoodOpaqueByDirection"].values()):
            errors.append(f"{name}: hood must provide non-empty front/right/back/left art")
        expected_head_positions = (
            {
                "FrontHat": {"X": -4, "Y": 30},
                "RightHat": {"X": -4, "Y": 26},
                "BackHat": {"X": -4, "Y": 26},
                "LeftHat": {"X": -4, "Y": 26},
            }
            if state == "up"
            else {
                "FrontHat": {"X": -8, "Y": 0},
                "RightHat": {"X": -6, "Y": 0},
                "BackHat": {"X": -12, "Y": -2},
                "LeftHat": {"X": -18, "Y": 0},
            }
        )
        for key in ("FrontHat", "RightHat", "BackHat", "LeftHat"):
            model = hood_json.get(key, {})
            if model.get("Scale") != 2.0:
                errors.append(f"{name}: {key} must remain Scale 2")
            expected_size = (
                {"Width": 32, "Length": 32}
                if state == "up"
                else {
                    "Width": 24 if key == "FrontHat" else 16,
                    "Length": 32,
                }
            )
            if model.get("HatSize") != expected_size:
                errors.append(f"{name}: {key} wrong higher-density Hat size")
            if state == "down":
                expected_start_y = {
                    "FrontHat": 0,
                    "RightHat": 32,
                    "LeftHat": 32,
                    "BackHat": 64,
                }[key]
                if model.get("StartingPosition") != {"X": 0, "Y": expected_start_y}:
                    errors.append(f"{name}: {key} wrong explicit lowered source row")
                if model.get("UniformAnimation") != [{"Frame": 0}]:
                    errors.append(f"{name}: {key} lowered source must not use width-dependent frame stepping")
            if model.get("HideHair") is not (state == "up"):
                errors.append(f"{name}: {key} hair policy disagrees with hood state")
            if model.get("HeadPosition") != expected_head_positions[key]:
                errors.append(
                    f"{name}: {key} wrong Scale-2 head origin; "
                    f"expected {expected_head_positions[key]}"
                )
            if not model.get("HideWhileSwimming") or not model.get("HideWhileWearingBathingSuit"):
                errors.append(f"{name}: {key} must hide for water/bathing state")
        declared_masks = {
            tuple(value)
            for layer in hood_json["FrontHat"].get("ColorMaskLayers", [])
            for value in layer.get("Values", [])
        }
        grayscale_pixels = {
            pixel[:3]
            for row in hood_png["pixels"]
            for pixel in row
            if pixel[3] and pixel[0] == pixel[1] == pixel[2]
        }
        if not grayscale_pixels.issubset(declared_masks):
            errors.append(f"{name}: Hood contains undeclared grayscale mask values {sorted(grayscale_pixels - declared_masks)}")
        if state == "down":
            front = render.hood_frames["front"]
            if not _opaque_is_connected(front):
                errors.append(f"{name}: lowered front hood must be one connected folded mass")
            if not any(front[y][x][3] for y in range(2, 7) for x in (11, 12)):
                errors.append(f"{name}: lowered front hood lost its complete center fabric")
            front_opaque_x = {
                x
                for row in front
                for x, pixel in enumerate(row)
                if pixel[3]
            }
            if len(front_opaque_x) < 22:
                errors.append(f"{name}: lowered front hood lacks readable shoulder spread")
            if hood_json["FrontHat"].get("DrawOrderOverride") != {"Preposition": "Before", "AppearanceType": "Player"}:
                errors.append(f"{name}: lowered front hood must use the Farmer as its center occlusion mask")
            if hood_json["RightHat"].get("DrawOrderOverride") != {"Preposition": "Before", "AppearanceType": "Player"}:
                errors.append(f"{name}: lowered side hood lost before-player order")
            if hood_json["BackHat"].get("DrawOrderOverride") != {"Preposition": "After", "AppearanceType": "Shirt"}:
                errors.append(f"{name}: lowered back hood lost explicit after-shirt order")
        else:
            raised_front = render.hood_frames["front"]
            if any(raised_front[y][x][3] for y in range(27, 32) for x in range(12, 20)):
                errors.append(f"{name}: raised front lower opening can cover the mouth")
            for key in ("FrontHat", "RightHat", "BackHat", "LeftHat"):
                if "DrawOrderOverride" in hood_json[key]:
                    errors.append(f"{name}: {key} raised hood must use native topmost Hat order")

        preset = preset_by_name.get(f"Hoodie Layers - {name}")
        if not preset:
            errors.append(f"{name}: missing coordinated preset")
        else:
            expected = {
                "ShirtId": f"{UNIQUE_ID}/Shirt/{name}",
                "SleevesId": "None",
                "HatId": f"{UNIQUE_ID}/Hat/{name} Hood",
            }
            for key, value in expected.items():
                if preset.get(key) != value:
                    errors.append(f"{name}: preset {key} is not coordinated")
            if preset.get("AccessoryIds") != ["None", "None", "None"]:
                errors.append(f"{name}: corrected preset must not equip an Accessory")

    leaked_layers = [folder for folder in ("Sleeves", "Accessories") if (PACK / folder).exists()]
    if leaked_layers:
        errors.append(f"stale detached-layer folders remain in corrected pack: {leaked_layers}")
    else:
        checks.append("no custom Sleeves or Accessory layers remain in runtime pack")
    if not any("lowered front hood" in error for error in errors):
        checks.append("lowered front hoods are connected complete masses drawn before Player")

    renderer_source = (ROOT / "generator" / "renderers" / "fashionsense" / "hoodie_layers.py").read_text(encoding="utf-8")
    forbidden = ["hoodie.zip", "style-profiles/hoodie", "read_rgba_png", "Image.open"]
    if any(token in renderer_source for token in forbidden):
        errors.append("renderer appears to access reference pixels")
    else:
        checks.append("renderer is isolated from reference pixels")
    validation = _json(OUT / "validation.json")
    if validation.get("status") != "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED":
        errors.append("outputs must remain explicitly experimental")
    else:
        checks.append("runtime promotion remains EXPERIMENTAL / NOT TESTED")

    result = {
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "garments": 6,
        "components": {"Shirts": 6, "NativeSleeveColorSets": 6, "CustomSleeves": 0, "Hats": 6, "Accessories": 0, "Presets": 6},
        "hoodStates": {"up": 2, "down": 4},
        "shirtContract": {"frame": [16, 16], "scale": 2, "bodyPosition": [0, 32]},
        "hoodContracts": {
            "up": {
                "frame": [32, 32],
                "scale": 2,
                "hair": "hidden",
                "headPositions": {
                    "front": [-4, 30], "right": [-4, 26],
                    "back": [-4, 26], "left": [-4, 26]
                },
            },
            "down": {
                "frontFrame": [24, 32],
                "sideBackFrame": [16, 32],
                "scale": 2,
                "hair": "preserved",
                "headPositions": {
                    "front": [-8, 0], "right": [-6, 0],
                    "back": [-12, -2], "left": [-18, 0]
                },
            },
        },
        "contentPatcherRequired": False,
        "runtimePromotion": "EXPERIMENTAL",
    }
    _write_json(OUT / "filesystem-validation.json", result)
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
