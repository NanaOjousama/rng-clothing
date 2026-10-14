"""Phase-4 FRONT-LoRA evaluation (GPU host, INFERENCE ONLY).  Prepared 2026-10-14, not run.
Same prompts, seeds and sampler for:
  p1      phase-1 front LoRA (runs/phase1_front_512/sdvhat_phase1_front_512.safetensors; 20x20, 24-px blocks)
  p4 eNN  every phase-4 front checkpoint (24x24, 20-px cells); best = lowest holdout-caption loss proxy:
          mean hat_iou on the holdout captions (seed 7), then seeds 8 9
Prompts (phase4_eval_jobs.json): 4 witch families x 3 decorations x colours + 6 general-hat prompts, and up to
15 holdout captions (12 general + the 3 witch references) -> hat_iou against the real front.
Per render: grid_dev (0 = block-exact), colours, cells, novelty = max silhouette IoU with any TRAIN front of that
model's own dataset (high = copying), witch_novelty = same vs the witch training fronts only.
Metrics are advisory; the sheets are for the eye (x1 / x4 / x10).
usage: python eval_front_phase4.py <p4_front_run_dir> <p1_lora> <out_dir>"""
import glob, json, os, re, sys
import numpy as np, torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
R = r'C:\Users\Chris\sdxl_lora_research'
MODEL = r'C:\Users\Chris\stardew-lora-lab\models\sdxl\sd_xl_base_1.0.safetensors'
D4 = os.path.join(R, 'dataset', 'phase4_front_512'); D1 = os.path.join(R, 'dataset', 'phase1_front_512')
NEG = 'photo, realistic, 3d render, blurry, gradient, text, watermark, person, face, multiple objects, pattern'
BG_TOL, STEPS, CFG = 40, 28, 7.0


def layout(M):
    if 'frame' in M: return M['frame'], M['cell'], M['margin']                  # phase 4
    return 20, M['block'], M['offset']                                          # phase 1


