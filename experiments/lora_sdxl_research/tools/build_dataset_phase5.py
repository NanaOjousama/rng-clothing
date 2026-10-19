"""Phase-5 dataset (user, 2026-10-18): one general-purpose hat LoRA, A40, 768 px.  Pure Python (zlib/struct), Deck.

ONE dataset, TWO layouts of the same hats, captioned apart (user rule: the model must not confuse them):
  front     'front view, single sprite'   24x24 frame x 32-px cells = 768, no margin
  fourview  'four views, 2x2 sheet, ...'  2x2 sheet of 24x24 frames (F|R / L|B) x 16-px cells = 768, no margin
Every logical pixel is an exact cell x cell block (cell is a multiple of 8, so it sits on the SDXL latent grid).
No scaling filter anywhere; translucent author shadows are dropped (phases 1-4).

Frame: 24x24 window = vanilla hat cell x -2..21, y -4..19 (phase 4).  Each view is placed by its own FS HeadPosition:
cell (x, y) of an HxW view lands at (x - HeadPosition.X + 2, y - HeadPosition.Y + 4), the rule
build_dataset_phase4.pack_hats used; library 'head' is the same FS HeadPosition (pack_study/tools/extract_hats.py).

Sources (read-only, never written; raw packs are read from the MAIN checkout when run from a worktree):
  library   pack_study/data/library.json -- every studied construction and colourway (not only the phase-1/3 picks)
  packs     the six phase-4 witch / foliage reference packs (build_dataset_phase4.PACKS, read by its pack_hats)
NEVER used: generated experiments (build_dataset_phase4.FORBIDDEN_SOURCES); the validator checks.

Colourable (FS-tinted grey) hats are TINTED the way Fashion Sense draws them (DrawManager.DrawColorMask: the base is
drawn untinted, then every pixel that exactly matches a ColorMaskLayer value is redrawn multiplied by that layer's
colour; no mask layers = the whole model multiplied).  One deterministic tint per construction, recorded per item.

Families: shape families from names (vanilla names for ConcernedApe only: the phase-1 vanilla-slot bug), the hand labels
in pack_study/data/host_labels.json, and the eye-verified table configs/phase5_family_overrides.json (wins).
Brim words come only from the verified pack_study/data/host_structure.json.
Balance by SELECTION: num_repeats 1, each family capped at FAMILY_SHARE of the kept hats by keeping its most distinct
silhouettes.  Holdout: whole silhouette bodies, per family, for every family with >= 3 bodies.
usage: python3 -I build_dataset_phase5.py [--review] [--stats]"""
import collections, hashlib, json, math, os, random, re, shutil, sys
sys.argv, _ARGS = [sys.argv[0], '512'], sys.argv[1:]     # build_dataset_4view reads its layout from argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_dataset as B
import build_dataset_4view as F
import build_dataset_phase4 as P4
HERE, ROOT = B.HERE, B.ROOT


def main_checkout():
    """the repo whose gitignored raw packs / dataset dir we use (this file may run from a worktree)."""
    g = os.path.join(ROOT, '.git')
    if os.path.isfile(g):
        gd = open(g).read().split('gitdir:', 1)[1].strip()
        return os.path.dirname(os.path.dirname(os.path.dirname(gd)))
    return ROOT


SRC = main_checkout()
P4.EXP = os.path.join(SRC, 'experiments')
NAME = 'phase5_v1'
OUT = os.path.join(SRC, 'experiments', 'lora_sdxl_research', 'dataset', NAME)
OVERRIDES = os.path.join(HERE, 'configs', 'phase5_family_overrides.json')
FW, OX, OY = 24, 2, 4
CAN = 768
LAYOUTS = {'front': {'grid': FW, 'cell': 32, 'phrase': 'front view, single sprite', 'frame': '24x24 sprite'},
           'fourview': {'grid': 2 * FW, 'cell': 16, 'frame': '24x24 sprites',
                        'phrase': 'four views, 2x2 sheet, front top-left, right top-right, left bottom-left, back bottom-right'}}
SEED, HOLD, FAMILY_SHARE = 20261018, 0.10, 0.12
MAX_PER_STRUCT, SIDE_IOU, BODY_IOU, MAX_PER_BODY = 2, 0.90, 0.95, 4
# FS dye-like tints, light enough that a multiply keeps the grey ramp readable
TINTS = [(224, 78, 66), (236, 146, 58), (238, 206, 86), (122, 186, 80), (78, 168, 170), (88, 128, 214),
         (156, 98, 196), (232, 128, 172), (164, 112, 70), (210, 196, 160)]
