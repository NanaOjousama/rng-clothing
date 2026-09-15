"""Material-mask thickness gate: a treatment stroke is one logical pixel thick.

Checking the edit operations is not enough. "Every edit touched a single cell"
says nothing about the line the eye reads: a treatment cell landing beside a
structural pixel of the same (or deeper) tone reads as ONE stroke with it, and
two such cells side by side make a two-pixel line. So this validates the FINAL
TREATMENT MASK against the pixels it actually lands on.

A treatment is rejected when it produces:

  mask_2x2    four treatment cells in a 2x2 block
  merge       a treatment cell whose neighbour ACROSS its stroke is a structural
              pixel reading as the same stroke -> a two-cell-wide line
  merged_2x2  a 2x2 block made of treatment cells plus structural cells that
              merge with them

Stroke direction comes from the mask: a cell with treatment neighbours
left/right runs horizontally, up/down vertically. A crossing runs both ways and
has no "across"; an isolated dot is checked on all four sides. "Reads as the
same stroke" means same polarity as the line (a dark line merges with anything
as dark or darker, within TOL L*; a light line with anything as light or
lighter). The silhouette outline (an opaque cell with a transparent
4-neighbour) is never a merge partner -- lines run into it in the reference too.

Calibration, run by default: synthetic cases that must pass and must fail; the
hat_8 reference's line mask must pass; the shipped beret_03 plaid must FAIL.

    python3 tools/validate_material_mask.py               # self-tests + calibration
    python3 tools/validate_material_mask.py --generator   # every family base x treatment x palette
    python3 tools/validate_material_mask.py --image T.png --felt beret_03:CUTE_COCOA_GOLD [--out DIR]
    python3 tools/validate_material_mask.py --image T.png --base B.png [--out DIR]
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from v5 import authored
from v5.pngio import blank_image, blit, nearest_scale, read_rgba_png, write_rgba_png

REFERENCE = os.path.join(ROOT, "BERET_MATERIAL⁄PATTERN REFERENCE", "Hats", "hat_8", "hat.png")
SHIPPED_PLAID = os.path.join(ROOT, "test-packs", "fashionsense", "RNG-Beret03-Base", "Hats",
                             "Beret03PlaidCocoaGold", "hat.png")
TOL = 2.0       # L* within which a neighbour reads as part of the same stroke
LINE_T = 3.0    # L* a reference line cell sits below both flanks
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def lstar(c):
    f = lambda v: ((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92
    y = 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])
    return 116 * y ** (1 / 3) - 16 if y > 0.008856 else 903.3 * y


class Sheet:
    """A sprite sheet split into square frames; neighbours never cross frames."""

    def __init__(self, px, frame_h=None):
        self.px, self.w, self.h = px, len(px[0]), len(px)
        self.fh = frame_h or self.w

    def at(self, p, d):
        x, y = p[0] + d[0], p[1] + d[1]
        if not (0 <= x < self.w and 0 <= y < self.h) or y // self.fh != p[1] // self.fh:
            return None
        return (x, y) if self.px[y][x][3] else None

    def outline(self, p):
        return any(self.at(p, d) is None for d in N4)

    def L(self, p):
        return lstar(self.px[p[1]][p[0]])

    def opaque_cells(self):
        return [(x, y) for y in range(self.h) for x in range(self.w) if self.px[y][x][3]]


def mask_from_diff(img: Sheet, base: Sheet):
    """Treatment mask = cells whose colour differs from the untreated render.
    Returns (mask, polarity); raises if the silhouette itself changed."""
    if (img.w, img.h) != (base.w, base.h):
        raise ValueError(f"size differs: {img.w}x{img.h} vs {base.w}x{base.h}")
    mask, pol = set(), {}
    for y in range(img.h):
        for x in range(img.w):
            a, b = img.px[y][x], base.px[y][x]
            if (a[3] > 0) != (b[3] > 0):
                raise ValueError(f"silhouette differs at ({x},{y}) -- not a treatment")
            if a[3] and a[:3] != b[:3]:
                mask.add((x, y))
                pol[(x, y)] = -1 if lstar(a) < lstar(b) else 1
    return mask, pol


def extract_dark_lines(s: Sheet, t=LINE_T):
    """Reference line cells: interior cells darker than BOTH flanks on an axis.
    Thin by construction, so it is paired with two_wide_valleys() below, which
    looks for exactly the lines this extraction would silently miss.

    Also returns each cell's ACROSS axis -- the one whose flanks are lighter. A
    line running beside the outline is found only where its flanks are both
    body, so it can come out as isolated cells; without the axis, the next cell
    ALONG that line would be misread as a neighbour across it."""
    mask, across = set(), {}
    for p in s.opaque_cells():
        if s.outline(p):
            continue
        for axis, (a, b) in (("h", ((-1, 0), (1, 0))), ("v", ((0, -1), (0, 1)))):
            qa, qb = s.at(p, a), s.at(p, b)
            if qa and qb and s.L(qa) - s.L(p) >= t and s.L(qb) - s.L(p) >= t:
                mask.add(p)
                across[p] = across.get(p, "") + axis
    return mask, {p: -1 for p in mask}, across


def two_wide_valleys(s: Sheet, t=LINE_T, tol=TOL):
    """Pairs of like-toned interior cells that are both darker than the cells
    flanking the pair: a two-pixel-wide dark line."""
    found = []
    for p in s.opaque_cells():
        for d in ((1, 0), (0, 1)):
            q = s.at(p, d)
            if not q or s.outline(p) or s.outline(q) or abs(s.L(p) - s.L(q)) > tol:
                continue
            fa, fb = s.at(p, (-d[0], -d[1])), s.at(q, d)
            if fa and fb and min(s.L(fa), s.L(fb)) - max(s.L(p), s.L(q)) >= t:
                found.append((p, q))
    return found


def _merges(s, mask, pol, p, q, tol):
    if q is None or q in mask or s.outline(q):
        return False
    return s.L(q) <= s.L(p) + tol if pol[p] < 0 else s.L(q) >= s.L(p) - tol


def violations(s: Sheet, mask, pol, tol=TOL, across_hint=None):
    """across_hint: {cell: "h" | "v" | "hv"} from extract_dark_lines -- used only
    for a cell the mask alone leaves directionless. A treatment mask built from a
    diff has no hint, so its lone dots are checked on all four sides."""
    out = []
    for p in sorted(mask, key=lambda c: (c[1], c[0])):
        h = any(s.at(p, d) in mask for d in ((1, 0), (-1, 0)))
        v = any(s.at(p, d) in mask for d in ((0, 1), (0, -1)))
        if not (h or v) and across_hint and p in across_hint:
            v, h = "h" in across_hint[p], "v" in across_hint[p]
        across = () if h and v else (((0, -1), (0, 1)) if h else (((-1, 0), (1, 0)) if v else N4))
        for d in across:
            q = s.at(p, d)
            if _merges(s, mask, pol, p, q, tol):
                out.append(("merge", p, q))
    merged = set(mask)
    for p in mask:
        merged.update(q for d in N8 if _merges(s, mask, pol, p, q := s.at(p, d), tol))
    for (x, y) in sorted(merged, key=lambda c: (c[1], c[0])):
        block = [(x, y), s.at((x, y), (1, 0)), s.at((x, y), (0, 1)), s.at((x, y), (1, 1))]
        if None in block or not all(c in merged for c in block):
            continue
        if all(c in mask for c in block):
            out.append(("mask_2x2", (x, y), None))
        elif any(c in mask for c in block):
            out.append(("merged_2x2", (x, y), None))
    return out


def view_of(s: Sheet, p):
    i = p[1] // s.fh
    order = authored.ATLAS_ORDER
    return order[i] if s.fh == 20 and s.h == 80 and i < len(order) else f"frame{i}"


def describe(s, v):
    kind, p, q = v
    at = f"{view_of(s, p)} ({p[0]},{p[1] % s.fh}) sheet({p[0]},{p[1]})"
    return f"{kind:10} {at}" + (f" with sheet({q[0]},{q[1]})" if q else "")


def mask_images(s: Sheet, mask, viol, out_dir, name, scale=8):
    """<name>_mask.png at native size and _mask_x8.png: silhouette pale grey,
    treatment cells black; the x8 copy marks every violating cell red."""
    img = blank_image(s.w, s.h, (255, 255, 255, 255))
    for (x, y) in s.opaque_cells():
        img[y][x] = (205, 205, 205, 255)
    for (x, y) in mask:
        img[y][x] = (0, 0, 0, 255)
    os.makedirs(out_dir, exist_ok=True)
    write_rgba_png(os.path.join(out_dir, f"{name}_mask.png"), img)
    bad = set()
    for kind, p, q in viol:
        if kind == "merge":
            bad.update((p, q))
        else:
            bad.update(c for c in (p, s.at(p, (1, 0)), s.at(p, (0, 1)), s.at(p, (1, 1))) if c)
    big = nearest_scale(img, scale)
    for (x, y) in bad:
        red = (230, 30, 30, 255) if (x, y) in mask else (255, 150, 150, 255)
        for j in range(scale):
            for i in range(scale):
                big[y * scale + j][x * scale + i] = red
    write_rgba_png(os.path.join(out_dir, f"{name}_mask_x8.png"), big)


# --- generator renders ---------------------------------------------------------

def render_sheet(lib, base, palette, treatment):
    dirs, _ = authored._render(base, (), palette, lib.tone_for(base), treatment)
    img = blank_image(base.size[0], base.size[1] * len(authored.ATLAS_ORDER))
    for i, view in enumerate(authored.ATLAS_ORDER):
        blit(img, dirs[view], 0, i * base.size[1])
    return img


def _base(lib, shape):
    b = next((b for b in lib.bases if getattr(b, "shape_variant", None) == shape or b.name == shape), None)
    if b is None:
        raise SystemExit(f"no authored base {shape!r}")
    return b


def _palette(lib, pid):
    p = next((p for p in lib.palettes if p.id == pid), None)
    if p is None:
        raise SystemExit(f"no curated palette {pid!r}")
    return p


# --- runs -------------------------------------------------------------------------

FAILS, CHECKS = [], [0]


def check(name, cond, detail=""):
    CHECKS[0] += 1
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        FAILS.append(name)


def _synthetic(rows, light=False):
    """'#' outline, '.' body, 's' shade (darker), 'h' highlight (lighter),
    'm' treatment mark. Polarity is dark unless light=True."""
    col = {"#": (30, 30, 30, 255), ".": (150, 150, 150, 255), "s": (110, 110, 110, 255),
           "h": (215, 215, 215, 255), "m": ((215, 215, 215, 255) if light else (110, 110, 110, 255))}
    px = [[col[c] for c in r] for r in rows]
    s = Sheet(px, len(rows))
    mask = {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "m"}
    return s, mask, {p: (1 if light else -1) for p in mask}


SELF_TESTS = [
    ("plus crossing passes", True, False,
     ["#######", "#..m..#", "#..m..#", "#mmmmm#", "#..m..#", "#.....#", "#######"]),
    ("staircase diagonal passes", True, False,
     ["#######", "#mm...#", "#.mm..#", "#..mm.#", "#.....#", "#.....#", "#######"]),
    ("line ending into shade along its run passes", True, False,
     ["#######", "#.....#", "#mmmss#", "#.....#", "#.....#", "#.....#", "#######"]),
    ("two-wide stroke fails", False, False,
     ["#######", "#.....#", "#mmmm.#", "#mmmm.#", "#.....#", "#.....#", "#######"]),
    ("line with same-tone shade directly below fails", False, False,
     ["#######", "#.....#", "#mmmm.#", "#ssss.#", "#.....#", "#.....#", "#######"]),
    ("dot beside shade fails", False, False,
     ["#######", "#.....#", "#..ms.#", "#.....#", "#.....#", "#.....#", "#######"]),
    ("vertical line beside shade fails", False, False,
     ["#######", "#.ms..#", "#.m...#", "#.m...#", "#.....#", "#.....#", "#######"]),
    ("light line beside highlight fails", False, True,
     ["#######", "#hhhh.#", "#mmmm.#", "#.....#", "#.....#", "#.....#", "#######"]),
    ("light line beside darker shade passes", True, True,
     ["#######", "#ssss.#", "#mmmm.#", "#.....#", "#.....#", "#.....#", "#######"]),
]


def run_default():
    print("self-tests")
    for name, should_pass, light, rows in SELF_TESTS:
        s, mask, pol = _synthetic(rows, light)
        v = violations(s, mask, pol)
        check(name, (not v) == should_pass, "; ".join(k for k, _, _ in v) or "clean")

    print("calibration: hat_8 reference line mask")
    ref = Sheet(read_rgba_png(REFERENCE))
    rmask, rpol, raxis = extract_dark_lines(ref)
    rv = violations(ref, rmask, rpol, across_hint=raxis)
    check("reference yields a line mask", len(rmask) >= 40, f"{len(rmask)} cells")
    # Measured on the back view, where the plaid lies on an open crown field.
    # The profile brims taper to a 2-3 cell tip between outlines; there a
    # local-minimum rule cannot tell a line from rim shading, so those views are
    # reported, not gated. That is a limit of extraction, not a claim about hat_8.
    back = [v for v in rv if view_of(ref, v[1]) == "back"]
    check("reference back-view line mask is 1px everywhere", not back,
          "; ".join(describe(ref, v) for v in back[:6]) or
          f"{len(rv)} unmeasurable elsewhere: " + ", ".join(describe(ref, v).split()[1] for v in rv))
    # hat_8 has exactly one two-wide dark feature: the pale-rose pair either side
    # of the centre crossing on the back crown (x 9-10). That is the crown-centre
    # mark -- structure, like beret_03's own dimple -- not a material stroke. Any
    # other valley would be a line the extraction is hiding.
    valleys = two_wide_valleys(ref)
    stray = [(p, q) for p, q in valleys
             if not (view_of(ref, p) == "back" and {p[0], q[0]} <= {9, 10})]
    check("reference's only two-wide dark feature is the crown-centre mark", not stray,
          f"{len(valleys)} centre pairs, {len(stray)} elsewhere")

    print("calibration: shipped beret_03 plaid must be rejected")
    lib = authored.load()
    base, pal = _base(lib, "beret_03"), _palette(lib, "CUTE_COCOA_GOLD")
    plaid = render_sheet(lib, base, pal, lib.treatment("plaid"))
    felt = render_sheet(lib, base, pal, lib.treatment("felt"))
    if os.path.exists(SHIPPED_PLAID):
        check("generator plaid render == shipped pack sheet", plaid == read_rgba_png(SHIPPED_PLAID))
    ps = Sheet(plaid)
    pmask, ppol = mask_from_diff(ps, Sheet(felt))
    pv = violations(ps, pmask, ppol)
    check("shipped plaid is rejected", bool(pv), f"{len(pv)} violations over {len(pmask)} cells")

    print(f"\n{CHECKS[0] - len(FAILS)}/{CHECKS[0]} checks passed")
    return 1 if FAILS else 0


def run_generator():
    lib = authored.load()
    bad = 0
    for base in sorted(lib.bases, key=lambda b: b.name):
        felt_cache = {}
        for tname, treat in sorted((lib.treatments or {}).items()):
            if treat.rule == "plain":
                continue
            fails = []
            for pal in lib.palettes:
                if not set(base.style) & set(pal.style):
                    continue
                felt = felt_cache.setdefault(pal.id, render_sheet(lib, base, pal, None))
                s = Sheet(render_sheet(lib, base, pal, treat))
                mask, pol = mask_from_diff(s, Sheet(felt))
                v = violations(s, mask, pol)
                if v:
                    fails.append((pal.id, len(v), describe(s, v[0])))
            status = "FAIL" if fails else "PASS"
            bad += bool(fails)
            print(f"  {status}  {base.name:14} {tname:9}" +
                  (f"  {len(fails)} palettes, e.g. {fails[0][0]}: {fails[0][1]} x, first {fails[0][2]}"
                   if fails else ""))
    print(f"\n{bad} base x treatment combinations produce over-thick material")
    return 1 if bad else 0


def run_image(args):
    img = Sheet(read_rgba_png(args.image))
    if args.base:
        base_px = read_rgba_png(args.base)
    else:
        shape, pid = args.felt.split(":")
        lib = authored.load()
        base_px = render_sheet(lib, _base(lib, shape), _palette(lib, pid), None)
    mask, pol = mask_from_diff(img, Sheet(base_px))
    v = violations(img, mask, pol)
    print(f"{args.image}: {len(mask)} treatment cells, {len(v)} violations")
    for x in v:
        print("  " + describe(img, x))
    if args.out:
        name = os.path.splitext(os.path.basename(args.image))[0]
        mask_images(img, mask, v, args.out, name)
        print(f"  mask images -> {args.out}/{name}_mask.png, _mask_x8.png")
    return 1 if v else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--generator", action="store_true", help="check every base x treatment x palette")
    ap.add_argument("--image", help="treated sheet to check")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--base", help="the same sheet without the treatment")
    g.add_argument("--felt", help="SHAPE:PALETTE -- render the untreated sheet from the library")
    ap.add_argument("--reference", help="extract and check a reference sheet's dark line mask")
    ap.add_argument("--out", help="write native and x8 mask images here")
    args = ap.parse_args()
    if args.reference:
        s = Sheet(read_rgba_png(args.reference))
        mask, pol, axis = extract_dark_lines(s)
        v = violations(s, mask, pol, across_hint=axis)
        print(f"{args.reference}: {len(mask)} line cells, {len(v)} violations, "
              f"{len(two_wide_valleys(s))} two-wide valleys")
        for x in v:
            print("  " + describe(s, x))
        if args.out:
            mask_images(s, mask, v, args.out, "reference")
        return 1 if v else 0
    if args.image:
        if not (args.base or args.felt):
            ap.error("--image needs --base or --felt")
        return run_image(args)
    return run_generator() if args.generator else run_default()


if __name__ == "__main__":
    sys.exit(main())
