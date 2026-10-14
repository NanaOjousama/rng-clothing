# Phase 4 plan: front LoRA + four-view LoRA with six witch reference packs

Status 2026-10-14: **PREPARED, NOT TRAINED.** Datasets are built and validated, configs are written, and the
eval harness is written. Training needs the user's approval.

Kept separate from the front-design experiment (`experiments/witch_front_design_01`): no hand-drawn or
generated front is in any training set. The six silhouette-test fronts are used only as *eval inputs*.

## Sources

| source | author | hats read | in phase 3? |
|---|---|---|---|
| pack_study library (general hats) | many | phase-1 / phase-3 selections | yes |
| Hats and Horns | PlatinumCats | 34 (witch + general) | partly (20x20 only) |
| Luny's Witch Hats | Luny | 3 | yes |
| [FS] Witch Hats | Kailey | 14 | yes (all recolours) |
| Witch Hat 492815 | Naver (내편엘리엇 / Mychocolate) | 10 | **new** |
| Wildwood Collection | mushlune | 6 | **new** |
| Bloom Collection (hats only) | mushlune | 10 | **new** (`experiments/bloom_reference_01`) |

All reference packs stay read-only in their `raw/` folders. Wildwood and Bloom enter training **only if this
plan is approved**.

## Proposed changes vs phase 3

1. **24x24 frame** (was 20x20), covering vanilla x −2..21 and y −4..19.
   - Fashion Sense anchors a hat at its top-left + `HeadPosition` (`DrawManager.GetPositionOffset`). Each hat
     keeps its native seating, with no scaling or shifting.
   - Nine witch / general hats that phase 3 had to skip now fit: HnH Veiled ×3, Mossy, Vines, both Mushroom
     hats, Coral, and others. All 22-wide Wildwood / Bloom / Luny hats fit too.
   - Still out (do not fit, or are missing a view): Cathulhu, Magikarp, Ribbon Straw, Witchy Hat – Horn
     (26 px wide), Small Laurel (no back view).
2. **Recolour control.**
   - **(a)** Hats whose fronts are identical and whose sides/backs are ≥ 90% alike count as one structure:
     at most 2 are kept, authored colours first, then the most different colours.
   - **(b)** Hats that share one silhouette body (front IoU ≥ 0.95, mirror included) are capped at 6, chosen
     for different decorations and colours.
   - **(c)** Exact duplicates are dropped (the Prismatic copies).
   - Result: 12 Kailey/Naver recolours and 2 Bloom variants dropped. Every drop is listed in the manifest.
3. **Captions.**
   - The phase-3 fix is kept: a `hats_N` slot gets the vanilla name only for ConcernedApe hats.
   - Witch hats get one of four family phrases (short / tall floppy / classic pointed / low sweeping) plus a
     decoration word (veil, moss, flower crown, single flower, bow, moon and stars, mushrooms, herb sprigs,
     straw, ragged brim, curled brim, band, flowers, leaves, pumpkin).
   - Families and decorations were assigned by eye on the matrix sheets. Please check `contact_witch.png`.
4. **Two models from the same selection.**
   - **Front LoRA** (replaces phase 1): 24x24 frame, 20-px cells. It now also gets mirror augmentation for
     light-neutral hats.
   - **Four-view LoRA** (replaces phase 3): 2x2 sheet, 10-px cells, the same method-C clean-front trainer.
5. **Witch weighting.** The 43 witch images sit in their own subset with `num_repeats = 2`.
   - Otherwise four families have to compete with 480 general images.
   - Recolours are already capped, so this repeats variety, not copies.
   - Set it to 1 for a pure rerun.
6. **Fresh from base.** The frame changed, so the phase-1 and phase-3 weights are not resumed. They stay the
   baselines.

## Dataset counts

