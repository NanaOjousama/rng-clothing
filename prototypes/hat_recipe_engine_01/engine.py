"""Hat recipe engine — prototype 01, v2.

One family recipe (``crown_brim``) builds a 4-view construction template
directly on the target pixel grid from integer/ratio parameters.  Nothing is
drawn large and shrunk; nothing is anti-aliased.

A template is NOT flattened pixels.  Every cell carries
    region  — crown / band / brim_top / brim_under / seam / cast
    role    — O outline, S shadow, M mid, L light, H highlight, C cast
so a downstream generator can repaint by (region, role).

Brim constructions (one recipe, chosen by ``brim_kind``):
    disc   — a ring seen slightly from above: an ellipse (far edge visible beside
             the crown, near edge dipping at the centre) that may droop toward the
             tips (fishing hat lobes) or curl up on one side (soft sun hat).
    skirt  — a brim angled down all round (bucket hat): a row-built trapezoid.

View rules:
    left  = exact mirror of right                       (default, always)
    back  = front silhouette                            (default, back_rule "front_outline")
          | bowl: front crown + brim seen from above/behind, near edge deeper
                                                        (exception, back_rule "bowl";
             evidence: vanilla Fishing 55, Straw 4, Gil's 98, plurffle Sun/Straw)

Screen-space light comes from the upper right in front/back and from the face
side in the right view (left view mirrors it, as vanilla does).
Frame order matches vanilla hats.png: front, right, left, back.  Stdlib only.
"""
from __future__ import annotations

import math

SIZE = 20
CX = 10                      # frame centre lies between columns 9 and 10
VIEWS = ("front", "right", "left", "back")
ROLES = "OSMLHC"
REGIONS = ("crown", "band", "brim_top", "brim_under", "seam", "cast")

# Head span in hat-frame columns (vanilla farmer_base head x3..12, hat drawn at -2,-2).
HEAD_X = (5, 15)


def _rnd(v: float) -> int:
    return int(math.floor(v + 0.5))


def _curve(kind: str, t: float) -> float:
    if kind == "linear":
        return t
    if kind == "bell":
        return t * t
    if kind == "dome":
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

def crown_rows(p, view):
    """{y: (x0, x1)} inclusive, crown above the brim root.

    Bowl back view: the crown's back is nearer the viewer than the brim root, so
    it continues ``bowl_crown_extend`` rows down into the bowl (vanilla Fishing 55)."""
    side = view in ("right", "left")
    extra = p["side_crown_extra"] if side else 0
    top = p["brim_root_y"] - p["crown_h"]
    n = p["crown_h"]
    rows = {}
    for i in range(n):
        t = i / (n - 1) if n > 1 else 1.0
        hw = _rnd(p["crown_top_hw"] + (p["crown_base_hw"] - p["crown_top_hw"]) * _curve(p["crown_curve"], t))
        if i == 0:
            hw -= p["top_round"]
        if i == n - 1:
            hw += p["base_flare"]
        rows[top + i] = (CX - hw - extra, CX + hw - 1)
    if view == "back" and p["back_rule"] == "bowl":
        x0, x1 = rows[top + n - 1]
        for k in range(p["bowl_crown_extend"]):
            rows[top + n + k] = (x0, x1)
    return rows


def _disc_columns(p, view):
    """{x: (top, bottom, part)} for a disc brim.  part: lip | L | R | curl."""
    side = view in ("right", "left")
    root, thick = p["brim_root_y"], p["brim_thick"]
    if side:
        rx_l, rx_r = p["side_brim_back_hw"], p["side_brim_front_hw"]
        dr_l, dr_r = p["side_droop_back"], p["side_droop_front"]
    else:
        rx_l = rx_r = p["brim_hw"]
        dr_l = dr_r = p["brim_droop"]
    curl_side = None
    if p["brim_curl"] and view == "front":
        curl_side = "R"
    elif p["brim_curl"] and view == "back":
        curl_side = "L"                                   # the same flap, seen from behind
    lip_hw = p["lip_hw"]
    cols = {}
    for x in range(CX - rx_l, CX + rx_r):
        dx = x + 0.5 - CX
        s = "L" if dx < 0 else "R"
        rx, droop = (rx_l, dr_l) if s == "L" else (rx_r, dr_r)
        a_c = abs(dx) / rx                                 # pixel centre
        a_e = (abs(dx) + 0.5) / rx                         # pixel outer edge (tip reaches 1)
        e = math.sqrt(max(0.0, 1 - a_c * a_c))
        a0 = p["crown_base_hw"] / rx
        u = max(0.0, (a_e - a0) / max(1e-6, 1 - a0))
        d = _rnd(droop * u ** p["droop_power"])
        top = root - _rnd(p["brim_far"] * e) + _rnd(d * p["brim_top_follow"])
        bot = root + thick - 1 + _rnd(p["brim_near"] * e) + d
        part = "lip" if abs(dx) < lip_hw else s
        if curl_side == s and part != "lip":
            lift = _rnd(p["brim_curl"] * u ** 2)
            top, bot = top - lift, bot - lift // 2       # the flap bends up; its root stays attached
            if lift:
                part = "curl"
        if a_e >= 1 and p["tip_round"]:
            top += 1
            if bot - top >= 3:
                bot -= 1
        cols[x] = (top, bot, part)
    return cols


