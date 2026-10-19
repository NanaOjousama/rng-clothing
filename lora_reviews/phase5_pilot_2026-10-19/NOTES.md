# Phase 5 pilot — three-arm comparison, 2026-10-19

Fresh SDXL Base 1.0 LoRA, trained on RunPod A40 from the rebuilt `phase5_v1` dataset (912 train / 82
per-family holdout, 26 shape families, solid (0,0,255) background, front + four-view layouts both
captioned). 4 epochs each, 768 px, batch 4, bf16, AdamW8bit, min-SNR 5.

| arm | rank/alpha | text encoders |
|---|---|---|
| A | 16/8  | trained, lr 2.5e-5 |
| B | 32/16 | trained, lr 2.5e-5 |
| C | 32/16 | **frozen**, cached TE outputs |
| B_e2 | 32/16 | B's epoch-2 checkpoint (earlier stop) |

## Verdict, by eye (not by loss/metrics — see CLAUDE.md judging rule)

**Arm C wins clearly and is the only arm worth carrying forward.** In both `compare_front_s101.png`
and `compare_fourview_s101.png`:
- **A and B** (trained text encoders) mostly failed to learn the training format: striped/checkered
  backgrounds instead of the solid training color, full faces or whole character bodies drawn instead
  of an isolated hat sprite, and in four-view, wrong panel counts / grid-line noise / mismatched quadrants.
  B_e2 (an earlier checkpoint of B) is not meaningfully better — the text-encoder-trained arms look
  unstable across epochs, not just "not yet converged."
- **C** (frozen text encoders) is the only arm that reliably produces an isolated hat on a solid
  background with a correct 2x2 F/R/L/B layout in four-view. Shapes are recognizable per family
  (witch hat, cowboy hat, straw hat, beret, flower crown, top hat all come through), though some are
  simplified/blobby (cap, beret) rather than crisp.
- `C_front_holdout.png` / `C_fourview_holdout.png`: held-out hats (never trained on) generate
  plausible same-family shapes — e.g. a held-out mushroom hat generates a mushroom-cap shape, a
  held-out crown generates a crown — so this isn't just memorizing the training set.

Known imperfection even in C: background color drifts off the trained (0,0,255) (comes out gray/olive/
lavender depending on family) rather than reproducing it exactly. Not a blocker — still a flat, keyable
background — but worth tightening in the full run.

The numeric metrics (`metrics_summary.json`) agree with the by-eye read (C: empty_rate ~0.0–0.01,
grid_dev ~5–9 vs A/B's ~40–50, bg_purity ~0.98–0.996 vs A/B's ~0.76–0.94) but the by-eye read is what
decided this, per project rule.

## Recommendation

Run the full training from arm C's recipe (rank 32/alpha 16, frozen text encoders, cached TE outputs),
extended epochs (16–20) with cosine schedule, before anything else. Do not spend full-run budget on
the text-encoder-trained recipe (A/B) without a different schedule/LR — at 4 epochs / lr 2.5e-5 it
actively hurt output quality relative to not training the text encoders at all.

## Files
- `compare_front_s101.png`, `compare_fourview_s101.png` — all 5 checkpoints side by side, 8 families, seed 101
- `C_front_seeds.png`, `C_fourview_seeds.png` — arm C, seed variety (4 seeds) per family
- `C_front_holdout.png`, `C_fourview_holdout.png` — arm C, held-out hats: ground truth vs generation
- `metrics_summary.json` — context only, not the basis for the verdict above

Images and notes only — no weights, no training data, no source art, per CLAUDE.md §11.
