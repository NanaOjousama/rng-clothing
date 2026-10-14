# Phase 2 plan: four-view LoRA (proposal, nothing run)

Date 2026-10-11. Starting point: phase 1 (front views, 512 px, 24 px blocks, 12 epochs, user-run).

## What phase 1 proved and didn't

- **Proved:** a small LoRA makes SDXL draw on the exact 20x20 grid (block deviation 58.9 -> 1.6 on the
  witch test), with dark outlines, ramps and the trained background, in about 3 hours on the laptop.
- **Not usable (user, 2026-10-11):** quality is only slightly better than before; stray parts
  appear (a stick, a hanging crescent); and it is **front-only**. A hat needs four views that agree.

## Evidence from the full phase-1 eval (`runs/eval/sdvhat_phase1_front_512/`, 60 renders, seen 2026-10-11)

- **Held-out hat types come out genuinely Stardew-like** (flower crowns, caps, berets, horns,
  bear ears, knits): native grid, outlines, ramps; not copies (silhouette IoU with the real
  held-out front 0.32; nearest training front 0.66).
- **New concepts become the object, not a hat:** mushroom -> a mushroom, frog -> a frog face,
  strawberry -> strawberries, acorn -> an acorn, bee -> antennae only. Witch / tricorn / chef work.
  Cause: the captions never pair "X-themed" with "hat".
- **Background keying broken:** the generated magenta drifts (lavender on some seeds), so the
  decode leaves pink / grey halos and alpha is wrong. A decoder problem; fixable without training.
- **Stray parts:** e.g. a stick and a hanging crescent on the witch test.
- **Front-only.**

## Step 0: free fixes before any new training (no GPU training)

1. Robust decode: flood the background from the border **on the 20x20 grid**, accepting cells close
   to the background colour family (magenta / lavender hue band), not one RGB +-40. Re-score the
   existing 60 renders.
2. Prompt grammar test with the current LoRA: "sdvhat, front view, <family> hat **decorated like a
   frog** / **with a mushroom-cap crown**", plus negatives "creature, fruit, plant, animal, object".
   This tells whether the object problem needs data or just prompts.
3. Epoch sweep (epochs 6 / 9 / 12, already saved) on the same seeds: pick the checkpoint that keeps
   hat shapes without stray parts.

## Core idea: train on all four views together, generate the missing views in context

Phase 1 kept consistency out of the model on purpose, because independent per-view generation
disagreed. The fix is to have the model **see all four views in one image** and **paint the
missing views next to views it already has**:

1. **Training image = a 2x2 sheet** of one hat (front | right / left | back), each logical pixel an
   exact 16 px block: 40x40 logical -> 640x640, on the 8 px latent grid (2x2 latent cells per pixel).
   The model learns how a front turns into a side and a back, from 300+ real hats.
2. **Generation, in-context:** make or choose a front (LoRA, forge, or a design brief), place it in
   the top-left quadrant, and **inpaint the other three quadrants** with the same LoRA. The views
   are conditioned on the actual front pixels, not invented independently.
3. Also allowed: generate a whole sheet at once, and compare it with the in-context mode.

This is what the old ChatGPT 2x2 runs could not do: they mixed layouts, stacked checkpoints,
used weak captions and non-aligned blocks, and never inpainted from a fixed front.

## Dataset v2 (builder, Deck, pure Python; no training needed to build)

- source: the pack_study library, all constructions with 4 authored views (about 300 after
  exclusions), up to 2 colourways each
- **view-swap augmentation** (valid, unlike a plain flip): mirror every view and swap right <->
  left. This gives a correct new sheet and doubles the data.
- colourable hats baked with their author's proven tints (brings plurffle back)
- captions: phase-1 caption + "four views, front top-left, right top-right, left bottom-left, back
  bottom-right"; plus a theme phrase where the hat has one ("decorated like a cat", "flower crown"),
  so "X-themed hat" is learned as a hat
- holdout by construction (as in phase 1); validator: blocks exact, quadrants aligned, no leak

## Training (needs approval)

| step | what | estimate |
|---|---|---|
| probe | 20 steps at 640 px, rank 32 | ~10 min; checks VRAM / speed (512 ran 3.05 s/it, 768 ran 37 s/it) |
| train | about 600 sheets x 8 epochs, rank 32, U-Net only | about 5-7 h at ~4-5 s/it |
| fallback | if 640 does not fit: 2-view pairs (front + one other view) at 704x384, 16 px blocks | similar time |

## Evaluation (judged at native size, as agreed)

- **holdout:** take a held-out hat's real front, inpaint its 3 other views, and compare with the
  author's real views (silhouette IoU per view; the rule-derived baseline was 0.58-0.66)
- **witch:** the vanilla Witch Hat stays the control. Feed the 6 forge picks' fronts and new LoRA
  fronts, inpaint, and judge the 4 views at 1x and 4x against the control and against the forge's
  own 4 views
- the 1-2 best -> FS pack -> worn QC through the bridge (needs the game running)

## Meanwhile (no training)

- finish the phase-1 evaluation (running): final vs epoch 6, 12 holdout + 8 concepts x 3 seeds
- cheap baseline: phase-1 LoRA fronts -> derive v2 / forge reader, to measure how far rules
  get on their own (phase 2 has to beat this)
- build and validate dataset v2

## Results 2026-10-12 (Steps 0-2 + conditioning; NO training run started)

Images: `analysis/results_2026-10-12/`.

**Step 0 (inference only):**
- decode_v2 works on e09 too: median 273 halo cells removed per render, 51/60 renders fixed.
  It still fails where the background drifted to *grey* instead of lavender (chef s9, c272);
  a phase-2 run should add a background-consistency check.
- e06 / e09 / final look alike at native size. No epoch is clearly better, so epoch choice is
  not the lever.
