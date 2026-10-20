# phase5_template_test_2026-10-20

**STATUS: REVIEWED — result is a FAIL against the stated success bar.**

Inference-only construction-template test on pilot3 D_balance (rank32/alpha16, frozen TE, 7 epochs,
fourview 2x-upweighted -- the project's strongest four-view-recovery checkpoint). No training, no
dataset changes, no checkpoint changes. 3 families x 2 seeds x 3 images (front, baseline fourview,
template-guided fourview) = 18 generations, 30 steps/768px, A40.

**Method.** A = today's method: one independent SDXL txt2img call for the whole four-panel sheet.
B = template-guided: generate the front panel alone, downscale it to four-view-quadrant scale, paste
it into the top-left of the canvas, then run SDXL **inpainting** with that quadrant masked OUT (kept
fixed, real pixels) and the other three masked IN (generated), conditioned on the fourview prompt plus
that fixed front context in the same image -- a real pixel anchor, not a prompt-only hint.

**Verdict is from the images themselves (see `*_enlarged.png`, `*_native.png`), not from
`baseline_lr_iou` / `template_lr_iou` in `metrics.json`** -- those numbers move in both directions
across seeds and do not track what's visually wrong below; per this project's rule, a render always
outranks a metric.

## cowboy hat -- FAIL
- s101: (1) baseline's 4 panels read as the same hat (consistent brim/color); template's front panel
  matches the anchor but the other 3 panels have a visible **white loop/rim artifact** at the lower
  edge not present in the baseline or implied by the prompt. (2) baseline's panels read as plausible
  angle changes; template's extra white shapes read as inpainting-seam noise, not hat structure.
  (3) template is clearly **worse**, not better.
- s102: same pattern -- the back panel (bottom-right) in template has a large bright white smudge
  across the crown. Baseline has no such defect.
- **Template-guided is not better than baseline for this family.**

## witch hat -- FAIL
- s101: baseline's 4 panels are strikingly consistent (same purple/yellow/point shape all 4 ways) --
  already a strong baseline. Template's front matches, but the top-right panel shows a checkerboard
  noise patch, and both bottom panels show a white blob bleeding into the hat silhouette.
- s102: template's top-right panel sits on a visibly mismatched gray rectangular patch, smaller/offset
  from the other panels -- a clear inpainting-boundary seam, not a rotation of the same object.
- **Template-guided is not better than baseline for this family.**

## straw sun hat -- FAIL
- s101: baseline's 4 panels all share the same red/white-dot ornament and blue/green band -- reads as
  one decorated hat from 4 angles. Template's front (the "anchor") is the plain hat with no ornament,
  but the other 3 panels all show a chin-strap cord and a blue zigzag band that the front doesn't have
  -- the four panels do **not** read as the same hat; the anchor itself is the odd one out.
- s102: same failure mode -- front has a distinct sprout/leaf bump, the other 3 panels don't, and show
  a different trim color instead.
- **Template-guided is not better than baseline -- it actively breaks "same hat" consistency here.**

## Structural finding (why, not just that)
Front-anchored inpainting does not deliver the hoped-for improvement with this implementation, for two
distinct reasons:
1. **Boundary artifacts.** In 2/3 families, the inpainting mask edge itself introduces visible
   white/checkerboard noise or mismatched-background patches -- a side effect of blending a fixed
   quadrant back in at every denoising step, not a real feature of the hat.
2. **Detail non-propagation.** In the 3rd family, the model could not carry specific decorative details
   (the ornament, the sprout) from the fixed front quadrant into the three panels it generates mostly
   independently, conditioned mainly by the text prompt rather than by the actual front pixels --
   producing a front-vs-rest mismatch that single-shot joint generation (baseline) does not have,
   because baseline settles on one design for the whole canvas from the start.

Readability at native-ish scale (`*_native.png`, 4x zoom) confirms this isn't just a decode-metric
artifact: baseline reads as a clean, single recognizable hat in all 4 panels for all 3 families;
template's seam artifacts remain visibly wrong even at that smaller scale.

## Recommendation
This specific front-anchored-inpainting template is **not a promising direction as implemented** --
it fails the stated success bar (criterion 4: "clearly better than baseline") for every family tested,
and in one case actively breaks the "same hat" requirement that baseline already satisfied. If the
front-anchoring idea is worth revisiting, it would likely need either a properly trained
reference-conditioning mechanism (ControlNet-style -- out of scope here, requires training) rather than
naive mask inpainting, or a different anchoring mechanism that doesn't create a hard pixel-level seam.

No retraining was performed. No dataset or checkpoint changes were made. Checkpoint used:
`pilot3_D_balance` (`sdvhat_p5_pilot3_D_balance.safetensors`), unchanged.
