"""Fingerprint a phase-4 dataset: per image sha256(decoded RGB pixels) + sha256(caption), keyed by relative path.
Prints a per-folder count and one combined hash; writes the full list to <out_json>.  PIL only.
usage: python fingerprint_phase4.py <dataset_dir> <out_json>"""
import hashlib, json, os, sys
from PIL import Image
D, out = sys.argv[1], sys.argv[2]; rows = {}
for dp, _, fs in os.walk(D):
    for f in sorted(fs):
        if not f.endswith('.png') or f.startswith('contact'): continue
        rel = os.path.relpath(os.path.join(dp, f), D).replace('\\', '/')
        im = Image.open(os.path.join(dp, f)).convert('RGB')
        cap = open(os.path.join(dp, f[:-4] + '.txt'), 'rb').read()
        rows[rel] = [im.size[0], im.size[1], hashlib.sha256(im.tobytes()).hexdigest(), hashlib.sha256(cap).hexdigest()]
folders = {}
for k in rows: folders[k.rsplit('/', 1)[0]] = folders.get(k.rsplit('/', 1)[0], 0) + 1
man = hashlib.sha256(open(os.path.join(D, 'manifest.json'), 'rb').read()).hexdigest()
comb = hashlib.sha256(json.dumps(sorted(rows.items())).encode()).hexdigest()
json.dump({'images': len(rows), 'folders': folders, 'manifest_sha256': man, 'combined': comb, 'rows': rows}, open(out, 'w'))
print(json.dumps({'images': len(rows), 'folders': folders, 'manifest_sha256': man[:16], 'combined': comb}))