def native(im, M):
    n, B, O = layout(M); a = np.asarray(im.convert('RGB')).astype(np.int32); bg = np.array(M['background']); cells, dev = {}, []
    for y in range(n):
        for x in range(n):
            blk = a[O + y * B:O + (y + 1) * B, O + x * B:O + (x + 1) * B].reshape(-1, 3)
            med = np.median(a[O + y * B + B // 4:O + y * B + 3 * B // 4, O + x * B + B // 4:O + x * B + 3 * B // 4].reshape(-1, 3), 0)
            dev.append(np.abs(blk - med).mean())
            if np.abs(med - bg).sum() > BG_TOL: cells[(x, y)] = tuple(int(v) for v in med)
    if n == 20: cells = {(x + 2, y + 4): c for (x, y), c in cells.items()}     # compare everything in the 24 window
    return cells, float(np.mean(dev))


def n_colours(cells):
    reps = []
    for c in cells.values():
        if all(sum(abs(a - b) for a, b in zip(c, r)) > 12 for r in reps): reps.append(c)
    return len(reps)


def iou(a, b): return len(a & b) / len(a | b) if a | b else 0.0


def train_fronts(Dd, M, witch_only=False):
    out = {}
    for it in M['items']:
        if it['split'] != 'train' or it.get('augmented') or (witch_only and not it.get('family')): continue
        sub = os.path.join('train', ('2_' if it.get('subset') == 'witch' else '1_') + M['trigger'])
        out[it['file']] = set(native(Image.open(os.path.join(Dd, sub, it['file'] + '.png')), M)[0])
    return out


def jobs_for(M, J, phase):
    tail = 'pixel art, 24x24 sprites, dark outline' if phase == 4 else 'pixel art, 20x20 sprite, dark outline'
    js = [('prompt', p['id'], f"{M['trigger']}, front view, {p['words']}, {p['colours']}, {tail}", p['family']) for p in J['front_prompts']]
    hold = [it for it in json.load(open(os.path.join(D4, 'manifest.json')))['items'] if it['split'] == 'holdout']
    hold = [h for h in hold if h.get('family')] + [h for h in hold if not h.get('family')][:12]
    for h in hold:
        cap = h['caption'] if phase == 4 else h['caption'].replace('24x24 sprites', '20x20 sprite')
        js.append(('holdout', h['file'], cap, h.get('family') or 'general'))
    return js


def run(lora, tag, M, phase, J, seeds, out, res, train_m, witch_m, hold_m):
    pipe = StableDiffusionXLPipeline.from_single_file(MODEL, torch_dtype=torch.float16, local_files_only=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(os.path.dirname(lora), weight_name=os.path.basename(lora)); pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
    od = os.path.join(out, 'renders', tag); os.makedirs(od, exist_ok=True)
    for kind, key, prompt, fam in jobs_for(M, J, phase):
        for s in seeds:
            k = f'{tag}|{kind}__{key}|{s}'
            if k in res: continue
            im = pipe(prompt=prompt, negative_prompt=NEG, width=M['canvas'], height=M['canvas'], guidance_scale=CFG,
                      num_inference_steps=STEPS, generator=torch.Generator('cpu').manual_seed(s)).images[0]
            im.save(os.path.join(od, f'{kind}__{key}__s{s}.png')); cells, grid = native(im, M); sil = set(cells)
            r = {'tag': tag, 'kind': kind, 'key': key, 'family': fam, 'seed': s, 'prompt': prompt, 'grid_dev': round(grid, 2),
                 'colours': n_colours(cells), 'cells': len(cells),
                 'novelty': round(max((iou(sil, m) for m in train_m.values()), default=0), 3),
                 'witch_novelty': round(max((iou(sil, m) for m in witch_m.values()), default=0), 3)}
            if kind == 'holdout': r['hat_iou'] = round(iou(sil, hold_m.get(key, set())), 3)
            res[k] = r; np.save(os.path.join(od, f'{kind}__{key}__s{s}.npy'), np.array([[*xy, *c] for xy, c in cells.items()]).reshape(-1, 5))
            json.dump(res, open(os.path.join(out, 'metrics.json'), 'w'), indent=1); print(tag, kind, key, s, r['grid_dev'], flush=True)
    del pipe; torch.cuda.empty_cache()


def sheet(res, out, tags, s):
    keys = sorted({(r['kind'], r['key'], r['family']) for r in res.values()}, key=lambda t: (t[0] != 'prompt', t[2], t[1]))
    T = 24 * s; G = 4; LW = 220; cols = [(t, sd) for t in tags for sd in (7, 8, 9)]
    W = LW + len(cols) * (T + G) + 40; H = 30 + len(keys) * (T + G)
    im = Image.new('RGB', (W, H), (34, 36, 44)); d = ImageDraw.Draw(im)
    for c, (t, sd) in enumerate(cols): d.text((LW + c * (T + G) + (20 if c >= 3 else 0), 4), f'{t} s{sd}', fill=(200, 200, 120))
    for rI, (kind, key, fam) in enumerate(keys):
        y = 26 + rI * (T + G); d.text((4, y), f'{fam} | {key}'[:34], fill=(225, 225, 225))
        for c, (t, sd) in enumerate(cols):
            p = os.path.join(out, 'renders', t, f'{kind}__{key}__s{sd}.npy')
            if not os.path.exists(p): continue
            t_ = Image.new('RGB', (24, 24), (118, 146, 96))
            for x, y_, r, g, b in np.load(p).reshape(-1, 5): t_.putpixel((int(x), int(y_)), (int(r), int(g), int(b)))
            im.paste(t_.resize((T, T), Image.NEAREST), (LW + c * (T + G) + (20 if c >= 3 else 0), y))
    im.save(os.path.join(out, f'front_compare_x{s}.png'))


def main():
    run4, p1, out = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
    J = json.load(open(os.path.join(R, 'dataset', 'phase4_eval_jobs.json')))
    M4 = json.load(open(os.path.join(D4, 'manifest.json'))); M1 = json.load(open(os.path.join(D1, 'manifest.json')))
    mp = os.path.join(out, 'metrics.json'); res = json.load(open(mp)) if os.path.exists(mp) else {}
    tr4, w4 = train_fronts(D4, M4), train_fronts(D4, M4, True); tr1 = train_fronts(D1, M1)
    hold = {it['file']: set(native(Image.open(os.path.join(D4, 'holdout', it['file'] + '.png')), M4)[0]) for it in M4['items'] if it['split'] == 'holdout'}
    run(p1, 'p1', M1, 1, J, [7, 8, 9], out, res, tr1, w4, hold)
    ck = {}
    for f in glob.glob(os.path.join(run4, '*.safetensors')):
        m = re.search(r'-(\d{6})\.safetensors$', f); ck[f'p4e{int(m.group(1)):02d}' if m else 'p4e10'] = f
    for t in sorted(ck): run(ck[t], t, M4, 4, J, [7], out, res, tr4, w4, hold)
    sc = {t: np.mean([r['hat_iou'] for r in res.values() if r['tag'] == t and r['kind'] == 'holdout' and r['seed'] == 7]) for t in ck}
    best = max(sc, key=sc.get); run(ck[best], best, M4, 4, J, [8, 9], out, res, tr4, w4, hold)
    summ = {}
    for t in ('p1', best):
        for fam in sorted({r['family'] for r in res.values()}):
            rs = [r for r in res.values() if r['tag'] == t and r['family'] == fam]
            summ[f'{t}|{fam}'] = {k: round(float(np.mean([r[k] for r in rs if k in r])), 3) for k in ('grid_dev', 'colours', 'cells', 'novelty', 'witch_novelty', 'hat_iou') if any(k in r for r in rs)}
    json.dump({'best_p4': best, 'holdout_iou_by_ckpt': {k: round(float(v), 3) for k, v in sc.items()}, 'by_family': summ}, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    for s in (1, 4, 10): sheet(res, out, ['p1', best], s)
    open(os.path.join(out, 'DONE'), 'w').write(best)


if __name__ == '__main__':
    main()
