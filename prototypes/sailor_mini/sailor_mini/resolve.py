"""Stages 1-4: seed -> weighted variable resolution -> dependency filter -> ResolvedSpec.

The ResolvedSpec is the contract between design resolution and rendering.
Nothing downstream may re-decide a variable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict

from . import ARCHITECTURE, FAMILY
from .palette import FAMILY_ORDER, build_palette, contrast
from .rules import is_valid, violations
from .vocabulary import (COLLAR_SPAN, FIT_COLLAR_WIDENING, FIT_TAPER, FLAP_DEPTH,
                         MATERIAL, ORDER, V_DEPTH, VARIABLES)

MAX_ATTEMPTS = 40


def derive(seed: int, *path: str) -> int:
    payload = json.dumps({"seed": int(seed), "path": list(path)}, separators=(",", ":")).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def weighted_pick(seed: int, options: dict[str, int]) -> str:
    total = sum(options.values())
    x = derive(seed, "pick") % total
    for value, weight in options.items():
        if x < weight:
            return value
        x -= weight
    return next(iter(options))


@dataclass
class ResolvedSpec:
    id: str
    seed: int
    attempt: int
    family: str
    architecture: str
    fit: str
    material: str
    collar_width: str
    rear_flap_depth: str
    neckline: str
    trim_style: str
    center_detail: str
    color_architecture: str
    palette_family: str
    palette: dict = field(default_factory=dict)
    derived: dict = field(default_factory=dict)
    rejected: list = field(default_factory=list)
    pinned: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        d = asdict(self)
        d["palette"] = {slot: {role: "#%02X%02X%02X" % c[:3] for role, c in roles.items()}
                        for slot, roles in self.palette.items()}
        return d


def _derived_flags(c: dict) -> dict:
    """Numeric consequences carried into the architecture stage."""
    widen = FIT_COLLAR_WIDENING[c["fit"]]
    left, right = COLLAR_SPAN[c["collar_width"]]
    left = max(2, left - widen); right = min(13, right + widen)
    flap = min(9, FLAP_DEPTH[c["rear_flap_depth"]] + widen)
    mat = MATERIAL[c["material"]]
    return {
        "collar_left": left,
        "collar_right": right,
        "collar_columns": right - left + 1,
        "flap_depth_rows": flap,
        "v_depth_row": V_DEPTH[c["neckline"]],
        "fit_taper": FIT_TAPER[c["fit"]],
        "relaxed_widening_applied": bool(widen),
        "crisp_collar_edge": mat["crisp_collar_edge"],
        "hem_rib": mat["hem_rib"],
        "fold_density": mat["fold_density"],
        "trim_lines": {"NONE": 0, "SINGLE": 1, "DOUBLE": 2}[c["trim_style"]],
        "has_center_detail": c["center_detail"] != "NONE",
    }


def resolve(seed: int, *, spec_id: str, pinned: dict | None = None,
            palette_family: str | None = None) -> ResolvedSpec:
    """Roll every variable from the seed, reject invalid combinations, reroll internally.

    `pinned` forces variables to fixed values; a pinned combination that is
    invalid raises rather than silently drifting, so controlled comparison pairs
    cannot be quietly altered by the resolver.
    """
    pinned = dict(pinned or {})
    for key in pinned:
        if key not in VARIABLES:
            raise KeyError(f"unknown pinned variable {key!r}")
        if pinned[key] not in VARIABLES[key]:
            raise ValueError(f"{key}={pinned[key]!r} not in vocabulary")

    rejected = []
    for attempt in range(MAX_ATTEMPTS):
        candidate = {}
        for var in ORDER:
            candidate[var] = pinned[var] if var in pinned else weighted_pick(derive(seed, str(attempt), var), VARIABLES[var])
        bad = violations(candidate)
        if not bad:
            break
        rejected.append({"attempt": attempt, "candidate": dict(candidate), "violations": bad})
    else:
        raise RuntimeError(f"{spec_id}: no valid combination in {MAX_ATTEMPTS} attempts; pinned={pinned}")

    if pinned and not is_valid({**candidate, **pinned}):
        raise RuntimeError(f"{spec_id}: pinned combination is structurally invalid: {violations(candidate)}")

    family = palette_family or FAMILY_ORDER[derive(seed, "palette_family") % len(FAMILY_ORDER)]
    palette = build_palette(family, candidate["color_architecture"])
    derived = _derived_flags(candidate)
    derived["collar_body_contrast"] = contrast(palette, "collar", "body")
    derived["trim_collar_contrast"] = contrast(palette, "trim", "collar")

    return ResolvedSpec(
        id=spec_id, seed=seed, attempt=attempt, family=FAMILY, architecture=ARCHITECTURE,
        palette_family=family, palette=palette, derived=derived, rejected=rejected,
        pinned=dict(pinned), **candidate,
    )
