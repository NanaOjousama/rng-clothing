"""QUALITY / DIVERSITY GATE (Pass 14).

Generation validity and visual diversity are separate problems.  This gate runs
on the RASTER, never on the metadata: two semantically different specs that
rasterize identically are near-duplicates, whatever their records say.

The gate never mutates the generator and never triggers backtracking (INV-12,
section 42).  It classifies, and the batch report aggregates.
"""

from __future__ import annotations

from dataclasses import dataclass

from .grammar import (COLOR_HARD_CEILING, IDENTITY_CONTRAST_FLOOR, VIEWS,
                      luminance, perceptual_distance)

ACCEPT = "ACCEPT"
NEAR_DUPLICATE = "NEAR_DUPLICATE"
IDENTITY_TOO_WEAK = "IDENTITY_TOO_WEAK"
LEGIBILITY_FAILURE = "LEGIBILITY_FAILURE"

NEAR_DUPLICATE_DISTANCE = 0.14      # provisional; the final metric is still open

_ROLE_CLASS = {"body": "B", "trim": "T", "under_layer": "I", "accent": "A",
               "secondary_accent": "S", "hardware": "H"}


@dataclass
class Signature:
    mask: dict
    value: dict
    palette: frozenset
    partition: dict
    focal: dict
    accents: dict

    def cells(self):
        return [(v, c) for v in VIEWS for c in sorted(self.mask[v])]


