"""Study Tea-Loving Lad's "Vanilla Hats Extended" (Nexus 26851) against real vanilla
hats and the pack_study corpus.  Analysis-only (PIL + numpy).

    python3 pack_study/tools/vhe_study.py <hat-version-dir> <accessory-version-dir>

<...-dir> are the unzipped "[FS] Vanilla Hats Extended (...)" folders.  Vanilla comes
from the game's unpacked Content (Characters/Farmer/hats.png + Data/hats.json).

Every VHE item is normalised to the corpus 80x20 strip (front, right, left, back) and
classified against its best vanilla match and every corpus hat:

  IDENTICAL   same mask, colours within +-3          -> duplicate, not new evidence
  RECOLOUR    same mask, one bijective colour map     -> palette evidence only
  PARTIAL     same mask, only some colours changed    -> the changed colours are a role
  RESHADE     same mask, not a remap                  -> pattern / shading change
  ADDON       base mask inside B, base kept >= 85%    -> added part (decoration)
  REMOVAL     B mask inside base, B kept >= 85%       -> removed part (decoration of base)
  STRUCTURAL  masks differ both ways, IoU >= 0.5      -> shape edit of the base
  NOVEL       no vanilla base with IoU >= 0.5

Accessory version: ColorMaskLayers (named, offset grey ramps) are mapped onto pixels
and back onto the hat-version colours -> author-named regions + palette roles.
Writes data/vhe/{items,pairs,mask_layers,summary}.json and out/vhe_*.png.
"""
import glob, json, os, re, sys
from collections import Counter
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vanilla import CONTENT, clean, strip_from_vertical, load_vanilla

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DATA = os.path.join(HERE, 'data', 'vhe')
OUT_IMG = os.path.join(HERE, 'out')
TOL = 3


def load_fs(root, kind):
    sub, js, key = (('Hats', 'hat.json', 'Hat') if kind == 'hat'
                    else ('Accessories', 'accessory.json', 'Accessory'))
    items = {}
    for d in sorted(glob.glob(os.path.join(glob.escape(root), sub, '*'))):
        png = glob.glob(os.path.join(glob.escape(d), '*.png'))
        if not png: continue
        text = open(os.path.join(d, js), encoding='utf-8-sig').read()
        text_nc = re.sub(r'^\s*//.*$', '', text, flags=re.M)
        meta = json.loads(text_nc)
        items[os.path.basename(d)] = {'arr': strip_from_vertical(Image.open(png[0])), 'json': meta,
                                      'name': meta.get('Name', os.path.basename(d)), 'key': key}
    return items


def mask(a): return a[..., 3] > 0


def iou(a, b):
    ma, mb = mask(a), mask(b)
    u = (ma | mb).sum()
    return float((ma & mb).sum() / u) if u else 0.0


def colours(a, m):
    return [tuple(p) for p in a[m]]


def is_remap(a, b, m):
    fa, fb = {}, {}
    for x, y in zip(colours(a, m), colours(b, m)):
        if fa.setdefault(x, y) != y or fb.setdefault(y, x) != x: return False
    return True


def near(a, b, m):
    return bool((np.abs(a[m] - b[m]).max(initial=0)) <= TOL)


def kept(a, b, region):
    """Fraction of region pixels identical (within TOL) between a and b."""
    if not region.any(): return 0.0
    return float((np.abs(a[region] - b[region]).max(axis=1) <= TOL).mean())


def shift_view(v, dx, dy):
    out = np.zeros_like(v)
    h, w = v.shape[:2]
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = v[ys, xs]
    return out


def align(base, b, r=8):
    """Per view, the (dx, dy) moving base onto b that maximises identical opaque pixels.
    Ties keep the smallest move.  Returns aligned base strip and the shifts."""
    out, shifts = np.zeros_like(base), []
    for k in range(4):
        vb, vt = base[:, k * 20:(k + 1) * 20], b[:, k * 20:(k + 1) * 20]
        best = (-1, 0, 0, 0)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                sv = shift_view(vb, dx, dy)
                if mask(sv).sum() < mask(vb).sum(): continue      # never crop the base
                m = mask(sv) & mask(vt)
                score = int((np.abs(sv[m] - vt[m]).max(axis=1, initial=0) <= TOL).sum()) if m.any() else 0
                cand = (score, -(abs(dx) + abs(dy)), dx, dy)
                if cand > best: best = cand
        _, _, dx, dy = best
        out[:, k * 20:(k + 1) * 20] = shift_view(vb, dx, dy)
        shifts.append([dx, dy])
    return out, shifts


