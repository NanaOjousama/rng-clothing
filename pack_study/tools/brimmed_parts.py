"""Brimmed-hat parts: crown above / brim at-and-below a per-view junction row.

Widths are measured on MATERIAL pixels only (decorations and bands -- chromatic
pixels far from the dominant hue -- are ignored), so a sunflower on the crown
does not move the junction.  Hats whose side-view brim is tilted (Coii straw,
boater) are not row-splittable and are listed in EXCLUDE.
Writes data/brimmed_parts.json: per hat, per view: junction, crown pixels, brim
pixels, crown base centre/width (row junction-1) and seat centre/width (brim
material row at the junction).
"""
import colorsys, json, os
from collections import Counter
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = [l.strip() for l in open(os.path.join(HERE, 'data', 'straw_family.txt')) if l.strip()]
EXCLUDE = {'coii__female_4__65feb3': 'side-view brim tilted', 'plurffle__boater_hat__a34628': 'side-view brim tilted',
           'kailey__straw_hat_sunflower__94b36c': 'sunflower shares straw hue; junction lands on the flower',
           'kailey__straw_hat_colourable_2__eceb78': 'same drawing as Straw Hat (Blue), mask-tinted copy'}
VIEWS = ['front', 'right', 'left', 'back']

def hsv(p): return colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))

def main():
    recs = {r['id']: r for r in json.load(open(os.path.join(HERE, 'data', 'hats.json')))}
    out = {}
    for i in IDS:
        if i in EXCLUDE: continue
        r = recs[i]; w, h = r['frame']
        strip = Image.open(os.path.join(HERE, 'data', 'hats', i + '.png')).convert('RGBA')
        cnt = Counter(p[:3] for p in strip.get_flattened_data() if p[3] and hsv(p)[1] > 0.15)
        dom = hsv(cnt.most_common(1)[0][0])[0] * 360 if cnt else None
        def material(p):
            if not p[3]: return False
            hh, ss, _ = hsv(p)
            return dom is None or ss <= 0.25 or min(abs(hh * 360 - dom), 360 - abs(hh * 360 - dom)) <= 35
        views = {}
        for v, name in enumerate(VIEWS):
            f = strip.crop((v * w, 0, v * w + w, h)); px = f.load()
            rows = [[x for x in range(w) if material(px[x, y])] for y in range(h)]
            ys = [y for y in range(h) if rows[y]]
            y0, y1 = ys[0], ys[-1]
            wid = lambda y: (max(rows[y]) - min(rows[y]) + 1) if rows[y] else 0
            cen = lambda y: (max(rows[y]) + min(rows[y])) / 2 if rows[y] else w / 2
            lim = y0 + max(1, int((y1 - y0) * 0.75))
            jump, j = max((wid(y) - wid(y - 1), y) for y in range(y0 + 1, lim + 1))
            allpx = [[x, y, list(px[x, y])] for y in range(h) for x in range(w) if px[x, y][3]]
            views[name] = {'junction': j, 'jump': jump,
                           'crown': [p for p in allpx if p[1] < j], 'brim': [p for p in allpx if p[1] >= j],
                           'crownBase': [cen(j - 1), wid(j - 1)], 'seat': [cen(j - 1), wid(j - 1)]}
        masks = [list(v) for l in r['flags'].get('colorMaskLayers', []) for v in l['values']]
        out[i] = {'maskValues': masks, 'author': r['author'], 'name': r['name'], 'frame': [w, h], 'head': r.get('head') or {}, 'views': views}
    json.dump({'excluded': EXCLUDE, 'hats': out}, open(os.path.join(HERE, 'data', 'brimmed_parts.json'), 'w'))
    for i, o in out.items():
        print(f"{o['author'][:12]:12s} {o['name'][:28]:28s} " + ' '.join(f"{n[0]}:j{o['views'][n]['junction']} base{o['views'][n]['crownBase'][1]}" for n in VIEWS))

if __name__ == '__main__':
    main()
