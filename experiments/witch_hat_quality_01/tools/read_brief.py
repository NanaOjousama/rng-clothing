"""Read an SDXL witch-hat render as a DESIGN BRIEF for forge.py (GPU host; PIL + numpy).
Only the AI's design choices are taken; the sprite is drawn by forge.py on the native grid.

  cut-out     extract_v2 (border-grown background, largest blob, holes filled)
  brim/crown  brim = rows at >= 70% of the widest row; crown = rows above the first such row
  colours     region medians over mid-luminance pixels (outline and highlights excluded):
              crown, band (bottom 18% of the crown, if it differs), brim, rim (outer ring, if it differs)
  accent      crown/band pixels far from both crown and band colours; their median = accent;
              connected blobs -> a buckle (blob on the band near the centre) and charms (on the crown)
  lean        tip centre (top 15% of crown rows) vs base centre -> side (bend_yaw +-135) and amount;
              hook = how much the top 10% bends further than the top 30% -> crook
  proportion  crown height / brim width -> H; crown base width / brim width -> r0
  words       the prompt picks the charm shape (moon / star / patch / dot) and brim character
              (wavy / floppy / upturned): they are the AI brief's own words
usage: python read_brief.py <run_dir>  -> <run_dir>/designs.json (forge input) + brief_debug.png"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import extract_v2 as X


def med(a, m):
    px = a[m]
    if len(px) < 8: return None
    L = px.mean(1); lo, hi = np.percentile(L, 25), np.percentile(L, 90)
    sel = px[(L >= lo) & (L <= hi)]
    return [int(v) for v in np.median(sel if len(sel) else px, axis=0)]


def dist(c1, c2): return float(np.abs(np.array(c1) - np.array(c2)).sum()) if c1 and c2 else 0.0


def blobs(mask):
    H, W = mask.shape; seen = np.zeros_like(mask); out = []
    for y0, x0 in zip(*np.where(mask)):
        if seen[y0, x0]: continue
        st, comp = [(y0, x0)], []; seen[y0, x0] = True
        while st:
            y, x = st.pop(); comp.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; st.append((yy, xx))
        if len(comp) >= 60: out.append(np.array(comp))
    return out


def read(path, prompt):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.int32)
    m = X.fill_holes(X.largest_blob(~X.background(a)))
    if m.mean() < 0.02 or m.mean() > 0.75: return None, 'cut-out failed'
    widths = m.sum(1); maxw = widths.max(); rows = np.where(widths > 0)[0]
    brim_rows = np.where(widths >= 0.7 * maxw)[0]; yb = brim_rows.min(); ytop = rows.min(); ybot = rows.max()
    crown = m.copy(); crown[yb:] = False; brim = m.copy(); brim[:yb] = False
    ch = yb - ytop
    if ch < 20: return None, 'no crown found'
    band_m = crown.copy(); band_m[:yb - int(0.18 * ch)] = False
    body_m = crown.copy(); body_m[yb - int(0.18 * ch):] = False
    crown_c = med(a, body_m); band_c = med(a, band_m); brim_c = med(a, brim)
    if dist(band_c, crown_c) < 70: band_c = None
    # rim: brim pixels within 3% of the canvas of the brim's outer edge
    k = 20; inner = brim.copy()
    for dy, dx in ((k, 0), (-k, 0), (0, k), (0, -k)):
        inner &= np.roll(np.roll(brim, dy, 0), dx, 1)                 # erosion by k px (brim never touches the border)
    er = brim & ~inner
    rim_c = med(a, er)
    if dist(rim_c, brim_c) < 70: rim_c = None
    # accent: crown pixels far from crown and band colours, away from the outline (crown eroded 8 px),
    # with real colour (chroma) or a big lightness jump - not grey outline or highlight streaks
    core = crown.copy()
    for dy, dx in ((8, 0), (-8, 0), (0, 8), (0, -8)): core &= np.roll(np.roll(crown, dy, 0), dx, 1)
    far = (np.abs(a - np.array(crown_c)).sum(2) > 150) & ((np.abs(a - np.array(band_c)).sum(2) > 150) if band_c else True)
    chroma = a.max(2) - a.min(2)
    acc_m = core & far & (a.mean(2) > 40) & ((chroma > 60) | (np.abs(a.mean(2) - np.mean(crown_c)) > 110))
    acc_c = med(a, acc_m) if acc_m.sum() > 60 else None
    buckle, charms = None, []
    words = prompt.lower()
    shape = 'moon' if 'moon' in words else 'patch' if 'patch' in words else 'dot' if ('mushroom' in words or 'gem' in words) else 'star'
    xs_all = np.where(m.any(0))[0]; cx_brim = (xs_all.min() + xs_all.max()) / 2
    for b in blobs(acc_m) if acc_c else []:
        by, bx = b[:, 0].mean(), b[:, 1].mean()
        hf = (yb - by) / ch
        if hf < 0.22 and abs(bx - cx_brim) < 0.12 * maxw: buckle = 'square'; continue
        if hf > 0.72 or len(b) > 0.06 * crown.sum(): continue          # tip highlights / big shading areas are not charms
        if len(charms) < 3:
            row = np.where(crown[int(by)])[0]
            ang = 0.0 if len(row) < 2 else float(np.clip((bx - row.mean()) / (np.ptp(row) / 2 + 1e-6), -1, 1) * 70)
            charms.append({'h': round(float(np.clip(hf, 0.15, 0.8)), 2), 'angle': round(ang), 'shape': shape})
    # lean
    cen = {y: np.where(m[y])[0].mean() for y in range(ytop, yb)}
    base_x = np.mean([cen[y] for y in range(yb - max(2, ch // 6), yb)])
    tip_x = np.mean([cen[y] for y in range(ytop, ytop + max(2, ch // 7))])
    mid_x = np.mean([cen[y] for y in range(ytop + int(0.25 * ch), ytop + int(0.35 * ch) + 1)])
    lean = (tip_x - base_x) / maxw; hook = abs(tip_x - mid_x) / maxw
    dev = max((cen[y] - base_x for y in range(ytop, ytop + int(0.4 * ch) + 1)), key=abs)
    if abs(dev) / maxw > abs(lean): lean = dev / maxw                  # the hook's furthest point, not just the tip centre
    # pom-pom: a light round blob at the very tip
    tip_rows = crown.copy(); tip_rows[ytop + max(3, ch // 8):] = False
    tip_c = med(a, tip_rows)
    pom = tip_c if (tip_c and np.mean(tip_c) > np.mean(crown_c) + 60 and dist(tip_c, crown_c) > 150) else None
    side = 135 if lean > 0 else -135
    base_w = widths[yb - max(2, ch // 6):yb].mean()
    d = {'name': os.path.basename(path)[:-4], 'source_render': os.path.basename(path), 'tag': 'AI-ORIGINAL',
         'base': crown_c, 'band': band_c or [int(c * 0.45) for c in crown_c], 'brim_col': brim_c if dist(brim_c, crown_c) > 90 else None,
         'rim': rim_c, 'accent': acc_c or [235, 205, 120], 'buckle': buckle, 'charms': charms,
         'bend_yaw': side, 'bend': round(float(np.clip(abs(lean) * 16, 1.4, 3.6)), 2), 'crook': round(float(np.clip(hook * 12, 0.5, 1.8)), 2),
         'H': round(float(np.clip(ch / maxw * 16, 8.0, 12.0)), 2), 'r0': round(float(np.clip(base_w / maxw * 7.6, 2.5, 3.6)), 2),
         'wave': 0.06 if ('wavy' in words or 'ragged' in words) else 0.0, 'droop': 1.0 if 'floppy' in words else 0.3,
         'curl': 0.7 if ('upturned' in words or 'curled brim' in words) else 0.0, 'tip_pom': pom}
    dbg = {'crown_px': int(crown.sum()), 'brim_row': int(yb), 'crown_h': int(ch), 'lean': round(float(lean), 3), 'hook': round(float(hook), 3)}
    return d, dbg


def main():
    run = sys.argv[1]; idx = json.load(open(os.path.join(run, 'briefs_index.json')))
    out, log = [], {}
    for k, meta in idx.items():
        d, info = read(os.path.join(run, k + '.png'), meta['prompt'])
        log[k] = info
        if d: d['prompt'] = meta['prompt']; d['seed'] = meta['seed']; out.append(d)
        print(k, info if not d else 'ok', flush=True)
    json.dump(out, open(os.path.join(run, 'designs.json'), 'w'), indent=1)
    json.dump(log, open(os.path.join(run, 'brief_log.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
