#!/usr/bin/env python3
"""Render exactly three selected AoT-inspired profile recipes through frozen FS HD V2."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.png_utils import (
    RGBA,
    blank_image,
    blit,
    draw_rect,
    draw_text,
    nearest_scale,
    text_width,
    write_rgba_png,
)
from generator.renderers.fashionsense import diagnose_fs_hd_render, render_fs_hd_v2
from generator.v2_recipe_engine import load_v2_data


RECIPE_BATCH = ROOT / "output" / "recipes" / "aot_style_profile_poc.json"
BASE_OUTPUT = ROOT / "output" / "fashionsense" / "style-profile-aot"
OUTPUT = BASE_OUTPUT / "revised"
COMPARISON = ROOT / "output" / "comparisons" / "AOT_STYLE_PROFILE_3WAY.png"
BEFORE_AFTER = ROOT / "output" / "comparisons" / "AOT_STYLE_PROFILE_PREVIOUS_VS_REVISED.png"
PACK = ROOT / "test-packs" / "fashionsense" / "RNG-Clothing-AoT-Style-POC"
STACK_ORDER = ("front", "right", "left", "back")
DIRECTIONS = ("front", "back", "left", "right")
BACKGROUND: RGBA = (236, 226, 211, 255)
INK: RGBA = (61, 55, 51, 255)
BORDER: RGBA = (91, 83, 75, 255)
FRAME_BACK: RGBA = (215, 207, 194, 255)


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _slug(name: str) -> str:
    return "_".join(name.lower().replace("-", " ").split())


def _folder(name: str) -> str:
    return "".join(part.title() for part in _slug(name).split("_"))


def _stack(frames):
    result = blank_image(16, 64)
    for index, direction in enumerate(STACK_ORDER):
        for y, row in enumerate(frames[direction]):
            result[index * 16 + y] = list(row)
    return result


def _bordered_blit(destination, source, x: int, y: int) -> None:
    draw_rect(destination, x - 2, y - 2, len(source[0]) + 4, len(source) + 4, BORDER)
    draw_rect(destination, x - 1, y - 1, len(source[0]) + 2, len(source) + 2, FRAME_BACK)
    blit(destination, source, x, y)


def _contact(title: str, frames, scale: int):
    size = 16 * scale
    gap = 18
    left = 16
    top = 38
    width = left * 2 + size * 4 + gap * 3
    canvas = blank_image(width, top + size + 16, BACKGROUND)
    draw_text(canvas, title, max(3, (width - text_width(title)) // 2), 7, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = left + index * (size + gap)
        draw_text(canvas, direction, x + (size - text_width(direction)) // 2, 23, color=INK)
        _bordered_blit(canvas, nearest_scale(frames[direction], scale), x, top)
    return canvas


def _comparison(rendered):
    sprite = 32
    label_width = 122
    gap = 20
    top = 48
    row_height = 55
    width = label_width + sprite * 4 + gap * 3 + 20
    height = top + row_height * len(rendered) + 16
    canvas = blank_image(width, height, BACKGROUND)
    title = "AOT INSPIRED STYLE PROFILE - GAMEPLAY FOOTPRINT"
    subtitle = "ORIGINAL FIELDWEAR - 16X16 AT SCALE 2"
    draw_text(canvas, title, max(3, (width - text_width(title)) // 2), 7, color=INK)
    draw_text(canvas, subtitle, max(3, (width - text_width(subtitle)) // 2), 20, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = label_width + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 34, color=INK)
    for row_index, (candidate, render) in enumerate(rendered):
        y = top + row_index * row_height
        name = candidate["recipe"]["itemName"]
        words = name.upper().split()
        midpoint = max(1, len(words) // 2)
        draw_text(canvas, " ".join(words[:midpoint]), 7, y + 8, color=INK)
        draw_text(canvas, " ".join(words[midpoint:]), 7, y + 20, color=INK)
        draw_text(canvas, candidate["styleStrength"], 7, y + 34, color=INK)
        for index, direction in enumerate(DIRECTIONS):
            x = label_width + index * (sprite + gap)
            _bordered_blit(canvas, nearest_scale(render.default_frames[direction], 2), x, y)
    return canvas


def _before_after(previous, revised):
    sprite = 32
    label_width = 128
    gap = 20
    top = 58
    row_height = 49
    section_gap = 16
    width = label_width + sprite * 4 + gap * 3 + 20
    height = top + row_height * 6 + section_gap + 14
    canvas = blank_image(width, height, BACKGROUND)
    title = "AOT STYLE POOL - PREVIOUS VS REVISED"
    subtitle = "EXACT GAMEPLAY FOOTPRINT - CONSTRUCTION DIFFERENTIATION"
    draw_text(canvas, title, max(3, (width - text_width(title)) // 2), 7, color=INK)
    draw_text(canvas, subtitle, max(3, (width - text_width(subtitle)) // 2), 20, color=INK)
    for index, direction in enumerate(DIRECTIONS):
        x = label_width + index * (sprite + gap)
        draw_text(canvas, direction, x + (sprite - text_width(direction)) // 2, 41, color=INK)

    y = top
    for section, garments in (("PREVIOUS", previous), ("REVISED", revised)):
        for index_in_section, (candidate, render) in enumerate(garments):
            recipe = candidate["recipe"]
            draw_text(canvas, section if index_in_section == 0 else "", 6, y + 2, color=INK)
            words = recipe["itemName"].upper().split()
            midpoint = max(1, len(words) // 2)
            draw_text(canvas, " ".join(words[:midpoint]), 6, y + 14, color=INK)
            draw_text(canvas, " ".join(words[midpoint:]), 6, y + 26, color=INK)
            for direction_index, direction in enumerate(DIRECTIONS):
                x = label_width + direction_index * (sprite + gap)
                _bordered_blit(canvas, nearest_scale(render.default_frames[direction], 2), x, y)
            y += row_height
        y += section_gap
    return canvas


def _previous_set():
    paths = (
        BASE_OUTPUT / "rampart_field_jacket-recipe-summary.json",
        BASE_OUTPUT / "mosswatch_utility_jacket-recipe-summary.json",
        BASE_OUTPUT / "cadence_yoke_shirt-recipe-summary.json",
    )
    previous = []
    for path in paths:
        summary = json.loads(path.read_text(encoding="utf-8"))
        candidate = {
            "styleStrength": summary["styleStrength"],
            "branch": summary["branch"],
            "styleEvidence": summary["styleEvidence"],
            "recipe": summary["recipe"],
        }
        previous.append((candidate, render_fs_hd_v2(candidate["recipe"])))
    return previous


def _shirt_model(render, y: int) -> dict[str, Any]:
    config = render.config
    palette = load_v2_data()["palettes"]["families"][render.recipe["paletteFamily"]]
    return {
        "Scale": 2.0,
        "HideSleeves": False,
        "DisableGrayscale": False,
        "ColorMaskLayers": [{
            "Name": "Primary Fabric",
            "DefaultColor": palette["defaultDye"],
            "Values": [[config["outerMaskRamp"][role]] * 3 for role in render.active_main_roles],
        }],
        "SleeveColors": [[config["outerMaskRamp"][role]] * 3 for role in config["sleeveMaskRoles"]],
        "StartingPosition": {"X": 0, "Y": y},
        "BodyPosition": {"X": 0, "Y": 32},
        "ShirtSize": {"Width": 16, "Length": 16},
    }


def _shirt_json(candidate, render):
    recipe = candidate["recipe"]
    tags = [
        "Lifestyle",
        "Military Fieldwear",
        recipe["archetype"].replace("_", " ").title(),
        recipe["rarity"],
        candidate["styleStrength"].title(),
        "RNG Clothing",
        "Test",
    ]
    return {
        "Name": recipe["itemName"],
        "Format": "7.5.0",
        "Tags": tags,
        "FrontShirt": _shirt_model(render, 0),
        "RightShirt": _shirt_model(render, 16),
        "LeftShirt": _shirt_model(render, 32),
        "BackShirt": _shirt_model(render, 48),
    }


def _readme(names: list[str]) -> str:
    garments = "\n".join(f"- {name}" for name in names)
    return f"""# RNG Clothing - AoT-Inspired Style Profile POC

