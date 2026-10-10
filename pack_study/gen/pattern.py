"""Transfer an approved surface PATTERN (CuteBeret plaid) onto another hat.  Pure Python.

The pattern is measured, not drawn.  On the author's solid hat A and the same hat with
the pattern B (identical mask), each pixel's OKLab lightness change dL = L(B) - L(A) is
the pattern.  CuteBeret's plaid is NOT a uniform tile (measured, back view): horizontal
lines every 3 rows from the top, vertical lines SYMMETRIC about the centre -- a wider
centre panel, then a line every 3 px outward -- and crossings darker than single lines.
So per view we measure the LAYOUT:
  vertical lines   columns where most interior pixels darken -> centre gap (half the
                   distance of the two central lines) + spacing outward
  horizontal lines rows where most interior pixels darken -> offset from the view top
                   + spacing
  darkness         median dL of single-line pixels and of crossings
and lay the same lines out on the target view, centred on ITS centre, from ITS top,
over INTERIOR pixels only (the target's outline stays), as a lightness change on the
target's own colour (hue and chroma kept): the restyle principle applied to pattern.
Only pixels the author's own colourways prove to be the recolourable material.
"""
import json, os, re
from collections import Counter
from colour import to_lch, from_lch
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']
TEXTURED = re.compile(r'straw|knit|woven|weave|wicker', re.I)   # inherent texture: no pattern on top
MAX_DETAIL = 0.9          # measured front interior colour-change rate (hat_features.json); straw ~0.99
MIN_INNER = 30            # front interior px: below this (clips, headphones) lines do not read as cloth
_FEAT = None


def load_approved(lib):
    ap = json.load(open(os.path.join(HERE, 'data', 'patterns_approved.json')))['approved']
    meas = {(m['solid'], m['patterned']): m for m in json.load(open(os.path.join(HERE, 'data', 'patterns.json')))}
    by_name = {(c['author'], n): c for c in lib['constructions'] for n in c['names']}
    out = []
    for key, meta in ap.items():
        author, sa, sb = key.split('|')
        a, b = by_name[(author, sa)], by_name[(author, sb)]
        out.append(dict(meta, units=units(a, b, meas[(a['id'], b['id'])]), source=key))
    return out


def material_mask(c):
    """Strip pixels the pattern may touch.  With >= 2 proven colourways the author's
    MATERIAL indices are known -> only those (FIXED ones are another material: fur
    trim, lace, eyes).  Otherwise every opaque pixel (eligible() has already required
    one material)."""
    w, h = c['frame']; W = 4 * w
    mat = c.get('material')
    return {(k % W, k // W) for k, g in enumerate(c['grid'])
            if g >= 0 and (mat is None or mat[g])}


def eligible(c):
    """Big enough, untextured, and the author's own colourways prove which pixels are
    the recolourable material.  Without them, measurement could not tell fur trim
    (Santa), inner ears (bunny) or panda patches from a highlight (A/B 2026-10-09), so
    unproven hats take no pattern."""
    global _FEAT
    if c['missing'] or c['colourable']: return False
    if any(TEXTURED.search(n) for n in c['names']): return False
    if c.get('material') is None or not any(c['material']): return False
    if _FEAT is None:
        _FEAT = {f['id']: f for f in json.load(open(os.path.join(HERE, 'data', 'hat_features.json')))}
    f = _FEAT.get(c['colourways'][0]['source'])
    if f is None or not f['views']['front']: return False
    v = f['views']['front']
    w = c['frame'][0]; allowed = material_mask(c)
    inner = sum(1 for (x, y) in allowed if x < w and all((x + dx, y + dy) in allowed
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))))
    return v['detail'] < MAX_DETAIL and inner >= MIN_INNER


def _lines(cnt, tot, frac=0.6):
    return sorted(k for k in tot if tot[k] >= 2 and cnt.get(k, 0) / tot[k] >= frac)


def units(a, b, m):
    w, h = a['frame']; W = 4 * w
    pa, pb = a['colourways'][0]['palette'], b['colourways'][0]['palette']
    out = {}
    for vi, v in enumerate(VIEWS):
        dl = {}
        for k, (ga, gb) in enumerate(zip(a['grid'], b['grid'])):
            x, y = k % W, k // W
            if x // w == vi and ga >= 0 and gb >= 0:
                dl[(x % w, y)] = to_lch(pb[gb])[0] - to_lch(pa[ga])[0]
        if not dl: out[v] = None; continue
        inner = {q for q in dl if all((q[0] + dx, q[1] + dy) in dl for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        dark = {q for q in inner if dl[q] < -0.04}
        ct, cn, rt, rn = Counter(), Counter(), Counter(), Counter()
        for (x, y) in inner:
            ct[x] += 1; rt[y] += 1
            if (x, y) in dark: cn[x] += 1; rn[y] += 1
        cols, rows = _lines(cn, ct), _lines(rn, rt)
        xs = [x for x, _ in dl]; ys = [y for _, y in dl]
        cx = (min(xs) + max(xs)) / 2; y0 = min(ys)
        offs = sorted({abs(x - cx) for x in cols})
        if not offs or not rows: out[v] = None; continue
        steps = [b2 - a2 for a2, b2 in zip(offs, offs[1:])] or [3]
        rsteps = [b2 - a2 for a2, b2 in zip(rows, rows[1:])] or [3]
        single = [dl[q] for q in dark if (q[0] in cols) != (q[1] in rows)]
        cross = [dl[q] for q in dark if q[0] in cols and q[1] in rows]
        med = lambda l, d: sorted(l)[len(l) // 2] if l else d
        out[v] = {'colGap': offs[0], 'colStep': Counter(steps).most_common(1)[0][0],
                  'rowOff': rows[0] - y0, 'rowStep': Counter(rsteps).most_common(1)[0][0],
                  'line': round(med(single, -0.12), 3), 'cross': round(med(cross, -0.18), 3)}
    return out


def _on(pos, start, step):
    return pos >= start - 1e-6 and abs(((pos - start) / step) - round((pos - start) / step)) < 1e-6


def apply(pattern, px_rows, frame, allowed=None):
    """px_rows: rows of RGBA tuples over the 4-view strip.  allowed: strip (x, y) the
    pattern may touch (material_mask); None = all.  Returns a new strip."""
    w, h = frame
    out = [list(r) for r in px_rows]
    for vi, v in enumerate(VIEWS):
        u = pattern['units'].get(v) or pattern['units']['front']
        if u is None: continue
        op = {(x, y) for y in range(h) for x in range(w) if px_rows[y][vi * w + x][3]}
        if not op: continue
        xs = [x for x, _ in op]
        cx, y0 = (min(xs) + max(xs)) / 2, min(y for _, y in op)
        # same centre gap: a half-integer gap on an integer centre rounds outward
        gap = u['colGap'] if (cx + u['colGap']) % 1 == 0 else u['colGap'] + 0.5
        for (x, y) in op:
            if any((x + dx, y + dy) not in op for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue                                    # outline stays the target's
            vline = _on(abs(x - cx), gap, u['colStep'])
            hline = _on(y - y0, u['rowOff'], u['rowStep'])
            if allowed is not None and (vi * w + x, y) not in allowed: continue
            d = u['cross'] if vline and hline else (u['line'] if vline or hline else 0)
            if not d: continue
            p = px_rows[y][vi * w + x]
            L, C, H = to_lch(p)
            out[y][vi * w + x] = tuple(from_lch(max(0.0, min(1.0, L + d)), C, H)) + (p[3],)
    return out