def classify(base, b):
    """Relation of b to base, after per-view alignment (a moved part is not a new part)."""
    aligned, shifts = align(base, b)
    r = classify_aligned(aligned, b)
    changed = r.get('added', 0) + r.get('removed', 0) + r.get('changedPx', 0)
    if r['cls'] not in ('IDENTICAL', 'NOVEL') and changed <= 8:
        r['tweakOf'] = r['cls']; r['cls'] = 'TWEAK'          # touch-up, not new evidence
    if any(s != [0, 0] for s in shifts):
        r['moved'] = shifts
        r['unalignedIou'] = round(iou(base, b), 3)
    return r


def classify_aligned(base, b):
    ma, mb = mask(base), mask(b)
    r = {'iou': round(iou(base, b), 3), 'basePx': int(ma.sum()), 'px': int(mb.sum()),
         'added': int((mb & ~ma).sum()), 'removed': int((ma & ~mb).sum())}
    if (ma == mb).all():
        if near(base, b, ma): r['cls'] = 'IDENTICAL'
        elif is_remap(base, b, ma):
            same = np.abs(base[ma] - b[ma]).max(axis=1) <= TOL
            r['changedPx'] = int((~same).sum())
            src = Counter(colours(base, ma))
            chg = {tuple(c) for c, s in zip(base[ma], same) if not s}
            r['changedColours'] = len(chg)
            r['baseColours'] = len(src)
            r['cls'] = 'RECOLOUR' if len(chg) == len(src) else 'PARTIAL'
        else:
            r['cls'] = 'RESHADE'
            r['changedPx'] = int((np.abs(base[ma] - b[ma]).max(axis=1) > TOL).sum())
    elif not (ma & ~mb).any():
        r['cls'] = 'ADDON'; r['baseKept'] = round(kept(base, b, ma), 3)
    elif not (mb & ~ma).any():
        r['cls'] = 'REMOVAL'; r['baseKept'] = round(kept(base, b, mb), 3)
    else:
        r['cls'] = 'STRUCTURAL' if r['iou'] >= 0.5 else 'NOVEL'
        r['baseKept'] = round(kept(base, b, ma & mb), 3)
    return r


def best_match(arr, pool):
    best = max(pool.items(), key=lambda kv: (iou(arr, kv[1]['arr']),
                                             kept(arr, kv[1]['arr'], mask(arr) & mask(kv[1]['arr']))))
    return best[0], iou(arr, best[1]['arr'])


def norm(n):
    n = re.sub(r' (Alt(?: \d)?|\d)$', '', n)
    return re.sub(r'[^a-z0-9]', '', n.lower().replace('hat', ''))


def match_vanilla(folder, arr, van):
    """Name first (base name for Alt/numbered variants), else best shape whose shared
    pixels mostly survive.  Shape overlap alone is coincidence-prone (README finding 2)."""
    by_name = [i for i, v in van.items() if norm(v['name']) == norm(folder)]
    if by_name:
        return max(by_name, key=lambda i: iou(arr, van[i]['arr'])), 'name'
    vi, s = best_match(arr, van)
    k = kept(arr, van[vi]['arr'], mask(arr) & mask(van[vi]['arr']))
    return (vi, 'shape') if s >= 0.5 and k >= 0.5 else (None, None)


def internal_sets(pool):
    """Same-mask groups inside the mod; members that are pure recolours of the first."""
    groups = {}
    for f, it in pool.items():
        groups.setdefault(mask(it['arr']).tobytes(), []).append(f)
    out = []
    for fs in groups.values():
        if len(fs) < 2: continue
        b = fs[0]
        out.append({'base': b, 'members': fs,
                    'relations': {f: classify(pool[b]['arr'], pool[f]['arr'])['cls'] for f in fs[1:]}})
    return out