SLOT = re.compile(r'^(hats_\d+|(good ?hat)?(fe)?male_\d+|goodhatmale_\d+|hyoung_hats_\d+|kookoroo_\d+|tt\.summer\..*|'
                  r'hat \d+|subabytvanz hat \d+|\d+)$', re.I)
# shape families, first match wins, on lower-case display names.  'accessory' = not a hat (excluded).
RULES = [
    (r'witch|wizard|\bmage\b|arcane', 'witch hat'),
    (r'\bhood', 'hood'),
    (r'cap ?& ?headphones', 'cap'),
    # a worn object that is not a hat, even when a hat word is in the name ('Veil (Tiara)', 'Earmuffs (Horns)')
    (r'headphones|earmuffs|headband|hair ?buns?|\bbells?\b|veil|mask|goggles|eye patch|hair bone|tropiclip|^daisy$|'
     r'watermelon band|\bears\b|bunny ?band|\bhorns?\b|kafra band|antlers', 'accessory'),
    (r'flower crown|garland|wreath|flower dance', 'flower crown'),
    (r'helm|hard hat', 'helmet'),
    (r'tiara|diadem|coronet|crown', 'crown'),
    (r'cowboy|cowgal|cowpoke|gil.s hat|western', 'cowboy hat'),
    (r'top hat|magician|sweet ?gent|leprechaun|qi.s hat|governor', 'top hat'),
    (r'bowler|derby', 'bowler hat'),
    (r'fedora|trilby|detective|sherlock|watson', 'fedora'),
    (r'bucket|fishing hat|sou.wester', 'bucket hat'),
    (r'boater|flat topped', 'boater hat'),
    (r'straw hat|sun ?hat|sombrero|beekeeper|chapeau|fashion hat|hat ?of ?girl', 'wide-brim hat'),
    (r'sakkat|rice hat|conical', 'conical hat'),
    (r'tricorn|pirate|swashbuckler|cavalier', 'tricorn hat'),
    (r'party|cone hat|propeller|jester|paper hat|cake ?hat', 'party hat'),
    (r'mushroom', 'mushroom hat'),
    (r'paperboy|pageboy|newsboy|flat cap', 'flat cap'),
    (r'gnome', 'pointed cap'),
    (r'bonnet|maid cap', 'bonnet'),
    (r'\bcaps?\b|snapback|ballcap|trucker|visor', 'cap'),
    (r'beret|\btam\b', 'beret'),
    (r'beanie|knit|toque|trapper|santa|针织帽', 'beanie'),
    (r'headscarf|kerchief|bandana|turban', 'headscarf'),
    (r'panda|frog|tiger|raccoon|dinosaur|squid|shark|fish|teddy|\bbear|\bcat\b|bunny|rabbit|baobao|drooping|amistr|junimo', 'animal hat'),
    (r'chef|garbage|living hat|\bpan\b|tulip|strawberry|pumpkin|\bfez\b|emily|deviruchi|cake|melon', 'novelty hat'),
    (r'pillbox', 'pillbox hat'),
    # decoration words only decide when no hat shape matched ('Sun Hat (Ribbon)' is a sun hat, 'Pink Bow' is a bow)
    (r'\bbows?\b|ribbon|charming', 'accessory'),
]
STOP = re.compile(r'\b(prismatic|colou?rable|standard|round|angled|small|large|double|doubles|singles?|side|new|ver|'
                  r'red|orange|yellow|green|blue|purple|pink|white|black|grey|gray|brown|beige|cream|dark|light|bubblegum|flame)\b')
# pack_study hand-label families (host_labels.json, high/medium confidence) -> weak prior for slot-named hats
SEM_PRIOR = {'knit': 'beanie', 'straw': 'wide-brim hat', 'western': 'cowboy hat', 'cap': 'cap', 'hood': 'hood',
             'regal': 'crown', 'party': 'party hat', 'helmet': 'helmet', 'cavalier': 'tricorn hat', 'formal': 'top hat',
             'floral': 'flower crown', 'animal': 'animal hat', 'hair': 'accessory', 'device': 'accessory', 'mask': 'accessory'}
