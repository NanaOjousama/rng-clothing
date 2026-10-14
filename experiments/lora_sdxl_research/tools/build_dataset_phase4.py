"""Phase-4 datasets (user, 2026-10-14) -- PREPARED, NOT TRAINED.  Pure Python (zlib/struct), Deck.

Two datasets from the SAME selection of source hats:
  phase4_front_512  front view only          24x24 frame, 20-px cells, 16 margin  (front-generation LoRA)
  phase4_4view_512  2x2 sheet F|R / L|B       2 x 24x24 frames, 10-px cells, 16 margin (four-view LoRA, method C;
                                              front quadrant = pixels 16..256 = latent cells 2..32, as phase 3)

Frame: 24x24 window = vanilla hat cell x -2..21, y -4..19 (Fashion Sense draws a hat at its top-left + HeadPosition,
DrawManager.GetPositionOffset; frame pixel (x, y) lands at vanilla (x - HX, y - HY)).  Native proportions kept:
no scaling, no shifting; a hat that does not fit the window is left out (listed).  20x20 hats sit at (+2, +4).

Sources (read-only, never written):
  library      pack_study/data/library.json -- the phase-1 (front) / phase-3 (4-view) selections, captions with the
               phase-3 fix (hats_N -> vanilla name only for ConcernedApe)
  six packs    PlatinumCats 'Hats and Horns', Luny, Kailey  (experiments/witch_reference_packs_01/raw)
               Naver 'Witch Hat 492815'                     (experiments/witch_reference_packs_02/raw)
               mushlune Wildwood                            (experiments/wildwood_reference_01/raw)
               mushlune Bloom (hats only, crowns included as general hats) (experiments/bloom_reference_01/raw)
NEVER used: any generated experiment (witch_front_*, witch_cleanup_*, lora_worn_*, ...).  The validator checks.

Recolours: hats with an identical FRONT alpha mask and side/back masks >= SIDE_IOU alike are ONE structure; at most MAX_PER_STRUCT of them train
(authored colours preferred over FS-colourable grey, then the most different colours).  Then hats whose fronts are
>= BODY_IOU alike (one silhouette body, e.g. the 14 mushlune Wildwood/Bloom hats) keep at most MAX_PER_BODY, chosen for
different decoration words and colours.  Exact pixel duplicates dropped.  Mirror (view-swap) augmentation only for light-neutral hats (phase-2 rule).
Captions: witch hats get a family phrase + decoration words from hand tables (WITCH_FAMILY / WITCH_DECOR, by eye on
witch_silhouette_matrix_01 sheets) + 3 front colours.
usage: python3 -I build_dataset_phase4.py [--stats]"""
import collections, json, os, re, sys
sys.argv, _ARGS = [sys.argv[0], '512'], sys.argv[1:]     # build_dataset_4view reads its layout from argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dataset as B
import build_dataset_4view as F
import build_dataset_phase3 as P3
HERE, ROOT = B.HERE, B.ROOT
EXP = os.path.join(ROOT, 'experiments')
FW = 24; OX, OY = 2, 4                                     # window = vanilla x -2..21, y -4..19
MAX_PER_STRUCT = 2
SIDE_IOU = 0.90
BODY_IOU, MAX_PER_BODY = 0.95, 6        # one silhouette body (front IoU incl. mirror) -> at most 6 hats (decoration/colour variety)
PACKS = [  # (tag, author, author id, raw dir)
    ('Hats and Horns', 'PlatinumCats', 'platinumcats', 'witch_reference_packs_01/raw/Hats and Horns'),
    ("Luny's Witch Hats for FS", 'Luny', 'luny', "witch_reference_packs_01/raw/Luny's Witch Hats for FS"),
    ('Witch Hats', 'Kailey', 'kaileyw', 'witch_reference_packs_01/raw/Witch Hats'),
    ('Witch Hat 492815', 'Naver 492815', 'naver492815', 'witch_reference_packs_02/raw'),
    ('Wildwood Collection', 'mushlune', 'mushlune_wildwood', 'wildwood_reference_01/raw'),
    ('Bloom Collection', 'mushlune', 'mushlune_bloom', 'bloom_reference_01/raw'),
]
# family by eye (witch_silhouette_matrix_01/README.md + Bloom sheet 2026-10-14).  First match wins.
WITCH_FAMILY = [
    (r'^Witch Hat - Long$', 'short witch hat'), (r'^Witchy Hat - Horn$', 'short witch hat'),
    (r'^Witchy Hat - Vines$', 'short witch hat'), (r'^Witch Hat - Veiled', 'classic pointed witch hat'),
    (r'^Witchy Hat - Mossy$', 'classic pointed witch hat'), (r"^Luny's", 'low sweeping witch hat'),
    (r'^Witch Hat \(', 'tall floppy witch hat'), (r'^Witch Hat$', 'tall floppy witch hat'),
    (r'^Witch Hat_(1|3|5|7|9)$', 'short witch hat'), (r'^Witch Hat_(2|4|6|8|10)$', 'tall floppy witch hat'),
    (r"(Bow Witch|Celestial|Elegant Witch|Forager's Witch|Herbalist's Witch|Straw Witch) Hat$", 'low sweeping witch hat'),
    (r"^(Baby's-breath|Cornflower|Fiddle-leaf|Hyacinth|Hydrangias|Iris|Pumpkin|Sage) Hat$", 'low sweeping witch hat'),
]
WITCH_DECOR = [
    (r'Veiled', 'veil'), (r'Mossy', 'moss'), (r'Vines', 'vines and flowers'), (r'Horn', 'horns'),
    (r'Floral Witch Hat With Trim', 'flowers, trim'), (r'Floral', 'flowers'), (r'Flower Crown', 'flower crown'),
    (r'\(.*Flower\)', 'single flower'), (r'Ribbon', 'ribbon band'), (r'Kailey-Straw|\(Straw\)', 'straw, ragged brim'),
    (r'Bow Witch', 'bow'), (r'Celestial', 'moon and stars'), (r'Elegant', 'curled brim'), (r'Forager', 'mushrooms'),
    (r'Herbalist', 'herb sprigs'), (r'Straw Witch', 'straw'), (r"Baby's-breath", 'small white flowers'),
    (r'Cornflower|Hydrangias|Hyacinth|Iris|Sage', 'flowers'), (r'Fiddle-leaf', 'leaves'), (r'Pumpkin', 'pumpkin'),
    (r'Witch Hat_\d+$', 'band'),
]
# witch holdout: whole structures with ground truth, one per family (chosen from --stats; see PLAN_phase4.md)
WITCH_HOLDOUT = {'Witch Hat - Long', 'Witch Hat (Straw)', 'Elegant Witch Hat'}   # + vanilla Witch Hat c357 (library holdout)
FORBIDDEN_SOURCES = ('witch_front_', 'witch_cleanup', 'witch_side_repair', 'lora_worn', 'witch_hat_quality',
                     'esm_hairmode', 'ai_original', 'bucket_', 'beret_')


