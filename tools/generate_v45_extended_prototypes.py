#!/usr/bin/env python3
"""Generate bounded Fashion Sense V4.5 extended-garment prototypes."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, text_width, write_rgba_png
from generator.renderers.fashionsense import load_v45_fs_grammar, render_v45_prototype
from generator.v45 import generate_v45_prototypes


OUT = ROOT / "output" / "fashionsense" / "v45-extended-garments"
COMPARE = ROOT / "output" / "comparisons" / "V45_EXTENDED_ARTICLES.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V45-Extended-Prototypes"
DIRECTIONS = ("front", "back", "right", "left")
BG: RGBA = (236, 226, 211, 255); INK: RGBA = (54, 49, 45, 255); BORDER: RGBA = (81, 73, 66, 255); TILE: RGBA = (214, 205, 192, 255)


def _json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str): return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
def _folder(value: str): return "".join(word.title() for word in _slug(value).split("_"))


def _bordered(canvas, image, x, y):
    draw_rect(canvas, x - 2, y - 2, len(image[0]) + 4, len(image) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(image[0]) + 2, len(image) + 2, TILE); blit(canvas, image, x, y)


def _direction_sheet(recipe, render, scale):
    width, height = render.contract["frameSize"]; sprite_w = width * scale; sprite_h = height * scale
    gap = 18; label = 130; top = 42
    canvas = blank_image(label + 4 * (sprite_w + gap) + 10, top + sprite_h + 18, BG)
    draw_text(canvas, f"{recipe['name']} - {recipe['rarity'].upper()} - {recipe['runtimeStatus']}", 7, 7, color=INK)
    draw_text(canvas, recipe["articleType"].replace("_", " "), 7, 22, color=INK)
    for i, direction in enumerate(DIRECTIONS):
        x = label + i * (sprite_w + gap); draw_text(canvas, direction, x, 27, color=INK)
        _bordered(canvas, nearest_scale(render.frames[direction][0], scale), x, top)
    return canvas


def _motion_sheet(recipe, render):
    scale = 4; width, height = render.contract["frameSize"]; sw, sh = width * scale, height * scale
    gap = 12; top = 44; row_h = sh + 18; cols = render.contract["frameCount"]
    canvas = blank_image(138 + cols * (sw + gap), top + 4 * row_h + 10, BG)
    draw_text(canvas, f"{recipe['name']} - AUTHORED LOGICAL MOTION PHASES", 8, 7, color=INK)
    draw_text(canvas, "STATIC ASSET CHECK; RUNTIME POSES REMAIN MANUAL", 8, 21, color=INK)
    for row, direction in enumerate(DIRECTIONS):
        y = top + row * row_h; draw_text(canvas, direction, 8, y + 8, color=INK)
        for i, frame in enumerate(render.frames[direction]): _bordered(canvas, nearest_scale(frame, scale), 138 + i * (sw + gap), y)
    return canvas


def _movement(frame_count=4):
    grammar = load_v45_fs_grammar(); records = []
    for frame in grammar["movementSequence"]:
        records.append({"Frame": frame, "EndWhenFarmerFrameUpdates": True, "Conditions": [{"Name": "IsWalking", "Value": True}]})
    for frame in grammar["runningSequence"]:
        if frame >= frame_count: frame = 2
        records.append({"Frame": frame, "EndWhenFarmerFrameUpdates": True, "Conditions": [{"Name": "IsRunning", "Value": True}]})
    return records


def _model(recipe, render, direction, y):
    width, height = render.contract["frameSize"]; article = recipe["articleType"]
    model = {"Scale": 4.0, "DisableGrayscale": True, "StartingPosition": {"X": 0, "Y": y},
             "HideWhileSwimming": True, "HideWhileWearingBathingSuit": True,
             "IdleAnimation": [{"Frame": 0, "Duration": 100}], "MovementAnimation": _movement(render.contract["frameCount"])}
    if article in {"PANTS", "SKIRT"}:
        model["BodyPosition"] = {"X": 0, "Y": render.contract["bodyPosition"][1]}; model["PantsSize"] = {"Width": width, "Length": height}
        model["HideLegs"] = False; model["HideShadow"] = False
    elif article == "FOOTWEAR":
        model["BodyPosition"] = {"X": 0, "Y": render.contract["bodyPosition"][1]}; model["ShoesSize"] = {"Width": width, "Length": height}
        model["DrawBeforePants"] = True
    else:
        model["HeadPosition"] = {"X": render.contract["headPosition"][0], "Y": render.contract["headPosition"][1]}
        model["AccessorySize"] = {"Width": width, "Length": height}
        model["DrawOrderOverride"] = ({"Preposition": "After", "AppearanceType": "Shirt"} if direction == "front" and article == "MANTLE" else {"Preposition": "Before", "AppearanceType": "Player"})
    if direction == "left": model["Flipped"] = False
    return model


def _appearance_json(recipe, render):
    article = recipe["articleType"]; width, height = render.contract["frameSize"]
    root = {"Name": recipe["name"], "Format": "7.5.0", "Tags": ["AoT Inspired", article.replace("_", " ").title(), recipe["rarity"], "RNG Clothing", "V4.5", "Test"]}
    stem = "Pants" if article in {"PANTS", "SKIRT"} else "Shoes" if article == "FOOTWEAR" else "Accessory"
    for index, direction in enumerate(DIRECTIONS):
        field = direction.title() + stem; root[field] = _model(recipe, render, direction, index * height)
    return root


def _comparison(rendered):
    scale = 4; cell_w = 196; cell_h = 178; cols = 4; rows = 2
    canvas = blank_image(cols * cell_w, 34 + rows * cell_h, BG); draw_text(canvas, "V4.5 EXTENDED ARTICLE STATIC CAPABILITY PROTOTYPES", 8, 8, color=INK)
    for i, (recipe, render) in enumerate(rendered):
        x = (i % cols) * cell_w + 22; y = 34 + (i // cols) * cell_h + 45
        draw_text(canvas, f"{recipe['articleType'].replace('_', ' ')} - {recipe['rarity'].upper()}", x, y - 31, color=INK)
        draw_text(canvas, recipe["name"][:24], x, y - 18, color=INK)
        preview_direction = "back" if recipe["articleType"] in {"MANTLE", "COAT_TAIL_COMPANION"} else "front"
        image = nearest_scale(render.frames[preview_direction][0], scale); _bordered(canvas, image, x, y)
        draw_text(canvas, "NOT READY" if recipe["runtimeStatus"] == "NOT_READY" else "RUNTIME TEST PENDING", x, y + len(image) + 7, color=INK)
    return canvas


def main():
    recipes = generate_v45_prototypes(); rendered = []; installable = []
    _json(ROOT / "output" / "recipes" / "v45_extended_prototypes.json", {"generatorVersion": "4.5-audit", "count": len(recipes), "recipes": recipes})
    for recipe in recipes:
        render = render_v45_prototype(recipe); rendered.append((recipe, render)); slug = _slug(recipe["name"]); target = OUT / slug
        write_rgba_png(target / f"{slug}.png", render.texture)
        write_rgba_png(target / f"{slug}-directions-8x.png", _direction_sheet(recipe, render, 8))
        write_rgba_png(target / f"{slug}-gameplay-size.png", _direction_sheet(recipe, render, 4))
        write_rgba_png(target / f"{slug}-motion-phases.png", _motion_sheet(recipe, render))
        _json(target / f"{slug}-summary.json", {"recipe": recipe, "fashionSenseContract": render.contract,
            "staticValidation": {"passes": render.static_contract_passes, "errors": list(render.static_errors), "occupiedCellsByDirectionAndPhase": render.occupied_cells},
            "runtimeVerdict": recipe["runtimeStatus"], "runtimeEvidence": "NOT_TESTED_IN_GAME",
            "limitations": load_v45_fs_grammar()["limitations"]})
        if recipe["runtimeStatus"] != "NOT_READY":
            installable.append((recipe, render)); folder = render.contract["folder"]
            appearance_dir = PACK / folder / _folder(recipe["name"]); appearance_dir.mkdir(parents=True, exist_ok=True)
            stem = "pants" if recipe["articleType"] in {"PANTS", "SKIRT"} else "shoes" if recipe["articleType"] == "FOOTWEAR" else "accessory"
            _json(appearance_dir / f"{stem}.json", _appearance_json(recipe, render)); write_rgba_png(appearance_dir / f"{stem}.png", render.texture)
        else:
            _json(target / "DIAGNOSTIC_ONLY_NOT_FOR_INSTALL.json", _appearance_json(recipe, render))
    write_rgba_png(COMPARE, _comparison(rendered)); write_rgba_png(OUT / "V45_EXTENDED_ARTICLES.png", _comparison(rendered))
    _json(PACK / "manifest.json", {"Name": "RNG Clothing V4.5 Extended Garment Prototypes", "Author": "RNG Clothing Experiment", "Version": "0.1.0", "Description": "Manual runtime test pack for bounded pants, skirt, footwear, and mantle prototypes. No coat tail is included.", "UniqueID": "RNGClothing.FashionSense.V45ExtendedPrototypes", "UpdateKeys": [], "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"}})
    _json(PACK / "i18n" / "default.json", {key: value for recipe, _ in installable for key, value in ((f"appearance.{recipe['id']}.name", recipe["name"]), (f"appearance.{recipe['id']}.description", recipe["description"]))})
    (PACK / "README.md").write_text("""# RNG Clothing V4.5 Extended Garment Prototypes\n\nThis is a manual runtime capability pack, not production clothing. Copy this entire folder into `Stardew Valley/Mods`, with Fashion Sense 7.5.0 installed separately, then restart SMAPI. Use the Hand Mirror Pants, Shoes, and Accessories categories.\n\nThe pack contains two trousers, one short skirt, two footwear prototypes, and one mantle. The diagnostic coat-tail asset is deliberately excluded. Every included appearance has static-valid authored walk/run phases, but tools, fishing, horse, sitting, bed, swimming transitions, and multiplayer remain unverified. Record results against `reports/V45_RUNTIME_TEST_CHECKLIST.md`. Do not treat pack loading as runtime success.\n""", encoding="utf-8")
    _json(OUT / "validation.json", {"status": "PASS_STATIC_PROTOTYPE_CONTRACTS_RUNTIME_UNTESTED", "installedAutomatically": False,
        "installablePrototypeCount": len(installable), "diagnosticOnlyCount": len(rendered) - len(installable),
        "prototypes": [{"id": r["id"], "article": r["articleType"], "rarity": r["rarity"], "staticPass": x.static_contract_passes, "runtimeStatus": r["runtimeStatus"], "runtimeEvidence": "NOT_TESTED_IN_GAME"} for r, x in rendered]})
    print(f"Generated {len(rendered)} V4.5 prototypes; {len(installable)} in manual test pack; coat tail excluded")


if __name__ == "__main__": main()
