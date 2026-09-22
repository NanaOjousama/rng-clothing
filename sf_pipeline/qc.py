from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from v5.pngio import read_rgba_png
from .model import CandidateOutput, DirectionMethod, DirectionSetManifest, PromotionStatus


MAX_ACCEPTED_DIMENSION = 32
PREFERRED_MIN = 16
PREFERRED_MAX = 24
REQUIRED_SF_DIRECTIONS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
REQUIRED_CARDINAL_DIRECTIONS = {"front", "right", "back", "left"}


def _alpha_cells(path: str) -> Tuple[int, int, set[tuple[int, int]]]:
    image = read_rgba_png(Path(path))
    height = len(image)
    width = len(image[0]) if height else 0
    cells = {
        (x, y)
        for y, row in enumerate(image)
        for x, pixel in enumerate(row)
        if pixel[3] > 0
    }
    return width, height, cells


def _component_sizes(cells: set[tuple[int, int]]) -> List[int]:
    remaining = set(cells)
    sizes: List[int] = []
    while remaining:
        start = remaining.pop()
        q = deque([start])
        size = 1
        while q:
            x, y = q.popleft()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in remaining:
                    remaining.remove(n)
                    q.append(n)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def candidate_qc(output: CandidateOutput) -> Dict[str, object]:
    width, height, cells = _alpha_cells(output.local_path)
    components = _component_sizes(cells)
    issues: List[str] = []
    warnings: List[str] = []

    if width > MAX_ACCEPTED_DIMENSION or height > MAX_ACCEPTED_DIMENSION:
        issues.append("oversize")
    if not cells:
        issues.append("empty")
    if len(components) > 1:
        # Disconnected components are not always wrong (pom/tag), so this is a
        # mandatory human-review flag instead of an automatic reject.
        warnings.append(f"disconnected_components:{len(components)}")
    if width < PREFERRED_MIN or height < PREFERRED_MIN:
        warnings.append("below_preferred_size")
    if width > PREFERRED_MAX or height > PREFERRED_MAX:
        warnings.append("above_preferred_size")

    return {
        "passMechanical": not issues,
        "issues": issues,
        "warnings": warnings,
        "width": width,
        "height": height,
        "opaqueCells": len(cells),
        "componentSizes": components,
        "semanticHumanReviewRequired": True,
        "semanticChecklist": [
            "isolated garment only",
            "no person/mannequin/head/face",
            "no extra object/background/UI/text",
            "silhouette/design readable at Stardew scale",
        ],
    }


def direction_qc(manifest: DirectionSetManifest) -> Dict[str, object]:
    issues: List[str] = []
    warnings: List[str] = []
    present = set(manifest.directions)

    if manifest.method == DirectionMethod.EDIT_CARDINAL:
        missing = sorted(REQUIRED_CARDINAL_DIRECTIONS - present)
        if missing:
            issues.append("missing_cardinals:" + ",".join(missing))
        if manifest.garment_category.lower() in {"hat", "headwear"} and present != REQUIRED_CARDINAL_DIRECTIONS:
            warnings.append("headwear_edit_cardinal_should_only_package_cardinals")
    else:
        missing = sorted(REQUIRED_SF_DIRECTIONS - present)
        if missing:
            issues.append("missing_directions:" + ",".join(missing))
    size_reports = {}
    for direction, asset in manifest.directions.items():
        report = candidate_qc(
            CandidateOutput(
                index=0,
                asset_id=asset.asset_id,
                local_path=asset.local_path,
                width=asset.width,
                height=asset.height,
            )
        )
        size_reports[direction] = report
        if not report["passMechanical"]:
            issues.append(f"{direction}:" + ",".join(report["issues"]))
        warnings.extend(f"{direction}:{w}" for w in report["warnings"])

    return {
        "passMechanical": not issues,
        "issues": issues,
        "warnings": warnings,
        "cardinalMap": (
            {"front": "front", "right": "right", "back": "back", "left": "left"}
            if manifest.method == DirectionMethod.EDIT_CARDINAL
            else {"front": "S", "right": "E", "back": "N", "left": "W"}
        ),
        "method": manifest.method.value,
        "assetReports": size_reports,
        "semanticHumanReviewRequired": True,
        "consistencyChecklist": [
            "WHOLE_HAT identity consistent across cardinal views",
            "WRAPAROUND_REGION treatment continues on same semantic region",
            "LOCALIZED motifs are generator-controlled after base cardinals and only appear where physically intended",
            "left base matches a deterministic mirror of the selected right base unless construction explicitly forbids mirroring",
            "no new person/mannequin/head/face/background contamination",
            "side/back remain the same garment, not a redesigned garment",
        ],
    }


def promotion_allowed(status: PromotionStatus, candidate_ok: bool, direction_ok: bool,
                      human_art_approved: bool, esm_wear_approved: bool) -> bool:
    if status != PromotionStatus.PRODUCTION_APPROVED:
        return False
    return candidate_ok and direction_ok and human_art_approved and esm_wear_approved
