#!/usr/bin/env python3
"""Verify FS V4.6B direction models and make a marked preview-only audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import RGBA, blank_image, blit, draw_rect, draw_text, read_rgba_png, write_rgba_png
from generator.renderers.fashionsense import appearance_json_v46b, render_v46b
from generator.v46b import generate_v46b_prototypes
from tools.generate_v46b_lower_body import _composite


OUT = ROOT / "output" / "comparisons" / "V46B_DIRECTION_ORIENTATION_AUDIT.png"
AUDIT_JSON = ROOT / "output" / "fashionsense" / "v46b-lower-body-readability" / "orientation_audit.json"
FARMER = Path("/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Characters/Farmer/farmer_base.png")
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-V46B-LowerBody-Readability"
BG: RGBA = (229, 221, 208, 255)
TILE: RGBA = (201, 193, 181, 255)
INK: RGBA = (42, 38, 37, 255)
BORDER: RGBA = (66, 57, 54, 255)
MARKERS: tuple[RGBA, ...] = ((38, 111, 160, 255), (187, 91, 43, 255), (95, 65, 137, 255), (52, 130, 92, 255))

# Label, renderer direction, Farmer FacingDirection, current Farmer frame,
# expected FS model field, direction-block start Y, and runtime flip.
ORIENTATION = (
    ("FRONT / DOWN", "front", 2, 0, "FrontPants", 0, False),
    ("RIGHT", "right", 1, 6, "RightPants", 2752, False),
    ("BACK / UP", "back", 0, 12, "BackPants", 1376, False),
    ("LEFT", "left", 3, 6, "LeftPants", 4128, True),
)


def animation_source(model: dict, current_frame: int) -> int | None:
    for animation in model["UniformAnimation"]:
        for condition in animation.get("Conditions", []):
            if condition.get("Name") == "CurrentFarmerFrame" and int(condition.get("Value")) == current_frame:
                return int(animation["Frame"])
    return None


def make_sheet(recipe: dict, rendered, farmer_pixels) -> list[list[RGBA]]:
    tile_w, tile_h = 132, 203
    canvas = blank_image(4 * tile_w + 16, tile_h + 48, BG)
    draw_text(canvas, "V4.6B FASHION SENSE DIRECTION ORIENTATION AUDIT", 8, 7, color=INK)
    draw_text(canvas, "TEMPORARY MARKERS EXIST ONLY ON THIS SHEET", 8, 21, color=INK)
    model = appearance_json_v46b(recipe, rendered)
    for index, (label, direction, facing, current, field, start_y, flipped) in enumerate(ORIENTATION):
        x = 8 + index * tile_w
        marker = MARKERS[index]
        draw_rect(canvas, x, 38, tile_w - 8, 12, marker)
        draw_text(canvas, label, x + 4, 40, color=(255, 255, 255, 255))
        draw_text(canvas, f"FS {field}", x + 2, 55, color=INK)
        draw_text(canvas, f"FACING {facing} FRAME {current}", x + 2, 68, color=INK)
        draw_text(canvas, f"BLOCK Y {start_y} FLIP {str(flipped).upper()}", x + 2, 81, color=INK)
        image = _composite(recipe, rendered, direction, current, farmer_pixels)
        draw_rect(canvas, x + 30, 96, 68, 132, BORDER)
        draw_rect(canvas, x + 32, 98, 64, 128, TILE)
        blit(canvas, image, x + 32, 98)
        # Read and assert the model used by the actual generated content.
        view = model[field]
        assert view["StartingPosition"] == {"X": 0, "Y": start_y}
        assert view["Flipped"] is flipped
        assert animation_source(view, current) == current
    return canvas


def main() -> None:
    farmer = read_rgba_png(FARMER)["pixels"]
    recipes = generate_v46b_prototypes()
    results = []
    for recipe in recipes:
        rendered = render_v46b(recipe)
        generated = appearance_json_v46b(recipe, rendered)
        folder = "".join(part.title() for part in recipe["name"].lower().replace("-", " ").split())
        packed = json.loads((PACK / "Pants" / folder / "pants.json").read_text(encoding="utf-8"))
        directions = {}
        for label, direction, facing, current, field, start_y, flipped in ORIENTATION:
            source = animation_source(packed[field], current)
            ok = (
                packed[field]["StartingPosition"] == {"X": 0, "Y": start_y}
                and generated[field]["StartingPosition"] == {"X": 0, "Y": start_y}
                and packed[field].get("Flipped", False) is flipped
                and generated[field].get("Flipped", False) is flipped
                and source == current
            )
            directions[direction] = {
                "label": label,
                "farmerFacingDirection": facing,
                "currentFarmerFrame": current,
                "fashionSenseModel": field,
                "sourceFrame": source,
                "directionBlockY": start_y,
                "flipped": flipped,
                "passes": ok,
            }
        results.append({"id": recipe["id"], "name": recipe["name"], "directions": directions, "passes": all(item["passes"] for item in directions.values())})

    diagnostic_recipe = recipes[1]
    diagnostic_render = render_v46b(diagnostic_recipe)
    write_rgba_png(OUT, make_sheet(diagnostic_recipe, diagnostic_render, farmer))
    report = {
        "fashionSenseVersion": "7.5.0",
        "authority": "PantsContentPack.GetPantsFromFacingDirection plus official SimplePantsTemplate UniformAnimation",
        "fashionSenseAssetMapping": "FIXED",
        "previewRendererMapping": "FIXED",
        "diagnosticGarment": diagnostic_recipe["name"],
        "garments": results,
        "temporaryMarkersInGameAssets": False,
    }
    AUDIT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not all(item["passes"] for item in results):
        raise SystemExit("orientation audit failed")
    print(json.dumps({"fashionSenseAssetMapping": "FIXED", "previewRendererMapping": "FIXED", "garments": len(results)}, indent=2))


if __name__ == "__main__":
    main()
