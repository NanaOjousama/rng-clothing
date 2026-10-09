"""Find registered variant sets inside each author's work.

RECOLOUR  : identical alpha mask in all 4 views -> same construction, palette swap.
            Pixel-to-pixel colour mapping between members gives the palette roles.
ADDON     : mask A is a subset of mask B in all 4 views and B's pixels that lie
            inside A keep A's *structure* (same colour-index pattern) -> B = A + part.
            The extra pixels of B are a candidate part, already in all 4 views.
PATTERN   : identical mask, but colour-index structure differs (not a pure remap)
            -> same construction, different surface pattern (e.g. plaid vs solid).
Writes data/variant_sets.json.
"""
import json, os
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(r):
    s = Image.open(os.path.join(HERE, 'data', 'hats', r['id'] + '.png')).convert('RGBA')
    return s

def mask(s):
    return tuple(a > 0 for a in s.getchannel('A').tobytes())

def is_remap(sa, sb, region=None):
    """True if a single colour->colour function maps sa onto sb (both ways) over region."""
    fa, fb = {}, {}
    pa, pb = sa.get_flattened_data(), sb.get_flattened_data()
    for i, (x, y) in enumerate(zip(pa, pb)):
        if region is not None and not region[i]: continue
        if x[3] == 0 and y[3] == 0: continue
        if fa.setdefault(x, y) != y or fb.setdefault(y, x) != x:
            return False
    return True

def remap_score(sa, sb, region):
    """Fraction of region pixels consistent with the majority colour mapping sa->sb.
    Pixels that break it are where B paints over A (occluding add-on) or re-shades."""
    from collections import Counter
    pa, pb = sa.get_flattened_data(), sb.get_flattened_data()
    pairs = [(pa[i], pb[i]) for i in range(len(pa)) if region[i]]
    if not pairs: return 0, []
    best = {}
    for (x, y), n in Counter(pairs).most_common():
        best.setdefault(x, y)
    ok = [i for i in range(len(pa)) if region[i] and best.get(pa[i]) == pb[i]]
    return len(ok) / len(pairs), ok

def identity_kept(sa, sb, region):
    pa, pb = sa.get_flattened_data(), sb.get_flattened_data()
    idx = [i for i in range(len(pa)) if region[i]]
    return sum(pa[i] == pb[i] for i in idx) / max(1, len(idx))

def main():
    recs = json.load(open(os.path.join(HERE, 'data', 'hats.json')))
    by = {}
    for r in recs:
        by.setdefault((r['author'], tuple(r['frame'])), []).append(r)
    sets = []
    for (author, frame), rs in by.items():
        imgs = {r['id']: load(r) for r in rs}
        masks = {k: mask(v) for k, v in imgs.items()}
        groups = {}
        for r in rs: groups.setdefault(masks[r['id']], []).append(r['id'])
        for m, ids in groups.items():
            if len(ids) < 2: continue
            base = ids[0]
            remap = [i for i in ids[1:] if is_remap(imgs[base], imgs[i])]
            pattern = [i for i in ids[1:] if i not in remap]
            sets.append({'type': 'RECOLOUR' if not pattern else 'RECOLOUR+PATTERN', 'author': author,
                         'base': base, 'recolours': remap, 'patternVariants': pattern, 'size': len(ids)})
        keys = list(groups)
        for a in keys:
            for b in keys:
                if a == b: continue
                if all(y or not x for x, y in zip(a, b)) and sum(b) > sum(a):
                    ia, ib = groups[a][0], groups[b][0]
                    # Mask containment alone is coincidence-prone (a small clip "fits inside"
                    # any big hat).  Require the base to survive *unchanged* inside B and
                    # to be a real share of B.
                    if sum(a) < 0.2 * sum(b): continue
                    best = max(((identity_kept(imgs[ja], imgs[jb], a), ja, jb)
                                for ja in groups[a] for jb in groups[b]), default=None)
                    added = sum(b) - sum(a)
                    if best and best[0] >= 0.85 and added >= 3:
                        sets.append({'type': 'ADDON' if added >= 8 else 'TWEAK', 'author': author,
                                     'base': best[1], 'with': best[2], 'baseKept': round(best[0], 3),
                                     'addedPixels': added, 'basePixels': sum(a)})
    json.dump(sets, open(os.path.join(HERE, 'data', 'variant_sets.json'), 'w'), indent=1)
    from collections import Counter
    c = Counter((s['author'], s['type']) for s in sets)
    for (a, t), n in sorted(c.items()): print(f'{n:3d} {t:17s} {a}')
    print('recolour members total', sum(s.get('size', 0) for s in sets), '| addon pairs', sum(s['type'] == 'ADDON' for s in sets))

if __name__ == '__main__':
    main()
