"""Why do our witch hats look muddy?  Measure well-made pointed hats vs ours, same metrics.
Analysis tool (.venv: PIL + numpy).  Benchmarks are MEASURED and SHOWN, never copied.

Per sprite (each of the 4 views, then averaged):
  opaque      opaque pixel count; bbox w x h
  colours     distinct opaque colours
  ramps       colours grouped into hue families (OKLCh: chroma<0.04 = neutral family; else hue
              within 30 deg); steps = colours per family; longest ramp
  value_span  OKLab L range over opaque pixels (contrast budget)
  noise       share of interior pixels whose 4 neighbours all have a different colour
              (speckle - dithering or extraction noise)
  outline     share of silhouette-edge pixels that are the darkest colour of their family;
              outline L; mean hue shift edge vs adjacent interior (coloured vs black outline)
  light       interior L: left-right and top-bottom difference (consistent light direction?)
  hue_shift   in the main ramp: hue difference between darkest and lightest step (degrees)
-> out/benchmark.json, out/benchmark_sheet.png (x6 and game-scale x4)"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = '/run/media/deck/USD00/RNG_clothing'
sys.path.insert(0, os.path.join(ROOT, 'pack_study', 'gen')); sys.path.insert(0, os.path.join(ROOT, 'pack_study', 'tools'))
from colour import to_lch
import vanilla as VAN
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPH = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def from_library(cid, way=0):
    L = json.load(open(os.path.join(ROOT, 'pack_study', 'data', 'library.json')))
    c = next(x for x in L['constructions'] if x['id'] == cid); pal = c['colourways'][way]['palette']
    a = np.zeros((20, 80, 4), np.int16)
    for k, g in enumerate(c['grid']):
        if g >= 0: a[k // 80, k % 80] = pal[g]
    return a


def from_sheet(path, key):
    h = json.load(open(path))[key]; a = np.zeros((20, 80, 4), np.int16)
    for i, ch in enumerate(h['idx']):
        if ch != '.': a[i // 80, i % 80] = h['pal'][ALPH.index(ch)] + [255]
    return a


def families(cols):
    lch = {c: to_lch(c) for c in cols}; fam = []
    for c in sorted(cols, key=lambda c: -lch[c][1]):
        L, C, H = lch[c]
        for f in fam:
            L2, C2, H2 = lch[f[0]]
            if (C < 0.04 and C2 < 0.04) or (C >= 0.04 and C2 >= 0.04 and min(abs(H - H2), 360 - abs(H - H2)) <= 30):
                f.append(c); break
        else: fam.append([c])
    return fam, lch


def view_metrics(v):
    op = v[..., 3] > 0
    if not op.any(): return None
    ys, xs = np.where(op); cols = {tuple(int(t) for t in v[y, x, :3]) for y, x in zip(ys, xs)}
    fam, lch = families(cols); famof = {c: i for i, f in enumerate(fam) for c in f}
    Ls = np.array([lch[tuple(int(t) for t in v[y, x, :3])][0] for y, x in zip(ys, xs)])
    H, W = op.shape
    def col(y, x): return tuple(int(t) for t in v[y, x, :3])
    def isedge(y, x): return any(not (0 <= y + dy < H and 0 <= x + dx < W and op[y + dy, x + dx]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    edge = [(y, x) for y, x in zip(ys, xs) if isedge(y, x)]; inner = [(y, x) for y, x in zip(ys, xs) if not isedge(y, x)]
    noise = sum(all(col(y, x) != col(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))) for y, x in inner) / max(1, len(inner))
    darkest = {i: min(f, key=lambda c: lch[c][0]) for i, f in enumerate(fam)}
    globdark = min(cols, key=lambda c: lch[c][0])
    out_dark = sum(col(y, x) in (darkest[famof[col(y, x)]], globdark) for y, x in edge) / max(1, len(edge))
    outL = float(np.mean([lch[col(y, x)][0] for y, x in edge])); inL = float(np.mean([lch[col(y, x)][0] for y, x in inner])) if inner else outL
    shifts = []
    for y, x in edge:
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (y + dy, x + dx)
            if q in set(inner):
                a, b = lch[col(y, x)], lch[col(*q)]
                if a[1] > 0.04 and b[1] > 0.04: shifts.append(min(abs(a[2] - b[2]), 360 - abs(a[2] - b[2])))
                break
    main = max(fam, key=lambda f: sum(1 for y, x in zip(ys, xs) if col(y, x) in f))
    hs = sorted(main, key=lambda c: lch[c][0])
    hue_shift = min(abs(lch[hs[0]][2] - lch[hs[-1]][2]), 360 - abs(lch[hs[0]][2] - lch[hs[-1]][2])) if len(hs) > 1 and lch[hs[0]][1] > 0.04 else 0
    inn = np.array(inner) if inner else np.zeros((0, 2), int)
    cx, cy = xs.mean(), ys.mean()
    lr = (np.mean([lch[col(y, x)][0] for y, x in inner if x < cx]) - np.mean([lch[col(y, x)][0] for y, x in inner if x > cx])) if len(inner) > 4 else 0
    tb = (np.mean([lch[col(y, x)][0] for y, x in inner if y < cy]) - np.mean([lch[col(y, x)][0] for y, x in inner if y > cy])) if len(inner) > 4 else 0
    return {'opaque': int(op.sum()), 'bbox': [int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)], 'colours': len(cols),
            'families': len(fam), 'longest_ramp': max(len(f) for f in fam), 'value_span': round(float(Ls.max() - Ls.min()), 3),
            'noise': round(noise, 3), 'outline_is_darkest': round(out_dark, 2), 'outline_L': round(outL, 3), 'inner_L': round(inL, 3),
            'edge_hue_shift': round(float(np.mean(shifts)), 1) if shifts else None, 'ramp_hue_shift': round(float(hue_shift), 1),
            'light_left_minus_right': round(float(lr), 3), 'light_top_minus_bottom': round(float(tb), 3)}


def main():
    van = VAN.load_vanilla()
    sets = [('BENCH vanilla Witch Hat', van[70]['arr']), ("BENCH vanilla Emily's Magic Hat", van[41]['arr']),
            ('BENCH vanilla Paper Hat', van[114]['arr']), ('BENCH lovisity Mage Hat', from_library('lovisity__c259')),
            ('BENCH lovisity Magician Hat', from_library('lovisity__c266')), ('BENCH Seyph elf cap', from_library('seyph__c310'))]
    AO = os.path.join(ROOT, 'experiments', 'ai_original_hats_01', 'out')
    for key, f in (('witch__C__s44', 'sheet_r4.json'), ('witch__C__s66', 'sheet_r4.json'), ('witch__s11', 'sheet_r2_rec.json'), ('witch__s33', 'sheet_r2_rec.json')):
        sets.append(('OURS ' + key, from_sheet(os.path.join(AO, f), key)))
    res = {}
    for name, a in sets:
        vs = [view_metrics(a[:, i * 20:(i + 1) * 20]) for i in range(4)]
        res[name] = {'front': vs[0], 'views': vs}
    json.dump(res, open(os.path.join(HERE, 'out', 'benchmark.json'), 'w'), indent=1)
    keys = ['bbox', 'colours', 'families', 'longest_ramp', 'value_span', 'noise', 'outline_is_darkest', 'outline_L', 'inner_L',
            'edge_hue_shift', 'ramp_hue_shift', 'light_left_minus_right', 'light_top_minus_bottom']
    print('FRONT VIEW'.ljust(34) + ' '.join(k[:9].rjust(9) for k in keys))
    for n, r in res.items():
        print(n[:34].ljust(34) + ' '.join(str(r['front'][k])[:9].rjust(9) for k in keys))
    S, G = 6, 4; rowh = 20 * S + 14
    img = Image.new('RGB', (300 + 4 * (20 * S + 8) + 20 + 4 * (20 * G + 4), rowh * len(sets) + 10), (160, 160, 160)); d = ImageDraw.Draw(img)
    for r, (name, a) in enumerate(sets):
        y0 = 6 + r * rowh; d.text((4, y0 + 50), name, fill=(0, 0, 0))
        im = Image.fromarray(a.astype(np.uint8), 'RGBA')
        for v in range(4):
            big = im.crop((v * 20, 0, v * 20 + 20, 20)).resize((20 * S, 20 * S), Image.NEAREST); img.paste(big, (300 + v * (20 * S + 8), y0), big)
            sm = im.crop((v * 20, 0, v * 20 + 20, 20)).resize((20 * G, 20 * G), Image.NEAREST)
            x = 300 + 4 * (20 * S + 8) + 20 + v * (20 * G + 4); img.paste((96, 128, 72), (x, y0, x + 20 * G, y0 + 20 * G)); img.paste(sm, (x, y0), sm)
    img.save(os.path.join(HERE, 'out', 'benchmark_sheet.png'))


if __name__ == '__main__':
    main()