This isolated research pack contains exactly three original Fashion Sense garments generated from a corpus-level military-fieldwear style profile. No logo, insignia, character name, exact costume layout, or reference pixels are included.

## Requirements

- Stardew Valley 1.6.15
- SMAPI
- Fashion Sense 7.5.0 installed separately

## Install

Copy the entire `RNG-Clothing-AoT-Style-POC` folder into `Stardew Valley/Mods`, then fully restart SMAPI.

Expected path:

```text
Stardew Valley/Mods/RNG-Clothing-AoT-Style-POC/manifest.json
```

## Garments

{garments}

Run `fs_add_mirror` if you need a Hand Mirror, then select each entry under Shirts. Check all directions while standing and walking, plus normal tool and horse behavior.

The pack keeps 16x16 logical frames, Scale 2, BodyPosition `(0,32)`, and native animated sleeve recoloring. It is not installed automatically and is not production content.
"""


def main() -> None:
    previous = _previous_set()
    batch = json.loads(RECIPE_BATCH.read_text(encoding="utf-8"))
    selected = [candidate for candidate in batch["candidates"] if candidate["selection"] == "SELECTED"]
    if len(selected) != 3:
        raise ValueError("AoT POC must render exactly three selected recipes")
    rendered = []
    validation = {
        "status": "PASS_GENERATION",
        "beautyClaim": "PENDING_CRITICAL_STATIC_AND_INGAME_REVIEW",
        "rendererFrozen": True,
        "rendererSpecificPixelHacks": False,
        "garments": [],
    }
    translations = {}
    names = []

    for candidate in selected:
        recipe = candidate["recipe"]
        render = render_fs_hd_v2(recipe)
        diagnostics = diagnose_fs_hd_render(render)
        if not diagnostics.passes or diagnostics.warnings:
            raise ValueError(f"{recipe['id']}: permanent renderer diagnostics {diagnostics}")
        rendered.append((candidate, render))
        slug = _slug(recipe["itemName"])
        write_rgba_png(OUTPUT / f"{slug}.png", render.texture)
        write_rgba_png(OUTPUT / f"{slug}-default-8x.png", nearest_scale(_stack(render.default_frames), 8))
        write_rgba_png(OUTPUT / f"{slug}-directions-8x.png", _contact(recipe["itemName"], render.default_frames, 8))
        write_rgba_png(OUTPUT / f"{slug}-directions-gameplay-2x.png", _contact(recipe["itemName"] + " GAME SIZE", render.default_frames, 2))
        _json(OUTPUT / f"{slug}-recipe-summary.json", {
            "styleStrength": candidate["styleStrength"],
            "branch": candidate["branch"],
            "styleEvidence": candidate["styleEvidence"],
            "recipe": recipe,
            "sideTemplate": render.side_template,
            "activeMainRoles": list(render.active_main_roles),
        })

        shirt_dir = PACK / "Shirts" / _folder(recipe["itemName"])
        shirt_dir.mkdir(parents=True, exist_ok=True)
        _json(shirt_dir / "shirt.json", _shirt_json(candidate, render))
        write_rgba_png(shirt_dir / "shirt.png", render.texture)
        key = slug.replace("_", "-")
        translations[f"shirt.{key}.name"] = recipe["itemName"]
        translations[f"shirt.{key}.description"] = recipe["itemDescription"]
        names.append(recipe["itemName"])
        validation["garments"].append({
            "id": recipe["id"],
            "name": recipe["itemName"],
            "styleStrength": candidate["styleStrength"],
            "branch": candidate["branch"],
            "sideTemplate": render.side_template,
            "diagnostics": {"passes": True, "errors": [], "warnings": [], "metrics": diagnostics.metrics},
        })

    write_rgba_png(COMPARISON, _comparison(rendered))
    write_rgba_png(BEFORE_AFTER, _before_after(previous, rendered))
    _json(OUTPUT / "validation.json", validation)
    _json(OUTPUT / "rendered_selection.json", {
        "sourceBatch": str(RECIPE_BATCH.relative_to(ROOT)),
        "count": 3,
        "selectedIds": [candidate["recipe"]["id"] for candidate in selected],
        "recipes": [candidate["recipe"] for candidate in selected],
    })
    _json(PACK / "manifest.json", {
        "Name": "RNG Clothing AoT-Inspired Style POC",
        "Author": "RNG Clothing Experiment",
        "Version": "1.0.0",
        "Description": "Test-only Fashion Sense pack containing three original military-fieldwear style-profile garments.",
        "UniqueID": "RNGClothing.FashionSense.AoTStylePOC",
        "UpdateKeys": [],
        "ContentPackFor": {"UniqueID": "PeacefulEnd.FashionSense", "MinimumVersion": "7.5.0"},
    })
    _json(PACK / "i18n" / "default.json", translations)
    (PACK / "README.md").write_text(_readme(names), encoding="utf-8")
    print(f"Rendered exactly three style-profile garments at {OUTPUT}")
    print(f"Created equal-footprint comparison at {COMPARISON}")
    print(f"Created previous-vs-revised comparison at {BEFORE_AFTER}")
    print(f"Created isolated test pack at {PACK}")


if __name__ == "__main__":
    main()
