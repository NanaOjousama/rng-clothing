"""Evaluation harness (GPU host, inference only - no training).  Same prompts + seeds for
base SDXL and every LoRA checkpoint, so runs are comparable.

Prompt sets:
  holdout   captions of held-out constructions (manifest.json) - shape language test
  concepts  the Lane 2a concepts, written in the training caption grammar - novelty test
Per render (768, grid = manifest block/offset):
  native    read each 32x32 cell's CENTRE 16x16 median -> 20x20; background = within BG_TOL
            of the manifest background colour (exact chroma key; the model learned it)
  grid      mean abs deviation of pixels from their cell median (0 = block-exact)
  colours   distinct native colours (after merging within 12 RGB)
  hat_iou   holdout only: native silhouette vs the held-out authored front
  novelty   max IoU of the native silhouette with ANY training front (high = copying)
Metrics are advisory (CLAUDE.md section 1); eval_sheet.png is for the eye.
usage: python eval_lora.py <dataset_dir> <out_dir> [lora.safetensors] [--n 3]
-> out_dir/<tag>/renders, native.json, metrics.json, eval_sheet.png"""
import argparse, json, os
import numpy as np, torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

MODEL = r'C:\Users\Chris\stardew-lora-lab\models\sdxl\sd_xl_base_1.0.safetensors'   # official base weights only
TAIL = 'pixel art, 20x20 sprite, dark outline'
CONCEPTS = {
    'mushroom': 'fantasy hat, toadstool mushroom cap hat with white spots, red, white',
    'witch': 'fantasy hat, wide brim, witch hat with a crescent moon buckle, dark purple, purple, yellow',
    'frog': 'animal hat, frog bucket hat with two eyes on top, green, light green, white',
    'tricorn': 'tricorn hat, pirate tricorn with gold trim, dark blue, yellow',
    'strawberry': 'knit beanie, strawberry beanie with a green leafy stem, red, green',
    'chef': 'cottage hat, tall chef toque, white, light grey',
    'acorn': 'acorn cap hat with a little stem, brown, light brown',
    'bee': 'knit beanie, yellow and black striped beanie with two antennae, yellow, black',
}
NEG = 'photo, realistic, 3d render, blurry, gradient, text, watermark, person, face, multiple objects, pattern'
BG_TOL, SEEDS = 40, [7, 8, 9]


def native(im, M):
    a = np.asarray(im.convert('RGB')).astype(np.int32); B, O = M['block'], M['offset']; bg = np.array(M['background'])
    cells, dev = {}, []
    for y in range(20):
        for x in range(20):
            blk = a[O + y * B:O + (y + 1) * B, O + x * B:O + (x + 1) * B].reshape(-1, 3)
            med = np.median(a[O + y * B + B // 4:O + y * B + 3 * B // 4, O + x * B + B // 4:O + x * B + 3 * B // 4].reshape(-1, 3), 0)
            dev.append(np.abs(blk - med).mean())
            if np.abs(med - bg).sum() > BG_TOL: cells[(x, y)] = tuple(int(v) for v in med)
    return cells, float(np.mean(dev))


def n_colours(cells):
    reps = []
    for c in cells.values():
        if all(sum(abs(a - b) for a, b in zip(c, r)) > 12 for r in reps): reps.append(c)
    return len(reps)


def iou(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def front_masks(D, M, split):
    out = {}
    for it in M['items']:
        if it['split'] != split or it['view'] != 'front': continue
        sub = os.path.join('train', f"1_{M['trigger']}") if split == 'train' else 'holdout'
        cells, _ = native(Image.open(os.path.join(D, sub, it['file'] + '.png')), M)
        out[it['file']] = set(cells)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('dataset'); ap.add_argument('out'); ap.add_argument('lora', nargs='?')
    ap.add_argument('--n', type=int, default=3); a = ap.parse_args()
    M = json.load(open(os.path.join(a.dataset, 'manifest.json')))
    tag = os.path.splitext(os.path.basename(a.lora))[0] if a.lora else 'base'
    out = os.path.join(a.out, tag); os.makedirs(out, exist_ok=True)
    train_m, hold_m = front_masks(a.dataset, M, 'train'), front_masks(a.dataset, M, 'holdout')
    hold_caps = [(it['file'], it['caption']) for it in M['items'] if it['split'] == 'holdout'][:12]
    jobs = [('holdout', f, c) for f, c in hold_caps] + [('concept', k, f"{M['trigger']}, front view, {v}, {TAIL}") for k, v in CONCEPTS.items()]
    pipe = StableDiffusionXLPipeline.from_single_file(MODEL, torch_dtype=torch.float16, local_files_only=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    if a.lora: pipe.load_lora_weights(os.path.dirname(a.lora), weight_name=os.path.basename(a.lora))
    pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
    res = []
    for kind, key, prompt in jobs:
        for s in SEEDS[:a.n]:
            im = pipe(prompt=prompt, negative_prompt=NEG, width=M['canvas'], height=M['canvas'], guidance_scale=7.0,
                      num_inference_steps=28, generator=torch.Generator('cpu').manual_seed(s)).images[0]
            name = f'{kind}__{key}__s{s}'; im.save(os.path.join(out, name + '.png'))
            cells, grid = native(im, M); sil = set(cells)
            r = {'name': name, 'kind': kind, 'prompt': prompt, 'seed': s, 'grid_dev': round(grid, 2),
                 'colours': n_colours(cells), 'cells': len(cells),
                 'novelty_max_iou_train': round(max((iou(sil, m) for m in train_m.values()), default=0), 3)}
            if kind == 'holdout': r['hat_iou'] = round(iou(sil, hold_m.get(key, set())), 3)
            res.append(r)
            json.dump({'tag': tag, 'lora': a.lora, 'results': res}, open(os.path.join(out, 'metrics.json'), 'w'), indent=1)
            sp = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
            for (x, y), c in cells.items(): sp.putpixel((x, y), c + (255,))
            sp.save(os.path.join(out, name + '__native.png'))
    T = 192; cols = 6; sheet = Image.new('RGB', (cols * (T + 168), ((len(res) + cols - 1) // cols) * (T + 20)), (150, 150, 150))
    d = ImageDraw.Draw(sheet)
    for i, r in enumerate(res):
        x0, y0 = (i % cols) * (T + 168), (i // cols) * (T + 20)
        sheet.paste(Image.open(os.path.join(out, r['name'] + '.png')).convert('RGB').resize((T, T)), (x0, y0 + 18))
        nat = Image.open(os.path.join(out, r['name'] + '__native.png')).resize((160, 160), Image.NEAREST)
        sheet.paste(nat, (x0 + T + 4, y0 + 18), nat); d.text((x0 + 2, y0 + 2), r['name'][:44], fill=(0, 0, 0))
    sheet.save(os.path.join(out, 'eval_sheet.png'))


if __name__ == '__main__':
    main()
