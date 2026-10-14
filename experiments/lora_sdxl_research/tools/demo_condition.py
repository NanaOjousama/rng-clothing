"""Front-conditioned view generation: DEMONSTRATE THE MECHANISM (inference only, no training).

Given a fixed 20x20 FRONT, produce right/left/back in the 2x2 sheet (704 px, 16-px cells).
Conditioning paths compared (all keep the front quadrant exact):
  A  attention only      front quadrant = the given front; other quadrants start from NOISE;
                         every denoising step re-imposes the front's (noised) latents (masked latent
                         blending, as diffusers' SDXL inpaint pipeline does for a 4-channel U-Net).
                         The only route from front to other views is self-attention across the sheet.
  B  rough prior, s=0.5  other quadrants START from a rule-built rough view (front silhouette, rows
                         filled with the row's dominant colour: the measured best simple rule, IoU
                         0.59-0.66 vs authored views); SDEdit refines it; front blended as in A.
  C  rough prior, s=0.75 same, more freedom.
After decoding, the front quadrant's exact pixels are pasted back (the front is given, so this is
legitimate) and every quadrant is decoded to 20x20 with decode_v2.
Model here = SDXL base + the PHASE-1 LoRA (fronts only, 512 px / 24-px cells): it was never trained
on sheets, so this shows the MECHANICS and how much each path leans on the prior; it cannot show
the quality a sheet-trained LoRA would give.
usage: python demo_condition.py <subset_dir> <lora.safetensors> <out_dir> <file> [<file> ...]"""
import json, os, sys
import numpy as np, torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLInpaintPipeline, DPMSolverMultistepScheduler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode_v2 as D

MODEL = r'C:\Users\Chris\stardew-lora-lab\models\sdxl\sd_xl_base_1.0.safetensors'
VIEWS = ['front', 'right', 'left', 'back']
NEG = 'photo, realistic, 3d render, blurry, gradient, text, watermark, person, face, pattern'


def read_views(im, M):
    a = np.asarray(im.convert('RGB')).astype(int); C, MAR = M['cell'], M['margin']; out = {}
    for v in VIEWS:
        qx, qy = M['quadrants'][v]; g = np.zeros((20, 20, 3), int)
        for y in range(20):
            for x in range(20):
                x0, y0 = MAR + (qx + x) * C, MAR + (qy + y) * C
                g[y, x] = np.median(a[y0 + C // 4:y0 + 3 * C // 4, x0 + C // 4:x0 + 3 * C // 4].reshape(-1, 3), 0)
        out[v] = g
    return out


def rough_from_front(F, bg):
    """rows of the front silhouette, filled, coloured with each row's dominant colour; outline kept."""
    hat = np.abs(F - np.array(bg)).sum(2) > 40; R = np.zeros_like(F); R[:] = bg
    for y in range(20):
        xs = np.where(hat[y])[0]
        if not len(xs): continue
        cols = [tuple(F[y, x]) for x in xs[1:-1]] or [tuple(F[y, x]) for x in xs]
        dom = max(set(cols), key=cols.count); edge = tuple(F[y, xs[0]])
        R[y, xs[0]:xs[-1] + 1] = dom; R[y, xs[0]] = edge; R[y, xs[-1]] = edge
    return R


def paint(sheet_px, views, M):
    C, MAR = M['cell'], M['margin']
    for v, g in views.items():
        qx, qy = M['quadrants'][v]
        for y in range(20):
            for x in range(20):
                x0, y0 = MAR + (qx + x) * C, MAR + (qy + y) * C
                sheet_px[y0:y0 + C, x0:x0 + C] = g[y, x]


def iou(a, b): return float((a & b).sum() / max(1, (a | b).sum()))


def main():
    sub, lora, out = sys.argv[1:4]; files = sys.argv[4:]; os.makedirs(out, exist_ok=True)
    M = json.load(open(os.path.join(sub, 'manifest.json'))); bg = M['background']; CAN = M['canvas']
    caps = {i['file']: i['caption'] for i in M['items']}
    pipe = StableDiffusionXLInpaintPipeline.from_single_file(MODEL, torch_dtype=torch.float16, local_files_only=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(os.path.dirname(lora), weight_name=os.path.basename(lora))
    pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
    mask = np.full((CAN, CAN), 255, np.uint8); C, MAR = M['cell'], M['margin']; qx, qy = M['quadrants']['front']
    mask[MAR + qy * C:MAR + (qy + 20) * C, MAR + qx * C:MAR + (qx + 20) * C] = 0      # black = keep (front)
    mask_im = Image.fromarray(mask)
    report = {}
    for f in files:
        split = 'holdout' if os.path.exists(os.path.join(sub, 'holdout', f + '.png')) else os.path.join('train', '1_sdvhat')
        truth_im = Image.open(os.path.join(sub, split, f + '.png')).convert('RGB'); T = read_views(truth_im, M)
        R = rough_from_front(T['front'], bg)
        prior = np.zeros((CAN, CAN, 3), np.uint8); prior[:] = bg
        paint(prior, {'front': T['front'], 'right': R, 'left': R, 'back': R}, M)
        noise_init = np.zeros((CAN, CAN, 3), np.uint8); noise_init[:] = bg; paint(noise_init, {'front': T['front']}, M)
        rows = [('authored (truth)', truth_im), ('rough prior', Image.fromarray(prior))]; report[f] = {}
        for tag, init, strength in (('A attention only', noise_init, 1.0), ('B prior s0.5', prior, 0.5), ('C prior s0.75', prior, 0.75)):
            im = pipe(prompt=caps[f], negative_prompt=NEG, image=Image.fromarray(init), mask_image=mask_im, width=CAN, height=CAN,
                      strength=strength, guidance_scale=7.0, num_inference_steps=30, generator=torch.Generator('cpu').manual_seed(7)).images[0]
            a = np.asarray(im).copy(); paint(a, {'front': T['front']}, M); im = Image.fromarray(a)     # exact front back
            G = read_views(im, M); rep = {}
            for v in VIEWS[1:]:
                hg, _ = D.decode_v2(G[v], bg); ht, _ = D.decode_v2(T[v], bg); hr, _ = D.decode_v2(R, bg)
                rep[v] = {'iou_vs_authored': round(iou(hg, ht), 3), 'iou_vs_prior': round(iou(hg, hr), 3)}
            hf, _ = D.decode_v2(G['front'], bg); htf, _ = D.decode_v2(T['front'], bg)
            rep['front_exact'] = bool((G['front'] == T['front']).all())
            report[f][tag] = rep; rows.append((tag, im))
            im.save(os.path.join(out, f'{f}__{tag.split()[0]}.png'))
        prior_iou = {v: round(iou(D.decode_v2(R, bg)[0], D.decode_v2(T[v], bg)[0]), 3) for v in VIEWS[1:]}
        report[f]['rough prior'] = {v: {'iou_vs_authored': prior_iou[v]} for v in VIEWS[1:]}
        W = 300; sheet = Image.new('RGB', (len(rows) * (W + 6), W + 20), (150, 150, 150)); dr = ImageDraw.Draw(sheet)
        for i, (tag, im) in enumerate(rows):
            sheet.paste(im.resize((W, W), Image.NEAREST), (i * (W + 6), 18)); dr.text((i * (W + 6) + 2, 2), tag, fill=(0, 0, 0))
        sheet.save(os.path.join(out, f'{f}__compare.png'))
        json.dump(report, open(os.path.join(out, 'report.json'), 'w'), indent=1)
        print(f, json.dumps(report[f]), flush=True)


if __name__ == '__main__':
    main()
