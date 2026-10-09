"""Find decorations: pixels an author added on top of an otherwise-unchanged hat.

For every same-author pair (A, B) of equal frame size whose front masks overlap
(IoU >= 0.5): per view, shift A by up to +-2 px to maximise pixels that are
IDENTICAL in A and B.  If, over all four views, >= 80% of A's material survives
unchanged in B, then B = A + something.  The something (B pixels not equal to
the aligned A) is split into 4-connected components; components >= 3 px that sit
on/above A's silhouette are decoration candidates.  Large diffs (> 55% of B) are
re-drawings, not decorations, and are dropped.

Writes data/decorations.json (per decoration, per view: pixels in frame coords +
the aligned base mask, so placement can be computed relative to the base).
Proposal only -- the label "decoration" is confirmed on the contact sheet.
"""
import json, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']

def load(i, frame):
    a = np.array(Image.open(os.path.join(HERE, 'data', 'hats', i + '.png')).convert('RGBA')).astype(int)
    w = frame[0]
    return [a[:, k * w:(k + 1) * w] for k in range(4)]

def components(mask):
    seen = np.zeros_like(mask, bool); out = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]: continue
        stack, comp = [(y, x)], []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop(); comp.append((cy, cx))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; stack.append((ny, nx))
        out.append(comp)
    return out

def shift(a, dx, dy):
    return np.roll(np.roll(a, dy, 0), dx, 1)

def main():
    recs = json.load(open(os.path.join(HERE, 'data', 'hats.json')))
    by = {}
    for r in recs:
        if not r['missing']: by.setdefault((r['author'], tuple(r['frame'])), []).append(r)
    decs = []
    for (author, frame), rs in by.items():
        imgs = {r['id']: load(r['id'], frame) for r in rs}
        for A in rs:
            for B in rs:
                if A['id'] == B['id']: continue
                ma, mb = imgs[A['id']][0][:, :, 3] > 0, imgs[B['id']][0][:, :, 3] > 0
                if (ma & mb).sum() / max(1, (ma | mb).sum()) < 0.5: continue
                # align each view by alpha overlap, then learn ONE colour map A->B
                # (majority vote over all views) so a recoloured base still counts as
                # the base (Kailey's sunflower hat is her straw hat in another straw colour)
                aligned = []
                for v in range(4):
                    a, b = imgs[A['id']][v], imgs[B['id']][v]
                    bm = b[:, :, 3] > 0
                    _, dx, dy = max(((((shift(a, dx, dy)[:, :, 3] > 0) & bm).sum(), dx, dy)
                                     for dx in range(-2, 3) for dy in range(-2, 3)))
                    aligned.append((dx, dy, shift(a, dx, dy), b))
                from collections import Counter
                votes = Counter()
                for dx, dy, s, b in aligned:
                    m = (s[:, :, 3] > 0) & (b[:, :, 3] > 0)
                    for pa, pb in zip(map(tuple, s[m]), map(tuple, b[m])): votes[(pa, pb)] += 1
                cmap = {}
                for (pa, pb), n in votes.most_common():
                    cmap.setdefault(pa, pb)
                kept = tot = 0; per = []
                for dx, dy, s, b in aligned:
                    am = s[:, :, 3] > 0; bm = b[:, :, 3] > 0
                    mapped = np.zeros_like(s)
                    for y, x in zip(*np.nonzero(am)): mapped[y, x] = cmap.get(tuple(s[y, x]), (-99, -99, -99, -99))
                    same = am & bm & (np.abs(mapped - b).max(axis=2) <= 3)
                    kept += same.sum(); tot += am.sum()
                    per.append((dx, dy, am, bm & ~same, b))
                if tot == 0 or kept / tot < 0.8: continue
                bsum = sum(p[4][:, :, 3].astype(bool).sum() for p in per)
                dsum = sum(p[3].sum() for p in per)
                if dsum < 6 or dsum > 0.55 * bsum: continue
                views = {}
                for v, (dx, dy, am, diff, b) in enumerate(per):
                    comps = [c for c in components(diff) if len(c) >= 3]
                    px = [[int(x), int(y), [int(c) for c in b[y, x]]] for comp in comps for (y, x) in comp]
                    views[VIEWS[v]] = {'pixels': px, 'baseMask': [[int(x) for x in row] for row in am.astype(int)]}
                if sum(len(views[v]['pixels']) for v in VIEWS) < 6: continue
                decs.append({'id': f'dec_{len(decs)}', 'author': author, 'frame': list(frame), 'base': A['id'],
                             'from': B['id'], 'baseName': A['name'], 'fromName': B['name'],
                             'baseKept': round(kept / tot, 3), 'views': views})
    # visible in >= 3 views (a worn decoration is seen from most sides)
    decs = [d for d in decs if sum(bool(d['views'][v]['pixels']) for v in VIEWS) >= 3]
    # A->B and B->A both match; the real decoration is the direction whose extra
    # pixels differ most from the hat's own dominant colour (a new material).
    def distinct(d):
        from collections import Counter
        b = load(d['from'], d['frame'])
        cnt = Counter(tuple(p) for v in b for p in v.reshape(-1, 4) if p[3])
        dom = np.array(cnt.most_common(1)[0][0][:3])
        px = [p for v in VIEWS for _, _, p in d['views'][v]['pixels']]
        return float(np.mean([np.abs(np.array(p[:3]) - dom).sum() for p in px])) if px else 0
    for d in decs: d['distinct'] = round(distinct(d), 1)
    pair = {}
    for d in decs:
        k = (d['author'], frozenset((d['base'], d['from'])))
        if k not in pair or d['distinct'] > pair[k]['distinct']: pair[k] = d
    decs = list(pair.values())
    # one decoration per (author, from): keep the pair with the best-kept base
    best = {}
    for d in decs:
        k = (d['author'], d['from'])
        if k not in best or d['baseKept'] > best[k]['baseKept']: best[k] = d
    decs = list(best.values())
    json.dump(decs, open(os.path.join(HERE, 'data', 'decorations.json'), 'w'))
    from collections import Counter
    print(len(decs), Counter(d['author'] for d in decs).most_common())
    for d in decs: print(f"  {d['author'][:10]:10s} {d['fromName'][:30]:30s} <- base {d['baseName'][:26]:26s} kept={d['baseKept']} distinct={d['distinct']} px=" +
                         '/'.join(str(len(d['views'][v]['pixels'])) for v in VIEWS))

if __name__ == '__main__':
    main()