def place20(V):
    return {v: {(x + OX, y + OY): p for (x, y), p in d.items()} for v, d in V.items()}


def mirror24(V):
    m = lambda d: {(FW - 1 - x, y): p for (x, y), p in d.items()}
    return {'front': m(V['front']), 'right': m(V['left']), 'left': m(V['right']), 'back': m(V['back'])}


def render(cells, grid, cell, margin, bg):
    can = 2 * margin + grid * cell; bgrow = bytes(bg) * can; rows = []
    for py in range(can):
        if not (margin <= py < margin + grid * cell): rows.append(bgrow); continue
        ly = (py - margin) // cell; r = bytearray(bgrow)
        for lx in range(grid):
            p = cells.get((lx, ly))
            if p is None: continue
            x0 = (margin + lx * cell) * 3; r[x0:x0 + cell * 3] = bytes(p) * cell
        rows.append(bytes(r))
    return can, rows


QUAD = {'front': (0, 0), 'right': (FW, 0), 'left': (0, FW), 'back': (FW, FW)}
def sheet_cells(V): return {(QUAD[v][0] + x, QUAD[v][1] + y): p for v, d in V.items() for (x, y), p in d.items()}
def front_cells(V): return dict(V['front'])


def pack_hats():
    hats, skipped = [], []
    for tag, author, aid, rel in PACKS:
        base = os.path.join(EXP, rel)
        for root, _, files in sorted(os.walk(base)):
            if 'hat.json' not in files: continue
            d = P3.loose_json(os.path.join(root, 'hat.json')); name = d.get('Name') or os.path.basename(root)
            w, h, px = P3.read_png_rgba(os.path.join(root, 'hat.png'))
            V, bad = {}, []
            for v, k in P3.KEYS.items():
                m = d.get(k)
                if not m: bad.append(f'{v}: missing'); continue
                sx, sy = m['StartingPosition']['X'], m['StartingPosition']['Y']
                fw, fh = m['HatSize']['Width'], m['HatSize']['Length']
                hp = m.get('HeadPosition') or {}; hx, hy = hp.get('X', 0), hp.get('Y', 0)
                if m.get('Scale', 4) != 4: bad.append(f'{v}: scale'); continue
                flip = bool(m.get('Flipped')); cells = {}
                for y in range(fh):
                    for x in range(fw):
                        if not (0 <= sx + x < w and 0 <= sy + y < h): continue
                        p = px(sx + x, sy + y)
                        if p[3] < 255: continue                       # translucent author shadows dropped (phases 1-3)
                        cells[((fw - 1 - x if flip else x) - hx + OX, y - hy + OY)] = p[:3]
                V[v] = cells
            r = os.path.relpath(root, EXP)
            if bad or not all(V.get(v) for v in P3.KEYS):
                skipped.append({'hat': r, 'why': bad[:2] or ['empty view']}); continue
            xs = [x for c in V.values() for x, _ in c]; ys = [y for c in V.values() for _, y in c]
            if min(xs) < 0 or max(xs) >= FW or min(ys) < 0 or max(ys) >= FW:
                skipped.append({'hat': r, 'why': [f'outside 24x24 window (vanilla x {min(xs) - OX}..{max(xs) - OX}, '
                                                  f'y {min(ys) - OY}..{max(ys) - OY})']}); continue
            colourable = bool(re.search(r'colou?rable|prismatic', name, re.I)) or \
                all(max(p) - min(p) <= 12 for c in V.values() for p in c.values())
            hats.append({'pack': tag, 'author': author, 'aid': aid, 'name': name, 'rel': r, 'V': V, 'colourable': colourable})
    return hats, skipped


