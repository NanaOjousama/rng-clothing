"""Rebuild four-view sheets on the GPU host from the compact export (exact same pixels as the Deck
dataset: 704 canvas, 16-px cells, 2-cell gutter, magenta background).  PIL only.
usage: python build_subset_laptop.py subset_30_compact.json out_dir
-> out_dir/train/1_sdvhat/*.png+.txt, out_dir/holdout/*.png+.txt, out_dir/manifest.json"""
import json, os, re, sys
from PIL import Image
S = json.load(open(sys.argv[1])); out = sys.argv[2]; M = S['meta']; A = S['alphabet']
CAN, CELL, MAR = M['canvas'], M['cell'], M['margin']; BG = tuple(M['background'])
VIEWS = ['front', 'right', 'left', 'back']
for it in S['items']:
    d = os.path.join(out, 'train', '1_' + M['trigger']) if it['split'] == 'train' else os.path.join(out, 'holdout')
    os.makedirs(d, exist_ok=True)
    im = Image.new('RGB', (CAN, CAN), BG); px = im.load()
    for v, s in zip(VIEWS, it['views']):
        s = re.sub(r'\((\d+)\)', lambda m: '.' * int(m.group(1)), s); assert len(s) == 400, (it['file'], v, len(s))
        qx, qy = M['quadrants'][v]
        for i, ch in enumerate(s):
            if ch == '.': continue
            c = tuple(it['pal'][A.index(ch)]); x0 = MAR + (qx + i % 20) * CELL; y0 = MAR + (qy + i // 20) * CELL
            for yy in range(y0, y0 + CELL):
                for xx in range(x0, x0 + CELL): px[xx, yy] = c
    im.save(os.path.join(d, it['file'] + '.png'))
    open(os.path.join(d, it['file'] + '.txt'), 'w', encoding='ascii').write(it['caption'])
json.dump({**M, 'items': [{k: it[k] for k in ('file', 'split', 'caption')} for it in S['items']]}, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
print('built', len(S['items']), 'sheets in', out)
