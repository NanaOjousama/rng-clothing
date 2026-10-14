"""Step 0.2: does prompt wording fix 'concept becomes the object, not a hat'?  Inference only.
Same LoRA, same seeds; for each failing concept, the eval_lora wording vs hat-first wordings,
with object/creature negatives.  Decoded with decode_v2.  -> out/prompt_test.png + results.json
usage: python prompt_test.py <dataset_512_dir> <lora.safetensors> <out_dir>"""
import json, os, sys
import numpy as np, torch
from PIL import Image, ImageDraw
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decode_v2 as D
MODEL = r'C:\Users\Chris\stardew-lora-lab\models\sdxl\sd_xl_base_1.0.safetensors'
TAIL = 'pixel art, 20x20 sprite, dark outline'
NEG0 = 'photo, realistic, 3d render, blurry, gradient, text, watermark, person, face, multiple objects, pattern'
NEG1 = NEG0 + ', creature, animal, insect, fruit, plant, food, mushroom stem, object, toy, eyes only'
TESTS = {
    'mushroom': ['fantasy hat, toadstool mushroom cap hat with white spots, red, white',
                 'knit beanie, a red beanie hat decorated like a toadstool cap, white spots, red, white',
                 'cottage hat, a red bucket hat with white toadstool spots, red, white'],
    'frog': ['animal hat, frog bucket hat with two eyes on top, green, light green, white',
             'animal hat, a green bucket hat with two round frog eyes sewn on top, green, light green, white',
             'knit beanie, a green beanie hat decorated like a frog face, green, white'],
    'strawberry': ['knit beanie, strawberry beanie with a green leafy stem, red, green',
                   'knit beanie, a red beanie hat with seed dots and a green leaf cuff on top, red, green',
                   'cottage hat, a red beret with tiny seeds and a green leaf stem, red, green'],
    'acorn': ['acorn cap hat with a little stem, brown, light brown',
              'knit beanie, a brown beanie hat shaped like an acorn cap with a tiny stem, brown, light brown',
              'cap, a brown cap with a woven acorn-cup texture and a short stem, brown, light brown'],
    'bee': ['knit beanie, yellow and black striped beanie with two antennae, yellow, black',
            'knit beanie, a yellow beanie hat with black stripes and two little antennae on top, yellow, black',
            'animal hat, a fuzzy yellow hood hat with black stripes and antennae, yellow, black'],
}
SEEDS = [7, 8, 9]


def main():
    ds, lora, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
    M = json.load(open(os.path.join(ds, 'manifest.json'))); bg = M['background']
    pipe = StableDiffusionXLPipeline.from_single_file(MODEL, torch_dtype=torch.float16, local_files_only=True)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(os.path.dirname(lora), weight_name=os.path.basename(lora))
    pipe.enable_model_cpu_offload(); pipe.enable_vae_tiling()
    rows, res = [], {}
    for c, wordings in TESTS.items():
        for wi, w in enumerate(wordings):
            neg = NEG0 if wi == 0 else NEG1
            for s in SEEDS:
                p = f"{M['trigger']}, front view, {w}, {TAIL}"
                im = pipe(prompt=p, negative_prompt=neg, width=M['canvas'], height=M['canvas'], guidance_scale=7.0,
                          num_inference_steps=28, generator=torch.Generator('cpu').manual_seed(s)).images[0]
                key = f'{c}__w{wi}__s{s}'; im.save(os.path.join(out, key + '.png'))
                C = D.cells(im, M); h, _ = D.decode_v2(C, bg)
                sp = Image.new('RGBA', (20, 20), (0, 0, 0, 0))
                for y in range(20):
                    for x in range(20):
                        if h[y, x]: sp.putpixel((x, y), tuple(int(v) for v in C[y, x]) + (255,))
                sp.save(os.path.join(out, key + '__native.png')); rows.append((key, sp)); res[key] = {'prompt': p, 'negative': neg, 'cells': int(h.sum())}
                json.dump(res, open(os.path.join(out, 'results.json'), 'w'), indent=1)
    S = 6; cw = 20 * S + 8; ch = 20 * S + 16; cols = 9
    sheet = Image.new('RGB', (cols * cw, ((len(rows) + cols - 1) // cols) * ch), (96, 128, 72)); dr = ImageDraw.Draw(sheet)
    for i, (k, sp) in enumerate(rows):
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        big = sp.resize((20 * S, 20 * S), Image.NEAREST); sheet.paste(big, (x0, y0 + 14), big); dr.text((x0 + 2, y0 + 1), k, fill=(0, 0, 0))
    sheet.save(os.path.join(out, 'prompt_test.png'))


if __name__ == '__main__':
    main()
