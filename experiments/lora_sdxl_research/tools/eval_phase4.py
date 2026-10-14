"""Phase-4 FOUR-VIEW evaluation (GPU host, INFERENCE ONLY: never trains).  Prepared 2026-10-14, not run.

Reuses eval_phase3 (generation with the clean front held + pasted back, the same consistency metrics) with the
grid helpers made size-aware (24x24 phase-4 frame; 20x20 for the e10 baseline).

Jobs (same for every model):
  holdout       the phase-4 holdout sheets: 26 library hats (= the phase-3 holdout) + 3 witch references
                (HnH Witch Hat - Long = short, Kailey Straw = tall floppy, Wildwood Elegant = low sweeping; the
                classic pointed reference is the vanilla Witch Hat c357, inside the 26)
  witch_test    the 6 silhouette-test fronts (S1 T1 W1 W2 P1 P2) = the runs/witch_fronts_e10_01 inputs
Models:
  e10           phase-3 best (runs/phase3_cleanfront_resume), in ITS 20x20 layout; jobs that do not fit 20x20 skipped
                (W1/W2 use e10's own 20-wide copies, as in witch_fronts_e10_01).  Seeds 7 8 9.
  p4 e02..e10   every phase-4 checkpoint, seed 7; the best (mean holdout IoU) also seeds 8 9.
All grids are compared in the 24x24 window (20x20 results sit at +2,+4), so numbers are directly comparable.
-> <out>/metrics.json, summary.json (per group & family: e10 vs p4 best), sheets/*_x{1,4,10}.png
usage: python eval_phase4.py <p4_run_dir> <e10.safetensors> <out_dir>"""
import gc, glob, json, os, re, sys, time
import numpy as np, torch
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_phase3 as E
import decode_v2 as D
import demo_condition as DC

R = r'C:\Users\Chris\sdxl_lora_research'
SUB4 = os.path.join(R, 'dataset', 'phase4_4view_512'); SUB3 = os.path.join(R, 'dataset', 'phase3_4view_512')
JOBS = os.path.join(R, 'dataset', 'phase4_eval_jobs.json')
VIEWS = DC.VIEWS; N = 24; OX, OY = 2, 4


