"""Render ADDON evidence: base | with | extracted part (pixels of B not explained by A), 4 views each."""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from variants import remap_score, mask
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sets = [s for s in json.load(open(os.path.join(HERE, 'data', 'variant_sets.json'))) if s['type'] in ('ADDON', 'TWEAK')]
S, rows = 3, []
for s in sets:
    a = Image.open(os.path.join(HERE, 'data', 'hats', s['base'] + '.png')).convert('RGBA')
    b = Image.open(os.path.join(HERE, 'data', 'hats', s['with'] + '.png')).convert('RGBA')
    pa, pb = a.get_flattened_data(), b.get_flattened_data()
    ok = [i for i in range(len(pa)) if pa[i][3] and pa[i] == pb[i]]
    part = b.copy(); px = part.load(); w = b.width
    for i in ok: px[i % w, i // w] = (0, 0, 0, 0)
    rows.append((s, [a, b, part]))
W = 3 * (80 * S + 10); im = Image.new('RGBA', (W, len(rows) * (20 * S + 14)), (118, 128, 112, 255)); d = ImageDraw.Draw(im)
for k, (s, ims) in enumerate(rows):
    y = k * (20 * S + 14)
    d.text((2, y), f"{s['author'][:14]} {s['base'].split('__')[1][:22]} + -> {s['with'].split('__')[1][:22]} kept={s['baseKept']} {s['type']}", fill='white')
    for j, x in enumerate(ims):
        im.alpha_composite(x.resize((x.width * S, x.height * S), Image.NEAREST), (j * (80 * S + 10), y + 12))
im.save(os.path.join(HERE, 'out', 'addon_evidence.png')); print(len(rows))
