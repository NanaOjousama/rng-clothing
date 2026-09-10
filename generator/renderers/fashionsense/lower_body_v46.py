"""Full-frame Fashion Sense lower-body adapters for V4.6.

The installed official template alpha is a pose/coverage contract. All visible
colors, region roles, outlines, and semantic details are generated locally.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from generator.png_utils import RGBA, blank_image
from generator.v46.engine import validate_v46_recipe


ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "generator" / "data" / "fashionsense" / "v46" / "lower_body_frame_contracts.json"
MASK = {"deep": (54, 54, 54, 255), "shadow": (102, 102, 102, 255), "base": (154, 154, 154, 255), "light": (205, 205, 205, 255)}
FIXED = {"outline": (35, 31, 29, 255), "leather": (76, 49, 36, 255), "olive": (78, 88, 58, 255), "brass": (173, 129, 64, 255), "charcoal": (62, 61, 62, 255)}


@dataclass(frozen=True)
class V46Render:
    recipe: dict
    contract: dict
    texture: list[list[RGBA]]
    frame_previews: dict[int, list[list[RGBA]]]
    static_errors: tuple[str, ...]
    runtime_status: str = "EXPERIMENTAL"


def load_contracts() -> dict:
    return json.loads(CONTRACTS.read_text(encoding="utf-8"))


def _cells(entry: dict) -> set[tuple[int, int]]:
    return {(x, row["y"]) for row in entry["rowSpans"] for a, b in row["spans"] for x in range(a, b + 1)}


def _neighbors(cell):
    x, y = cell
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))


def _bounds(cells):
    xs = [x for x, _ in cells]; ys = [y for _, y in cells]
    return min(xs), min(ys), max(xs), max(ys)


def _extend_boot(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """Add a compact frame-relative shaft; runtime behavior remains unproven."""
    if not cells:
        return cells
    x0, y0, x1, _ = _bounds(cells)
    inset = 1 if x1 - x0 + 1 >= 6 else 0
    for y in range(max(0, y0 - 2), y0):
        for x in range(x0 + inset, x1 - inset + 1):
            cells.add((x, y))
    return cells


def _render_frame(recipe: dict, entry: dict) -> list[list[RGBA]]:
    frame = blank_image(16, 32)
    cells = _cells(entry)
    rare = recipe["rarity"] == "Rare"
    article = recipe["articleType"]
    if article == "FOOTWEAR" and rare:
        cells = _extend_boot(set(cells))
    if not cells:
        return frame
    x0, y0, x1, y1 = _bounds(cells)
    height = max(1, y1 - y0 + 1); mid = (x0 + x1) / 2
    for x, y in sorted(cells, key=lambda value: (value[1], value[0])):
        exterior = any(n not in cells for n in _neighbors((x, y)))
        rel = (y - y0) / max(1, height - 1)
        color = MASK["base"]
        if exterior: color = FIXED["outline"]
        elif x <= x0 + 1 or rel > .78: color = MASK["shadow"]
        elif y <= y0 + 1 and x < mid: color = MASK["light"]
        if article == "FITTED_PANTS":
            if y == y0 + 1 and not exterior: color = FIXED["leather"] if rare else MASK["deep"]
            if rare and not exterior and (x <= x0 + 1 or x >= x1 - 1) and .18 < rel < .72: color = FIXED["olive"]
            if rare and not exterior and .48 < rel < .65 and abs(x - mid) >= 1.5: color = MASK["deep"]
            if rare and not exterior and .22 < rel < .44 and x == int(mid) - 2: color = FIXED["leather"]
        else:
            if y >= y1 - 1: color = FIXED["outline"]
            elif y <= y0 + (1 if rare else 0) and not exterior: color = FIXED["leather"]
            elif rare and not exterior and .28 < rel < .58: color = FIXED["leather"]
            elif rare and not exterior and x >= mid and rel < .38: color = FIXED["brass"]
            elif not rare and not exterior: color = FIXED["charcoal"]
        frame[y][x] = color
    return frame


def _place(atlas, frame, index):
    x0 = (index % 6) * 16; y0 = (index // 6) * 32
    for y, row in enumerate(frame): atlas[y0 + y][x0:x0 + 16] = list(row)


def render_v46(recipe: dict) -> V46Render:
    errors = list(validate_v46_recipe(recipe))
    contract = load_contracts()["contracts"][recipe["articleType"]]
    info = contract["texture"]
    atlas = blank_image(info["width"], info["height"]); previews = {}
    for index in range(info["capacity"]):
        frame = _render_frame(recipe, contract["coverage"].get(str(index), {"rowSpans": []}))
        previews[index] = frame; _place(atlas, frame, index)
    alpha = {pixel[3] for row in atlas for pixel in row}
    if alpha - {0, 255}: errors.append("alpha is not binary")
    intentional_empty = set(contract.get("intentionallyEmptyUsedFrames", []))
    for index in contract["usedFrames"]:
        if index not in intentional_empty and not any(pixel[3] for row in previews[index] for pixel in row): errors.append(f"used frame {index} unexpectedly lost coverage")
    return V46Render(recipe, contract, atlas, previews, tuple(errors))


def color_mask_layers(recipe: dict) -> list[dict]:
    default = [181, 161, 118] if recipe["articleType"] == "FITTED_PANTS" and recipe["rarity"] == "Common" else [91, 105, 69] if recipe["articleType"] == "FITTED_PANTS" else [74, 69, 66] if recipe["rarity"] == "Common" else [91, 59, 43]
    return [{"Name": "Primary material", "DefaultColor": default, "Values": [[v, v, v] for v in (54, 102, 154, 205)]}]


def appearance_json(recipe: dict, render: V46Render) -> dict:
    article = recipe["articleType"]; suffix = "Pants" if article == "FITTED_PANTS" else "Shoes"
    root = {"Name": recipe["name"], "Format": "7.5.0", "Tags": ["RNG Clothing", "V4.6", "Runtime Proof", article.replace("_", " ").title(), recipe["rarity"]]}
    for direction in ("front", "back", "right", "left"):
        source = render.contract["models"][direction]
        model = {"Scale": 4.0, "DisableNativeOffset": True, "DisableGrayscale": False, "ColorMaskLayers": color_mask_layers(recipe), "StartingPosition": source["startingPosition"], "BodyPosition": source["bodyPosition"], suffix + "Size": source["size"], "HideWhileSwimming": True, "HideWhileWearingBathingSuit": True, "UniformAnimation": source["uniformAnimation"]}
        if article == "FITTED_PANTS": model.update({"HideLegs": False, "HideShadow": False})
        else: model["DrawBeforePants"] = True
        root[direction.title() + suffix] = model
    return root
