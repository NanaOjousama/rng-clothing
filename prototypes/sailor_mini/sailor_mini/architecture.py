"""Stage 5: ResolvedSpec -> ArchitecturePlan.

ARCHITECTURE decisions only: where fabric physically is, and how it attaches.
This stage answers "what is the garment built from", never "how is it shaded".

Every region carries an attachment classification:
    ATTACHED  - this edge is sewn/continuous with the body or the collar band.
    FREE      - this edge hangs. It terminates the fabric and occludes what is behind it.

The FREE/ATTACHED split is what stops the rear flap reading as a pasted square.
"""

from __future__ import annotations

from dataclasses import dataclass, field

W = 16
NECK_GAP = (6, 9)          # front/back neck columns in the body silhouette
SIDE_NECK_GAP = (6, 7)
SHOULDER_ROWS = 2          # rows where the collar keeps its full shoulder span


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


@dataclass
class Region:
    """A contiguous construction region, described per row as inclusive spans."""
    name: str
    rows: dict[int, list[tuple[int, int]]] = field(default_factory=dict)

    def add(self, y: int, x0: int, x1: int) -> None:
        if x1 >= x0:
            self.rows.setdefault(y, []).append((x0, x1))

    def cells(self) -> set[tuple[int, int]]:
        return {(x, y) for y, spans in self.rows.items() for a, b in spans for x in range(a, b + 1)}

    def bottom_row(self) -> int:
        return max(self.rows) if self.rows else -1


@dataclass
class ArchitecturePlan:
    view: str
    regions: dict[str, Region] = field(default_factory=dict)
    free_edges: dict[str, set] = field(default_factory=dict)      # region -> cells whose outward side hangs
    attached_edges: dict[str, set] = field(default_factory=dict)  # region -> cells continuous with body/collar
    occlusion: set = field(default_factory=set)                   # BODY cells shadowed by an overhanging free edge
    notes: list = field(default_factory=list)

    def region(self, name: str) -> Region:
        return self.regions.setdefault(name, Region(name))


# ---------------------------------------------------------------------------
# FRONT
# ---------------------------------------------------------------------------

def _front(spec) -> ArchitecturePlan:
    d = spec.derived
    plan = ArchitecturePlan("front")
    left, right = d["collar_left"], d["collar_right"]
    v = d["v_depth_row"]
    collar = plan.region("collar_front")
    free, attached = set(), set()

    for y in range(0, v + 1):
        # inner boundary: the V edge, from the neck gap down to the apex
        ti = min(1.0, y / max(1, v))
        inner_l = int(round(_lerp(NECK_GAP[0] - 1, 7, ti)))
        inner_r = int(round(_lerp(NECK_GAP[1] + 1, 8, ti)))
        # outer boundary: full shoulder span for the top rows, then converging
        if y <= SHOULDER_ROWS:
            outer_l, outer_r = left, right
        else:
            # convex curve: the leaf keeps its width down the chest and only
            # converges near the apex, so it reads as a collar and not a stripe
            to = ((y - SHOULDER_ROWS) / max(1, v - SHOULDER_ROWS)) ** 1.8
            outer_l = int(round(_lerp(left, 7, to)))
            outer_r = int(round(_lerp(right, 8, to)))
        collar.add(y, outer_l, inner_l)
        collar.add(y, inner_r, outer_r)
        # The V edge is the dominant FREE edge on both leaves. The outer edge is
        # ATTACHED at the shoulder and only becomes a second free edge where the
        # leaf is at least three cells wide; below that a second outline would
        # consume the whole leaf and leave no fabric.
        free.add((inner_l, y)); free.add((inner_r, y))
        if y <= SHOULDER_ROWS:
            attached.add((outer_l, y)); attached.add((outer_r, y))
        else:
            if inner_l - outer_l + 1 >= 3:
                free.add((outer_l, y))
            if outer_r - inner_r + 1 >= 3:
                free.add((outer_r, y))

    plan.free_edges["collar_front"] = free
    plan.attached_edges["collar_front"] = attached

    # The V opening between the leaves shows the body; the apex row below the
    # collar receives the occlusion of the two converging free edges.
    if v + 1 < W:
        plan.occlusion.update({(7, v + 1), (8, v + 1)})

    # Centre detail hangs from the apex.
    if spec.center_detail != "NONE":
        detail = plan.region("center_detail")
        top = v + 1
        if spec.center_detail == "TIE":
            detail.add(top, 7, 8)
            detail.add(top + 1, 7, 7); detail.add(top + 1, 8, 8)
            detail.add(top + 2, 8, 8)
            plan.notes.append("TIE: two-cell knot at the apex with one hanging end")
        else:  # BOW
            detail.add(top, 6, 9)
            detail.add(top + 1, 6, 6); detail.add(top + 1, 9, 9)
            detail.add(top + 1, 7, 8)
            plan.notes.append("BOW: four-cell knot spanning the apex with two wings")
        plan.free_edges["center_detail"] = set(detail.cells())
    return plan


# ---------------------------------------------------------------------------
# BACK  — the square flap. This is the construction the family lives or dies on.
# ---------------------------------------------------------------------------

