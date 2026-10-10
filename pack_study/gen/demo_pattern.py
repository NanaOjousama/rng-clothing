"""Plaid transfer: self-check against the author's own plaid, then a target matrix.
usage: demo_pattern.py [n_targets]  -> out/pattern_matrix.png"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
import pattern as P
from restyle import single_material
from colour import to_lch
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip(c):
    w, h = c['frame']; W = 4 * w; pal = c['colourways'][0]['palette']
    return [[tuple(pal[c['grid'][y * W + x]]) if c['grid'][y * W + x] >= 0 else (0, 0, 0, 0)
             for x in range(W)] for y in range(h)]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    pats = P.load_approved(lib)
    by = {(c['author'], nm): c for c in lib['constructions'] for nm in c['names']}
    # self-check: solid + transferred plaid vs the author's own plaid
    for p in pats:
        a_, sa, sb = p['source'].split('|')
        a, b = by[(a_, sa)], by[(a_, sb)]
        got, want = P.apply(p, strip(a), a['frame']), strip(b)
        op = [(y, x) for y, r in enumerate(want) for x, q in enumerate(r) if q[3]]
        close = sum(abs(to_lch(got[y][x])[0] - to_lch(want[y][x])[0]) < 0.04 for y, x in op) / len(op)
        print(f"self-check {p['source']}: {close:.1%} of pixels within dL 0.04 of the author's plaid")
    # targets: single-material, all 4 views, 20 wide, one per family, not the source author
    seen, tg = set(), []
    for c in lib['constructions']:
        if c['missing'] or c['frame'][0] != 20 or c['family'] in seen or c['author'].startswith('CuteBeret'): continue
        if not P.eligible(c): continue
        seen.add(c['family']); tg.append(c)
    tg = tg[:n]
    S, gap = 4, 6
    cw = 4 * 20 * S + gap
    W, H = 2 * cw + 10, len(tg) * (22 * S + 4)
    canvas = [[(118, 128, 112, 255)] * W for _ in range(H)]
    for i, c in enumerate(tg):
        for j, img in enumerate([strip(c), P.apply(pats[0], strip(c), c['frame'], P.material_mask(c))]):
            for y, row in enumerate(img):
                for x, q in enumerate(row):
                    if not q[3] or x >= 80: continue
                    for yy in range(S):
                        r = canvas[i * (22 * S + 4) + y * S + yy]
                        for xx in range(S): r[j * cw + x * S + xx] = q[:3] + (255,)
    png.write(os.path.join(HERE, 'out', 'pattern_matrix.png'), W, H, canvas)
    print('targets:', [f"{c['author'][:10]}:{c['names'][0][:16]}" for c in tg])


if __name__ == '__main__':
    main()