| | four-view (`phase4_4view_512`) | front (`phase4_front_512`) | phase 3 / phase 1 |
|---|---|---|---|
| general train (orig + mirror) | 298 + 180 | 295 + 195 | 307 + 182 / 270 + 0 |
| witch train (orig + mirror) | 31 + 12 | 31 + 12 | (in general) |
| holdout | 26 general + 3 witch | 29 general + 3 witch | 26 / 29 |
| steps per epoch (witch ×2) | 564 | 576 | 489 / 270 |

Witch training images per family (orig + mirror):

| family | count |
|---|---|
| short | 10 |
| tall floppy | 11 |
| classic pointed | 6 |
| low sweeping | 16 |

Witch holdout, one per family, each with authored ground-truth views:

| family | holdout hat | nearest training front IoU |
|---|---|---|
| short | HnH Witch Hat – Long | 0.80 |
| tall floppy | Kailey Straw | 0.74 |
| low sweeping | Wildwood Elegant | 0.90 |
| classic pointed | vanilla Witch Hat c357 (in the general holdout) | — |

Naver 7/9 was the first short pick. It was rejected because its front IoU with Naver 1/5 is 0.99, so it would
not have been unseen.

**Thin spots:**
- **Classic pointed has the least data** (6 images, all HnH).
- **Low sweeping is two silhouette bodies:** Luny, and mushlune's Wildwood/Bloom.

## Validation (`tools/check_dataset_phase4.py` → `analysis/phase4_validation.json`)

**0 errors in 550 + 565 images.** The validator checks:
- every cell is exact and the margins are background
- every image decodes exactly to its laptop export. Rebuild tests with `build_phase4_laptop.py` were pixel-identical for both datasets: four-view 550/550, front 565/565 (2026-10-14; captions, folder split 490 / 43 / 32 and manifest also identical)
- mirror pairs are exact
- no construction appears in both splits
- captions are ASCII, have the family phrase, and contain no slot names or brimmed-hat words on witch hats
- no source comes from a generated experiment

The **background** magenta's nearest corpus colour is now OKLab 0.074 away (HnH Coral Headdress pink); it was
0.107. That's still clear, but a decode tolerance below 0.07 would be needed if it ever drifts.

**VAE round trip** (laptop, inference only, on phase-3 sheets re-laid into the phase-4 layouts):

| layout | wrong logical pixels (mean) | worst image |
|---|---|---|
| four-view, 10-px cells | 0.21% | 0.69% |
| front, 20-px cells | 0.15% | 2.6% |
| phase-3 four-view, 12-px cells (reference) | 0.23% | 1.25% |

The smaller cells cost nothing. Results are in `runs/vae_probe_phase4/` on the laptop.

## Training plan (laptop RTX 3060 6 GB; `configs/train_phase4.ps1`, sequential, never two at once)

| step | config | steps | time (1.06–1.89 s/it measured at 512) |
|---|---|---|---|
| 1 four-view LoRA | `phase4_4view_train.toml` (rank 16 / α 8, AdamW8bit 1e-4, 10 epochs, save every 2, save_state, clean-front p 0.75) | 5,640 | **~1.7–3.0 h** |
| 2 four-view eval | `eval_phase4.py` | ~350 renders | ~1.2 h |
| 3 front LoRA | `phase4_front_train.toml` (same hyper-parameters, plain sd-scripts trainer) | 5,760 | **~1.7–3.0 h** (phase 1 ran 3.05 s/it, so up to 4.9 h) |
| 4 front eval | `eval_front_phase4.py` | ~330 renders | ~1 h |
| 5 variety test | `eval_variety_phase4.py` | 256 renders | ~45–50 min |

**Total about 7–10 h.** The steps can run as two sessions: `train_phase4.ps1 -FourViewOnly` and `-FrontOnly`.
VRAM should match phase 3 (peak 5,979 MiB at 512): same resolution, rank and batch.

## Comparisons against previous checkpoints

