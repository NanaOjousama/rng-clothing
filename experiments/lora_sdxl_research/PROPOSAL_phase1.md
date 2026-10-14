# Proposal: phase-1 LoRA training run (NOT started, needs approval)

Date 2026-10-11. Separate from the witch-hat forge work; this file only asks.

## What the experiment would answer

The witch-hat study (`experiments/witch_hat_quality_01`) showed why base SDXL hats look muddy:
shrinking an illustration to 16 px collapses tapering forms and loses deliberate shading.
Building on the native grid fixes that, but needs a hand-built model per hat family.

**Question:** can SDXL + a small LoRA trained on real Stardew/FS hat fronts draw a hat front
**directly on the 20x20 grid** (32 px blocks, exact), with Stardew-like silhouettes, ramps and
outlines? If yes, every family gets native-quality fronts without a per-family forge. If no,
the forge route is confirmed and training stops.

## Run

| step | what | cost on the laptop (RTX 3060 6 GB) |
|---|---|---|
| 0 | copy `dataset/phase1_front` (3.6 MB) to `C:\Users\Chris\sdxl_lora_research\dataset\` | you, once (USB / share) |
| 1 | **memory probe**: 20 steps at 768, rank 16, U-Net only, bf16, cached latents/TE | ~5-10 min; nothing kept |
| 2 | **baseline eval** of base SDXL with `tools/eval_lora.py` (inference only) | ~25 min |
| 3 | **training**: 270 images x 12 epochs = 3,240 steps, checkpoint every epoch | estimate 3-5 h (from the probe's s/it) |
| 4 | eval each checkpoint (fixed seeds, holdout + witch/novel prompts) | ~25 min per checkpoint, 3-4 chosen |

Starts from the official base model; no older LoRA is reused. Seeds, configs and captions
are fixed in `configs/`.

## Pass / fail (judged at native size, as for the witch hats)

- **pass:** at least half the novel-concept fronts are block-exact, read as Stardew hats at 1x
  next to authored hats, and are not near-copies of training fronts (novelty IoU < 0.8).
- **fail:** blurry or misaligned blocks, or copies of the training set, or no better than
  base SDXL plus the snap.

## Risks

- 6 GB VRAM may not fit 768 px (the probe checks; fallback 640 or 512 px with a 24 px block).
- ~270 images is small: style may transfer, novelty may not.
- The machine is busy for a few hours; the GPU can't run SDXL concepts at the same time.

**Asking:** may I run step 1 (the probe) after you copy the dataset, and then step 3 if it passes?
