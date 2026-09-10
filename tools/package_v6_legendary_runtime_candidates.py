#!/usr/bin/env python3
"""Package six approved V6 Legendary candidates with frozen runtime contracts."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import read_rgba_png, write_rgba_png
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames
from generator.renderers.fashionsense.hoodie_layers import render_fs_hoodie_layers
from generator.renderers.fashionsense.legendary_v6 import apply_legendary_construction, apply_legendary_signature
from generator.renderers.fashionsense.upper_v5b import _stack
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v2_recipe_engine import load_v2_data
from generator.v6 import generate_legendary_batch

PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V6-Legendary-Runtime-Candidates"
UNIQUE_ID = "RNGClothing.FashionSense.V6LegendaryRuntimeCandidates"
NAMES = (
    "Graphite Tide Hood",
    "Jade Conservatory Coat",
    "Pearl Nocturne Ceremonial Blazer",
    "Sundown Waymark Tunic",
    "Crimson Arc Relay Jacket",
    "Frostguard Standard Jacket",
)
DIRECTION_MODELS = (("FrontShirt", 0), ("RightShirt", 16), ("LeftShirt", 32), ("BackShirt", 48))


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _folder(value: str) -> str:
    return "".join(part.capitalize() for part in "".join(ch if ch.isalnum() else " " for ch in value).split())


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mask_layer(permanent, name: str) -> dict[str, Any]:
    palette = load_v2_data()["palettes"]["families"][permanent.recipe["paletteFamily"]]
    return {
        "Name": name,
        "DefaultColor": palette["defaultDye"],
        "Values": [[permanent.config["outerMaskRamp"][role]] * 3 for role in permanent.active_main_roles],
    }


def _shirt_model(permanent, sleeve_colors, y: int, layer_name: str) -> dict[str, Any]:
    return {
        "Scale": 2.0,
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [_mask_layer(permanent, layer_name)],
        "SleeveColors": [list(color) for color in sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(name: str, permanent, sleeve_colors, family: str, layer_name: str) -> dict[str, Any]:
    result = {
        "Name": name,
        "Format": "7.5.0",
        "Tags": ["Lifestyle", "RNG Clothing", "V6", "Legendary", family.title(), "Runtime Test"],
    }
    for key, y in DIRECTION_MODELS:
        result[key] = _shirt_model(permanent, sleeve_colors, y, layer_name)
    return result


def _preset(name: str, *, hood: bool) -> dict[str, Any]:
    return {
        "Name": f"Legendary Runtime - {name}",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": f"{UNIQUE_ID}/Hat/{name} Raised Hood" if hood else "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{name}",
        "SleevesId": "None",
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _validate(pack: Path, candidates: list[dict[str, Any]], presets: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("exact candidate count", len(candidates) == 6, [c["name"] for c in candidates])
    check("exact preset count", len(presets) == 6, [p["Name"] for p in presets])
    check("custom Sleeves atlas absent", not (pack / "Sleeves").exists(), "SleevesId must remain None")
    check("single hood component", len(list((pack / "Hats").glob("*/hat.json"))) == 1, "Graphite Tide only")
    all_models = []
    for shirt_path in sorted((pack / "Shirts").glob("*/shirt.json")):
        data = json.loads(shirt_path.read_text(encoding="utf-8"))
        for key, expected_y in DIRECTION_MODELS:
            model = data[key]; all_models.append((shirt_path.parent.name, key, model))
            check(f"{shirt_path.parent.name} {key} frozen anchor", model["Scale"] == 2.0 and model["BodyPosition"] == {"X": 0, "Y": 32} and model["StartingPosition"] == {"X": 0, "Y": expected_y}, model)
            check(f"{shirt_path.parent.name} {key} native sleeves", model["HideSleeves"] is False and len(model["SleeveColors"]) == 3, model["SleeveColors"])
    check("all direction models present", len(all_models) == 24, len(all_models))
    check("all presets reject custom Sleeves", all(p["SleevesId"] == "None" for p in presets), [p["SleevesId"] for p in presets])
    check("only Graphite Tide has Hat", sum(p["HatId"] != "None" for p in presets) == 1 and presets[0]["HatId"].endswith("Graphite Tide Hood Raised Hood"), [p["HatId"] for p in presets])
    pngs = sorted(pack.rglob("*.png"))
    check("expected native textures", len(pngs) == 7, [str(p.relative_to(pack)) for p in pngs])
    dimensions = {}
    binary_alpha = True
    for path in pngs:
        image = read_rgba_png(path)
        relative = str(path.relative_to(pack))
        dimensions[relative] = [image["width"], image["height"]]
        binary_alpha = binary_alpha and {pixel[3] for row in image["pixels"] for pixel in row} <= {0, 255}
    check("shirt atlases are 16x64", all(dimensions[str(p.relative_to(pack))] == [16, 64] for p in pngs if "/Shirts/" in "/" + str(p.relative_to(pack))), dimensions)
    check("hood atlas uses proven 3x 32x32 topology", dimensions.get("Hats/GraphiteTideHoodRaisedHood/hat.png") == [96, 32], dimensions.get("Hats/GraphiteTideHoodRaisedHood/hat.png"))
    check("all textures use binary alpha", binary_alpha, "allowed alpha values: 0,255")
    check("deterministic file hashes recorded", bool(pngs), {str(p.relative_to(pack)): _hash(p) for p in pngs})
    failed = [c["name"] for c in checks if not c["passed"]]
    return {
        "status": "PASS_STATIC_RUNTIME_NOT_TESTED" if not failed else "FAIL_STATIC",
        "checks": checks,
        "failed": failed,
        "runtimeContract": "NATIVE_ANIMATED_SLEEVES_V1",
        "promotion": "EXPERIMENTAL",
        "liveTestRequired": ["front", "right", "back", "left"],
    }


def main() -> None:
    batch = generate_legendary_batch()
    selected = [next(e for e in batch["entries"] if e["name"] == name) for name in NAMES]
    if PACK.exists(): shutil.rmtree(PACK)
    PACK.mkdir(parents=True)
    presets: list[dict[str, Any]] = []
    localization: dict[str, str] = {}
    exported: list[dict[str, Any]] = []

    for entry in selected:
        name = entry["name"]; folder = _folder(name)
        shirt_dir = PACK / "Shirts" / folder; shirt_dir.mkdir(parents=True)
        if entry["runtimeAssembly"] == "coordinated_hoodie":
            render = render_fs_hoodie_layers(entry["recipe"])
            permanent = render.upper.base.base.design.base
            write_rgba_png(shirt_dir / "shirt.png", render.shirt_texture)
            _json(shirt_dir / "shirt.json", _shirt_json(name, permanent, render.upper.sleeve_colors, entry["garmentFamily"], "Primary Hoodie Fabric"))
            hood_dir = PACK / "Hats" / (folder + "RaisedHood"); hood_dir.mkdir(parents=True)
            hood_json = dict(render.hood_json); hood_json["Name"] = name + " Raised Hood"
            write_rgba_png(hood_dir / "hat.png", render.hood_texture)
            _json(hood_dir / "hat.json", hood_json)
            hood = True
        else:
            raw = render_fs_v5d(entry["recipe"])
            polished = polish_upper_frames(raw.base, raw.frames, raw.default_frames, article_family=entry["articleRole"])
            constructed = apply_legendary_construction(polished.frames, polished.default_frames, entry["articleRole"])
            signed = apply_legendary_signature(constructed.frames, constructed.default_frames, entry["articleRole"])
            permanent = raw.base.base.design.base
            write_rgba_png(shirt_dir / "shirt.png", _stack(signed.frames))
            _json(shirt_dir / "shirt.json", _shirt_json(name, permanent, raw.sleeve_colors, entry["garmentFamily"], "Primary Fabric"))
            hood = False
        presets.append(_preset(name, hood=hood))
        key = entry["id"]
        localization[f"legendary.{key}.name"] = name
        localization[f"legendary.{key}.description"] = entry["coreIdentity"]
        exported.append({"id": entry["id"], "name": name, "preset": f"Legendary Runtime - {name}", "shirt": f"Shirts/{folder}", "hood": f"Hats/{folder}RaisedHood" if hood else None, "nativeSleeves": True, "customSleeves": False})

    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing V6 Legendary Runtime Candidates",
        "Author": "RNG Clothing Experiment",
        "Version": "2.0.0",
        "Description": "Six test-only Legendary candidates using proven native sleeve and coordinated hoodie contracts.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "i18n" / "default.json", localization)
    validation = _validate(PACK, exported, presets)
    _json(PACK / "runtime-contract-validation.json", validation)
    _json(PACK / "candidate-index.json", exported)
    (PACK / "README.md").write_text(
        "# V6 Legendary Runtime Candidates\n\n"
        "Copy this entire folder into `Stardew Valley/Mods`, fully restart SMAPI, then use the Fashion Sense Hand Mirror and open **Outfits > Presets**.\n\n"
        "Presets:\n" + "".join(f"- **Legendary Runtime - {name}**\n" for name in NAMES) +
        "\nAll six Shirts use the live-proven native Farmer arm path: `HideSleeves: false`, three `SleeveColors`, Scale 2, and BodyPosition `(0,32)`. `SleevesId` is deliberately `None`; this pack contains no custom Sleeves atlas. Graphite Tide additionally uses its proven coordinated Hat/Hood. No files are installed automatically. Status: **EXPERIMENTAL / STATIC PASS / LIVE TEST REQUIRED**.\n",
        encoding="utf-8",
    )
    (ROOT / "reports" / "V6_LEGENDARY_RUNTIME_TEST_PACK.md").write_text(
        "# V6 Legendary Runtime Test Pack\n\n"
        f"Install source: `{PACK}`\n\n"
        "Copy the entire `RNG-Clothing-V6-Legendary-Runtime-Candidates` folder into the Stardew Valley `Mods` directory, fully restart SMAPI, then open the Fashion Sense Hand Mirror and choose **Outfits > Presets**.\n\n"
        "## Presets\n\n" + "".join(f"- `Legendary Runtime - {name}`\n" for name in NAMES) +
        "\n## Focused live check\n\n"
        "For each preset check standing **front, right, back, and left**. Confirm the torso remains anchored, native arms remain attached, sleeve colors follow Farmer animation, and no component appears near the feet. For Graphite Tide additionally confirm the hood stays at the head in every direction.\n\n"
        "Static status: **PASS**. Runtime status: **NOT TESTED**. All appearances remain **EXPERIMENTAL**.\n",
        encoding="utf-8",
    )
    if validation["failed"]: raise SystemExit("static validation failed: " + ", ".join(validation["failed"]))
    print(f"Packaged {len(exported)} Legendary runtime candidates")
    print(PACK)
    print(validation["status"])


if __name__ == "__main__": main()
