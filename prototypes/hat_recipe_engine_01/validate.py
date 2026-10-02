"""Automatic validation for crown_brim templates.

Hard checks gate the build; soft checks are reported evidence.  The helmet
metric is calibrated in-run: real vanilla brimmed hats must pass it and two
deliberately helmet-shaped strawmen must fail it, or the metric itself fails.
"""
from __future__ import annotations

from engine import REGIONS, ROLES, SIZE, VIEWS, Grid
from preview import FARMER, read_rgba_png, vanilla_strip

CAST_RGB = (33, 9, 19)


def _res(ok, hard=True, **detail):
    return {"pass": bool(ok), "hard": hard, **detail}


def _solid(grid):
    return grid.mask()


def _strip_mask(strip, vi):
    """Silhouette of a reference strip view (vanilla cast colour excluded)."""
    return {(x, y) for y in range(SIZE) for x in range(SIZE)
            if strip[vi * 20 + y][x][3] and tuple(strip[vi * 20 + y][x][:3]) != CAST_RGB}


def _head_rows():
    """Front-view head half-extents in hat-frame rows: {y: (x0, x1)}."""
    body = read_rgba_png(FARMER / "farmer_base.png")
    rows = {}
    for by in range(32):
        xs = [x for x in range(16) if body[by][x][3]]
        if xs and by <= 12:
            rows[by + 2] = (xs[0] + 2, xs[-1] + 2)
    return rows


HEAD = None


def helmet_metric(mask):
    """Gap profile between hat outline and head outline, per head row the hat covers.

    gap(y) = hat half-extent beyond the head on the narrower side.  A helmet hugs the
    head at a constant gap; a hat lifts off it (crown above the head) and breaks
    outward at the brim (gap jumps)."""
    global HEAD
    HEAD = HEAD or _head_rows()
    gaps = []
    for y, (h0, h1) in sorted(HEAD.items()):
        xs = [x for (x, yy) in mask if yy == y]
        if not xs:
            continue
        gaps.append(min(h0 - min(xs), max(xs) - h1))
    top = min(y for (_, y) in mask) if mask else SIZE
    head_top = min(HEAD)
    if not gaps:
        return {"max_gap": 0, "spread": 0, "lift": 0, "helmet": True}
    m = {"max_gap": max(gaps), "spread": max(gaps) - min(gaps), "lift": head_top - top}
    m["helmet"] = not (m["max_gap"] >= 2 and m["spread"] >= 1 and m["lift"] >= 2)
    return m


def _strawman(offset):
    """Helmet: the head outline dilated by `offset`, covering down to the brow."""
    global HEAD
    HEAD = HEAD or _head_rows()
    head = {(x, y) for y, (a, b) in HEAD.items() for x in range(a, b + 1) if y <= 11}
    out = set(head)
    for _ in range(offset):
        out |= {(x + dx, y + dy) for (x, y) in out for dx, dy in ((1, 0), (-1, 0), (0, -1))}
    return out


def _lip_bottom(mask):
    """Lowest hat row in the two centre columns (where the brim lip sits on the face)."""
    return max(y for (x, y) in mask if x in (9, 10))


VANILLA_LIPS = {f"{n} ({i})": _lip_bottom(_strip_mask(vanilla_strip(i), 0))
                for n, i in (("Bucket Hat", 102), ("Fishing Hat", 55), ("Straw Hat", 4))}


def _iou(a, b):
    return len(a & b) / max(1, len(a | b))