def family_of(name):
    return next((f for rx, f in WITCH_FAMILY if re.search(rx, name)), None)


def decor_of(name, pack):
    key = f"{'Kailey-' if pack == 'Witch Hats' else ''}{name}"
    return next((d for rx, d in WITCH_DECOR if re.search(rx, key)), None)


def caption(layout, words, V, frame_word):
    cnt = collections.Counter(V['front'].values()); names = []
    for p, _ in cnt.most_common():
        nm = B.colour_name(p)
        if nm not in names: names.append(nm)
        if len(names) == 3: break
    return ', '.join([B.TRIGGER, layout] + [w for w in words if w] + [', '.join(names), f'pixel art, {frame_word}, dark outline'])


def pack_words(hh):
    fam = family_of(hh['name']) if hh['pack'] != 'Hats and Horns' or 'witch' in hh['name'].lower() else None
    if fam:
        return [fam, decor_of(hh['name'], hh['pack'])], fam
    nm = re.sub(r'[^\x00-\x7f]', '', hh['name']).lower()                       # non-witch HnH / Bloom crowns
    nm = re.sub(r'\b(colou?rable|prismatic)\b', ' ', nm); nm = ' '.join(re.sub(r'[()\-_,]+', ' ', nm).split())
    return [nm], None


def struct_key(V): return tuple(tuple(sorted(V[v])) for v in F.VIEWS)


def colour_dist(a, b):
    ma = [sum(c) / len(c) for c in zip(*a['V']['front'].values())]; mb = [sum(c) / len(c) for c in zip(*b['V']['front'].values())]
    return sum((x - y) ** 2 for x, y in zip(ma, mb)) ** 0.5


