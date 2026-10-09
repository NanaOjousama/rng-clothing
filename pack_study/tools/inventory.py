"""Inventory every third-party Fashion Sense item under the given roots.

One row per FS item (hat/shirt/pants/sleeves/shoes/accessory): pack, author,
item name, png, direction rects, and a content hash so duplicate copies of the
same pack collapse.  Read-only over the roots.
"""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from jsonl import load

KINDS = {'hat.json': 'hat', 'shirt.json': 'shirt', 'pants.json': 'pants',
         'sleeves.json': 'sleeves', 'shoes.json': 'shoes', 'accessory.json': 'accessory'}
SKIP = ('test-packs', '/output/', '.git', '.claude', 'fashion-sense-official',
        'FASHION SENSE', 'qc_bridge', '/mods/')

def pack_root(d, stop):
    while len(d) >= len(stop):
        if os.path.exists(os.path.join(d, 'manifest.json')):
            return d
        nd = os.path.dirname(d)
        if nd == d: break
        d = nd
    return None

def main(out, roots):
    rows, manifests = [], {}
    for root in roots:
        for dp, dn, fn in os.walk(root):
            if any(s in dp + '/' for s in SKIP): dn[:] = []; continue
            for f in fn:
                k = KINDS.get(f.lower())
                if not k: continue
                jp = os.path.join(dp, f)
                pr = pack_root(dp, root)
                if pr and pr not in manifests:
                    try: manifests[pr] = load(os.path.join(pr, 'manifest.json'))
                    except Exception as e: manifests[pr] = {'_err': str(e)}
                m = manifests.get(pr, {}) if pr else {}
                try: j = load(jp)
                except Exception as e: rows.append({'json': jp, 'err': str(e)}); continue
                pngs = sorted(p for p in os.listdir(dp) if p.lower().endswith('.png'))
                h = hashlib.sha1()
                for p in pngs: h.update(open(os.path.join(dp, p), 'rb').read())
                rows.append({
                    'kind': k, 'name': j.get('Name'), 'json': jp, 'dir': dp,
                    'pngs': pngs, 'hash': h.hexdigest()[:16],
                    'pack': m.get('Name') or (os.path.basename(pr) if pr else '?'),
                    'author': m.get('Author', '?'), 'uid': m.get('UniqueID', '?'),
                    'packRoot': pr,
                })
    seen, uniq = {}, []
    for r in rows:
        if 'err' in r: continue
        if r['hash'] in seen: seen[r['hash']]['copies'].append(r['dir']); continue
        r['copies'] = []; seen[r['hash']] = r; uniq.append(r)
    json.dump({'items': uniq, 'errors': [r for r in rows if 'err' in r]}, open(out, 'w'), indent=1)
    from collections import Counter
    c = Counter((r['author'], r['pack'], r['kind']) for r in uniq)
    for (a, p, k), n in sorted(c.items()): print(f'{n:4d}  {k:9s} {a[:22]:22s} {p}')
    print('unique items', len(uniq), 'raw', len(rows), 'errors', sum('err' in r for r in rows))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