def check_variant(name, tpl, bank):
    v = tpl["views"]
    p = tpl["params"]
    checks = {}

    bad = [(vw, x, y) for vw in VIEWS for y in range(SIZE) for x in range(SIZE)
           if v[vw].cells[y][x] and (v[vw].cells[y][x][0] not in REGIONS or v[vw].cells[y][x][1] not in ROLES)]
    checks["grid_and_codes"] = _res(not bad and all(len(v[vw].cells) == SIZE for vw in VIEWS), bad=bad[:5])

    checks["left_mirrors_right"] = _res(v["left"].cells == v["right"].mirrored().cells)
    if p["back_rule"] == "front_outline":
        checks["back_view_rule"] = _res(_solid(v["back"]) == _solid(v["front"]), rule="back silhouette == front")
    else:   # bowl exception: same crown top and brim span as the front, and it must reach lower (seen from above)
        fb, bb = _solid(v["front"]), _solid(v["back"])
        span = lambda m: (min(x for x, _ in m), max(x for x, _ in m), min(y for _, y in m))
        checks["back_view_rule"] = _res(span(fb) == span(bb) and max(y for _, y in bb) > max(y for _, y in fb),
                                        rule="bowl: same width/top as front, deeper", front=span(fb), back=span(bb))

    open_edges = []
    for vw in VIEWS:
        s = _solid(v[vw])
        for (x, y) in s:
            if any((x + dx, y + dy) not in s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) \
                    and v[vw].cells[y][x][1] != "O":
                open_edges.append((vw, x, y))
    checks["outline_closed"] = _res(not open_edges, open=open_edges[:5])

    orphans = []
    for vw in VIEWS:
        s = _solid(v[vw])
        for (x, y) in s:
            n = sum((x + dx, y + dy) in s for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
            if n < 2:
                orphans.append((vw, x, y))
    checks["no_orphan_pixels"] = _res(not orphans, orphans=orphans[:5])

    def span(vw):
        ys = [y for (_, y) in _solid(v[vw])]
        return min(ys), max(ys)
    (ft, fb), (st, sb) = span("front"), span("right")
    checks["front_side_height_agree"] = _res(abs(ft - st) <= 1 and abs(fb - sb) <= 1,
                                             front=[ft, fb], side=[st, sb])

    centre_bottom = _lip_bottom(_solid(v["front"]))
    lo, hi = min(VANILLA_LIPS.values()), max(VANILLA_LIPS.values())
    checks["seating_vs_vanilla"] = _res(3 <= ft and lo <= centre_bottom <= hi,
                                        crown_top=ft, front_lip_bottom=centre_bottom,
                                        vanilla_lip_bottom=VANILLA_LIPS)

    need = {"crown", "brim_top"} | ({"band"} if p["band_h"] else set())
    missing = {vw: sorted(need - {c[0] for r in v[vw].cells for c in r if c}) for vw in VIEWS}
    missing = {k: m for k, m in missing.items() if m}
    roles_used = sorted({c[1] for r in v["front"].cells for c in r if c})
    checks["regions_and_roles_present"] = _res(not missing and {"O", "S", "M", "L"} <= set(roles_used),
                                               missing=missing, front_roles=roles_used)

    hm = helmet_metric(_solid(v["front"]))
    checks["not_helmet"] = _res(not hm["helmet"], **hm)

    scores = []
    for label, strip in bank.items():
        s = sum(_iou(_solid(v[vw]), _strip_mask(strip, i)) for i, vw in enumerate(VIEWS)) / 4
        scores.append((round(s, 3), label))
    scores.sort(reverse=True)
    checks["nearest_references"] = _res(True, hard=False, top5=scores[:5])
    return {"checks": checks}


def validate_all(tpls, bank):
    report = {"variants": {n: check_variant(n, t, bank) for n, t in tpls.items()}, "family": {}}

    names = list(tpls)
    pairs = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = tpls[names[i]]["views"], tpls[names[j]]["views"]
            iou = (_iou(a["front"].mask(), b["front"].mask()) + _iou(a["right"].mask(), b["right"].mask())) / 2
            pairs[f"{names[i]}~{names[j]}"] = round(iou, 3)
    report["family"]["variants_distinct"] = _res(all(x < 0.85 for x in pairs.values()),
                                                 detail=f"front+side silhouette IoU {pairs}", iou=pairs)

    calib = {}
    for label, idx in (("vanilla Bucket Hat 102", 102), ("vanilla Fishing Hat 55", 55),
                       ("vanilla Straw Hat 4", 4), ("vanilla Cowboy Hat 0", 0)):
        calib[label] = helmet_metric(_strip_mask(vanilla_strip(idx), 0))
    for off in (1, 2):
        calib[f"strawman head+{off}px shell"] = helmet_metric(_strawman(off))
    ok = all(not m["helmet"] for k, m in calib.items() if k.startswith("vanilla")) and \
        all(m["helmet"] for k, m in calib.items() if k.startswith("strawman"))
    report["family"]["helmet_metric_calibrated"] = _res(
        ok, detail="vanilla brimmed hats pass, head-shell strawmen fail" if ok else "metric does not separate", calib=calib)
    return report
