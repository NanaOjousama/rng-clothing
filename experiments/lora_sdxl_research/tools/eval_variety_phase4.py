"""Phase-4 FRONT-LoRA VARIETY test (GPU host, INFERENCE ONLY).  Prepared 2026-10-14, not run.
Question (user, 2026-10-14): the witch families rest on very few silhouette bodies -- low sweeping is 16 images but
only 3 bodies (Luny; mushlune Wildwood; mushlune Bloom; IoU 0.93-1.00 inside a body, 0.60-0.86 between bodies).
Does the front LoRA make NEW low-sweeping hats, or re-draw the training bodies in new colours?
Run AFTER eval_front_phase4.py (reads its summary.json for the best phase-4 checkpoint).
Per witch family: its 3 eval prompts + 1 plain prompt, x 8 seeds (101-108), for the best phase-4 front LoRA and the
phase-1 front LoRA (baseline).  Per render, silhouettes compared MIRROR-AWARE in the 24x24 window:
  nearest training witch front + its body; class  copy >= 0.93 (inside-a-body level) | variant 0.85-0.93 |
  new < 0.85 (the gap between two different authored bodies) | empty (< 20 cells, or > 400 = not a hat)
Per prompt: distinct silhouettes among its 8 seeds (greedy, 0.93) and mean pairwise IoU (high = mode collapse).
'new' only counts if it still reads as that family by eye: variety_<family>_x{4,10}.png shows every render
above its nearest training front.  Metrics are advisory; the eye decides (CLAUDE.md s1).
usage: python eval_variety_phase4.py <p4_front_run_dir> <p1_lora> <front_eval_out_dir> <out_dir>"""
import itertools, json, os, re, sys, glob
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_front_phase4 as E
SEEDS = list(range(101, 109)); COPY, VARIANT = 0.93, 0.85
FAM = {'short': 'short witch hat', 'tall_floppy': 'tall floppy witch hat', 'classic': 'classic pointed witch hat',
       'low_sweeping': 'low sweeping witch hat'}


def mirror(s): return {(23 - x, y) for x, y in s}
def miou(a, b): return max(E.iou(a, b), E.iou(a, mirror(b)))


def bodies(witch, man):
    """single-linkage clusters of the training witch fronts at COPY, per family -> {file: body label}"""
    out = {}
    for fam in FAM.values():
        fs = [f for f in witch if man[f].get('family') == fam]; lab = {f: i for i, f in enumerate(fs)}
        for a, b in itertools.combinations(fs, 2):
            if miou(witch[a], witch[b]) >= COPY:
                la, lb = lab[a], lab[b]; lab = {f: (la if l == lb else l) for f, l in lab.items()}
        groups = {}
        for f, l in lab.items(): groups.setdefault(l, []).append(f)
        for n, fs_ in enumerate(sorted(groups.values(), key=len, reverse=True)):
            packs = sorted({man[f]['pack'] for f in fs_})
            for f in fs_: out[f] = f"{fam.split(' witch')[0]} body {n + 1} ({'/'.join(packs)}, {len(fs_)})"
    return out


def jobs(J, phase):
    tail = 'pixel art, 24x24 sprites, dark outline' if phase == 4 else 'pixel art, 20x20 sprite, dark outline'
    ps = [p for p in J['front_prompts'] if p['family'] in FAM]
    ps += [{'id': f'{k}_plain', 'family': k, 'words': v, 'colours': 'dark purple, purple, yellow'} for k, v in FAM.items()]
    return [('variety', p['id'], f"sdvhat, front view, {p['words']}, {p['colours']}, {tail}", p['family']) for p in ps]


