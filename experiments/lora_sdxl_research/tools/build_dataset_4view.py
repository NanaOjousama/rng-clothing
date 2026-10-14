"""Phase-2 dataset: one image = all four views of one hat, block-exact.  Pure Python.

Layout (logical pixels): 2x2 grid of the 20x20 views with a 2-cell background gutter between them
-> 42x42 cells, inside a 16-px margin:
    [front][gutter][right]
    [gutter row         ]
    [left ][gutter][back ]
cell = 16 px (2x2 latent cells), canvas 704 = 16 + 42*16 + 16, offset 16: on the 8-px latent grid.
Background = the phase-1 magenta (farthest from every corpus colour).  Translucent author shadows
dropped (as in phase 1).  Nearest-neighbour block fill only; the 20x20 pixels are copied exactly.

View-swap augmentation (`analysis/aug_check.json`, measured on 379 hats):
  * mirror = x -> 19 - x inside the 20-px frame (341/379 fronts are centred on x = 9.5, so the hat
    stays seated where its author put it)
  * mirrored right becomes the new LEFT and mirrored left the new RIGHT; front/back mirror in place
  * side lighting survives (sides are lit on the facing side: right 198 vs 69, left 180 vs 90);
    front/back are mostly flat-lit but 101 fronts lean to screen-right light, so ONLY hats whose
    front AND back are light-neutral (|L left - L right| <= 0.02) are augmented: 219/379.
Holdout = the phase-1 holdout constructions (same split, comparable), plus new ones by the same rule.
usage: python3 -I build_dataset_4view.py [512]  -> dataset/phase2_4view[_512]/{train/1_sdvhat,holdout}, manifest.json
  512 = the probed sheet512 layout (12-px cells, no gutter, 16 margin; front latents 2..32), chosen for method C"""
import collections, json, os, random, struct, sys, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dataset as B                               # phase-1 caption / colour / family helpers
HERE = B.HERE; ROOT = B.ROOT
VIEWS = ['front', 'right', 'left', 'back']
L512 = sys.argv[1:] == ['512']
CELL, GUT, MARGIN = (12, 0, 16) if L512 else (16, 2, 16)
GRID = 20 * 2 + GUT                                     # 42 logical cells (40 for 512)
CAN = MARGIN * 2 + GRID * CELL                          # 704 (512)
QUAD = {'front': (0, 0), 'right': (20 + GUT, 0), 'left': (0, 20 + GUT), 'back': (20 + GUT, 20 + GUT)}
LAYOUT = 'four views, front top-left, right top-right, left bottom-left, back bottom-right'
SIL_IOU = 0.90                                          # front-silhouette IoU (incl. mirror) that ties two shapes into one split group


