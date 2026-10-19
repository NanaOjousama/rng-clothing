# Phase 5 — fresh general-purpose SDXL hat LoRA on the RunPod A40

Status 2026-10-19: **dataset built and validated; three-arm pilot trained and evaluated on the A40; results
published to `lora-reviews`.** Full run waits for the user's review of the pilot sheets (user rule: judged
on images, never on loss / metrics alone). Pod `5kstuywlqnafya` stopped after results were pulled.

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

## Pilot results (2026-10-19)

Trained all three arms (B, A, C in that order; ~27 min each) plus B's epoch-2 checkpoint (B_e2), then
evaluated all five (base, A, B, C, B_e2) with `eval_phase5.py`: 8 families x {front, four-view} x 4 seeds,
plus every holdout caption at seed 101. Two bugs hit and fixed along the way (not data/config bugs — tooling):
- `validation_split` is dataset-level only in sd-scripts v0.12.0, not per-subset; removed the holdout subset
  from `dataset_phase5.toml` (holdout is still never trained on, judged only through generated images).
- diffusers 0.40.0's `pipe.load_lora_weights` crashes on this checkpoint's text-encoder-2 LoRA (its own
  converter bug, confirmed via a raw safetensors key dump that both TE1/TE2 blocks are intact). Fixed by
  loading/merging through sd-scripts' own `networks.lora.create_network_from_weights(for_inference=True)`
  + `network.merge_to(...)` in `eval_phase5.py`, instead of diffusers' loader.

**Verdict, by eye** (`lora-reviews` commit `bfa328f`, `lora_reviews/phase5_pilot_2026-10-19/`): arm **C**
(rank 32/alpha 16, frozen text encoders, cached TE outputs) is the only usable arm. A and B (text encoders
trained, lr 2.5e-5, 4 epochs) mostly failed to learn the training format — non-solid backgrounds, whole
faces/bodies drawn instead of an isolated hat, broken four-view panel layouts; B_e2 is not meaningfully
better, so this looks like instability from training the text encoders at this LR/schedule, not just
undertraining. C reliably isolates a hat on a flat background in the correct 2x2 F/R/L/B layout, and
generalizes plausibly to held-out families. Known gap even in C: background color drifts off the trained
(0,0,255) per family (still flat/keyable, not exact) — worth tightening in the full run.

## Pilot 2 results: C2 (rank32/10ep) vs C3 (rank64/10ep) — 2026-10-19

Tested arm C's recipe pushed further in two ways: C2 = same rank 32/alpha 16, epochs 4->10. C3 = rank
64/alpha 32, epochs 10. Both frozen TE / cached TE outputs, same as C.

**Critical eval bug found and fixed**: the LoRA-merge path matched **0 U-Net modules** whenever `unet`
passed to `create_network_from_weights` was a diffusers `UNet2DConditionModel` — sd-scripts' saved keys
only match its own native SD-style-named `SdxlUNet2DConditionModel`. This silently affected every eval
after the first bugfix attempt (arms A, B, B_e2, C2, C3), **invalidating the original pilot-1 "arm C
wins" A/B/C comparison** (arm C's own original eval had used a different working path and was
unaffected; A/B never actually got their trained U-Net LoRA applied). Fixed in `eval_phase5.py`: load a
native `sdxl_model_util.load_models_from_sdxl_checkpoint(...)` U-Net, merge via
`networks.lora.create_network_from_weights(..., for_inference=True)` + `network.merge_to(...)`, then
`convert_sdxl_unet_state_dict_to_diffusers(...)` back into `pipe.unet`. Verified: 722 modules matched
(vs 0), 0 missing/unexpected keys. Arm C's own eval was re-run under the fix as a consistency check and
matched its original numbers.

**Verdict, by eye** (`lora-reviews` commits `0873317`, `e2a06c9`): mixed, not a clean win. Front layout
improved over arm C (crisper detail, esp. cap/flower crown; 2 clear holdout misses: an orange-glyph
headscarf, an animal-hat/party-hat family breaking into a garbled 4-panel grid). **Four-view layout
regressed badly** in both C2 and C3 — noisy checkerboard backgrounds and garbled panel structure, clearly
worse than arm C. Isolation follow-up (re-evaluating C3's existing, never-scored epoch-4 checkpoint,
i.e. rank64 at arm C's own 4-epoch count, no retraining) showed the **same regression**, so it's not
purely an epoch-count or purely a rank effect — either lever pushed above arm C's exact recipe breaks
four-view, consistent with four-view being crowded out by extra capacity/steps spent on the front-layout
majority. All pilot-2 checkpoints backed up + sha256-verified locally (not published), network volume
untouched.

## Pilot 3 results: D_balance (four-view upweighting) — 2026-10-19

Verified the dataset is already exactly 1:1 by raw count (456 train front / 456 train fourview) — the
regression is not a raw-count imbalance. Hypothesis: four-view's 16px-per-view cells (vs front's 32px)
carry a weaker training signal per image at equal counts.

**D_balance**: C2's recipe, but the dataset split into two subsets by layout via symlinks only (original
dataset untouched) — front `num_repeats=1`, fourview `num_repeats=2`. Epochs cut 10->7 to hold total
steps roughly level with C2 (+5%). Exact subset manifests saved for reproducibility.

**Result: four-view substantially recovered (not fully), front stays near C2 level — a genuine
improvement to the tradeoff**, not just a shift. Fourview empty/noise score 0.041 (vs C2 0.452/C3 0.507,
arm C 0.0); bg purity 0.977 (vs C2/C3 ~0.88, arm C 0.983). By eye: most families back to a solid
background (mushroom hat, crown, helmet, party hat, cap); a few still regress (beret stays noisy;
tricorn, cowboy hat, bucket hat, headscarves, animal hat show partial noise / off-hue background). Front
holdout IoU 0.517, same band as C2/C3, not degraded; same two known miss types recur (not new). Cost:
~76 min GPU, ~$0.75, matching the pre-run estimate. Published `lora-reviews` commit `b14d91b`. All 7
checkpoints backed up + sha256-verified locally (not published), network volume untouched.

## Next
1. **user review** of all pilot sheets together (C / C2 / C3 / D_balance) — **no winner declared yet**,
   especially on four-direction consistency; awaiting verdict before any further training.
2. If pursuing D_balance further: stronger fourview upweight (beyond 2x), or target the specific
   remaining failure families (beret especially) directly, rather than a blanket rebalance.
3. Full run (beyond pilot scale) only after a recipe is picked by the user from the above.
4. ControlNet comparison later: a pretrained SDXL ControlNet with a **2x2 four-view conditioning sheet in the output
   layout** (never a single-view control against a four-view prompt — the failed T2I-adapter mismatch)
5. 1024 px stays open for a later experiment
5. consider tightening background-color fidelity for the full run (arm C drifted off-target per family)
