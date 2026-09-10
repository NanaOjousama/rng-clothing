"""V5B upper-garment renderer and coordinated Fashion Sense Sleeves adapter.

The Shirt renderer remains the frozen V4/V3 implementation.  This module adds
article-owned shoulder/neckline finishing and, when requested, a full Fashion
Sense 7.5.0 Sleeves atlas generated from the framework's pose template at the
target 32x64 logical resolution.  Semantic recipes contain no cells.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from generator.png_utils import RGBA, TRANSPARENT, blank_image, read_rgba_png
from generator.renderers.fashionsense.article_v4 import _apply_vest, load_v4_article_grammar, render_fs_v4
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.v3.engine import load_v3_data


ROOT = Path(__file__).resolve().parents[3]
GRAMMAR = ROOT / "generator" / "data" / "fashionsense" / "v5b_upper_grammar.json"
FS_SLEEVES = ROOT / "FASHION SENSE" / "FashionSense-stable" / "FashionSense" / "Framework" / "Assets" / "Local Pack" / "Sleeves"
GARMENT_MASKS = {(36, 36, 36), (119, 119, 119), (158, 158, 158)}


@dataclass(frozen=True)
class FSV5BUpperRender:
    recipe: dict[str, Any]
    base: Any
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    texture: list[list[RGBA]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    hide_native_sleeves: bool
    companion_required: bool
    sleeves_texture: list[list[RGBA]] | None
    sleeves_json: dict[str, Any] | None
    sleeve_idle_frames: dict[str, list[list[RGBA]]] | None
    modified_cells: dict[str, frozenset[tuple[int, int]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    sleeve_metrics: dict[str, Any]


def load_v5b_fs_grammar() -> dict[str, Any]:
    return json.loads(GRAMMAR.read_text(encoding="utf-8"))


def _stack(frames: dict[str, list[list[RGBA]]]) -> list[list[RGBA]]:
    texture = blank_image(16, 64)
    for index, direction in enumerate(DIRECTION_ORDER):
        for y, row in enumerate(frames[direction]):
            texture[index * 16 + y] = list(row)
    return texture


def _story(render) -> dict[str, Any]:
    name = render.base.design.recipe["paletteStory"]
    return load_v3_data()["palettes"]["stories"][name]


def _mask_value(render, role: str) -> RGBA:
    value = render.base.design.base.config["outerMaskRamp"].get(role, 119)
    return value, value, value, 255


def _default_value(render, role: str) -> RGBA:
    story = _story(render)
    if role in {"EXTERIOR_CONTOUR", "DEEP_CREASE", "STRUCTURAL_EDGE", "SHADOW"}:
        rgb = story["darkAccent"]
    elif role in {"LIGHT", "OPTIONAL_HIGHLIGHT"}:
        rgb = story["lightAccent"]
    else:
        rgb = story["secondary"]
    return tuple(rgb) + (255,)


def _paint(frames, defaults, direction: str, x: int, y: int, mask: RGBA, default: RGBA, modified) -> None:
    if 0 <= y < 16 and 0 <= x < 16 and frames[direction][y][x][3]:
        frames[direction][y][x] = mask
        defaults[direction][y][x] = default
        modified[direction].add((x, y))


def _apply_shoulder_intent(render, frames, defaults, modified) -> None:
    intent = render.recipe["shoulderIntent"]
    if intent == "standard": return
    regions = render.base.design.base.regions
    role = "SHADOW" if intent == "narrow" else "STRUCTURAL_EDGE"
    for direction in DIRECTION_ORDER:
        for y in range(5):
            cells = [x for x in range(16) if regions[direction][y][x] == "SHOULDER_CAP" and frames[direction][y][x][3]]
            if not cells: continue
            targets = {cells[0], cells[-1]} if intent == "narrow" else {x for x in cells if y >= 1}
            for x in targets:
                _paint(frames, defaults, direction, x, y, _mask_value(render, role), _default_value(render, role), modified)


def _apply_neckline_intent(render, frames, defaults, modified) -> None:
    intent = render.recipe["necklineIntent"]
    for direction in ("front", "back"):
        if intent == "high":
            for x, y, role in ((6, 0, "SHADOW"), (9, 0, "SHADOW"), (6, 1, "BASE"), (9, 1, "BASE")):
                # Fill only if the adjacent collar already proves this is the neck recess.
                if frames[direction][y][max(0, x - 1)][3] or frames[direction][y][min(15, x + 1)][3]:
                    frames[direction][y][x] = _mask_value(render, role)
                    defaults[direction][y][x] = _default_value(render, role)
                    modified[direction].add((x, y))
        elif intent == "v_neck" and direction == "front":
            for x, y in ((6, 1), (9, 1), (7, 2), (8, 2)):
                _paint(frames, defaults, direction, x, y, _mask_value(render, "DEEP_CREASE"), _default_value(render, "DEEP_CREASE"), modified)
        elif intent == "square" and direction == "front":
            for x, y in ((5, 1), (6, 1), (9, 1), (10, 1), (6, 2), (9, 2)):
                _paint(frames, defaults, direction, x, y, _mask_value(render, "STRUCTURAL_EDGE"), _default_value(render, "STRUCTURAL_EDGE"), modified)


def _hide_placket_for_tee(render, frames, defaults, modified) -> None:
    regions = render.base.design.base.regions
    for direction in DIRECTION_ORDER:
        for y in range(16):
            body = [x for x in range(16) if regions[direction][y][x] == "BODY" and frames[direction][y][x][3]]
            if not body: continue
            source = body[len(body) // 2]
            for x in range(16):
                if regions[direction][y][x] == "PLACKET" and frames[direction][y][x][3]:
                    frames[direction][y][x] = frames[direction][y][source]
                    defaults[direction][y][x] = defaults[direction][y][source]
                    modified[direction].add((x, y))


def _apply_blouse_finish(render, frames, defaults, modified) -> None:
    variant = render.recipe["constructionVariant"]
    story = _story(render)
    accent = tuple(story["lightAccent"]) + (255,)
    dark = tuple(story["darkAccent"]) + (255,)
    if variant == "sailor_blouse":
        for direction in ("front", "back"):
            for x, y in ((4, 1), (5, 2), (10, 2), (11, 1), (4, 2), (11, 2)):
                _paint(frames, defaults, direction, x, y, _mask_value(render, "SECONDARY_LIGHT"), accent, modified)
    elif variant == "bow_blouse":
        for x, y, color in ((6, 3, dark), (7, 3, accent), (8, 3, accent), (9, 3, dark), (7, 4, dark), (8, 4, dark)):
            _paint(frames, defaults, "front", x, y, _mask_value(render, "SECONDARY_LIGHT"), color, modified)


def _coverage_missing(render, frames, *, allow_sleeve_exposure: bool) -> dict[str, tuple[tuple[int, int], ...]]:
    source = render.base.design.base.config["bodyCoverageEnvelope"]
    regions = render.base.design.base.regions
    result = {}
    for direction in DIRECTION_ORDER:
        name = "right" if direction == "left" else direction
        rows = source[name]
        if direction == "left": rows = [row[::-1] for row in rows]
        missing = []
        for y, row in enumerate(rows):
            for x, marker in enumerate(row):
                if marker != "#" or frames[direction][y][x][3]: continue
                if allow_sleeve_exposure and regions[direction][y][x] == "SLEEVE": continue
                missing.append((x, y))
        result[direction] = tuple(missing)
    return result


def _apply_sleeveless(render, frames, defaults, modified) -> None:
    regions = render.base.design.base.regions
    for direction in DIRECTION_ORDER:
        for y in range(16):
            for x in range(16):
                if regions[direction][y][x] == "SLEEVE" and frames[direction][y][x][3]:
                    frames[direction][y][x] = TRANSPARENT
                    defaults[direction][y][x] = TRANSPARENT
                    modified[direction].add((x, y))


def _load_sleeve_source(template: str) -> tuple[list[list[RGBA]], dict[str, Any]]:
    folder = FS_SLEEVES / template
    pixels = read_rgba_png(folder / "sleeves.png")["pixels"]
    text = (folder / "sleeves.json").read_text(encoding="utf-8-sig")
    # The official 7.5.0 templates are JSON-with-comments. Strip // only when
    # it occurs outside a quoted string so documentation URLs remain intact.
    clean_lines = []
    for line in text.splitlines():
        quoted = escaped = False; cut = len(line); index = 0
        while index < len(line):
            char = line[index]
            if escaped: escaped = False
            elif char == "\\" and quoted: escaped = True
            elif char == '"': quoted = not quoted
            elif not quoted and char == "/" and index + 1 < len(line) and line[index + 1] == "/":
                cut = index; break
            index += 1
        clean_lines.append(line[:cut])
    text = "\n".join(clean_lines)
    model = json.loads(text)
    return pixels, model


def _target_atlas(source: list[list[RGBA]]) -> list[list[RGBA]]:
    """Author a 2x-density logical atlas directly from the FS pose topology.

    Each source topology cell seeds four target cells; subsequent passes add
    one-cell optical edges and cuff/layer structure that do not exist at the
    source density. Alpha is intentionally binary.
    """
    target = blank_image(len(source[0]) * 2, len(source) * 2)
    for y, row in enumerate(source):
        for x, pixel in enumerate(row):
            normalized = pixel[:3] + ((255,) if pixel[3] else (0,))
            for yy in (y * 2, y * 2 + 1):
                for xx in (x * 2, x * 2 + 1):
                    target[yy][xx] = normalized
    # Scale-2 optical weight: reinforce shadow-facing right/bottom contours by
    # one target logical cell, not by a uniform doubled border.
    original = [list(row) for row in target]
    for y, row in enumerate(original):
        for x, pixel in enumerate(row):
            if pixel[:3] not in GARMENT_MASKS or not pixel[3]: continue
            right_open = x + 1 >= len(row) or not original[y][x + 1][3]
            below_open = y + 1 >= len(original) or not original[y + 1][x][3]
            if right_open or below_open:
                target[y][x] = (36, 36, 36, 255)
    return target


def _add_cuff(atlas: list[list[RGBA]], model: dict[str, Any], depth: int, colors: tuple[RGBA, RGBA]) -> int:
    if depth <= 0: return 0
    skin = model["FrontSleeves"]["SkinToneMasks"]
    skin_colors = {tuple(skin[key]) for key in ("LightTone", "MediumTone", "DarkTone")}
    garment = {(x, y) for y, row in enumerate(atlas) for x, p in enumerate(row) if p[:3] in GARMENT_MASKS and p[3]}
    skin_cells = {(x, y) for y, row in enumerate(atlas) for x, p in enumerate(row) if p[:3] in skin_colors and p[3]}
    frontier = {cell for cell in garment if any((cell[0] + dx, cell[1] + dy) in skin_cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    visited: set[tuple[int, int]] = set(); current = set(frontier)
    for distance in range(depth):
        next_cells: set[tuple[int, int]] = set()
        color = colors[min(distance, len(colors) - 1)]
        for x, y in current - visited:
            atlas[y][x] = color; visited.add((x, y))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (x + dx, y + dy)
                if neighbor in garment and neighbor not in visited: next_cells.add(neighbor)
        current = next_cells
    return len(visited)


def _convert_garment_masks_to_skin(atlas: list[list[RGBA]], model: dict[str, Any]) -> int:
    """Convert the full animated cloth mask into a skin-tone-masked arm."""
    skin = model["FrontSleeves"]["SkinToneMasks"]
    mapping = {
        (36, 36, 36): tuple(skin["DarkTone"]),
        (119, 119, 119): tuple(skin["MediumTone"]),
        (158, 158, 158): tuple(skin["LightTone"]),
    }
    changed = 0
    for y, row in enumerate(atlas):
        for x, pixel in enumerate(row):
            if pixel[:3] in mapping and pixel[3]:
                atlas[y][x] = mapping[pixel[:3]] + (255,)
                changed += 1
    return changed


def _sleeves_json(name: str, source: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(source); result["Name"] = name; result["Format"] = "7.5.0"
    for key in ("FrontSleeves", "BackSleeves", "RightSleeves", "LeftSleeves"):
        model = result[key]
        model["SleevesSize"] = {"Width": 32, "Length": 64}
        model["Scale"] = 2.0
        model["BodyPosition"] = {"X": 0, "Y": 0}
        model["DisableNativeOffset"] = True
        model["DrawBeforeShirt"] = True
        model["UseShirtColors"] = True
    return result


def _crop_frame(atlas: list[list[RGBA]], index: int) -> list[list[RGBA]]:
    width = 32; height = 64; columns = len(atlas[0]) // width
    x0 = (index % columns) * width; y0 = (index // columns) * height
    return [list(row[x0:x0 + width]) for row in atlas[y0:y0 + height]]


def _flip(frame: list[list[RGBA]]) -> list[list[RGBA]]:
    return [list(reversed(row)) for row in frame]


def _idle_frames(atlas, model) -> dict[str, list[list[RGBA]]]:
    result = {}
    for direction, key in (("front", "FrontSleeves"), ("right", "RightSleeves"), ("back", "BackSleeves"), ("left", "LeftSleeves")):
        part = model[key]; frame_index = part["UniformAnimation"][0]["Frame"]
        frame = _crop_frame(atlas, frame_index)
        result[direction] = _flip(frame) if part.get("Flipped") else frame
    return result


def _build_companion(render, name: str) -> tuple[list[list[RGBA]], dict[str, Any], dict[str, list[list[RGBA]]], dict[str, Any]]:
    grammar = load_v5b_fs_grammar()["customSleeves"]; intent = render.recipe["sleeveIntent"]
    family = grammar["families"][intent]
    source, source_json = _load_sleeve_source(family["template"])
    atlas = _target_atlas(source)
    story = _story(render)
    dark = tuple(story["darkAccent"]) + (255,)
    secondary = tuple(story["secondary"]) + (255,)
    bare_arm_cells = _convert_garment_masks_to_skin(atlas, source_json) if family.get("bareArm") else 0
    cuff_cells = _add_cuff(atlas, source_json, family["cuffDepth"], (dark, secondary))
    model = _sleeves_json(name + " Sleeves", source_json)
    return atlas, model, _idle_frames(atlas, model), {
        "template": family["template"], "targetFrame": [32, 64], "scale": 2,
        "atlas": [len(atlas[0]), len(atlas)], "cuffCells": cuff_cells, "bareArmCells": bare_arm_cells,
        "alphaValues": sorted({p[3] for row in atlas for p in row}),
        "highestReferencedFrame": max(a["Frame"] for key in ("FrontSleeves", "BackSleeves", "RightSleeves", "LeftSleeves") for a in model[key]["UniformAnimation"]),
    }


def render_fs_v5b(recipe: dict[str, Any]) -> FSV5BUpperRender:
    from generator.v5b.engine import validate_v5b_recipe

    validation = validate_v5b_recipe(recipe)
    if not validation.valid: raise ValueError("invalid V5B recipe: " + "; ".join(validation.errors))
    base = render_fs_v4(recipe["baseArticleRecipe"])
    holder = type("V5BHolder", (), {})(); holder.recipe = recipe; holder.base = base
    frames = {d: [list(row) for row in base.frames[d]] for d in DIRECTION_ORDER}
    defaults = {d: [list(row) for row in base.default_frames[d]] for d in DIRECTION_ORDER}
    modified = {d: set() for d in DIRECTION_ORDER}
    sleeve_colors = base.sleeve_colors
    if recipe["articleType"] == "VEST_TOP":
        translated = {d: set() for d in DIRECTION_ORDER}
        sleeve_colors = _apply_vest(frames, defaults, base.design, load_v4_article_grammar()["articles"]["VEST_TOP"], translated)
        for direction in DIRECTION_ORDER: modified[direction].update(translated[direction])
    holder.frames = frames; holder.default_frames = defaults
    _apply_shoulder_intent(holder, frames, defaults, modified)
    _apply_neckline_intent(holder, frames, defaults, modified)
    if recipe["constructionVariant"] == "plain_tee": _hide_placket_for_tee(holder, frames, defaults, modified)
    if recipe["articleType"] == "BLOUSE": _apply_blouse_finish(holder, frames, defaults, modified)
    sleeveless = recipe["sleeveIntent"] == "SLEEVELESS"
    hide_native = False
    if sleeveless: _apply_sleeveless(holder, frames, defaults, modified)
    coverage = _coverage_missing(holder, frames, allow_sleeve_exposure=sleeveless)
    if any(coverage.values()): raise ValueError(f"V5B body coverage failed: {coverage}")
    companion = recipe["sleeveIntent"] in {"SLEEVELESS", "FITTED_LONG_SLEEVE", "ROLLED_CUFFED_SLEEVE", "LAYERED_INNER_OUTER_SLEEVE"}
    sleeve_texture = sleeve_json = idle = None; sleeve_metrics: dict[str, Any] = {"mechanism": "native"}
    if companion:
        name = recipe["baseArticleRecipe"]["designRecipe"]["itemName"]
        sleeve_texture, sleeve_json, idle, sleeve_metrics = _build_companion(holder, name)
        sleeve_metrics["mechanism"] = "generated_fs_sleeves_companion"
    return FSV5BUpperRender(
        recipe, base, frames, defaults, _stack(frames), sleeve_colors, hide_native, companion,
        sleeve_texture, sleeve_json, idle, {d: frozenset(v) for d, v in modified.items()}, coverage, sleeve_metrics,
    )
