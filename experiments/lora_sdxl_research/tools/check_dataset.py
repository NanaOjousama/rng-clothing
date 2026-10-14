"""Validate a built dataset (analysis tool; uses the .venv PIL).  Fails loudly.
Checks per image: canvas size; outside the 20x20 grid is exactly the background colour;
every BLOCKxBLOCK cell is ONE colour (block-exact, nothing resampled); caption is ASCII,
starts with the trigger, names the view.  Across the set: no construction in both splits.
Also writes contact.png (first 48 train + all holdout, nearest x0.25).
usage: source tools/env.sh; python experiments/lora_sdxl_research/tools/check_dataset.py <dataset_dir>"""
import json, os, sys
from PIL import Image
D = sys.argv[1]; M = json.load(open(os.path.join(D, 'manifest.json')))
CAN, BLK, OFF, BG = M['canvas'], M['block'], M['offset'], tuple(M['background'])
errors = []
for it in M['items']:
    sub = os.path.join('train', f"1_{M['trigger']}") if it['split'] == 'train' else 'holdout'
    p = os.path.join(D, sub, it['file'])
    im = Image.open(p + '.png').convert('RGB')
    if im.size != (CAN, CAN): errors.append((it['file'], 'size', im.size)); continue
    px = im.load()
    for (x, y) in ((0, 0), (CAN - 1, CAN - 1), (OFF - 1, OFF - 1), (OFF + 20 * BLK, OFF)):
        if px[x, y] != BG: errors.append((it['file'], 'background', (x, y), px[x, y]))
    for ly in range(20):
        for lx in range(20):
            x0, y0 = OFF + lx * BLK, OFF + ly * BLK
            c = px[x0, y0]
            if any(px[x0 + dx, y0 + dy] != c for dx in (0, BLK // 2, BLK - 1) for dy in (0, BLK // 2, BLK - 1)):
                errors.append((it['file'], 'block not uniform', lx, ly)); break
    cap = open(p + '.txt', encoding='ascii').read()
    if not cap.startswith(M['trigger'] + ', ') or f"{it['view']} view" not in cap: errors.append((it['file'], 'caption', cap[:40]))
tr = {i['construction'] for i in M['items'] if i['split'] == 'train'}
ho = {i['construction'] for i in M['items'] if i['split'] == 'holdout'}
if tr & ho: errors.append(('split', 'construction in both', sorted(tr & ho)[:5]))
sel = [i for i in M['items'] if i['split'] == 'train'][:48] + [i for i in M['items'] if i['split'] == 'holdout']
T = CAN // 4; cols = 10
sheet = Image.new('RGB', (cols * T, ((len(sel) + cols - 1) // cols) * T), (40, 40, 40))
for k, it in enumerate(sel):
    sub = os.path.join('train', f"1_{M['trigger']}") if it['split'] == 'train' else 'holdout'
    sheet.paste(Image.open(os.path.join(D, sub, it['file'] + '.png')).convert('RGB').resize((T, T), Image.NEAREST),
                ((k % cols) * T, (k // cols) * T))
sheet.save(os.path.join(D, 'contact.png'))
print('items', len(M['items']), '| errors', len(errors))
for e in errors[:20]: print('  ', e)
sys.exit(1 if errors else 0)