def signature(spec, construction, art, raster) -> Signature:
    mask, value, partition = {}, {}, {}
    for view in VIEWS:
        cells = construction.silhouette[view]
        mask[view] = frozenset(cells)
        value[view] = {c: int(luminance(raster[view][c]) // 32) for c in cells}
        partition[view] = {c: _ROLE_CLASS.get(art.paint[view][c].role, "?") for c in cells}
    # Palettes are coarsely quantised: two garments a few RGB steps apart are
    # the same palette to a player, and an exact-match Jaccard would report
    # every roll as maximally distinct.
    palette = frozenset((c[0] // 48, c[1] // 48, c[2] // 48)
                        for view in VIEWS for c in raster[view].values())
    return Signature(mask, value, palette, partition, dict(art.focal),
                     {v: frozenset(art.point_accents.get(v, ())) for v in VIEWS})


def distance(a: Signature, b: Signature) -> float:
    """Perceptual raster distance, 0 = identical."""
    cells = [(v, c) for v in VIEWS for c in sorted(a.mask[v] | b.mask[v])]
    n = len(cells) or 1
    mask_d = sum((c in a.mask[v]) != (c in b.mask[v]) for v, c in cells) / n
    val_d = sum(abs(a.value[v].get(c, -1) - b.value[v].get(c, -1)) > 0 for v, c in cells) / n
    part_d = sum(a.partition[v].get(c) != b.partition[v].get(c) for v, c in cells) / n
    inter = len(a.palette & b.palette)
    union = len(a.palette | b.palette) or 1
    pal_d = 1.0 - inter / union
    return 0.45 * val_d + 0.25 * part_d + 0.20 * pal_d + 0.10 * mask_d


def _role_values(art, raster, roles, views=VIEWS):
    """Cells painted in these roles, ordered so a median picks a typical colour."""
    vals = []
    for view in views:
        for c, pc in art.paint[view].items():
            if pc.role in roles and c in raster[view]:
                vals.append(raster[view][c])
    return sorted(vals, key=luminance)


def _median(xs):
    return xs[len(xs) // 2] if xs else (0, 0, 0, 0)


def identity_score(spec, construction, art, raster, architecture) -> dict:
    """How strongly does the raster still say what the Architecture claims?

    The Architecture declares which role pairs carry its identity; the gate
    measures exactly those, on pixels, across every view.  Nothing here knows
    what a collar, a yoke or a flap is — that was the last family-specific
    branch outside the library.
    """
    out = {}
    for rule in architecture.separation_rules:
        if rule.needs and construction.by_name(rule.needs) is None:
            continue        # the feature was never instantiated (INV-03)
        av = _role_values(art, raster, (rule.role,))
        bv = _role_values(art, raster, (rule.against,))
        if not av or not bv:
            continue
        out[rule.key] = perceptual_distance(_median(av), _median(bv))
    return out


def identity_composite(ident: dict, architecture) -> tuple:
    """Weighted mean of each declared cue's measured/required ratio.

    Capped per cue so one very strong relationship cannot mask two collapsed
    ones, but strong enough that it can carry a single weak one.
    """
    num = den = 0.0
    parts = {}
    for rule in architecture.separation_rules:
        if rule.key not in ident:
            continue
        floor = architecture.identity_floor * rule.floor_scale
        ratio = min(ident[rule.key] / floor, 2.0) if floor else 2.0
        parts[rule.key] = round(ratio, 2)
        num += ratio * rule.weight
        den += rule.weight
    return (num / den if den else 2.0), parts


def identity_retention(construction, art, architecture) -> dict:
    """Fraction of each identity piece still painted in its own role.

    Returns (achieved, required) so the gate compares against the piece's own
    authored floor — some pieces are meant to be painted over.
    """
    out = {}
    for piece in construction.pieces:
        floor = (piece.min_retention if piece.min_retention is not None
                 else architecture.identity_retention)
        own = piece.view_cells("front")
        if not piece.identity or not own or floor >= 1.0:
            continue
        # Detail burial only: a construction piece layering over this one is
        # the garment working as designed.
        buried = sum(1 for c in own
                     if art.paint["front"].get(c)
                     and any(art.paint["front"][c].feature.startswith(p)
                             for p in ("collar_trim", "yoke_trim", "surface:")))
        out[piece.name] = (1.0 - buried / len(own), floor)
    return out


def legibility(spec, raster) -> dict:
    colors = {c for view in VIEWS for c in raster[view].values()}
    levels = {int(luminance(c) // 32) for c in raster["front"].values()}
    return {"colors": len(colors), "front_value_levels": len(levels)}


@dataclass
class Verdict:
    classification: str
    reasons: list
    identity: dict
    legibility: dict
    nearest: tuple | None = None
    warnings: tuple = ()


def evaluate(spec, construction, art, raster, seen: list, architecture) -> tuple:
    """Returns (Verdict, Signature).  `seen` is [(seed, Signature)] already accepted."""
    ident = identity_score(spec, construction, art, raster, architecture)
    retention = identity_retention(construction, art, architecture)
    leg = legibility(spec, raster)
    leg["min_retention"] = round(min((a for a, _ in retention.values()), default=1.0), 2)
    sig = signature(spec, construction, art, raster)
    reasons = []

    if leg["colors"] > COLOR_HARD_CEILING:
        reasons.append(f"{leg['colors']} colours exceeds the {COLOR_HARD_CEILING} ceiling")
    if leg["front_value_levels"] < 3:
        reasons.append(f"front collapses to {leg['front_value_levels']} value level(s)")
    if reasons:
        return Verdict(LEGIBILITY_FAILURE, reasons, ident, leg), sig

    # Every separation the Architecture declared is checked, at the floor it
    # declared, and only when the feature it depends on actually exists.  A
    # failure is recorded, but whether it is FATAL is decided compositionally.
    composite, ratios = identity_composite(ident, architecture)
    leg["identity_composite"] = round(composite, 2)
    warnings = []
    shortfalls = []
    for rule in architecture.separation_rules:
        if rule.key not in ident:
            continue
        floor = architecture.identity_floor * rule.floor_scale
        if ident[rule.key] < floor:
            msg = f"{rule.key} reads at {ident[rule.key]:.0f}, needs {floor:.0f}"
            (shortfalls if rule.required else warnings).append(msg)
    if shortfalls:
        if composite < architecture.identity_composite_floor:
            reasons.extend(shortfalls)
            reasons.append(f"identity composite {composite:.2f} below "
                           f"{architecture.identity_composite_floor:.2f}")
        else:
            # Other cues carry it: record the shortfall, do not reject on it.
            warnings.extend(f"{m} (carried, composite {composite:.2f})"
                            for m in shortfalls)
    for name, (frac, floor) in retention.items():
        if frac < floor - 1e-6:
            reasons.append(f"{name} keeps only {frac:.0%} of its own role, "
                           f"needs {floor:.0%}")
    if reasons:
        return Verdict(IDENTITY_TOO_WEAK, reasons, ident, leg, warnings=tuple(warnings)), sig

    nearest = None
    for other_seed, other in seen:
        d = distance(sig, other)
        if nearest is None or d < nearest[1]:
            nearest = (other_seed, d)
    if nearest and nearest[1] < NEAR_DUPLICATE_DISTANCE:
        return Verdict(NEAR_DUPLICATE,
                       [f"distance {nearest[1]:.3f} to seed {nearest[0]}"],
                       ident, leg, nearest, tuple(warnings)), sig

    return Verdict(ACCEPT, [], ident, leg, nearest, tuple(warnings)), sig
