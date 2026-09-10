#!/usr/bin/env python3
"""Generate the deterministic V5D masculine art-grammar batch and test pack."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, nearest_scale, text_width, write_rgba_png
from generator.renderers.fashionsense.upper_v5b import render_fs_v5b
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v2_recipe_engine import load_v2_data
from generator.v5b import generate_v5b_benchmark
from generator.v5d import diagnose_v5d_article, diagnose_v5d_collection, generate_v5d_batch


OUT = ROOT / "output" / "fashionsense" / "v5d-masculine"
COMPARE = ROOT / "output" / "comparisons"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V5D-Masculine"
UNIQUE_ID = "RNGClothing.FashionSense.V5DMasculine"
PREVIEW_ORDER = ("front", "right", "back", "left")
BG: RGBA = (235, 227, 216, 255)
TILE: RGBA = (213, 205, 193, 255)
INK: RGBA = (44, 42, 40, 255)
BORDER: RGBA = (75, 69, 64, 255)
LIGHT_PANEL: RGBA = (205, 218, 212, 255)
DARK_PANEL: RGBA = (197, 190, 188, 255)


# Filled after human inspection of the generated sheets. Static metrics never
# award these scores; they record the art review and keep it auditable.
QUALITY_REVIEW: dict[str, dict[str, int | str]] = {
    "v5d-01": {"articleReadability": 4, "silhouetteQuality": 4, "constructionQuality": 4, "surfaceDesign": 4, "sideBackQuality": 4, "extraResolutionValue": 4, "collectibilityAppeal": 4, "note": "Weakest included piece, but the revised short placket now reads as a henley instead of an open jacket."},
    "v5d-02": {"articleReadability": 5, "silhouetteQuality": 4, "constructionQuality": 5, "surfaceDesign": 4, "sideBackQuality": 4, "extraResolutionValue": 4, "collectibilityAppeal": 4, "note": "Work collar, full placket, pockets, and back yoke establish practical farmwear without decorative excess."},
    "v5d-03": {"articleReadability": 5, "silhouetteQuality": 4, "constructionQuality": 4, "surfaceDesign": 5, "sideBackQuality": 5, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "One connected stepped knit band carries through every view and the ribbed termination stays clear."},
    "v5d-04": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 4, "sideBackQuality": 5, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Large hood mass and pouch pocket survive gameplay scale; sleeve stripe remains subordinate."},
    "v5d-05": {"articleReadability": 5, "silhouetteQuality": 4, "constructionQuality": 5, "surfaceDesign": 4, "sideBackQuality": 5, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Open knit edges, visible inner shirt, pockets, and quiet back-neck treatment distinguish the cardigan."},
    "v5d-06": {"articleReadability": 5, "silhouetteQuality": 4, "constructionQuality": 5, "surfaceDesign": 4, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Deep V, shirt contrast, narrow button rhythm, and tailored points make the waistcoat immediately formal."},
    "v5d-07": {"articleReadability": 5, "silhouetteQuality": 4, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 4, "note": "Utility blocks and shoulder tabs read well; the back is intentionally quieter and is the limiting view."},
    "v5d-08": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 4, "sideBackQuality": 5, "extraResolutionValue": 5, "collectibilityAppeal": 4, "note": "Cropped outer shell, lapel opening, pocket flaps, and back yoke are clear; its restrained field palette is less showy than other Rares."},
    "v5d-09": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Lapel-shirt-tie hierarchy and pocket square sell formalwear; the broad profile opening remains a runtime-review concern."},
    "v5d-10": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Cravat, offset closure, restrained diagonal brocade, and back coat seam create a distinct period identity."},
    "v5d-11": {"articleReadability": 5, "silhouetteQuality": 4, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "High service collar, ordered chest tabs, belt line, and yoke read as military tailoring rather than generic olive outerwear."},
    "v5d-12": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Layered V, diagonal sash, belt, and waymark strongly separate the tunic; the back deliberately reduces to belt and shoulder cues."},
    "v5d-13": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 5, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Plate caps, segmented chest, center tabard, crest, and strong back treatment make this the clearest full-article translation."},
    "v5d-14": {"articleReadability": 5, "silhouetteQuality": 5, "constructionQuality": 5, "surfaceDesign": 5, "sideBackQuality": 4, "extraResolutionValue": 5, "collectibilityAppeal": 5, "note": "Asymmetric cross-zip and one-shoulder panel remain distinct in profile without simply mirroring the front."},
}


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return "_".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def _folder(value: str) -> str:
    return "".join(piece.title() for piece in _slug(value).split("_"))


def _design(recipe):
    return recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]


def _old_design(recipe):
    return recipe["baseArticleRecipe"]["designRecipe"]


def _bordered(canvas, sprite, x: int, y: int, tile: RGBA = TILE) -> None:
    draw_rect(canvas, x - 2, y - 2, len(sprite[0]) + 4, len(sprite) + 4, BORDER)
    draw_rect(canvas, x - 1, y - 1, len(sprite[0]) + 2, len(sprite) + 2, tile)
    blit(canvas, sprite, x, y)


def _direction_sheet(title: str, frames, scale: int):
    size = 16 * scale
    gap = max(18, scale * 3)
    margin = 16
    top = 43
    canvas = blank_image(margin * 2 + size * 4 + gap * 3, top + size + 16, BG)
    draw_text(canvas, title, max(4, (len(canvas[0]) - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        x = margin + index * (size + gap)
        label = direction.upper()
        draw_text(canvas, label, x + (size - text_width(label)) // 2, 25, color=INK)
        _bordered(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _collection_sheet(title: str, rendered, *, scale: int):
    sprite = 16 * scale
    label_w = 245
    gap = max(14, scale * 2)
    top = 58
    row_h = sprite + 28
    canvas = blank_image(label_w + sprite * 4 + gap * 3 + 20, top + row_h * len(rendered) + 12, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    draw_text(canvas, "VERIFIED FS ORDER - FRONT | RIGHT | BACK | LEFT", 8, 21, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (sprite + gap), 43, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h
        design = _design(recipe)
        draw_text(canvas, f"{row + 1:02d} {design['rarity'].upper()}  {recipe['articleRole'].replace('_', ' ')}", 6, y + 1, color=INK)
        draw_text(canvas, design["itemName"][:38], 6, y + 14, color=INK)
        draw_text(canvas, recipe["sleeveIntent"].replace("_", " ")[:38], 6, y + 27, color=INK)
        for index, direction in enumerate(PREVIEW_ORDER):
            _bordered(canvas, nearest_scale(render.default_frames[direction], scale), label_w + index * (sprite + gap), y)
    return canvas


def _front_grid(title: str, rendered, *, scale: int = 7, columns: int = 4):
    sprite = 16 * scale
    cell_w = sprite + 102
    cell_h = sprite + 72
    rows = (len(rendered) + columns - 1) // columns
    canvas = blank_image(columns * cell_w, 35 + rows * cell_h, BG)
    draw_text(canvas, title, 8, 8, color=INK)
    for index, (recipe, render, _) in enumerate(rendered):
        column, row = index % columns, index // columns
        x = column * cell_w + 48
        y = 35 + row * cell_h + 48
        design = _design(recipe)
        draw_text(canvas, f"{index + 1:02d} {design['rarity'].upper()}", x - 37, y - 38, color=INK)
        draw_text(canvas, recipe["articleRole"].replace("_", " ")[:28], x - 37, y - 25, color=INK)
        draw_text(canvas, design["itemName"][:28], x - 37, y - 12, color=INK)
        _bordered(canvas, nearest_scale(render.default_frames["front"], scale), x, y)
    return canvas


def _rarity_sheet(rendered):
    ordered = []
    for rarity in ("Common", "Uncommon", "Rare"):
        ordered.extend(entry for entry in rendered if _design(entry[0])["rarity"] == rarity)
    return _front_grid("V5D RARITY: COMMON 3 | UNCOMMON 4 | RARE 7", ordered, scale=7, columns=4)


def _light_dark_sheet(rendered):
    groups = [
        ("LIGHT / COLORFUL CONSTRUCTION", [entry for entry in rendered if entry[0]["lightPalette"]], LIGHT_PANEL),
        ("DARK / GROUNDED CONSTRUCTION", [entry for entry in rendered if not entry[0]["lightPalette"]], DARK_PANEL),
    ]
    scale = 6
    sprite = 16 * scale
    columns = 7
    cell_w = 152
    cell_h = sprite + 50
    canvas = blank_image(columns * cell_w, 52 + cell_h * 2, BG)
    for row, (title, entries, tile) in enumerate(groups):
        y0 = 6 + row * cell_h
        draw_text(canvas, title, 8, y0, color=INK)
        for index, (recipe, render, _) in enumerate(entries):
            x = index * cell_w + 27
            y = y0 + 34
            draw_text(canvas, _design(recipe)["itemName"][:20], x - 17, y - 13, color=INK)
            _bordered(canvas, nearest_scale(render.default_frames["front"], scale), x, y, tile)
    return canvas


def _sleeve_sheet(rendered):
    frame_w, frame_h = 32, 64
    label_w = 245
    gap = 10
    top = 58
    row_h = frame_h + 21
    canvas = blank_image(label_w + frame_w * 4 + gap * 3 + 20, top + row_h * len(rendered) + 10, BG)
    draw_text(canvas, "V5D SLEEVE RUNTIME CONTRACT DIAGNOSTIC", 8, 7, color=INK)
    draw_text(canvas, "CUSTOM 384X1344 ATLASES; SHORT SLEEVE USES FS DEFAULT", 8, 21, color=INK)
    for index, direction in enumerate(PREVIEW_ORDER):
        draw_text(canvas, direction.upper(), label_w + index * (frame_w + gap), 43, color=INK)
    for row, (recipe, render, _) in enumerate(rendered):
        y = top + row * row_h
        draw_text(canvas, _design(recipe)["itemName"][:36], 6, y + 3, color=INK)
        draw_text(canvas, recipe["sleeveIntent"].replace("_", " ")[:36], 6, y + 17, color=INK)
        if render.sleeve_idle_frames:
            for index, direction in enumerate(PREVIEW_ORDER):
                _bordered(canvas, render.sleeve_idle_frames[direction], label_w + index * (frame_w + gap), y)
        else:
            for index in range(4):
                draw_text(canvas, "FS SHORT", label_w + index * (frame_w + gap) - 6, y + 28, color=INK)
    return canvas


def _old_vs_new_sheet(rendered):
    old_recipes = generate_v5b_benchmark()["recipes"]
    old = {_old_design(recipe)["itemName"]: render_fs_v5b(recipe) for recipe in old_recipes}
    new = {_design(recipe)["itemName"]: render for recipe, render, _ in rendered}
    pairs = [
        ("Saltair Fitted Tee", "Tideglass Henley", "TEE -> HENLEY + WRAP BAND"),
        ("Signalwork Rolled Shirt", "Orchard Hand Workshirt", "PLACKET + POCKETS + YOKE"),
        ("Maple Loom Knit", "Skylark Cable Knit", "KNIT BAND + RIBBING"),
        ("Juniper Rain Cardigan", "Rowan Morning Cardigan", "OPEN KNIT + INNER LAYER"),
        ("Duskline Waistcoat", "Silverline Evening Waistcoat", "V FRAME + FORMAL POINTS"),
        ("Relay Utility Vest", "Brasshook Utility Vest", "UTILITY BLOCKS + TABS"),
        ("Rookwing Cropped Field Jacket", "Sunfield Scout Jacket", "CROP + LAPEL + POCKETS"),
        ("Gilded Evening Blazer", "Midnight Laurel Blazer", "FORMAL VALUE HIERARCHY"),
    ]
    scale = 6
    sprite = 16 * scale
    label_w = 248
    gap = 30
    top = 58
    row_h = sprite + 22
    canvas = blank_image(label_w + sprite * 2 + gap + 20, top + row_h * len(pairs) + 10, BG)
    draw_text(canvas, "OLDER V5B FRONT -> V5D BENCHMARK-INFORMED FRONT", 8, 7, color=INK)
    draw_text(canvas, "OLD", label_w, 39, color=INK)
    draw_text(canvas, "V5D", label_w + sprite + gap, 39, color=INK)
    for row, (old_name, new_name, note) in enumerate(pairs):
        y = top + row * row_h
        draw_text(canvas, new_name[:37], 6, y + 3, color=INK)
        draw_text(canvas, note[:37], 6, y + 17, color=INK)
        _bordered(canvas, nearest_scale(old[old_name].default_frames["front"], scale), label_w, y)
        _bordered(canvas, nearest_scale(new[new_name].default_frames["front"], scale), label_w + sprite + gap, y)
    return canvas


def _shirt_model(render, y: int) -> dict[str, Any]:
    base = render.base.base.design.base
    palette = load_v2_data()["palettes"]["families"][base.recipe["paletteFamily"]]
    return {
        "Scale": 2.0,
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Primary Fabric",
            "DefaultColor": palette["defaultDye"],
            "Values": [[base.config["outerMaskRamp"][role]] * 3 for role in base.active_main_roles],
        }],
        "SleeveColors": [list(value) for value in render.sleeve_colors],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(recipe, render) -> dict[str, Any]:
    design = _design(recipe)
    return {
        "Name": design["itemName"],
        "Format": "7.5.0",
        "Tags": ["Lifestyle", "RNG Clothing", "Generator V5D", recipe["fashionFamily"].replace("_", " ").title(), design["rarity"], "Test"],
        "FrontShirt": _shirt_model(render, 0),
        "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32),
        "BackShirt": _shirt_model(render, 48),
    }


def _preset(recipe, render) -> dict[str, Any]:
    name = _design(recipe)["itemName"]
    if render.companion_required:
        sleeves_id = f"{UNIQUE_ID}/Sleeves/{name} Sleeves"
    elif recipe["sleeveIntent"] == "SHORT_SLEEVE":
        sleeves_id = "PeacefulEnd.FashionSense.LocalPack/Sleeves/Default (Short)"
    else:
        sleeves_id = "None"
    return {
        "Name": f"V5D - {name}",
        "Author": "RNG Clothing Experiment",
        "Version": 3,
        "AccessoryIds": ["None", "None", "None"],
        "HairId": "None",
        "HatId": "None",
        "ShirtId": f"{UNIQUE_ID}/Shirt/{name}",
        "SleevesId": sleeves_id,
        "PantsId": "None",
        "ShoesId": "None",
        "BodyId": "None",
        "AppearanceToMaskColors": {},
    }


def _readme(rendered) -> str:
    rows = []
    for index, (recipe, render, _) in enumerate(rendered, 1):
        design = _design(recipe)
        sleeve = "paired generated Sleeves" if render.companion_required else "Fashion Sense Default (Short)"
        rows.append(f"{index}. **{design['itemName']}** — {design['rarity']}; {recipe['articleRole'].replace('_', ' ').title()}; {sleeve}")
    return """# RNG Clothing V5D Masculine Art Grammar

