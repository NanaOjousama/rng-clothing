"""Phase-5 pilot evaluation (pod, GPU; diffusers + numpy + PIL in /workspace/phase5/venv).

Generates with FIXED prompts and seeds, then judges the images two ways:
  * the images themselves -- comparison sheets (published to lora-reviews; the user judges these, not the numbers)
  * measurements on the decoded logical grid (context for the sheets, never a verdict on their own)
Prompts: 8 hat families x {front, fourview} x 4 seeds, captioned exactly like the training data (layout phrase
first); plus every per-family HOLDOUT caption (never trained) in both layouts, seed 101, vs its ground truth.
Decode: each image's own border median = background; cells (32 px front / 16 px four-view) sampled at their central
half; a cell is hat when its OKLab distance from the background exceeds KEY.  Nothing is resampled: the decoded
sprite IS the cell grid.  Metrics:
  empty      hat cells < 12 or > 75 % of the grid (decode failed / no hat / background lost)
  grid_dev   mean RGB std inside hat cells (0 = perfectly flat pixel-art cells)
  bg_purity  share of border pixels within BG_TOL of the background (clean removal)
  colours    distinct colours among hat cells after 16-level rounding
  holdout_iou  silhouette IoU vs the held-out truth (best of +-3 cell shifts, mirror allowed); four-view: mean of 4 views
  novelty    max front IoU vs all 291 training fronts (>= 0.93 = copy, 0.85-0.93 = close variant)
  lr_iou     four-view only: right view vs mirrored left view (consistency of the side views)
  views_ok   four-view only: all four quadrants hold a hat
usage: python eval_phase5.py --tag B --lora /workspace/phase5/runs/pilot_B/sdvhat_p5_pilot_B.safetensors [--seeds 4] [--no-holdout]
       python eval_phase5.py --tag base            (no LoRA)
       python eval_phase5.py --sheets              (comparison sheets + summary over every tag already evaluated)"""
import argparse, glob, json, os
import numpy as np
from PIL import Image, ImageDraw

P = '/workspace/phase5'; DS = f'{P}/dataset/phase5_v1'; OUT = f'{P}/eval'
LAYOUT = {'front': ('front view, single sprite', '24x24 sprite', 32, 24),
          'fourview': ('four views, 2x2 sheet, front top-left, right top-right, left bottom-left, back bottom-right', '24x24 sprites', 16, 48)}
FAMILIES = [('beanie', 'beanie, red, dark red, white'),
            ('witch hat', 'witch hat, black, dark purple, light yellow'),
            ('straw sun hat', 'wide-brim hat, wide brim, straw hat, light yellow, orange, dark brown'),
            ('cap', 'cap, blue, dark blue, white'),
            ('cowboy hat', 'cowboy hat, wide brim, brown, dark brown, light orange'),
            ('beret', 'beret, dark green, green, black'),
            ('flower crown', 'flower crown, pink, light pink, green'),
            ('top hat', 'top hat, black, dark grey, red')]
SEEDS = [101, 102, 103, 104]
KEY, BG_TOL = 0.08, 0.06
STEPS, CFG = 30, 6.0


def prompt(desc, layout):
    ph, fr, _, _ = LAYOUT[layout]
    return f'sdvhat, {ph}, {desc}, pixel art, {fr}, dark outline'


def oklab(rgb):
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    l = 0.4122214708 * c[..., 0] + 0.5363325363 * c[..., 1] + 0.0514459929 * c[..., 2]
    m = 0.2119034982 * c[..., 0] + 0.6806995451 * c[..., 1] + 0.1073969566 * c[..., 2]
    s = 0.0883024619 * c[..., 0] + 0.2817188376 * c[..., 1] + 0.6299787005 * c[..., 2]
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1)


