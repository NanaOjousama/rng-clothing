"""Phase-2 evaluation of the method-C clean-front LoRA.  INFERENCE ONLY: never trains.

Stage 1: every checkpoint in <run_dir>, seed 7, on
  - all 26 holdout sheets (front = the authored front; right/left/back compared with the authored views
    and with the rule prior, demo_condition.rough_from_front)
  - CUSTOM fronts: the best phase-1 LoRA fronts (flower crowns, animal hats, witch hats), decoded to the
    20x20 grid (decode_strict: no magenta-family rule, keeps pink flowers) and lightly palette-merged (OKLab < 0.035) so cell-median noise is not counted
    as extra colours.  These have no authored side views: only consistency metrics apply.
Stage 2: the best checkpoint (mean holdout silhouette IoU over right/left/back), seeds 8 and 9.

Front: the clean front latent is held at every step (same condition as training) and the exact front
pixels are pasted back after decoding.  'front_drift' reports how far the RAW decoded front strayed
before that paste (share of cells off by OKLab > 0.04).

Consistency metrics (per view, vs the given front; the same numbers on authored views are the reference):
  iou_auth        silhouette IoU vs authored view (holdout only); prior_iou = the rule prior's
  palette_adh     share of hat cells within OKLab 0.06 of some front colour
  new_colours     distinct colours (merged at 0.035) not near any front colour
  accent_recall   share of the front's small non-outline colours (< 8% of cells) found in the view;
                  a DECORATION PROXY only (colour carry-over), not a semantic claim (CLAUDE.md s3)
  dL / ramp       mean OKLab L difference, and L spread (p90-p10) ratio view/front (shading)
  outline         share of silhouette-boundary cells with L < 0.4
  dh / dw         bbox height / width difference in cells (dw only for the back)
  lr_mirror       IoU(left, mirrored right);  back_front = IoU(back, front or mirrored front, best)
Sheets (x1 = true pixels, x4 = in game at zoom 100%, x10 = enlarged) in <out_dir>/sheets.
usage: python eval_phase2.py <run_dir> <out_dir>"""
import gc, glob, json, os, re, sys, time
import numpy as np, torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode_v2 as D
import demo_condition as DC

R = r'C:\Users\Chris\sdxl_lora_research'
SUB = os.path.join(R, 'dataset', 'phase2_4view_512')
P1 = os.path.join(R, 'dataset', 'phase1_front_512', 'manifest.json')
EV1 = os.path.join(R, 'runs', 'eval', 'sdvhat_phase1_front_512')
STEPS, CFG = 30, 7.0
VIEWS = DC.VIEWS
BACKDROP = (118, 146, 96)

# best phase-1 LoRA fronts, picked by eye from runs/eval/sdvhat_phase1_front_512/eval_sheet.png
CUSTOM = [
    ('flower', 'holdout__plurffle__c80__w0__s7', 'plurffle__c80__w0'),
    ('flower', 'holdout__plurffle__c80__w0__s8', 'plurffle__c80__w0'),
    ('flower', 'holdout__kailey__c226__w0__s7', 'kailey__c226__w0'),
    ('flower', 'holdout__kailey__c226__w0__s9', 'kailey__c226__w0'),
    ('animal', 'holdout__seyph__c287__w0__s7', 'seyph__c287__w0'),
    ('animal', 'holdout__seyph__c287__w0__s9', 'seyph__c287__w0'),
    ('animal', 'holdout__lovisity__c263__w0__s7', 'lovisity__c263__w0'),
    ('animal', 'holdout__lovisity__c263__w0__s9', 'lovisity__c263__w0'),
    ('animal', 'concept__frog__s9', 'animal hat, frog bucket hat with two eyes on top, green, light green, white'),
    ('animal', 'concept__bee__s7', 'knit beanie, yellow and black striped beanie with two antennae, yellow, black'),
    ('witch', 'concept__witch__s7', 'wide brim, witch hat with a crescent moon buckle, dark purple, purple, yellow'),
    ('witch', 'concept__witch__s8', 'wide brim, witch hat with a crescent moon buckle, dark purple, purple, yellow'),
    ('witch', 'concept__witch__s9', 'wide brim, witch hat with a crescent moon buckle, dark purple, purple, yellow'),
]


