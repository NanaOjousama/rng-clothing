# Phase 5 — fresh general-purpose SDXL hat LoRA on the RunPod A40

Status 2026-10-19: **dataset built and validated; three-arm pilot running on the A40.** Full run waits for the
user's review of the pilot sheets (user rule: judged on images, never on loss / metrics alone).

AI-ORIGINAL lane (CLAUDE.md 2b): everything trained here is experimental and unapproved; nothing is promoted to any
pool without a worn four-direction QC capture and explicit user approval.

## Why
The phase-4 data (see `PLAN_phase4.md`) had: witch-heavy sources (six witch / foliage packs + the narrow phase-1/3
library picks), the vanilla-slot caption bug (`hats_N` names on replacement art: Kailey berets captioned
cowboy / bowler / top hat), muddled straw captions, witch `num_repeats 2`, a frozen text encoder, and a magenta
background 0.074 OKLab from pale hats.  (The bad A40 straw hat of 2026-10-18 was the separate laptop-lab grid16
baseline LoRA — rank 4, 512 px — not phase 4.)

## Dataset `dataset/phase5_v1` (gitignored, rebuildable, in the MAIN checkout)
Builder `tools/build_dataset_phase5.py` (pure Python), validator `tools/check_dataset_phase5.py` (pure Python),
eye-review sheets `tools/contact_phase5.py` (venv PIL, analysis only), family table
`configs/phase5_family_overrides.json` (eye-verified, wins over rules).

| | |
|---|---|
| sources | ALL of `pack_study/data/library.json` (441 constructions fit the 24x24 window) + the six phase-4 reference packs |
| placement | per view by FS HeadPosition: cell (x, y) -> (x - HX + 2, y - HY + 4) in the 24x24 window |
| colourable hats | tinted as Fashion Sense draws them (DrawManager.DrawColorMask: mask-layer pixels multiplied by the layer colour), one deterministic tint per hat |
| families | 26 shape families from: vanilla names (ConcernedApe only), name rules, pack_study hand labels, eye overrides. 569 candidates -> 143 excluded (accessories, masks, ears, unverifiable shapes; each with a reason) |
| dedupe | exact duplicates; <= 2 colourings per structure; <= 4 hats per silhouette body |
| balance | each family capped at 12 % of kept hats by keeping its most distinct silhouettes; `num_repeats = 1` everywhere |
| split | 41 held-out hats = whole silhouette bodies, per family, every family with >= 3 bodies (22 families) |
| layouts | front: 24x24 frame x 32-px cells = 768; four-view 2x2 F/R/L/B: 48x48 x 16-px cells = 768; no outer margin; both latent-aligned |
| captions | `sdvhat, <layout phrase>, <family>[, brim][, name][, decor], <3 colours>, pixel art, <frame>, dark outline` — layout phrases are disjoint |
| background | solid (0, 0, 255), the corpus-farthest colour; nearest hat colour (63, 72, 204) at 0.123 OKLab |
| size | 912 train (291 hats x 2 layouts + 165 neutral hats mirrored x 2) + 82 holdout |

Validator checks (0 errors): exact cell grid; keying the background recovers each item's exact cell mask; tolerant
key (0.06 OKLab) safe; caption/layout/family rules; no word in > 40 % of captions; train/holdout disjoint by
construction, colourway, structure group and body; holdout never mirrored; family share <= 13 % (largest: beanie
12.9 %, animal 9.6 %, witch 9.0 %); no generated-experiment source.
The validator missed one bug that the built-image sample sheet caught ('decorated' in every caption); the check that
would have caught it is now in the validator.

## Pilot (A40, `pod_phase5/`)
sd-scripts **v0.12.0** (2026-09-24), plain `sdxl_train_network.py`, fresh from SDXL Base 1.0 (volume copy, sha256 in
`/workspace/phase5/base_model.sha256`).  Shared: 768 px, batch 4, bf16, sdpa, no_half_vae, cached latents,
AdamW8bit, unet lr 1e-4, constant_with_warmup 5 %, min-SNR 5, 4 epochs, checkpoint every epoch, seed 20261018,
holdout as the deterministic validation subset.

| arm | rank / alpha | text encoders |
|---|---|---|
| A | 16 / 8 | trained, lr 2.5e-5 |
| B | 32 / 16 | trained, lr 2.5e-5 |
| C | 32 / 16 | frozen, outputs cached (the phase-4 choice) |

Eval (`eval_phase5.py`): 8 families (incl. "wide-brim hat, straw hat") x {front, four-view} x 4 seeds, plus every
holdout caption in both layouts; Euler a, 30 steps, CFG 6; decode by each image's own border colour.  Sheets: arms
side by side per family and layout, 4-seed variety per arm, decoded sprites with the background removed, holdout
truth vs generation.  Metrics are context only.

## Next
1. pilot results + sheets on `lora-reviews`; user review
2. full run only after review (winning arm, 16-20 epochs, cosine)
3. ControlNet comparison later: a pretrained SDXL ControlNet with a **2x2 four-view conditioning sheet in the output
   layout** (never a single-view control against a four-view prompt — the failed T2I-adapter mismatch)
4. 1024 px stays open for a later experiment
