"""Controlled signature overlays for the V6 Legendary calibration.

These overlays spend existing palette roles on one coherent identity gesture.
They never expand the coverage mask, add antialiasing, or change runtime
assembly.  Coordinates belong to reusable article-role templates, not named
garments.
"""

from __future__ import annotations

from dataclasses import dataclass

from generator.png_utils import RGBA


@dataclass(frozen=True)
class LegendarySignatureFrames:
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    metrics: dict[str, object]


@dataclass(frozen=True)
class LegendaryConstructionFrames:
    frames: dict[str, list[list[RGBA]]]
    default_frames: dict[str, list[list[RGBA]]]
    metrics: dict[str, object]


def _copy(frames):
    return {direction: [list(row) for row in frame] for direction, frame in frames.items()}


def _lum(color: RGBA) -> float:
    return .2126 * color[0] + .7152 * color[1] + .0722 * color[2]


def _sat(color: RGBA) -> int:
    return max(color[:3]) - min(color[:3])


def _role_pairs(mask_frames, default_frames):
    pairs: dict[tuple[RGBA, RGBA], int] = {}
    for direction in default_frames:
        for y, row in enumerate(default_frames[direction]):
            for x, color in enumerate(row):
                mask = mask_frames[direction][y][x]
                if color[3] and mask[3]: pairs[(mask, color)] = pairs.get((mask, color), 0) + 1
    values = list(pairs)
    accent = max(values, key=lambda pair: (_sat(pair[1]) * 2 + _lum(pair[1]), pairs[pair]))
    light = max(values, key=lambda pair: (_lum(pair[1]), _sat(pair[1]), pairs[pair]))
    dark = min(values, key=lambda pair: (_lum(pair[1]), -pairs[pair]))
    return {"accent": accent, "light": light, "dark": dark}


def _paint(mask_frames, default_frames, direction, coords, pair):
    painted = 0
    for x, y in coords:
        if 0 <= y < 16 and 0 <= x < 16 and default_frames[direction][y][x][3]:
            mask_frames[direction][y][x], default_frames[direction][y][x] = pair
            painted += 1
    return painted


def _clear(mask_frames, default_frames, direction, coords):
    cleared = 0
    transparent: RGBA = (0, 0, 0, 0)
    for x, y in coords:
        if 0 <= y < 16 and 0 <= x < 16 and default_frames[direction][y][x][3]:
            mask_frames[direction][y][x] = transparent
            default_frames[direction][y][x] = transparent
            cleared += 1
    return cleared


def _add(mask_frames, default_frames, direction, coords, pair):
    added = 0
    for x, y in coords:
        if 0 <= y < 16 and 0 <= x < 16 and not default_frames[direction][y][x][3]:
            mask_frames[direction][y][x], default_frames[direction][y][x] = pair
            added += 1
    return added


CONSTRUCTION = {
    # A short open shell: the two hem notches keep the center opening alive
    # through the cropped termination instead of forming a shirt-like bar.
    "CROPPED_FIELD_JACKET": {
        "clear": {"front": [(7, 12), (8, 12)], "back": [(7, 12), (8, 12)]},
        "add": {},
    },
    # Within the safe Shirt box, two divided lower points and a projected side
    # back-edge provide a bounded coat-tail illusion without leg geometry.
    "PERIOD_TOP": {
        "clear": {
            "front": [(7, 12), (8, 12), (7, 13), (8, 13), (7, 14), (8, 14), (7, 15), (8, 15)],
            "back": [(7, 12), (8, 12), (7, 13), (8, 13), (7, 14), (8, 14), (7, 15), (8, 15)],
        },
        "add": {
            "front": [(0, 10), (15, 10), (0, 11), (15, 11), (0, 12), (1, 12), (14, 12), (15, 12), (0, 13), (1, 13), (14, 13), (15, 13), (0, 14), (1, 14), (14, 14), (15, 14), (0, 15), (1, 15), (2, 15), (13, 15), (14, 15), (15, 15)],
            "back": [(0, 10), (15, 10), (0, 11), (15, 11), (0, 12), (1, 12), (14, 12), (15, 12), (0, 13), (1, 13), (14, 13), (15, 13), (0, 14), (1, 14), (14, 14), (15, 14), (0, 15), (1, 15), (2, 15), (13, 15), (14, 15), (15, 15)],
            "right": [(2, 12), (3, 12), (4, 12), (14, 12), (2, 13), (3, 13), (4, 13), (14, 13), (15, 13), (2, 14), (3, 14), (4, 14), (14, 14), (15, 14), (2, 15), (3, 15), (4, 15), (15, 15)],
            "left": [(0, 13), (1, 12), (11, 12), (12, 12), (13, 12), (0, 14), (1, 14), (11, 13), (12, 13), (13, 13), (0, 15), (11, 14), (12, 14), (13, 14), (11, 15), (12, 15), (13, 15)],
        },
    },
    # Formalwear is narrower and terminates in a compact center point rather
    # than sharing the period coat's long split mass.
    "FORMAL_BLAZER": {
        "clear": {
            "front": [(3, 14), (4, 14), (11, 14), (12, 14), (3, 15), (4, 15), (5, 15), (10, 15), (11, 15), (12, 15)],
            "back": [(3, 15), (4, 15), (5, 15), (6, 15), (7, 15), (8, 15), (9, 15), (10, 15), (11, 15), (12, 15)],
            "right": [(5, 15), (6, 15), (7, 15), (8, 15), (9, 15), (10, 15), (11, 15), (12, 15), (13, 15), (14, 15)],
            "left": [(1, 15), (2, 15), (3, 15), (4, 15), (5, 15), (6, 15), (7, 15), (8, 15), (9, 15), (10, 15)],
        },
        "add": {},
    },
    # A cold field shell keeps broad guarded shoulders but cuts inward at the
    # lower corners. This separates its side/back silhouette from the cropped
    # open relay jacket while retaining full shoulder coverage.
    "MILITARY_TOP": {
        "clear": {
            "front": [(0, 10), (15, 10), (0, 11), (15, 11), (1, 12), (2, 12), (13, 12), (14, 12), (1, 13), (2, 13), (3, 13), (12, 13), (13, 13), (14, 13)],
            "back": [(0, 10), (15, 10), (0, 11), (15, 11), (1, 12), (2, 12), (13, 12), (14, 12), (1, 13), (2, 13), (3, 13), (12, 13), (13, 13), (14, 13)],
            "right": [(2, 9), (13, 9), (3, 10), (13, 10), (3, 11), (13, 11), (4, 12), (5, 12), (12, 12), (13, 12), (4, 13), (5, 13), (6, 13), (11, 13), (12, 13), (13, 13)],
            "left": [(2, 9), (13, 9), (2, 10), (12, 10), (2, 11), (12, 11), (2, 12), (3, 12), (10, 12), (11, 12), (2, 13), (3, 13), (4, 13), (9, 13), (10, 13), (11, 13)],
        },
        "add": {},
    },
    # The tunic falls asymmetrically: its wrapped side continues lower while
    # the opposite side rises into the belt, unlike any jacket hem.
    "ADVENTURER_TUNIC": {
        "clear": {
            "front": [(10, 14), (11, 14), (12, 14), (9, 15), (10, 15), (11, 15), (12, 15)],
            "back": [(3, 15), (4, 15), (11, 15), (12, 15)],
            "right": [(10, 15), (11, 15), (12, 15)],
            "left": [(3, 14), (3, 15), (4, 15)],
        },
        "add": {"front": [(2, 15)], "right": [(4, 15)], "left": [(11, 15)]},
    },
}


