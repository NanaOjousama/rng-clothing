"""Measure every normalised hat: per-view geometry + style fingerprint.

Writes data/hat_features.json and prints a per-author style table.
Everything is measured from source pixels; nothing here is a judgement.
"""
import colorsys, json, os, statistics as st, sys
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']

def frames(rec):
    s = Image.open(os.path.join(HERE, 'data', 'hats', rec['id'] + '.png')).convert('RGBA')
    w, h = rec['frame']
    return [s.crop((i * w, 0, i * w + w, h)) for i in range(4)]

def lum(p):
    return (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) / 255

def view_features(f):
    w, h = f.size; px = f.load()
    op = {(x, y) for x in range(w) for y in range(h) if px[x, y][3] > 0}
    if not op: return None
    xs = [x for x, _ in op]; ys = [y for _, y in op]
    edge = {(x, y) for (x, y) in op if any((x + dx, y + dy) not in op for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    inner = op - edge
    cols = {px[p][:3] for p in op}
    L = lambda S: st.mean(lum(px[p]) for p in S) if S else 0
    sat = lambda p: colorsys.rgb_to_hsv(*(c / 255 for c in px[p][:3]))[1]
    changes = sum(1 for (x, y) in inner for dx, dy in ((1, 0), (0, 1)) if (x + dx, y + dy) in op and px[x + dx, y + dy][:3] != px[x, y][:3])
    cx = (min(xs) + max(xs)) / 2
    tl = [p for p in inner if p[0] < cx and p[1] < (min(ys) + max(ys)) / 2]
    br = [p for p in inner if p[0] > cx and p[1] > (min(ys) + max(ys)) / 2]
    return {
        'bbox': [min(xs), min(ys), max(xs) + 1, max(ys) + 1], 'w': max(xs) - min(xs) + 1, 'h': max(ys) - min(ys) + 1,
        'area': len(op), 'ncol': len(cols),
        'edgeL': round(L(edge), 3), 'innerL': round(L(inner), 3),
        'edgeDark': round(sum(lum(px[p]) < 0.22 for p in edge) / len(edge), 3),
        'gray': round(sum(sat(p) < 0.08 for p in op) / len(op), 3),
        'semi': round(sum(0 < px[p][3] < 255 for p in op) / len(op), 3),
        'detail': round(changes / max(1, 2 * len(inner)), 3),
        'lightTLminusBR': round(L(tl) - L(br), 3) if tl and br else None,
        'mask': [[int((x, y) in op) for x in range(w)] for y in range(h)],
    }

def main():
    recs = json.load(open(os.path.join(HERE, 'data', 'hats.json')))
    out = []
    for r in recs:
        fr = frames(r)
        vf = {v: view_features(f) for v, f in zip(VIEWS, fr)}
        fv = vf['front']
        left_mirror = None
        if vf['right'] and vf['left']:
            left_mirror = fr[1].transpose(Image.FLIP_LEFT_RIGHT).tobytes() == fr[2].tobytes()
        sym = None
        if fv:
            m = fv['mask']; sym = round(sum(row[x] == row[len(row) - 1 - x] for row in m for x in range(len(row))) / (len(m) * len(m[0])), 3)
        out.append({'id': r['id'], 'author': r['author'], 'pack': r['pack'], 'name': r['name'],
                    'colourable': r['colourable'], 'views': vf, 'leftIsMirror': left_mirror, 'frontSym': sym})
    json.dump(out, open(os.path.join(HERE, 'data', 'hat_features.json'), 'w'))
    by = {}
    for o in out: by.setdefault(o['author'], []).append(o)
    keys = ['ncol', 'edgeDark', 'edgeL', 'innerL', 'gray', 'semi', 'detail', 'lightTLminusBR', 'w', 'h']
    print(f"{'author':18s} {'n':>3s} " + ' '.join(f'{k[:8]:>8s}' for k in keys) + '  mirrorL')
    for a, os_ in sorted(by.items(), key=lambda kv: -len(kv[1])):
        fv = [o['views']['front'] for o in os_ if o['views']['front']]
        med = lambda k: st.median([v[k] for v in fv if v[k] is not None]) if fv else 0
        mir = sum(bool(o['leftIsMirror']) for o in os_) / len(os_)
        print(f'{a[:18]:18s} {len(os_):3d} ' + ' '.join(f'{med(k):8.3f}' if isinstance(med(k), float) else f'{med(k):8}' for k in keys) + f'  {mir:.2f}')

if __name__ == '__main__':
    main()
