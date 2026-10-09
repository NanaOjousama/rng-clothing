"""Turn the measured study into a generator library (data/library.json).

Everything in the library is source pixels plus measured relations:

construction  one author's drawing of one shape, as an index grid over the 4 views,
              with every PROVEN colourway (the author's own recolours).  An index
              whose colour changes across the author's colourways is MATERIAL;
              one that never changes is FIXED (lace, gold, eyes...).  With a single
              colourway the split is UNKNOWN and the construction is not recoloured
              (unless it is greyscale-colourable, where FS itself tints every pixel).
pattern       two constructions with the same alpha mask whose colour structure
              differs (e.g. plaid vs solid) -> recorded as `patternOf`.
addon         pixels an author ADDED to an unchanged base (identity-preserved in all
              views) -> a part with its own pixels, proven on that base only.
style         per-author outline class measured from edge/interior luminance.
"""
import json, os, statistics as st
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(HERE, 'data', *p)

def style_class(ratio):
    return 'hard_outline' if ratio < 0.4 else ('tonal_outline' if ratio < 0.78 else 'soft')

def main():
    recs = {r['id']: r for r in json.load(open(D('hats.json')))}
    feats = {f['id']: f for f in json.load(open(D('hat_features.json')))}
    fam_of = {m: f['family'] for f in json.load(open(D('families.json'))) for m in f['members']}
    variants = json.load(open(D('variant_sets.json')))

    # ---- style per author (measured) -------------------------------------
    styles = {}
    by_author = {}
    for f in feats.values(): by_author.setdefault(f['author'], []).append(f)
    for a, fs in by_author.items():
        fr = [f['views']['front'] for f in fs if f['views']['front'] and f['views']['front']['innerL'] > 0]
        ratio = st.median(v['edgeL'] / v['innerL'] for v in fr) if fr else 1.0
        gray = st.median(v['gray'] for v in fr) if fr else 0
        styles[a] = {'edgeToInnerL': round(ratio, 3), 'outline': style_class(ratio),
                     'greyscaleAuthored': gray > 0.8, 'medianColours': st.median(v['ncol'] for v in fr) if fr else 0,
                     'n': len(fs)}

    # ---- constructions ----------------------------------------------------
    img = lambda i: Image.open(D('hats', i + '.png')).convert('RGBA')
    groups = {}
    for i, r in recs.items():
        m = bytes(a > 0 for a in img(i).getchannel('A').tobytes())
        groups.setdefault((r['author'], tuple(r['frame']), m), []).append(i)
    cons, cid_of = [], {}
    for (author, frame, _), ids in groups.items():
        classes = []                     # remap classes = one construction each
        for i in ids:
            px = img(i).get_flattened_data()
            for c in classes:
                fa, fb, ok = {}, {}, True
                for x, y in zip(c['px0'], px):
                    if x[3] == 0 and y[3] == 0: continue
                    if fa.setdefault(x, y) != y or fb.setdefault(y, x) != x: ok = False; break
                if ok: c['members'].append((i, px)); break
            else:
                classes.append({'px0': px, 'members': [(i, px)]})
        for k, c in enumerate(classes):
            base_px = c['px0']
            pal = []; index = {}
            grid = []
            for p in base_px:
                if p[3] == 0: grid.append(-1); continue
                if p not in index: index[p] = len(pal); pal.append(p)
                grid.append(index[p])
            ways = []
            for mid, px in c['members']:
                cw = [None] * len(pal)
                for g, p in zip(grid, px):
                    if g >= 0: cw[g] = list(p)
                ways.append({'source': mid, 'palette': cw})
            if len(ways) > 1:
                material = [any(max(abs(a - b) for a, b in zip(w['palette'][j], ways[0]['palette'][j])) > 6 for w in ways)
                            for j in range(len(pal))]
            else:
                material = None
            r0 = recs[c['members'][0][0]]
            # FS tints only listed mask colours (whole sprite if none listed).
            # Bake only greyscale mask values (multiply is confirmed); non-grey
            # mask values use an additive overlay we have not verified -> keep author colour.
            tint_layers = None
            if r0['colourable']:
                layers = r0['flags'].get('colorMaskLayers') or []
                isgrey = lambda p: max(p[:3]) - min(p[:3]) <= 2
                if layers:
                    tint_layers = [[j for j, p in enumerate(pal) if list(p[:3]) in [list(v) for v in l['values']] and isgrey(p)]
                                   for l in layers]
                else:
                    tint_layers = [list(range(len(pal)))]   # no masks: FS tints the whole sprite
            cid = f"{r0['id'].split('__')[0]}__c{len(cons)}"
            for mid, _ in c['members']: cid_of[mid] = cid
            cons.append({'id': cid, 'author': author, 'pack': r0['pack'], 'names': [recs[m]['name'] for m, _ in c['members']],
                         'family': fam_of.get(r0['id']), 'frame': list(frame), 'head': r0.get('head') or {},
                         'colourable': r0['colourable'], 'flags': r0['flags'], 'missing': r0['missing'],
                         'grid': grid, 'colourways': ways, 'material': material, 'tintLayers': tint_layers,
                         'maskGroup': f'{author}|{frame}|{hash(_)}', 'patternOf': None})
        # constructions sharing a mask but not a colour structure: pattern variants
        if len(classes) > 1:
            first = cons[-len(classes)]['id']
            for c in cons[-len(classes) + 1:]: c['patternOf'] = first

    # ---- addons -----------------------------------------------------------
    addons = []
    for v in variants:
        if v['type'] != 'ADDON': continue
        a, b = img(v['base']).get_flattened_data(), img(v['with']).get_flattened_data()
        w, h = recs[v['with']]['frame']
        pix = [[k % (4 * w), k // (4 * w), list(pb)] for k, (pa, pb) in enumerate(zip(a, b)) if pb[3] and pa != pb]
        views = sorted({['front', 'right', 'left', 'back'][x // w] for x, _, _ in pix})
        addons.append({'id': f"addon_{len(addons)}", 'author': v['author'], 'base': cid_of[v['base']],
                       'example': cid_of[v['with']], 'from': recs[v['with']]['name'], 'pixels': pix,
                       'views': views, 'frame': [w, h]})

    lib = {'schema': 'pack_study-hat-library/v0', 'styles': styles, 'constructions': cons, 'addons': addons}
    json.dump(lib, open(D('library.json'), 'w'))
    print('constructions', len(cons), '| recolourable (>=2 proven colourways)', sum(c['material'] is not None for c in cons),
          '| greyscale-colourable', sum(c['colourable'] for c in cons), '| pattern variants', sum(bool(c['patternOf']) for c in cons),
          '| addons', len(addons))
    for a, s in sorted(styles.items(), key=lambda kv: kv[1]['edgeToInnerL']):
        print(f"  {a[:24]:24s} {s['outline']:14s} ratio={s['edgeToInnerL']:.2f} grey={s['greyscaleAuthored']} n={s['n']}")

if __name__ == '__main__':
    main()
