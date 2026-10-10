"""Matrix: rows = approved bands, cols = brimmed targets (one per shape family).
usage: demo_band.py [max_targets]  -> out/band_matrix.png"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
from decorate import load_approved, VIEWS
import band as B
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def views_of(c):
    w, h = c['frame']; W = 4 * w; pal = c['colourways'][0]['palette']
    px = {v: {} for v in VIEWS}; masks = {v: [[0] * w for _ in range(h)] for v in VIEWS}
    for k, g in enumerate(c['grid']):
        if g < 0: continue
        x, y = k % W, k // W; v = VIEWS[x // w]
        px[v][(x % w, y)] = pal[g]; masks[v][y][x % w] = 1
    return px, masks


def targets(lib, n):
    """Brimmed hats, one per shape family.  A width jump alone does not prove a brim
    (a veil, a mask or a crown jump too -- CLAUDE.md s3), so a target also needs
    positive evidence: an author's own name for it.  Shape-family membership is not
    enough (families at IoU 0.72 put a plague-doctor mask next to a sun hat)."""
    hats = {r['id']: r for r in json.load(open(os.path.join(HERE, 'data', 'hats.json')))}
    named = lambda c: B.eligible(c['names'] + [hats[w['source']].get('vanillaName')
                                               for w in c['colourways'] if w['source'] in hats])
    seen, out = set(), []
    for c in lib['constructions']:
        if c['missing'] or c['frame'][0] != 20 or c['family'] in seen: continue
        if not named(c): continue
        _, m = views_of(c)
        jf = B.junction(m['front'])
        if jf and jf[0] >= B.MIN_JUMP:
            seen.add(c['family']); out.append(c)
    return out[:n]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    bands = [d for d in load_approved() if d['kind'] == 'band']
    tg = targets(lib, n)
    S = 4; fw = 20 * S; cell = 4 * (fw + 3) + 10; rowh = 26 * S + 6
    W = (1 + len(tg)) * cell; H = len(bands) * rowh
    bg = (118, 128, 112, 255); canvas = [[bg] * W for _ in range(H)]

    def put(pxv, ox, oy):
        for vi, v in enumerate(VIEWS):
            for (x, y), p in pxv[v].items():
                if not p[3] or y >= 26: continue
                a = p[3] / 255
                for yy in range(S):
                    row = canvas[oy + y * S + yy]
                    for xx in range(S):
                        X = ox + vi * (fw + 3) + x * S + xx
                        if X < W:
                            q = row[X]; row[X] = tuple(round(p[j] * a + q[j] * (1 - a)) for j in range(3)) + (255,)
    for r, d in enumerate(bands):
        src = {v: {(x, y): p for x, y, p in d['views'][v]['pixels']} for v in VIEWS}
        put(src, 2, r * rowh + 3)
        ok = []
        for k, t in enumerate(tg):
            px, m = views_of(t)
            res = B.place(d, m)
            if res is None: continue
            ok.append(f"{t['author'][:10]}:{t['names'][0][:18]}")
            comp = {v: dict(px[v]) for v in VIEWS}
            for v in VIEWS:
                for x, y, p in res[v]: comp[v][(x, y)] = p
            put(comp, (k + 1) * cell + 2, r * rowh + 3)
        print(f"{d['label']}: {len(ok)}/{len(tg)}  {ok}")
    png.write(os.path.join(HERE, 'out', 'band_matrix.png'), W, H, canvas)
    print('cols:', [f"{t['author'][:10]}:{t['names'][0][:18]}" for t in tg])


if __name__ == '__main__':
    main()