def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)


# ---------------------------------------------------------------- grid helpers
def merge_palette(G, mask, thr=0.035):
    """greedy merge of near-identical cell colours (most frequent first)"""
    cols, cnt = np.unique(G[mask].reshape(-1, 3), axis=0, return_counts=True); reps = []
    out = G.copy()
    for c in cols[np.argsort(-cnt)]:
        lab = D.oklab(c[None])[0]
        rep = next((r for r in reps if np.linalg.norm(D.oklab(r[None])[0] - lab) < thr), None)
        if rep is None: reps.append(c); rep = c
        out[mask & (G == c).all(-1)] = rep
    return out


def hat(G, bg, F=None):
    """F None: an exact-key grid (authored view, given front, rule prior): hat = not the key colour.
    F given: a GENERATED view: decode_v2 (drifted background), but cells matching a front colour
    (OKLab < 0.05) and not near the key (> 0.08) are kept; decode_v2 alone eats pale-magenta flowers."""
    if F is None: return (G != np.array(bg)).any(-1)
    m = D.decode_v2(G, bg)[0]; mf = hat(F, bg)
    if mf.any():
        lab = D.oklab(G); near = np.linalg.norm(lab[..., None, :] - D.oklab(F[mf])[None, None], axis=-1).min(-1) < 0.05
        m |= near & (np.linalg.norm(lab - D.oklab(np.array(bg)), axis=-1) > 0.08)
    return m


def decode_strict(C, bg):
    """phase-1 renders -> front mask: background = cells within OKLab 0.12 of the key, flood-filled from the
    border, plus enclosed cells within 0.08.  No magenta-family rule (it removes pink flowers)."""
    d = np.linalg.norm(D.oklab(C) - D.oklab(np.array(bg)), axis=-1); like = d < 0.12; bgm = np.zeros((20, 20), bool)
    st = [(y, x) for y in range(20) for x in range(20) if (y in (0, 19) or x in (0, 19)) and like[y, x]]
    for p in st: bgm[p] = True
    while st:
        y, x = st.pop()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < 20 and 0 <= xx < 20 and like[yy, xx] and not bgm[yy, xx]: bgm[yy, xx] = True; st.append((yy, xx))
    return ~(bgm | (d < 0.08))


def bbox(m):
    ys, xs = np.where(m)
    return (0, 0) if not len(ys) else (ys.max() - ys.min() + 1, xs.max() - xs.min() + 1)


def boundary(m):
    p = np.pad(m, 1); inner = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m & ~inner


def view_metrics(V, F, bg, gen):
    mf, mv = hat(F, bg), hat(V, bg, F if gen else None); out = {}
    if not mv.any(): return {'empty': True}
    labF = D.oklab(F[mf]); labV = D.oklab(V[mv])
    dmin = np.linalg.norm(labV[:, None] - labF[None], axis=-1).min(1)
    out['palette_adh'] = round(float((dmin < 0.06).mean()), 3)
    vcols = np.unique(merge_palette(V, mv)[mv].reshape(-1, 3), axis=0)
    out['new_colours'] = int((np.linalg.norm(D.oklab(vcols)[:, None] - labF[None], axis=-1).min(1) >= 0.06).sum())
    fcols, fcnt = np.unique(F[mf].reshape(-1, 3), axis=0, return_counts=True)
    acc = [c for c, n in zip(fcols, fcnt) if n / mf.sum() < 0.08 and D.oklab(c[None])[0, 0] >= 0.4]
    if acc:
        hit = [np.linalg.norm(labV - D.oklab(c[None])[0], axis=-1).min() < 0.06 for c in acc]
        out['accent_recall'] = round(float(np.mean(hit)), 3)
    LF, LV = labF[:, 0], labV[:, 0]
    out['dL'] = round(float(LV.mean() - LF.mean()), 3)
    sf = np.percentile(LF, 90) - np.percentile(LF, 10)
    out['ramp'] = round(float((np.percentile(LV, 90) - np.percentile(LV, 10)) / max(sf, 1e-3)), 2)
    b = boundary(mv); out['outline'] = round(float((D.oklab(V[b])[:, 0] < 0.4).mean()), 3)
    (hf, wf), (hv, wv) = bbox(mf), bbox(mv); out['dh'] = int(hv - hf); out['_dw'] = int(wv - wf)
    return out