# ---------------------------------------------------------------- size-aware helpers (patched into E / D / DC)
def read_views(im, M):
    n = M.get('frame', 20); a = np.asarray(im.convert('RGB')).astype(int); C, MAR = M['cell'], M['margin']; out = {}
    for v in VIEWS:
        qx, qy = M['quadrants'][v]; g = np.zeros((n, n, 3), int)
        for y in range(n):
            for x in range(n):
                x0, y0 = MAR + (qx + x) * C, MAR + (qy + y) * C
                g[y, x] = np.median(a[y0 + C // 4:y0 + 3 * C // 4, x0 + C // 4:x0 + 3 * C // 4].reshape(-1, 3), 0)
        out[v] = g
    return out


def paint(px, views, M):
    C, MAR = M['cell'], M['margin']
    for v, g in views.items():
        qx, qy = M['quadrants'][v]
        for y in range(g.shape[0]):
            for x in range(g.shape[1]):
                x0, y0 = MAR + (qx + x) * C, MAR + (qy + y) * C; px[y0:y0 + C, x0:x0 + C] = g[y, x]


def rough_from_front(F, bg):
    hat = np.abs(F - np.array(bg)).sum(2) > 40; Rr = np.zeros_like(F); Rr[:] = bg
    for y in range(F.shape[0]):
        xs = np.where(hat[y])[0]
        if not len(xs): continue
        cols = [tuple(F[y, x]) for x in xs[1:-1]] or [tuple(F[y, x]) for x in xs]
        dom = max(set(cols), key=cols.count); edge = tuple(F[y, xs[0]])
        Rr[y, xs[0]:xs[-1] + 1] = dom; Rr[y, xs[0]] = edge; Rr[y, xs[-1]] = edge
    return Rr


def decode_v2(C, bg):
    n = C.shape[0]; d = np.linalg.norm(D.oklab(C) - D.oklab(np.array(bg)), axis=-1)
    fam = (C[..., 0] > 150) & (C[..., 2] > 150) & (C[..., 1] < np.minimum(C[..., 0], C[..., 2]) - 45)
    like = (d < 0.22) | fam; bgm = np.zeros((n, n), bool)
    st = [p for p in [(y, x) for y in range(n) for x in (0, n - 1)] + [(y, x) for x in range(n) for y in (0, n - 1)] if like[p]]
    for p in st: bgm[p] = True
    while st:
        y, x = st.pop()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < n and 0 <= xx < n and like[yy, xx] and not bgm[yy, xx]: bgm[yy, xx] = True; st.append((yy, xx))
    bgm |= d < 0.12
    return ~bgm, int((fam & bgm & (d > 0.22)).sum())


def rgba(G, bg, F=None):
    n = G.shape[0]; m = E.hat(G, bg, F); a = np.zeros((n, n, 4), np.uint8); a[..., :3] = G; a[..., 3] = m * 255
    return Image.fromarray(a, 'RGBA')


def tile(g, bg, s):
    G, F = g if isinstance(g, tuple) else (g, None); n = G.shape[0]
    a = rgba(G, bg, F).resize((n * s, n * s), Image.NEAREST); t = Image.new('RGB', (n * s, n * s), E.BACKDROP); t.paste(a, (0, 0), a)
    return t


def make_sheet(rows, header, bg, s, path):
    LW, GAP, TH = 300, max(2, s), 14; T = N * s
    groups0 = rows[0][1]; widths = [len(g[1]) * (T + GAP) + 3 * GAP for g in groups0]
    W = LW + sum(widths); H = TH * 2 + len(rows) * (max(T, TH) + GAP) + GAP
    im = Image.new('RGB', (W, H), (34, 36, 44)); d = ImageDraw.Draw(im); d.text((4, 2), header, fill=(240, 240, 240)); x = LW
    for (title, _), w in zip(groups0, widths): d.text((x, TH + 1), title, fill=(200, 200, 120)); x += w
    y = TH * 2
    for label, groups in rows:
        d.text((4, y + 1), label[:50], fill=(225, 225, 225)); x = LW
        for (_, grids), w in zip(groups, widths):
            for i, g in enumerate(grids):
                if g is not None: im.paste(tile(g, bg, s), (x + i * (T + GAP), y))
            x += w
        y += max(T, TH) + GAP
    im.save(path)


DC.read_views, DC.paint, DC.rough_from_front, D.decode_v2 = read_views, paint, rough_from_front, decode_v2
E.rgba, E.tile, E.make_sheet = rgba, tile, make_sheet


# ---------------------------------------------------------------- jobs
def pad24(G, bg):
    out = np.zeros((N, N, 3), int); out[:] = bg; out[OY:OY + 20, OX:OX + 20] = G; return out


def crop20(G, bg):
    """24 -> 20 window, or None if any hat cell falls outside it"""
    m = (G != np.array(bg)).any(-1); inner = np.zeros_like(m); inner[OY:OY + 20, OX:OX + 20] = True
    return None if (m & ~inner).any() else G[OY:OY + 20, OX:OX + 20].copy()


def grid_of(rows, n, bg):
    G = np.zeros((n, n, 3), int); G[:] = bg
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c is not None: G[y, x] = c
    return G


def build_jobs(M4, M3):
    bg = M4['background']; jobs = []
    for i in M4['items']:
        if i['split'] != 'holdout': continue
        T = read_views(Image.open(os.path.join(SUB4, 'holdout', i['file'] + '.png')).convert('RGB'), M4)
        grp = 'holdout_witch' if i.get('family') else 'holdout'
        j = {'id': f"{grp}__{i['file']}", 'group': grp, 'family': i.get('family'), 'caption': i['caption'], 'front': T['front'], 'truth': T}
        f20 = {v: crop20(T[v], bg) for v in VIEWS}
        if all(g is not None for g in f20.values()):
            cap3 = i['caption'].replace('24x24 sprites', '20x20 sprites')
            j['e10'] = {'front': f20['front'], 'caption': cap3}
        jobs.append(j)
    W = json.load(open(JOBS))
    for w in W['witch_test']:
        cap = f"{M4['trigger']}, {M4['layout_caption']}, {w['caption_tail']}, pixel art, 24x24 sprites, dark outline"
        jobs.append({'id': w['id'], 'group': 'witch_test', 'family': w['family'], 'caption': cap, 'front': grid_of(w['front24'], N, bg),
                     'truth': None, 'e10': {'front': grid_of(w['front20'], 20, bg), 'caption': cap.replace('24x24', '20x20')}})
    return jobs


def run_model(lora, tag, jobs, seeds, M, box, out, results, legacy):
    sel = [j for j in jobs if (not legacy) or 'e10' in j]
    jj = [dict(j, front=j['e10']['front'], caption=j['e10']['caption']) if legacy else j for j in sel]
    E.log('load', tag, os.path.basename(lora), len(jj), 'jobs'); pipe = E.load_pipe(lora); lats = E.encode_fronts(pipe, jj, M); bg = M['background']
    for seed in seeds:
        for j0, j in zip(sel, jj):
            key = f"{tag}|{seed}|{j['id']}"
            if key in results: continue
            t = time.time(); im, G, drift = E.generate(pipe, j, lats[j['id']], seed, M, box)
            if legacy: G = {v: pad24(G[v], bg) for v in VIEWS}
            os.makedirs(os.path.join(out, 'renders', tag), exist_ok=True)
            im.save(os.path.join(out, 'renders', tag, f"{j['id']}__s{seed}.png"))
            np.save(os.path.join(out, 'renders', tag, f"{j['id']}__s{seed}.npy"), np.stack([G[v] for v in VIEWS]))
            r = {'ckpt': tag, 'seed': seed, 'id': j['id'], 'group': j0['group'], 'family': j0['family'], 'front_drift': drift,
                 'gen': E.sheet_metrics(G, bg)}
            if j0['truth'] is not None:
                for v in VIEWS[1:]: r['gen'][v]['iou_auth'] = round(DC.iou(E.hat(G[v], bg, G['front']), E.hat(j0['truth'][v], bg)), 3)
            results[key] = r; E.log(tag, seed, j['id'], f'{time.time() - t:.0f}s')
            json.dump(results, open(os.path.join(out, 'metrics.json'), 'w'), indent=1)
    del pipe; gc.collect(); torch.cuda.empty_cache()


KEYS = ('iou_auth', 'palette_adh', 'new_colours', 'accent_recall', 'outline')


def summarise(results, jobs, M, out, best):
    bg = M['background']; sh = os.path.join(out, 'sheets'); os.makedirs(sh, exist_ok=True); S = {'best_p4': best, 'tables': {}}
    def row(rs):
        if not rs: return None
        d = {'n': len(rs), 'front_drift': E.mean([r['front_drift'] for r in rs]), 'lr_mirror': E.mean([r['gen']['lr_mirror'] for r in rs]),
             'back_front': E.mean([r['gen']['back_front'] for r in rs])}
        for k in KEYS: d[k] = {v: E.mean([r['gen'][v].get(k) for r in rs]) for v in VIEWS[1:]}
        return d
    shared = {j['id'] for j in jobs if 'e10' in j}                          # like-for-like subset
    for tag in ('e10', best):
        for grp in ('holdout', 'holdout_witch', 'witch_test'):
            rs = [r for r in results.values() if r['ckpt'] == tag and r['group'] == grp]
            S['tables'][f'{tag}|{grp}|all_seeds'] = row(rs)
            S['tables'][f'{tag}|{grp}|shared_jobs'] = row([r for r in rs if r['id'] in shared])
        for fam in sorted({j['family'] for j in jobs if j['family']}):
            S['tables'][f'{tag}|family|{fam}'] = row([r for r in results.values() if r['ckpt'] == tag and r['family'] == fam and r['id'] in shared])
    S['checkpoint_holdout_iou'] = {t: E.mean([np.mean([r['gen'][v]['iou_auth'] for v in VIEWS[1:]]) for r in results.values()
                                              if r['ckpt'] == t and r['seed'] == 7 and 'iou_auth' in r['gen']['right']])
                                   for t in sorted({r['ckpt'] for r in results.values()})}
    json.dump(S, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    load = lambda tag, jid, sd: np.load(os.path.join(out, 'renders', tag, f'{jid}__s{sd}.npy'))
    for grp in ('witch_test', 'holdout_witch', 'holdout'):
        rows = []
        for j in [j for j in jobs if j['group'] == grp]:
            g = [['given front' if j['truth'] is None else 'authored F R L B', [j['front']] + ([None] * 3 if j['truth'] is None else [j['truth'][v] for v in VIEWS[1:]])]]
            for tag in ('e10', best):
                for sd in (7, 8, 9):
                    ok = os.path.exists(os.path.join(out, 'renders', tag, f"{j['id']}__s{sd}.npy"))
                    G = load(tag, j['id'], sd) if ok else None
                    g.append([f'{tag} s{sd} R L B', [(x, G[0]) for x in G[1:]] if ok else [None] * 3])
            rows.append((f"{j['id'][-30:]}  {j['family'] or ''}", g))
        if rows: E.three_scales(rows, f'Phase 4 {grp}: e10 (phase 3) vs p4 {best}, front given', bg, sh, f'{grp}_e10_vs_{best}')
    E.log('sheets ->', sh)


def main():
    run, e10, out = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
    M4 = json.load(open(os.path.join(SUB4, 'manifest.json'))); M3 = json.load(open(os.path.join(SUB3, 'manifest.json')))
    def box_of(M, n):
        C, MAR = M['cell'], M['margin']; return (MAR // 8, MAR // 8, (MAR + n * C) // 8, (MAR + n * C) // 8)
    b4, b3 = box_of(M4, N), box_of(M3, 20); assert b4 == b3 == (2, 2, 32, 32), (b4, b3)
    jobs = build_jobs(M4, M3); mp = os.path.join(out, 'metrics.json'); results = json.load(open(mp)) if os.path.exists(mp) else {}
    E.log(len(jobs), 'jobs;', sum('e10' in j for j in jobs), 'fit e10 20x20')
    run_model(e10, 'e10', jobs, [7, 8, 9], M3, b3, out, results, legacy=True)
    ck = {}
    for f in glob.glob(os.path.join(run, '*.safetensors')):
        m = re.search(r'-(\d{6})\.safetensors$', f); ck[f'p{int(m.group(1)):02d}' if m else 'p10'] = f
    assert 'p10' in ck, 'final phase-4 checkpoint missing'
    for tag in sorted(ck, key=lambda t: int(t[1:])): run_model(ck[tag], tag, jobs, [7], M4, b4, out, results, legacy=False)
    score = {t: E.mean([np.mean([r['gen'][v]['iou_auth'] for v in VIEWS[1:]]) for r in results.values()
                        if r['ckpt'] == t and r['seed'] == 7 and r['group'].startswith('holdout')]) for t in ck}
    best = max(score, key=score.get); E.log('holdout IoU per checkpoint', score, 'best', best)
    run_model(ck[best], best, jobs, [8, 9], M4, b4, out, results, legacy=False)
    summarise(results, jobs, M4, out, best); open(os.path.join(out, 'DONE'), 'w').write(best)


if __name__ == '__main__':
    main()
