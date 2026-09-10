"""SURFACE LIBRARY (section 25) — separate from Ornament.

Surface is doubly gated: the Material must permit it, and the resolved
Architecture must leave enough area in the target domain for it to read.
If a repeating pattern cannot render meaningfully we drop it rather than
compress it into noise.
"""

from __future__ import annotations

from dataclasses import dataclass

from .grammar import GIRTH, PLANE, terminate_inboard


@dataclass(frozen=True)
class SurfaceType:
    name: str
    min_readable_area: int      # cells the domain must have for the pattern to read
    min_span: int               # cells across the pattern axis
    wrap: str
    periodic: bool
    role_map: tuple             # (ground role, figure role)


SURFACES = {
    s.name: s for s in (
        SurfaceType("solid", 0, 0, PLANE, False, ("body", "body")),
        # Breton stripes are tonal.  Using the signal accent here put a
        # saturated band across the chest that competed with the tie for the
        # same role — the reference sailors keep the shell solid and spend
        # saturation on the tie alone.
        SurfaceType("horizontal_stripe", 12, 4, GIRTH, True, ("body", "secondary_accent")),
        SurfaceType("vertical_stripe", 12, 4, GIRTH, True, ("body", "secondary_accent")),
        SurfaceType("panel", 8, 3, PLANE, False, ("body", "secondary_accent")),
    )
}


def domain_cells(construction, domain: str, view: str) -> set:
    names = construction.surface_domains.get(domain, ())
    region = construction.region_map(view)
    return {c for c, owner in region.items() if owner in names}


def readable(surface: SurfaceType, cells: set, period: int | None) -> bool:
    """Would this pattern actually read, or collapse into noise?"""
    if surface.name == "solid":
        return True
    if len(cells) < surface.min_readable_area:
        return False
    if surface.name == "horizontal_stripe":
        rows = {y for _, y in cells}
        if len(rows) < surface.min_span:
            return False
        return period is not None and len(rows) // period >= 2
    if surface.name == "vertical_stripe":
        cols = {x for x, _ in cells}
        if len(cols) < surface.min_span:
            return False
        return period is not None and len(cols) // period >= 2
    if surface.name == "panel":
        cols = {x for x, _ in cells}
        return len(cols) >= surface.min_span
    return True


def figure_cells(surface: SurfaceType, cells: set, period: int, phase: int,
                 registration: int) -> set:
    """Which cells of the domain carry the figure role."""
    # Stripes are decorative linework, so their runs terminate one cell inboard
    # of the silhouette rather than on it.  `panel` below is deliberately NOT
    # treated: it is a contiguous structural block whose edges are meant to
    # land on the garment boundary.
    if surface.name == "horizontal_stripe":
        return terminate_inboard(
            {c for c in cells if (c[1] + phase) % period == 0}, run_axis=0)
    if surface.name == "vertical_stripe":
        return terminate_inboard(
            {c for c in cells if (c[0] + phase) % period == 0}, run_axis=1)
    if surface.name == "panel":
        cols = sorted({x for x, _ in cells})
        lo = cols[max(0, len(cols) // 2 - 1 + registration)]
        hi = cols[min(len(cols) - 1, len(cols) // 2 + registration)]
        return {c for c in cells if lo <= c[0] <= hi}
    return set()