def views_of(c, pal):
    out = {v: {} for v in VIEWS}
    for k, g in enumerate(c['grid']):
        if g < 0: continue
        y, x = divmod(k, 80); p = pal[g]
        if p[3] < 255: continue
        out[VIEWS[x // 20]][(x % 20, y)] = tuple(p[:3])
    return out


def mirror_swap(V):
    m = lambda d: {(19 - x, y): p for (x, y), p in d.items()}
    return {'front': m(V['front']), 'right': m(V['left']), 'left': m(V['right']), 'back': m(V['back'])}


def render(V, bg):
    cells = {}
    for v, (qx, qy) in QUAD.items():
        for (x, y), p in V[v].items(): cells[(qx + x, qy + y)] = p
    bgrow = bytes(bg) * CAN; rows = []
    for py in range(CAN):
        if not (MARGIN <= py < MARGIN + GRID * CELL): rows.append(bgrow); continue
        ly = (py - MARGIN) // CELL; r = bytearray(bgrow)
        for lx in range(GRID):
            p = cells.get((lx, ly))
            if p is None: continue
            x0 = (MARGIN + lx * CELL) * 3; r[x0:x0 + CELL * 3] = bytes(p) * CELL
        rows.append(bytes(r))
    return rows


def main():
    lib = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))
    labels = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_labels.json')))['labels']
    struct_ = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_structure.json')))['hosts']
    vanilla = {}
    for k, v in json.load(open(B.VANILLA, encoding='utf-8')).items():
        f = v.split('/'); vanilla[int(f[6]) if len(f) > 6 and f[6].strip() else int(k)] = f[0].lower()
    p1 = json.load(open(os.path.join(HERE, 'dataset', 'phase1_front', 'manifest.json')))
    bg = tuple(p1['background']); hold = set(p1['holdout_constructions'])
    aug = json.load(open(os.path.join(HERE, 'analysis', 'aug_check.json')))
    eligible = {r['id'] for r in aug if all(r['light'][v] is None or abs(r['light'][v]) <= 0.02 for v in ('front', 'back'))}
    cons = [c for c in lib['constructions'] if not c['missing'] and c['frame'] == [20, 20] and not c['colourable']]
    def fams_of(c): return SEMF(c) - {'brimmed', 'brim-narrow', 'unknown'}
    excluded = [c['id'] for c in cons if fams_of(c) and fams_of(c) <= B.ACCESSORY_ONLY]
    cons = [c for c in cons if c['id'] not in set(excluded)]
    out = os.path.join(HERE, 'dataset', 'phase2_4view_512' if L512 else 'phase2_4view'); tr = os.path.join(out, 'train', f'1_{B.TRIGGER}'); ho = os.path.join(out, 'holdout')
    for d in (tr, ho): os.makedirs(d, exist_ok=True)
    man = {'canvas': CAN, 'cell': CELL, 'margin': MARGIN, 'gutter': GUT, 'grid': GRID, 'quadrants': QUAD, 'background': list(bg),
           'trigger': B.TRIGGER, 'layout_caption': LAYOUT, 'mirror': 'x -> 19 - x in the 20-px frame; right<->left swapped',
           'aug_rule': 'only constructions whose front and back are light-neutral (|dL| <= 0.02)', 'excluded_accessory_only': excluded,
           'skipped_colourable': True, 'silhouette_group_iou': SIL_IOU, 'translucent_pixels': 'dropped', 'items': []}
    # silhouette groups: a shape (or its mirror) must not sit on both sides of the split (party-hat c345/c346 leak)
    def sil(c): return frozenset(V_ for V_ in views_of(c, c['colourways'][0]['palette'])['front'])
    def iou(a, b): return len(a & b) / max(1, len(a | b))
    S_ = {c['id']: sil(c) for c in cons}; S_mx = {i: frozenset((19 - x, y) for x, y in s) for i, s in S_.items()}
    ids = [c['id'] for c in cons]; parent = {i: i for i in ids}
    def find(i):
        while parent[i] != i: i = parent[i]
        return i
    for a_i, a in enumerate(ids):
        for b in ids[a_i + 1:]:
            if max(iou(S_[a], S_[b]), iou(S_mx[a], S_[b])) >= SIL_IOU: parent[find(a)] = find(b)
    groups = collections.defaultdict(set)
    for i in ids: groups[find(i)].add(i)
    moved, released = [], []                              # mixed group -> wholly to its majority side
    for g in groups.values():
        h = g & hold
        if not h or h == g: continue
        if 2 * len(h) >= len(g): moved += sorted(g - hold); hold |= g
        else: released += sorted(h); hold -= h
    for c in cons:
        dest = ho if c['id'] in hold else tr
        for k, w in enumerate(c['colourways'][:B.MAX_WAYS]):
            V = views_of(c, w['palette'])
            cap1 = B.caption(c, w['palette'], {}, vanilla, labels, struct_)        # colour words recomputed below
            cnt = collections.Counter(p for p in V['front'].values())
            names = []
            for p, _ in cnt.most_common():
                nm = B.colour_name(p)
                if nm not in names: names.append(nm)
                if len(names) == 3: break
            parts = cap1.split(', ')
            body = [t for t in parts[2:] if t and t != 'pixel art' and not t.startswith('20x20') and t != 'dark outline']
            body = [t for t in body if t]  # family / brim / name / note
            cap = ', '.join([B.TRIGGER, LAYOUT] + body + [', '.join(names), 'pixel art, 20x20 sprites, dark outline'])
            variants = [('', V)] + ([('__mx', mirror_swap(V))] if (c['id'] in eligible and dest == tr) else [])
            for suf, VV in variants:
                stem = f"{c['id']}__w{k}{suf}"
                B.write_png(os.path.join(dest, stem + '.png'), CAN, CAN, render(VV, bg))
                open(os.path.join(dest, stem + '.txt'), 'w', encoding='ascii').write(cap)
                man['items'].append({'file': stem, 'split': 'holdout' if dest == ho else 'train', 'construction': c['id'], 'author': c['author'],
                                     'source': w['source'], 'augmented': bool(suf), 'caption': cap})
    cc = collections.Counter((i['split'], i['augmented']) for i in man['items'])
    man['counts'] = {f"{s}{'_aug' if a else ''}": n for (s, a), n in cc.items()}
    man['moved_to_holdout_by_silhouette'] = moved; man['released_to_train_by_silhouette'] = released
    man['holdout_constructions'] = sorted({i['construction'] for i in man['items'] if i['split'] == 'holdout'})
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    print('canvas', CAN, 'cell', CELL, '| counts', man['counts'], '| holdout constructions', len(man['holdout_constructions']))


def SEMF(c):
    return B.SEM.host_families(c['names'], c['id'])


if __name__ == '__main__':
    main()