BRIMMED = {'wide-brim hat', 'cowboy hat', 'bowler hat', 'fedora', 'top hat', 'bucket hat', 'boater hat'}


def vanilla_names():
    out = {}
    for k, v in json.load(open(B.VANILLA, encoding='utf-8')).items():
        f = v.split('/'); out[int(f[6]) if len(f) > 6 and f[6].strip() else int(k)] = f[0]
    return out


def tint_of(key):
    h = int(hashlib.sha1(key.encode()).hexdigest(), 16)
    return TINTS[h % len(TINTS)], TINTS[(h // len(TINTS) + 3) % len(TINTS)]


def mul(p, t): return tuple(round(a * b / 255) for a, b in zip(p, t))
def is_grey(p): return max(p) - min(p) <= 12


def tinted(pal, masks, colourable, key):
    """FS draw of a colourable model: mask-layer pixels multiplied by their layer colour (layer 0, 1 tints)."""
    if not colourable: return pal, None
    t0, t1 = tint_of(key); out = []
    layers = [{tuple(v[:3]) for v in m['values']} for m in masks]
    for p in pal:
        rgb = tuple(p[:3]); hit = next((i for i, L in enumerate(layers) if rgb in L), None)
        if layers: q = mul(rgb, (t0, t1)[min(hit, 1)]) if hit is not None else rgb
        else: q = mul(rgb, t0) if is_grey(rgb) else rgb
        out.append(list(q) + [p[3]])
    return out, [list(t0)] + ([list(t1)] if len(layers) > 1 else [])


def place(c, pal):
    W, H = c['frame']; V = {v: {} for v in F.VIEWS}
    for k, g in enumerate(c['grid']):
        if g < 0: continue
        y, x = divmod(k, 4 * W); p = pal[g]
        if p[3] < 255: continue                       # translucent author shadow: dropped (phases 1-4)
        v = F.VIEWS[x // W]; hx, hy = c['head'].get(v, [0, 0])
        V[v][(x % W - hx + OX, y - hy + OY)] = tuple(p[:3])
    return V


def fits(V):
    xs = [x for d in V.values() for x, _ in d]; ys = [y for d in V.values() for _, y in d]
    return all(V[v] for v in F.VIEWS) and min(xs) >= 0 and max(xs) < FW and min(ys) >= 0 and max(ys) < FW


def display_names(names, author, vanilla):
    out = []
    for n in names:
        m = re.fullmatch(r'hats_(\d+)', n)
        if m:
            if author == 'ConcernedApe' and vanilla.get(int(m.group(1))): out.append(vanilla[int(m.group(1))])
            continue                                   # replacement art in a vanilla slot: name unverified
        if SLOT.match(n.strip()): continue
        if not n.isascii():
            if '针织帽' in n: out.append('knit hat')
            continue
        n2 = re.sub(r'([a-z])([A-Z])', r'\1 \2', n); n2 = re.sub(r'^\d+[_ ]', '', n2); n2 = n2.replace('w/', 'with')
        n2 = re.sub(r'[_\.]+', ' ', n2); n2 = re.sub(r'\b\d+\b', ' ', n2); n2 = re.sub(r'\(\s*\)', ' ', n2)
        n2 = re.sub(r'\s+', ' ', n2).strip(' -,')
        if len(n2) >= 3: out.append(n2)
    return list(dict.fromkeys(out))


def split_name(n):
    """'Sun Hat (Ribbon)' -> ('sun hat', 'ribbon'); colour / variant words dropped (colours are captioned separately)."""
    n = n.lower(); m = re.match(r'^(.*?)\s*\((.*?)\)\s*(.*)$', n)
    base, dec = ((m.group(1) + ' ' + m.group(3)), m.group(2)) if m else (re.sub(r'\s+-\s+.*$', '', n), (n.split(' - ', 1)[1] if ' - ' in n else ''))
    clean = lambda s: re.sub(r'\s+', ' ', STOP.sub(' ', re.sub(r'[,()]', ' ', s))).strip(' -')
    base, dec = clean(base), clean(dec)
    return (base if len(base) >= 3 else None), (dec if len(dec) >= 3 else None)


def auto_family(dnames, sem):
    for n in dnames:
        for rx, f in RULES:
            if re.search(rx, n.lower()): return f, f'name:{n}'
    for s in sorted(sem):
        if s in SEM_PRIOR: return SEM_PRIOR[s], f'label:{s}'
    return None, 'none'


def library_hats(vanilla):
    lib = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))
    struct_ = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'host_structure.json')))['hosts']
    hats, skipped = [], []
    for c in lib['constructions']:
        if c['missing']: continue
        dn = display_names(c['names'], c['author'], vanilla)
        sem = B.SEM.host_families(c['names'], c['id']) - {'brimmed', 'brim-narrow', 'unknown'}
        for k, w in enumerate(c['colourways']):
            pal, tint = tinted(w['palette'], c['flags'].get('colorMaskLayers', []), bool(c['colourable']), c['id'])
            V = place(c, pal)
            if not fits(V): skipped.append({'hat': f"{c['id']}__w{k}", 'why': 'outside 24x24 window or empty view'}); continue
            hats.append({'key': c['id'], 'rel': f"{c['id']}__w{k}", 'kind': 'library', 'author': c['author'], 'pack': c['pack'],
                         'names': dn, 'sem': sorted(sem), 'V': V, 'colourable': bool(c['colourable']), 'tint': tint,
                         'brim': struct_.get(c['id'], {}).get('brim'), 'source': w['source'], 'witch_sub': None, 'decor': None})
    return hats, skipped


