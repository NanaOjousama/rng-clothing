"""Re-render chosen fronts with a corrected caption (INFERENCE ONLY).  2026-10-12: the bear (seyph c287) is
captioned 'animal hat, cowboy hat, bear hat with face' and the model drew cowboy brims on every side view.
Same fronts, same seeds, same checkpoint as eval_phase2; only the caption changes -> isolates the caption.
usage: python caption_retest.py <lora.safetensors> <out_dir>"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_phase2 as E

LAY = 'sdvhat, four views, front top-left, right top-right, left bottom-left, back bottom-right, '
TAIL = ', pixel art, 20x20 sprites, dark outline'
TESTS = {   # job id -> corrected caption
    'animal__holdout__seyph__c287__w0__s7': 'animal hat, teddybear hat, bear hat with face, round ears, dark brown, brown, pale orange',
    'animal__holdout__seyph__c287__w0__s9': 'animal hat, teddybear hat, bear hat with face, round ears, dark brown, brown, pale orange',
    'holdout__seyph__c287__w0': 'animal hat, teddybear hat, bear hat with face, round ears, dark brown, brown, pale orange',
    'holdout__seyph__c288__w0': 'animal hat, cat hat, ears and tail, black, dark grey, white',
}


def main():
    lora, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    M = json.load(open(os.path.join(E.SUB, 'manifest.json'))); M1 = json.load(open(E.P1)); bg = M['background']
    jobs = [j for j in E.build_jobs(M, M1) if j['id'] in TESTS]
    for j in jobs: j['old_caption'] = j['caption']; j['caption'] = LAY + TESTS[j['id']] + TAIL
    pipe = E.load_pipe(lora); lats = E.encode_fronts(pipe, jobs, M); rows = []; rep = {}
    for j in jobs:
        gs = []
        for seed in (7, 8, 9):
            im, G, drift = E.generate(pipe, j, lats[j['id']], seed, M, (2, 2, 32, 32))
            im.save(os.path.join(out, f"{j['id']}__s{seed}.png")); gs.append(G)
            r = E.sheet_metrics(G, bg)
            if j['truth'] is not None:
                for v in E.VIEWS[1:]: r[v]['iou_auth'] = round(E.DC.iou(E.hat(G[v], bg, G['front']), E.hat(j['truth'][v], bg)), 3)
            rep[f"{j['id']}|{seed}"] = {'caption': j['caption'], 'old_caption': j['old_caption'], 'front_drift': drift, 'gen': r}
            E.log(j['id'], seed, json.dumps({v: r[v].get('iou_auth') for v in E.VIEWS[1:]}))
        groups = ([['authored F R L B', [j['truth'][v] for v in E.VIEWS]]] if j['truth'] is not None else [['front', [j['front']]]])
        rows.append((j['id'], groups + [[f's{s} R L B', [(g, G['front']) for g in [G[v] for v in E.VIEWS[1:]]]] for s, G in zip((7, 8, 9), gs)]))
    json.dump(rep, open(os.path.join(out, 'report.json'), 'w'), indent=1)
    # pad rows so every row has the same group layout (authored rows have 4 tiles, front-only rows 1)
    for k, (lab, g) in enumerate(rows):
        if len(g[0][1]) == 1: rows[k] = (lab, [[g[0][0], g[0][1] + [None, None, None]]] + g[1:])
    E.three_scales(rows, 'Corrected captions (teddybear / cat, no cowboy / bowler)', bg, out, 'caption_retest')
    open(os.path.join(out, 'DONE'), 'w').write('ok')


if __name__ == '__main__':
    main()
