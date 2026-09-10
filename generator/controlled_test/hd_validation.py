"""Quality gates for the three-garment HD-adapter repair proof."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from generator.controlled_test.hd_adapter import ControlledHDAdapterRender, SUPPORTED
from generator.png_utils import read_rgba_png


ROOT = Path(__file__).resolve().parents[2]
ANCHORS = {
    "Sunfield Pathfinder Jacket": ROOT / "output/fashionsense/v5e-art-polish-showcase/sunfield_pathfinder/shirt.png",
    "Juniper Vale Cardigan": ROOT / "output/fashionsense/v6-rare-ceiling/juniper_vale_cardigan/shirt.png",
    "Orchard Reserve Workshirt": ROOT / "output/fashionsense/v6-rare-ceiling/orchard_reserve_workshirt/shirt.png",
}


def _opaque(frame):
    return [(x, y, pixel) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]]


def _luminance(pixel) -> float:
    return 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]


def _frame_metrics(frame, role_frame=None) -> dict[str, Any]:
    opaque = _opaque(frame)
    colors = Counter(pixel[:3] for _, _, pixel in opaque)
    values = [_luminance(pixel) for _, _, pixel in opaque]
    result = {
        "opaqueCells": len(opaque),
        "activeColors": len(colors),
        "dominantFillPercentage": round(max(colors.values(), default=0) / max(1, len(opaque)), 4),
        "luminanceRange": round(max(values, default=0) - min(values, default=0), 2),
    }
    if role_frame is not None:
        roles = Counter(role for row in role_frame for role in row if role)
        result.update({
            "lightPlaneCells": sum(value for role, value in roles.items() if role.endswith(".LIGHT") or role.endswith(".OPTIONAL_HIGHLIGHT")),
            "shadowPlaneCells": sum(value for role, value in roles.items() if role.endswith(".SHADOW")),
            "structuralDarkCells": sum(value for role, value in roles.items() if role.endswith(".EXTERIOR_CONTOUR") or role.endswith(".DEEP_CREASE") or role.endswith(".STRUCTURAL_EDGE")),
            "semanticRoleCounts": dict(sorted(roles.items())),
        })
    return result


def _front_back_difference(render: ControlledHDAdapterRender) -> float:
    front, back = render.frames["front"], render.frames["back"]
    changed = total = 0
    for y in range(16):
        for x in range(16):
            if front[y][x][3] or back[y][x][3]:
                total += 1
                changed += front[y][x] != back[y][x]
    return round(changed / max(1, total), 4)


def _construction_count(render, system: str, direction: str) -> int:
    return len(render.construction_signals.get(system, {}).get(direction, ()))


def _neck_evidence(render) -> int:
    roles = render.role_frames["front"]
    return sum(1 for y in range(4) for x in range(4, 12) if roles[y][x] and not roles[y][x].endswith(".BASE"))


def _hem_evidence(render) -> int:
    roles = render.role_frames["front"]
    occupied = [y for y in range(16) if any(roles[y])]
    bottom = max(occupied)
    return sum(1 for role in roles[bottom] if role and not role.endswith(".BASE"))


def _layer_metrics(render) -> dict[str, Any]:
    front = render.role_frames["front"]
    secondary = [(x, y) for y, row in enumerate(front) for x, role in enumerate(row) if role and role.startswith("SecondaryFabric")]
    widths = {}
    for x, y in secondary:
        widths.setdefault(y, []).append(x)
    broad_rows = sum(1 for xs in widths.values() if max(xs) - min(xs) + 1 >= 4)
    return {"secondaryCells": len(secondary), "broadSecondaryRows": broad_rows}


def _anchor_metrics() -> dict[str, Any]:
    result = {}
    for name, path in ANCHORS.items():
        if not path.exists():
            result[name] = {"available": False, "path": str(path)}
            continue
        image = read_rgba_png(path)
        front = image["pixels"][:16]
        result[name] = {"available": True, "path": str(path), **_frame_metrics(front)}
    return result


def validate_hd_adapter_render(render: ControlledHDAdapterRender) -> dict[str, Any]:
    grammar = render.recipe["grammarId"]
    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    direction = {name: _frame_metrics(render.frames[name], render.role_frames[name]) for name in ("front", "right", "back", "left")}
    front = direction["front"]
    dominant_ceiling = {"FITTED_TEE": 0.65, "OPEN_CARDIGAN": 0.48, "WORK_JACKET": 0.48}[grammar]
    check("proven HD stage trace", render.stage_trace[0] == "render_fs_hd_v2" and "polish_upper_frames" in render.stage_trace, render.stage_trace)
    check("binary 16x16 directional art", all(len(frame) == 16 and all(len(row) == 16 and all(pixel[3] in {0,255} for pixel in row) for row in frame) for frame in render.frames.values()), "four 16x16 frames")
    check("body coverage", not any(render.coverage_missing.values()), render.coverage_missing)
    check("dominant fill controlled", front["dominantFillPercentage"] <= dominant_ceiling, {"actual": front["dominantFillPercentage"], "ceiling": dominant_ceiling})
    check("meaningful light plane", front["lightPlaneCells"] >= (8 if grammar == "FITTED_TEE" else 10), front["lightPlaneCells"])
    check("meaningful shadow plane", front["shadowPlaneCells"] >= 12, front["shadowPlaneCells"])
    check("structural dark hierarchy", 20 <= front["structuralDarkCells"] <= int(front["opaqueCells"] * 0.55), front["structuralDarkCells"])
    check("material changes pixels", render.material_evidence["pixelLevelEvidence"] and render.material_evidence["materialAffectedShadeCells"] >= 24, render.material_evidence)
    check("neckline or collar readable", _neck_evidence(render) >= 8, _neck_evidence(render))
    check("hem readable", _hem_evidence(render) >= 4, _hem_evidence(render))
    # A fitted tee intentionally has a quiet rear carrier; requiring jacket-
    # scale divergence would reward invented decoration. Ten percent still
    # requires the neck binding, light plane, and hem construction to differ.
    check("front/back differentiated", _front_back_difference(render) >= (0.10 if grammar == "FITTED_TEE" else 0.22), _front_back_difference(render))
    check("contour anchors", min(render.polish_metrics["darkExteriorAnchors"].values()) >= 20, render.polish_metrics["darkExteriorAnchors"])
    check("native sleeve ramp", len(render.sleeve_colors) == 3 and len(set(render.sleeve_colors)) == 3, render.sleeve_colors)

    layers = _layer_metrics(render)
    if grammar == "FITTED_TEE":
        center_secondary = sum(1 for y in range(3, 13) for x in (7,8) if render.role_frames["front"][y][x] and render.role_frames["front"][y][x].startswith("SecondaryFabric"))
        check("no fake center stripe", center_secondary == 0, center_secondary)
    elif grammar == "OPEN_CARDIGAN":
        check("broad inner layer", layers["secondaryCells"] >= 24 and layers["broadSecondaryRows"] >= 6, layers)
        check("two knit opening edges", _construction_count(render, "opening", "front") >= 20, _construction_count(render, "opening", "front"))
        check("side hanging edge", _construction_count(render, "opening", "right") >= 8 and _construction_count(render, "opening", "left") >= 8, {"right": _construction_count(render,"opening","right"), "left": _construction_count(render,"opening","left")})
        check("coherent knit back carrier", _construction_count(render, "collar", "back") >= 4 and direction["back"]["lightPlaneCells"] >= 8, {"collar": _construction_count(render,"collar","back"), "light": direction["back"]["lightPlaneCells"]})
    else:
        check("large practical pocket system", _construction_count(render, "pockets", "front") >= 10, _construction_count(render, "pockets", "front"))
        check("broad rear yoke", _construction_count(render, "panels", "back") >= 8, _construction_count(render, "panels", "back"))
        check("firm placket", _construction_count(render, "opening", "front") >= 8, _construction_count(render, "opening", "front"))
        check("straight heavy hem", _construction_count(render, "hem", "front") >= 4 and _construction_count(render, "hem", "back") >= 4, {"front": _construction_count(render,"hem","front"), "back": _construction_count(render,"hem","back")})

    failed = [item["name"] for item in checks if not item["passed"]]
    return {
        "id": render.recipe["id"],
        "grammarId": grammar,
        "status": "PASS" if not failed else "FAIL",
        "failed": failed,
        "checks": checks,
        "directionMetrics": direction,
        "frontBackDifference": _front_back_difference(render),
        "layerMetrics": layers,
        "backend": render.backend,
        "stageTrace": render.stage_trace,
    }


def validate_hd_adapter_collection(renders: list[ControlledHDAdapterRender]) -> dict[str, Any]:
    grammar_ids = tuple(render.recipe["grammarId"] for render in renders)
    per_garment = [validate_hd_adapter_render(render) for render in renders]
    failed = [item["grammarId"] for item in per_garment if item["status"] == "FAIL"]
    exact = grammar_ids == SUPPORTED
    anchors = _anchor_metrics()
    return {
        "status": "PASS_STATIC_RUNTIME_NOT_TESTED" if exact and not failed else "FAIL_STATIC",
        "exactThreeGrammarScope": exact,
        "grammarIds": grammar_ids,
        "failedGarments": failed,
        "perGarment": per_garment,
        "qualityAnchors": anchors,
        "anchorComparisonPolicy": "Anchor metrics contextualize shade/contrast discipline; simpler tee construction is not forced to match Rare feature count.",
        "runtimeStatus": "NOT_TESTED",
        "promotion": "EXPERIMENTAL",
    }