def sheet_metrics(Vs, bg, gen=True):
    """Vs: dict view -> 20x20 grid (front = given); gen: right/left/back are generated"""
    F = Vs['front']; m = {v: view_metrics(Vs[v], F, bg, gen) for v in VIEWS[1:]}
    m['back']['dw'] = m['back'].pop('_dw', 0)
    for v in ('right', 'left'): m[v].pop('_dw', None)
    mr, ml, mb = (hat(Vs[v], bg, F if gen else None) for v in ('right', 'left', 'back')); mf = hat(F, bg)
    m['lr_mirror'] = round(DC.iou(ml, mr[:, ::-1]), 3)
    m['back_front'] = round(max(DC.iou(mb, mf), DC.iou(mb, mf[:, ::-1])), 3)
    return m


# ---------------------------------------------------------------- rendering
def rgba(G, bg, F=None):
    m = hat(G, bg, F); a = np.zeros((20, 20, 4), np.uint8); a[..., :3] = G; a[..., 3] = m * 255
    return Image.fromarray(a, 'RGBA')


def tile(g, bg, s):
    """g: exact grid, or (generated grid, its front)"""
    G, F = g if isinstance(g, tuple) else (g, None)
    a = rgba(G, bg, F).resize((20 * s, 20 * s), Image.NEAREST); t = Image.new('RGB', (20 * s, 20 * s), BACKDROP); t.paste(a, (0, 0), a)
    return t


def make_sheet(rows, header, bg, s, path):
    """rows: [(label, [[group title, [grid or None, ...]], ...])]"""
    LW, GAP, TH = 300, max(2, s), 14
    groups0 = rows[0][1]; widths = [len(g[1]) * (20 * s + GAP) + 3 * GAP for g in groups0]
    W = LW + sum(widths); H = TH * 2 + len(rows) * (max(20 * s, TH) + GAP) + GAP
    im = Image.new('RGB', (W, H), (34, 36, 44)); d = ImageDraw.Draw(im)
    d.text((4, 2), header, fill=(240, 240, 240)); x = LW
    for (title, _), w in zip(groups0, widths): d.text((x, TH + 1), title, fill=(200, 200, 120)); x += w
    y = TH * 2
    for label, groups in rows:
        d.text((4, y + 1), label[:50], fill=(225, 225, 225)); x = LW
        for (_, grids), w in zip(groups, widths):
            for i, g in enumerate(grids):
                if g is not None: im.paste(tile(g, bg, s), (x + i * (20 * s + GAP), y))
            x += w
        y += max(20 * s, TH) + GAP
    im.save(path)


def three_scales(rows, header, bg, out, name):
    for s in (1, 4, 10): make_sheet(rows, f'{header}  |  x{s}' + ('  (true pixels)' if s == 1 else '  (in game, zoom 100%)' if s == 4 else '  (enlarged)'), bg, s, os.path.join(out, f'{name}_x{s}.png'))


