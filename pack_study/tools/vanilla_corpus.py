"""Make the corpus agree with real vanilla.  Rerunnable; run after extract_hats.py.

1. RECREDIT: any 20x20 corpus hat pixel-identical to a vanilla hat is ConcernedApe's,
   whatever pack it was found in (replacement sheets keep unchanged vanilla cells).
   ids and names are kept so existing references (decorations_approved, demos) hold;
   `foundIn` keeps the pack it came from, `creditFix` records the old author.
2. BACKFILL: every vanilla hat not already present -- exactly, or as the same art
   moved by <=2 px in every view -- is added as ConcernedApe, name `hats_<index>`
   (the convention the inferred vanilla records already use).
All matched/added records get `vanillaIndex` + `vanillaName`.
Writes data/hats.json (+ data/hats/<id>.png for added hats), data/vanilla_corpus_log.json.
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vanilla import CONTENT, clean, load_vanilla

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(HERE, 'data', *p)
TOL = 3


def same(a, b):
    m = a[..., 3] > 0
    return (m == (b[..., 3] > 0)).all() and np.abs(a[m] - b[m]).max(initial=0) <= TOL


def shift(v, dx, dy):
    out = np.zeros_like(v)
    h, w = v.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = v[ys, xs]
    return out


def same_moved(a, b, r=2):
    """Same art with each view moved by at most r px (no cropping)."""
    for k in range(4):
        va, vb = a[:, k * 20:(k + 1) * 20], b[:, k * 20:(k + 1) * 20]
        if not any((sv[..., 3] > 0).sum() == (va[..., 3] > 0).sum() and same(sv, vb)
                   for dy in range(-r, r + 1) for dx in range(-r, r + 1)
                   for sv in [shift(va, dx, dy)]):
            return False
    return True


def main():
    recs = json.load(open(D('hats.json')))
    van = load_vanilla()
    arr = {}
    for r in recs:
        if r['frame'] == [20, 20]:
            arr[r['id']] = clean(np.asarray(Image.open(D('hats', r['id'] + '.png')).convert('RGBA'), dtype=np.int16))
    log = {'recredited': [], 'alreadyVanilla': [], 'presentMoved': [], 'added': []}
    present = set()
    for r in recs:
        a = arr.get(r['id'])
        if a is None: continue
        for idx, v in van.items():
            if same(v['arr'], a):
                r['vanillaIndex'], r['vanillaName'] = idx, v['name']
                present.add(idx)
                if r['author'] != 'ConcernedApe':
                    r.setdefault('foundIn', r['pack'])
                    r['creditFix'] = {'was': r['author'], 'why': 'pixel-identical to vanilla hats.png cell %d' % idx}
                    r['author'] = 'ConcernedApe'
                    log['recredited'].append([r['id'], r['creditFix']['was'], idx, v['name']])
                elif 'creditFix' not in r:
                    log['alreadyVanilla'].append([r['id'], idx, v['name']])
                break
    for idx, v in sorted(van.items()):
        if idx in present: continue
        moved = [r['id'] for r in recs if r['id'] in arr and same_moved(v['arr'], arr[r['id']])]
        if moved:
            log['presentMoved'].append([idx, v['name'], moved])
            continue
        rid = f'concernedape__hats_{idx}__vanilla'
        if any(r['id'] == rid for r in recs): continue
        Image.fromarray(v['arr'].astype(np.uint8), 'RGBA').save(D('hats', rid + '.png'))
        recs.append({'author': 'ConcernedApe', 'pack': 'vanilla (Content unpacked hats.png)', 'name': f'hats_{idx}',
                     'format': 'sheet', 'scale': [4], 'colourable': False, 'flags': {},
                     'src': os.path.join(CONTENT, 'Characters', 'Farmer', 'hats.png'), 'cell': idx,
                     'id': rid, 'frame': [20, 20], 'missing': [], 'vanillaIndex': idx, 'vanillaName': v['name']})
        log['added'].append([rid, idx, v['name']])
    # log from record state, so a rerun reports the same corpus truthfully
    log['recredited'] = [[r['id'], r['creditFix']['was'], r['vanillaIndex'], r['vanillaName']] for r in recs if 'creditFix' in r]
    log['added'] = [[r['id'], r['vanillaIndex'], r['vanillaName']] for r in recs if r['id'].endswith('__vanilla')]
    log['alreadyVanilla'] = [[r['id'], r['vanillaIndex'], r['vanillaName']] for r in recs
                             if 'vanillaIndex' in r and 'creditFix' not in r and not r['id'].endswith('__vanilla')]
    json.dump(recs, open(D('hats.json'), 'w'), indent=1)
    json.dump(log, open(D('vanilla_corpus_log.json'), 'w'), indent=1)
    from collections import Counter
    print({k: len(v) for k, v in log.items()}, '| corpus', len(recs),
          '| ConcernedApe', sum(r['author'] == 'ConcernedApe' for r in recs))
    print('recredited from', Counter(x[1] for x in log['recredited']))
    for m in log['presentMoved']: print('  present moved:', m)


if __name__ == '__main__':
    main()
