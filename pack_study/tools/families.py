"""Cluster hats into silhouette families across all authors.

Distance = 1 - mean IoU of the front/right/back alpha masks, each pair at its
best shift within +-2 px (seating differs between authors by a pixel or two).
Average-linkage agglomerative clustering, cut at a fixed IoU.  Shape only --
colour, author and name play no part.  Writes data/families.json.
"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUT = float(sys.argv[1]) if len(sys.argv) > 1 else 0.55

def masks(r):
    s = np.array(Image.open(os.path.join(HERE, 'data', 'hats', r['id'] + '.png')).convert('RGBA'))[:, :, 3] > 0
    w = r['frame'][0]
    m = [s[:, i * w:(i + 1) * w] for i in (0, 1, 3)]
    out = []
    for v in m:
        c = np.zeros((24, 24), bool); h, ww = v.shape; c[:min(h, 24), :min(ww, 24)] = v[:24, :24]; out.append(c)
    return np.stack(out)

def main():
    recs = json.load(open(os.path.join(HERE, 'data', 'hats.json')))
    M = np.stack([masks(r) for r in recs]).astype(np.uint8)          # n,3,24,24
    n = len(recs); best = np.zeros((n, n), np.float32)
    area = M.sum(axis=(2, 3)).astype(np.float32)                       # n,3
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            S = np.roll(np.roll(M, dy, axis=2), dx, axis=3)
            inter = np.einsum('avij,bvij->abv', M.astype(np.float32), S.astype(np.float32))
            union = area[:, None, :] + area[None, :, :] - inter
            iou = np.where(union > 0, inter / np.maximum(union, 1), 1.0).mean(axis=2)
            best = np.maximum(best, iou)
    best = np.maximum(best, best.T)
    clusters = [[i] for i in range(n)]
    sim = best.copy(); np.fill_diagonal(sim, -1)
    active = list(range(n))
    C = {i: [i] for i in range(n)}
    while True:
        ids = list(C)
        if len(ids) < 2: break
        bi, bj, bv = None, None, -1
        A = np.array(ids)
        sub = sim[np.ix_(A, A)]
        k = np.unravel_index(np.argmax(sub), sub.shape)
        bv = sub[k]
        if bv < CUT: break
        i, j = A[k[0]], A[k[1]]
        ni, nj = len(C[i]), len(C[j])
        sim[i, :] = (sim[i, :] * ni + sim[j, :] * nj) / (ni + nj); sim[:, i] = sim[i, :]; sim[i, i] = -1
        sim[j, :] = -1; sim[:, j] = -1
        C[i] += C.pop(j)
    fams = sorted(C.values(), key=len, reverse=True)
    out = []
    for k, f in enumerate(fams):
        authors = sorted({recs[i]['author'] for i in f})
        out.append({'family': k, 'size': len(f), 'authors': authors, 'members': [recs[i]['id'] for i in f],
                    'names': [recs[i]['name'] for i in f]})
    json.dump(out, open(os.path.join(HERE, 'data', 'families.json'), 'w'), indent=1)
    multi = [o for o in out if len(o['authors']) >= 2]
    print(f'cut={CUT} families={len(out)} singletons={sum(o["size"]==1 for o in out)} multi-author={len(multi)}')
    for o in out[:40]:
        print(f"{o['family']:3d} n={o['size']:3d} authors={len(o['authors'])} {', '.join(sorted(set(x[:14] for x in o['names'])))[:110]}")

if __name__ == '__main__':
    main()
