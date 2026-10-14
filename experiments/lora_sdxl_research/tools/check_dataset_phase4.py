"""Validate the phase-4 datasets (analysis, .venv PIL).  Fails loudly (exit 1 on any error).
  1  every cell is ONE colour; margins pure background; canvas size
  2  each image decodes EXACTLY to its compact-export item (so the laptop rebuild is pixel-identical)
  3  each __mx image is exactly the mirror-swap of its original (x -> 23-x, right<->left)
  4  no construction in both splits; witch holdout: nearest TRAIN front silhouette IoU (mirror included) reported
  5  captions: ASCII, trigger + layout first, frame word, witch subset carries a family phrase, no vanilla slot names
     (hats_N) and no brimmed-hat words on witch hats
  6  provenance: every pack source sits under a REFERENCE raw folder; nothing from a generated experiment
  7  background: the 5 corpus colours closest to it (OKLab)
  -> analysis/phase4_validation.json, dataset/<ds>/contact_witch.png (every witch item, x2 per cell, caption below)
usage: (repo root) source tools/env.sh; python experiments/lora_sdxl_research/tools/check_dataset_phase4.py"""
import json, math, os, re, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(HERE, 'tools'))
ROOT = os.path.dirname(os.path.dirname(HERE)); sys.path.insert(0, os.path.join(ROOT, 'pack_study', 'gen'))
from colour import to_lch
VIEWS = ['front', 'right', 'left', 'back']
FORBIDDEN = ('witch_front_', 'witch_cleanup', 'witch_side_repair', 'lora_worn', 'witch_hat_quality', 'esm_hairmode', 'ai_original')
REF_OK = ('witch_reference_packs_01/raw/', 'witch_reference_packs_02/raw/', 'wildwood_reference_01/raw/', 'bloom_reference_01/raw/')
BRIM_WORDS = ['cowboy hat', 'bowler hat', 'top hat', 'fedora', 'boater', 'sombrero', 'straw hat', 'sun hat', 'panama']
FAMS = ('short witch hat', 'tall floppy witch hat', 'classic pointed witch hat', 'low sweeping witch hat')
report = {}; bad = 0


def oklab(p):
    L, C, H = to_lch(p); return L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H))


