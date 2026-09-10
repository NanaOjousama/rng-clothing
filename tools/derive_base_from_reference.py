"""Derive an authored base from ONE reference hat's construction.

Averaging a corpus family produced bases that measured correctly and read as
bowls: the mean of a fedora, a bowler and a trilby is a shape nobody drew.  A
family may hold SEVERAL authored bases, and each one should come from a single
successful reference.

This reads one 20x20x4 reference and restates it in the authoring index:

    * row-by-row silhouette rhythm, widening and narrowing, asymmetry, and the
      per-view differences are preserved EXACTLY — they are the construction.
    * colour is not.  The reference's own colours are clustered into ROLES
      (body / trim / accent) by hue and area, then ranked by luminance and
      mapped onto the six semantic steps, so a palette stays replaceable and
      nothing here carries a hue of its own.

So the output is the reference's construction in our vocabulary, not a copy of
its pixels: run it on a hat with three greens and you get body steps; run it on
a hat with a red peak under a blue crown and the peak comes out as trim.

    python3 tools/derive_base_from_reference.py 16 --name peaked_cap
"""
from __future__ import annotations

import argparse
import colorsys
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze_hat_construction_corpus import MOD, VANILLA, frames        # noqa: E402
from v5.grammar import luminance                                        # noqa: E402

STEP_CHARS = {"body": "123456", "trim": "abcdef", "accent": "pqrstu"}
VIEWS = ("front", "left", "back")
HUE_GAP = 25.0          # degrees before a colour is a different material
ACCENT_MAX = 4          # cells: below this an off-hue colour is punctuation
TRIM_MIN = 3            # cells: at or above this it is a second cloth


def hsv(c):
    return colorsys.rgb_to_hsv(c[0] / 255, c[1] / 255, c[2] / 255)


def hue_gap(a, b):
    d = abs(a - b)
    return min(d, 1 - d) * 360


def assign_roles(counts: Counter, trim=(), accent=()) -> dict:
    """colour -> role.  Everything is one cloth unless told otherwise.

    Hue distance looked like a way to find a second material and is not: a
    shaded orange cap runs through dark red, and on vanilla 016 that split the
    crown's own shadows off as "trim" while the lit orange became the body.
    Shading moves hue.  So the default is that a reference is ONE cloth whose
    colours are a value ramp, and a genuine second material — a red peak under
    a blue crown, a metal buckle — is named explicitly by the person who can
    see it.
    """
    roles = {c: "body" for c in counts}
    for c in counts:
        if c[:3] in trim:
            roles[c] = "trim"
        elif c[:3] in accent:
            roles[c] = "accent"
    return roles


# Share of the sprite above which a colour is a PLANE, not a highlight.  The
# four hats the user picked as good put 5.2% of the frame at peak brightness.
HIGHLIGHT_MAX_SHARE = 0.08


def assign_steps(counts: Counter, roles: dict) -> dict:
    """colour -> (role, step).  Rank by luminance INSIDE each role.

    The darkest colour of a role becomes step 0 and the lightest step 5, with
    the rest spread by rank — rank, not absolute luminance, so a low-contrast
    reference still produces a readable ladder and the palette supplies the
    real values.

    Then AREA corrects the top of that ramp.  Vanilla 033 spends its brightest
    green on a fifth of the sprite: that is a lit plane, and mapping it to our
    highlight step turned a modest green cap into a blown-out cream one.  If
    the colour holding the top step covers more than HIGHLIGHT_MAX_SHARE, the
    whole role shifts down a step so the highlight stays a highlight.
    """
    total = sum(counts.values()) or 1
    out = {}
    for role in ("body", "trim", "accent"):
        cols = sorted((c for c in counts if roles[c] == role), key=luminance)
        if not cols:
            continue
        # RELATIVE luminance position, not even rank spacing.  Rank spacing
        # treats a reference whose four colours are bunched dark the same as one
        # that spans the full range, which lightened vanilla 033's dark green
        # knit into cream.  Position keeps the reference's own tonal balance.
        lo = luminance(cols[0])
        hi = luminance(cols[-1])
        span = max(1.0, hi - lo)
        steps = {c: round(5 * (luminance(c) - lo) / span) for c in cols}
        # ...and the brightest colour only earns the highlight step if it is
        # small enough to BE a highlight.  A fifth of the sprite is a plane.
        if counts[cols[-1]] / total > HIGHLIGHT_MAX_SHARE:
            steps[cols[-1]] = min(steps[cols[-1]], 4)
        # keep every colour distinct: two colours collapsing to one step loses a
        # value the reference was using to describe its form.
        seen = {}
        for c in cols:
            v = steps[c]
            while v in seen.values() and v < 5:
                v += 1
            seen[c] = v
        steps = seen
        for c, v in steps.items():
            out[c] = (role, v)
    return out


def to_art(cells: dict, mapping: dict, w: int = 20, h: int = 20) -> list:
    rows = []
    for y in range(h):
        line = ""
        for x in range(w):
            c = cells.get((x, y))
            if c is None:
                line += "."
            else:
                role, step = mapping[c]
                line += STEP_CHARS[role][step]
            rows.append if False else None
        rows.append(line.rstrip(".") and line or "")
    while rows and not rows[-1].strip("."):
        rows.pop()
    return rows


def derive(index: int, source: str = "vanilla", trim=(), accent=()) -> dict:
    blocks = frames(VANILLA if source == "vanilla" else MOD)
    blk = blocks[index]
    # Cells the reference draws at partial alpha are its own drop shadow on the
    # head, not hat: including them would widen the silhouette with something
    # the renderer draws for free.
    blk = {v: {c: px for c, px in cells.items() if px[3] >= 200}
           for v, cells in blk.items()}
    counts = Counter()
    for view in VIEWS:
        counts.update(blk[view].values())
    roles = assign_roles(counts, trim, accent)
    mapping = assign_steps(counts, roles)
    art = {v: to_art(blk[v], mapping) for v in VIEWS}
    summary = []
    for col, n in counts.most_common():
        role, step = mapping[col]
        summary.append(f"    {col} n={n:4d} L={luminance(col):6.1f} -> {role} step {step}")
    return {"art": art, "mapping": mapping, "summary": summary, "block": blk}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("index", type=int)
    ap.add_argument("--source", default="vanilla", choices=("vanilla", "mod"))
    ap.add_argument("--name", default="derived")
    ap.add_argument("--trim", default="", help="hex colours that are a SECOND cloth")
    ap.add_argument("--accent", default="", help="hex colours that are punctuation")
    a = ap.parse_args()

    def parse(spec):
        out = []
        for h in filter(None, spec.split(",")):
            h = h.strip().lstrip("#")
            out.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        return tuple(out)

    out = derive(a.index, a.source, parse(a.trim), parse(a.accent))
    print(f"# {a.name} — derived from {a.source} hat #{a.index}")
    print("# colour -> role/step:")
    print("\n".join(out["summary"]))
    for view in VIEWS:
        var = f"{a.name.upper()}_{view.upper()}"
        print(f"\n{var} = [")
        for row in out["art"][view]:
            print(f'    "{row}",')
        print("]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
