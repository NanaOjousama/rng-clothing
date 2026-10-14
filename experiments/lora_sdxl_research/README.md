# lora_sdxl_research: independent SDXL LoRA project

AI-ORIGINAL lane (CLAUDE.md §2b), separate from the clothing generator. Plan and
reasoning: `PLAN.md`. **No training run, memory probe or paid service without the user's OK.**

## Status (2026-10-11)

| step | state |
|---|---|
| audit of the old ChatGPT lab | done; it is failure evidence only (PLAN.md §0) |
| sd-scripts | clean upstream kohya clone on the laptop, commit `690ea7f`, `git status` clean; bitsandbytes 0.50.2 present |
| phase-1 dataset | **built and validated**: 299 front views (270 train / 29 holdout, 27 held-out constructions), 768 canvas, 32 px blocks, magenta background (255,102,255) |
| configs | written, option names checked against this sd-scripts version (`configs/`) |
| eval harness | written (`tools/eval_lora.py`), not run yet; can also run on base SDXL as the baseline |
| memory probe | 768 too slow (37 s/it); 512 copy with 24 px blocks made on the laptop |
| phase-1 training | **done (user-run, 2026-10-11)**: 512 px, 3,240 steps, 2 h 45 min, loss 0.0147 -> 0.0093; witch test block deviation 58.9 (base) -> 1.6 (LoRA). User verdict: slightly better, not usable, front-only |
| phase 2 | `PLAN_phase2.md`: dataset (512, leak-free) + probes + method-C clean-front trainer done and tested (2026-10-12); full run **approved + started 2026-10-12 17:01 (laptop)**: `configs/train_phase2.ps1` -> `runs/phase2_cleanfront/` |

## Run

    python3 -I tools/build_dataset.py                       # Deck, pure Python -> dataset/phase1_front/
    source tools/env.sh; python tools/check_dataset.py dataset/phase1_front   # (from repo root) validator + contact.png
    # laptop, after approval:
    powershell -File configs\memory_probe.ps1
    powershell -File configs\train_phase1.ps1
    python tools\eval_lora.py <dataset> <out> [lora]        # inference only

## Dataset decisions (measured, in manifest.json)

- One view per image (front). Four-view consistency stays with rules and shared tables
  (shown necessary by `template_locked_hats_01`).
- 20x20 -> exact 32 px blocks, offset 64, so the grid sits on the 8 px latent grid.
  The validator checks every block.
- Background = the colour farthest (OKLab 0.107) from every corpus colour, so alpha is
  recovered by chroma key, not by guessing at grey.
- Holdout by construction (all colourways of one shape together), stratified by family.
  The validator checks that no construction is in both splits.
- Left out of phase 1, and recorded in manifest.json:
  - 74 colourable (FS-tinted grey) constructions, which have no authored colour; this
    removes most of plurffle
  - 29 accessory-only constructions (headbands, bows, earmuffs), whose fronts are thin arcs
  - authors' translucent shadow pixels (composited on magenta they turned purple)
- 8 captions carry colour words only (Coii hats with opaque names); listed in the manifest.

## Open: moving the dataset to the laptop

`dataset/phase1_front` is 3.6 MB. Desktop Commander can only carry text, so either copy
the folder to `C:\Users\Chris\sdxl_lora_research\dataset\phase1_front` (USB / share), or
approve rebuilding it on the laptop from a compact export.
