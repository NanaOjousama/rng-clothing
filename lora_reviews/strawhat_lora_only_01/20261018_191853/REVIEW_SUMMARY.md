# strawhat_lora_only — resolution comparison

Review-only comparison of a straw-hat 4-view generation (LoRA-only, no adapter),
run on RunPod A40 at three resolutions to find the usable one.

| Res  | 4-view layout                    | Color                       | Verdict                          |
|------|----------------------------------|-----------------------------|----------------------------------|
| 512  | clean 2×2 (front/right/left/back)| reverted to grey            | layout good, color failed        |
| 768  | clean 2×2                        | straw-gold + brown outline  | **the good sprite**              |
| 1024 | duplicated into ~8 scattered hats| straw-gold                  | crisp but composition broken     |

**Finding:** the LoRA was trained at 512, so 1024 tiles the subject (duplication)
and 512 loses color. 768 is the sweet spot — enough resolution for straw color to
express, low enough that the 4-view grid stays intact. 768 is the ceiling until
the LoRA is retrained at higher native resolution.

Still a 768px raster, not yet a Stardew asset: needs grid reduction (per-cell
sampling + palette snap, no resampling) → real alpha → worn QC via the bridge.

Provenance: LoRA-only (plan A, no adapter). Files preserved on RunPod volume
qlenaxj02c at results/strawhat_lora_only_1024/. Pod stardew-a40 stopped after run.
