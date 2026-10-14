"""Inference for clean-front (method C) LoRAs: the SAME conditioning as training.
The front quadrant's latent is the CLEAN VAE latent of the given front at every step (not re-noised,
unlike diffusers' inpaint pipeline = method A); the other quadrants denoise from noise or from the
rough prior (SDEdit, --strength < 1).  Exact front pixels are pasted back after decoding.
Runs with any LoRA (the phase-1 LoRA only exercises the mechanics; meaningful results need a LoRA
trained with sdxl_train_cleanfront.py).
usage: python infer_cleanfront.py <subset_dir> <lora.safetensors> <out_dir> <strength> <file> [<file> ...]"""
import json, os, sys
import numpy as np, torch
from PIL import Image
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode_v2 as D
import demo_condition as DC

STEPS = 30


def main():
    sub, lora, out, strength = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]); files = sys.argv[5:]
    assert strength == 1.0, 'prior start (strength < 1) not implemented yet: base SDXL pipeline has no denoising_start'
    os.makedirs(out, exist_ok=True)
    M = json.load(open(os.path.join(sub, 'manifest.json'))); bg = M['background']; CAN, C, MAR = M['canvas'], M['cell'], M['margin']
    qx, qy = M['quadrants']['front']; x0, y0 = (MAR + qx * C) // 8, (MAR + qy * C) // 8; x1, y1 = x0 + 20 * C // 8, y0 + 20 * C // 8
    assert (MAR + qx * C) % 8 == 0 and (20 * C) % 8 == 0, 'front box must sit on the 8-px latent grid'
    caps = {i['file']: i['caption'] for i in M['items']}
    pipe = StableDiffusionXLPipeline.from_single_file(DC.MODEL, torch_dtype=torch.float16, local_files_only=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(os.path.dirname(lora), weight_name=os.path.basename(lora))
    vae = pipe.vae.to('cuda', torch.float32); sf = vae.config.scaling_factor
    jobs = {}
    for f in files:                                    # encode before offload (fp32 VAE: SDXL VAE NaNs in fp16)
        split = 'holdout' if os.path.exists(os.path.join(sub, 'holdout', f + '.png')) else os.path.join('train', '1_sdvhat')
        truth = Image.open(os.path.join(sub, split, f + '.png')).convert('RGB'); T = DC.read_views(truth, M)
        R = DC.rough_from_front(T['front'], bg); init = np.zeros((CAN, CAN, 3), np.uint8); init[:] = bg
        DC.paint(init, {'front': T['front'], 'right': R, 'left': R, 'back': R} if strength < 1 else {'front': T['front']}, M)
        x = torch.from_numpy(init).permute(2, 0, 1)[None].float().cuda() / 127.5 - 1
        with torch.no_grad(): lat = vae.encode(x).latent_dist.mean * sf
        jobs[f] = (T, lat.half().cpu())
    vae.to('cpu', torch.float16); torch.cuda.empty_cache(); pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
    report = {}
    for f, (T, lat0) in jobs.items():
        g = torch.Generator('cpu').manual_seed(7); noise = torch.randn(lat0.shape, generator=g, dtype=torch.float16)
        lat = noise * pipe.scheduler.init_noise_sigma
        lat[:, :, y0:y1, x0:x1] = lat0[:, :, y0:y1, x0:x1]                       # clean front from step 0

        def keep_front(p, i, t, kw):
            L = kw['latents']; L[:, :, y0:y1, x0:x1] = lat0[:, :, y0:y1, x0:x1].to(L.device, L.dtype); return {'latents': L}
        kwargs = dict(prompt=caps[f], negative_prompt=DC.NEG, width=CAN, height=CAN, guidance_scale=7.0, num_inference_steps=STEPS,
                      latents=lat, callback_on_step_end=keep_front, callback_on_step_end_tensor_inputs=['latents'])
        im = pipe(**kwargs).images[0]
        a = np.asarray(im).copy(); DC.paint(a, {'front': T['front']}, M); im = Image.fromarray(a)
        im.save(os.path.join(out, f'{f}__C_s{strength}.png'))
        G = DC.read_views(im, M); rep = {'front_exact': bool((G['front'] == T['front']).all())}
        for v in DC.VIEWS[1:]:
            rep[v] = {'iou_vs_authored': round(DC.iou(D.decode_v2(G[v], bg)[0], D.decode_v2(T[v], bg)[0]), 3)}
        report[f] = rep; print(f, json.dumps(rep), flush=True)
    json.dump(report, open(os.path.join(out, f'report_C_s{strength}.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
