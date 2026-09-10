#!/usr/bin/env python3
"""Render the fixed-seed Sailor technical-outline refinement proof."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.projector import DirectionalProjector
from generator.hybrid_v3.compiler.pixel_grammar_v4 import (
    PixelGrammarCompilerV4,
    V42_SAILOR_OUTLINE_PROFILE,
    V42_SAILOR_TECHNICAL_PROFILE,
    V42_SHAPE_LIBRARY_VERSION,
)
from generator.png_utils import blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from tools.generate_controlled_grammar_hd_adapter_repair import FARMER, HAIR, _farmer_composite

OUT = ROOT / "output/v4-sailor-outline-refinement"
DIRECTIONS = ("front", "right", "back", "left")
CASE = {
    "family": "SAILOR_TOP", "intent": "SAILOR_DECK_CLASSIC", "fit": "UNISEX_REGULAR",
    "seed": 420205, "palette": "SAILOR_NAVY", "material": "WOVEN_SHIRT",
}
BEFORE_VARIANTS = {
    "SAILOR_COLLAR_FRONT_TECHNICAL_V1", "SAILOR_COLLAR_SIDE_TECHNICAL_V1",
    "SAILOR_REAR_FLAP_TECHNICAL_V1", "SAILOR_COLLAR_BORDER_TECHNICAL_V1",
    "SAILOR_FRONT_OPENING_OR_INSERT_V1",
}
AFTER_VARIANTS = {
    "SAILOR_COLLAR_FRONT_TECHNICAL_V1", "SAILOR_COLLAR_SIDE_TECHNICAL_V1",
    "SAILOR_REAR_FLAP_TECHNICAL_V1", "SAILOR_COLLAR_FLAP_OUTLINE_REFINED_V1",
    "SAILOR_FRONT_BOW_TIE_OUTLINE_REFINED_V1",
}
EXPECTED_TOPOLOGY = {("ADD", "right", 12, 1), ("ADD", "left", 3, 1)}
BG = (232, 226, 217, 255); PANEL = (205, 197, 186, 255)
INK = (39, 37, 36, 255); ACC = (46, 116, 125, 255)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def cells(render, system, direction):
    return {tuple(cell) for cell in render.semantic_regions["systems"][system][direction]}


def alpha_cells(render, direction):
    return {(x, y) for y, row in enumerate(render.frames[direction]) for x, pixel in enumerate(row) if pixel[3]}


def topology_signature(render):
    return {(op["op"], op["direction"], op["cell"][0], op["cell"][1]) for op in render.topology_map}


def four_connected(group):
    if not group:
        return False
    unseen = set(group); todo = [unseen.pop()]
    while todo:
        x, y = todo.pop()
        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if neighbor in unseen:
                unseen.remove(neighbor); todo.append(neighbor)
    return not unseen


def has_two_by_two(group):
    return any({(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)} <= group for x, y in group)


def assert_route(label, render, variants, profile):
    if render.validation["status"] != "PASS":
        raise RuntimeError(f"{label} validation failed: {render.validation['issues']}")
    if render.metrics["executionProfile"] != profile or render.metrics["shapeLibraryVersion"] != V42_SHAPE_LIBRARY_VERSION:
        raise RuntimeError(f"{label} compiler routing mismatch: {render.metrics['routing']}")
    if set(render.metrics["shapeVariants"]) != variants or set(render.metrics["expectedShapeVariants"]) != variants:
        raise RuntimeError(f"{label} variant mismatch: {render.metrics['shapeVariants']}")
    if topology_signature(render) != EXPECTED_TOPOLOGY:
        raise RuntimeError(f"{label} topology mismatch: {render.topology_map}")


def run_outline_qc(before, after):
    same_alpha = {d: alpha_cells(before, d) == alpha_cells(after, d) for d in DIRECTIONS}
    same_collar = {d: cells(before, "collar", d) == cells(after, "collar", d) for d in DIRECTIONS}
    same_rear = {d: cells(before, "rear_panel", d) == cells(after, "rear_panel", d) for d in DIRECTIONS}
    same_border_footprint = {d: cells(before, "collar_border", d) == cells(after, "collar_border", d) for d in DIRECTIONS}
    before_insert = cells(before, "inner_layer", "front")
    tie = cells(after, "tie", "front")
    border = {d: cells(after, "collar_border", d) for d in DIRECTIONS}
    parent = {d: cells(after, "collar", d) | cells(after, "rear_panel", d) for d in DIRECTIONS}
    supported = {}
    for direction in DIRECTIONS:
        supported[direction] = all(
            any((x + dx, y + dy) in parent[direction] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0))
            for x, y in border[direction]
        )
    changed = {}
    scoped_changes = {}
    for direction in DIRECTIONS:
        changed[direction] = {
            (x, y) for y in range(16) for x in range(16)
            if before.frames[direction][y][x] != after.frames[direction][y][x]
        }
        permitted = border[direction] | (tie if direction == "front" else set())
        scoped_changes[direction] = changed[direction] <= permitted
    owner_entries = [
        item for item in after.semantic_regions["ownership"]["cells"]["front"]
        if tuple(item["cell"]) in tie
    ]
    rejected = after.semantic_regions["ownership"]["rejectedMutations"]
    rejected_cells_survived = all(
        after.pre_polish_frames[item["direction"]][item["cell"][1]][item["cell"][0]]
        == after.post_polish_frames[item["direction"]][item["cell"][1]][item["cell"][0]]
        for item in rejected
    )
    checks = {
        "sameCanonical": digest(before.canonical) == digest(after.canonical),
        "sameProjections": digest(before.projections) == digest(after.projections),
        "sameBodySilhouetteAlpha": all(same_alpha.values()),
        "sameCollarFillFootprint": all(same_collar.values()),
        "sameRearFlapFillFootprint": all(same_rear.values()),
        "sameCollarBorderFootprint": all(same_border_footprint.values()),
        "bowReusesExistingInsertFootprint": tie == before_insert and len(tie) == 4,
        "bowIsOneConnectedCluster": four_connected(tie),
        "bowDoesNotMergeWithCollarBorder": not any(abs(x - bx) + abs(y - by) == 1 for x, y in tie for bx, by in border["front"]),
        "outlineSupportedByCollarOrFlap": all(supported.values()),
        "outlineNeverFormsTwoPixelBlock": not any(has_two_by_two(border[d]) for d in DIRECTIONS),
        "pixelChangesRestrictedToBorderAndBow": all(scoped_changes.values()),
        "noGlobalBodyDarkening": all(scoped_changes.values()),
        "bowOwnershipRecorded": len(owner_entries) == 4 and all(item["component_owner"] == "sailor_bow_tie" and item["system"] == "tie" for item in owner_entries),
        "outlineAndBowProtectedFromLegacyPolish": all(
            item["protection_level"] == "STRUCTURAL" and "LEGACY_POLISH" not in item["allowed_later_mutations"]
            for direction in DIRECTIONS
            for item in after.semantic_regions["ownership"]["cells"][direction]
            if item["system"] in {"collar_border", "tie"}
        ),
        "noOwnershipConflicts": not after.semantic_regions["ownership"]["conflicts"],
        "legacyPolishRejectionsRecordedAndPreserved": bool(rejected) and rejected_cells_survived
        and after.metrics["ownershipRejectedMutationCount"] == len(rejected),
    }
    details = {
        "sameAlphaByDirection": same_alpha,
        "sameCollarByDirection": same_collar,
        "sameRearFlapByDirection": same_rear,
        "sameBorderFootprintByDirection": same_border_footprint,
        "outlineSupportedByDirection": supported,
        "changedFinalLogicalCells": {d: [list(c) for c in sorted(changed[d])] for d in DIRECTIONS},
        "tieCells": [list(c) for c in sorted(tie)],
        "outlineCells": {d: [list(c) for c in sorted(border[d])] for d in DIRECTIONS},
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "details": details}


def tile(canvas, image, x, y, border):
    draw_rect(canvas, x - 2, y - 2, len(image[0]) + 4, len(image) + 4, border)
    draw_rect(canvas, x - 1, y - 1, len(image[0]) + 2, len(image) + 2, PANEL)
    blit(canvas, image, x, y)


def comparison_sheet(title, before, after, *, farmer=False):
    scale = 2 if farmer else 8
    sprite_w = (64 if farmer else 16) * scale
    sprite_h = (128 if farmer else 16) * scale
    label = 184; gap = 18; top = 35; row_h = sprite_h + 35
    canvas = blank_image(label + 4 * (sprite_w + gap), top + 2 * row_h + 8, BG)
    draw_text(canvas, title, 8, 7, color=INK)
    rows = (("CURRENT TECHNICAL", before), ("OUTLINE REFINEMENT", after))
    for row, (name, frames) in enumerate(rows):
        y = top + row * row_h
        draw_text(canvas, name, 8, y + sprite_h // 2, color=INK if row == 0 else ACC)
        for col, direction in enumerate(DIRECTIONS):
            x = label + col * (sprite_w + gap)
            draw_text(canvas, direction.upper(), x, y, color=ACC)
            tile(canvas, nearest_scale(frames[direction], scale), x, y + 16, INK if row == 0 else ACC)
    return canvas


def main():
    if not FARMER.exists() or not HAIR.exists():
        raise FileNotFoundError("unpacked Farmer fixtures are required")
    OUT.mkdir(parents=True, exist_ok=True)
    canonical = CanonicalGarmentBuilder().build(
        family=CASE["family"], design_intent=CASE["intent"], fit_profile=CASE["fit"],
        root_seed=CASE["seed"], rarity_budget="V4_2_SAILOR_OUTLINE_REFINEMENT", material=CASE["material"],
    )
    projections = DirectionalProjector().project(canonical)
    before = PixelGrammarCompilerV4(execution_profile=V42_SAILOR_TECHNICAL_PROFILE).compile(
        canonical, projections, palette_story=CASE["palette"], required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,
        expected_shape_variants=BEFORE_VARIANTS,
    )
    after = PixelGrammarCompilerV4(execution_profile=V42_SAILOR_OUTLINE_PROFILE).compile(
        canonical, projections, palette_story=CASE["palette"], required_shape_library_version=V42_SHAPE_LIBRARY_VERSION,
        expected_shape_variants=AFTER_VARIANTS,
    )
    assert_route("before", before, BEFORE_VARIANTS, V42_SAILOR_TECHNICAL_PROFILE)
    assert_route("after", after, AFTER_VARIANTS, V42_SAILOR_OUTLINE_PROFILE)
    qc = run_outline_qc(before, after)
    after_validation = {**after.validation, "outlineRefinementQC": qc, "humanVisualQC": "PENDING"}
    if qc["status"] != "PASS":
        after_validation["status"] = "FAIL"
        after_validation["automatedQC"] = "FAIL"
    comparison = {
        "case": CASE, "sameSeed": True, "sameFit": True, "sameMaterial": True, "samePaletteStory": True,
        "onlyOutlineAndBowGrammarDiffers": True, "automatedQC": after_validation["automatedQC"], "humanVisualQC": "PENDING",
    }
    body = read_rgba_png(FARMER)["pixels"]; hair = read_rgba_png(HAIR)["pixels"]
    before_farmer = {d: _farmer_composite(body, hair, before.frames[d], d) for d in DIRECTIONS}
    after_farmer = {d: _farmer_composite(body, hair, after.frames[d], d) for d in DIRECTIONS}

    dump(OUT / "updated-shape-outline-variant-ids.json", {
        "shapeLibraryVersion": V42_SHAPE_LIBRARY_VERSION,
        "before": sorted(BEFORE_VARIANTS), "after": sorted(AFTER_VARIANTS),
        "addedForRefinement": sorted(AFTER_VARIANTS - BEFORE_VARIANTS),
        "replacedFromTechnical": sorted(BEFORE_VARIANTS - AFTER_VARIANTS),
    })
    dump(OUT / "ownership-ledger.json", after.semantic_regions["ownership"])
    dump(OUT / "metrics.json", {**after.metrics, "outlineRefinement": comparison, "outlineRefinementQC": qc})
    dump(OUT / "validation.json", after_validation)
    write_rgba_png(OUT / "final-logical-atlas.png", after.texture)
    write_rgba_png(OUT / "SAILOR_OUTLINE_BEFORE_AFTER_FARMER.png", comparison_sheet(
        "SAILOR OUTLINE REFINEMENT | SAME FIXED SEED 420205 | HUMAN QC PENDING", before_farmer, after_farmer, farmer=True,
    ))
    write_rgba_png(OUT / "SAILOR_OUTLINE_BEFORE_AFTER_ISOLATED_8X.png", comparison_sheet(
        "SAILOR OUTLINE REFINEMENT | CURRENT TECHNICAL VS CONTROLLED EDGE + BOW", before.frames, after.frames,
    ))
    print(json.dumps({"automatedQC": after_validation["automatedQC"], "humanVisualQC": "PENDING", "checks": qc["checks"]}, indent=2))
    if after_validation["automatedQC"] != "PASS":
        raise RuntimeError("outline refinement QC failed; see validation.json")


if __name__ == "__main__":
    main()