def reference_pack_hats():
    hats, skipped = P4.pack_hats(); out = []
    for h in hats:
        key = f"{h['aid']}::{h['name']}"; V = h['V']; tint = None
        if h['colourable']:
            t0, _ = tint_of(key); tint = [list(t0)]
            V = {v: {a: (mul(p, t0) if is_grey(p) else p) for a, p in d.items()} for v, d in V.items()}
        sub = P4.family_of(h['name']) if h['pack'] != 'Hats and Horns' or 'witch' in h['name'].lower() else None
        out.append({'key': key, 'rel': h['rel'], 'kind': 'reference_pack', 'author': h['author'], 'pack': h['pack'],
                    'names': [P4.pack_words(h)[0][0]] if not sub else [h['name']], 'sem': [], 'V': V,
                    'colourable': h['colourable'], 'tint': tint, 'brim': None, 'source': h['rel'],
                    'witch_sub': sub, 'decor': P4.decor_of(h['name'], h['pack']) if sub else None})
    return out, skipped


def assign(hats, overrides):
    for h in hats:
        o = overrides.get(h['key'], {})
        if h['witch_sub']: fam, why = 'witch hat', 'pack:witch'
        else: fam, why = auto_family(h['names'], h['sem'])
        if 'family' in o: fam, why = o['family'], 'override'
        h['family'], h['family_why'] = fam, why
        base, dec = split_name(h['names'][0]) if h['names'] and not h['witch_sub'] else (None, None)
        h['name'] = o['name'] if 'name' in o else (base if base and base != fam else None)
        if dec and not h['decor']: h['decor'] = dec
        if 'decor' in o: h['decor'] = o['decor']
        if 'brim' in o: h['brim'] = o['brim']           # eye x4 correction of host_structure.json
        if o.get('witch_sub'): h['witch_sub'] = o['witch_sub']
        h['exclude'] = o.get('exclude') or ('accessory, not a hat' if fam == 'accessory' else None)
        h['note'] = o.get('note')
    fams = {h['family'] for h in hats} - {None}
    for h in hats:                                      # a decoration / name must never read as another family
        if h['decor'] and h['decor'] in fams and h['decor'] != h['family']: h['decor'] = DECOR_RENAME.get(h['decor'], h['decor'] + ' shape')
        if h['name'] and h['name'] in fams and h['name'] != h['family']: h['name'] = None
    return hats


DECOR_RENAME = {'flower crown': 'ring of flowers', 'crown': 'small crown', 'beret': 'beret shape'}


def fr(h): return frozenset(h['V']['front'])


def iou_m(a, b):
    am = frozenset((FW - 1 - x, y) for x, y in a)
    return max(len(a & b) / len(a | b), len(am & b) / len(am | b))


def cdist(a, b):
    ma = [sum(c) / len(c) for c in zip(*a['V']['front'].values())]; mb = [sum(c) / len(c) for c in zip(*b['V']['front'].values())]
    return sum((x - y) ** 2 for x, y in zip(ma, mb)) ** 0.5


