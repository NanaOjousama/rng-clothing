"""Is 'mirror every view + swap right<->left' a valid augmentation for Stardew hats?  Pure Python.
Measured on every studied 20x20 construction with 4 authored views (pack_study library):
  left_is_mirror_right  left view == horizontal mirror of right view (exact pixels)
  front_symmetric       front == its own mirror (exact), and >=90% of pixels
  light (per view)      interior OKLab L, left half minus right half (positive = lit from screen-left)
If authors light from a fixed screen side, mirroring moves the light to the wrong side.
-> analysis/aug_check.json + printout"""
import json, os, statistics, sys
ROOT = '/run/media/deck/USD00/RNG_clothing'
sys.path.insert(0, os.path.join(ROOT, 'pack_study', 'gen'))
from colour import to_lch
VIEWS = ['front', 'right', 'left', 'back']
L = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))
cons = [c for c in L['constructions'] if not c['missing'] and c['frame'] == [20, 20]]
res = []
for c in cons:
    pal = c['colourways'][0]['palette']
    V = {}
    for vi, v in enumerate(VIEWS):
        V[v] = {(x % 20, y): tuple(pal[g]) for k, g in enumerate(c['grid']) if g >= 0 for y, x in [divmod(k, 80)] if x // 20 == vi}
    def mirror(d):
        if not d: return {}
        xs = [x for x, _ in d]; a = min(xs) + max(xs)
        return {(a - x, y): p for (x, y), p in d.items()}
    def same(a, b, frac=1.0):
        if not a or not b: return False
        keys = set(a) | set(b); eq = sum(a.get(k) == b.get(k) for k in keys)
        return eq / len(keys) >= frac
    def light(d):
        op = set(d); inner = [(x, y) for x, y in d if all((x + dx, y + dy) in op for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        if len(inner) < 8: return None
        cx = statistics.mean(x for x, _ in inner)
        l = [to_lch(d[p])[0] for p in inner if p[0] < cx]; r = [to_lch(d[p])[0] for p in inner if p[0] > cx]
        return statistics.mean(l) - statistics.mean(r) if l and r else None
    res.append({'id': c['id'], 'author': c['author'],
                'left_is_mirror_right': same(V['left'], mirror(V['right'])),
                'left_is_mirror_right_90': same(V['left'], mirror(V['right']), 0.9),
                'front_symmetric': same(V['front'], mirror(V['front'])),
                'front_symmetric_90': same(V['front'], mirror(V['front']), 0.9),
                'light': {v: light(V[v]) for v in VIEWS}})
json.dump(res, open(os.path.join(ROOT, 'experiments', 'lora_sdxl_research', 'analysis', 'aug_check.json'), 'w'), indent=0)
n = len(res)
for k in ('left_is_mirror_right', 'left_is_mirror_right_90', 'front_symmetric', 'front_symmetric_90'):
    print(f'{k:26s} {sum(r[k] for r in res)}/{n}')
for v in VIEWS:
    xs = [r['light'][v] for r in res if r['light'][v] is not None]
    pos = sum(x > 0.02 for x in xs); neg = sum(x < -0.02 for x in xs)
    print(f'light {v:5s} n={len(xs)} lit-from-screen-left {pos}  from-right {neg}  flat {len(xs) - pos - neg}  median {statistics.median(xs):+.3f}')
by = {}
for r in res:
    x = r['light']['front']
    if x is not None: by.setdefault(r['author'], []).append(x)
print('front light by author (median, n):', {a: (round(statistics.median(v), 3), len(v)) for a, v in sorted(by.items(), key=lambda t: -len(t[1]))[:10]})
