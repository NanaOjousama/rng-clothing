"""Witch-hat concept round (laptop GPU): SDXL base 1.0, no LoRA, no training.
The render is a DESIGN BRIEF only (colours, trims, charms, lean, brim character); the sprite is
built by forge.py on the native grid.  Guidance = a generic cone blank tinted with the brief's
main colour (round-4 method from ai_original_hats_01: 24/24 real hats).
usage: python gen_witch_briefs.py out_dir   -> <key>.png + briefs_index.json"""
import json, os, sys, time
import torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline, DPMSolverMultistepScheduler

MODEL = r'C:\Users\Chris\stardew-lora-lab\models\sdxl\sd_xl_base_1.0.safetensors'
CONCEPTS = {   # key: (description, blank fill)
    'midnight_stars': ('a deep navy blue witch hat with a crooked tip, small golden stars scattered on the cone, gold band', (35, 45, 110)),
    'moss_mushroom': ('a mossy green witch hat with a bent tip, a brown leather band and a tiny red mushroom charm', (70, 120, 60)),
    'plum_moon': ('a plum purple witch hat with a drooping tip, a silver crescent moon charm and a black band', (110, 50, 120)),
    'pumpkin_patch': ('an orange witch hat with a floppy tip, stitched patches and a green band', (220, 120, 40)),
    'rose_ribbon': ('a dusty rose pink witch hat with a curled tip, a cream ribbon band with a bow', (200, 120, 140)),
    'storm_teal': ('a dark teal witch hat with a crooked tip, a wavy ragged brim and a purple band with a silver buckle', (30, 100, 110)),
    'ember_black': ('a black witch hat with a bent tip, a crimson band and a glowing orange gem buckle', (40, 35, 45)),
    'frost_lilac': ('a pale lilac witch hat with a tall curled tip, white snowflake charms and a light blue band', (180, 160, 220)),
}
SEEDS = [101, 202]
PROMPT = ('{c}, single hat only, nobody wearing it, straight-on front view, centered, large, '
          'flat cartoon game art, simple cel shading, thick dark outline, plain flat light grey background')
NEG = ('person, face, head, hands, animal, pattern, wallpaper, repeating, tiled, sprite sheet, many, multiple objects, '
       'text, watermark, photo, realistic, 3d render, blurry, gradient background, vignette, cast shadow, three-quarter view, tilted')


def blank(fill, CAN=768):
    im = Image.new('RGB', (CAN, CAN), (205, 205, 205)); d = ImageDraw.Draw(im)
    line = tuple(int(c * 0.35) for c in fill); w = 10
    d.ellipse((134, 470, 634, 570), fill=fill, outline=line, width=w)
    d.polygon([(384, 130), (544, 510), (224, 510)], fill=fill)
    d.line([(384, 130), (544, 510)], fill=line, width=w); d.line([(384, 130), (224, 510)], fill=line, width=w)
    return im


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    t2i = StableDiffusionXLPipeline.from_single_file(MODEL, torch_dtype=torch.float16, local_files_only=True)
    t2i.scheduler = DPMSolverMultistepScheduler.from_config(t2i.scheduler.config)
    i2i = StableDiffusionXLImg2ImgPipeline(**t2i.components); i2i.enable_model_cpu_offload(); i2i.enable_vae_tiling()
    idx, t0 = {}, time.time(); jobs = [(k, s) for k in CONCEPTS for s in SEEDS]
    for i, (k, s) in enumerate(jobs, 1):
        desc, fill = CONCEPTS[k]; p = PROMPT.format(c=desc)
        im = i2i(prompt=p, negative_prompt=NEG, image=blank(fill), strength=0.90, guidance_scale=7.0,
                 num_inference_steps=30, generator=torch.Generator('cpu').manual_seed(s)).images[0]
        key = f'{k}__s{s}'; im.save(os.path.join(out, key + '.png'))
        idx[key] = {'prompt': p, 'negative': NEG, 'seed': s, 'blank_fill': fill, 'strength': 0.90, 'model': os.path.basename(MODEL)}
        json.dump(idx, open(os.path.join(out, 'briefs_index.json'), 'w'), indent=1)
        open(os.path.join(out, 'status.txt'), 'w').write(f'RUNNING {i}/{len(jobs)} {time.time() - t0:.0f}s\n')
    open(os.path.join(out, 'status.txt'), 'w').write(f'COMPLETE {len(jobs)}/{len(jobs)} {time.time() - t0:.0f}s\n')


if __name__ == '__main__':
    main()