def main():
    run4, p1, fe, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
    J = json.load(open(os.path.join(E.R, 'dataset', 'phase4_eval_jobs.json')))
    M4 = json.load(open(os.path.join(E.D4, 'manifest.json'))); M1 = json.load(open(os.path.join(E.D1, 'manifest.json')))
    man = {i['file']: i for i in M4['items']}
    witch = E.train_fronts(E.D4, M4, True); body = bodies(witch, man)
    best = json.load(open(os.path.join(fe, 'summary.json')))['best_p4']
    ck = {}
    for f in glob.glob(os.path.join(run4, '*.safetensors')):
        m = re.search(r'-(\d{6})\.safetensors$', f); ck[f'p4e{int(m.group(1)):02d}' if m else 'p4e10'] = f
    mp = os.path.join(out, 'metrics.json'); res = json.load(open(mp)) if os.path.exists(mp) else {}
    E.jobs_for = lambda M, J_, phase: jobs(J_, phase)                    # reuse E.run with the variety prompts
    E.run(p1, 'p1', M1, 1, J, SEEDS, out, res, {}, {}, {})
    E.run(ck[best], best, M4, 4, J, SEEDS, out, res, {}, {}, {})
    sil = {}
    for k, r in res.items():
        a = np.load(os.path.join(out, 'renders', r['tag'], f"variety__{r['key']}__s{r['seed']}.npy")).reshape(-1, 5)
        s = {(int(x), int(y)) for x, y, *_ in a}; sil[k] = s
        nf, ni = max(((f, miou(s, w)) for f, w in witch.items()), key=lambda t: t[1])
        r.update(nearest=nf, nearest_name=man[nf].get('name'), nearest_body=body[nf], nearest_iou=round(ni, 3),
                 cls='empty' if not 20 <= len(s) <= 400 else 'copy' if ni >= COPY else 'variant' if ni >= VARIANT else 'new')
    summ = {'best_p4': best, 'thresholds': {'copy': COPY, 'variant': VARIANT}, 'bodies': sorted(set(body.values())), 'by_family': {}, 'by_prompt': {}}
    for t in ('p1', best):
        for fam in FAM:
            rs = [r for r in res.values() if r['tag'] == t and r['family'] == fam]
            summ['by_family'][f'{t}|{fam}'] = {'renders': len(rs), **{c: sum(r['cls'] == c for r in rs) for c in ('new', 'variant', 'copy', 'empty')},
                                                 'nearest_bodies': dict(sorted({b: sum(r['nearest_body'] == b for r in rs) for b in {r['nearest_body'] for r in rs}}.items()))}
        for pid in sorted({r['key'] for r in res.values()}):
            ks = [k for k, r in res.items() if r['tag'] == t and r['key'] == pid and r['cls'] != 'empty']; reps = []
            for k in ks:
                if all(miou(sil[k], sil[q]) < COPY for q in reps): reps.append(k)
            pw = [miou(sil[a], sil[b]) for a, b in itertools.combinations(ks, 2)]
            summ['by_prompt'][f'{t}|{pid}'] = {'distinct_silhouettes': len(reps), 'of': len(ks), 'mean_pairwise_iou': round(float(np.mean(pw)), 3) if pw else None}
    json.dump(res, open(mp, 'w'), indent=1); json.dump(summ, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
    for fam in FAM:
        for s in (4, 10): sheet(res, out, fam, ('p1', best), s)
    open(os.path.join(out, 'DONE'), 'w').write(best)


def tile(cells, s):
    t = Image.new('RGB', (24, 24), (118, 146, 96))
    for (x, y), c in cells.items(): t.putpixel((x, y), c)
    return t.resize((24 * s, 24 * s), Image.NEAREST)


def sheet(res, out, fam, tags, s):
    """per prompt and model: 8 renders (top) over their nearest training front (bottom), labelled class + IoU"""
    rows = [(t, pid) for t in tags for pid in sorted({r['key'] for r in res.values() if r['family'] == fam})]
    T, G, LW = 24 * s, 4, 200; W = LW + len(SEEDS) * (T + G); H = 10 + len(rows) * (2 * T + 3 * G + 14)
    im = Image.new('RGB', (W, H), (34, 36, 44)); d = ImageDraw.Draw(im)
    for i, (t, pid) in enumerate(rows):
        y = 10 + i * (2 * T + 3 * G + 14); d.text((4, y), f'{t}\n{pid}', fill=(225, 225, 225))
        for c, sd in enumerate(SEEDS):
            r = res.get(f'{t}|variety__{pid}|{sd}')
            if not r: continue
            a = np.load(os.path.join(out, 'renders', t, f'variety__{pid}__s{sd}.npy')).reshape(-1, 5)
            x = LW + c * (T + G); im.paste(tile({(int(p[0]), int(p[1])): tuple(int(v) for v in p[2:]) for p in a}, s), (x, y))
            ref = Image.open(os.path.join(E.D4, 'train', '2_sdvhat', r['nearest'] + '.png'))
            im.paste(tile(E.native(ref, json.load(open(os.path.join(E.D4, 'manifest.json'))))[0], s), (x, y + T + G))
            col = {'new': (120, 220, 120), 'variant': (230, 200, 90), 'copy': (240, 110, 110), 'empty': (150, 150, 150)}[r['cls']]
            d.text((x, y + 2 * T + 2 * G), f"{r['cls']} {r['nearest_iou']:.2f}", fill=col)
    im.save(os.path.join(out, f'variety_{fam}_x{s}.png'))


if __name__ == '__main__':
    main()
