"""Witch-hat silhouette measurements (analysis only, REFERENCE study).  Input: 20x80 strip, views top->bottom
Front|Right|Left|Back (FS StartingPosition order), RGBA, or RGB with a flat background (corner colour).
Per view: brim row (widest opaque row), brim width, crown height (rows above the brim), and the crown spine:
  base_x  centre of the crown just above the brim
  low     lean over the LOWER half of the crown, px per row (+ = toward image right)  -> 'italic' if large
  top     x offset of the topmost crown pixel from base_x                             -> the bend/flop
  fold    tip turns back toward the centre in the top rows (x of top row closer to base than the max excursion)
usage: python witch_shape.py <label=png> ...   (prints one line per view)"""
import sys
from PIL import Image


def mask(img, y0):
    im = img.convert('RGBA'); px = im.load(); W = im.size[0]
    bg = px[0, y0] if im.mode == 'RGBA' and px[0, y0][3] == 255 else None
    if bg is None or px[0, y0][3] < 255: return [[px[x, y0 + y][3] > 0 for x in range(W)] for y in range(20)]
    return [[px[x, y0 + y][:3] != bg[:3] for x in range(W)] for y in range(20)]


def measure(M):
    rows = [[x for x, v in enumerate(r) if v] for r in M]; occ = [y for y, r in enumerate(rows) if r]
    if not occ: return None
    widths = [(max(r) - min(r) + 1) if r else 0 for r in rows]; brim = max(range(20), key=lambda y: (widths[y], y))
    crown = [y for y in occ if y < brim]
    # crown spine: centre of each row, but only rows clearly narrower than the brim (exclude brim slope)
    cw = [y for y in crown if widths[y] <= widths[brim] - 4]
    if len(cw) < 3: return dict(brim=brim, brim_w=widths[brim], crown_h=len(crown))
    cen = {y: (min(rows[y]) + max(rows[y])) / 2 for y in cw}; base = max(cw); topy = min(cw); h = base - topy
    mid = base - h // 2; low = (cen[mid] - cen[base]) / max(1, base - mid)
    exc = max(cw, key=lambda y: abs(cen[y] - cen[base])); top = cen[topy] - cen[base]
    fold = abs(cen[topy] - cen[base]) < abs(cen[exc] - cen[base]) - 0.5 and exc != topy
    return dict(brim=brim, brim_w=widths[brim], crown_h=base - topy + 1, top_y=min(occ), low=round(low, 2),
                top=round(top, 1), max_ex=round(cen[exc] - cen[base], 1), fold=fold, base_w=widths[base])


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        lab, p = arg.split('=', 1); img = Image.open(p)
        for i, v in enumerate(('F', 'R', 'L', 'B')):
            print(lab, v, measure(mask(img, 20 * i)))