for ds in ('phase4_4view_512', 'phase4_front_512'):
    D = os.path.join(HERE, 'dataset', ds); M = json.load(open(os.path.join(D, 'manifest.json')))
    C = json.load(open(os.path.join(HERE, 'dataset', f'{ds}_compact.json'), encoding='utf-8')); A = C['alphabet']
    comp = {it['file']: it for it in C['items']}
    CELL, MAR, GRID, FW, BG = M['cell'], M['margin'], M['grid'], M['frame'], tuple(M['background'])
    Q = {k: tuple(v) for k, v in M['quadrants'].items()}; views = [v for v in VIEWS if v in Q]
    E = []; dec = {}

    def path(it):
        sub = 'holdout' if it['split'] == 'holdout' else os.path.join('train', ('2_' if it['subset'] == 'witch' else '1_') + M['trigger'])
        return os.path.join(D, sub, it['file'])

    for it in M['items']:
        im = Image.open(path(it) + '.png').convert('RGB')
        if im.size != (M['canvas'],) * 2: E.append((it['file'], 'size')); continue
        px = im.load(); V = {}
        if any(px[x, y] != BG for x, y in ((0, 0), (MAR - 1, MAR - 1), (M['canvas'] - 1, M['canvas'] - 1), (M['canvas'] - MAR, 5))):
            E.append((it['file'], 'margin not background'))
        for v in views:
            qx, qy = Q[v]; d = {}
            for y in range(FW):
                for x in range(FW):
                    x0, y0 = MAR + (qx + x) * CELL, MAR + (qy + y) * CELL; c = px[x0, y0]
                    if any(px[x0 + a, y0 + b] != c for a in (0, CELL // 2, CELL - 1) for b in (0, CELL // 2, CELL - 1)):
                        E.append((it['file'], f'non-uniform cell {v} {x},{y}')); break
                    if c != BG: d[(x, y)] = c
            V[v] = d
        dec[it['file']] = V
        ci = comp.get(it['file'])                                                  # 2: compact identity
        if ci is None: E.append((it['file'], 'missing from compact')); continue
        for v, s in zip(views, ci['views']):
            s = re.sub(r'\((\d+)\)', lambda m: '.' * int(m.group(1)), s)
            want = {(i % FW, i // FW): tuple(ci['pal'][A.index(ch)]) for i, ch in enumerate(s) if ch != '.'}
            if want != V[v]: E.append((it['file'], f'compact mismatch {v}'))
        cap = it['caption']                                                        # 5: captions
        if not cap.isascii(): E.append((it['file'], 'caption not ascii'))
        if not cap.startswith(f"{M['trigger']}, {M['layout_caption']}, "): E.append((it['file'], 'caption prefix'))
        if '24x24 sprites' not in cap: E.append((it['file'], 'frame word'))
        if re.search(r'\bhats_\d+\b', cap): E.append((it['file'], 'vanilla slot name in caption'))
        if it['subset'] == 'witch' and not any(f in cap for f in FAMS): E.append((it['file'], 'witch item without family phrase'))
        if it.get('family') and any(w in cap for w in BRIM_WORDS): E.append((it['file'], 'brimmed-hat word on a witch hat'))
        src = it.get('source', '')                                                 # 6: provenance
        if any(f in src for f in FORBIDDEN): E.append((it['file'], f'generated-experiment source {src}'))
        if it['source_kind'] == 'reference_pack' and not src.startswith(REF_OK): E.append((it['file'], f'not a reference raw folder {src}'))
    for it in M['items']:                                                          # 3: mirror pairs
        if not it['augmented']: continue
        o, a = dec[it['file'][:-4]], dec[it['file']]; m = lambda d: {(FW - 1 - x, y): p for (x, y), p in d.items()}
        want = {'front': m(o['front'])} if views == ['front'] else {'front': m(o['front']), 'right': m(o['left']), 'left': m(o['right']), 'back': m(o['back'])}
        if want != a: E.append((it['file'], 'mirror pair mismatch'))
    sp = {}                                                                         # 4: split leak
    for it in M['items']: sp.setdefault(it['construction'], set()).add(it['split'])
    E += [(c, 'construction in both splits') for c, s in sp.items() if len(s) > 1]
    tr_fronts = [(it['file'], frozenset(dec[it['file']]['front'])) for it in M['items'] if it['split'] == 'train' and not it['augmented']]
    leak = {}
    for it in M['items']:
        if it['split'] != 'holdout' or not it.get('family'): continue
        f = frozenset(dec[it['file']]['front']); fm = frozenset((FW - 1 - x, y) for x, y in f)
        best = max(((max(len(f & g) / len(f | g), len(fm & g) / len(fm | g)), n) for n, g in tr_fronts))
        leak[it['file']] = {'name': it['name'], 'family': it['family'], 'nearest_train': best[1], 'front_iou': round(best[0], 3)}
    cols = {p for V in dec.values() for d in V.values() for p in d.values()}       # 7: background
    near = sorted((round(math.dist(oklab(BG), oklab(p)), 3), p) for p in cols)[:5]
    who = {p: sorted({f for f, V in dec.items() if any(p in d.values() for d in V.values())})[:4] for _, p in near}
    report[ds] = {'images': len(M['items']), 'counts': M['counts'], 'family_counts': M['family_counts'], 'errors': E[:50], 'n_errors': len(E),
                  'witch_holdout_nearest_train': leak, 'background_nearest': [{'oklab_dist': d, 'rgb': p, 'in': who[p]} for d, p in near],
                  'pack_skipped': M['pack_skipped'], 'pack_dropped': M['pack_dropped']}
    bad += len(E)
    W = [it for it in M['items'] if it['subset'] == 'witch' or (it['split'] == 'holdout' and it.get('family'))]  # contact sheet
    S = 2; tw = (2 * FW if views != ['front'] else FW) * S
    th = (2 * FW if views != ['front'] else FW) * S
    cols_n = 6; cw, ch = max(tw, 150) + 10, th + 46
    sheet = Image.new('RGB', (cols_n * cw + 10, ((len(W) + cols_n - 1) // cols_n) * ch + 10), (30, 32, 40)); dr = ImageDraw.Draw(sheet)
    for k, it in enumerate(W):
        x0, y0 = 10 + (k % cols_n) * cw, 10 + (k // cols_n) * ch
        t = Image.new('RGB', (tw // S, th // S), BG); tp = t.load()
        for v in views:
            for (x, y), p in dec[it['file']][v].items(): tp[Q[v][0] + x, Q[v][1] + y] = p
        sheet.paste(t.resize((tw, th), Image.NEAREST), (x0, y0))
        words = it['caption'].split(', ')[1 + len(M['layout_caption'].split(', ')):-3]
        dr.text((x0, y0 + th + 2), (('HOLDOUT ' if it['split'] == 'holdout' else '') + it['file'][-24:])[:28], fill=(255, 220, 140) if it['split'] == 'holdout' else (230, 230, 230))
        dr.text((x0, y0 + th + 14), ', '.join(words)[:30], fill=(190, 200, 210)); dr.text((x0, y0 + th + 26), ', '.join(words)[30:60], fill=(190, 200, 210))
    sheet.save(os.path.join(D, 'contact_witch.png'))
    print(ds, len(M['items']), 'images |', len(E), 'errors |', 'bg nearest', near[0])
    for f, r in leak.items(): print('   holdout', r['name'], '->', r['nearest_train'], r['front_iou'])
json.dump(report, open(os.path.join(HERE, 'analysis', 'phase4_validation.json'), 'w'), indent=1)
sys.exit(1 if bad else 0)