def dedupe(hats):
    """exact duplicates, then <= MAX_PER_STRUCT colourings of one structure, then <= MAX_PER_BODY hats per silhouette body.
    phase-4 select(), generalised: authored colours before tinted, then the most different colours / names."""
    seen, uniq, dropped = {}, [], []
    for h in hats:
        k = json.dumps({v: sorted((list(a), list(p)) for a, p in h['V'][v].items()) for v in F.VIEWS})
        if k in seen: dropped.append({'hat': h['rel'], 'why': f'exact duplicate of {seen[k]}'}); continue
        seen[k] = h['rel']; uniq.append(h)
    def same(a, b):
        if set(a['V']['front']) != set(b['V']['front']): return False
        return all(len(set(a['V'][v]) & set(b['V'][v])) / max(1, len(set(a['V'][v]) | set(b['V'][v]))) >= SIDE_IOU for v in ('right', 'left', 'back'))
    groups = []
    for h in uniq:
        g = next((g for g in groups if same(g[0], h)), None)
        (g.append(h) if g else groups.append([h]))
    keep = []
    for g in groups:
        g = sorted(g, key=lambda h: (h['colourable'], h['rel'])); chosen = [g[0]]
        while len(chosen) < min(MAX_PER_STRUCT, len(g)):
            rest = [h for h in g if h not in chosen and not h['colourable']] or [h for h in g if h not in chosen]
            chosen.append(max(rest, key=lambda h: min(cdist(h, c) for c in chosen)))
        for h in g:
            h['struct_group'] = sorted(x['rel'] for x in g)
            if h in chosen: keep.append(h)
            else: dropped.append({'hat': h['rel'], 'why': f'recolour cap: {len(g)} colourings of one structure'})
    bodies = []
    for h in keep:
        hit = [b for b in bodies if any(iou_m(fr(h), fr(o)) >= BODY_IOU for o in b)]
        bodies = [b for b in bodies if b not in hit] + [[h] + [o for b in hit for o in b]]
    keep2 = []
    for bi, b in enumerate(sorted(bodies, key=lambda b: sorted(x['rel'] for x in b))):
        b = sorted(b, key=lambda h: (h['colourable'], h['rel'])); chosen = []
        while len(chosen) < min(MAX_PER_BODY, len(b)):
            rest = [h for h in b if h not in chosen]
            chosen.append(max(rest, key=lambda h: (not h['colourable'], (h['name'], h['decor']) not in {(c['name'], c['decor']) for c in chosen},
                                                     min([cdist(h, c) for c in chosen] or [0]))))
        bid = f"body{bi:03d}"
        for h in b:
            h['body'] = bid
            if h in chosen: keep2.append(h)
            else: dropped.append({'hat': h['rel'], 'why': f'body cap: {len(b)} hats share one silhouette'})
    return keep2, dropped


def balance(keep):
    """cap each family at FAMILY_SHARE of all kept hats: keep the most distinct silhouettes (farthest point, front IoU)."""
    cap = max(1, math.floor(FAMILY_SHARE * len(keep))); byf = collections.defaultdict(list); out, dropped = [], []
    for h in keep: byf[h['family']].append(h)
    for f, hs in sorted(byf.items()):
        if len(hs) <= cap: out += hs; continue
        hs = sorted(hs, key=lambda h: (h['colourable'], h['rel'])); chosen = [hs[0]]
        while len(chosen) < cap:
            chosen.append(max((h for h in hs if h not in chosen),
                              key=lambda h: (min(1 - iou_m(fr(h), fr(c)) for c in chosen), not h['colourable'])))
        out += chosen
        dropped += [{'hat': h['rel'], 'why': f'family cap: {f} {len(hs)} > {cap}'} for h in hs if h not in chosen]
    return out, dropped, cap


def split(keep):
    rng = random.Random(SEED); byf = collections.defaultdict(set); hold = set()
    for h in keep: byf[h['family']].add(h['body'])
    for f, bs in sorted(byf.items()):
        bs = sorted(bs)
        if len(bs) < 3: continue
        rng.shuffle(bs); hold |= set(bs[:max(1, round(len(bs) * HOLD))])
    for h in keep: h['split'] = 'holdout' if h['body'] in hold else 'train'
    return hold


