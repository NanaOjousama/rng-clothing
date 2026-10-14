# SDXL LoRA research: independent plan

Started 2026-10-11. **AI-ORIGINAL lane (CLAUDE.md §2b).** This is a separate project: it
runs alongside the clothing generator (Lane 1 recombination and Lane 2a AI fronts) and
doesn't replace either.
**Approval gates:** no training run, memory probe or paid service without the user's OK.

## 0. Starting point: what failed before (audit of the ChatGPT lab, 2026-10-10)

The laptop lab (`C:\Users\Chris\stardew-lora-lab`) is failure evidence only. Nothing from it
is reused except the clean upstream `sd-scripts` clone (kohya-ss, commit `690ea7f`,
2026-09-24, `git status` clean) and the official `sd_xl_base_1.0.safetensors` weights.

| failure in the old lab | consequence | this plan |
|---|---|---|
| model asked to draw all 4 views in a 2x2 sheet | views disagree (reproduced in `template_locked_hats_01`: per-view generation mismatched on every hat even with the shape locked) | LoRA draws **one view per image**; four-view consistency comes from rules / shared tables, never from the model |
| layout changed between runs while checkpoints were stacked (`--network_weights`) | conflicting priors | every run starts from the base model; one layout for the whole project |
| captions = boilerplate + pack item name (Chinese names, "hat" for veils) | caption can't steer design | captions built from verified data: family, brim, colours, author notes; ASCII only |
| random 10% holdout per item | recolours of held-out hats in training (leak) | holdout by **construction group** (all colourways of a shape together) |
| eval = two invented prompts + one block-flatness number | no holdout test, no 4-view test, no worn test | eval harness §5 |
| SDXL at 512, 12 px blocks (not a multiple of 8) | blur and misaligned pixels | 768 canvas, **32 px blocks** = 4x4 latent cells per pixel, grid on latent boundaries |
| grey background + "alpha = near grey" heuristic | grey or silver hats erased | background colour chosen to be **absent from the corpus**; alpha recovered exactly on the known grid |

## 1. Role of the LoRA in the pipeline

Lane 2a showed the bottleneck: SDXL base draws illustrations. Snapped to 16 px, they lose
their details (buckles, eyes, trim) and come out crude, and 11 of 29 renders were not
hats at all. The LoRA's job is narrow:

> Draw **one hat view directly on a native 20x20 grid in Stardew style** (block-exact,
> few colours, dark outline, Stardew proportions), from a design prompt.

The rest stays outside the model: extraction is trivial, because the grid is known; the
other views come from derive v2 or a later view-conditioned experiment; seating comes
from the geometry host; and worn QC decides.

## 2. Data

- Source: `pack_study/data/library.json`: 379 constructions, 20x20, all 4 authored views,
  16 authors (ConcernedApe 117, Coii 54, plurffle 40, lovisity 38, Seyph 32, ...);
  422 colourways in all.
- Personal use only (project memory); author recorded per image.
- Per image: one view of one colourway. Phase 1 trains **front** views only (one view
  per construction, the view Lane 2a generates). The other views are kept for a
  later view-token experiment.
- Recolour balance: at most 2 colourways per construction, so big recolour sets do not
  dominate.
- Grid: 20x20 view -> 640x640 (32 px blocks) centred on 768x768, offset 64 (multiple of 8).
  Nearest-neighbour only; every block is exactly one colour (checked).
- Background: the flat colour farthest (OKLab) from every corpus colour, written in the
  manifest. Semi-transparent author shadows are composited onto it and flagged.

## 3. Captions

`sdvhat, <view> view, <family words>, <brim>, <colour words>, <short note>`
- family: `pack_study/gen/semantics.host_families` (names + hand labels, high/medium only)
- brim: the verified `host_structure.json` value (`wide` / `narrow`); omitted when
  unreviewed
- names: author item names cleaned to ASCII words; vanilla `hats_<i>` mapped to the real
  name from `Content (unpacked)/Data/hats.json`; non-ASCII or opaque names dropped
- colours: the 1-3 largest material colours named from OKLCh (e.g. "dark navy", "pale straw")
- note: the hand label's description (e.g. "white ribbon bow") when present
- no author token in phase 1 (style is wanted Stardew-wide, not per author)

## 4. Split

Group = construction (`maskGroup`: all colourways of one shape). About 10% of groups go
to holdout, stratified by family and author, seed fixed. Nothing of a held-out group
appears in training. Vanilla duplicates in replacement packs are already collapsed by
`vanilla_corpus.py`.

## 5. Evaluation harness (laptop, inference only)

For base SDXL and each checkpoint, with fixed seeds:
1. **holdout prompts**: captions of held-out constructions. Score:
   - silhouette IoU with the held-out front (does it learn shape language)
   - nearest-corpus IoU (novelty: too close means copying)
2. **novel concept prompts**: the Lane 2a concepts (mushroom, witch, frog, tricorn, ...).
   Score:
   - extraction success
   - grid adherence (variance inside 32 px blocks)
   - colour count
   - not-a-hat rate (by eye, with the rejections.json categories)
3. comparison sheet: render | snapped front | derived 4 views, next to Lane 2a base-SDXL output
4. best candidates -> worn QC through the bridge (needs the game)

Metrics are advisory (CLAUDE.md §1): the sheet and the worn capture decide.

## 6. Training config (written, NOT run)

kohya `sdxl_train_network.py`, LoRA rank 16 / alpha 8, U-Net only, AdamW8bit or
Adafactor (pick after a memory probe), lr 1e-4 constant with warmup, batch 1, grad
checkpointing, bf16, cached latents + text-encoder outputs, 768 res, no bucketing, no flip
(left/right matter in later view work), no caption shuffle, min-SNR-gamma 5, 10-15 epochs,
save every epoch, fixed-seed samples per epoch. File: `configs/phase1_front.toml`.

## 7. Ladder (each step needs the user's OK)

1. **Memory probe**: 20 steps at 768 on the 6 GB GPU. Pass = no OOM, s/it measured.
   If it fails: 640 canvas (block 28 -> 4 latent cells is lost; then block 24 @ 512).
2. **Phase 1**: fronts only, ~380-420 images, ~10 epochs. Eval §5.
3. **Phase 2** (if phase 1 helps): all 4 views with a view token. Test whether
   img2img from derived views + view token improves side views over pure rules.
4. **Phase 3**: clothing (shirts) once the clothing corpus is studied.

## 8. Not yet known

- whether SDXL LoRA training at 768 fits in 6 GB (memory probe)
- whether ~400 images of 20x20 content are enough (expected: style yes, novelty partial)
- whether the block-grid style survives at inference without a grid-locking trick
