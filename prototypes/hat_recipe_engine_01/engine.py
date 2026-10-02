"""Hat recipe engine — prototype 01.

One family recipe (``crown_brim``) builds a 4-view construction template
directly on the target pixel grid from a handful of integer parameters.
Nothing is drawn large and shrunk; nothing is anti-aliased.

A template is NOT flattened pixels.  Every cell carries
    region  — what the cell is made of (crown / band / brim_top / brim_under / cast)
    role    — how it is shaded       (O outline, S shadow, M mid, L light, H highlight, C cast)
so a downstream generator can repaint by (region, role) without re-deriving
structure.

View rules (defaults, per the prototype brief):
    left  = exact horizontal mirror of right
    back  = same silhouette as front; only interior roles differ
Family exceptions are expressed as explicit recipe keys, never silent code paths.

Frame order matches vanilla hats.png: front, right, left, back.
Dependency-free (stdlib only).
"""
from __future__ import annotations

import math

SIZE = 20
CX = 10                      # frame centre lies between columns 9 and 10
VIEWS = ("front", "right", "left", "back")
ROLES = "OSMLHC"
REGIONS = ("crown", "band", "brim_top", "brim_under", "cast")

# Head span in hat-frame columns (vanilla farmer_base head x3..12, hat drawn at -2,-2).
HEAD_X = (5, 15)


def _rnd(v: float) -> int:
    return int(math.floor(v + 0.5))


def _curve(kind: str, t: float) -> float:
    if kind == "linear":
        return t
    if kind == "bell":                       # widens late: tall soft crown flaring at the base
        return t * t
    if kind == "dome":                       # widens early: round crown
        return math.sqrt(t)
    raise ValueError(f"unknown crown curve {kind!r}")


class Grid:
    def __init__(self):
        self.cells = [[None] * SIZE for _ in range(SIZE)]   # (region, role) | None

    def get(self, x, y):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            return self.cells[y][x]
        return None

    def set(self, x, y, region, role):
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.cells[y][x] = (region, role)

    def mask(self, include_cast=False):
        return {(x, y) for y in range(SIZE) for x in range(SIZE)
                if self.cells[y][x] and (include_cast or self.cells[y][x][0] != "cast")}

    def mirrored(self):
        g = Grid()
        g.cells = [list(reversed(r)) for r in self.cells]
        return g


# --------------------------------------------------------------------------- geometry

def _crown_rows(p, view):
    """{y: (x0, x1)} inclusive, for the crown above the brim root."""
    side = view in ("right", "left")
    shift = -p["side_crown_shift"] if side else 0
    extra = p["side_crown_extra"] if side else 0
    top = p["brim_root_y"] - p["crown_h"]
    rows = {}
    n = p["crown_h"]
    for i in range(n):
        t = i / (n - 1) if n > 1 else 1.0
        hw = p["crown_top_hw"] + (p["crown_base_hw"] - p["crown_top_hw"]) * _curve(p["crown_curve"], t)
        hw = _rnd(hw)
        if i == 0:
            hw -= p["top_round"]
        rows[top + i] = (CX + shift - hw - extra, CX + shift + hw - 1)
    return rows


def _brim_columns(p, view):
    """{x: (y_top, y_bottom, droop_px, part)} inclusive.

    Vanilla grammar (Fishing Hat 55, Straw Hat 4, Bucket Hat 102): seen from the
    front a brim is a short central LIP (the part in front of the face, high, with
    the cast shadow under it) flanked by two LOBES (the brim's sides seen edge-on,
    which hang lower and read as the bowl of the brim).  part in {'lip','L','R'}.
    """
    side_view = view in ("right", "left")
    shift = -p["side_crown_shift"] if side_view else 0
    if side_view:
        bl, br = CX - p["side_brim_back_hw"], CX + p["side_brim_front_hw"] - 1
        droop_l, droop_r = p["side_droop_back"], p["side_droop_front"]
    else:
        bl, br = CX - p["brim_hw"], CX + p["brim_hw"] - 1
        droop_l = droop_r = p["brim_droop"]
    root, thick, tilt = p["brim_root_y"], p["brim_thick"], p["brim_tilt"]
    lip_l, lip_r = CX + shift - p["lip_hw"], CX + shift + p["lip_hw"] - 1
    lip_bottom = root + thick - 1
    cols = {}
    for x in range(bl, br + 1):
        if lip_l <= x <= lip_r:
            cols[x] = (root, lip_bottom, 0, "lip")
            continue
        if x < lip_l:
            k, n, droop, part = lip_l - x, lip_l - bl, droop_l, "L"
        else:
            k, n, droop, part = x - lip_r, br - lip_r, droop_r, "R"
        u = k / max(1, n)
        d = max(1, _rnd(droop * u ** p["droop_power"])) if droop else 0
        y0 = root - tilt + _rnd(d * p["brim_top_follow"])
        y1 = lip_bottom + d
        if k == n and p["tip_round"]:
            y0 += 1                                   # round the brim tip
            if y1 - y0 >= 3:
                y1 -= 1
        cols[x] = (y0, y1, d, part)
    return cols


# --------------------------------------------------------------------------- shading

