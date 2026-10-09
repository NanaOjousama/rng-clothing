"""Crown from hat A + brim from hat B, per view, re-shaded into one author's style.

Rules:
  * seat compatibility: |crown base width A - crown base width B| <= SEAT_TOL in
    every view (otherwise the crown overhangs / floats on the brim).
  * placement: A's crown base row lands on B's row junction-1, centres aligned.
  * shading: each part is ranked against ITS OWN source colours (material only),
    then mapped onto the target ramp at the same rank (user rule 2026-10-09:
    take the shape, use the target art's shading).  Outer edges of the new
    silhouette take the target's edge level, which also re-outlines the seam.
  * band / decoration pixels (chromatic, far from the part's dominant hue) keep
    their source colour.
usage: combine_brimmed.py  -> out/brimmed_combos.png + data/brimmed_combos.json
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
from colour import to_lch
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']
SEAT_TOL = 2

def lch(p): return to_lch(p)

def is_material(p, dom):
    """Opaque pixels near the dominant hue (or truly neutral).  Semi-transparent
    pixels are a drop-shadow layer (Kailey: 0,0,0,99) and never join the ramp."""
    if p[3] < 255: return False
    L, C, H = lch(p)
    return dom is None or C < 0.03 or min(abs(H - dom), 360 - abs(H - dom)) <= 35

def dominant(pixels):
    from collections import Counter
    c = Counter(tuple(p[2][:3]) for p in pixels if lch(p[2])[1] >= 0.05)
    return lch(c.most_common(1)[0][0])[2] if c else None

def rank_map(pixels, dom):
    """Pixel-weighted rank: midpoint of each lightness level's share of the part's
    material pixels (histogram matching, so the target keeps its tonal balance)."""
    from collections import Counter
    cnt = Counter(round(lch(p[2])[0], 3) for p in pixels if is_material(p[2], dom))
    tot = sum(cnt.values()) or 1; acc = 0; mid = {}
    for L in sorted(cnt):
        mid[L] = (acc + cnt[L] / 2) / tot; acc += cnt[L]
    return lambda p: mid[round(lch(p)[0], 3)]

def target_ramp(hat):
    """Target material colours with their cumulative pixel share, dark -> light."""
    from collections import Counter
    pix = [p for v in VIEWS for part in ('crown', 'brim') for p in hat['views'][v][part]]
    pix = [p for p in pix if p[2][:3] not in hat.get('maskValues', [])]
    dom = dominant(pix)
    cnt = Counter(); col = {}
    for p in pix:
        if is_material(p[2], dom):
            L = round(lch(p[2])[0], 3); cnt[L] += 1; col.setdefault(L, p[2])
    tot = sum(cnt.values()); acc = 0; ramp = []
    for L in sorted(cnt):
        acc += cnt[L]; ramp.append((acc / tot, col[L]))
    return ramp

def edge_rank(hat):
    """Median value rank of outer-edge pixels in the target hat (its outline habit)."""
    import statistics as st
    rs = []
    for v in VIEWS:
        pix = [p for p in hat['views'][v]['crown'] + hat['views'][v]['brim'] if p[2][:3] not in hat.get('maskValues', [])]
        dom = dominant(pix); rk = rank_map(pix, dom)
        occ = {(x, y) for x, y, _ in pix}
        for x, y, p in pix:
            if is_material(p, dom) and any((x + dx, y + dy) not in occ for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                rs.append(rk(p))
    return st.median(rs) if rs else 0

def compatible(a, b):
    return all(abs(a['views'][v]['crownBase'][1] - b['views'][v]['crownBase'][1]) <= SEAT_TOL for v in VIEWS)

def combine(a, b, tgt, frame):
    ramp = target_ramp(tgt); er = edge_rank(tgt)
    lvl = lambda t: next((c for q, c in ramp if t <= q), ramp[-1][1])
    w, h = frame
    out = {}
    for v in VIEWS:
        va, vb = a['views'][v], b['views'][v]
        dx = round(vb['crownBase'][0] - va['crownBase'][0]); dy = vb['junction'] - va['junction']
        crown = [[x + dx, y + dy, p] for x, y, p in va['crown'] if 0 <= x + dx < w and 0 <= y + dy < h]
        brim = vb['brim']
        cells = {}
        for part, src in ((brim, b), (crown, a)):     # crown drawn last: it sits in front at the seam
            masks = src.get('maskValues', [])
            mat = [q for q in part if q[2][:3] not in masks]          # FS mask pixels = band, keep colour
            dom = dominant(mat); rk = rank_map(mat, dom)
            for x, y, p in part:
                m = p[:3] not in masks and is_material(p, dom)
                cells[(x, y)] = (p, m, rk(p) if m else None)
        img = {}
        for (x, y), (p, mat, r) in cells.items():
            if not mat: img[(x, y)] = list(p); continue
            edge = any((x + ex, y + ey) not in cells for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            q = lvl(min(r, er) if edge else r)
            img[(x, y)] = [q[0], q[1], q[2], p[3]]
        out[v] = img
    return out

def main():
    data = json.load(open(os.path.join(HERE, 'data', 'brimmed_parts.json')))['hats']
    ids = list(data)
    combos = []
    for ia in ids:
        for ib in ids:
            a, b = data[ia], data[ib]
            if ia == ib or a['author'] == b['author'] and a['name'].split(' w/')[0] == b['name'].split(' w/')[0]: continue
            if a['frame'] != b['frame'] or not compatible(a, b): continue
            for it in {ia, ib}:
                combos.append((ia, ib, it))
    print('compatible (crown, brim, style) triples:', len(combos))
    rows = []
    for ia, ib, it in combos:
        a, b, t = data[ia], data[ib], data[it]
        rows.append((ia, ib, it, combine(a, b, t, b['frame'])))
    json.dump([{'crown': ia, 'brim': ib, 'style': it} for ia, ib, it, _ in rows],
              open(os.path.join(HERE, 'data', 'brimmed_combos.json'), 'w'), indent=1)
    # contact sheet: crown source | brim source | result   (4 views each, x4)
    S = 4; fw = 20 * S; cell = 4 * fw + 12; gap = 16
    W = 3 * cell + 2 * gap; rowh = 25 * S + 6
    H = len(rows) * rowh
    bg = (118, 128, 112, 255); canvas = [[bg] * W for _ in range(H)]
    def put(img_by_view, ox, oy):
        for vi, v in enumerate(VIEWS):
            for (x, y), p in img_by_view[v].items():
                if not p[3]: continue
                a = p[3] / 255
                for yy in range(S):
                    row = canvas[oy + y * S + yy]
                    for xx in range(S):
                        X = ox + vi * (fw + 4) + x * S + xx
                        q = row[X]; row[X] = tuple(round(p[j] * a + q[j] * (1 - a)) for j in range(3)) + (255,)
    src = lambda hat: {v: {(x, y): p for x, y, p in hat['views'][v]['crown'] + hat['views'][v]['brim']} for v in VIEWS}
    for k, (ia, ib, it, res) in enumerate(rows):
        y = k * rowh + 3
        put(src(data[ia]), 0, y); put(src(data[ib]), cell + gap, y); put(res, 2 * (cell + gap), y)
    png.write(os.path.join(HERE, 'out', 'brimmed_combos.png'), W, H, canvas)
    for ia, ib, it, _ in rows: print(f"crown {data[ia]['author'][:8]}:{data[ia]['name'][:20]:20s} | brim {data[ib]['author'][:8]}:{data[ib]['name'][:20]:20s} | style {data[it]['author']}")

if __name__ == '__main__':
    main()