def caption(h, layout):
    L = LAYOUTS[layout]; words = [B.TRIGGER, L['phrase'], h['family']]
    if h['witch_sub'] and h['witch_sub'] != h['family']: words.append(h['witch_sub'])
    if h['brim'] in ('wide', 'narrow', 'upturned') and h['family'] != 'witch hat': words.append(f"{h['brim']} brim")
    if h['name'] and h['name'] != h['family'] and h['name'] not in words: words.append(h['name'])
    if h['decor']: words.append(h['decor'])
    cnt = collections.Counter(h['V']['front'].values()); names = []
    for p, _ in cnt.most_common():
        nm = B.colour_name(p)
        if nm not in names: names.append(nm)
        if len(names) == 3: break
    return ', '.join(words + names + ['pixel art', L['frame'], 'dark outline'])


def cells_of(V, layout):
    return dict(V['front']) if layout == 'front' else P4.sheet_cells(V)


def cell_hash(cells):
    return hashlib.sha1(json.dumps(sorted(cells)).encode()).hexdigest()[:16]


def flags(h):
    """caption-level conflicts the eye review must resolve (audit_captions BRIM_CONFLICT equivalent)."""
    out = []
    if h['family'] in BRIMMED and h['brim'] == 'none': out.append('BRIM_CONFLICT: brimmed family, verified brim none')
    if h['family'] not in BRIMMED and h['brim'] in ('wide',) and h['family'] not in ('witch hat', 'tricorn hat', 'conical hat', 'party hat'):
        out.append(f"BRIM_CONFLICT: verified wide brim on {h['family']}")
    if h['family'] is None: out.append('NO_FAMILY')
    return out


def gather():
    vanilla = vanilla_names(); overrides = json.load(open(OVERRIDES)) if os.path.exists(OVERRIDES) else {}
    overrides = {k: v for k, v in overrides.items() if not k.startswith('_')}
    lib, sk1 = library_hats(vanilla); packs, sk2 = reference_pack_hats()
    hats = assign(lib + packs, overrides)
    unknown = sorted(set(overrides) - {h['key'] for h in hats})
    if unknown: sys.exit(f'override keys match no candidate: {unknown}')
    return hats, sk1 + sk2, overrides


def review(hats):
    os.makedirs(OUT + '_review', exist_ok=True)
    rows = [{'key': h['key'], 'rel': h['rel'], 'family': h['family'], 'why': h['family_why'], 'name': h['name'],
             'names': h['names'], 'sem': h['sem'], 'brim': h['brim'], 'author': h['author'], 'pack': h['pack'],
             'witch_sub': h['witch_sub'], 'exclude': h['exclude'], 'tint': h['tint'], 'flags': flags(h),
             'views': {v: [[x, y, *p] for (x, y), p in sorted(d.items())] for v, d in h['V'].items()}} for h in hats]
    json.dump(rows, open(os.path.join(OUT + '_review', 'candidates.json'), 'w'))
    c = collections.Counter(h['family'] for h in hats)
    print('candidates', len(hats), '| by family', c.most_common())
    print('flags', collections.Counter(f.split(':')[0] for h in hats for f in flags(h)))


