# Phase 5 pilot 2 — C2 (rank32/10ep) vs C3 (rank64/10ep) vs original arm C, 2026-10-19

Follow-up to `phase5_pilot_2026-10-19` (the first pilot). Both new arms extend winning arm C's recipe
(frozen text encoders, cached TE outputs): **C2** = same rank 32/alpha 16, extended 4->10 epochs.
**C3** = rank 64/alpha 32, 10 epochs. Both trained successfully; eval required a tooling fix mid-way
(sd-scripts' own LoRA-merge path was matching 0 U-Net modules against a diffusers U-Net -- fixed by merging
onto a native sd-scripts SdxlUNet2DConditionModel and converting its state dict back to diffusers naming).
Re-ran arm C's eval too as a consistency check after the fix (numbers match its original pilot-1 result).

## Verdict so far -- NOT final, mixed result, needs your look

**Front layout (single sprite):** C2/C3 look like a real improvement over arm C in several families --
cap and flower crown in particular are noticeably crisper/more detailed. `p2_C2_front_holdout.png` (never
trained on) generalizes well for most families (mushroom hat, bucket hat, crown, cowboy hat all recognizable
and clean) with two clear misses: one headscarf came out as an orange glyph/icon, one "animal hat" came out
as a broken 4-panel grid instead of one sprite.

**Four-view layout (2x2 F/R/L/B sheet): regressed badly.** Both C2 and C3 show noisy checkerboard-pattern
backgrounds (not the solid training background) and a garbled panel structure, clearly worse than arm C's
four-view output which stayed clean (solid background, correct 2x2 quadrants). Witch hat four-view is
unrecognizable in both.

## Follow-up: isolating epoch-count from rank (same day)

C2 and C3 share the epoch count (10), so pilot 2 alone couldn't tell whether the four-view regression
came from more epochs, more rank, or both. Rather than retrain, we re-evaluated a checkpoint that already
existed and had never been scored: **C3's own epoch-4 intermediate save** (`sdvhat_p5_pilot2_C3-000004.safetensors`,
tag `p2_C3_e4`) -- rank 64/alpha 32, but only 4 epochs, i.e. the same epoch count as the original arm C,
with only rank changed. (No new training was run; this checkpoint was already backed up and sha256-verified
before this eval.)

**Result: p2_C3_e4 also shows the four-view regression** -- same noisy checkerboard background, same garbled
panel structure, clearly worse than arm C, visible across every held-out family in `p2_C3_e4_fourview_holdout.png`.
So the regression is **not** purely an epoch-count effect: raising rank alone (even at arm C's original 4
epochs) is sufficient to break four-view. Combined with C2 (rank unchanged, epochs raised, four-view also
regressed), the pattern is that *either* lever pushed above arm C's exact recipe breaks four-view -- consistent
with the four-view layout being a minority of the training captions and getting crowded out by any extra
capacity or training time that the model spends overfitting the front-layout majority instead. Front-view
quality for p2_C3_e4 is comparable to C2/C3 (crisper detail, same kind of occasional holdout miss).

Still not declaring a winner -- arm C (rank32/4ep) remains the only recipe tested so far with a clean
four-view output. Next experiment, not yet started: directly test whether rebalancing/upweighting four-view
captions in the dataset prevents the regression even at higher rank or epoch count.

## Files
- `compare_front_s101.png`, `compare_fourview_s101.png` -- all checkpoints (base, A, B, C, B_e2, p2_C2, p2_C3,
  **p2_C3_e4**) side by side, 8 families, seed 101
- `p2_C2_front_holdout.png`, `p2_C3_front_holdout.png`, `p2_C3_e4_front_holdout.png` -- held-out hats: ground
  truth vs generation, front layout
- `p2_C2_fourview_holdout.png`, `p2_C3_fourview_holdout.png`, `p2_C3_e4_fourview_holdout.png` -- same, four-view
  layout (shows the regression in all three)
- `p2_C2_front_seeds.png`, `p2_C3_front_seeds.png`, `p2_C3_e4_front_seeds.png` -- seed variety (4 seeds) per
  family, front layout

Images and notes only -- no weights, no training data, no source art, per CLAUDE.md. The actual checkpoints
(C2 and C3, final + every epoch-2 intermediate, including the C3 epoch-4 save evaluated here) are backed up
locally to the Steam Deck, verified by sha256 against the pod, in
`experiments/lora_sdxl_research/lora_backups/phase5_pilot2/` (not published anywhere).
