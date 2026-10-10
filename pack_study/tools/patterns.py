"""Find SURFACE PATTERNS: an author's solid hat and the same hat with a pattern drawn on.

For each library pair (solid A, B = patternOf A, identical alpha mask):
  split pixels  A pixels whose single colour index becomes >= 2 different colours in B
                (a pure recolour never splits; a reshade splits but not periodically)
  class map     per split pixel, which of B's colours it took, ranked by lightness
                within its A index (0 = darkest) -> a small integer grid
  period        smallest horizontal / vertical shift p (2..8) under which the front
                view's class map agrees with itself on >= AGREE of overlapping pixels
A candidate needs split pixels on >= MIN_SPLIT of the front material and a period
in at least one direction.  Proposal only: approval is by eye on out/patterns.png,
like decorations (CLAUDE.md s3 -- separable pixels do not prove "plaid").
Writes data/patterns.json.  Analysis-only (PIL).
"""
import json, os
from collections import Counter, defaultdict
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(HERE, 'data', *p)
MIN_SPLIT, AGREE = 0.25, 0.8


def lum(p): return 0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]


def period(cls, w, h, axis):
    best = None
    for p in range(2, 9):
        same = tot = 0
        for (x, y), k in cls.items():
            q = (x + p, y) if axis == 'x' else (x, y + p)
            if q in cls:
                tot += 1; same += cls[q] == k
        if tot >= 8 and same / tot >= AGREE:
            best = (p, round(same / tot, 3)); break
    return best


def main():
    lib = json.load(open(D('library.json')))
    by = {c['id']: c for c in lib['constructions']}
    out = []
    for b in lib['constructions']:
        if not b['patternOf']: continue
        a = by[b['patternOf']]
        w, h = a['frame']; W = 4 * w
        pa, pb = a['colourways'][0]['palette'], b['colourways'][0]['palette']
        to = defaultdict(Counter)
        for k, (ga, gb) in enumerate(zip(a['grid'], b['grid'])):
            if ga >= 0 and gb >= 0: to[ga][gb] += 1
        split = {j for j, c in to.items() if len([n for n in c.values() if n >= 2]) >= 2}
        # rank B colours within each split A index by lightness -> class id
        rank = {j: {g: r for r, g in enumerate(sorted(to[j], key=lambda g: lum(pb[g])))} for j in split}
        views = {}
        for vi, v in enumerate(['front', 'right', 'left', 'back']):
            cls = {}
            for k, (ga, gb) in enumerate(zip(a['grid'], b['grid'])):
                x, y = k % W, k // W
                if x // w != vi or ga not in split or gb < 0: continue
                cls[(x % w, y)] = rank[ga][gb]
            views[v] = cls
        front_mat = sum(1 for k, g in enumerate(a['grid']) if g >= 0 and (k % W) // w == 0)
        frac = len(views['front']) / max(1, front_mat)
        px_, py_ = period(views['front'], w, h, 'x'), period(views['front'], w, h, 'y')
        rec = {'solid': a['id'], 'patterned': b['id'], 'author': a['author'], 'names': [a['names'][0], b['names'][0]],
               'frame': [w, h], 'splitFrac': round(frac, 3), 'periodX': px_, 'periodY': py_,
               'candidate': frac >= MIN_SPLIT and bool(px_ or py_)}
        out.append(rec)
    json.dump(out, open(D('patterns.json'), 'w'), indent=1)
    cands = [r for r in out if r['candidate']]
    print(f'pairs {len(out)} | candidates {len(cands)}')
    for r in cands:
        print(f"  {r['author'][:14]:14s} {r['names'][0][:22]:22s} -> {r['names'][1][:22]:22s} split={r['splitFrac']} px={r['periodX']} py={r['periodY']}")
    # contact sheet: solid | patterned, x5
    S = 5; rows = cands
    im = Image.new('RGBA', (2 * (4 * 20 * S + 12), max(1, len(rows)) * (20 * S + 6)), (118, 128, 112, 255))
    for i, r in enumerate(rows):
        for j, cid in enumerate([r['solid'], r['patterned']]):
            c = by[cid]; w, h = c['frame']; pal = c['colourways'][0]['palette']
            t = Image.new('RGBA', (4 * w, h))
            t.putdata([tuple(pal[g]) if g >= 0 else (0, 0, 0, 0) for g in c['grid']])
            t = t.resize((4 * w * S, h * S), Image.NEAREST)
            im.alpha_composite(t.crop((0, 0, min(t.width, 4 * 20 * S), min(t.height, 20 * S))), (j * (4 * 20 * S + 12), i * (20 * S + 6)))
    im.save(os.path.join(HERE, 'out', 'patterns.png'))


if __name__ == '__main__':
    main()