def main():
    hats, skipped, overrides = gather()
    if '--review' in _ARGS: review(hats); return
    bad = [h for h in hats if not h['exclude'] and flags(h)]
    if bad:
        for h in bad[:40]: print('  UNRESOLVED', h['rel'], h['family'], h['names'], flags(h))
        sys.exit(f'{len(bad)} candidates with unresolved family / brim flags: add them to {OVERRIDES}')
    excluded = [{'hat': h['rel'], 'why': h['exclude']} for h in hats if h['exclude']]
    keep, dropped = dedupe([h for h in hats if not h['exclude']])
    keep, dropped2, cap = balance(keep); hold = split(keep)
    allcol = {p for h in keep for d in h['V'].values() for p in d.values()}
    bg, margin = B.pick_background(sorted(allcol))
    if '--stats' in _ARGS:
        c = collections.Counter((h['family'], h['split']) for h in keep)
        for f in sorted({f for f, _ in c}): print(f'  {f:16} train {c[(f, "train")]:3}  holdout {c[(f, "holdout")]:3}')
        print('kept', len(keep), '| family cap', cap, '| excluded', len(excluded), '| dropped', len(dropped) + len(dropped2),
              '| bg', bg, 'min OKLab', round(margin, 3)); return
    man = {'phase': 5, 'dataset': NAME, 'canvas': CAN, 'layouts': {k: {kk: vv for kk, vv in v.items()} for k, v in LAYOUTS.items()},
           'frame': FW, 'window_vanilla': {'x': [-OX, FW - 1 - OX], 'y': [-OY, FW - 1 - OY]}, 'background': list(bg),
           'background_min_oklab_distance': round(margin, 3), 'trigger': B.TRIGGER, 'seed': SEED, 'family_share': FAMILY_SHARE,
           'family_cap': cap, 'max_per_structure': MAX_PER_STRUCT, 'max_per_body': MAX_PER_BODY, 'holdout_bodies': sorted(hold),
           'quadrants': P4.QUAD, 'mirror': f'x -> {FW - 1} - x in the 24-px frame; right<->left swapped', 'num_repeats': 1,
           'lane': 'AI-ORIGINAL training data (source art, CLAUDE.md 2b)', 'skipped': skipped, 'excluded': excluded,
           'dropped': dropped + dropped2, 'items': []}
    tr, ho = os.path.join(OUT, 'train', f'1_{B.TRIGGER}'), os.path.join(OUT, 'holdout')
    for d in (tr, ho):                                  # this script's own versioned output only
        if os.path.isdir(d): shutil.rmtree(d)
        os.makedirs(d)
    stems = set()
    for n, h in enumerate(sorted(keep, key=lambda h: h['rel'])):
        if h['kind'] == 'library': stem0 = re.sub(r'[^A-Za-z0-9_]+', '_', h['rel'])
        else:
            aid, nm = h['key'].split('::', 1)
            stem0 = f"{aid}__p_{re.sub(r'[^A-Za-z0-9]+', '_', nm).strip('_')[:60]}_{hashlib.sha1(h['rel'].encode()).hexdigest()[:6]}"
        assert stem0 not in stems, f'stem collision {stem0}'; stems.add(stem0)
        variants = [(h['V'], False)] + ([(P4.mirror24(h['V']), True)] if h['split'] == 'train' and P4.light_neutral(h['V']) else [])
        for V, aug in variants:
            hh = dict(h, V=V)
            for lay, L in LAYOUTS.items():
                stem = f"{stem0}__{lay}" + ('__mx' if aug else '')
                cells = cells_of(V, lay); can, rows = P4.render(cells, L['grid'], L['cell'], 0, bg)
                assert can == CAN
                dest = ho if h['split'] == 'holdout' else tr
                B.write_png(os.path.join(dest, stem + '.png'), can, can, rows)
                cap_ = caption(hh, lay); open(os.path.join(dest, stem + '.txt'), 'w', encoding='ascii').write(cap_)
                man['items'].append({'file': stem, 'split': h['split'], 'layout': lay, 'augmented': aug, 'family': h['family'],
                                     'witch_sub': h['witch_sub'], 'construction': h['key'], 'colourway': h['rel'],
                                     'struct_group': h['struct_group'], 'body': h['body'], 'author': h['author'], 'pack': h['pack'],
                                     'source': h['source'], 'source_kind': h['kind'], 'colourable': h['colourable'], 'tint': h['tint'],
                                     'brim': h['brim'], 'family_why': h['family_why'], 'n_cells': len(cells), 'cells_sha': cell_hash(cells),
                                     'colours': sorted({list(p) and B.colour_name(p) for p in cells.values()}), 'caption': cap_})
    c = collections.Counter((i['split'], i['layout'], i['augmented']) for i in man['items'])
    man['counts'] = {f"{s}|{l}|{'aug' if a else 'orig'}": n for (s, l, a), n in sorted(c.items())}
    tf = collections.Counter(i['family'] for i in man['items'] if i['split'] == 'train')
    man['train_family_share'] = {f: round(n / sum(tf.values()), 3) for f, n in tf.most_common()}
    man['holdout_families'] = dict(collections.Counter(i['family'] for i in man['items'] if i['split'] == 'holdout' and i['layout'] == 'front'))
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
    print(NAME, '| bg', bg, 'min OKLab', man['background_min_oklab_distance'], '| family cap', cap)
    for k, v in man['counts'].items(): print('   ', k, v)
    print('    train share', man['train_family_share']); print('    holdout', man['holdout_families'])


if __name__ == '__main__':
    main()