def decode(img, layout, exact_bg=None):
    """-> cell colours (g,g,3) uint8, hat mask (g,g) bool, metrics.  exact_bg: training/holdout truth (exact key)."""
    _, _, cell, g = LAYOUT[layout]; a = np.asarray(img.convert('RGB'))
    border = np.concatenate([a[:4].reshape(-1, 3), a[-4:].reshape(-1, 3), a[:, :4].reshape(-1, 3), a[:, -4:].reshape(-1, 3)])
    bg = np.array(exact_bg, dtype=np.uint8) if exact_bg is not None else np.median(border, 0).astype(np.uint8)
    blocks = a.reshape(g, cell, g, cell, 3).transpose(0, 2, 1, 3, 4)
    q = cell // 4
    cols = np.median(blocks[:, :, q:cell - q, q:cell - q].reshape(g, g, -1, 3), 2).astype(np.uint8)
    if exact_bg is not None: mask = np.any(cols != bg, -1)
    else: mask = np.linalg.norm(oklab(cols) - oklab(bg[None, None]), axis=-1) > KEY
    dev = blocks.reshape(g, g, -1, 3).astype(np.float64).std(2).mean(-1)
    purity = float((np.linalg.norm(oklab(border) - oklab(bg[None]), axis=-1) < BG_TOL).mean())
    n = int(mask.sum()); ncol = len({tuple(c) for c in (cols[mask] // 16)}) if n else 0
    return cols, mask, {'cells': n, 'empty': bool(n < 12 or n > 0.75 * g * g), 'grid_dev': round(float(dev[mask].mean()) if n else 0.0, 2),
                        'bg_purity': round(purity, 3), 'colours': ncol, 'bg': bg.tolist()}


def shift(m, dx, dy):
    o = np.zeros_like(m); h, w = m.shape
    o[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return o


def iou(a, b, mirror=True, r=3):
    best = 0.0
    for m in ([a, a[:, ::-1]] if mirror else [a]):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                s = shift(m, dx, dy); u = (s | b).sum()
                if u: best = max(best, (s & b).sum() / u)
    return float(best)


def quads(mask):
    return {'front': mask[:24, :24], 'right': mask[:24, 24:], 'left': mask[24:, :24], 'back': mask[24:, 24:]}


def train_fronts():
    man = json.load(open(f'{DS}/manifest.json')); out = []
    for it in man['items']:
        if it['split'] == 'train' and it['layout'] == 'front' and not it['augmented']:
            _, m, _ = decode(Image.open(f"{DS}/train/1_sdvhat/{it['file']}.png"), 'front', man['background']); out.append(m)
    return out, man


def novelty(front_mask, fronts):
    return max(iou(front_mask, t, r=2) for t in fronts) if front_mask.any() else 0.0


def generate(args):
    import torch
    from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
    base = open(f'{P}/base_model.txt').read().strip()
    pipe = StableDiffusionXLPipeline.from_single_file(base, torch_dtype=torch.float16).to('cuda')
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(pipe.scheduler.config)
    pipe.set_progress_bar_config(disable=True)
    if args.lora: pipe.load_lora_weights(os.path.dirname(args.lora), weight_name=os.path.basename(args.lora))
    fronts, man = train_fronts(); od = f'{OUT}/{args.tag}'; os.makedirs(od, exist_ok=True)
    jobs = [(f'fam__{fam.replace(" ", "_")}__{lay}', prompt(desc, lay), lay, SEEDS[:args.seeds], None)
            for fam, desc in FAMILIES for lay in LAYOUT]
    if not args.no_holdout:
        for it in man['items']:
            if it['split'] == 'holdout':
                jobs.append((f"hold__{it['file']}", it['caption'], it['layout'], [101], it))
    rows = []
    for name, pr, lay, seeds, truth in jobs:
        g = [torch.Generator('cuda').manual_seed(s) for s in seeds]
        ims = pipe(prompt=[pr] * len(seeds), generator=g, height=768, width=768, num_inference_steps=STEPS, guidance_scale=CFG).images
        for s, im in zip(seeds, ims):
            fn = f'{name}__s{s}.png'; im.save(f'{od}/{fn}')
            cols, mask, met = decode(im, lay)
            r = {'file': fn, 'job': name, 'layout': lay, 'seed': s, 'prompt': pr, **met}
            front = mask if lay == 'front' else quads(mask)['front']
            r['novelty'] = round(novelty(front, fronts), 3)
            if lay == 'fourview':
                q = quads(mask); r['views_ok'] = all(v.sum() >= 6 for v in q.values())
                r['lr_iou'] = round(iou(q['right'], q['left'][:, ::-1], mirror=False, r=2), 3)
            if truth is not None:
                _, tm, _ = decode(Image.open(f"{DS}/holdout/{truth['file']}.png"), lay, man['background'])
                r['family'] = truth['family']
                r['holdout_iou'] = round(iou(mask, tm), 3) if lay == 'front' else \
                    round(float(np.mean([iou(quads(mask)[v], quads(tm)[v]) for v in ('front', 'right', 'left', 'back')])), 3)
            rows.append(r)
        print(name, len(rows), flush=True)
    json.dump({'tag': args.tag, 'lora': args.lora, 'steps': STEPS, 'cfg': CFG, 'sampler': 'euler_a', 'rows': rows},
              open(f'{od}/metrics.json', 'w'), indent=1)


def summary(rows):
    def avg(k, rs): v = [r[k] for r in rs if k in r]; return round(float(np.mean(v)), 3) if v else None
    out = {}
    for lay in LAYOUT:
        fam = [r for r in rows if r['layout'] == lay and r['job'].startswith('fam__')]
        hold = [r for r in rows if r['layout'] == lay and r['job'].startswith('hold__')]
        allr = fam + hold
        out[lay] = {'n': len(allr), 'empty_rate': round(sum(r['empty'] for r in allr) / max(1, len(allr)), 3),
                    'holdout_iou': avg('holdout_iou', hold), 'novelty_mean': avg('novelty', fam),
                    'copies(>=0.93)': sum(r['novelty'] >= 0.93 for r in fam), 'grid_dev': avg('grid_dev', allr),
                    'bg_purity': avg('bg_purity', allr), 'colours': avg('colours', allr)}
        if lay == 'fourview':
            out[lay]['views_ok_rate'] = round(sum(r.get('views_ok', False) for r in allr) / max(1, len(allr)), 3)
            out[lay]['lr_iou'] = avg('lr_iou', allr)
    return out


def sheet(paths_by_row, col_titles, row_titles, title, fn, t=384):
    W, H = 160 + t * len(col_titles), 40 + (t + 6) * len(row_titles)
    im = Image.new('RGB', (W, H), (34, 34, 34)); d = ImageDraw.Draw(im); d.text((6, 6), title, fill=(255, 255, 255))
    for j, c in enumerate(col_titles): d.text((160 + j * t + 4, 24), c, fill=(255, 220, 120))
    for i, (rt, ps) in enumerate(zip(row_titles, paths_by_row)):
        y = 40 + i * (t + 6); d.text((6, y + t // 2), rt, fill=(230, 230, 230))
        for j, p in enumerate(ps):
            if p and os.path.exists(p): im.paste(Image.open(p).convert('RGB').resize((t, t), Image.NEAREST), (160 + j * t, y))
    im.save(fn)


def decoded_sheet(tag, lay, fn, z=6):
    """decoded sprites with the background REMOVED (transparent -> checker): shows what removal leaves."""
    g = LAYOUT[lay][3]; rows = []
    for fam, _ in FAMILIES:
        for s in SEEDS:
            p = f"{OUT}/{tag}/fam__{fam.replace(' ', '_')}__{lay}__s{s}.png"
            if os.path.exists(p): rows.append((fam, s, decode(Image.open(p), lay)))
    cols = 4; W = cols * (g * z + 8) + 8; H = ((len(rows) + cols - 1) // cols) * (g * z + 22) + 8
    im = Image.new('RGB', (W, H), (60, 60, 60)); d = ImageDraw.Draw(im)
    for k, (fam, s, (c, m, met)) in enumerate(rows):
        ox, oy = 8 + (k % cols) * (g * z + 8), 8 + (k // cols) * (g * z + 22)
        for y in range(g):
            for x in range(g):
                col = tuple(int(v) for v in c[y, x]) if m[y, x] else ((90, 90, 90) if (x + y) % 2 else (120, 120, 120))
                d.rectangle([ox + x * z, oy + y * z, ox + x * z + z - 1, oy + y * z + z - 1], fill=col)
        d.text((ox, oy + g * z + 2), f'{fam} s{s}', fill=(255, 255, 255))
    im.save(fn)


def sheets():
    tags = sorted(t for t in os.listdir(OUT) if os.path.exists(f'{OUT}/{t}/metrics.json'))
    order = [t for t in ('base', 'prev', 'A', 'B', 'C') if t in tags] + [t for t in tags if t not in ('base', 'prev', 'A', 'B', 'C')]
    sd = f'{OUT}/sheets'; os.makedirs(sd, exist_ok=True); summ = {}
    for t in order: summ[t] = summary(json.load(open(f'{OUT}/{t}/metrics.json'))['rows'])
    json.dump(summ, open(f'{sd}/summary.json', 'w'), indent=1)
    for lay in LAYOUT:
        rows = [[f"{OUT}/{t}/fam__{fam.replace(' ', '_')}__{lay}__s101.png" for t in order] for fam, _ in FAMILIES]
        sheet(rows, order, [f for f, _ in FAMILIES], f'phase-5 pilot, {lay}, seed 101, columns = checkpoints', f'{sd}/compare_{lay}_s101.png')
        for t in order:
            if t == 'base': continue
            rows = [[f"{OUT}/{t}/fam__{fam.replace(' ', '_')}__{lay}__s{s}.png" for s in SEEDS] for fam, _ in FAMILIES]
            sheet(rows, [f's{s}' for s in SEEDS], [f for f, _ in FAMILIES], f'arm {t}, {lay}, 4 seeds (variety)', f'{sd}/{t}_{lay}_seeds.png', t=256)
            decoded_sheet(t, lay, f'{sd}/{t}_{lay}_decoded_bg_removed.png')
            hold = sorted(glob.glob(f'{OUT}/{t}/hold__*__{lay}__s101.png'))[:16]
            if hold:
                man = {i['file']: i for i in json.load(open(f'{DS}/manifest.json'))['items']}
                stem = lambda h: os.path.basename(h)[len('hold__'):-len('__s101.png')]
                truth = [f"{DS}/holdout/{stem(h)}.png" for h in hold]
                sheet([[tr, h] for tr, h in zip(truth, hold)], ['held-out truth (never trained)', f'arm {t} from its caption'],
                      [man.get(stem(h), {}).get('family', '?') for h in hold], f'arm {t}, {lay}, holdout', f'{sd}/{t}_{lay}_holdout.png', t=256)
    lines = ['| checkpoint | layout | empty | holdout IoU | novelty | copies | grid dev | bg purity | colours | views ok | L/R IoU |', '|' + '---|' * 11]
    for t in order:
        for lay in LAYOUT:
            s = summ[t][lay]
            lines.append(f"| {t} | {lay} | {s['empty_rate']} | {s['holdout_iou']} | {s['novelty_mean']} | {s['copies(>=0.93)']} | {s['grid_dev']} | "
                         f"{s['bg_purity']} | {s['colours']} | {s.get('views_ok_rate', '')} | {s.get('lr_iou', '')} |")
    open(f'{sd}/SUMMARY.md', 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--tag'); ap.add_argument('--lora'); ap.add_argument('--seeds', type=int, default=4)
    ap.add_argument('--no-holdout', action='store_true'); ap.add_argument('--sheets', action='store_true'); a = ap.parse_args()
    sheets() if a.sheets else generate(a)
