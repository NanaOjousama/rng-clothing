"""Hard validation and the identity-salience report.

Every check is generic; family requirements come from template/plan data.
Checks may assert a garment is *valid*; none of them asserts it is *good*.
"""

from __future__ import annotations

from .colorize import distinct_colors
from .compose import ComposeResult
from .data import Library
from .roleimage import DIRECTIONS, SIZE, SRC_NONE, RoleImage


def _components(cells: set[tuple[int, int]]) -> list[int]:
    cells = set(cells); sizes = []
    while cells:
        todo = [cells.pop()]; n = 0
        while todo:
            x, y = todo.pop(); n += 1
            for nb in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nb in cells:
                    cells.remove(nb); todo.append(nb)
        sizes.append(n)
    return sorted(sizes, reverse=True)


def luminance(p) -> float:
    return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def salience(img: RoleImage, frame, piece_index: int) -> dict:
    """Cell count and strongest rendered contrast of one piece against adjacent non-piece cells."""
    cells = [(x, y) for y in range(SIZE) for x in range(SIZE) if img.src[y][x] == piece_index and img.role[y][x]]
    best = 0.0; touched = 0
    for x, y in cells:
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < SIZE and 0 <= ny < SIZE and img.role[ny][nx] and img.src[ny][nx] != piece_index:
                touched += 1
                best = max(best, abs(luminance(frame[y][x]) - luminance(frame[ny][nx])))
    return {"cells": len(cells), "max_contrast": round(best, 1), "boundary_samples": touched}


def validate(result: ComposeResult, frames, lib: Library) -> dict:
    plan = result.plan; contract = lib.contract; checks = []
    template = lib.templates[plan.template] if plan.template else None

    def check(name, ok, detail=None, level="error"):
        checks.append({"check": name, "status": "PASS" if ok else ("WARN" if level == "warn" else "FAIL"), "detail": detail})

    # dimensions / binary alpha (roles are integers; alpha is role != 0 by construction)
    check("dimensions", all(len(f) == SIZE and all(len(r) == SIZE for r in f) for f in frames.values()) and set(frames) == set(DIRECTIONS))
    check("binary_alpha", all(p[3] in (0, 255) for f in frames.values() for r in f for p in r))

    # connectedness
    expected = {d: 1 for d in DIRECTIONS}
    if template: expected.update({("right" if k == "side" else k): v for k, v in template.components.items()})
    comps = {d: _components(result.images[d].alpha()) for d in DIRECTIONS}
    check("connected_components", all(len(comps[d]) == expected[d] for d in DIRECTIONS), {d: comps[d] for d in DIRECTIONS})

    # required coverage (runtime invariant from the vanilla tee)
    missing = {}
    for d in DIRECTIONS:
        key = "side" if d in ("right", "left") else d
        rows = contract["required_coverage"][key]
        if d == "left": rows = [r[::-1] for r in rows]
        miss = [[x, y] for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#" and not result.images[d].role[y][x]]
        if miss: missing[d] = miss
    check("required_coverage", not missing, missing or None)

    # provenance: every opaque cell traces to blank or a piece
    unattributed = {d: [[x, y] for y in range(SIZE) for x in range(SIZE) if img.role[y][x] and img.src[y][x] == SRC_NONE] for d, img in result.images.items()}
    unattributed = {d: v for d, v in unattributed.items() if v}
    check("provenance_complete", not unattributed, unattributed or None)

    # template membership
    if template:
        ids = [p.id for p in plan.pieces]
        check("template_blank", plan.blank == template.blank, {"plan": plan.blank, "template": template.blank})
        check("template_allowed_pieces", all(i in template.allowed for i in ids), [i for i in ids if i not in template.allowed] or None)
        check("template_identity_present", all(i in ids for i in template.identity), [i for i in template.identity if i not in ids] or None)

    # identity pieces painted cells in every view they define
    identity = lib.plan_identity(plan)
    id_fail = {}
    for ap in result.applied:
        if ap.piece.id not in identity: continue
        for view, direction in (("front", "front"), ("side", "right"), ("back", "back")):
            if view in ap.piece.views:
                n = sum(1 for y in range(SIZE) for x in range(SIZE) if result.images[direction].src[y][x] == ap.index and result.images[direction].role[y][x])
                if n == 0: id_fail.setdefault(ap.piece.id, []).append(direction)
    check("identity_pieces_painted", not id_fail, id_fail or None)

    # left mirrors side unless explicit left data exists
    if not result.explicit_left:
        m = result.images["right"].mirrored()
        same = all(m.role == result.images["left"].role and m.slot == result.images["left"].slot for _ in (0,))
        check("left_is_mirror_of_side", same)
    else:
        check("left_explicit_declared", True, "explicit left data present", level="warn")

    # wrap/band pieces appear in all four directions
    wrap_fail = {}
    for ap in result.applied:
        if not ap.piece.wrap: continue
        for d in DIRECTIONS:
            n = sum(1 for y in range(SIZE) for x in range(SIZE) if result.images[d].src[y][x] == ap.index and result.images[d].role[y][x])
            if n == 0: wrap_fail.setdefault(ap.piece.id, []).append(d)
    check("wrap_pieces_all_directions", not wrap_fail, wrap_fail or None)

    # colour budget
    colors = distinct_colors(frames); budget = lib.plan_max_colors(plan)
    check("colour_budget", len(colors) <= budget, {"distinct": len(colors), "budget": budget})

    # sleeve colours
    pal = lib.palettes[plan.palette]
    check("sleeve_slot_in_palette", plan.sleeve_slot in pal.slots, plan.sleeve_slot)

    # reports (never gates)
    check("double_writes", not result.double_writes, result.double_writes or None, level="warn")
    check("skipped_cells", not result.skipped, result.skipped or None, level="warn")

    sal = {}
    for ap in result.applied:
        if ap.piece.id in identity:
            sal[ap.piece.id] = {d: salience(result.images[d], frames[d], ap.index) for d in DIRECTIONS}

    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS"
    return {"plan": plan.id, "status": status, "checks": checks, "salience": sal, "distinct_colors": len(colors),
            "alpha_ops": result.alpha_ops, "explicit_left": result.explicit_left}