def _back(spec) -> ArchitecturePlan:
    d = spec.derived
    plan = ArchitecturePlan("back")
    left, right = d["collar_left"], d["collar_right"]
    depth = d["flap_depth_rows"]
    flap = plan.region("flap_back")
    free, attached = set(), set()

    bottom = min(depth, W - 3)
    for y in range(0, bottom + 1):
        # gentle inward taper over the last three rows so the panel is a
        # trapezoid that hangs, not a rectangle that is pasted on.
        if y >= bottom - 1:
            inset = 2
        elif y >= bottom - 2:
            inset = 1
        else:
            inset = 0
        x0, x1 = left + inset, right - inset
        flap.add(y, x0, x1)
        if y == 0:
            # Row 0 is continuous with the neck/shoulder line: ATTACHED, no outline.
            attached.update({(x, y) for x in range(x0, x1 + 1)})
        else:
            # Side columns are ATTACHED down to the shoulder line, FREE below it,
            # because that is where the panel stops following the body.
            attached.add((x0, y)) if y <= SHOULDER_ROWS else free.add((x0, y))
            attached.add((x1, y)) if y <= SHOULDER_ROWS else free.add((x1, y))
        if y == bottom:
            free.update({(x, y) for x in range(x0, x1 + 1)})

    plan.free_edges["flap_back"] = free
    plan.attached_edges["flap_back"] = attached

    # OCCLUSION: the body row under the hanging bottom edge, and the body cell
    # just outside each free side column. This is the layering proof.
    spans = flap.rows.get(bottom, [])
    for a, b in spans:
        for x in range(a, b + 1):
            if bottom + 1 < W:
                plan.occlusion.add((x, bottom + 1))
    for y in range(SHOULDER_ROWS + 1, bottom + 1):
        for a, b in flap.rows.get(y, []):
            if a - 1 >= 0:
                plan.occlusion.add((a - 1, y))
            if b + 1 < W:
                plan.occlusion.add((b + 1, y))
    plan.notes.append(f"flap rows 0..{bottom}; row 0 attached to the neck line; bottom and lower sides are free edges")
    plan.notes.append("occlusion cast onto the body below the free bottom edge and outside the free side edges")

    # A shallow rear neck band ties the flap to the collar rather than floating it.
    band = plan.region("neck_band_back")
    band.add(0, NECK_GAP[0] - 1, NECK_GAP[1] + 1)
    plan.attached_edges["neck_band_back"] = set(band.cells())
    return plan


# ---------------------------------------------------------------------------
# SIDE — proves front-to-back continuity.
# Front of the body is +x in the right-facing view (measured from installed
# vanilla shirts: the overall bib and the sailor tie both sit at higher x).
# ---------------------------------------------------------------------------

def _side(spec) -> ArchitecturePlan:
    d = spec.derived
    plan = ArchitecturePlan("side")
    depth = d["flap_depth_rows"]
    v = d["v_depth_row"]
    span_extra = {7: 0, 8: 0, 9: 1, 10: 1, 11: 2, 12: 2, 13: 3}.get(d["collar_columns"], 1)

    back_x0, back_x1 = 2, 4 + span_extra          # flap seen edge-on, behind the shoulder
    front_x0, front_x1 = 9 - span_extra, 11       # front leaf seen edge-on, on the chest

    band = plan.region("collar_side")
    free, attached = set(), set()
    # 1. The shoulder band: one continuous run of collar across the whole
    #    shoulder, from the back flap to the front leaf. This single region is
    #    the continuity proof: the same fabric is visible front and back.
    for y in range(0, SHOULDER_ROWS + 1):
        band.add(y, back_x0, front_x1)
        attached.update({(x, y) for x in range(back_x0, front_x1 + 1)})

    # 2. The flap descends at the back, the leaf descends at the front.
    back_depth = min(SHOULDER_ROWS + max(2, depth // 2), W - 4)
    for y in range(SHOULDER_ROWS + 1, back_depth + 1):
        band.add(y, back_x0, back_x1)
        free.add((back_x1, y))
    for y in range(SHOULDER_ROWS + 1, min(SHOULDER_ROWS + max(2, v // 2), W - 4) + 1):
        band.add(y, front_x0, front_x1)
        free.add((front_x0, y))

    free.update({(x, back_depth) for x in range(back_x0, back_x1 + 1)})
    plan.free_edges["collar_side"] = free
    plan.attached_edges["collar_side"] = attached

    for x in range(back_x0, back_x1 + 1):
        if back_depth + 1 < W:
            plan.occlusion.add((x, back_depth + 1))
    plan.notes.append("one collar run crosses the shoulder from the back flap to the front leaf: the continuity proof")
    plan.notes.append(f"back flap tab rows {SHOULDER_ROWS + 1}..{back_depth}, front leaf tab on the chest side")

    if spec.center_detail != "NONE":
        detail = plan.region("center_detail")
        detail.add(SHOULDER_ROWS + max(2, v // 2) + 1, front_x0, front_x0 + 1)
        plan.free_edges["center_detail"] = set(detail.cells())
    return plan


def build_architecture(spec) -> dict[str, ArchitecturePlan]:
    return {"front": _front(spec), "side": _side(spec), "back": _back(spec)}
