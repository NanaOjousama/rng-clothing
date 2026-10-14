"""Phase-1 LoRA dataset: one FRONT view per image, block-exact on the latent grid.
Pure Python (zlib/struct).  Source = pack_study/data/library.json (studied source hats).
Reads only; writes under experiments/lora_sdxl_research/dataset/.

Per image: a 20x20 view, every logical pixel an exact BLOCKxBLOCK square, centred on a
CANVASxCANVAS flat background whose colour is the one farthest (OKLab) from every corpus
colour.  Semi-transparent author shadows are DROPPED (composited onto magenta they turned purple).
Constructions that are only hair accessories / devices / masks are left out of phase 1.
Split: whole constructions (all colourways of a shape) go to holdout, ~10%, stratified by
first family word, fixed seed.  At most MAX_WAYS colourways per construction.
Colourable (FS-tinted grey) constructions are skipped in phase 1 (no authored colour).
usage: python3 -I build_dataset.py [--views front] [--canvas 768 --block 32]
-> dataset/phase1_front/{train/1_sdvhat,holdout}/<id>__w<k>.png/.txt, manifest.json, contact.png"""
import argparse, collections, json, math, os, random, re, struct, sys, zlib
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'pack_study', 'gen'))
from colour import to_lch
import semantics as SEM
VIEWS = ['front', 'right', 'left', 'back']
VANILLA = '/run/media/deck/USD00/steamapps/common/Stardew Valley/Content (unpacked)/Data/hats.json'
TRIGGER, MAX_WAYS, SEED, HOLD = 'sdvhat', 2, 20261011, 0.10
# phase 1 is about HATS: a construction whose only families are these is left out (its front is a thin
# arc - headbands, bows, earmuffs); they stay available for a later accessory run.
ACCESSORY_ONLY = {'hair', 'device', 'mask'}
FAMILY_WORDS = {'straw': 'straw hat', 'floral': 'flower hat', 'cottage': 'cottage hat', 'western': 'cowboy hat',
                'formal': 'formal hat', 'cavalier': 'tricorn hat', 'cap': 'cap', 'knit': 'knit beanie',
                'fantasy': 'fantasy hat', 'regal': 'crown', 'helmet': 'helmet', 'party': 'party hat',
                'animal': 'animal hat', 'hair': 'hair accessory', 'device': 'head device', 'mask': 'mask', 'hood': 'hood'}


def write_png(path, w, h, rows):
    """rows: list of h bytes objects, each w*3 RGB bytes."""
    raw = b''.join(b'\x00' + r for r in rows)
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def oklab(p):
    L, C, H = to_lch(p); return L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H))


def pick_background(colours):
    labs = [oklab(c) for c in colours]
    best = None
    for r in range(0, 256, 17):
        for g in range(0, 256, 17):
            for b in range(0, 256, 17):
                q = oklab((r, g, b)); d = min(math.dist(q, l) for l in labs)
                if best is None or d > best[0]: best = (d, (r, g, b))
    return best[1], best[0]


def colour_name(p):
    L, C, H = to_lch(p)
    if C < 0.03: return 'black' if L < 0.3 else 'white' if L > 0.9 else 'dark grey' if L < 0.5 else 'grey' if L < 0.75 else 'light grey'
    hue = ('pink' if H < 20 or H >= 345 else 'red' if H < 45 else 'orange' if H < 70 else 'yellow' if H < 110 else
           'green' if H < 165 else 'teal' if H < 200 else 'blue' if H < 265 else 'purple' if H < 315 else 'magenta')
    if hue in ('orange', 'red') and L < 0.55 and C < 0.15: hue = 'brown'
    if hue == 'yellow' and C < 0.09: hue = 'beige'
    tone = 'dark ' if L < 0.45 else 'pale ' if L > 0.85 else 'light ' if L > 0.72 else ''
    return tone + hue


def clean_name(n, vanilla):
    m = re.fullmatch(r'hats_(\d+)', n)
    if m: return vanilla.get(int(m.group(1)))
    if not n.isascii(): return None
    n = re.sub(r'([a-z])([A-Z])', r'\1 \2', n)
    n = re.sub(r'[_\-\.]+', ' ', n); n = re.sub(r'\(.*?\)', ' ', n); n = re.sub(r'\b\d+\b', ' ', n)
    n = re.sub(r'\b(fs|tt|c|v\d*)\b', ' ', n, flags=re.I)
    n = ' '.join(n.split()).lower()
    return n if len(n) >= 3 and not re.fullmatch(r'(female|male|hat|hats|kookoroo|cute beret)', n) else None