def _shade_crown(g, p, crown, view):
    top = min(crown)
    root = p["brim_root_y"]
    band_rows = set(range(root - p["band_h"], root)) if p["band_h"] else set()
    for y, (x0, x1) in crown.items():
        for x in range(x0, x1 + 1):
            region = "band" if y in band_rows else "crown"
            interior_rank = min(x - x0, x1 - x)     # 0 = edge column
            if region == "band":
                role = "S" if interior_rank <= 1 else "M"
            elif y == top + 1:
                role = "L" if interior_rank <= 1 else "H"
            elif y == top + 2 and p["crown_h"] >= 5:
                role = "L" if interior_rank >= 2 else "M"
            elif interior_rank == 1 and y >= root - 2:
                role = "S"
            else:
                role = "M"
            g.set(x, y, region, role)


def _shade_brim(g, p, cols, view):
    front_part = "R" if view == "right" else None
    root = p["brim_root_y"]
    for x, (y0, y1, d, part) in cols.items():
        for y in range(y0, y1 + 1):
            if g.get(x, y) and y < root:           # crown stands in front of the brim's far half
                continue
            if part == "lip":
                if y == root and p["brim_thick"] >= 3:
                    role, region = "S", "brim_top"           # crown base occludes the brim
                elif y == root:
                    role, region = "L", "brim_top"           # thin lip: vanilla lights its top (Straw Hat 4)
                else:
                    role, region = ("L" if view == "front" else "M"), "brim_top"
            elif y >= y1 - 1 and y > y0 + 1 and (d > 0 or part == front_part):
                role, region = "S", "brim_under"             # lobe underside
            elif y == y0 + 1 or (y == y0 and y < root):
                role, region = "L", "brim_top"
            else:
                role, region = "M", "brim_top"
            g.set(x, y, region, role)


def _lip_dividers(cols):
    """The line where each lobe turns under, beside the lip (vanilla Fishing Hat x6/x13)."""
    out = set()
    lip = [x for x, c in cols.items() if c[3] == "lip"]
    if not lip:
        return out
    root, lip_bottom = cols[lip[0]][0], cols[lip[0]][1]
    for x in (min(lip) - 1, max(lip) + 1):
        if x in cols:
            out |= {(x, y) for y in range(root + 1, lip_bottom + 1)}
    return out


def _outline(g, crown, extra=()):
    """Outer contour + crown sides where the crown stands against the brim + brim dividers."""
    solid = g.mask()
    out = set()
    for (x, y) in solid:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in solid:
                out.add((x, y))
    for y, (x0, x1) in crown.items():
        for x in (x0, x1):
            out.add((x, y))
    out |= {c for c in extra if g.get(*c)}
    for (x, y) in out:
        region = g.cells[y][x][0]
        g.set(x, y, region, "O")


def _cast(g, view):
    if view == "back":
        return
    solid = g.mask()
    for x in range(*HEAD_X):
        ys = [y for (xx, y) in solid if xx == x]
        if not ys:
            continue
        y = max(ys) + 1
        if view == "right" and x < CX - 1:      # cast falls on the face side only
            continue
        if g.get(x, y) is None and y < SIZE:
            g.set(x, y, "cast", "C")


# --------------------------------------------------------------------------- build

def build_view(p, view):
    if view == "left":
        return build_view(p, "right").mirrored()
    if view == "back" and p.get("back_rule", "front_outline") == "front_outline":
        front = build_view(p, "front")
        g = Grid()
        crown = _crown_rows(p, "front")
        _shade_crown(g, p, crown, "back")
        cols = _brim_columns(p, "front")
        _shade_brim(g, p, cols, "back")
        _outline(g, crown, _lip_dividers(cols))
        assert g.mask() == front.mask(), "back silhouette must equal front"
        return g
    g = Grid()
    crown = _crown_rows(p, view)
    _shade_crown(g, p, crown, view)
    cols = _brim_columns(p, view)
    _shade_brim(g, p, cols, view)
    _outline(g, crown, _lip_dividers(cols))
    _cast(g, view)
    return g


def build_template(params: dict) -> dict:
    p = dict(params)
    views = {v: build_view(p, v) for v in VIEWS}
    return {"params": p, "views": views}


def serialise(tpl: dict, name: str) -> dict:
    """JSON form: per view, a region map (one char per cell) + role map."""
    rcode = {"crown": "c", "band": "b", "brim_top": "t", "brim_under": "u", "cast": "x"}
    out = {"name": name, "frame": [SIZE, SIZE], "view_order": list(VIEWS),
           "region_codes": {v: k for k, v in rcode.items()},
           "role_codes": {"O": "outline", "S": "shadow", "M": "mid", "L": "light",
                          "H": "highlight", "C": "cast"},
           "view_rules": {"left": "mirror(right)", "back": tpl["params"].get("back_rule", "front_outline")},
           "params": tpl["params"], "views": {}}
    for v, g in tpl["views"].items():
        out["views"][v] = {
            "region": ["".join(rcode[c[0]] if c else "." for c in row) for row in g.cells],
            "role": ["".join(c[1] if c else "." for c in row) for row in g.cells],
        }
    return out
