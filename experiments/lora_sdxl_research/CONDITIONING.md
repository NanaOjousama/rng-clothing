# How the missing three views get conditioned on a fixed front (analysis, 2026-10-11)

User concern: training on finished four-view sheets alone may not be enough for reliable
inpainting. **Agreed, and this file explains why.** It compares four mechanisms; all need
the same four-view data.

The inference task: given a fixed front (20x20, from the forge, the LoRA, or an author),
produce right / left / back that match it, keeping the front exactly.

## A. Sheet LoRA + masked latent blending (plain "inpaint" with a 4-channel U-Net)

- **Training:** complete sheets only (all quadrants noised together).
- **Inference:** at every denoising step the front quadrant's latent is replaced by the
  front's own latent noised to that step (what diffusers' SDXL inpaint pipeline does for a
  4-channel U-Net); the other quadrants are denoised. The front pixels are pasted back at the end.
- **Weak points:**
  1. **Train/test mismatch.** The model never saw a clean, fixed front during training; it
     learned the joint distribution, not "views given a front".
  2. **Early steps.** At high noise the front's latent is mostly noise too, so the layout of the
     other views is decided before the front's information is available. That is the classic
     inpainting failure: plausible views of *a* hat, not of *this* hat.
  3. Mitigations exist (RePaint resampling: re-noise and repeat steps), but they only reduce
     the problem and multiply inference time.
- **Verdict:** works sometimes; **not reliable enough** on its own.

## B. A + a rough rule-built prior (SDEdit start)

- The other quadrants start from a rough view built from the front (front silhouette with
  rows filled with each row's dominant colour; the measured best simple rule, silhouette IoU
  0.59-0.66 vs the author's own view), noised to strength s, then refined.
- **Strengths:** the front's silhouette and colours enter at every step through the starting
  image, and views stay aligned.
- **Limits:** low s copies the crude prior; high s falls back to A. Details that differ between
  views (a buckle seen side-on, a back bow) still depend on the model guessing.
- **Verdict:** better than A; still no trained conditional behaviour.

## C. Clean-front in-context training (recommended)

- **Training:** the same sheets, but in each step the **front quadrant's latent is kept clean**
  (not noised), only the other three quadrants are noised, and the **loss is computed only on
  those three** (masked loss). The model learns exactly *p(right, left, back | clean front)*.
- **Inference:** the identical setup. The front stays clean and fixed for every step; the other
  quadrants denoise from noise (or from B's prior). Training and inference match; no mismatch.
- This is the standard way to condition a 4-channel model on known content (the
  "clean context frame" idea from video and multi-view diffusion work).
- **Cost:** same memory and time as LoRA training on the same images.
- **Needs** a small patch to the training step in sd-scripts (keep the front-quadrant latents
  un-noised; apply the quadrant mask to the loss). sd-scripts already supports masked loss; the
  per-region noise is the part to add. I would write and unit-test it before any run.
- Variant: also randomly keep a second view clean (e.g. front + right given -> left, back). The
  same model then fills in from any subset of views.

## D. ControlNet-LLLite (supported by the installed sd-scripts for SDXL)

- **Training pairs:** conditioning image = the front + B's rough views (spatially aligned
  hints); target = the authored sheet. This is explicit conditioning, through code that
  already exists.
- **Limits:**
  - the docs only confirm 24 GB VRAM (6 GB is unproven, needs its own probe)
  - the conditioning is spatially local, so moving information from the front quadrant to
    the others still relies on the U-Net's attention, as in C
- **Verdict:** the best fallback if patching the training step is unwanted.

## Recommendation

Use **C**, trained on the four-view data, with B's rough prior as an optional inference start.
Before a full run:
1. Implement the clean-front + masked-loss patch and unit-test it (no training). **Done 2026-10-11:**
   - `tools/sdxl_train_cleanfront.py` subclasses sd-scripts' `SdxlNetworkTrainer` and overrides
     only `get_noise_pred_and_target`; upstream sd-scripts is not edited.
   - Per sample, with probability `--clean_front_prob` (0.75), the front box's latents are taken
     un-noised, and that region's prediction is set to the (detached) target. Loss and gradient
     there are therefore exactly 0.
   - The remaining 25% of samples train the full sheet as usual.
   - `tools/test_cleanfront.py` passes on CPU. It checks:
     - the mask covers exactly the box
     - the front region is clean and the other quadrants are still noised
     - zero gradient from the front, non-zero from the others
     - prob 0 gives plain training, and prob 0.75 is honoured
   - The parser builds with the extra arguments.
   - `tools/infer_cleanfront.py` is the matching inference path: the clean front latent is
     re-imposed after every step via `callback_on_step_end`, which is the same input condition
     as training. diffusers' inpaint pipeline cannot do this, because it re-noises the front
     (= A).
   - Not implemented yet: starting from B's prior (strength < 1).
2. Demonstrate the inference path (`tools/demo_condition.py`). Done with the phase-1 LoRA:
   it exercises the mechanics (exact front, quadrant masking, prior start), not quality.
3. Short probe of the chosen layout for speed (results in `PLAN_phase2.md`).