def select(hats):
    """dedupe exact pixels, then cap each identical-structure group at MAX_PER_STRUCT."""
    seen, uniq, dropped = {}, [], []
    for hh in hats:
        k = json.dumps({v: sorted((list(a), list(p)) for a, p in hh['V'][v].items()) for v in F.VIEWS})
        if k in seen: dropped.append({'hat': hh['rel'], 'why': f'exact duplicate of {seen[k]}'}); continue
        seen[k] = hh['rel']; uniq.append(hh)
    def same(a, b):
        if set(a['V']['front']) != set(b['V']['front']): return False
        return all(len(set(a['V'][v]) & set(b['V'][v])) / max(1, len(set(a['V'][v]) | set(b['V'][v]))) >= SIDE_IOU for v in ('right', 'left', 'back'))
    groups = []
    for hh in uniq:
        g = next((g for g in groups if same(g[0], hh)), None)
        (g.append(hh) if g else groups.append([hh]))
    keep = []
    for g in groups:
        g = sorted(g, key=lambda h: (h['colourable'], h['name']))
        chosen = [g[0]]
        while len(chosen) < MAX_PER_STRUCT and len(chosen) < len(g):
            rest = [h for h in g if h not in chosen and not h['colourable']] or [h for h in g if h not in chosen]
            chosen.append(max(rest, key=lambda h: min(colour_dist(h, c) for c in chosen)))
        for h in g:
            if h in chosen: h['struct_group'] = [x['name'] for x in g]; keep.append(h)
            else: dropped.append({'hat': h['rel'], 'why': f'recolour cap ({len(g)} recolours of one structure; kept '
                                                         f'{", ".join(c["name"] for c in chosen)})'})
    # body cap: one silhouette body = front IoU >= BODY_IOU (mirror included), single-link
    W = FW
    def fr(h): return frozenset(h['V']['front'])
    def iou(a, b):
        am = frozenset((W - 1 - x, y) for x, y in a)
        return max(len(a & b) / len(a | b), len(am & b) / len(am | b))
    bodies = []
    for h in keep:
        hit = [b for b in bodies if any(iou(fr(h), fr(o)) >= BODY_IOU for o in b)]
        nb = [h] + [o for b in hit for o in b]; bodies = [b for b in bodies if b not in hit] + [nb]
    keep2 = []
    for b in bodies:
        b = sorted(b, key=lambda h: (h['colourable'], h['name'])); chosen = []
        while len(chosen) < min(MAX_PER_BODY, len(b)):
            rest = [h for h in b if h not in chosen]
            def score(h):
                d = decor_of(h['name'], h['pack']); newdec = d not in {decor_of(c['name'], c['pack']) for c in chosen}
                return (not h['colourable'], newdec, min([colour_dist(h, c) for c in chosen] or [0]))
            chosen.append(max(rest, key=score))
        for h in b:
            h['body_group'] = sorted(x['name'] for x in b)
            if h in chosen: keep2.append(h)
            else: dropped.append({'hat': h['rel'], 'why': f'body cap ({len(b)} hats share one silhouette body; kept '
                                                        f'{", ".join(c["name"] for c in chosen)})'})
    return keep2, dropped


def library_items():
    """phase-3 4-view library items and phase-1 front items, with the phase-3 caption fix."""
    p3 = json.load(open(os.path.join(HERE, 'dataset', 'phase3_4view_512', 'manifest.json')))
    p1 = json.load(open(os.path.join(HERE, 'dataset', 'phase1_front', 'manifest.json')))
    lib = {c['id']: c for c in json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))['constructions']}
    labels = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_labels.json')))['labels']
    struct_ = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_structure.json')))['hosts']
    vanilla = {}
    for k, v in json.load(open(B.VANILLA, encoding='utf-8')).items():
        f = v.split('/'); vanilla[int(f[6]) if len(f) > 6 and f[6].strip() else int(k)] = f[0].lower()
    def one(it):
        c = lib[it['construction']]; k = int(re.search(r'__w(\d+)', it['file']).group(1)); w = c['colourways'][k]
        V = place20(F.views_of(c, w['palette']))
        cap1 = B.caption(c, w['palette'], {}, vanilla if c['author'] == 'ConcernedApe' else {}, labels, struct_)
        body = [t for t in cap1.split(', ')[2:] if t and t != 'pixel art' and not t.startswith('20x20') and t != 'dark outline']
        # cap1 ends with the (empty-cells) colour slot; colour words are recomputed by caption()
        return V, body, c, w
    out4, out1 = [], []
    for it in p3['items']:
        if it.get('source_kind') != 'library' or it['augmented']: continue
        V, body, c, w = one(it)
        out4.append({'id': it['construction'], 'file': it['file'], 'split': it['split'], 'author': c['author'], 'source': w['source'],
                     'V': V, 'words': body, 'aug_ok': any(j['file'] == it['file'] + '__mx' for j in p3['items'])})
    for it in p1['items']:
        V, body, c, w = one(it)
        out1.append({'id': it['construction'], 'file': it['file'], 'split': it['split'], 'author': c['author'], 'source': w['source'],
                     'V': V, 'words': body})
    return out4, out1, p3, p1


