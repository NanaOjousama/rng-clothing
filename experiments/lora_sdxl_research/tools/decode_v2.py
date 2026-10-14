"""Robust 20x20 decode of LoRA renders (GPU host or Deck, PIL + numpy).  Step-0 fix.

v1 (eval_lora / auto test): a cell is background if its centre median is within RGB-sum 40 of the
trained magenta.  The model's background drifts (magenta -> lavender), so v1 leaves pink/grey halos.
v2, on the 20x20 grid:
  1. cell colour = median of the cell's centre half
  2. 'background-like' = OKLab distance to the trained magenta < 0.22, OR in the magenta/lavender
     family (R and B both > 150 and G at least 45 below min(R, B))
  3. background = background-like cells 4-connected to the canvas border (flood), plus enclosed
     background-like pockets that are very close to the magenta (dist < 0.12)
A hat cell that is genuinely magenta/pink and touches the outside would be lost: such cells are
counted and reported (risk), not hidden.
usage: python decode_v2.py <manifest.json> <render_dir> [<render_dir> ...]
-> <render_dir>/decode_v2.json (per render: cells v1, cells v2, halo cells removed) + decode_v2_compare.png"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw


def lin(c): c = c / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def oklab(rgb):
    r, g, b = [lin(np.asarray(rgb, float)[..., i]) for i in range(3)]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1)


def cells(im, M):
    a = np.asarray(im.convert('RGB')).astype(np.int32); B, O = M['block'], M['offset']; out = np.zeros((20, 20, 3), int)
    for y in range(20):
        for x in range(20):
            out[y, x] = np.median(a[O + y * B + B // 4:O + y * B + 3 * B // 4, O + x * B + B // 4:O + x * B + 3 * B // 4].reshape(-1, 3), 0)
    return out


def decode_v1(C, bg): return np.abs(C - np.array(bg)).sum(2) > 40          # True = hat


def decode_v2(C, bg):
    d = np.linalg.norm(oklab(C) - oklab(np.array(bg)), axis=-1)
    fam = (C[..., 0] > 150) & (C[..., 2] > 150) & (C[..., 1] < np.minimum(C[..., 0], C[..., 2]) - 45)
    like = (d < 0.22) | fam
    bgm = np.zeros((20, 20), bool); st = [(y, x) for y in range(20) for x in (0, 19)] + [(y, x) for x in range(20) for y in (0, 19)]
    st = [p for p in st if like[p]]
    for p in st: bgm[p] = True
    while st:
        y, x = st.pop()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < 20 and 0 <= xx < 20 and like[yy, xx] and not bgm[yy, xx]: bgm[yy, xx] = True; st.append((yy, xx))
    bgm |= d < 0.12
    risk = int((fam & bgm & (d > 0.22)).sum())          # family-only background cells: could be pink hat cells
    return ~bgm, risk


def main():
    M = json.load(open(sys.argv[1])); bg = M['background']
    for rd in sys.argv[2:]:
        rows, res = [], {}
        for f in sorted(os.listdir(rd)):
            if not f.endswith('.png') or '__native' in f or f.startswith(('eval_sheet', 'decode_v2')): continue
            C = cells(Image.open(os.path.join(rd, f)), M)
            h1 = decode_v1(C, bg); h2, risk = decode_v2(C, bg)
            res[f] = {'cells_v1': int(h1.sum()), 'cells_v2': int(h2.sum()), 'halo_removed': int((h1 & ~h2).sum()), 'family_risk_cells': risk}
            rows.append((f, C, h1, h2))
        json.dump(res, open(os.path.join(rd, 'decode_v2.json'), 'w'), indent=1)
        S = 6; cw = 2 * (20 * S) + 30; ch = 20 * S + 16; cols = 4
        sheet = Image.new('RGB', (cols * cw, ((len(rows) + cols - 1) // cols) * ch), (150, 150, 150)); dr = ImageDraw.Draw(sheet)
        for i, (f, C, h1, h2) in enumerate(rows):
            x0, y0 = (i % cols) * cw, (i // cols) * ch
            for j, h in enumerate((h1, h2)):
                im = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
                for y in range(20):
                    for x in range(20):
                        if h[y, x]: im.putpixel((x, y), tuple(int(v) for v in C[y, x]) + (255,))
                big = im.resize((20 * S, 20 * S), Image.NEAREST); sheet.paste((96, 128, 72), (x0 + j * (20 * S + 10), y0 + 14, x0 + j * (20 * S + 10) + 20 * S, y0 + 14 + 20 * S))
                sheet.paste(big, (x0 + j * (20 * S + 10), y0 + 14), big)
            dr.text((x0 + 2, y0 + 1), f[:34] + ' v1|v2', fill=(0, 0, 0))
        sheet.save(os.path.join(rd, 'decode_v2_compare.png'))
        n = len(res); print(rd, 'renders', n, '| v1 halo cells removed (median)', np.median([r['halo_removed'] for r in res.values()]),
                            '| renders with halos fixed', sum(r['halo_removed'] > 0 for r in res.values()),
                            '| family-risk cells total', sum(r['family_risk_cells'] for r in res.values()))


if __name__ == '__main__':
    main()
