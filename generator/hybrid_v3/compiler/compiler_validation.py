"""Hard canonical, compiler, and final-sprite validation for Phase 2."""

from __future__ import annotations

from typing import Any

from generator.hybrid_v3.validator import PhysicalValidator
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER


def _components(frame):
    cells = {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}
    groups = []
    while cells:
        root = cells.pop(); group = {root}; todo = [root]
        while todo:
            x, y = todo.pop()
            for nxt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nxt in cells:
                    cells.remove(nxt); group.add(nxt); todo.append(nxt)
        groups.append(group)
    return sorted(groups, key=len, reverse=True)


def _luma(pixel):
    return (pixel[0] * 299 + pixel[1] * 587 + pixel[2] * 114) // 1000


def _accidental_dark_bands(frame):
    """Detect long interior dark rails/bands, excluding the silhouette edge."""
    dark_by_row={}
    for y,row in enumerate(frame):
        opaque=[(x,p) for x,p in enumerate(row) if p[3]]
        if not opaque: continue
        values=sorted(_luma(p) for _,p in opaque); median=values[len(values)//2]
        lo,hi=opaque[0][0],opaque[-1][0]
        dark_by_row[y]={x for x,p in opaque if lo < x < hi and _luma(p) <= median-28}
    vertical=[]
    for x in range(16):
        run=[]
        for y in range(3,13):
            if x in dark_by_row.get(y,set()): run.append(y)
            else:
                if len(run)>=6: vertical.append({"x":x,"fromY":run[0],"toY":run[-1]})
                run=[]
        if len(run)>=6: vertical.append({"x":x,"fromY":run[0],"toY":run[-1]})
    horizontal=[]
    for y in range(5,13):
        run=[]
        for x in range(1,15):
            if x in dark_by_row.get(y,set()): run.append(x)
            else:
                if len(run)>=8: horizontal.append({"y":y,"fromX":run[0],"toX":run[-1]})
                run=[]
        if len(run)>=8: horizontal.append({"y":y,"fromX":run[0],"toX":run[-1]})
    return {"vertical":vertical,"horizontal":horizontal}


def validate_compiled(canonical: dict[str, Any], projections: dict, frames: dict, regions, coverage_missing: dict,
                      *, topology_operations=(), safe_envelopes=None, shape_events=(), shape_contract_enabled=False,
                      shape_library_version=None, required_shape_library_version=None, expected_shape_variants=None) -> dict[str, Any]:
    validator = PhysicalValidator()
    canonical_result = validator.validate(canonical)
    projection_result = validator.validate_projections(canonical, projections)
    issues = []
    if canonical_result["status"] != "PASS": issues.append({"code": "CANONICAL_INVALID", "detail": canonical_result["issues"]})
    if projection_result["status"] != "PASS": issues.append({"code": "PROJECTION_INVALID", "detail": projection_result["issues"]})

    components = {}; top_rows = {}; binary_alpha = True; dark_bands={}
    for direction in DIRECTION_ORDER:
        groups = _components(frames[direction]); components[direction] = [len(group) for group in groups]
        if len(groups) != 1:
            issues.append({"code": "ALPHA_COMPONENT_COUNT", "direction": direction, "expected": 1, "actual": len(groups), "sizes": components[direction]})
        unsupported = []
        for y in range(0, 5):
            for x, pixel in enumerate(frames[direction][y]):
                if pixel[3] not in (0, 255): binary_alpha = False
                if y == 0 and pixel[3]:
                    supported = any(frames[direction][1][nx][3] for nx in range(max(0,x-1), min(16,x+2)))
                    if not supported: unsupported.append([x, y])
        top_rows[direction] = {"unsupportedRowZeroCells": unsupported, "opaqueCellsRows0To4": sum(1 for y in range(5) for p in frames[direction][y] if p[3])}
        if unsupported:
            issues.append({"code": "TOP_EDGE_CONTAMINATION", "direction": direction, "cells": unsupported})
        dark_bands[direction]=_accidental_dark_bands(frames[direction])
        if shape_contract_enabled and (dark_bands[direction]["vertical"] or dark_bands[direction]["horizontal"]):
            issues.append({"code":"ACCIDENTAL_DARK_BAND","direction":direction,"detail":dark_bands[direction]})
    if not binary_alpha: issues.append({"code": "NON_BINARY_ALPHA"})
    if any(coverage_missing.values()): issues.append({"code": "RUNTIME_ENVELOPE_COVERAGE", "detail": {d:list(v) for d,v in coverage_missing.items() if v}})

    projection_by = {d:{x["componentInstance"]:x for x in projections[d]} for d in DIRECTION_ORDER}
    for component in canonical["components"]:
        instance = component["instanceId"]
        for direction in DIRECTION_ORDER:
            visibility = projection_by[direction][instance]["visibility"]
            cells = regions.component_cells.get(instance, {}).get(direction, set())
            runtime = regions.runtime_components.get(instance, {}).get(direction)
            if visibility in {"FULL", "COMPRESSED", "DEPTH_ONLY", "EDGE_ONLY"} and component["mandatory"] and not cells and not runtime:
                issues.append({"code": "MANDATORY_IDENTITY_NOT_EMITTED", "component": instance, "direction": direction, "visibility": visibility})
            if visibility == "FORBIDDEN" and (cells or runtime):
                issues.append({"code": "COMPONENT_IN_FORBIDDEN_DIRECTION", "component": instance, "direction": direction})

    family = canonical["identity"]["family"]
    if family == "SWEATER_VEST":
        if any(c["componentType"] == "SLEEVE" for c in canonical["components"]):
            issues.append({"code": "VEST_SLEEVE_COMPONENT"})
        for direction in ("right", "left"):
            armhole = regions.component_cells.get("armholes", {}).get(direction, set())
            if len(armhole) < 4: issues.append({"code": "VEST_SIDE_ARMHOLE_UNREADABLE", "direction": direction, "cells": len(armhole)})

    # V4.1 identity-salience contract. These are structural minimums, not a
    # visual PASS. They only prevent a family from compiling after losing its
    # mandatory construction anchors.
    if family == "POLO_SHIRT":
        collar_front = regions.systems.get("collar", {}).get("front", set())
        placket_front = regions.systems.get("placket", {}).get("front", set())
        side_collar = min(
            len(regions.systems.get("collar", {}).get("right", set())),
            len(regions.systems.get("collar", {}).get("left", set())),
        )
        if len(collar_front) < 6:
            issues.append({"code":"IDENTITY_ANCHOR_WEAK", "family":family, "anchor":"folded_collar_front", "cells":len(collar_front), "minimum":6})
        if len(placket_front) < 4:
            issues.append({"code":"IDENTITY_ANCHOR_WEAK", "family":family, "anchor":"short_front_placket", "cells":len(placket_front), "minimum":4})
        if side_collar < 3:
            issues.append({"code":"IDENTITY_ANCHOR_WEAK", "family":family, "anchor":"folded_collar_side_depth", "cells":side_collar, "minimum":3})
    elif family == "SAILOR_TOP":
        rear = regions.systems.get("rear_panel", {}).get("back", set())
        collar = regions.systems.get("collar", {}).get("front", set())
        if len(collar) < 6 or len(rear) < 12:
            issues.append({"code":"IDENTITY_ANCHOR_WEAK", "family":family, "anchor":"sailor_collar_plus_rear_panel", "frontCollar":len(collar), "rearPanel":len(rear)})

    default_expected_variants={
        "POLO_SHIRT":{"FOLDED_POLO_COLLAR_FRONT_V1","FOLDED_POLO_COLLAR_SIDE_V1","FOLDED_POLO_COLLAR_BACK_V1","SHORT_POLO_PLACKET_FRONT_V1"},
        "SWEATER_VEST":{"V_BINDING_FRONT_V1","V_BINDING_SIDE_V1","V_BINDING_BACK_V1","CUTIN_ARMHOLE_SIDE_V1","INNER_SHIRT_EXPOSURE_SIDE_V1","KNIT_HEM_TERMINATION_V1"},
        "SAILOR_TOP":{"SAILOR_COLLAR_FRONT_V1","SAILOR_COLLAR_SIDE_V1","SAILOR_REAR_PANEL_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"},
    }.get(family,set())
    expected_variants=(set(expected_shape_variants) if expected_shape_variants is not None else default_expected_variants) if (shape_contract_enabled or required_shape_library_version is not None) else set()
    actual_variants={event["variantId"] for event in shape_events}
    if required_shape_library_version is not None:
        if shape_library_version != required_shape_library_version:
            issues.append({"code":"V4_2_SHAPE_LIBRARY_VERSION_MISMATCH","required":required_shape_library_version,"actual":shape_library_version})
        if not expected_variants:
            issues.append({"code":"V4_2_EXPECTED_VARIANTS_EMPTY","family":family})
    missing_variants=sorted(expected_variants-actual_variants)
    if missing_variants:
        issues.append({"code":"REQUIRED_SHAPE_VARIANT_NOT_EXECUTED","variants":missing_variants})
    minimum_failures=[]
    for event in shape_events:
        for direction,minimum in event["minimumIdentityCells"].items():
            actual=event["emitted"].get(direction,0)
            if actual < minimum:
                minimum_failures.append({"variantId":event["variantId"],"direction":direction,"actual":actual,"minimum":minimum})
    if minimum_failures:
        issues.append({"code":"SHAPE_VARIANT_MINIMUM_IDENTITY","detail":minimum_failures})

    envelope_failures=[]; survival_failures=[]
    safe_envelopes=safe_envelopes or {}
    for operation in topology_operations:
        d=operation["direction"]; cell=tuple(operation["cell"]); x,y=cell
        if cell not in safe_envelopes.get(d,set()): envelope_failures.append(operation)
        final_opaque=bool(frames[d][y][x][3])
        expected=operation["op"]=="ADD"
        if final_opaque != expected: survival_failures.append({**operation,"finalOpaque":final_opaque})
    if envelope_failures: issues.append({"code":"TOPOLOGY_OUTSIDE_SAFE_ENVELOPE","detail":envelope_failures})
    if survival_failures: issues.append({"code":"STRUCTURAL_CHANGE_DID_NOT_SURVIVE","detail":survival_failures})

    required_topology=({"POLO_SHIRT":{"ADD":2},"SWEATER_VEST":{"REMOVE":4},"SAILOR_TOP":{"ADD":2}}.get(family,{}) if (shape_contract_enabled or required_shape_library_version is not None) else {})
    topology_counts={op:sum(1 for item in topology_operations if item["op"]==op and item["alphaDisplacement"]) for op in ("ADD","REMOVE")}
    visual_change_failures=[]
    for op,minimum in required_topology.items():
        if topology_counts[op] < minimum: visual_change_failures.append({"operation":op,"actual":topology_counts[op],"minimum":minimum})
    if visual_change_failures: issues.append({"code":"VISUAL_CHANGE_CONTRACT","detail":visual_change_failures})

    owned_survival=[]
    for direction,owners in regions.ownership.cells.items():
        for (x,y),owner in owners.items():
            if owner.protection_level not in {"STRUCTURAL","LOCKED"}: continue
            opaque=bool(frames[direction][y][x][3])
            expected=owner.topology_role != "ALPHA_REMOVAL"
            if opaque != expected: owned_survival.append({"direction":direction,"cell":[x,y],"owner":owner.component_owner,"topologyRole":owner.topology_role})
    if owned_survival: issues.append({"code":"PROTECTED_STRUCTURAL_CELL_LOST","detail":owned_survival})

    return {
        "status": "PASS" if not issues else "FAIL", "issues": issues,
        "canonicalValidation": canonical_result, "projectionValidation": projection_result,
        "connectedComponents": components, "topRows": top_rows, "binaryAlpha": binary_alpha,
        "darkBandScan":dark_bands,
        "shapeVariantExecution":{"requiredLibraryVersion":required_shape_library_version,"loadedLibraryVersion":shape_library_version,"expected":sorted(expected_variants),"actual":sorted(actual_variants),"minimumFailures":minimum_failures},
        "topology":{"operations":list(topology_operations),"counts":topology_counts,"safeEnvelopeFailures":envelope_failures,"survivalFailures":survival_failures},
        "visualChangeContract":{"status":"PASS" if not visual_change_failures else "FAIL","failures":visual_change_failures,"roleOnlyRecolorsReportedAsGeometry":False},
        "protectedStructuralSurvival":{"status":"PASS" if not owned_survival else "FAIL","failures":owned_survival},
        "ownershipConflicts":{"count":len(regions.ownership.conflicts),"allRejected":all(c.get("resolution")=="INCOMING_CLAIM_REJECTED_EXISTING_OWNER_PRESERVED" for c in regions.ownership.conflicts)},
        "mandatoryIdentityPresent": not any(i["code"] == "MANDATORY_IDENTITY_NOT_EMITTED" for i in issues),
        "automatedQC":"PASS" if not issues else "FAIL",
        "humanVisualQC": {"status": "PENDING", "authority": "Farmer composite; identity without garment labels"},
        "farmerVisualReview": {"status": "PENDING_HUMAN_INSPECTION", "authority": "Farmer composite"},
    }