Test-only Fashion Sense pack. It is not installed automatically and none of these appearances is production-ready.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the entire `RNG-Clothing-V5D-Masculine` folder into Stardew Valley's `Mods` folder, then fully restart SMAPI.

## Equip the coordinated garments

Open the Fashion Sense Hand Mirror, choose **Outfits**, switch to **Presets**, and select a preset beginning with `V5D -`. Thirteen presets equip a generated Shirt and matching animated Sleeves appearance. Tideglass Henley uses Fashion Sense's built-in `Default (Short)` sleeve. You may equip components manually under **Shirts** and **Sleeves**, but the names must match.

## Garments

""" + "\n".join(rows) + """

## Runtime status

All fourteen are `EXPERIMENTAL / NOT TESTED`. Static validation proves file, anchor, frame, coverage, alpha, and deterministic contracts only. Test idle/walk/run/tools/sitting/horse/equip/recolor in all directions before promotion.
"""


def main() -> None:
    batch = generate_v5d_batch()
    required_review_axes = {"articleReadability", "silhouetteQuality", "constructionQuality", "surfaceDesign", "sideBackQuality", "extraResolutionValue", "collectibilityAppeal"}
    for recipe in batch["recipes"]:
        review = QUALITY_REVIEW.get(recipe["id"], {})
        missing = required_review_axes - set(review)
        if missing:
            raise ValueError(f"{recipe['id']} lacks human art-review axes: {sorted(missing)}")
        if min(int(review[axis]) for axis in required_review_axes) < 4:
            raise ValueError(f"{recipe['id']} failed the required V5D human quality floor and must be revised")
    renders = [render_fs_v5d(recipe) for recipe in batch["recipes"]]
    diagnostics = [diagnose_v5d_article(render) for render in renders]
    collection = diagnose_v5d_collection(batch["recipes"], renders, diagnostics)
    if not collection.passes:
        raise ValueError("V5D collection failed: " + "; ".join(collection.errors))
    rendered = list(zip(batch["recipes"], renders, diagnostics))
    OUT.mkdir(parents=True, exist_ok=True)
    COMPARE.mkdir(parents=True, exist_ok=True)
    PACK.mkdir(parents=True, exist_ok=True)
    presets: list[dict[str, Any]] = []
    localization: dict[str, str] = {}
    for recipe, render, diagnostic in rendered:
        design = _design(recipe)
        name = design["itemName"]
        target = OUT / _slug(name)
        target.mkdir(parents=True, exist_ok=True)
        write_rgba_png(target / "shirt.png", render.texture)
        write_rgba_png(target / "shirt-8x.png", nearest_scale(render.texture, 8))
        write_rgba_png(target / "directions-8x.png", _direction_sheet(name, render.default_frames, 8))
        write_rgba_png(target / "gameplay-footprint.png", _direction_sheet(name + " - SCALE 2", render.default_frames, 2))
        if render.sleeves_texture is not None:
            write_rgba_png(target / "sleeves.png", render.sleeves_texture)
            _json(target / "sleeves.json", render.sleeves_json)
            write_rgba_png(target / "sleeves-idle-directions.png", _sleeve_sheet([(recipe, render, diagnostic)]))
        _json(target / "summary.json", {
            "name": name,
            "description": design["itemDescription"],
            "rarity": design["rarity"],
            "fashionFamily": recipe["fashionFamily"],
            "articleRole": recipe["articleRole"],
            "articleSubtype": recipe["articleSubtype"],
            "sleeveIntent": recipe["sleeveIntent"],
            "constructionFeatures": recipe["constructionFeatures"],
            "surfacePlan": recipe["surfacePlan"],
            "paletteStory": recipe["paletteStory"],
            "benchmarkBasis": recipe["benchmarkBasis"],
            "qualityReview": QUALITY_REVIEW.get(recipe["id"], "PENDING_HUMAN_ART_REVIEW"),
            "promotion": "EXPERIMENTAL",
            "runtime": "NOT_TESTED",
            "recipe": recipe,
            "diagnostics": {"passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics},
        })
        shirt_dir = PACK / "Shirts" / _folder(name)
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(recipe, render))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)
        if render.companion_required:
            sleeves_dir = PACK / "Sleeves" / (_folder(name) + "Sleeves")
            sleeves_dir.mkdir(parents=True, exist_ok=True)
            _json(sleeves_dir / "sleeves.json", render.sleeves_json)
            write_rgba_png(sleeves_dir / "sleeves.png", render.sleeves_texture)
        presets.append(_preset(recipe, render))
        localization[f"garment.{recipe['id']}.name"] = name
        localization[f"garment.{recipe['id']}.description"] = design["itemDescription"]

    _json(ROOT / "output" / "recipes" / "v5d_masculine_diagnostics.json", batch)
    _json(OUT / "validation.json", {
        "status": "PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED",
        "runtimePromotion": "EXPERIMENTAL",
        "beautyClaim": "HUMAN_REVIEW_REQUIRED",
        "collection": {"passes": collection.passes, "errors": list(collection.errors), "warnings": list(collection.warnings), "metrics": collection.metrics},
        "garments": [{"id": recipe["id"], "name": _design(recipe)["itemName"], "passes": diagnostic.passes, "errors": list(diagnostic.errors), "warnings": list(diagnostic.warnings), "metrics": diagnostic.metrics, "qualityReview": QUALITY_REVIEW.get(recipe["id"], "PENDING_HUMAN_ART_REVIEW")} for recipe, diagnostic in zip(batch["recipes"], diagnostics)],
    })
    write_rgba_png(OUT / "V5D_GAMEPLAY_FOOTPRINT.png", _collection_sheet("V5D MASCULINE - GAMEPLAY FOOTPRINT", rendered, scale=2))
    write_rgba_png(OUT / "V5D_ENLARGED_NEAREST.png", _collection_sheet("V5D MASCULINE - ENLARGED DIRECT PIXELS", rendered, scale=6))
    write_rgba_png(COMPARE / "V5D_FRONT_RIGHT_BACK_LEFT.png", _collection_sheet("V5D ORIENTATION AND DIRECTIONAL RECONSTRUCTION", rendered, scale=4))
    write_rgba_png(OUT / "V5D_FASHION_FAMILY_COMPARISON.png", _front_grid("V5D FOURTEEN MASCULINE FASHION IDENTITIES", rendered))
    write_rgba_png(OUT / "V5D_RARITY_COMPARISON.png", _rarity_sheet(rendered))
    write_rgba_png(OUT / "V5D_LIGHT_VS_DARK.png", _light_dark_sheet(rendered))
    write_rgba_png(COMPARE / "V5D_OLD_VS_NEW.png", _old_vs_new_sheet(rendered))
    write_rgba_png(OUT / "V5D_SLEEVE_RUNTIME_DIAGNOSTIC.png", _sleeve_sheet(rendered))
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing V5D Masculine Art Grammar",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Test-only V5D masculine fashion-family and art-grammar diagnostics.",
        "UniqueID": UNIQUE_ID,
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "preset_outfits.json", presets)
    _json(PACK / "i18n" / "default.json", localization)
    (PACK / "README.md").write_text(_readme(rendered), encoding="utf-8")
    print(f"Generated {len(rendered)} V5D garments with {sum(render.companion_required for render in renders)} coordinated sleeve companions")
    print(OUT)
    print(PACK)


if __name__ == "__main__":
    main()
