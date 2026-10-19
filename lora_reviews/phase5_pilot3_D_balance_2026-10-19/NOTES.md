# Phase 5 pilot 3 -- D_balance: fourview-upweighted training, 2026-10-19

Follow-up to `phase5_pilot2_2026-10-19` (C2/C3 four-view regression) and its same-day isolation
follow-up (rank alone also broke four-view, at arm C's own epoch count). First verified the raw
dataset was **already exactly 1:1** by image count (456 train front / 456 train fourview, matching
augmented counts too) -- so the regression wasn't a raw-count imbalance. Hypothesis instead: four-view
cells render at 16px vs front's 32px (4x less pixel detail per view), so four-view carries a weaker
training signal per image even at equal counts, and any extra capacity/steps a model gets gets spent
on the easier front layout instead.

## Experiment

**D_balance**: same recipe as C2 (rank 32/alpha 16, frozen TE, cached TE outputs, same optimizer/lr/seed),
but the dataset was split into two subsets by layout -- front `num_repeats=1`, fourview `num_repeats=2`
-- doubling fourview's weight per epoch. Epochs cut 10->7 to hold total optimizer steps roughly level
with C2 (2280 steps for C2 vs 2394 for D_balance, +5%). The split was built as **symlinks only**,
additive against the existing `phase5_v1/train/1_sdvhat` folder -- the original dataset was never
copied or modified. Exact subset manifests are included here for reproducibility:
`D_balance_split_front_manifest.txt` / `D_balance_split_fourview_manifest.txt` (456 stems each).

Training: 64 min (2026-10-19 18:01-19:05 UTC). Eval: 12 min, same corrected UNet-merge loader,
identical fixed prompts/seeds/holdout families as every other arm (confirmed "create LoRA for U-Net:
722 modules" / "All keys matched" in the eval log, same as C2/C3/C3_e4). Total GPU cost: ~76 min at
$0.59/hr (A40, secure cloud CA-MTL-1) = **~$0.75**, in line with the pre-run estimate. Automatic
watchdog + independent backstop (130 min safety cap) stopped the pod after sheets regenerated; network
volume and all prior checkpoints/dataset untouched throughout.

## Verdict -- partial, genuine improvement to the tradeoff, not just a shift

**Four-view: substantially recovered, not fully.** By the metrics (see `summary.json`/`SUMMARY.md` in
the eval dir), fourview "empty" score dropped from C2's 0.452 / C3's 0.507 to **0.041** (arm C's
original was 0.0), and background purity rose from ~0.88 (C2/C3) to **0.977** (arm C was 0.983) --
both close to arm C's clean baseline. By eye (`compare_fourview_s101.png`, `p3_D_balance_fourview_holdout.png`):
most families now render on a **solid background again** (mushroom hat, crown, helmet, party hat,
cap all clean) instead of C2/C3's near-universal checkerboard noise. Some families still regress
(beret stays checkerboard-noisy; tricorn hat, cowboy hat, bucket hat, headscarves, animal hat show
partial noise or odd background hue rather than the training blue). So: real recovery, not a full
return to arm C's quality on every family.

**Front: stays close to C2/C3 level.** Holdout IoU 0.517 (vs C2 0.465, C3 0.503, C3_e4 0.523) --
within the same band, not degraded by the fourview upweighting. By eye (`p3_D_balance_front_holdout.png`):
crown, mushroom hat, bucket hat, several headscarves all clean and recognizable; same two kinds of
holdout misses seen before (animal hat and party hat both break into a garbled 4-panel grid, matching
the failure mode already seen in C2/C3's holdout results -- not a new problem introduced by D_balance).

**Net read:** this is a genuine improvement to the Pareto tradeoff rather than just moving the problem
around -- four-view's worst failure mode (checkerboard/garbled structure) is fixed for most families
while front quality is preserved at C2/C3's improved level over arm C. It is not yet a full win: arm C
remains the cleanest four-view output overall, and a few families (beret especially) still need work.
Not declaring this the final arm -- worth a look together before deciding whether to push further
(e.g. a higher fourview upweight, or targeting the beret/animal-hat/party-hat failure modes specifically).

## Files
- `compare_front_s101.png`, `compare_fourview_s101.png` -- all checkpoints (base, A, B, C, B_e2, p2_C2,
  p2_C3, p2_C3_e4, **p3_D_balance**) side by side, 8 families, seed 101
- `p3_D_balance_front_holdout.png`, `p3_D_balance_fourview_holdout.png` -- held-out hats: ground truth
  vs generation, both layouts
- `p3_D_balance_front_seeds.png`, `p3_D_balance_fourview_seeds.png` -- seed variety (4 seeds) per family
- `D_balance_split_front_manifest.txt`, `D_balance_split_fourview_manifest.txt` -- exact stem lists used
  to build the symlink subset split, for reproducibility

Images and notes only -- no weights, no training data, no source art, per CLAUDE.md. The D_balance
checkpoints (final + every epoch intermediate, 7 total) are backed up locally to the Steam Deck,
verified by sha256 against the pod, in
`experiments/lora_sdxl_research/lora_backups/phase5_pilot3/pilot3_D_balance/` (not published anywhere).