- Prompt wording (`prompt_test.png`, 5 concepts x 3 wordings x 3 seeds) helps only at the
  margins:
  - mushroom: wording 1/2 gives a cap-like hat, sometimes with a band
  - bee: gives wearable antenna headbands
  - frog: stays a frog face in every wording and seed
  - strawberry and acorn: mostly loose objects
  - **Verdict:** concepts outside the training families need a hat-shape prior (start from a
    host silhouette), not better words.

**Step 1:** `phase2_4view` (704/16 px) and `phase2_4view_512` (512/12 px, chosen). Both validate
with 0 errors.
- Holdout leak fixed: identical silhouettes (front IoU >= 0.9, mirror included) are grouped, and
  a mixed group goes wholly to its majority side.
- Counts: 273 train + 165 view-swap + 26 holdout sheets (25 constructions).

**Step 2 (probes, 20 steps each):**

| layout | rank | s/it | VAE round-trip cells wrong |
|---|---|---|---|
| 2x2 sheet 704 | 32 | 43.3 (VRAM full) | - |
| 2x2 sheet 640 | 32 | 28.6 | - |
| pair 704x384 | 32 | 14.1 | 0.0% |
| pair 704x384 | 16 | 4.86 | 0.0% |
| **2x2 sheet 512, 12-px cells** | **16** | **1.89** | **0.08% (max 0.31%)** |
| phase-1 front 512, 24 px | - | - | 0.0% |

**Conditioning demonstration (phase-1 LoRA, so this shows mechanics, not trained quality):**
- **A, inpaint from noise:** other views are *different hats* (witch -> brown hat, broken
  shapes). Attention alone does not carry identity. Confirms A is unreliable.
- **B/C, rule prior + SDEdit:** the model returns the prior almost unchanged (IoU vs prior
  0.97-1.0). Where the prior is right (witch) this looks good; where views really differ
  (trucker: bill side-on) it is simply wrong. The prior adds nothing a trained model would add.
- **Clean-front inference (`infer_cleanfront.py`, method C at inference, untrained):**
  - the mechanics work: the front stays exact, no NaNs
  - the untrained model draws generic witch hats at the wrong block scale on a grey
    background, and nothing at all for the chef hat
  - **This is the gap the clean-front training must close.**
- Method-C trainer `tools/sdxl_train_cleanfront.py` is written and unit-tested (CPU; see
  CONDITIONING.md).

**Verdict:** Method C is technically sound. Training and inference use the identical condition
(clean front latent, other quadrants noised, loss only on those). It is implemented without
editing sd-scripts and is tested.
- What it cannot guarantee: originality and beauty of the *fronts*. Those still come from the
  front generator (phase-1 LoRA, forge, or authored).
- Risks:
  - 273 base sheets is small for learning view rotation in general
  - the 12-px cells at 512 show a small VAE error (0.08%), which the per-cell decode absorbs

**Proposed full run (awaiting approval):**
- sheet512 + method C (clean_front_prob 0.75), rank 16, U-Net only, AdamW8bit, bf16, cached
  latents
- 438 train sheets x 10 epochs = 4380 steps x 1.89 s/it ~= **2.3 h** (+ ~10 min caching)
- Checkpoint every 2 epochs.
- Eval:
  - holdout fronts -> 3 views, IoU vs authored (must beat the rule prior's 0.57-0.90)
  - witch control and forge fronts at 1x/4x
  - then worn QC of the best
- Needs `dataset/phase2_4view_512` (4 MB) copied to the laptop manually (LAN serving was
  refused).

## Asking

0. Step 0 is inference-only on the laptop; I'll run it unless you say not to.
1. OK to build dataset v2 (no GPU)?
2. OK to run the 640 px memory probe after it's validated, then the training if the probe passes?

## Results 2026-10-12 evening (full run + eval)

Run: try 3, 4380 steps, 1.56 s/it, loss 0.026 -> 0.0156. Eval (`tools/eval_phase2.py`, sheets copied to
`analysis/results_2026-10-12/phase2/`). Best checkpoint by holdout silhouette IoU: **e06**.

| ckpt | holdout IoU R / L / B | rule prior R / L / B | palette adherence R / B (authored 0.99) |
|---|---|---|---|
| e02 | 0.57 / 0.55 / 0.68 | 0.64 / 0.64 / 0.67 | 0.47 / 0.57 |
| e04 | 0.53 / 0.53 / 0.69 | | 0.39 / 0.47 |
| **e06** | **0.63 / 0.62 / 0.76** | | 0.61 / 0.65 |
| e08 | 0.55 / 0.55 / 0.74 | | 0.54 / 0.64 |
| e10 | 0.59 / 0.59 / 0.72 | | 0.58 / 0.68 |

- Silhouette: sides only tie the rule prior; the back beats it. But visually the model draws real side
  perspective (angled brims, profile faces) where the prior is a flat slab, so IoU undersells it.
- Front stays exact after paste; raw drift before paste ~2% of cells.
- Colour drift is the main measured weakness (palette adherence ~0.6 vs 0.99 authored; potion hats change colour).
- User verdict: most custom fronts OK, **the bear failed** (cowboy brims on every side view), although it
  scored best on palette/mirror metrics (s1 rule: render beats metric).
- **Cause: caption.** seyph c287 is labelled 'animal hat, cowboy hat, bear hat with face'; in training 'cowboy hat'
  only ever means wide brims. `tools/caption_retest.py` (same fronts/seeds/ckpt, caption 'teddybear hat ... round
  ears'): brims gone, bear profiles with snout; authored-bear IoU 0.72 -> 0.72-0.88; cat c288 ('bowler' dropped) also
  fixed. Base-family words in captions override the front. Dataset captions need an audit before any phase 3.
