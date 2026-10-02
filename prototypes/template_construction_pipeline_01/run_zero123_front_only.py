#!/usr/bin/env python3
from pathlib import Path
import json, time
from PIL import Image
import torch
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "run_trucker_front_only_zero123_01"
CACHE = Path("/run/media/deck/USD00/ai-model-cache")
SOURCE = ROOT / "cap reference/pt_input_front_plain.png"


def prepare_input(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGB")
    bg = im.getpixel((0, 0))
    rgba = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            d = sum((p[i] - bg[i]) ** 2 for i in range(3)) ** 0.5
            rgba.putpixel((x, y), (*p, 255 if d > 18 else 0))
    box = rgba.getchannel("A").getbbox()
    if not box:
        raise RuntimeError("foreground extraction failed")
    obj = rgba.crop(box)
    side = max(obj.size)
    pad = max(24, round(side * 0.18))
    canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(obj, ((canvas.width - obj.width)//2, (canvas.height - obj.height)//2))
    return canvas.resize((320, 320), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inp = prepare_input(SOURCE)
    inp.save(OUT / "00_front_only_input.png")
    started = time.time()
    pipe = DiffusionPipeline.from_pretrained(
        "sudo-ai/zero123plus-v1.2",
        custom_pipeline="sudo-ai/zero123plus-pipeline",
        torch_dtype=torch.float32,
        cache_dir=str(CACHE),
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipe.scheduler.config, timestep_spacing="trailing")
    pipe.to("cpu")
    pipe.enable_attention_slicing()
    load_seconds = time.time() - started
    seed = 424242
    gen = torch.Generator(device="cpu").manual_seed(seed)
    run_started = time.time()
    result = pipe(inp, num_inference_steps=8, guidance_scale=4.0, generator=gen).images[0]
    infer_seconds = time.time() - run_started
    result.save(OUT / "01_zero123_multiview_8step.png")
    meta = {
        "model": "sudo-ai/zero123plus-v1.2",
        "customPipeline": "sudo-ai/zero123plus-pipeline",
        "input": str(SOURCE.relative_to(ROOT)),
        "inputPolicy": "FRONT VIEW ONLY; side/back references withheld from model",
        "seed": seed,
        "steps": 8,
        "guidanceScale": 4.0,
        "dtype": "float32",
        "device": "cpu",
        "loadSeconds": load_seconds,
        "inferenceSeconds": infer_seconds,
        "status": "RAW_MULTIVIEW_CANDIDATE_NOT_APPROVED",
    }
    (OUT / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
