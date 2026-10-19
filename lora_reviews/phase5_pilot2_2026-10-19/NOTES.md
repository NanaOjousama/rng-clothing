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

So right now: extending epochs (and/or raising rank -- C2 and C3 share the epoch count, so this pilot alone
doesn't separate which factor caused it) helped the front layout's detail but broke the four-view layout.
Not declaring a winner from this pilot. Next experiment should isolate epoch-count from rank, and
specifically check whether four-view-layout training signal is being crowded out (relatively less of the
dataset, or converging slower, so extra epochs/capacity overfit toward front almost exclusively).

## Files
- `compare_front_s101.png`, `compare_fourview_s101.png` -- all checkpoints (base, A, B, C, B_e2, p2_C2, p2_C3)
  side by side, 8 families, seed 101
- `p2_C2_front_holdout.png`, `p2_C3_front_holdout.png` -- held-out hats: ground truth vs generation, front layout
- `p2_C2_fourview_holdout.png`, `p2_C3_fourview_holdout.png` -- same, four-view layout (shows the regression)
- `p2_C2_front_seeds.png`, `p2_C3_front_seeds.png` -- seed variety (4 seeds) per family, front layout

Images and notes only -- no weights, no training data, no source art, per CLAUDE.md. The actual checkpoints
(C2 and C3, final + every epoch-2 intermediate) are backed up locally to the Steam Deck, verified by sha256
against the pod, in `experiments/lora_sdxl_research/lora_backups/phase5_pilot2/` (not published anywhere).
