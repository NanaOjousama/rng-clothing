"""Phase-3 dataset (user, 2026-10-13): phase-2 recipe (sheet512, 2x2 views, 12-px cells, magenta background,
light-neutral mirror augmentation) + two changes:

1. CAPTION FIX (analysis/caption_audit.md root cause): a 'hats_N' slot name is translated to vanilla hat N's
   name ONLY for ConcernedApe constructions.  Packs that replace vanilla art (Seyph, Kailey, ...) keep no slot name
   (seyph c287 bear was 'cowboy hat', c288 cat 'bowler hat', ...).
2. NEW SOURCE PACKS the user downloaded (experiments/witch_reference_packs_01/raw, personal use, author recorded):
   PlatinumCats 'Hats and Horns', Luny 'Luny's Witch Hats', Kailey '[FS] Witch Hats'.  Read straight from their FS
   hat.json; nothing is written into pack_study/data.  Placement follows Fashion Sense (DrawManager line 623:
   origin += HeadPosition), so frame pixel (x, y) lands at vanilla 20x20 cell (x - HeadPosition.X, y - HeadPosition.Y).
   A hat with any opaque pixel outside the 20x20 frame in any view is left out (listed in the manifest).
   Translucent pixels dropped (as phases 1-2).  Exact duplicates (Prismatic copies) dropped.
   Colourable (FS-tinted grey) sprites are KEPT here: they are the only side/back witch views for those shapes;
   their caption says their real colours (grey / white).

Holdout: the phase-2 holdout (26 constructions, comparable eval; includes the vanilla Witch Hat c357).  'Witchy Hat -
Mossy' was meant as an extra unseen witch but does not fit 20x20 (skipped), and every other new witch shares a
silhouette with siblings (Kailey x11, Luny x3), so all new hats train.
usage: python3 -I build_dataset_phase3.py  -> dataset/phase3_4view_512/ + dataset/phase3_compact.json (laptop export)"""
import collections, json, os, re, sys, zlib, struct
sys.argv = [sys.argv[0], '512']                         # build_dataset_4view reads its layout from argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dataset as B
import build_dataset_4view as F
HERE, ROOT = B.HERE, B.ROOT
RAW = os.path.join(ROOT, 'experiments', 'witch_reference_packs_01', 'raw')
OUT = os.path.join(HERE, 'dataset', 'phase3_4view_512')
NEW_HOLDOUT = {'Witchy Hat - Mossy'}
MAX_DY = 5
KEYS = {'front': 'FrontHat', 'right': 'RightHat', 'left': 'LeftHat', 'back': 'BackHat'}
PACK_AUTHOR = {'Hats and Horns': ('PlatinumCats', 'platinumcats'), "Luny's Witch Hats for FS": ('Luny', 'luny'),
               'Witch Hats': ('Kailey', 'kaileyw')}


def loose_json(path):
    """FS packs are read by SMAPI's lenient Json.NET: allow // and /* */ comments and trailing commas."""
    s = open(path, encoding='utf-8-sig').read()
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    s = re.sub(r'(?m)^\s*//.*$', '', s)
    s = re.sub(r',\s*([}\]])', r'\1', s)
    return json.loads(s)


