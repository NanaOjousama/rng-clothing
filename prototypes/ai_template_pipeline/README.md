# Experimental AI Template Pipeline

Purpose: test whether local AI can help create/refine clothing construction-template candidates without replacing or modifying the frozen RNG clothing generator.

## Stack
- Base: SDXL 1.0
- Structure control: SDXL Canny ControlNet
- Pixel style: switchable LoRA (`Hadimeeee/pixel-art-lora-sdxl` default, `nerijs/pixel-art-xl` alternate)
- Postprocess: nearest-neighbor reduction + limited palette + optional alpha lock

## Why SDXL first
SDXL currently gives us the cleanest combination of mature ControlNet support and pixel-art LoRAs. FLUX can be added later behind the same experiment boundary if SDXL is not good enough.

## Safety boundary
This prototype reads approved template frames but does not write into `generator/`, `authored/`, or ESM assets. All output stays under this prototype's `runs/` folder unless an explicit output path is supplied.

## Modes
`alpha-mode=lock` keeps the exact approved silhouette and tests styling/material assistance.

`alpha-mode=threshold` allows the generated result to propose a new silhouette candidate. It is experimental and must never auto-promote into the frozen template library.

## First test
Use `slouch_pl24` front view because its geometry is already approved and understood. Compare whether the AI makes useful source/template material without destroying readability.

## Setup on Steam Deck
```bash
cd '/run/media/deck/USD00/RNG_clothing/prototypes/ai_template_pipeline'
chmod +x setup_steamdeck.sh
./setup_steamdeck.sh
```

## Prepare-only smoke test
```bash
./.venv/bin/python run_pipeline.py --template-id slouch_pl24 --view front --prepare-only
```
This creates the NN-upscaled source and Canny control image without downloading the large models.

## Full generation
```bash
./.venv/bin/python run_pipeline.py --template-id slouch_pl24 --view front --lora hadimeeee
```
Alternate LoRA:
```bash
./.venv/bin/python run_pipeline.py --template-id slouch_pl24 --view front --lora nerijs
```

Outputs: `01_init.png`, `02_canny.png`, `03_raw.png`, `04_native.png`, `05_preview_x12.png`, and `metadata.json`.

The Steam Deck has an AMD Van Gogh GPU. This prototype uses CPU PyTorch by default on the Deck, so full SDXL inference is expected to be slow. The model cache is intentionally placed on the SD card rather than `/home`.