def apply_legendary_construction(mask_frames, default_frames, article_role: str) -> LegendaryConstructionFrames:
    masks = _copy(mask_frames); defaults = _copy(default_frames)
    template = CONSTRUCTION.get(article_role, {"clear": {}, "add": {}})
    pairs = _role_pairs(masks, defaults)
    cleared = added = 0
    for direction, coords in template["clear"].items():
        cleared += _clear(masks, defaults, direction, coords)
    for direction, coords in template["add"].items():
        added += _add(masks, defaults, direction, coords, pairs["dark"])
    return LegendaryConstructionFrames(masks, defaults, {
        "template": article_role if article_role in CONSTRUCTION else "native_article_shape",
        "clearedCells": cleared, "addedCells": added,
        "boundsPreserved": True, "anchorChanged": False,
    })


TEMPLATES = {
    "CROPPED_FIELD_JACKET": {
        "front": [(3, 3), (4, 3), (11, 3), (12, 3), (4, 8), (5, 8), (10, 8), (11, 8)],
        "right": [(4, 3), (5, 3), (5, 8), (6, 8)],
        "back": [(4, 3), (5, 3), (10, 3), (11, 3), (7, 6), (8, 6), (6, 7), (9, 7)],
        "left": [(10, 3), (11, 3), (9, 8), (10, 8)],
    },
    "PERIOD_TOP": {
        "front": [(3, 4), (3, 5), (3, 6), (12, 4), (12, 5), (12, 6), (4, 12), (11, 12)],
        "right": [(5, 4), (5, 5), (5, 6), (6, 12)],
        "back": [(5, 4), (6, 5), (7, 6), (8, 6), (9, 5), (10, 4)],
        "left": [(10, 4), (10, 5), (10, 6), (9, 12)],
    },
    "FORMAL_BLAZER": {
        "front": [(4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11)],
        "right": [(5, 4), (6, 5), (7, 6), (8, 7)],
        "back": [(4, 4), (5, 4), (10, 4), (11, 4), (7, 6), (8, 6)],
        "left": [(10, 4), (9, 5), (8, 6), (7, 7)],
    },
    "MILITARY_TOP": {
        "front": [(3, 3), (4, 3), (11, 3), (12, 3), (4, 6), (5, 6), (10, 6), (11, 6), (7, 9), (8, 9)],
        "right": [(4, 3), (5, 3), (5, 6), (6, 6)],
        "back": [(4, 3), (5, 3), (10, 3), (11, 3), (5, 5), (6, 6), (7, 7), (8, 7), (9, 6), (10, 5)],
        "left": [(10, 3), (11, 3), (9, 6), (10, 6)],
    },
    "ADVENTURER_TUNIC": {
        "front": [(4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9), (11, 10)],
        "right": [(5, 4), (6, 5), (7, 6)],
        "back": [(6, 4), (7, 5), (8, 5), (9, 4), (7, 10), (8, 10)],
        "left": [(10, 4), (9, 5), (8, 6)],
    },
}


def apply_legendary_signature(mask_frames, default_frames, article_role: str) -> LegendarySignatureFrames:
    masks = _copy(mask_frames); defaults = _copy(default_frames)
    template = TEMPLATES.get(article_role)
    if not template:
        return LegendarySignatureFrames(masks, defaults, {"template": "native_identity", "paintedCells": 0})
    pairs = _role_pairs(masks, defaults)
    painted = 0
    for direction, coords in template.items():
        painted += _paint(masks, defaults, direction, coords, pairs["accent"])
    return LegendarySignatureFrames(masks, defaults, {"template": article_role, "paintedCells": painted, "role": "existing_palette_accent"})
