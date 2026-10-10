"""Move an approved BAND (ribbon / hatband) onto another brimmed hat.  Pure Python.

A band wraps the crown just above the brim, so it is placed relative to the
crown/brim JUNCTION, not to the top surface (decorate.py does perched parts).

Per view:
  junction  first row, in the upper 75% of the bbox, where opaque width jumps the
            most (same measure as tools/split_brimmed.py).  A target needs a real
            brim: jump >= MIN_JUMP in the front view.
  rows      each band pixel keeps its row offset from the source junction.
  width     each band row is laid over the source row span [L..R] and resampled to
            the target row span [L'..R']: the EDGE columns at each end keep their
            place, the middle columns are CYCLED (repeated or cut) -- a dotted band
            keeps its dot spacing instead of being stretched.
  outline   the target's own outline pixels are never painted over (the band sits
            inside the hat's edge, as on the source); band pixels that would land
            off the target are dropped.  Too many dropped in a view -> reject.
Band pixels keep their source colour (separate material).
"""
import re
VIEWS = ['front', 'right', 'left', 'back']
EDGE = 2
MIN_JUMP = 2
MAX_DROP = 0.35
# author/vanilla names that positively say "brimmed hat" (target evidence, not a pixel test)
BRIM_NAMES = re.compile(r'straw|sun ?hat|boater|cowboy|cowgal|cowpoke|fedora|bowler|top ?hat|sombrero|fishing|bucket|panama|witch hat', re.I)

HAS_BAND = re.compile(r'ribbon|band|bow\b|bow\)', re.I)


def eligible(names):
    """Named brimmed hat that does not already carry a band (author's own words)."""
    names = [n for n in names if n]
    return any(BRIM_NAMES.search(n) for n in names) and not any(HAS_BAND.search(n) for n in names)


def spans(mask):
    return [([x for x, v in enumerate(row) if v] or None) for row in mask]


def junction(mask):
    rows = spans(mask)
    ys = [y for y, r in enumerate(rows) if r]
    if not ys: return None
    y0, y1 = ys[0], ys[-1]
    width = lambda y: (rows[y][-1] - rows[y][0] + 1) if rows[y] else 0
    lim = y0 + max(1, int((y1 - y0) * 0.75))
    jumps = [(width(y) - width(y - 1), y) for y in range(y0 + 1, lim + 1)]
    return max(jumps) if jumps else (0, y0)


def is_edge(mask, x, y):
    h, w = len(mask), len(mask[0])
    return any(not (0 <= x + dx < w and 0 <= y + dy < h) or not mask[y + dy][x + dx]
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def resample(cells, n):
    """cells: list over the source span (pixel or None) -> list of length n."""
    m = len(cells)
    if n == m: return list(cells)
    e = min(EDGE, m // 2, n // 2)
    mid = cells[e:m - e] or [None]
    out = []
    for k in range(n):
        if k < e: out.append(cells[k])
        elif k >= n - e: out.append(cells[m - (n - k)])
        else: out.append(mid[(k - e) % len(mid)])
    return out


def place_view(band_px, src_mask, tgt_mask):
    if not band_px: return []
    js, jt = junction(src_mask), junction(tgt_mask)
    if not js or not jt: return None
    ss, ts = spans(src_mask), spans(tgt_mask)
    h = len(tgt_mask)
    rows = {}
    for x, y, p in band_px: rows.setdefault(y, {})[x] = p
    out, dropped = [], 0
    for y, cols in rows.items():
        ty = y - js[1] + jt[1]
        if not (0 <= y < len(ss)) or not ss[y] or not (0 <= ty < h) or not ts[ty]:
            dropped += len(cols); continue
        L, R = ss[y][0], ss[y][-1]
        L2, R2 = ts[ty][0], ts[ty][-1]
        outside = {x: p for x, p in cols.items() if not L <= x <= R}
        dropped += len(outside)
        cells = resample([cols.get(x) for x in range(L, R + 1)], R2 - L2 + 1)
        for k, p in enumerate(cells):
            if p is None: continue
            x = L2 + k
            if not tgt_mask[ty][x] or is_edge(tgt_mask, x, ty):
                if not tgt_mask[ty][x]: dropped += 1
                continue
            out.append([x, ty, p])
    if dropped > MAX_DROP * len(band_px): return None
    return out


def place(band, target_masks):
    """band: approved decoration of kind 'band'.  Returns {view: pixels} or None."""
    jf = junction(target_masks['front'])
    if not jf or jf[0] < MIN_JUMP: return None
    res = {}
    for v in VIEWS:
        r = place_view(band['views'][v]['pixels'], band['views'][v]['baseMask'], target_masks[v])
        if r is None: return None
        res[v] = r
    return res