# ---------------------------------------------------------------- generation
def build_jobs(M, M1):
    bg = M['background']; items = {i['file']: i for i in M['items']}; jobs = []
    for i in M['items']:
        if i['split'] != 'holdout': continue
        T = DC.read_views(Image.open(os.path.join(SUB, 'holdout', i['file'] + '.png')).convert('RGB'), M)
        jobs.append({'id': 'holdout__' + i['file'], 'group': 'holdout', 'caption': i['caption'], 'front': T['front'], 'truth': T})
    lay = f"{M['trigger']}, {M['layout_caption']}, "
    for group, src, cap in CUSTOM:
        C = D.cells(Image.open(os.path.join(EV1, src + '.png')), M1); mk = decode_strict(C, bg)
        F = merge_palette(C, mk); F[~mk] = bg
        caption = items[cap]['caption'] if cap in items else lay + cap + ', pixel art, 20x20 sprites, dark outline'
        jobs.append({'id': f'{group}__{src}', 'group': group, 'caption': caption, 'front': F, 'truth': None})
    return jobs


def load_pipe(lora):
    pipe = StableDiffusionXLPipeline.from_single_file(DC.MODEL, torch_dtype=torch.float16, local_files_only=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(os.path.dirname(lora), weight_name=os.path.basename(lora))
    return pipe


def encode_fronts(pipe, jobs, M):
    bg = M['background']; CAN = M['canvas']
    vae = pipe.vae.to('cuda', torch.float32); sf = vae.config.scaling_factor; lats = {}
    for j in jobs:
        init = np.zeros((CAN, CAN, 3), np.uint8); init[:] = bg; DC.paint(init, {'front': j['front']}, M)
        x = torch.from_numpy(init).permute(2, 0, 1)[None].float().cuda() / 127.5 - 1
        with torch.no_grad(): lats[j['id']] = (vae.encode(x).latent_dist.mean * sf).half().cpu()
    vae.to('cpu', torch.float16); torch.cuda.empty_cache(); pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
    return lats


def generate(pipe, j, lat0, seed, M, box):
    x0, y0, x1, y1 = box
    g = torch.Generator('cpu').manual_seed(seed); lat = torch.randn(lat0.shape, generator=g, dtype=torch.float16) * pipe.scheduler.init_noise_sigma
    lat[:, :, y0:y1, x0:x1] = lat0[:, :, y0:y1, x0:x1]

    def keep_front(p, i, t, kw):
        L = kw['latents']; L[:, :, y0:y1, x0:x1] = lat0[:, :, y0:y1, x0:x1].to(L.device, L.dtype); return {'latents': L}
    im = pipe(prompt=j['caption'], negative_prompt=DC.NEG, width=M['canvas'], height=M['canvas'], guidance_scale=CFG,
              num_inference_steps=STEPS, latents=lat, callback_on_step_end=keep_front,
              callback_on_step_end_tensor_inputs=['latents']).images[0]
    raw = DC.read_views(im, M)
    lab_d = np.linalg.norm(D.oklab(raw['front']) - D.oklab(j['front']), axis=-1)
    a = np.asarray(im).copy(); DC.paint(a, {'front': j['front']}, M); im = Image.fromarray(a)
    G = DC.read_views(im, M)
    assert (G['front'] == j['front']).all()
    return im, G, round(float((lab_d > 0.04).mean()), 3)


def run_ckpt(lora, tag, jobs, seeds, M, box, out, results):
    log('load', tag, os.path.basename(lora)); pipe = load_pipe(lora); lats = encode_fronts(pipe, jobs, M); bg = M['background']
    for seed in seeds:
        for j in jobs:
            key = f"{tag}|{seed}|{j['id']}"
            if key in results: continue
            t = time.time(); im, G, drift = generate(pipe, j, lats[j['id']], seed, M, box)
            os.makedirs(os.path.join(out, 'renders', tag), exist_ok=True)
            im.save(os.path.join(out, 'renders', tag, f"{j['id']}__s{seed}.png"))
            np.save(os.path.join(out, 'renders', tag, f"{j['id']}__s{seed}.npy"), np.stack([G[v] for v in VIEWS]))
            r = {'ckpt': tag, 'seed': seed, 'id': j['id'], 'group': j['group'], 'front_exact_after_paste': True,
                 'front_drift': drift, 'gen': sheet_metrics(G, bg)}
            if j['truth'] is not None:
                T = j['truth']; prior = DC.rough_from_front(T['front'], bg)
                for v in VIEWS[1:]:
                    r['gen'][v]['iou_auth'] = round(DC.iou(hat(G[v], bg, G['front']), hat(T[v], bg)), 3)
                    r['gen'][v]['prior_iou'] = round(DC.iou(hat(prior, bg), hat(T[v], bg)), 3)
            results[key] = r
            log(tag, seed, j['id'], f'{time.time() - t:.0f}s', json.dumps({v: r['gen'][v].get('iou_auth') for v in VIEWS[1:]}))
            json.dump(results, open(os.path.join(out, 'metrics.json'), 'w'), indent=1)
    del pipe; gc.collect(); torch.cuda.empty_cache()


# ---------------------------------------------------------------- summary
def mean(xs):
    xs = [x for x in xs if x is not None]; return round(float(np.mean(xs)), 3) if xs else None


def summarise(results, jobs, M, out, best):
    bg = M['background']; sh = os.path.join(out, 'sheets'); os.makedirs(sh, exist_ok=True)
    tags = sorted({r['ckpt'] for r in results.values()}, key=lambda t: int(t[1:]))
    load = lambda tag, jid, seed: np.load(os.path.join(out, 'renders', tag, f'{jid}__s{seed}.npy'))
    S = {'checkpoints': {}, 'best': best}
    ref = {}
    for j in jobs:
        if j['truth'] is not None: ref[j['id']] = sheet_metrics(j['truth'], bg, gen=False)
    for tag in tags:
        rs = [r for r in results.values() if r['ckpt'] == tag and r['seed'] == 7]
        s = {}
        for grp in ('holdout', 'custom'):
            g = [r for r in rs if (r['group'] == 'holdout') == (grp == 'holdout')]
            if not g: continue
            row = {'n': len(g), 'front_drift': mean([r['front_drift'] for r in g])}
            for k in ('iou_auth', 'prior_iou', 'palette_adh', 'new_colours', 'accent_recall', 'dL', 'ramp', 'outline', 'dh'):
                row[k] = {v: mean([r['gen'][v].get(k) for r in g]) for v in VIEWS[1:]}
            row['lr_mirror'] = mean([r['gen']['lr_mirror'] for r in g]); row['back_front'] = mean([r['gen']['back_front'] for r in g])
            s[grp] = row
        S['checkpoints'][tag] = s
    S['authored_reference'] = {k: {v: mean([m[v].get(k) for m in ref.values()]) for v in VIEWS[1:]}
                               for k in ('palette_adh', 'new_colours', 'accent_recall', 'dL', 'ramp', 'outline', 'dh')}
    S['authored_reference']['lr_mirror'] = mean([m['lr_mirror'] for m in ref.values()])
    S['authored_reference']['back_front'] = mean([m['back_front'] for m in ref.values()])
    # per-hat ranking for the custom fronts at the best checkpoint (all seeds)
    S['custom_best'] = sorted([{'id': r['id'], 'seed': r['seed'], 'palette_adh': mean([r['gen'][v]['palette_adh'] for v in VIEWS[1:] if 'palette_adh' in r['gen'][v]]),
                                'lr_mirror': r['gen']['lr_mirror'], 'back_front': r['gen']['back_front'], 'front_drift': r['front_drift']}
                               for r in results.values() if r['ckpt'] == best and r['group'] != 'holdout'], key=lambda d: -(d['palette_adh'] or 0))
    json.dump(S, open(os.path.join(out, 'summary.json'), 'w'), indent=1)

    # 1. holdout at best checkpoint: authored | rule prior | generated
    rows = []
    for j in jobs:
        if j['truth'] is None: continue
        T = j['truth']; P = DC.rough_from_front(T['front'], bg); Gs = load(best, j['id'], 7)
        r = results[f"{best}|7|{j['id']}"]['gen']
        lab = f"{j['id'][9:]}  iou {mean([r[v]['iou_auth'] for v in VIEWS[1:]])} (prior {mean([r[v]['prior_iou'] for v in VIEWS[1:]])})"
        rows.append((lab, [['authored F R L B', [T[v] for v in VIEWS]], ['rule prior R L B', [P, P, P]], [f'{best} s7 R L B', [(g, Gs[0]) for g in Gs[1:]]]]))
    three_scales(rows, f'Phase-2 holdout, {best}: authored | rule prior | generated (front given)', bg, sh, f'holdout_{best}')
    # 2. checkpoint comparison: every hat, R L B per checkpoint
    rows = []
    for j in jobs:
        rows.append((j['id'].replace('holdout__', 'H ').replace('concept__', ''),
                     [['front', [j['front']]]] + [[t, [(g, j['front']) for g in load(t, j['id'], 7)[1:]]] for t in tags]))
    three_scales(rows, 'Checkpoint comparison, seed 7: right left back per checkpoint', bg, sh, 'checkpoints')
    # 3. custom fronts at best checkpoint, all seeds
    seeds = sorted({r['seed'] for r in results.values() if r['ckpt'] == best})
    rows = [(j['id'], [['front', [j['front']]]] + [[f's{sd} R L B', [(g, j['front']) for g in load(best, j['id'], sd)[1:]]] for sd in seeds])
            for j in jobs if j['truth'] is None]
    three_scales(rows, f'LoRA fronts (flower / animal / witch) -> generated views, {best}', bg, sh, f'custom_{best}')
    log('sheets written to', sh)


def main():
    run, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    M = json.load(open(os.path.join(SUB, 'manifest.json'))); M1 = json.load(open(P1))
    qx, qy = M['quadrants']['front']; C, MAR = M['cell'], M['margin']
    x0, y0 = (MAR + qx * C) // 8, (MAR + qy * C) // 8; box = (x0, y0, x0 + 20 * C // 8, y0 + 20 * C // 8)
    assert box == (2, 2, 32, 32), box
    ck = {}
    for f in glob.glob(os.path.join(run, '*.safetensors')):
        m = re.search(r'-(\d{6})\.safetensors$', f); ck[f'e{int(m.group(1)):02d}' if m else 'e10'] = f
    assert not ck or 'e10' in ck, 'final checkpoint missing'
    jobs = build_jobs(M, M1)
    sh = os.path.join(out, 'sheets'); os.makedirs(sh, exist_ok=True)
    three_scales([(j['id'], [['given front', [j['front']]]]) for j in jobs], 'Given fronts (holdout = authored; others = phase-1 LoRA, decoded)', M['background'], sh, 'fronts')
    if not ck: log('fronts only: no checkpoints'); return
    log(len(jobs), 'jobs,', len(ck), 'checkpoints:', sorted(ck))
    mp = os.path.join(out, 'metrics.json'); results = json.load(open(mp)) if os.path.exists(mp) else {}
    for tag in sorted(ck, key=lambda t: int(t[1:])): run_ckpt(ck[tag], tag, jobs, [7], M, box, out, results)
    score = {t: mean([np.mean([r['gen'][v]['iou_auth'] for v in VIEWS[1:]]) for r in results.values()
                      if r['ckpt'] == t and r['seed'] == 7 and r['group'] == 'holdout']) for t in ck}
    best = max(score, key=score.get); log('holdout mean IoU per checkpoint', score, 'best', best)
    run_ckpt(ck[best], best, jobs, [8, 9], M, box, out, results)
    summarise(results, jobs, M, out, best)
    open(os.path.join(out, 'DONE'), 'w').write(best)


if __name__ == '__main__':
    main()