def light_neutral(V):
    for v in ('front', 'back'):
        L = [B.to_lch(p)[0] for (x, y), p in V[v].items() if x < FW // 2]; R = [B.to_lch(p)[0] for (x, y), p in V[v].items() if x >= FW // 2]
        if L and R and abs(sum(L) / len(L) - sum(R) / len(R)) > 0.02: return False
    return True


def main():
    hats, skipped = pack_hats(); keep, dropped = select(hats)
    if '--stats' in _ARGS:
        fam = collections.Counter((family_of(h['name']) if 'witch' in h['name'].lower() or h['pack'] != 'Hats and Horns' else None) for h in keep)
        print('pack hats read', len(hats), '| kept', len(keep), '| dropped', len(dropped), '| skipped', len(skipped))
        print('by pack kept', collections.Counter(h['pack'] for h in keep)); print('by family kept', fam)
        for s in skipped: print('  SKIP', s['hat'].split('/')[-1], s['why'])
        for d in dropped: print('  DROP', d['hat'].split('/')[-1], '|', d['why'][:110])
        for h in keep: print('  KEEP', h['pack'][:12], '|', h['name'], '|', pack_words(h)[0], '| colourable' if h['colourable'] else '')
        return
    lib4, lib1, p3, p1 = library_items(); bg = tuple(p3['background'])
    L4 = 'four views, front top-left, right top-right, left bottom-left, back bottom-right'; FWORD = '24x24 sprites'
    allcol = {p for hh in keep for c in hh['V'].values() for p in c.values()} | {p for it in lib4 + lib1 for c in it['V'].values() for p in c.values()}
    bgmin = min(sum((a - b) ** 2 for a, b in zip(B.oklab(bg), B.oklab(p))) ** 0.5 for p in allcol)
    for ds, grid, cell, layout, cells_of in (('phase4_4view_512', 2 * FW, 10, L4, sheet_cells), ('phase4_front_512', FW, 20, 'front view', front_cells)):
        out = os.path.join(HERE, 'dataset', ds); tr = os.path.join(out, 'train', f'1_{B.TRIGGER}'); ho = os.path.join(out, 'holdout')
        tw = os.path.join(out, 'train', f'2_{B.TRIGGER}')       # witch-pack subset (num_repeats from the dataset toml)
        for d in (tr, ho, tw): os.makedirs(d, exist_ok=True)
        man = {'phase': 4, 'dataset': ds, 'canvas': 2 * 16 + grid * cell, 'cell': cell, 'margin': 16, 'grid': grid, 'frame': FW,
               'window_vanilla': {'x': [-OX, FW - 1 - OX], 'y': [-OY, FW - 1 - OY]}, 'background': list(bg),
               'background_min_oklab_distance': round(bgmin, 3), 'trigger': B.TRIGGER, 'layout_caption': layout,
               'quadrants': QUAD if 'sheet' in cells_of.__name__ else {'front': (0, 0)},
               'mirror': f'x -> {FW - 1} - x in the 24-px frame; right<->left swapped', 'max_per_structure': MAX_PER_STRUCT,
               'pack_skipped': skipped, 'pack_dropped': dropped, 'items': []}
        def emit(stem, split, V, cap, meta, sub):
            dest = ho if split == 'holdout' else (tw if sub == 'witch' else tr)
            can, rows = render(cells_of(V), grid, cell, 16, bg); B.write_png(os.path.join(dest, stem + '.png'), can, can, rows)
            open(os.path.join(dest, stem + '.txt'), 'w', encoding='ascii').write(cap)
            man['items'].append({'file': stem, 'split': split, 'subset': sub, 'caption': cap, **meta})
        lib = lib4 if ds.startswith('phase4_4view') else lib1
        for it in lib:
            cap = caption(layout, it['words'], it['V'], FWORD); meta = {'construction': it['id'], 'author': it['author'], 'source': it['source'], 'source_kind': 'library'}
            emit(it['file'], it['split'], it['V'], cap, {**meta, 'augmented': False}, 'general')
            ok = it.get('aug_ok') if ds.startswith('phase4_4view') else (it['split'] == 'train' and light_neutral({'front': it['V']['front'], 'back': {}}))
            if it['split'] == 'train' and ok:
                emit(it['file'] + '__mx', 'train', mirror24(it['V']), cap, {**meta, 'augmented': True}, 'general')
        for n, hh in enumerate(keep):
            words, fam = pack_words(hh); split = 'holdout' if hh['name'] in WITCH_HOLDOUT else 'train'
            cid = f"{hh['aid']}__p{n:02d}"; cap = caption(layout, words, hh['V'], FWORD); sub = 'witch' if fam else 'general'
            meta = {'construction': cid, 'author': hh['author'], 'pack': hh['pack'], 'name': hh['name'], 'family': fam,
                    'source': hh['rel'], 'source_kind': 'reference_pack', 'colourable': hh['colourable'], 'structure_group': hh['struct_group'], 'body_group': hh['body_group']}
            emit(cid + '__w0', split, hh['V'], cap, {**meta, 'augmented': False}, sub)
            if split == 'train' and light_neutral(hh['V']):
                emit(cid + '__w0__mx', 'train', mirror24(hh['V']), cap, {**meta, 'augmented': True}, sub)
        cc = collections.Counter((i['split'], i['subset'], i['augmented']) for i in man['items'])
        man['counts'] = {f"{s}|{sub}|{'aug' if a else 'orig'}": n for (s, sub, a), n in sorted(cc.items())}
        man['family_counts'] = dict(collections.Counter(f"{i['split']}|{i.get('family')}" for i in man['items'] if i.get('family')))
        man['holdout_constructions'] = sorted({i['construction'] for i in man['items'] if i['split'] == 'holdout'})
        json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
        print(ds, 'canvas', man['canvas'], 'cell', cell, '| bg min OKLab', man['background_min_oklab_distance'])
        for k, v in man['counts'].items(): print('   ', k, v)
        print('    families', man['family_counts'])
    export(keep, lib4, lib1, bg)


def export(keep, lib4, lib1, bg):
    """compact text export for the laptop (rebuilt there pixel-identical by tools/build_phase4_laptop.py)"""
    A = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+-:;<=>?@^_~' + ''.join(map(chr, range(0xC0, 0x250)))
    for ds in ('phase4_4view_512', 'phase4_front_512'):
        man = json.load(open(os.path.join(HERE, 'dataset', ds, 'manifest.json'))); src = {}
        for it in (lib4 if '4view' in ds else lib1): src[it['file']] = it['V']
        for n, hh in enumerate(keep): src[f"{hh['aid']}__p{n:02d}__w0"] = hh['V']
        items = []
        for it in man['items']:
            V = src[it['file'][:-4] if it['augmented'] else it['file']]
            if it['augmented']: V = mirror24(V)
            views = F.VIEWS if '4view' in ds else ['front']
            pal = sorted({p for v in views for p in V[v].values()}); enc = []
            for v in views:
                s = ''.join(A[pal.index(V[v][(i % FW, i // FW)])] if (i % FW, i // FW) in V[v] else '.' for i in range(FW * FW))
                enc.append(re.sub(r'\.{2,}', lambda m: f'({len(m.group(0))})', s))
            items.append({'file': it['file'], 'split': it['split'], 'subset': it['subset'], 'caption': it['caption'], 'pal': [list(p) for p in pal], 'views': enc})
        meta = {k: man[k] for k in ('canvas', 'cell', 'margin', 'grid', 'frame', 'background', 'trigger', 'quadrants')}
        json.dump({'meta': meta, 'alphabet': A, 'items': items}, open(os.path.join(HERE, 'dataset', f'{ds}_compact.json'), 'w', encoding='utf-8'),
                  separators=(',', ':'), ensure_ascii=False)


if __name__ == '__main__':
    main()