def _skirt_rows(p, view):
    """{y: (x0, x1)} for a skirt brim angled down all round."""
    side = view in ("right", "left")
    root = p["brim_root_y"]
    out = {}
    for r in range(p["skirt_rows"]):
        hw = p["crown_base_hw"] + p["skirt_out"] + _rnd(r * p["skirt_slope"])
        ext_l = p["side_skirt_back"] if side else 0
        ext_r = p["side_skirt_front"] if side else 0
        out[root + r] = (CX - hw - ext_l, CX + hw - 1 + ext_r)
    return out


def _bowl_bottom(p, x):
    """Back-view exception: the brim's near (back) edge, seen from above and behind."""
    dx = x + 0.5 - CX
    e = math.sqrt(max(0.0, 1 - (abs(dx) / p["brim_hw"]) ** 2))
    return p["brim_root_y"] + p["brim_thick"] - 1 + _rnd(p["bowl_depth"] * e ** p["bowl_power"])


# --------------------------------------------------------------------------- construction

def _paint_crown(g, p, crown, view):
    top = min(crown)
    root = max(crown) + 1                                         # crown base (moves down in a bowl back view)
    band = set(range(root - p["band_h"], root)) if p["band_h"] else set()
    light_right = view != "left"
    for y, (x0, x1) in crown.items():
        w = x1 - x0 + 1
        for x in range(x0, x1 + 1):
            lit_rank = (x1 - x) if light_right else (x - x0)      # 0 = edge on the lit side
            shade_rank = (x - x0) if light_right else (x1 - x)    # 0 = edge on the shadow side
            region = "band" if y in band else "crown"
            if region == "band":
                role = "S" if shade_rank <= 1 else ("L" if lit_rank == 1 else "M")
            elif y == top + 1:                                    # top plane, seen from above
                role = "H" if 2 <= lit_rank <= max(2, w // 2 - 1) else "L"
            elif y == top + 2 and p["crown_h"] >= 5:
                role = "L" if 1 <= lit_rank <= w // 2 else "M"
            elif shade_rank == 1 and y > top + 1:
                role = "S"
            elif y == root - 1 and not band and (shade_rank <= 2 or lit_rank <= 1):
                role = "S"                                        # base crease / flare
            else:
                role = "M"
            g.set(x, y, region, role)


def _paint_disc(g, p, cols, view):
    root = p["brim_root_y"]
    lit_side = "R" if view != "left" else "L"
    back = view == "back" and p["back_rule"] == "bowl"
    for x, (top, bot, part) in cols.items():
        if back:
            bot = max(bot, _bowl_bottom(p, x))
        for y in range(top, bot + 1):
            if g.get(x, y):                                       # crown in front of far brim
                continue
            if back:
                crown_base = root + p["bowl_crown_extend"]
                if y == bot - 1 and bot - top >= 3:
                    role, region = "L", "brim_top"                # near rim catches the light
                elif y <= crown_base and y > top + 1 and abs(x + 0.5 - CX) < p["crown_base_hw"] + 2:
                    role, region = "S", "brim_top"                # brim in the crown's shadow
                elif y <= top + 1 and part == lit_side:
                    role, region = "L", "brim_top"
                else:
                    role, region = "M", "brim_top"
            elif part == "lip":
                if y == root and p["brim_thick"] >= 3:
                    role, region = "S", "brim_top"                # crown base shades the brim
                elif view == "front":
                    role, region = ("H" if lit_side == "R" and 0 < x + 0.5 - CX < p["lip_hw"] - 1 else "L"), "brim_top"
                else:
                    role, region = "L", "brim_top"
            elif part == "curl":
                role, region = ("S", "brim_under") if y == top + 1 else ("M", "brim_top")
            elif y == bot - 1 and bot - top >= 4:
                role, region = "S", "brim_under"                  # lobe turning under
            elif y <= root + 1:
                role, region = ("L" if part == lit_side or y < root else "M"), "brim_top"   # top faces the light
            else:
                role, region = "M", "brim_top"
            g.set(x, y, region, role)


def _paint_skirt(g, p, rows, view):
    root = p["brim_root_y"]
    light_right = view != "left"
    n = len(rows)
    for y, (x0, x1) in rows.items():
        r = y - root
        for x in range(x0, x1 + 1):
            shade_rank = (x - x0) if light_right else (x1 - x)
            lit_rank = (x1 - x) if light_right else (x - x0)
            if r == 0:
                role, region = "S", "brim_top"                    # crease under the crown
            elif p["brim_stitch"] and r == p["brim_stitch"] and shade_rank >= 1 and lit_rank >= 1:
                role, region = ("H" if x % 2 == 0 else "L"), "seam"
            elif shade_rank == 1:
                role, region = "S", "brim_top"
            elif r == n - 2 and view != "back":
                role, region = "S", "brim_under"                  # front edge turns under
            elif r == 1:
                role, region = ("L" if lit_rank >= 1 else "M"), "brim_top"
            else:
                role, region = "M", "brim_top"
            g.set(x, y, region, role)


def _outline(g, crown, cols=None):
    """Outer contour + crown sides against the brim + lobe turn-under lines."""
    solid = g.mask()
    out = set()
    for (x, y) in solid:
        if any((x + dx, y + dy) not in solid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            out.add((x, y))
    for y, (x0, x1) in crown.items():
        out |= {(x0, y), (x1, y)}
    if cols:
        lip = [x for x, c in cols.items() if c[2] == "lip"]
        if lip:
            root, lip_bot = cols[lip[0]][0], cols[lip[0]][1]
            for x in (min(lip) - 1, max(lip) + 1):
                if x in cols and cols[x][1] > lip_bot:            # only where a lobe hangs below the lip
                    out |= {(x, y) for y in range(max(root, cols[x][0]) + 1, lip_bot + 1)}
    for (x, y) in out:
        if g.get(x, y):
            g.set(x, y, g.cells[y][x][0], "O")


def _cast(g, view):
    if view == "back":
        return
    solid = g.mask()
    for x in range(*HEAD_X):
        ys = [y for (xx, y) in solid if xx == x]
        if not ys:
            continue
        if view == "right" and x < CX - 1:                        # cast falls on the face side only
            continue
        y = max(ys) + 1
        if y < SIZE and g.get(x, y) is None:
            g.set(x, y, "cast", "C")


def build_view(p, view):
    if view == "left":
        return build_view(p, "right").mirrored()
    if view == "back" and p["back_rule"] == "front_outline":
        return _construct(p, "front", interior_view="back")
    return _construct(p, view)


def _construct(p, view, interior_view=None):
    iv = interior_view or view
    g = Grid()
    crown = crown_rows(p, view)
    _paint_crown(g, p, crown, iv)
    cols = None
    if p["brim_kind"] == "disc":
        cols = _disc_columns(p, view)
        _paint_disc(g, p, cols, iv)
    else:
        _paint_skirt(g, p, _skirt_rows(p, view), iv)
    _outline(g, crown, cols if iv != "back" else None)
    _cast(g, iv)
    dy = p["side_y_shift"] if view in ("right", "left") else 0
    if dy < 0:
        g.cells = g.cells[-dy:] + [[None] * SIZE for _ in range(-dy)]
    elif dy > 0:
        g.cells = [[None] * SIZE for _ in range(dy)] + g.cells[:-dy]
    return g


def build_template(params: dict) -> dict:
    p = dict(params)
    return {"params": p, "views": {v: build_view(p, v) for v in VIEWS}}


def serialise(tpl: dict, name: str) -> dict:
    """JSON form: per view, a region map (one char per cell) + role map."""
    rcode = {"crown": "c", "band": "b", "brim_top": "t", "brim_under": "u", "seam": "s", "cast": "x"}
    out = {"name": name, "frame": [SIZE, SIZE], "view_order": list(VIEWS),
           "region_codes": {v: k for k, v in rcode.items()},
           "role_codes": {"O": "outline", "S": "shadow", "M": "mid", "L": "light",
                          "H": "highlight", "C": "cast"},
           "view_rules": {"left": "mirror(right)", "back": tpl["params"]["back_rule"]},
           "params": tpl["params"], "views": {}}
    for v, g in tpl["views"].items():
        out["views"][v] = {
            "region": ["".join(rcode[c[0]] if c else "." for c in row) for row in g.cells],
            "role": ["".join(c[1] if c else "." for c in row) for row in g.cells],
        }
    return out
