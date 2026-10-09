"""PROPOSE crown / brim / band splits for brimmed hats, per view.  Proposal only:
labels are not promoted until the user confirms them on the contact sheet (CLAUDE.md s3).

junction row  = the first row (from the top) where opaque width jumps the most,
                searched in the upper 75% of the bbox -> crown above, brim at/below.
band pixels   = pixels within 2 rows of the junction whose hue is far from the
                hat's dominant (material) hue, or that are FS tint-mask pixels.
Writes data/brimmed_splits.json and out/brimmed_split_proposal.png
(original | crown=red-ish overlay, brim=blue overlay, band=yellow).
"""
import colorsys, json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDS = [l.strip() for l in open(os.path.join(HERE, 'data', 'straw_family.txt')) if l.strip()]

def hue(p):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3])); return h * 360, s, v

def split_view(f):
    w, h = f.size; px = f.load()
    rows = [[x for x in range(w) if px[x, y][3]] for y in range(h)]
    ys = [y for y in range(h) if rows[y]]
    if not ys: return None
    y0, y1 = ys[0], ys[-1]
    width = lambda y: (max(rows[y]) - min(rows[y]) + 1) if rows[y] else 0
    lim = y0 + max(1, int((y1 - y0) * 0.75))
    jumps = [(width(y) - width(y - 1), y) for y in range(y0 + 1, lim + 1)]
    best = max(jumps) if jumps else (0, y0)
    return {'junction': best[1], 'jump': best[0], 'top': y0, 'bottom': y1}

def main():
    recs = {r['id']: r for r in json.load(open(os.path.join(HERE, 'data', 'hats.json')))}
    out, S = {}, 5
    canvas = Image.new('RGBA', (2 * (4 * 20 * S + 20) + 10, len(IDS) * (25 * S + 16)), (118, 128, 112, 255))
    d = ImageDraw.Draw(canvas)
    for k, i in enumerate(IDS):
        r = recs[i]; w, h = r['frame']
        strip = Image.open(os.path.join(HERE, 'data', 'hats', i + '.png')).convert('RGBA')
        # dominant material hue = most common chromatic colour
        from collections import Counter
        cnt = Counter(p[:3] for p in strip.get_flattened_data() if p[3] and hue(p)[1] > 0.15)
        dom = hue(cnt.most_common(1)[0][0])[0] if cnt else None
        masks = [tuple(v) for l in r['flags'].get('colorMaskLayers', []) for v in l['values']]
        views = {}
        over = strip.copy(); op = over.load()
        for v, name in enumerate(['front', 'right', 'left', 'back']):
            f = strip.crop((v * w, 0, v * w + w, h)); sv = split_view(f)
            if not sv: continue
            j = sv['junction']; band = []
            for y in range(h):
                for x in range(w):
                    p = f.getpixel((x, y))
                    if not p[3]: continue
                    hh, ss, vv = hue(p)
                    far = dom is not None and ss > 0.25 and min(abs(hh - dom), 360 - abs(hh - dom)) > 35
                    is_band = abs(y - j) <= 2 and (far or (p[:3] in masks and r['colourable'] and max(p[:3]) - min(p[:3]) <= 2))
                    if is_band: band.append([x, y])
                    tint = (255, 230, 0) if is_band else ((230, 70, 60) if y < j else (60, 110, 230))
                    q = op[v * w + x, y]
                    op[v * w + x, y] = tuple((q[c] + tint[c]) // 2 for c in range(3)) + (255,)
            sv['band'] = band; views[name] = sv
        out[i] = views
        y = k * (25 * S + 16)
        d.text((2, y), f"{k}: {r['author']}: {r['name']}   junction rows F/R/L/B = " +
               '/'.join(str(views[n]['junction']) if n in views else '-' for n in ['front', 'right', 'left', 'back']), fill='white')
        for col, im in enumerate([strip, over]):
            canvas.alpha_composite(im.resize((im.width * S, im.height * S), Image.NEAREST), (col * (4 * 20 * S + 20), y + 12))
    json.dump(out, open(os.path.join(HERE, 'data', 'brimmed_splits.json'), 'w'), indent=1)
    canvas.save(os.path.join(HERE, 'out', 'brimmed_split_proposal.png'))
    print(len(out))

if __name__ == '__main__':
    main()
