"""Semantic construction adapter into the frozen V5/HD art backend.

This module is deliberately not a rasterizer.  It selects proven V5 carriers,
restores their permanent HD planes, adds garment-specific construction masks,
then delegates polish and semantic material coloring to existing stages.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from generator.controlled_test.reference_guided import (
    _bounds, _clear, _connected_components, _copy_frames, _hem_band, _paint,
    _reset_to_proven_hd_planes, _resolve, _signals,
)
from generator.controlled_test.hd_adapter import _remove_closed_opening_from_hd_regions
from generator.png_utils import RGBA
from generator.renderers.fashionsense.art_polish_v5e import polish_upper_frames, soften_shared_rear_neck
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER
from generator.renderers.fashionsense.upper_v5b import _coverage_missing, _stack, render_fs_v5b
from generator.renderers.fashionsense.upper_v5d import render_fs_v5d
from generator.v5b.engine import generate_v5b_benchmark
from generator.v5d.engine import generate_v5d_batch


@dataclass(frozen=True)
class AutonomousRecoveryRender:
    design: dict[str, Any]
    backend: str
    backend_recipe: dict[str, Any]
    stage_trace: tuple[str, ...]
    frames: dict[str, list[list[RGBA]]]
    role_frames: dict[str, list[list[str | None]]]
    texture: list[list[RGBA]]
    sleeve_colors: tuple[tuple[int, int, int], ...]
    construction_signals: dict[str, dict[str, frozenset[tuple[int, int]]]]
    coverage_missing: dict[str, tuple[tuple[int, int], ...]]
    material_evidence: dict[str, Any]
    polish_metrics: dict[str, Any]
    construction_metrics: dict[str, Any]


def _carrier(concept: dict[str, Any]):
    family = concept["family"]; v5b = generate_v5b_benchmark()["recipes"]
    v5d = generate_v5d_batch()["recipes"]
    if family in {"FITTED_TEE", "OPEN_CASUAL_SHIRT", "SWEATER_VEST", "CREWNECK_SWEATSHIRT", "SAILOR_TOP", "POLO_KNIT"}:
        index = {"FITTED_TEE":0, "OPEN_CASUAL_SHIRT":1, "SWEATER_VEST":4, "CREWNECK_SWEATSHIRT":2, "SAILOR_TOP":10, "POLO_KNIT":1}[family]
        recipe = copy.deepcopy(v5b[index]); recipe["id"] = f"autonomous-{family.lower()}"
        recipe["baseArticleRecipe"]["designRecipe"]["itemName"] = concept["name"]
        raw = render_fs_v5b(recipe)
        return recipe, raw, raw, f"V5B_{recipe['articleType']}_{recipe['constructionVariant']}_HD"
    index = {"TEXTURED_KNIT":2, "OPEN_CARDIGAN":4, "WORK_JACKET":1, "FORMAL_WAISTCOAT":5, "TRACK_JACKET":7, "FITTED_BLAZER":8}[family]
    recipe = copy.deepcopy(v5d[index])
    recipe["baseUpperRecipe"]["baseArticleRecipe"]["designRecipe"]["itemName"] = concept["name"]
    raw = render_fs_v5d(recipe)
    return recipe, raw, raw.base, f"V5D_{recipe['articleRole']}_{recipe['articleSubtype']}_HD"


def _row(base, frames, defaults, signals, fabrics, system, direction, y, x0, x1, shade, fabric="PrimaryFabric"):
    for x in range(x0, x1 + 1): _paint(base, frames, defaults, signals, fabrics, system, direction, x, y, shade, fabric)


def _rear_band(base, frames, defaults, signals, fabrics, *, fabric="Trim", deep=False):
    for x in range(5, 11):
        y = 1 if 6 <= x <= 9 else 2
        _paint(base, frames, defaults, signals, fabrics, "collar", "back", x, y, "STRUCTURAL_EDGE" if deep else "BASE", fabric)


def _component_cells(frame) -> list[set[tuple[int, int]]]:
    remaining = {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}
    components: list[set[tuple[int, int]]] = []
    while remaining:
        root = next(iter(remaining)); remaining.remove(root); component = {root}; queue = [root]
        while queue:
            x, y = queue.pop()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor); component.add(neighbor); queue.append(neighbor)
        components.append(component)
    return sorted(components, key=len, reverse=True)


def _clean_vest_side_top_overhang(
    frames, defaults, signals, fabrics, *, remove_detached_islands: bool = True
) -> dict[str, dict[str, tuple[tuple[int, int], ...]]]:
    """Remove unsupported carrier spill, then detached side alpha islands.

    The legacy V5B vest carrier has three opaque cells at the outer end of
    each side frame's top row with no supporting garment cell below.  Once the
    named surface is reset, semantic coloring exposes them as a horizontal
    fabric line.  Supported neck cells remain untouched.
    """
    removed: dict[str, dict[str, tuple[tuple[int, int], ...]]] = {}
    for direction in ("right", "left"):
        row_zero = tuple(
            (x, 0)
            for x, pixel in enumerate(frames[direction][0])
            if pixel[3] and not frames[direction][1][x][3]
        )
        for x, y in row_zero:
            _clear(frames, defaults, signals, fabrics, direction, x, y)
        detached: tuple[tuple[int, int], ...] = ()
        if remove_detached_islands:
            components = _component_cells(frames[direction])
            detached = tuple(sorted(cell for component in components[1:] for cell in component))
            for x, y in detached:
                _clear(frames, defaults, signals, fabrics, direction, x, y)
        removed[direction] = {
            "rowZero": tuple(sorted(row_zero)),
            "detached": detached,
            "all": tuple(sorted((*row_zero, *detached))),
        }
    return removed


def _construct(concept, base, frames, defaults, signals, fabrics) -> dict[str, Any]:
    family = concept["family"]; axes = concept["structuralAxes"]
    before = {d:{(x,y) for y,row in enumerate(frames[d]) for x,p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    # Closed carriers must not inherit the permanent button-shirt placket.
    if axes["openingTopology"] == "closed": _remove_closed_opening_from_hd_regions(base, frames, defaults)

    if family == "FITTED_TEE":
        for x,y,s in ((6,1,"BASE"),(7,1,"SHADOW"),(8,1,"SHADOW"),(9,1,"STRUCTURAL_EDGE"),(5,2,"LIGHT"),(10,2,"SHADOW")):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,s,"Trim")
        _rear_band(base,frames,defaults,signals,fabrics)
        if axes["pocketPanelArchitecture"] == "single_side_chest_plane":
            for x,y,s in ((4,6,"STRUCTURAL_EDGE"),(5,6,"LIGHT"),(4,7,"BASE"),(5,7,"SHADOW")):
                _paint(base,frames,defaults,signals,fabrics,"pockets","front",x,y,s,"SecondaryFabric")
        else:
            _row(base,frames,defaults,signals,fabrics,"panels","back",3,4,11,"SHADOW")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="PrimaryFabric")

    elif family == "TEXTURED_KNIT":
        for d in DIRECTION_ORDER:
            for x in range(5,11): _paint(base,frames,defaults,signals,fabrics,"collar",d,x,1,"BASE" if x<9 else "SHADOW","Trim")
        if axes["pocketPanelArchitecture"] == "paired_vertical_ribs":
            for d, cols in (("front",(5,10)),("back",(6,9))):
                for x in cols:
                    for y in range(4,13): _paint(base,frames,defaults,signals,fabrics,"panels",d,x,y,"LIGHT" if x<8 else "SHADOW")
        else:
            for d in ("front","back"):
                _row(base,frames,defaults,signals,fabrics,"panels",d,6,3,12,"LIGHT","SecondaryFabric")
                _row(base,frames,defaults,signals,fabrics,"panels",d,7,3,12,"BASE","SecondaryFabric")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="Trim",gathered=True)

    elif family == "SWEATER_VEST":
        for x,y in ((7,1),(8,1),(6,2),(7,2),(8,2),(9,2),(7,3),(8,3)):
            _paint(base,frames,defaults,signals,fabrics,"layering","front",x,y,"LIGHT" if y<3 else "SHADOW","SecondaryFabric")
        for x,y in ((5,1),(10,1),(6,2),(9,2),(6,3),(9,3),(7,4),(8,4)):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,"STRUCTURAL_EDGE" if y<3 else "DEEP_CREASE","Trim")
        for d in DIRECTION_ORDER:
            for y in range(2,9):
                b=_bounds(frames[d],y)
                if b:
                    for x in b: _paint(base,frames,defaults,signals,fabrics,"sleeves",d,x,y,"STRUCTURAL_EDGE","Trim")
        _rear_band(base,frames,defaults,signals,fabrics)
        if axes["pocketPanelArchitecture"] == "single_broad_knit_band":
            _row(base,frames,defaults,signals,fabrics,"panels","front",7,3,12,"BASE","SecondaryFabric")
            _row(base,frames,defaults,signals,fabrics,"panels","back",7,4,11,"SHADOW","SecondaryFabric")
        else:
            for x in (5,10):
                for y in range(6,13): _paint(base,frames,defaults,signals,fabrics,"panels","front",x,y,"LIGHT" if x<8 else "SHADOW")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="Trim",gathered=True)

    elif family == "OPEN_CARDIGAN":
        # Broad inner shirt; soft outer leaves taper instead of becoming a zip.
        for y in range(2,14):
            width = 4 if y < 6 else 3
            for x in range(8-width//2, 8+width//2+1):
                _paint(base,frames,defaults,signals,fabrics,"layering","front",x,y,"LIGHT" if x<=7 and y<7 else "BASE" if y<11 else "SHADOW","SecondaryFabric")
            for x in (5 if y<7 else 4, 10 if y<7 else 11):
                _paint(base,frames,defaults,signals,fabrics,"opening","front",x,y,"LIGHT" if x<8 else "SHADOW","Trim")
        for x,y,s in ((5,1,"LIGHT"),(6,2,"BASE"),(10,1,"SHADOW"),(9,2,"SHADOW")):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,s,"Trim")
        for d,x in (("right",10),("left",5)):
            for y in range(2,14): _paint(base,frames,defaults,signals,fabrics,"opening",d,x,y,"SHADOW" if d=="right" else "LIGHT","Trim")
        if axes["pocketPanelArchitecture"] == "integrated_patch_pockets":
            for x0,x1 in ((3,6),(9,12)):
                _row(base,frames,defaults,signals,fabrics,"pockets","front",9,x0,x1,"STRUCTURAL_EDGE")
                _row(base,frames,defaults,signals,fabrics,"pockets","front",10,x0,x1,"SHADOW")
        _rear_band(base,frames,defaults,signals,fabrics)
        _hem_band(base,frames,defaults,signals,fabrics,fabric="Trim",gathered=True)

    elif family == "OPEN_CASUAL_SHIRT":
        for x,y,s in ((4,1,"STRUCTURAL_EDGE"),(5,1,"LIGHT"),(5,2,"BASE"),(6,2,"SHADOW"),(11,1,"DEEP_CREASE"),(10,1,"BASE"),(10,2,"SHADOW"),(9,2,"DEEP_CREASE")):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,s,"PrimaryFabric")
        for y in range(2,13):
            for x in range(6,10): _paint(base,frames,defaults,signals,fabrics,"layering","front",x,y,"LIGHT" if x==6 and y<7 else "BASE" if y<11 else "SHADOW","SecondaryFabric")
            for x in (5,10): _paint(base,frames,defaults,signals,fabrics,"opening","front",x,y,"SHADOW","Trim")
        pocket_left = axes["pocketPanelArchitecture"] == "one_integrated_chest_pocket"
        x0,x1 = ((3,6) if pocket_left else (9,12))
        _row(base,frames,defaults,signals,fabrics,"pockets","front",7,x0,x1,"STRUCTURAL_EDGE")
        _row(base,frames,defaults,signals,fabrics,"pockets","front",8,x0,x1,"SHADOW")
        for d,x in (("right",11),("left",4)):
            for y in range(5,14): _paint(base,frames,defaults,signals,fabrics,"seams",d,x,y,"SHADOW")
        _rear_band(base,frames,defaults,signals,fabrics)
        _row(base,frames,defaults,signals,fabrics,"panels","back",4,3,11,"STRUCTURAL_EDGE")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="PrimaryFabric")

    elif family == "CREWNECK_SWEATSHIRT":
        for d in DIRECTION_ORDER:
            for x in range(5,11): _paint(base,frames,defaults,signals,fabrics,"collar",d,x,1,"BASE" if x<9 else "SHADOW","Trim")
        if axes["pocketPanelArchitecture"] == "single_horizontal_body_block":
            # One broad plane, not a graphic stripe.
            for d in ("front","back"):
                for y in (5,6):
                    b=_bounds(frames[d],y)
                    if b: _row(base,frames,defaults,signals,fabrics,"panels",d,y,b[0]+2,b[1]-2,"LIGHT" if y==5 else "BASE","SecondaryFabric")
        else:
            for d in DIRECTION_ORDER:
                b=_bounds(frames[d],4)
                if b: _row(base,frames,defaults,signals,fabrics,"panels",d,4,b[0]+1,b[1]-1,"LIGHT","SecondaryFabric")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="Trim",gathered=True)

    elif family == "WORK_JACKET":
        for x,y,s in ((4,1,"STRUCTURAL_EDGE"),(5,1,"LIGHT"),(5,2,"BASE"),(11,1,"DEEP_CREASE"),(10,1,"BASE"),(10,2,"SHADOW")):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,s,"Trim")
        for y in range(3,14):
            for x in (7,8): _paint(base,frames,defaults,signals,fabrics,"opening","front",x,y,"STRUCTURAL_EDGE" if x==7 else "SHADOW","Trim")
        pocket_ranges=((2,6),(9,13)) if axes["pocketPanelArchitecture"]=="paired_patch_pockets" else ((2,6),(10,13))
        for x0,x1 in pocket_ranges:
            _row(base,frames,defaults,signals,fabrics,"pockets","front",7,x0,x1,"STRUCTURAL_EDGE")
            for y in (8,9,10): _row(base,frames,defaults,signals,fabrics,"pockets","front",y,x0,x1,"LIGHT" if y==8 and x0<8 else "SHADOW" if y==10 else "BASE")
        _rear_band(base,frames,defaults,signals,fabrics,deep=True)
        _row(base,frames,defaults,signals,fabrics,"panels","back",4,2,13,"STRUCTURAL_EDGE")
        for d,x in (("right",11),("left",4)):
            for y in range(5,14): _paint(base,frames,defaults,signals,fabrics,"seams",d,x,y,"SHADOW")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="Trim")

    elif family == "FORMAL_WAISTCOAT":
        for x,y in ((7,1),(8,1),(6,2),(7,2),(8,2),(9,2),(7,3),(8,3)):
            _paint(base,frames,defaults,signals,fabrics,"layering","front",x,y,"LIGHT" if y<3 else "BASE","SecondaryFabric")
        for x,y in ((5,1),(10,1),(6,2),(9,2),(6,3),(9,3),(7,4),(8,4)):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,"STRUCTURAL_EDGE" if y<3 else "DEEP_CREASE","Trim")
        for y in (6,8,10,12): _paint(base,frames,defaults,signals,fabrics,"opening","front",8,y,"BASE","Accent")
        if axes["pocketPanelArchitecture"] == "paired_welt_pockets":
            for x0,x1 in ((3,6),(9,12)): _row(base,frames,defaults,signals,fabrics,"pockets","front",9,x0,x1,"SHADOW","Trim")
        for d in DIRECTION_ORDER:
            for y in range(2,9):
                b=_bounds(frames[d],y)
                if b:
                    for x in b: _paint(base,frames,defaults,signals,fabrics,"sleeves",d,x,y,"STRUCTURAL_EDGE","Trim")
        _rear_band(base,frames,defaults,signals,fabrics)
        _row(base,frames,defaults,signals,fabrics,"panels","back",11,5,10,"SHADOW","Trim")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="PrimaryFabric")

    elif family == "TRACK_JACKET":
        for d in DIRECTION_ORDER:
            for y,x0,x1 in ((0,6,9),(1,5,10),(2,5,10)): _row(base,frames,defaults,signals,fabrics,"collar",d,y,x0,x1,"LIGHT" if d in {"front","left"} else "SHADOW","Trim")
        for y in range(3,9):
            _paint(base,frames,defaults,signals,fabrics,"opening","front",7,y,"STRUCTURAL_EDGE","Trim")
            _paint(base,frames,defaults,signals,fabrics,"opening","front",8,y,"SHADOW","Trim")
        for d in DIRECTION_ORDER:
            rows=(4,5) if axes["pocketPanelArchitecture"]=="shoulder_to_sleeve_block" else (5,6)
            for y in rows:
                b=_bounds(frames[d],y)
                if b: _row(base,frames,defaults,signals,fabrics,"panels",d,y,b[0]+1,b[1]-1,"LIGHT" if y==rows[0] else "BASE","SecondaryFabric")
        for x,y in ((3,9),(4,10),(5,11),(12,9),(11,10),(10,11)):
            _paint(base,frames,defaults,signals,fabrics,"pockets","front",x,y,"STRUCTURAL_EDGE","Trim")
        _row(base,frames,defaults,signals,fabrics,"panels","back",4,3,12,"STRUCTURAL_EDGE","SecondaryFabric")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="Trim",gathered=True)

    elif family == "FITTED_BLAZER":
        for x,y,s in ((4,1,"STRUCTURAL_EDGE"),(5,2,"LIGHT"),(6,3,"BASE"),(7,4,"DEEP_CREASE"),(11,1,"DEEP_CREASE"),(10,2,"SHADOW"),(9,3,"SHADOW"),(8,4,"DEEP_CREASE")):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,s,"Trim")
        for y in range(2,7):
            for x in range(7,9): _paint(base,frames,defaults,signals,fabrics,"layering","front",x,y,"LIGHT" if x==7 else "BASE","SecondaryFabric")
        _paint(base,frames,defaults,signals,fabrics,"opening","front",8,9,"BASE","Accent")
        if axes["pocketPanelArchitecture"] == "paired_welt_pockets":
            for x0,x1 in ((3,6),(9,12)): _row(base,frames,defaults,signals,fabrics,"pockets","front",9,x0,x1,"SHADOW","Trim")
        else:
            for x,y,s in ((10,6,"LIGHT"),(11,6,"BASE"),(10,7,"SHADOW"),(11,7,"SHADOW")):
                _paint(base,frames,defaults,signals,fabrics,"pockets","front",x,y,s,"Accent")
        _rear_band(base,frames,defaults,signals,fabrics,deep=True)
        for y in range(4,14): _paint(base,frames,defaults,signals,fabrics,"seams","back",8,y,"SHADOW")
        for d,x in (("right",10),("left",5)):
            for y in range(2,10): _paint(base,frames,defaults,signals,fabrics,"collar",d,x,y,"SHADOW" if d=="right" else "LIGHT","Trim")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="PrimaryFabric")

    elif family == "SAILOR_TOP":
        for x,y in ((3,1),(4,1),(5,2),(6,3),(7,4),(12,1),(11,1),(10,2),(9,3),(8,4)):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,"LIGHT" if x<8 else "SHADOW","Trim")
        for x,y in ((7,1),(8,1),(7,2),(8,2),(7,3),(8,3)):
            _paint(base,frames,defaults,signals,fabrics,"layering","front",x,y,"BASE","SecondaryFabric")
        if axes["pocketPanelArchitecture"] == "double_collar_band":
            for x,y in ((4,2),(5,3),(6,4),(11,2),(10,3),(9,4)):
                _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,"BASE","Accent")
        _row(base,frames,defaults,signals,fabrics,"panels","back",2,3,12,"STRUCTURAL_EDGE","Trim")
        _row(base,frames,defaults,signals,fabrics,"panels","back",3,4,11,"BASE","Trim")
        for d,x in (("right",10),("left",5)):
            for y in range(1,5): _paint(base,frames,defaults,signals,fabrics,"collar",d,x,y,"SHADOW" if d=="right" else "LIGHT","Trim")
        _hem_band(base,frames,defaults,signals,fabrics,fabric="PrimaryFabric")

    elif family == "POLO_KNIT":
        for x,y,s in ((5,1,"LIGHT"),(6,1,"BASE"),(5,2,"STRUCTURAL_EDGE"),(10,1,"SHADOW"),(9,1,"BASE"),(10,2,"DEEP_CREASE")):
            _paint(base,frames,defaults,signals,fabrics,"collar","front",x,y,s,"Trim")
        for y in range(2,6): _paint(base,frames,defaults,signals,fabrics,"opening","front",8,y,"SHADOW","Trim")
        _paint(base,frames,defaults,signals,fabrics,"opening","front",7,3,"BASE","Accent")
        if axes["pocketPanelArchitecture"] == "single_chest_plane":
            for x,y,s in ((4,6,"STRUCTURAL_EDGE"),(5,6,"LIGHT"),(4,7,"BASE"),(5,7,"SHADOW")):
                _paint(base,frames,defaults,signals,fabrics,"pockets","front",x,y,s,"SecondaryFabric")
        _rear_band(base,frames,defaults,signals,fabrics)
        _hem_band(base,frames,defaults,signals,fabrics,fabric="PrimaryFabric")

    after = {d:{(x,y) for y,row in enumerate(frames[d]) for x,p in enumerate(row) if p[3]} for d in DIRECTION_ORDER}
    return {"alphaAdded":{d:len(after[d]-before[d]) for d in DIRECTION_ORDER}, "alphaRemoved":{d:len(before[d]-after[d]) for d in DIRECTION_ORDER}}


def render_autonomous_concept(
    concept: dict[str, Any], *, clean_vest_side_top: bool = True,
    remove_detached_vest_side_islands: bool = True,
) -> AutonomousRecoveryRender:
    recipe, raw, base, backend = _carrier(concept)
    frames = _copy_frames(raw.frames); defaults = _copy_frames(raw.default_frames)
    _reset_to_proven_hd_planes(base, frames, defaults)
    signals = _signals(); fabrics = {d:{} for d in DIRECTION_ORDER}
    metrics = _construct(concept, base, frames, defaults, signals, fabrics)
    allow_exposure = concept["family"] in {"SWEATER_VEST", "FORMAL_WAISTCOAT"}
    side_top_removed: dict[str, dict[str, tuple[tuple[int, int], ...]]] = {}
    if clean_vest_side_top and concept["family"] == "SWEATER_VEST":
        side_top_removed = _clean_vest_side_top_overhang(
            frames, defaults, signals, fabrics,
            remove_detached_islands=remove_detached_vest_side_islands,
        )
    coverage = _coverage_missing(base, frames, allow_sleeve_exposure=allow_exposure)
    # These cells belong to the carrier's unsupported collar overhang, not the
    # torso/body coverage envelope. Preserve all other coverage failures.
    if side_top_removed:
        coverage = {
            direction: tuple(
                cell for cell in cells
                if cell not in set(side_top_removed.get(direction, {}).get("all", ()))
            )
            for direction, cells in coverage.items()
        }
    if any(coverage.values()): raise ValueError(f"{concept['id']} broke proven coverage: {coverage}")
    polished = polish_upper_frames(base, frames, defaults, article_family=concept["family"])
    protected = frozenset(cell for system in signals.values() for cell in system["back"])
    polished = soften_shared_rear_neck(base, polished, protected_cells=protected)
    resolved, roles, ramps, evidence = _resolve(concept, polished, fabrics)
    sleeve_fabric = "SecondaryFabric" if allow_exposure else "PrimaryFabric"
    sleeve = ramps[sleeve_fabric]
    sleeve_colors = tuple(c[:3] for c in (sleeve["DEEP_CREASE"], sleeve["BASE"], sleeve["LIGHT"]))
    components = {d:_connected_components(resolved[d]) for d in DIRECTION_ORDER}
    allowed = {
        d: (
            1 if concept["family"] == "SWEATER_VEST" and clean_vest_side_top and remove_detached_vest_side_islands
            else 2 if allow_exposure and d in {"right", "left"}
            else 1
        )
        for d in DIRECTION_ORDER
    }
    if any(components[d] > allowed[d] for d in DIRECTION_ORDER): raise ValueError(f"unexpected alpha islands: {components}")
    metrics.update({"connectedComponents":components,"maximumLogicalY":max(y for d in DIRECTION_ORDER for y,row in enumerate(resolved[d]) if any(p[3] for p in row)),"customSleeves":False,"referenceArtworkLoaded":False,"sideTopOverhangRepair":{"applied":bool(side_top_removed),"removedCells":{d:list(groups["all"]) for d,groups in side_top_removed.items()},"rowZeroRemovedCells":{d:list(groups["rowZero"]) for d,groups in side_top_removed.items()},"detachedIslandRemovedCells":{d:list(groups["detached"]) for d,groups in side_top_removed.items()},"frontBackUntouched":bool(side_top_removed)}})
    frozen = {s:{d:frozenset(c) for d,c in views.items()} for s,views in signals.items()}
    trace=("autonomous_design_concept","select_existing_V5_carrier","render_fs_hd_v2","render_fs_v3_surface","render_fs_v4","render_fs_v5b","render_fs_v5d_if_required","reset_named_surface_to_proven_hd_planes",f"article_adapter.{concept['family'].lower()}") + (("clean_vest_side_top_overhang",) if side_top_removed else ()) + (("clean_vest_side_detached_islands",) if side_top_removed and remove_detached_vest_side_islands else ()) + ("polish_upper_frames","soften_shared_rear_neck","semantic_palette_material_adapter")
    return AutonomousRecoveryRender(concept,backend,recipe,trace,resolved,roles,_stack(resolved),sleeve_colors,frozen,coverage,evidence,polished.metrics,metrics)
