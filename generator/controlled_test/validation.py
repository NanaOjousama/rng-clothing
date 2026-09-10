"""Static and collection validation for the controlled grammar/palette proof."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from generator.controlled_test.engine import validate_controlled_test_recipes
from generator.renderers.fashionsense.reference_grammar import DIRECTIONS, ControlledGarmentRender


ROOT = Path(__file__).resolve().parents[2]
HD_CONTRACT = ROOT / "generator" / "data" / "fashionsense" / "hd_garment_grammar_v2.json"
AXES = ("silhouette", "collar", "opening", "layering", "hem", "sleeve", "panels", "side", "back", "colorTopology")


def _coverage_envelope(direction: str) -> list[str]:
    data = json.loads(HD_CONTRACT.read_text(encoding="utf-8"))["bodyCoverageEnvelope"]
    if direction == "left":
        return [row[::-1] for row in data["right"]]
    return data[direction]


def _opaque(frame):
    return {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}


def _iou(left, right) -> float:
    union = left | right
    return 0.0 if not union else len(left & right) / len(union)


def validate_render(render: ControlledGarmentRender) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    story_roles = set(render.recipe["paletteStory"]["roles"])
    check("exact direction set", set(render.frames) == set(DIRECTIONS), sorted(render.frames))
    check("logical frame dimensions", all(len(frame) == 16 and all(len(row) == 16 for row in frame) for frame in render.frames.values()), "16x16")
    check("binary alpha", all(pixel[3] in {0, 255} for frame in render.frames.values() for row in frame for pixel in row), "0 or 255")
    check("active roles belong to story", set(render.active_roles) <= story_roles, sorted(render.active_roles))
    check("role budget remains restrained", 4 <= len(render.active_roles) <= 8, len(render.active_roles))
    check("native sleeve ramp", len(render.sleeve_colors) == 3 and len(set(render.sleeve_colors)) == 3, render.sleeve_colors)
    check("material behavior applied", render.material_behavior_id == render.recipe["materialId"], render.material_behavior_id)
    missing = {}
    for direction in DIRECTIONS:
        absent = []
        for y, row in enumerate(_coverage_envelope(direction)):
            for x, marker in enumerate(row):
                if marker == "#" and render.role_frames[direction][y][x] is None:
                    absent.append([x, y])
        missing[direction] = absent
    check("frozen body coverage envelope", not any(missing.values()), missing)
    front_systems = {name for name, views in render.signal_cells.items() if views["front"]}
    side_systems = {name for name, views in render.signal_cells.items() if views["right"] or views["left"]}
    back_systems = {name for name, views in render.signal_cells.items() if views["back"]}
    check("front construction signals", {"silhouette", "collar", "hem"} <= front_systems, sorted(front_systems))
    check("side reconstructed", len(side_systems - {"silhouette", "highlight"}) >= 2, sorted(side_systems))
    check("back reconstructed", len(back_systems - {"silhouette", "highlight"}) >= 2, sorted(back_systems))
    opaque = {direction: len(_opaque(frame)) for direction, frame in render.frames.items()}
    check("nontrivial direct-pixel geometry", all(90 <= count <= 245 for count in opaque.values()), opaque)
    failed = [item["name"] for item in checks if not item["passed"]]
    return {"id": render.recipe["id"], "grammarId": render.recipe["grammarId"], "status": "PASS" if not failed else "FAIL", "failed": failed, "checks": checks}


def pairwise_diversity(renders: list[ControlledGarmentRender]) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for left, right in combinations(renders, 2):
        left_axes, right_axes = left.recipe["axes"], right.recipe["axes"]
        shared = [axis for axis in AXES if left_axes[axis] == right_axes[axis]]
        critical = all(axis in shared for axis in ("silhouette", "opening", "layering"))
        front_iou = _iou(_opaque(left.frames["front"]), _opaque(right.frames["front"]))
        side_iou = _iou(_opaque(left.frames["right"]), _opaque(right.frames["right"]))
        failed = len(shared) >= 7 or critical
        pairs.append({
            "left": left.recipe["grammarId"],
            "right": right.recipe["grammarId"],
            "sharedDimensions": shared,
            "sharedCount": len(shared),
            "criticalTripleOverlap": critical,
            "frontMaskIoU": round(front_iou, 4),
            "sideMaskIoU": round(side_iou, 4),
            "status": "FAIL" if failed else "PASS",
        })
    failed_pairs = [pair for pair in pairs if pair["status"] == "FAIL"]
    return {
        "status": "PASS" if not failed_pairs else "FAIL",
        "pairCount": len(pairs),
        "failedPairs": failed_pairs,
        "maximumSharedDimensions": max((pair["sharedCount"] for pair in pairs), default=0),
        "maximumFrontMaskIoU": max((pair["frontMaskIoU"] for pair in pairs), default=0.0),
        "pairs": pairs,
        "note": "Semantic and mask checks are guardrails; worn Farmer human review remains authoritative.",
    }


def validate_collection(recipes: list[dict[str, Any]], renders: list[ControlledGarmentRender]) -> dict[str, Any]:
    recipe_errors = list(validate_controlled_test_recipes(recipes))
    per_render = [validate_render(render) for render in renders]
    diversity = pairwise_diversity(renders)
    failed_renders = [item["id"] for item in per_render if item["status"] == "FAIL"]
    passed = not recipe_errors and not failed_renders and diversity["status"] == "PASS"
    return {
        "status": "PASS_STATIC_RUNTIME_NOT_TESTED" if passed else "FAIL_STATIC",
        "recipeErrors": recipe_errors,
        "failedRenders": failed_renders,
        "perSpecimen": per_render,
        "pairwiseDiversity": diversity,
        "runtimeStatus": "NOT_TESTED",
        "promotion": "EXPERIMENTAL",
    }
