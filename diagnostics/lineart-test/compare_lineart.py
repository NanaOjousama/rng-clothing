[Reading 87 lines from start (total: 87 lines, 0 remaining)]

#!/usr/bin/env python3
"""Small controlled SDXL/LoRA vs lineart adapter comparison. Inference only."""
import argparse, json, random, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageOps

def condition_from_reference(src: Image.Image, mode: str) -> Image.Image:
    # Holdout-derived control is a *diagnostic only*: it reveals target boundaries.
    from PIL import Image
    nearest = getattr(Image, "Resampling", Image).NEAREST
    if mode == "pixel_edges":
        coarse = src.convert("RGB").resize((64, 64), nearest)
        arr = np.asarray(coarse, dtype=np.int16)
        difference = np.zeros(arr.shape[:2], dtype=bool)
        difference[:,1:] |= (np.max(abs(arr[:,1:]-arr[:,:-1]), axis=2) > 40)
        difference[1:,:] |= (np.max(abs(arr[1:]-arr[:-1]), axis=2) > 40)
        edges = Image.fromarray((difference.astype(np.uint8)*255), "L")
        return Image.merge("RGB", (edges,edges,edges)).resize(src.size, nearest)
    gray = ImageOps.grayscale(src)
    edges = gray.filter(ImageFilter.FIND_EDGES).convert("RGB")
    return edges

def run():
    a = argparse.ArgumentParser()
    a.add_argument("--root", default="/workspace/stardew-lora-lab")
    a.add_argument("--control-image", help="Optional separate four-view construction template; default is held-out reference (diagnostic only)")
    a.add_argument("--holdout", default="hat_0049")
    a.add_argument("--seed", type=int, default=20261010)
    a.add_argument("--steps", type=int, default=24)
    a.add_argument("--strength", type=float, default=0.7)
    a.add_argument("--mode", choices=["pixel_edges","pil_edges"], default="pixel_edges")
    a.add_argument("--model-repo", default="TencentARC/t2i-adapter-lineart-sdxl-1.0")
    a.add_argument("--lora-scale", type=float, default=1.0)
    a.add_argument("--dry-run", action="store_true", help="Validate images/paths and preprocessing without a GPU")
    args = a.parse_args()
    root = Path(args.root); dataset = root/"datasets/exact_grid_16_v4/holdout"
    image_path = dataset/(args.holdout+".png"); caption_path = dataset/(args.holdout+".txt")
    lora = root/"outputs/sdxl_grid16_v4/sdxl_exact_grid_16.safetensors"
    base = root/"models/sdxl/sd_xl_base_1.0.safetensors"
    for p in (image_path,caption_path,lora,base):
        if not p.is_file(): raise FileNotFoundError(p)
    source = Image.open(args.control_image or image_path).convert("RGB")
    source = source.resize((512,512), Image.Resampling.NEAREST)
    cond = condition_from_reference(source,args.mode)
    out = root/"results/lineart_first_test"/args.holdout; out.mkdir(parents=True,exist_ok=True)
    cond.save(out/"conditioning.png")
    prompt = caption_path.read_text(encoding="utf-8").strip()
    details = {"holdout":args.holdout,"control_image":args.control_image or str(image_path),
        "reference_leakage":args.control_image is None,"seed":args.seed,"steps":args.steps,
        "strength":args.strength,"mode":args.mode,"lora_scale":args.lora_scale,
        "model_repo":args.model_repo,"prompt":prompt}
    (out/"run_metadata.json").write_text(json.dumps(details,indent=2), encoding="utf-8")
    if args.dry_run:
        print("DRY RUN OK",json.dumps(details,indent=2)); return
    import torch
    from diffusers import StableDiffusionXLPipeline, StableDiffusionXLAdapterPipeline, T2IAdapter
    assert torch.cuda.is_available(), "CUDA GPU required"
    dtype = torch.float16
    common = dict(torch_dtype=dtype, use_safetensors=True)
    def generator(): return torch.Generator(device="cuda").manual_seed(args.seed)
    def load_lora(pipe):
        # Diffusers supports Kohya-format safetensors in recent versions, but check actual compatibility.
        pipe.load_lora_weights(str(lora.parent), weight_name=lora.name, adapter_name="stardew")
        pipe.set_adapters(["stardew"],adapter_weights=[args.lora_scale])
        return pipe
    print("Loading baseline SDXL from single file")
    baseline = StableDiffusionXLPipeline.from_single_file(str(base), torch_dtype=dtype, use_safetensors=True).to("cuda")
    load_lora(baseline)
    start=time.monotonic()
    result=baseline(prompt=prompt,num_inference_steps=args.steps,generator=generator(),height=512,width=512).images[0]
    result.save(out/"lora_only.png")
    print("Baseline seconds:",round(time.monotonic()-start,1))
    del baseline; torch.cuda.empty_cache()
    print("Loading lineart SDXL adapter")
    adapter = T2IAdapter.from_pretrained(args.model_repo,torch_dtype=dtype,variant="fp16")
    # Base checkpoint stays the same to make this a meaningful controlled comparison.
    pipe = StableDiffusionXLAdapterPipeline.from_single_file(str(base),adapter=adapter,torch_dtype=dtype,use_safetensors=True).to("cuda")
    load_lora(pipe)
    start=time.monotonic()
    result=pipe(prompt=prompt,image=cond,adapter_conditioning_scale=args.strength,
        num_inference_steps=args.steps,generator=generator(),height=512,width=512).images[0]
    result.save(out/"lora_plus_lineart.png")
    print("Adapter seconds:",round(time.monotonic()-start,1))
    print("Outputs:",out)

if __name__=="__main__":run()

[executed on device: LAPTOP-GGEDSK3A (11c475b4-4eca-400d-8353-a8393d5d126f)]