def caption(c, pal, cells, vanilla, labels, struct_):
    words = [TRIGGER, 'front view']
    fams = sorted(f for f in SEM.host_families(c['names'], c['id']) if f in FAMILY_WORDS)
    words += [FAMILY_WORDS[f] for f in fams]
    brim = struct_.get(c['id'], {}).get('brim')
    if brim in ('wide', 'narrow'): words.append(f'{brim} brim')
    name = next((x for x in (clean_name(n, vanilla) for n in c['names']) if x), None)
    if name: words.append(name)
    note = labels.get(c['id'], {}).get('note')
    if (note and labels[c['id']].get('confidence') in ('high', 'medium') and note.isascii() and 6 <= len(note) < 60
            and '?' not in note and not re.match(r'(same|see|as )', note, re.I)):
        words.append(note.split(';')[0].strip())
    cnt = collections.Counter(g for g in cells.values() if pal[g][3] == 255)
    names = []
    for g, _ in cnt.most_common():
        nm = colour_name(pal[g])
        if nm not in names: names.append(nm)
        if len(names) == 3: break
    words.append(', '.join(names))
    words.append('pixel art, 20x20 sprite, dark outline')
    return ', '.join(w for w in words if w)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--views', default='front'); ap.add_argument('--canvas', type=int, default=768)
    ap.add_argument('--block', type=int, default=32); ap.add_argument('--name', default='phase1_front'); a = ap.parse_args()
    views = a.views.split(','); CAN, BLK = a.canvas, a.block; OFF = (CAN - 20 * BLK) // 2
    assert OFF >= 0 and OFF % 8 == 0 and BLK % 8 == 0, 'grid must sit on the 8 px latent grid'
    lib = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))
    labels = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_labels.json')))['labels']
    struct_ = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_structure.json')))['hosts']
    vanilla = {}
    for k, v in json.load(open(VANILLA, encoding='utf-8')).items():
        f = v.split('/'); vanilla[int(f[6]) if len(f) > 6 and f[6].strip() else int(k)] = f[0].lower()
    cons = [c for c in lib['constructions'] if not c['missing'] and c['frame'] == [20, 20] and not c['colourable']]
    def fams_of(c): return SEM.host_families(c['names'], c['id']) - {'brimmed', 'brim-narrow', 'unknown'}
    accessory = [c['id'] for c in cons if fams_of(c) and fams_of(c) <= ACCESSORY_ONLY]
    cons = [c for c in cons if c['id'] not in set(accessory)]
    allcol = {tuple(p[:3]) for c in cons for w in c['colourways'] for p in w['palette'] if p[3] > 0}
    bg, margin = pick_background(sorted(allcol))
    # grouped, stratified split
    rng = random.Random(SEED); byfam = collections.defaultdict(list)
    for c in cons:
        f = sorted(SEM.host_families(c['names'], c['id']) - {'brimmed', 'brim-narrow'}) or ['unknown']
        byfam[f[0]].append(c['id'])
    hold = set()
    for f, ids in sorted(byfam.items()):
        ids = sorted(ids); rng.shuffle(ids); hold |= set(ids[:max(1 if len(ids) >= 5 else 0, round(len(ids) * HOLD))])
    out = os.path.join(HERE, 'dataset', a.name)
    tr, ho = os.path.join(out, 'train', f'1_{TRIGGER}'), os.path.join(out, 'holdout')
    for d in (tr, ho): os.makedirs(d, exist_ok=True)
    manifest = {'canvas': CAN, 'block': BLK, 'offset': OFF, 'views': views, 'background': bg,
                'background_min_oklab_distance_to_corpus': round(margin, 3), 'trigger': TRIGGER, 'max_colourways': MAX_WAYS,
                'seed': SEED, 'source': 'pack_study/data/library.json', 'skipped_colourable': sum(c['colourable'] for c in lib['constructions'] if not c['missing'] and c['frame'] == [20, 20]),
                'excluded_accessory_only': accessory, 'translucent_pixels': 'dropped', 'items': []}
    for c in cons:
        dest = ho if c['id'] in hold else tr
        for k, w in enumerate(c['colourways'][:MAX_WAYS]):
            pal = w['palette']
            for v in views:
                vi = VIEWS.index(v); cells = {}
                for i, g in enumerate(c['grid']):
                    y, x = divmod(i, 80)
                    if g >= 0 and x // 20 == vi: cells[(x - vi * 20, y)] = g
                bgrow = bytes(bg) * CAN; rows = []
                for py in range(CAN):
                    ly = (py - OFF) // BLK
                    if not (OFF <= py < OFF + 20 * BLK): rows.append(bgrow); continue
                    r = bytearray(bgrow)
                    for lx in range(20):
                        g = cells.get((lx, ly))
                        if g is None: continue
                        p = pal[g]
                        if p[3] < 255: continue          # author's translucent shadow: dropped (it falls on the head, not the hat)
                        rgb = bytes(p[:3])
                        x0 = (OFF + lx * BLK) * 3; r[x0:x0 + BLK * 3] = rgb * BLK
                    rows.append(bytes(r))
                stem = f"{c['id']}__w{k}" + ('' if views == ['front'] else f'__{v}')
                write_png(os.path.join(dest, stem + '.png'), CAN, CAN, rows)
                cap = caption(c, pal, cells, vanilla, labels, struct_).replace('front view', f'{v} view')
                open(os.path.join(dest, stem + '.txt'), 'w', encoding='ascii').write(cap)
                manifest['items'].append({'file': stem, 'split': 'holdout' if c['id'] in hold else 'train', 'construction': c['id'],
                                          'author': c['author'], 'pack': c['pack'], 'source': w['source'], 'view': v,
                                          'translucent_px': sum(1 for g in cells.values() if 0 < pal[g][3] < 255), 'caption': cap})
    n = collections.Counter(i['split'] for i in manifest['items'])
    manifest['counts'] = dict(n); manifest['holdout_constructions'] = sorted(hold)
    manifest['captions_with_colour_only'] = [i['file'] for i in manifest['items']
                                             if i['caption'].split(', ')[2] in {colour_name(x) for x in allcol}]
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    print('background', bg, 'margin', round(margin, 3), '| images', dict(n), '| holdout constructions', len(hold))


if __name__ == '__main__':
    main()