def read_png_rgba(path):
    d = open(path, 'rb').read(); assert d[:8] == b'\x89PNG\r\n\x1a\n'
    i, idat, plte, trns = 8, b'', None, None
    while i < len(d):
        n, t = struct.unpack('>I4s', d[i:i + 8]); body = d[i + 8:i + 8 + n]; i += 12 + n
        if t == b'IHDR': w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', body)
        elif t == b'IDAT': idat += body
        elif t == b'PLTE': plte = [tuple(body[k:k + 3]) for k in range(0, len(body), 3)]
        elif t == b'tRNS': trns = body
    assert bd == 8 and il == 0 and ct in (2, 3, 6), (path, bd, ct, il)
    bpp = {2: 3, 3: 1, 6: 4}[ct]; raw = zlib.decompress(idat); stride = w * bpp; out = []; prev = bytearray(stride); p = 0
    for _ in range(h):
        f = raw[p]; line = bytearray(raw[p + 1:p + 1 + stride]); p += 1 + stride
        for k in range(stride):
            a = line[k - bpp] if k >= bpp else 0; b = prev[k]; c = prev[k - bpp] if k >= bpp else 0
            if f == 1: line[k] = (line[k] + a) & 255
            elif f == 2: line[k] = (line[k] + b) & 255
            elif f == 3: line[k] = (line[k] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[k] = (line[k] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out.append(bytes(line)); prev = line
    def px(x, y):
        r = out[y]
        if ct == 6: return tuple(r[x * 4:x * 4 + 4])
        if ct == 2: return tuple(r[x * 3:x * 3 + 3]) + (255,)
        k = r[x]; return plte[k] + ((trns[k] if trns and k < len(trns) else 255),)
    return w, h, px


def new_pack_hats():
    hats, skipped = [], []
    for pack in sorted(os.listdir(RAW)):
        author, aid = PACK_AUTHOR[pack]
        for root, _, files in sorted(os.walk(os.path.join(RAW, pack))):
            if 'hat.json' not in files: continue
            d = loose_json(os.path.join(root, 'hat.json')); name = d.get('Name') or os.path.basename(root)
            w, h, px = read_png_rgba(os.path.join(root, 'hat.png'))
            V, bad = {}, []
            for v, k in KEYS.items():
                m = d.get(k)
                if not m: bad.append(f'{v}: missing'); continue
                sx, sy = m['StartingPosition']['X'], m['StartingPosition']['Y']
                fw, fh = m['HatSize']['Width'], m['HatSize']['Length']
                hx, hy = (m.get('HeadPosition') or {}).get('X', 0), (m.get('HeadPosition') or {}).get('Y', 0)
                if m.get('Scale', 4) != 4: bad.append(f'{v}: scale'); continue
                flip = bool(m.get('Flipped'))       # FS SpriteEffects.FlipHorizontally: mirrored inside the frame
                cells = {}
                for y in range(fh):
                    for x in range(fw):
                        if not (0 <= sx + x < w and 0 <= sy + y < h): continue
                        p = px(sx + x, sy + y)
                        if p[3] < 255: continue
                        cells[((fw - 1 - x if flip else x) - hx, y - hy)] = p[:3]
                V[v] = cells
            rel = os.path.relpath(root, RAW)
            if bad or not all(V.get(v) for v in KEYS):
                skipped.append({'hat': rel, 'why': bad[:2] or ['empty view']}); continue
            # fit into the 20x20 vanilla frame: one uniform downward shift for all views (tips above the frame),
            # at most MAX_DY; sideways at most 1 px per view.  Recorded per hat.
            ys = [y for c in V.values() for _, y in c]; dy = max(0, -min(ys))
            shift, ok = {'dy': dy}, dy <= MAX_DY and max(ys) + dy < 20
            for v, c in V.items():
                xs = [x for x, _ in c]; dx = -min(xs) if min(xs) < 0 else (19 - max(xs) if max(xs) > 19 else 0)
                if abs(dx) > 1 or max(xs) - min(xs) > 19: ok = False
                shift[v] = dx
            if not ok:
                skipped.append({'hat': rel, 'why': [f'does not fit 20x20 (x {min(x for c in V.values() for x, _ in c)}..'
                                                    f'{max(x for c in V.values() for x, _ in c)}, y {min(ys)}..{max(ys)})']}); continue
            V = {v: {(x + shift[v], y + dy): p for (x, y), p in c.items()} for v, c in V.items()}
            hats.append({'pack': pack, 'author': author, 'aid': aid, 'name': name, 'rel': rel, 'V': V, 'shift': shift})
    # drop exact duplicates (Prismatic copies of the same sprite)
    seen, uniq = {}, []
    for hh in hats:
        key = json.dumps({v: sorted((list(k), list(p)) for k, p in hh['V'][v].items()) for v in KEYS})
        if key in seen: skipped.append({'hat': hh['rel'], 'why': [f"duplicate of {seen[key]}"]}); continue
        seen[key] = hh['rel']; uniq.append(hh)
    return uniq, skipped


def new_caption(hh):
    """'witch hat' family word + the FS name's descriptor (parenthesised part kept; author possessives,
    'colourable' / 'prismatic' (FS tint flags, not looks) and the family word itself removed) + front colours."""
    nm = re.sub(r'[^\x00-\x7f]', '', hh['name']).lower()
    words = ['witch hat'] if 'witch' in nm else []
    d = re.sub(r"\b\w+'s\b", ' ', nm)
    d = re.sub(r'\b(colou?rable|prismatic|witch(y)? hat|witch)\b', ' ', d)
    d = re.sub(r'[()\-_,]+', ' ', d); d = ' '.join(d.split())
    if d and d not in ('hat',): words.append(d)
    cnt = collections.Counter(hh['V']['front'].values()); names = []
    for p, _ in cnt.most_common():
        c = B.colour_name(p)
        if c not in names: names.append(c)
        if len(names) == 3: break
    return ', '.join([B.TRIGGER, F.LAYOUT] + words + [', '.join(names), 'pixel art, 20x20 sprites, dark outline'])


def light_neutral(V):
    """phase-2 rule (analysis/aug_check.json): front and back |L(left half) - L(right half)| <= 0.02 (OKLab L)."""
    for v in ('front', 'back'):
        L = [B.to_lch(p)[0] for (x, y), p in V[v].items() if x < 10]; R = [B.to_lch(p)[0] for (x, y), p in V[v].items() if x >= 10]
        if L and R and abs(sum(L) / len(L) - sum(R) / len(R)) > 0.02: return False
    return True


def main():
    # 1) library part: re-run the phase-2 builder logic with the caption fix, into OUT
    p2 = json.load(open(os.path.join(HERE, 'dataset', 'phase2_4view_512', 'manifest.json')))
    lib = {c['id']: c for c in json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))['constructions']}
    labels = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_labels.json')))['labels']
    struct_ = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_structure.json')))['hosts']
    vanilla = {}
    for k, v in json.load(open(B.VANILLA, encoding='utf-8')).items():
        f = v.split('/'); vanilla[int(f[6]) if len(f) > 6 and f[6].strip() else int(k)] = f[0].lower()
    bg = tuple(p2['background'])
    tr, ho = os.path.join(OUT, 'train', f'1_{B.TRIGGER}'), os.path.join(OUT, 'holdout')
    for dd in (tr, ho): os.makedirs(dd, exist_ok=True)
    man = {k: v for k, v in p2.items() if k not in ('items', 'counts', 'holdout_constructions')}
    man.update({'phase': 3, 'caption_fix': 'hats_N -> vanilla name only for ConcernedApe', 'items': [], 'new_packs': {}})
    fixed = []
    for it in p2['items']:
        c = lib[it['construction']]; k = int(re.search(r'__w(\d+)', it['file']).group(1)); w = c['colourways'][k]
        van = vanilla if c['author'] == 'ConcernedApe' else {}
        V = F.views_of(c, w['palette'])
        cap1 = B.caption(c, w['palette'], {}, van, labels, struct_)
        cnt = collections.Counter(V['front'].values()); names = []
        for p, _ in cnt.most_common():
            nm = B.colour_name(p)
            if nm not in names: names.append(nm)
            if len(names) == 3: break
        body = [t for t in cap1.split(', ')[2:] if t and t != 'pixel art' and not t.startswith('20x20') and t != 'dark outline']
        cap = ', '.join([B.TRIGGER, F.LAYOUT] + body + [', '.join(names), 'pixel art, 20x20 sprites, dark outline'])
        if cap != it['caption']: fixed.append({'file': it['file'], 'old': it['caption'], 'new': cap})
        VV = F.mirror_swap(V) if it['augmented'] else V
        dest = tr if it['split'] == 'train' else ho
        B.write_png(os.path.join(dest, it['file'] + '.png'), F.CAN, F.CAN, F.render(VV, bg))
        open(os.path.join(dest, it['file'] + '.txt'), 'w', encoding='ascii').write(cap)
        man['items'].append({**it, 'caption': cap, 'source_kind': 'library'})
    # 2) new packs
    hats, skipped = new_pack_hats(); added = collections.Counter()
    for n_, hh in enumerate(hats):
        cid = f"{hh['aid']}__x{n_:02d}"; split = 'holdout' if hh['name'] in NEW_HOLDOUT else 'train'
        cap = new_caption(hh); dest = tr if split == 'train' else ho
        variants = [('', hh['V'])] + ([('__mx', F.mirror_swap(hh['V']))] if split == 'train' and light_neutral(hh['V']) else [])
        for suf, VV in variants:
            stem = f'{cid}__w0{suf}'
            B.write_png(os.path.join(dest, stem + '.png'), F.CAN, F.CAN, F.render(VV, bg))
            open(os.path.join(dest, stem + '.txt'), 'w', encoding='ascii').write(cap)
            man['items'].append({'file': stem, 'split': split, 'construction': cid, 'author': hh['author'], 'source': hh['rel'],
                                 'augmented': bool(suf), 'caption': cap, 'source_kind': 'user_pack_2026-10-13'})
            added[(hh['pack'], split, bool(suf))] += 1
    man['new_packs'] = {'included': [{'construction': f"{hh['aid']}__x{i:02d}", 'hat': hh['rel'], 'name': hh['name'], 'shift': hh['shift']} for i, hh in enumerate(hats)],
                        'skipped': skipped, 'added_images': {f'{p}|{s}|{"aug" if a else "orig"}': n for (p, s, a), n in added.items()}}
    man['caption_fixed'] = fixed
    cc = collections.Counter((i['split'], i['augmented']) for i in man['items'])
    man['counts'] = {f"{s}{'_aug' if a else ''}": n for (s, a), n in cc.items()}
    man['holdout_constructions'] = sorted({i['construction'] for i in man['items'] if i['split'] == 'holdout'})
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
    # 3) compact export for the laptop (rebuilt there by build_subset_laptop.py, pixel-identical)
    A = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%&*+-:;<=>?@^_~' + ''.join(map(chr, range(0xC0, 0x250)))
    items = []
    for it in man['items']:
        V = None
        if it['source_kind'] == 'library':
            c = lib[it['construction']]; k = int(re.search(r'__w(\d+)', it['file']).group(1)); V = F.views_of(c, c['colourways'][k]['palette'])
        else:
            V = next(hh['V'] for i, hh in enumerate(hats) if f"{hh['aid']}__x{i:02d}" == it['construction'])
        if it['augmented']: V = F.mirror_swap(V)
        pal = sorted({p for v in V.values() for p in v.values()}); assert len(pal) <= len(A), it['file']
        enc = []
        for v in F.VIEWS:
            s = ''.join(A[pal.index(V[v][(i % 20, i // 20)])] if (i % 20, i // 20) in V[v] else '.' for i in range(400))
            enc.append(re.sub(r'\.{2,}', lambda m: f'({len(m.group(0))})', s))
        items.append({'file': it['file'], 'split': it['split'], 'caption': it['caption'], 'pal': [list(p) for p in pal], 'views': enc})
    meta = {'canvas': F.CAN, 'cell': F.CELL, 'margin': F.MARGIN, 'background': list(bg), 'trigger': B.TRIGGER, 'quadrants': F.QUAD}
    json.dump({'meta': meta, 'alphabet': A, 'items': items}, open(os.path.join(HERE, 'dataset', 'phase3_compact.json'), 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
    print('counts', man['counts'], '| captions fixed', len(fixed), '| new hats', len(hats), 'skipped', len(skipped))
    print('added', dict(man['new_packs']['added_images']))


if __name__ == '__main__':
    main()
