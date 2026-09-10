#!/usr/bin/env python3
"""Evidence-only audit of the Coastal Knit Polo micro-fix.

This tool does not write garment art, compiler data, packs, or renderer files.
It reconstructs the archived pre-fix branch and current post-fix branch in
memory, then emits only audit JSON and a diagnostic image.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generator.controlled_test.hd_adapter import _remove_closed_opening_from_hd_regions
from generator.controlled_test.reference_guided import _copy_frames, _reset_to_proven_hd_planes, _resolve
from generator.hybrid_v3.builder import CanonicalGarmentBuilder
from generator.hybrid_v3.compiler.carrier_registry import CarrierRegistry
from generator.hybrid_v3.compiler.component_compilers import compile_components
from generator.hybrid_v3.compiler.semantic_regions import SemanticRegionLedger
from generator.hybrid_v3.projector import DirectionalProjector
from generator.png_utils import blank_image, blit, draw_rect, draw_text, nearest_scale, read_rgba_png, write_rgba_png
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames, soften_shared_rear_neck
from generator.renderers.fashionsense.upper_v5b import _stack

BEFORE_ATLAS = ROOT / "output/hybrid-v3-phase2/polo-microfix/before-shirt.png"
AFTER_ATLAS = ROOT / "output/hybrid-v3-phase2/polo-microfix/after-shirt.png"
BEFORE_FARMER = ROOT / "output/hybrid-v3-phase2/polo-microfix/farmer-before.png"
AFTER_FARMER = ROOT / "output/hybrid-v3-phase2/polo-microfix/farmer-after.png"
QC_SHEET = ROOT / "output/comparisons/HYBRID_V3_PHASE2_COASTAL_POLO_MICROFIX_QC.png"
OUT_JSON = ROOT / "output/hybrid-v3-phase2/polo-microfix/failure-audit-data.json"
OUT_IMAGE = ROOT / "output/comparisons/COASTAL_POLO_STAGE_DIFF_AUDIT.png"
DIRECTIONS = ("front", "right", "back", "left")
OFFSETS = {"front": 0, "right": 16, "left": 32, "back": 48}
STAGES = ("carrier_base", "component_compilation", "polish_upper_frames", "soften_shared_rear_neck", "material_palette_adapter", "final_logical_atlas")
BG=(229,225,218,255); PANEL=(195,190,181,255); INK=(35,34,33,255); ACC=(38,116,126,255); HOT=(255,0,190,255); DIM=(75,72,70,255)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clone(frames):
    return {direction: [list(row) for row in frames[direction]] for direction in DIRECTIONS}


def atlas_frames(path: Path):
    pixels = read_rgba_png(path)["pixels"]
    return {direction: [list(row) for row in pixels[offset:offset+16]] for direction, offset in OFFSETS.items()}


def pipeline(*, cleanup: bool):
    canonical = CanonicalGarmentBuilder().build(
        family="POLO_SHIRT", design_intent="POLO_CLASSIC", fit_profile="MASC_TAILORED",
        root_seed=320203, rarity_budget="PHASE2_NEUTRAL_DEFAULT",
    )
    projections = DirectionalProjector().project(canonical)
    compiler_model = copy.deepcopy(canonical)
    if not cleanup:
        # The pre-fix handler ignored medium-vs-small width in side/back. The
        # current non-medium branch is the exact former implementation.
        next(item for item in compiler_model["components"] if item["instanceId"] == "collar")["parameters"]["width"] = "small"
    capability, _, raw = CarrierRegistry().select(compiler_model)
    base = raw
    frames = _copy_frames(raw.frames); defaults = _copy_frames(raw.default_frames)
    _reset_to_proven_hd_planes(base, frames, defaults)
    _remove_closed_opening_from_hd_regions(base, frames, defaults)
    snapshots = {"carrier_base": clone(frames)}
    ledger = SemanticRegionLedger()
    compile_components(compiler_model, projections, base, frames, defaults, ledger)
    snapshots["component_compilation"] = clone(frames)
    polished = polish_upper_frames(base, frames, defaults, article_family="POLO_SHIRT")
    snapshots["polish_upper_frames"] = clone(polished.frames)
    protected = frozenset(cell for system in ledger.systems.values() for cell in system["back"])
    softened = soften_shared_rear_neck(base, polished, protected_cells=protected)
    snapshots["soften_shared_rear_neck"] = clone(softened.frames)
    resolved, roles, _, _ = _resolve({"material":"KNIT", "paletteStory":"COASTAL_MIST"}, softened, ledger.fabrics)
    snapshots["material_palette_adapter"] = clone(resolved)
    snapshots["final_logical_atlas"] = clone(resolved)
    return {"canonical": canonical, "projections": projections, "capability": capability, "snapshots": snapshots, "roles": roles, "regions": ledger.as_json(), "texture": _stack(resolved)}


def pixel_diffs(before, after, direction):
    return [(x,y) for y in range(16) for x in range(16) if before[direction][y][x] != after[direction][y][x]]


def hex_color(pixel):
    return "#%02X%02X%02X%02X" % pixel


def overlay(frame, changed):
    image = [[(48,48,46,255) if pixel[3] else (235,232,225,255) for pixel in row] for row in frame]
    for x,y in changed:
        image[y][x] = HOT
    return image


def tile(canvas, image, x, y, border):
    draw_rect(canvas,x-2,y-2,len(image[0])+4,len(image)+4,border)
    draw_rect(canvas,x-1,y-1,len(image[0])+2,len(image)+2,PANEL)
    blit(canvas,image,x,y)


def stage_sheet(before, after, stage_diffs):
    row_h=150; canvas=blank_image(565,len(STAGES)*2*row_h+34,BG)
    draw_text(canvas,"COASTAL POLO FAILURE AUDIT | BEFORE -> CHANGED CELLS -> AFTER",8,8,color=INK)
    for stage_index, stage in enumerate(STAGES):
        for direction_index, direction in enumerate(("right","back")):
            row=stage_index*2+direction_index; y=34+row*row_h
            changed=[tuple(cell) for cell in stage_diffs[stage][direction]["coordinates"]]
            draw_text(canvas,f"{stage.upper()} | {direction.upper()} | {len(changed)} CHANGED",8,y+4,color=INK)
            draw_text(canvas,"BEFORE",8,y+18,color=DIM); draw_text(canvas,"DIFF",150,y+18,color=HOT); draw_text(canvas,"AFTER",292,y+18,color=ACC)
            tile(canvas,nearest_scale(before["snapshots"][stage][direction],8),8,y+34,DIM)
            tile(canvas,nearest_scale(overlay(before["snapshots"][stage][direction],changed),8),150,y+34,HOT)
            tile(canvas,nearest_scale(after["snapshots"][stage][direction],8),292,y+34,ACC)
    return canvas


def main():
    before = pipeline(cleanup=False); after = pipeline(cleanup=True)
    archived_before = atlas_frames(BEFORE_ATLAS); archived_after = atlas_frames(AFTER_ATLAS)
    reconstruction = {
        "beforeMatchesArchived": before["snapshots"]["final_logical_atlas"] == archived_before,
        "afterMatchesArchived": after["snapshots"]["final_logical_atlas"] == archived_after,
    }
    final_diffs = {}
    for direction in DIRECTIONS:
        records=[]
        for x,y in pixel_diffs(archived_before,archived_after,direction):
            records.append({
                "coordinate":[x,y],
                "oldRole":before["roles"][direction][y][x], "oldColor":hex_color(archived_before[direction][y][x]),
                "newRole":after["roles"][direction][y][x], "newColor":hex_color(archived_after[direction][y][x]),
            })
        final_diffs[direction]={"count":len(records),"pixels":records}
    stage_diffs={}
    for stage in STAGES:
        stage_diffs[stage]={}
        for direction in ("right","back"):
            cells=pixel_diffs(before["snapshots"][stage],after["snapshots"][stage],direction)
            stage_diffs[stage][direction]={"count":len(cells),"coordinates":[list(cell) for cell in cells]}
    old_collar={direction:before["regions"]["components"].get("collar",{}).get(direction,[]) for direction in DIRECTIONS}
    new_collar={direction:after["regions"]["components"].get("collar",{}).get(direction,[]) for direction in DIRECTIONS}
    # Interior dark cells in the user's right-side QC region. These are the
    # cells below a luma threshold, excluding transparent/background pixels.
    dark=[]
    for y in range(1,8):
        for x in range(5,11):
            pixel=archived_before["right"][y][x]
            if pixel[3] and sum(pixel[:3])/3 < 100:
                owners=[]
                for system, views in before["regions"]["systems"].items():
                    if [x,y] in views["right"]: owners.append(system)
                dark.append({"coordinate":[x,y],"color":hex_color(pixel),"role":before["roles"]["right"][y][x],"semanticOwners":owners or ["inherited_HD_plane"]})
    sources={str(path.relative_to(ROOT)):{"sha256":digest(path),"bytes":path.stat().st_size} for path in (BEFORE_ATLAS,AFTER_ATLAS,BEFORE_FARMER,AFTER_FARMER,QC_SHEET)}
    result={
        "status":"AUDIT_COMPLETE_NO_ART_CHANGES", "reconstruction":reconstruction,
        "sources":sources, "finalPixelDiff":final_diffs, "stageDiff":stage_diffs,
        "collarCells":{"old":old_collar,"new":new_collar},
        "rightTorsoDarkRegion":dark,
        "qcConstruction":{
            "beforeAtlas":str(BEFORE_ATLAS.relative_to(ROOT)),"afterAtlas":str(AFTER_ATLAS.relative_to(ROOT)),
            "beforeFarmerOutput":str(BEFORE_FARMER.relative_to(ROOT)),"afterFarmerOutput":str(AFTER_FARMER.relative_to(ROOT)),
            "sameAtlasFile":BEFORE_ATLAS.resolve()==AFTER_ATLAS.resolve(),"sameAtlasHash":digest(BEFORE_ATLAS)==digest(AFTER_ATLAS),
            "sameFarmerFile":BEFORE_FARMER.resolve()==AFTER_FARMER.resolve(),"sameFarmerHash":digest(BEFORE_FARMER)==digest(AFTER_FARMER),
        },
    }
    OUT_JSON.parent.mkdir(parents=True,exist_ok=True); OUT_JSON.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    write_rgba_png(OUT_IMAGE,stage_sheet(before,after,stage_diffs))
    print(json.dumps({"status":result["status"],"reconstruction":reconstruction,"finalCounts":{d:v["count"] for d,v in final_diffs.items()},"stageCounts":stage_diffs,"sources":sources},indent=2))

if __name__ == "__main__": main()
