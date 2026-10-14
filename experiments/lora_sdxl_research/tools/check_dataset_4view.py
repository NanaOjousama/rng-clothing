"""Validate the four-view dataset (analysis, .venv PIL).  Fails loudly.
  * every 16-px cell is ONE colour; margins and gutters are pure background
  * each quadrant decodes back to EXACTLY the author's 20x20 view (opaque pixels, from library.json)
  * each __mx image is exactly the mirror-swap of its original (x -> 19-x, right<->left)
  * no construction in both splits; captions ASCII, start with the trigger + layout
  * writes aug_pairs.png: original | augmented for 8 random augmented hats (x2 per cell)
usage: (repo root) source tools/env.sh; python experiments/lora_sdxl_research/tools/check_dataset_4view.py"""
import json, os, random, sys
from PIL import Image
ROOT = '/run/media/deck/USD00/RNG_clothing'; D = os.path.join(ROOT, 'experiments', 'lora_sdxl_research', 'dataset', 'phase2_4view_512' if sys.argv[1:] == ['512'] else 'phase2_4view')
M = json.load(open(os.path.join(D, 'manifest.json')))
CELL, MAR, GRID, BG = M['cell'], M['margin'], M['grid'], tuple(M['background'])
Q = {k: tuple(v) for k, v in M['quadrants'].items()}
VIEWS = ['front', 'right', 'left', 'back']
L = {c['id']: c for c in json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))['constructions']}
errors = []


def path(it): return os.path.join(D, *(('train', '1_' + M['trigger']) if it['split'] == 'train' else ('holdout',)), it['file'])


def decode(im):
    px = im.load(); cells = {}
    for ly in range(GRID):
        for lx in range(GRID):
            x0, y0 = MAR + lx * CELL, MAR + ly * CELL; c = px[x0, y0]
            if any(px[x0 + dx, y0 + dy] != c for dx in (0, CELL // 2, CELL - 1) for dy in (0, CELL // 2, CELL - 1)):
                return None, (lx, ly)
            cells[(lx, ly)] = c
    return cells, None


def views(cells):
    V = {}
    for v, (qx, qy) in Q.items():
        V[v] = {(x, y): cells[(qx + x, qy + y)] for y in range(20) for x in range(20) if cells[(qx + x, qy + y)] != BG}
    return V


def source(it):
    c = L[it['construction']]; w = next(w for w in c['colourways'] if w['source'] == it['source']); pal = w['palette']
    V = {v: {} for v in VIEWS}
    for k, g in enumerate(c['grid']):
        if g >= 0 and pal[g][3] == 255:
            y, x = divmod(k, 80); V[VIEWS[x // 20]][(x % 20, y)] = tuple(pal[g][:3])
    return V


def mswap(V):
    m = lambda d: {(19 - x, y): p for (x, y), p in d.items()}
    return {'front': m(V['front']), 'right': m(V['left']), 'left': m(V['right']), 'back': m(V['back'])}


dec = {}
for it in M['items']:
    im = Image.open(path(it) + '.png').convert('RGB')
    if im.size != (M['canvas'],) * 2: errors.append((it['file'], 'size')); continue
    px = im.load()
    for (x, y) in ((0, 0), (MAR - 1, MAR - 1), (M['canvas'] - 1, M['canvas'] - 1)):
        if px[x, y] != BG: errors.append((it['file'], 'margin not background'))
    cells, bad = decode(im)
    if cells is None: errors.append((it['file'], 'cell not uniform', bad)); continue
    for lx in range(GRID):
        for ly in range(GRID):
            in_gut = (20 <= lx < 20 + M['gutter']) or (20 <= ly < 20 + M['gutter'])
            if in_gut and cells[(lx, ly)] != BG: errors.append((it['file'], 'gutter not background', lx, ly)); break
    V = views(cells); dec[it['file']] = V
    want = source(it) if not it['augmented'] else mswap(source(it))
    for v in VIEWS:
        if V[v] != want[v]: errors.append((it['file'], f'{v} differs from source', len(set(V[v].items()) ^ set(want[v].items())))); break
    cap = open(path(it) + '.txt', encoding='ascii').read()
    if not cap.startswith(M['trigger'] + ', ' + M['layout_caption']): errors.append((it['file'], 'caption'))
tr = {i['construction'] for i in M['items'] if i['split'] == 'train'}; ho = {i['construction'] for i in M['items'] if i['split'] == 'holdout'}
if tr & ho: errors.append(('split', 'leak', sorted(tr & ho)[:5]))
aug = [i for i in M['items'] if i['augmented']]; random.seed(3); pick = random.sample(aug, min(8, len(aug)))
S = 2; W = M['canvas'] // CELL * S * 4 // 2
sheet = Image.new('RGB', (2 * (GRID + 2) * S * 4, len(pick) * (GRID + 2) * S * 4 // 2 + 4), (60, 60, 60))
for r, it in enumerate(pick):
    orig = it['file'][:-4]
    for j, f in enumerate((orig, it['file'])):
        im = Image.open(os.path.join(D, 'train', '1_' + M['trigger'], f + '.png')).convert('RGB')
        sm = im.resize((M['canvas'] // 4 * 2 // 2, M['canvas'] // 4 * 2 // 2), Image.NEAREST)
        sheet.paste(sm, (j * (sm.width + 8), r * (sm.height + 6)))
sheet = sheet.crop((0, 0, 2 * (M['canvas'] // 4) + 8, len(pick) * (M['canvas'] // 4 + 6)))
sheet.save(os.path.join(D, 'aug_pairs.png'))
print('items', len(M['items']), '| augmented', len(aug), '| errors', len(errors))
for e in errors[:15]: print('  ', e)
sys.exit(1 if errors else 0)
