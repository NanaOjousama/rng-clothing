"""Stage 6: ArchitecturePlan -> RenderPlan.

ART GRAMMAR decisions only. The architecture stage already said where the fabric
is and which of its edges hang. This stage decides how that reads as pixels:

  1. OUTLINE POLICY     an outline is allowed on a FREE edge and forbidden on an
                        ATTACHED edge. This is the single rule that makes the rear
                        flap read as fabric lying on the back rather than a
                        pasted square with a border all the way round.
  2. OCCLUSION          body cells behind a free edge take the body shadow, never
                        the darkest step: a free edge reads as deep fabric with a
                        softer drop shadow beneath it, not a two-pixel black bar.
  3. LIGHT FIELD        screen upper-left. Within any region the low-x/low-y side
                        takes light, the high-x/high-y side takes shadow.
  4. LIFT GRADIENT      a hanging panel is lighter where it lies flat on the
                        shoulders and darker toward its free edge.
  5. TRIM               runs parallel to the free edge, inset one cell, never on
                        an attached edge.
  6. MATERIAL           crisp materials take a deep outline on free edges; knit
                        takes shadow instead, and gains a hem rib.

Output is an ordered list of paint ops. Every op names the system that made it,
so any final pixel is attributable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .architecture import SHOULDER_ROWS, W


@dataclass
class Op:
    x: int
    y: int
    role: str
    slot: str
    system: str


def _region_bounds(region):
    cells = region.cells()
    xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
    return (min(xs), max(xs), min(ys), max(ys)) if cells else (0, 0, 0, 0)


def _light_role(x, y, x0, x1, y0, y1) -> str:
    """Rule 3: screen upper-left light field inside a region."""
    span_x = max(1, x1 - x0); span_y = max(1, y1 - y0)
    fx = (x - x0) / span_x; fy = (y - y0) / span_y
    if fx <= 0.34 and fy <= 0.5:
        return "light"
    if fx >= 0.72 or fy >= 0.8:
        return "shadow"
    return "base"


def build_render_plan(spec, plans) -> dict[str, list[Op]]:
    return {view: _plan_view(spec, view, plans[view]) for view in ("front", "side", "back")}


def _plan_view(spec, view, plan) -> list[Op]:
    d = spec.derived
    ops: list[Op] = []
    crisp = d["crisp_collar_edge"]
    # Rule 1a: a free edge only earns a dark outline when the collar and the body
    # are close in value. Where they already separate by colour, an outline on
    # both sides of a three-cell leaf consumes the whole leaf and the collar
    # reads as a bordered sticker. Installed vanilla sailor tops carry no outline
    # around a white collar on a navy body: the value change is the edge.
    strong_contrast = d["collar_body_contrast"] >= 45
    edge_role = "shadow" if (not crisp or strong_contrast) else "deep"

    # ---- Rule 2: occlusion onto the body, before any collar fabric is laid down
    for (x, y) in sorted(plan.occlusion):
        ops.append(Op(x, y, "shadow", "body", "occlusion_under_free_edge"))

    for name, region in plan.regions.items():
        if name == "center_detail":
            continue
        slot = "collar"
        x0, x1, y0, y1 = _region_bounds(region)
        free = plan.free_edges.get(name, set())
        attached = plan.attached_edges.get(name, set())
        bottom = region.bottom_row()

        # ---- Rules 3 + 4: fill the region with a light field plus a lift gradient
        for (x, y) in sorted(region.cells()):
            role = _light_role(x, y, x0, x1, y0, y1)
            if name == "flap_back":
                # a panel hanging off the shoulders: flat and lit at the top,
                # lifting and darker toward the free bottom edge
                if y <= SHOULDER_ROWS and x <= x0 + (x1 - x0) // 2:
                    role = "light"
                elif y >= bottom - 1:
                    role = "shadow"
            ops.append(Op(x, y, role, slot, f"{name}:light_field"))

        # ---- Rule 1: outline policy. FREE edges only.
        for (x, y) in sorted(free):
            ops.append(Op(x, y, edge_role, slot, f"{name}:free_edge_outline"))
        # ATTACHED edges are deliberately left as fabric. No op is emitted for
        # them; the absence is the point and is asserted by the tests.
        _ = attached

    # ---- Rule 5: trim parallel to the free edge
    ops.extend(_trim_ops(spec, view, plan))

    # ---- centre detail sits on top of everything
    if "center_detail" in plan.regions:
        det = plan.regions["center_detail"]
        cells = sorted(det.cells())
        for i, (x, y) in enumerate(cells):
            role = "base" if i % 3 != 2 else "shadow"
            ops.append(Op(x, y, role, "accent", "center_detail"))
        if cells:
            kx, ky = cells[0]
            ops.append(Op(kx, ky, "deep", "accent", "center_detail:knot_core"))

    # ---- Rule 6: material
    if d["hem_rib"]:
        for x in range(2, W - 2, 1):
            ops.append(Op(x, 14, "shadow", "body", "material:knit_hem_rib"))
    for i in range(d["fold_density"]):
        fx, fy = ((2, 10), (13, 12))[i]
        ops.append(Op(fx, fy, "shadow", "body", "material:fold"))
    return ops


def _trim_ops(spec, view, plan) -> list[Op]:
    """Trim lines run parallel to a free edge, inset 1 (and 3 for DOUBLE)."""
    lines = spec.derived["trim_lines"]
    if not lines:
        return []
    insets = [1] if lines == 1 else [1, 3]
    ops: list[Op] = []

    if view == "back" and "flap_back" in plan.regions:
        flap = plan.regions["flap_back"]
        bottom = flap.bottom_row()
        for inset in insets:
            y = bottom - inset
            for a, b in flap.rows.get(y, []):
                for x in range(a + 1, b):
                    ops.append(Op(x, y, "base", "trim", f"trim:flap_line_inset{inset}"))

    if view == "front" and "collar_front" in plan.regions:
        collar = plan.regions["collar_front"]
        for y, spans in collar.rows.items():
            for a, b in spans:
                # a stripe needs fabric on both sides of it; on a one- or
                # two-cell leaf it splits the collar instead of decorating it
                if b - a + 1 < 3:
                    continue
                inner_is_right = a < 7  # left leaf: its V edge is the right-hand end
                for inset in insets:
                    x = b - inset if inner_is_right else a + inset
                    if a <= x <= b:
                        ops.append(Op(x, y, "base", "trim", f"trim:leaf_line_inset{inset}"))

    if view == "side" and "collar_side" in plan.regions:
        band = plan.regions["collar_side"]
        bottom = band.bottom_row()
        for inset in insets:
            y = bottom - inset
            for a, b in band.rows.get(y, []):
                for x in range(a, b + 1):
                    ops.append(Op(x, y, "base", "trim", f"trim:side_line_inset{inset}"))
    return ops
