"""Matrix: rows = perched decorations, cols = target hats (first proven colourway)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
from decorate import load_approved, place, VIEWS
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))

def find(author, name):
    for c in lib['constructions']:
        if c['author'] == author and not c['missing'] and name in c['names']: return c
    raise SystemExit(f'missing {author} {name}')

TARGETS = [('CuteBeret-35115', 'Cute_beret_6'), ('Jedone', 'Vintage Cap_02'), ('h young FS Code By Mychocolate', 'hyoung_hats_20'),
           ('ConcernedApe', 'hats_47'), ('Seyph', 'hats_4'), ('Kookoroo', 'Kookoroo_2'), ('Kailey', 'Winter Beanie (Blue)'),
           ('ConcernedApe', 'hats_53'), ('Seyph', 'hats_2'), ('Kailey', 'hats_2')]

def views_of(c):
    w, h = c['frame']; W = 4 * w; pal = c['colourways'][0]['palette']
    px = {v: {} for v in VIEWS}; masks = {v: [[0] * w for _ in range(h)] for v in VIEWS}
    for k, g in enumerate(c['grid']):
        if g < 0: continue
        x, y = k % W, k // W; v = VIEWS[x // w]
        px[v][(x % w, y)] = pal[g]; masks[v][y][x % w] = 1
    return px, masks

def main():
    decs = [d for d in load_approved() if d['kind'] == 'perched']
    tg = [find(*t) for t in TARGETS]
    S = 4; fw = 20 * S; cell = 4 * (fw + 3) + 10; rowh = 22 * S + 6
    W = (1 + len(tg)) * cell; H = len(decs) * rowh
    bg = (118, 128, 112, 255); canvas = [[bg] * W for _ in range(H)]
    def put(px_by_view, ox, oy, frame):
        w, h = frame
        for vi, v in enumerate(VIEWS):
            for (x, y), p in px_by_view[v].items():
                if not p[3] or y >= 22: continue
                a = p[3] / 255
                for yy in range(S):
                    row = canvas[oy + y * S + yy]
                    for xx in range(S):
                        X = ox + vi * (fw + 3) + x * S + xx
                        if X >= W: continue
                        q = row[X]; row[X] = tuple(round(p[j] * a + q[j] * (1 - a)) for j in range(3)) + (255,)
    report = []
    for r, d in enumerate(decs):
        src = {v: {(x, y): p for x, y, p in d['views'][v]['pixels']} for v in VIEWS}
        put(src, 2, r * rowh + 3, d['frame'])
        ok = 0
        for k, t in enumerate(tg):
            px, masks = views_of(t)
            res = place(d, masks)
            if res is None: continue
            ok += 1
            comp = {v: dict(px[v]) for v in VIEWS}
            for v in VIEWS:
                for x, y, p in res[v]: comp[v][(x, y)] = p
            put(comp, (k + 1) * cell + 2, r * rowh + 3, t['frame'])
        report.append(f"{d['label']}: placed on {ok}/{len(tg)}")
    png.write(os.path.join(HERE, 'out', 'decorate_matrix.png'), W, H, canvas)
    print('\n'.join(report)); print('cols:', ', '.join(f'{a[:8]}:{n}' for a, n in TARGETS))

main()
