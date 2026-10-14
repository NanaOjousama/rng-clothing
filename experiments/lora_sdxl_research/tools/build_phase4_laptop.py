"""Rebuild a phase-4 dataset on the GPU host from its compact export, pixel-identical to the Deck build
(validated on the Deck by check_dataset_phase4.py: every image == its compact item).  PIL only.
Witch-pack images go to train/2_sdvhat (their own subset; num_repeats set in the dataset toml), the rest to
train/1_sdvhat; holdout to holdout/.  The Deck manifest.json is copied next to it for the eval scripts.
usage: python build_phase4_laptop.py <ds>_compact.json <manifest.json> <out_dir>"""
import json, os, re, shutil, sys
from PIL import Image
S = json.load(open(sys.argv[1], encoding='utf-8')); out = sys.argv[3]; M = S['meta']; A = S['alphabet']
CAN, CELL, MAR, FW = M['canvas'], M['cell'], M['margin'], M['frame']; BG = tuple(M['background'])
views = [v for v in ('front', 'right', 'left', 'back') if v in M['quadrants']]
n = 0
for it in S['items']:
    sub = 'holdout' if it['split'] == 'holdout' else os.path.join('train', ('2_' if it['subset'] == 'witch' else '1_') + M['trigger'])
    d = os.path.join(out, sub); os.makedirs(d, exist_ok=True)
    im = Image.new('RGB', (CAN, CAN), BG); px = im.load()
    for v, s in zip(views, it['views']):
        s = re.sub(r'\((\d+)\)', lambda m: '.' * int(m.group(1)), s); assert len(s) == FW * FW, (it['file'], v, len(s))
        qx, qy = M['quadrants'][v]
        for i, ch in enumerate(s):
            if ch == '.': continue
            c = tuple(it['pal'][A.index(ch)]); x0 = MAR + (qx + i % FW) * CELL; y0 = MAR + (qy + i // FW) * CELL
            for yy in range(y0, y0 + CELL):
                for xx in range(x0, x0 + CELL): px[xx, yy] = c
    im.save(os.path.join(d, it['file'] + '.png'))
    open(os.path.join(d, it['file'] + '.txt'), 'w', encoding='ascii').write(it['caption']); n += 1
shutil.copyfile(sys.argv[2], os.path.join(out, 'manifest.json'))
print('built', n, 'images in', out)
