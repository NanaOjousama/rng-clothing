from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CONFIG = json.loads((HERE / "config.json").read_text())
os.environ.setdefault("HF_HOME", CONFIG["hf_cache"])

DEFAULT_PROMPT = (
    "pixel art game clothing asset, single slouch beanie hat only, isolated object, "
    "clean hard pixel edges, simple readable silhouette, rib knit material, "
    "limited palette, crisp stepped shading, no antialiasing, no person, no face"
)
DEFAULT_NEGATIVE = (
    "person, face, head, body, hair, photorealistic, 3d, painterly, blur, "
    "antialiasing, text, watermark, drop shadow, multiple objects"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Experimental SDXL + ControlNet + pixel LoRA template helper")
    p.add_argument("--template-id", default="slouch_pl24")
    p.add_argument("--view", choices=["front", "right", "left", "back"], default="front")
    p.add_argument("--input", help="Optional direct PNG input instead of template lookup")
    p.add_argument("--prompt", default=DEFAULT_PROMPT)
    p.add_argument("--negative", default=DEFAULT_NEGATIVE)
    p.add_argument("--lora", choices=sorted(CONFIG["loras"]), default=CONFIG["default_lora"])
    p.add_argument("--seed", type=int, default=424242)
    p.add_argument("--steps", type=int, default=CONFIG["steps"])
    p.add_argument("--strength", type=float, default=CONFIG["strength"])
    p.add_argument("--control-scale", type=float, default=CONFIG["control_scale"])
    p.add_argument("--work-size", type=int, default=CONFIG["work_size"])
    p.add_argument("--palette-colors", type=int, default=CONFIG["palette_colors"])
    p.add_argument("--alpha-mode", choices=["lock", "threshold"], default="lock")
    p.add_argument("--output-dir")
    p.add_argument("--prepare-only", action="store_true", help="Build input/control images without loading models")
    return p.parse_args()


def resolve_input(args: argparse.Namespace) -> tuple[Path, dict | None]:
    if args.input:
        return Path(args.input).expanduser().resolve(), None
    spec_path = REPO / "generator/data/templates" / f"{args.template_id}.json"
    spec = json.loads(spec_path.read_text())
    frame = spec["frames"][args.view]["path"]
    return (REPO / frame).resolve(), spec


def square_on_white(src: Image.Image, size: int) -> Image.Image:
    rgba = src.convert("RGBA")
    bbox = rgba.getbbox()
    if not bbox:
        raise ValueError("Input is fully transparent")
    crop = rgba.crop(bbox)
    max_dim = max(crop.size)
    target = max(8, int(size * 0.56))
    scale = target / max_dim
    new_size = tuple(max(1, round(v * scale)) for v in crop.size)
    crop = crop.resize(new_size, Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    pos = ((size - crop.width) // 2, (size - crop.height) // 2)
    canvas.alpha_composite(crop, pos)
    return canvas.convert("RGB")


def make_canny(image: Image.Image) -> Image.Image:
    arr = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, CONFIG["canny_low"], CONFIG["canny_high"])
    rgb = np.repeat(edges[:, :, None], 3, axis=2)
    return Image.fromarray(rgb)


def quantize_rgba(rgb: Image.Image, alpha: Image.Image, colors: int) -> Image.Image:
    q = rgb.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors).convert("RGB")
    out = q.convert("RGBA")
    out.putalpha(alpha)
    return out


def threshold_alpha(rgb: Image.Image, cutoff: int = 36) -> Image.Image:
    arr = np.array(rgb.convert("RGB"), dtype=np.int16)
    dist = np.sqrt(np.sum((255 - arr) ** 2, axis=2))
    alpha = np.where(dist > cutoff, 255, 0).astype(np.uint8)
    return Image.fromarray(alpha, mode="L")


def save_preview(native: Image.Image, path: Path, scale: int = 12) -> None:
    native.resize((native.width * scale, native.height * scale), Image.Resampling.NEAREST).save(path)


def load_pipe(lora_name: str):
    import torch
    from diffusers import ControlNetModel, StableDiffusionXLControlNetImg2ImgPipeline

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    control = ControlNetModel.from_pretrained(CONFIG["controlnet"], torch_dtype=dtype)
    pipe = StableDiffusionXLControlNetImg2ImgPipeline.from_pretrained(
        CONFIG["base_model"], controlnet=control, torch_dtype=dtype, use_safetensors=True
    )
    lora = CONFIG["loras"][lora_name]
    pipe.load_lora_weights(lora["repo"], weight_name=lora["weight_name"], adapter_name=lora_name)
    pipe.set_adapters([lora_name], adapter_weights=[lora["weight"]])
    if torch.cuda.is_available():
        pipe.to("cuda")
    else:
        pipe.to("cpu")
        pipe.enable_attention_slicing()
    return pipe, torch


def main() -> None:
    args = parse_args()
    source_path, spec = resolve_input(args)
    source = Image.open(source_path).convert("RGBA")
    native_size = source.size

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.output_dir) if args.output_dir else HERE / "runs" / f"{args.template_id}_{args.view}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    init = square_on_white(source, args.work_size)
    control = make_canny(init)
    init.save(out_dir / "01_init.png")
    control.save(out_dir / "02_canny.png")

    metadata = {
        "source": str(source_path),
        "template_id": args.template_id,
        "view": args.view,
        "native_size": list(native_size),
        "work_size": args.work_size,
        "lora": args.lora,
        "seed": args.seed,
        "prompt": args.prompt,
        "negative": args.negative,
        "strength": args.strength,
        "control_scale": args.control_scale,
        "alpha_mode": args.alpha_mode,
        "generator_untouched": True,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    if args.prepare_only:
        print(f"Prepared {out_dir}")
        return

    pipe, torch = load_pipe(args.lora)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    generator = torch.Generator(device=device).manual_seed(args.seed)
    result = pipe(
        prompt=args.prompt,
        negative_prompt=args.negative,
        image=init,
        control_image=control,
        strength=args.strength,
        controlnet_conditioning_scale=args.control_scale,
        num_inference_steps=args.steps,
        guidance_scale=CONFIG["guidance"],
        generator=generator,
    ).images[0].convert("RGB")
    result.save(out_dir / "03_raw.png")

    reduced = result.resize(native_size, Image.Resampling.NEAREST)
    if args.alpha_mode == "lock":
        alpha = source.getchannel("A")
    else:
        alpha = threshold_alpha(reduced)
    native = quantize_rgba(reduced, alpha, args.palette_colors)
    native.save(out_dir / "04_native.png")
    save_preview(native, out_dir / "05_preview_x12.png")

    metadata["device"] = device
    metadata["steps"] = args.steps
    metadata["output"] = str(out_dir / "04_native.png")
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"Saved experiment to {out_dir}")


if __name__ == "__main__":
    main()