def new_evidence(hat_items, pool):
    """Items that differ from vanilla beyond a touch-up, are not in the corpus, and are not
    a recolour of another such item (one representative per same-mask recolour group)."""
    cand = [i['folder'] for i in hat_items
            if i['vsVanilla']['cls'] not in ('IDENTICAL', 'TWEAK') and not i['corpusDupeCount']]
    reps = []
    for f in cand:
        a = pool[f]['arr']
        if any((mask(a) == mask(pool[g]['arr'])).all() and is_remap(pool[g]['arr'], a, mask(a)) for g in reps):
            continue
        reps.append(f)
    return sorted(reps)


def load_corpus():
    recs = json.load(open(os.path.join(HERE, 'data', 'hats.json')))
    out = {}
    for r in recs:
        p = os.path.join(HERE, 'data', 'hats', r['id'] + '.png')
        if os.path.exists(p) and r['frame'] == [20, 20]:
            out[r['id']] = {'arr': clean(np.asarray(Image.open(p).convert('RGBA'), dtype=np.int16)),
                            'author': r['author'], 'name': r['name']}
    return out


def corpus_dupes(arr, corpus):
    """Corpus hats that are the same art (IDENTICAL) or a pure recolour of it."""
    m = mask(arr)
    hits = []
    for cid, c in corpus.items():
        if not (mask(c['arr']) == m).all(): continue
        if near(arr, c['arr'], m): hits.append((cid, c['author'], 'IDENTICAL'))
        elif is_remap(arr, c['arr'], m): hits.append((cid, c['author'], 'RECOLOUR'))
    return hits


def mask_layers(acc, hat_arr):
    """Map each named ColorMaskLayer onto pixels; read hat-version colours under it."""
    a = acc['arr']
    out = []
    for view, k in zip(range(4), ['Front', 'Right', 'Left', 'Back']):
        node = acc['json'].get(k + acc['key']) or {}
        for li, layer in enumerate(node.get('ColorMaskLayers') or []):
            vals = [tuple(v[:3]) for v in layer.get('Values', [])]
            sl = a[:, view * 20:(view + 1) * 20]
            hit = np.zeros(sl.shape[:2], bool)
            for v in vals:
                hit |= (sl[..., 3] > 0) & (np.abs(sl[..., :3] - v).max(axis=2) == 0)
            hc = Counter()
            if hat_arr is not None:
                hs = hat_arr[:, view * 20:(view + 1) * 20]
                hc = Counter('#%02X%02X%02X' % tuple(p[:3]) for p in hs[hit] if p[3] > 0)
            out.append({'view': ['front', 'right', 'left', 'back'][view], 'layer': li,
                        'name': layer.get('Name'), 'ramp': len(vals), 'px': int(hit.sum()),
                        'hatColours': dict(hc.most_common())})
    total = int(mask(a).sum())
    covered = sum(l['px'] for l in out)
    return out, total, covered


def sheet(rows, path, scale=4):
    """rows: list of (label, [arr, ...]).  Native pixels, nearest only."""
    if not rows: return
    n = max(len(r[1]) for r in rows)
    W, H = (80 * n + 8 * (n - 1)) * scale, len(rows) * 24 * scale
    im = Image.new('RGBA', (W, H), (60, 60, 70, 255))
    for i, (_, arrs) in enumerate(rows):
        for j, a in enumerate(arrs):
            t = Image.fromarray(a.astype(np.uint8), 'RGBA').resize((80 * scale, 20 * scale), Image.NEAREST)
            bg = Image.new('RGBA', t.size, (205, 200, 185, 255)); bg.alpha_composite(t)
            im.paste(bg, ((80 + 8) * j * scale, (i * 24 + 2) * scale))
    im.save(path)


def diff_arr(base, b):
    """Base greyed, B's added pixels in B colour, removed pixels magenta, recoloured pixels B colour."""
    out = np.zeros_like(base)
    ma, mb = mask(base), mask(b)
    g = base[..., :3].mean(axis=2, keepdims=True) * 0.35 + 120
    out[ma, :3] = g[ma].repeat(3, axis=1) if g[ma].ndim == 2 else g[ma]; out[ma, 3] = 255
    chg = mb & (~ma | (np.abs(base - b).max(axis=2) > TOL))
    out[chg] = b[chg]
    rem = ma & ~mb
    out[rem] = (255, 0, 255, 255)
    return out


