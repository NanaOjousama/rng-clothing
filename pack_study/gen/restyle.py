"""Restyle: shape (and internal light/dark structure) from one construction,
shading ramp + outline treatment from another author.  Pure Python.

Per user direction (2026-10-09): a shape whose shading does not match the target
art may be used with the target art's shading -- the two need not match before
deconstruction.

  1. source pixel -> normalised value rank in [0,1] among the source's colours
     (keeps the source's own construction lines: brim edge, folds, seams)
  2. rank -> the target ramp level at the same rank (target ramp = one of the
     target author's proven colourways, distinct colours sorted by lightness)
  3. outer-edge pixels -> the target author's measured edge level, so a soft
     author's shape picks up a hard author's outline and vice versa.
Only single-material constructions take part (chromatic colours within
SINGLE_HUE degrees, or greyscale); multi-material art (gold buckle on a felt
crown) would have its materials merged into one ramp, so it is excluded.
"""
import os, statistics as st, sys
sys.path.insert(0, os.path.dirname(__file__))
from colour import to_lch
SINGLE_HUE = 40

def palette_of(c, way=0):
    return c['colourways'][way]['palette']

def single_material(c):
    hs = sorted(to_lch(p)[2] for p in palette_of(c) if to_lch(p)[1] > 0.04)
    if len(hs) < 2: return True
    gaps = [(hs[(k + 1) % len(hs)] - hs[k]) % 360 for k in range(len(hs))]
    return 360 - max(gaps) <= SINGLE_HUE

def ranks(pal):
    Ls = sorted({round(to_lch(p)[0], 3) for p in pal})
    n = max(1, len(Ls) - 1)
    return [Ls.index(round(to_lch(p)[0], 3)) / n for p in pal]

def edges(c):
    w, h = c['frame']; W = 4 * w; g = c['grid']
    out = set()
    for k, v in enumerate(g):
        if v < 0: continue
        x, y = k % W, k // W
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if nx // w != x // w or not (0 <= nx < W and 0 <= ny < h) or g[ny * W + nx] < 0:
                out.add(k); break
    return out

def target_style(cons):
    """Measured from the target author's constructions: median value rank of edge pixels."""
    er = []
    for c in cons:
        r = ranks(palette_of(c)); e = edges(c)
        er += [r[c['grid'][k]] for k in e]
    return {'edgeRank': st.median(er) if er else 0.0}

def ramp_of(c, way):
    pal = palette_of(c, way)
    by = {}
    for p in pal: by.setdefault(round(to_lch(p)[0], 3), p)
    return [by[L] for L in sorted(by)]

def restyle(src, ramp, style):
    r = ranks(palette_of(src)); e = edges(src)
    lvl = lambda t: ramp[min(len(ramp) - 1, round(t * (len(ramp) - 1)))]
    pal = {}
    out = []
    for k, g in enumerate(src['grid']):
        if g < 0: out.append(None); continue
        t = min(r[g], style['edgeRank']) if k in e else r[g]
        p = lvl(t)
        out.append([p[0], p[1], p[2], palette_of(src)[g][3]])
    return out
