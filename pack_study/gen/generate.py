"""Random, coherent 4-view hats from the study library.  Pure Python.

Rules (each one traceable to measured source evidence):
  * STYLE UNIT = author.  One hat never mixes two authors' pixels unless a pair
    is listed in data/style_exceptions.json (empty until a worn capture proves one).
  * CONSTRUCTION = an author's actual drawing; never redrawn.  Only constructions
    with all four views are eligible.
  * COLOUR, one of two proven mechanisms:
      - author recolour: the author shipped >=2 colourways, so MATERIAL indices
        are known.  Take one proven colourway (keeps the author's value/chroma
        structure) and rotate the hue of MATERIAL indices only; FIXED indices
        (lace, gold, eyes) keep the author's colour.
      - greyscale-colourable: Fashion Sense multiplies every pixel by the player
        colour (DrawManager / BEHAVIOR_MAP D1), so baking = grey * tint.
  * PATTERN (uncommon): a pattern variant the author drew on the same mask.
  * ADDON (rare): pixels the author added to this exact construction, proven
    identity-preserving in all views.
usage: generate.py <out_dir> [count] [seed]
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
import png
from restyle import single_material, target_style, ramp_of, restyle
from decorate import load_approved, place
import combine_brimmed
from colour import to_lch, from_lch
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = ['front', 'right', 'left', 'back']
TIERS = [('common', 0.38), ('restyled', 0.20), ('combined', 0.15), ('uncommon', 0.12), ('rare', 0.15)]

def eligible(c):
    return not c['missing'] and (c['material'] is not None or c['colourable'])

FREE_HUE_SPAN = 90   # author's own colourways already span this much hue -> any hue is in-style
HUE_MARGIN = 20      # otherwise stay within the proven hue arc +- this

def hue_range(c, j):
    """Smallest arc covering the proven hues of index j (chromatic colourways only)."""
    hs = sorted(to_lch(w['palette'][j])[2] for w in c['colourways'] if to_lch(w['palette'][j])[1] > 0.03)
    if len(hs) < 2: return (hs[0] if hs else 0), 0
    gaps = [((hs[(k + 1) % len(hs)] - hs[k]) % 360, k) for k in range(len(hs))]
    g, k = max(gaps)
    return hs[(k + 1) % len(hs)], 360 - g

def colourise(c, rng):
    """Return (palette, description) for construction c."""
    if c['colourable']:
        base = c['colourways'][0]['palette']
        pal = [list(p) for p in base]; tints = []
        for layer in c['tintLayers'] or []:
            L, C, H = rng.uniform(0.62, 0.95), rng.uniform(0.03, 0.16), rng.uniform(0, 360)
            tint = from_lch(L, C, H); tints.append(list(tint))
            for j in layer:
                p = base[j]; pal[j] = [p[0] * tint[0] // 255, p[1] * tint[1] // 255, p[2] * tint[2] // 255, p[3]]
        return pal, {'mode': 'fs-multiply-masked', 'tints': tints, 'tint': tints[0] if tints else None}
    way = rng.choice(c['colourways'])
    pal = [list(p) for p in way['palette']]
    counts = [0] * len(pal)
    for g in c['grid']:
        if g >= 0: counts[g] += 1
    mats = [j for j, m in enumerate(c['material']) if m]
    main = max(mats, key=lambda j: counts[j])
    lo, span = hue_range(c, main)
    target = rng.uniform(0, 360) if span >= FREE_HUE_SPAN else (lo - HUE_MARGIN + rng.uniform(0, span + 2 * HUE_MARGIN)) % 360
    dh = target - to_lch(pal[main])[2]
    for j in mats:
        L, C, H = to_lch(pal[j])
        pal[j] = list(from_lch(L, C, (H + dh) % 360)) + [pal[j][3]]
    return pal, {'mode': 'hue-rotate-proven-colourway', 'from': way['source'], 'dHue': round(dh % 360, 1),
                 'hueFree': span >= FREE_HUE_SPAN, 'provenSpan': round(span)}

def render(c, pal, addon=None, tint=None):
    w, h = c['frame']
    W = 4 * w
    px = [[(0, 0, 0, 0)] * W for _ in range(h)]
    for k, g in enumerate(c['grid']):
        if g >= 0: px[k // W][k % W] = tuple(pal[g])
    if addon:
        for x, y, p in addon['pixels']:
            q = p if tint is None else [p[0] * tint[0] // 255, p[1] * tint[1] // 255, p[2] * tint[2] // 255, p[3]]
            px[y][x] = tuple(q)
    return px

def write_hat(pack_dir, name, c, px):
    w, h = c['frame']
    d = os.path.join(pack_dir, 'Hats', name); os.makedirs(d, exist_ok=True)
    sheet = [px[y][v * w:(v + 1) * w] for v in range(4) for y in range(h)]   # stack views vertically
    png.write(os.path.join(d, 'hat.png'), w, 4 * h, sheet)
    model = {'Name': name}
    for v, view in enumerate(VIEWS):
        hp = c['head'].get(view, [0, 0])
        m = {'DisableGrayscale': True, 'StartingPosition': {'X': 0, 'Y': v * h},
             'HeadPosition': {'X': int(hp[0]), 'Y': int(hp[1])}, 'HatSize': {'Width': w, 'Length': h}}
        if c['flags'].get('hideHair'): m['HideHair'] = True
        model[view.capitalize() + 'Hat'] = m
    json.dump(model, open(os.path.join(d, 'hat.json'), 'w'), indent=2)

_STYLE_CACHE = {}

def roll_restyled(lib, rng):
    """Shape from any author, shading from the rolled target author (user direction 2026-10-09)."""
    shapes = [c for c in lib['constructions'] if not c['missing'] and single_material(c)]
    tgt_cons = [c for c in lib['constructions'] if single_material(c) and not c['colourable'] and not c['missing']]
    authors = sorted({c['author'] for c in tgt_cons})
    author = rng.choices(authors, [sum(c['author'] == a for c in tgt_cons) ** 0.5 for a in authors])[0]
    mine = [c for c in tgt_cons if c['author'] == author]
    if author not in _STYLE_CACHE: _STYLE_CACHE[author] = target_style(mine)
    ref = rng.choice(mine); way = rng.randrange(len(ref['colourways']))
    ramp = ramp_of(ref, way)
    if len(ramp) < 3: return None          # too few levels: would flatten the shape
    shape = rng.choice(shapes)
    px = restyle(shape, ramp, _STYLE_CACHE[author])
    return {'tier': 'restyled', 'author': author, 'construction': shape, 'pixels': px,
            'colour': {'mode': 'restyle', 'shapeFrom': shape['id'], 'rampFrom': ref['colourways'][way]['source'],
                       'edgeRank': round(_STYLE_CACHE[author]['edgeRank'], 2)}, 'addon': None, 'palette': None}

_BRIM = None

def roll_combined(rng):
    """Crown of one straw hat on the brim of another, shaded as one author (see combine_brimmed)."""
    global _BRIM
    if _BRIM is None:
        data = json.load(open(os.path.join(HERE, 'data', 'brimmed_parts.json')))['hats']
        combos = [c for c in json.load(open(os.path.join(HERE, 'data', 'brimmed_combos.json')))
                  if 'sun_hat_ribbon' not in c['crown'] + c['brim']]
        _BRIM = (data, combos)
    data, combos = _BRIM
    c = rng.choice(combos)
    a, b, t = data[c['crown']], data[c['brim']], data[c['style']]
    res = combine_brimmed.combine(a, b, t, b['frame'])
    w, h = b['frame']
    px = [[None] * (4 * w) for _ in range(h)]
    for vi, v in enumerate(VIEWS):
        for (x, y), p in res[v].items(): px[y][vi * w + x] = p
    cons = {'id': f"combo:{c['crown']}+{c['brim']}", 'frame': b['frame'], 'head': b['head'], 'flags': {}, 'names': [a['name'], b['name']]}
    return {'tier': 'combined', 'author': t['author'], 'construction': cons,
            'pixels': [p for row in px for p in row], 'colour': {'mode': 'combine', **c}, 'addon': None, 'palette': None}

_DECS = None

def decorate(px, frame, rng):
    """Try approved perched decorations (random order) until one seats in all 4 views."""
    global _DECS
    if _DECS is None: _DECS = [d for d in load_approved() if d['kind'] == 'perched']
    w, h = frame
    masks = {v: [[1 if px[y][vi * w + x][3] else 0 for x in range(w)] for y in range(h)] for vi, v in enumerate(VIEWS)}
    for d in rng.sample(_DECS, len(_DECS)):
        if d['frame'][0] != w: continue
        res = place(d, masks)
        if res:
            for vi, v in enumerate(VIEWS):
                for x, y, p in res[v]: px[y][vi * w + x] = tuple(p)
            return d['label']
    return None

def roll(lib, rng):
    cons = [c for c in lib['constructions'] if eligible(c)]
    addons = {}
    for a in lib['addons']: addons.setdefault(a['base'], []).append(a)
    tier = rng.choices([t for t, _ in TIERS], [w for _, w in TIERS])[0]
    if tier == 'restyled':
        r = roll_restyled(lib, rng)
        if r: return r
        tier = 'common'
    if tier == 'combined':
        return roll_combined(rng)
    authors = sorted({c['author'] for c in cons})
    weight = {a: sum(c['author'] == a for c in cons) ** 0.5 for a in authors}   # variety without 1-item packs dominating
    author = rng.choices(authors, [weight[a] for a in authors])[0]
    mine = [c for c in cons if c['author'] == author]
    pools = {'common': [c for c in mine if not c['patternOf']],
             'uncommon': [c for c in mine if c['patternOf']],
             'rare': [c for c in mine if c['id'] in addons] or [c for c in mine if sum(g >= 0 for g in c['grid']) >= 160]}
    for t in [tier, 'uncommon', 'common']:
        if pools[t]: tier = t if t != 'uncommon' or tier != 'rare' else t; break
    c = rng.choice(pools[tier] or mine)
    pal, how = colourise(c, rng)
    addon = rng.choice(addons[c['id']]) if tier == 'rare' and c['id'] in addons else None
    # rare without an own-base add-on is decorated later (decorate()); demoted only if nothing seats
    return {'tier': tier, 'author': author, 'construction': c, 'palette': pal, 'colour': how, 'addon': addon}

def main():
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 24; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    lib = json.load(open(os.path.join(HERE, 'data', 'library.json')))
    rng = random.Random(seed)
    pack = os.path.join(out, f'[FS] PackStudy Hats s{seed}')
    os.makedirs(pack, exist_ok=True)
    json.dump({'Name': f'PackStudy Hats s{seed}', 'Author': 'pack_study generator', 'Version': '0.1.0',
               'Description': 'Generated from source hats; see pack_study/README.md', 'UniqueID': f'PackStudy.Hats.s{seed}',
               'UpdateKeys': [], 'ContentPackFor': {'UniqueID': 'PeacefulEnd.FashionSense'}},
              open(os.path.join(pack, 'manifest.json'), 'w'), indent=2)
    log, previews = [], []
    for i in range(n):
        r = roll(lib, rng); c = r['construction']
        if r['tier'] in ('restyled', 'combined'):
            w, h = c['frame']; W = 4 * w
            px = [[tuple(r['pixels'][y * W + x]) if r['pixels'][y * W + x] else (0, 0, 0, 0) for x in range(W)] for y in range(h)]
        else:
            tint = r['colour'].get('tint') if c['colourable'] else None
            px = render(c, r['palette'], r['addon'], tint)
        deco = None
        if r['tier'] == 'rare' and not r['addon']:
            deco = decorate(px, c['frame'], rng)
            tries = 0
            while not deco and tries < 12:      # other hats by the same author until one seats a decoration
                tries += 1
                pool = [k for k in lib['constructions'] if k['author'] == r['author'] and eligible(k)
                        and sum(g >= 0 for g in k['grid']) >= 120]
                if not pool: break
                c = rng.choice(pool); pal, how = colourise(c, rng)
                tint = how.get('tint') if c['colourable'] else None
                px = render(c, pal, None, tint)
                deco = decorate(px, c['frame'], rng)
                if deco: r['construction'], r['colour'] = c, how
            if not deco: r['tier'] = 'common'
        name = f"PS{seed}_{i:02d}_{r['tier']}"
        write_hat(pack, name, c, px)
        previews.append((name, c['frame'], px))
        log.append({'name': name, 'tier': r['tier'], 'author': r['author'], 'construction': c['id'],
                    'sourceNames': c['names'][:3], 'colour': r['colour'], 'addon': r['addon'] and r['addon']['id'], 'decoration': deco})
    json.dump(log, open(os.path.join(out, f'roll_log_s{seed}.json'), 'w'), indent=1)
    # preview: 4 views per hat at x4, 4 hats per row
    S, cols, bg = 4, 4, (118, 128, 112, 255)
    cw, ch = 4 * 24 * S + 16, 24 * S + 8
    rows = (len(previews) + cols - 1) // cols
    W, H = cols * cw, rows * ch
    canvas = [[bg] * W for _ in range(H)]
    for k, (name, (w, h), px) in enumerate(previews):
        ox, oy = (k % cols) * cw + 4, (k // cols) * ch + 4
        for y in range(h):
            for x in range(4 * w):
                p = px[y][x]
                if p[3] == 0: continue
                a = p[3] / 255
                for dy in range(S):
                    row = canvas[oy + y * S + dy]
                    for dx in range(S):
                        q = row[ox + x * S + dx + (x // w) * 4]
                        row[ox + x * S + dx + (x // w) * 4] = tuple(round(p[j] * a + q[j] * (1 - a)) for j in range(3)) + (255,)
    png.write(os.path.join(out, f'preview_s{seed}.png'), W, H, canvas)
    from collections import Counter
    print(Counter(l['tier'] for l in log), Counter(l['author'] for l in log).most_common(6))

if __name__ == '__main__':
    main()
