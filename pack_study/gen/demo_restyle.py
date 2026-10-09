"""Demo: rows = source shapes, cols = original + restyled into target authors."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
from restyle import single_material, target_style, ramp_of, restyle
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))

def find(author, name):
    for c in lib['constructions']:
        if c['author'] == author and not c['missing'] and any(n == name for n in c['names']): return c
    raise SystemExit(f'not found {author} {name}')

SHAPES = [('Jedone', 'Vintage Cap_01'), ('Kailey', 'Straw Hat (Blue)'), ('CuteBeret-35115', 'Cute_beret_3'),
          ('h young FS Code By Mychocolate', 'hyoung_hats_22'), ('ConcernedApe', 'hats_73'), ('Kookoroo', 'Kookoroo_15'),
          ('ConcernedApe', 'hats_47'), ('Jedone', 'Trapper Hat_01')]
TARGETS = [('CuteBeret-35115', 'Cute_beret_6'), ('Kailey', 'Winter Beanie (Blue)'), ('h young FS Code By Mychocolate', 'hyoung_hats_20'),
           ('ConcernedApe', 'hats_53'), ('Kookoroo', 'Kookoroo_3')]

def main():
    shapes = [find(*s) for s in SHAPES]
    targets = []
    for a, n in TARGETS:
        mine = [c for c in lib['constructions'] if c['author'] == a and single_material(c) and not c['colourable']]
        targets.append((a, find(a, n), target_style(mine)))
    S = 4; cw, ch = 4 * 20 * S + 24, 20 * S + 8
    W, H = (1 + len(targets)) * cw, len(shapes) * ch
    bg = (118, 128, 112, 255); canvas = [[bg] * W for _ in range(H)]
    def blit(px, w, h, ox, oy):
        for k, p in enumerate(px):
            if not p or p[3] == 0: continue
            x, y = k % (4 * w), k // (4 * w); a = p[3] / 255
            for dy in range(S):
                row = canvas[oy + y * S + dy]
                for dx in range(S):
                    X = ox + x * S + dx + (x // w) * 4
                    q = row[X]; row[X] = tuple(round(p[j] * a + q[j] * (1 - a)) for j in range(3)) + (255,)
    for i, s in enumerate(shapes):
        w, h = s['frame']
        blit([None if g < 0 else s['colourways'][0]['palette'][g] for g in s['grid']], w, h, 4, i * ch + 4)
        for j, (a, t, st_) in enumerate(targets):
            blit(restyle(s, ramp_of(t, 0), st_), w, h, (j + 1) * cw + 4, i * ch + 4)
        print(s['author'][:12], s['names'][0], 'single-material' if single_material(s) else 'MULTI-material')
    png.write(os.path.join(HERE, 'out', 'restyle_matrix.png'), W, H, canvas)
    print('cols: original |', ' | '.join(f"{a[:12]} edgeRank={st_['edgeRank']:.2f}" for a, _, st_ in targets))

main()