def main():
    hat_root, acc_root = sys.argv[1], sys.argv[2]
    os.makedirs(OUT_DATA, exist_ok=True)
    van = load_vanilla()
    hats, accs = load_fs(hat_root, 'hat'), load_fs(acc_root, 'acc')
    corpus = load_corpus()
    print(f'vanilla {len(van)} | VHE hat {len(hats)} | VHE accessory {len(accs)} | corpus {len(corpus)}')

    items = []
    for version, pool in (('hat', hats), ('accessory', accs)):
        for folder, it in pool.items():
            vi, how = match_vanilla(folder, it['arr'], van)
            sib = re.sub(r' (Alt(?: \d)?|\d)$', '', folder)
            if vi is None and sib != folder and sib in pool:
                vi, how = match_vanilla(sib, pool[sib]['arr'], van)
                how = how and 'sibling:' + how
            rel = classify(van[vi]['arr'], it['arr']) if vi is not None else {'cls': 'NOVEL', 'iou': 0.0}
            dup = corpus_dupes(it['arr'], corpus)
            items.append({'version': version, 'folder': folder, 'name': it['name'],
                          'vanilla': ({'index': vi, 'id': van[vi]['id'], 'name': van[vi]['name'], 'matchedBy': how}
                                      if vi is not None else None),
                          'vsVanilla': rel, 'corpusDupes': dup[:5], 'corpusDupeCount': len(dup),
                          'prismatic': '"IsPrismatic": true' in json.dumps(it['json'])})

    # Alt / numbered siblings inside each version
    pairs = []
    for version, pool in (('hat', hats), ('accessory', accs)):
        for folder, it in pool.items():
            m = re.match(r'^(.*?) (Alt(?: \d)?|\d)$', folder)
            if not m: continue
            base = m.group(1) if m.group(1) in pool else (m.group(1) + ' 1' if m.group(1) + ' 1' in pool else None)
            if base is None or base == folder: continue
            pairs.append({'version': version, 'base': base, 'variant': folder,
                          **classify(pool[base]['arr'], it['arr'])})

    internal = {'hat': internal_sets(hats), 'accessory': internal_sets(accs)}
    json.dump(internal, open(os.path.join(OUT_DATA, 'internal_sets.json'), 'w'), indent=1)

    # Accessory vs hat version, same name: is the accessory a greyscale mask of the same art?
    layers = {}
    for folder, a in accs.items():
        h = hats.get(folder)
        rel = classify(h['arr'], a['arr']) if h else None
        ls, tot, cov = mask_layers(a, h['arr'] if h else None)
        if ls or rel:
            layers[folder] = {'hatVersionRelation': rel, 'layers': ls,
                              'opaquePx': tot, 'maskedPx': cov,
                              'layerNames': sorted({l['name'] for l in ls if l['name']})}

    # Author-split parts: what a REMOVAL takes off the base (base author's pixels) and
    # what an ADDON puts on (VHE pixels).  Candidates only -- approval is by eye, like
    # data/decorations_approved.json.
    parts, part_rows = [], []
    rels = [(i['folder'], 'vanilla', van[i['vanilla']['index']]['arr'], hats[i['folder']]['arr'], i['vsVanilla'])
            for i in items if i['version'] == 'hat' and i['vanilla']]
    rels += [(p['variant'], p['base'], hats[p['base']]['arr'], hats[p['variant']]['arr'], p)
             for p in pairs if p['version'] == 'hat']
    seen = set()
    for folder, base_name, base, b, r in rels:
        if r['cls'] not in ('REMOVAL', 'ADDON') or r.get('added', 0) + r.get('removed', 0) < 6: continue
        aligned, _ = align(base, b)
        src, part_m = (aligned, mask(aligned) & ~mask(b)) if r['cls'] == 'REMOVAL' else (b, mask(b) & ~mask(aligned))
        key = part_m.tobytes()                  # recoloured copies of one split count once
        if key in seen: continue
        seen.add(key)
        part = np.zeros_like(src); part[part_m] = src[part_m]
        views = {}
        for k, v in enumerate(['front', 'right', 'left', 'back']):
            ys, xs = np.nonzero(part_m[:, k * 20:(k + 1) * 20])
            views[v] = [[int(x), int(y), *map(int, src[y, k * 20 + x])] for y, x in zip(ys, xs)]
        parts.append({'from': folder, 'base': base_name, 'kind': r['cls'],
                      'author': 'ConcernedApe' if r['cls'] == 'REMOVAL' and base_name == 'vanilla' else 'Tea-Loving Lad',
                      'px': int(part_m.sum()), 'viewsPresent': sum(bool(x) for x in views.values()),
                      'remainderKept': r.get('baseKept'), 'pixels': views})
        part_rows.append((folder, [base, b, part]))
    json.dump(parts, open(os.path.join(OUT_DATA, 'parts.json'), 'w'), indent=1)
    sheet(part_rows, os.path.join(OUT_IMG, 'vhe_parts.png'))

    # Placement evidence: consistent per-view moves of the same art
    moves = [{'item': i['folder'], 'cls': i['vsVanilla']['cls'], 'moved': i['vsVanilla']['moved']}
             for i in items if i['version'] == 'hat' and 'moved' in i['vsVanilla']]
    json.dump(moves, open(os.path.join(OUT_DATA, 'moves.json'), 'w'), indent=1)

    hat_items = [i for i in items if i['version'] == 'hat']
    acc_items = [i for i in items if i['version'] == 'accessory']
    summ = {
        'counts': {'vanilla': len(van), 'vheHat': len(hats), 'vheAccessory': len(accs), 'corpus': len(corpus)},
        'hatVsVanilla': Counter(i['vsVanilla']['cls'] for i in hat_items),
        'accessoryVsVanilla': Counter(i['vsVanilla']['cls'] for i in acc_items),
        'hatAlreadyInCorpus': sum(i['corpusDupeCount'] > 0 for i in hat_items),
        'vanillaCoveredByVHEHat': len({i['vanilla']['index'] for i in hat_items if i['vsVanilla']['cls'] == 'IDENTICAL'}),
        'internalSameMaskSets': {k: len(v) for k, v in internal.items()},
        'internalDuplicates': {k: sum(r in ('IDENTICAL', 'RECOLOUR') for g in v for r in g['relations'].values())
                               for k, v in internal.items()},
        'pairs': Counter(p['version'] + ':' + p['cls'] for p in pairs),
        'accessoryHatRelation': Counter(v['hatVersionRelation']['cls'] if v['hatVersionRelation'] else 'NO_HAT_TWIN'
                                        for v in layers.values()),
        'withMaskLayers': sum(bool(v['layers']) for v in layers.values()),
        'maskCoverage': round(sum(v['maskedPx'] for v in layers.values() if v['layers']) /
                              max(1, sum(v['opaquePx'] for v in layers.values() if v['layers'])), 3),
        'parts': Counter(p['kind'] + ':' + p['author'] for p in parts),
        'moved': len(moves),
        'newVsVanillaAndCorpus': new_evidence(hat_items, hats),
        'corpusDupeAuthors': Counter(d[1] for i in hat_items for d in i['corpusDupes'][:1]),
        'layerNames': Counter(n for v in layers.values() for n in v['layerNames']),
    }
    for name, obj in (('items', items), ('pairs', pairs), ('mask_layers', layers), ('summary', summ)):
        json.dump(obj, open(os.path.join(OUT_DATA, name + '.json'), 'w'), indent=1, default=str)
    print(json.dumps(summ, indent=1))

    # Sheets: every hat-version item that is not a plain duplicate of vanilla
    rows = []
    for i in hat_items:
        if i['vsVanilla']['cls'] == 'IDENTICAL': continue
        if not i['vanilla']: continue
        b = hats[i['folder']]['arr']; v = van[i['vanilla']['index']]['arr']
        rows.append((i['folder'], [v, b, diff_arr(v, b)]))
    sheet(rows, os.path.join(OUT_IMG, 'vhe_vs_vanilla.png'))
    rows = []
    for p in pairs:
        if p['version'] != 'hat': continue
        a, b = hats[p['base']]['arr'], hats[p['variant']]['arr']
        rows.append((p['variant'], [a, b, diff_arr(a, b)]))
    sheet(rows, os.path.join(OUT_IMG, 'vhe_alt_pairs.png'))
    print('rows vs vanilla', len([1 for i in hat_items if i['vsVanilla']['cls'] != 'IDENTICAL']), '| alt pairs', len(rows))


if __name__ == '__main__':
    main()