- **Four-view** (`eval_phase4.py`): phase-3 **e10** vs phase-4 checkpoints, on the same jobs and seeds
  (7 8 9), scored in the 24x24 window.
  - **Jobs:**
    - the 26 phase-3 holdout hats (directly comparable with `runs/phase3_eval`)
    - the 3 new witch holdouts, scored against their authored views
    - the 6 silhouette-test fronts S1 T1 W1 W2 P1 P2 (same inputs as `runs/witch_fronts_e10_01`)
  - **Metrics:**
    - silhouette IoU vs the authored views
    - palette adherence, new colours, accent recall
    - left/right mirror IoU, back/front IoU
    - front drift
  - These are reported per group and **per family**, plus sheets at x1/x4/x10.
  - **Pass bar for "rotates the family":**
    - holdout IoU at least e10's
    - palette adherence ≥ 0.6
    - by eye, the sides and back of W1/W2 and S1 keep their silhouette (e10 failed these)
- **Front** (`eval_front_phase4.py`): phase-1 front LoRA vs phase-4 front, on the same prompts and seeds.
  - **Prompts:** 4 families × 3 decorations, 6 general-hat regression prompts, and 15 holdout captions.
  - **Metrics:** grid exactness, colours, holdout IoU, and novelty (max IoU with any training front; high means
    copying). With only 6–16 images per family, **copying is the main risk to watch**.
- **Variety test** (`eval_variety_phase4.py`, user request 2026-10-14): does the front LoRA make *new* witch
  hats, or re-draw the training bodies in new colours?
  - **Why:** low sweeping is 16 images but only 3 constructions. Front IoU (mirror-aware) is 0.93–1.00 inside
    a body (Bloom ×6, Wildwood ×5, Luny ×3) and 0.60–0.86 between bodies. Classic pointed is 2 bodies; short
    and tall floppy are 2–3.
  - **Jobs:** per witch family, its 3 prompts + 1 plain prompt × 8 seeds (101–108), for the best phase-4 front
    checkpoint and the phase-1 front LoRA.
  - **Per render:** nearest training witch front and its body; class **copy** (IoU ≥ 0.93, inside-a-body
    level), **variant** (0.85–0.93), **new** (< 0.85, the gap between two authored bodies), **empty**.
  - **Per prompt:** distinct silhouettes among the 8 seeds, and mean pairwise IoU (mode-collapse check).
  - **Sheets:** `variety_<family>_x{4,10}.png`, every render above its nearest training front.
  - **Proposed pass bar for low sweeping:** at least a third of the 32 renders are *new* **and** still read as
    low-sweeping witch hats by eye; at most a third are copies; on average ≥ 4 distinct silhouettes per 8 seeds.
    "New" but broken does not count.
  - Dry-run on the Deck with stubbed renders: training hats classify as copy, the unseen short / tall-floppy
    holdouts as new, Wildwood Elegant as variant (0.90 to its own body), as intended.
  - The four-view side already tests unseen shapes: the six silhouette-test fronts are 0.57–0.66 IoU from
    any training front (W1 0.57, W2 0.60), so rotating them is not recall.
  - Not covered: a leave-one-body-out run (train without, e.g., Bloom, and see if it invents a similar body).
    That would be a second training and needs its own approval.
- **Worn QC is still the top authority:** nothing becomes a hat without a QC-bridge capture and approval.

## To run (after approval)

1. **Copy to the laptop.** Use USB or a share, because Desktop Commander carries text only (about 900 kB):
   - `dataset/phase4_4view_512_compact.json` and its `manifest.json`
   - `dataset/phase4_front_512_compact.json` and its `manifest.json`
   - `dataset/phase4_eval_jobs.json`
   - the `tools/` and `configs/` files above
2. **Rebuild on the laptop:**
   `python tools\build_phase4_laptop.py dataset\phase4_4view_512_compact.json <manifest> dataset\phase4_4view_512`
   (same for the front dataset)
3. **Start training:** `powershell -File configs\train_phase4.ps1` (or `-FourViewOnly` first).
